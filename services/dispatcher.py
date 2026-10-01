"""
Despachante e Orquestrador de Lotes de Pacientes - OpenLEA (OftalmoPE Tech).
Gerencia o loop de processamento, checagem de paradas (ESC / P), pintura em planilha,
coleta de métricas e envio de telemetria ao Sentinel.
"""

from datetime import datetime, timezone
import logging
from pathlib import Path
import time
from typing import Callable, List, Optional

from core.hotkeys import controle_execucao
from database.excel_reader import registrar_status
from database.models import RegistroPaciente, RelatorioLote, ResultadoItem
from services.smart_rpa import SmartRPADriver
from services.telemetry_service import TelemetryService

logger = logging.getLogger("openlea.dispatcher")


class BatchDispatcher:
    """Orquestrador responsável pelo ciclo de vida do lote de emissão de LEAs."""

    def __init__(
        self,
        driver: SmartRPADriver,
        telemetry_service: Optional[TelemetryService] = None,
        callback_progresso: Optional[Callable[[int, int, RegistroPaciente, str], None]] = None,
    ):
        self.driver = driver
        self.telemetry_service = telemetry_service
        self.callback_progresso = callback_progresso

    def executar_lote(
        self,
        caminho_planilha: Path | str,
        fila: List[RegistroPaciente],
        modo_simulacao: bool = False,
    ) -> RelatorioLote:
        """
        Executa a fila de pacientes com controle estrito de interrupção e contingência.
        """
        relatorio = RelatorioLote(
            total_itens=len(fila),
            modo_simulacao=modo_simulacao,
            arquivo_origem=str(caminho_planilha),
            timestamp_inicio=datetime.now(timezone.utc),
        )

        inicio_lote = time.perf_counter()
        total = len(fila)

        for i, paciente in enumerate(fila, start=1):
            # 1. Checagem de parada solicitada antes do próximo paciente
            if controle_execucao.deve_parar_apos_atual or controle_execucao.deve_parar_imediato:
                motivo = controle_execucao.motivo or "Interrupção solicitada pelo operador"
                logger.warning("Execução interrompida antes do paciente %s: %s", paciente.reg, motivo)
                registrar_status(caminho_planilha, paciente.row_index, "aviso")
                relatorio.resultados.append(
                    ResultadoItem(
                        item=paciente,
                        sucesso=False,
                        motivo_falha=motivo,
                        interrompido=True,
                    )
                )
                relatorio.total_inconsistencias += 1
                break

            if self.callback_progresso:
                self.callback_progresso(i, total, paciente, "Iniciando processamento...")

            inicio_item = time.perf_counter()
            sucesso_item = False
            motivo_falha = None
            interrompido = False

            try:
                self.driver.processar_paciente(paciente)
                sucesso_item = True
                duracao_item = time.perf_counter() - inicio_item
                registrar_status(caminho_planilha, paciente.row_index, "sucesso")
                relatorio.total_sucesso += 1
                if self.callback_progresso:
                    self.callback_progresso(i, total, paciente, "Concluído com sucesso (Azul).")
            except InterruptedError as ie:
                duracao_item = time.perf_counter() - inicio_item
                motivo_falha = str(ie)
                interrompido = True
                logger.warning("Interrupção imediata detectada: %s", ie)
                self.driver.acionar_fallback_reset()
                registrar_status(caminho_planilha, paciente.row_index, "aviso")
                relatorio.total_inconsistencias += 1
                relatorio.resultados.append(
                    ResultadoItem(
                        item=paciente,
                        sucesso=False,
                        motivo_falha=motivo_falha,
                        tempo_processamento=duracao_item,
                        interrompido=True,
                    )
                )
                break
            except Exception as e:
                duracao_item = time.perf_counter() - inicio_item
                motivo_falha = str(e)
                logger.error("Falha ao emitir LEA para prontuário %s: %s", paciente.reg, e)
                self.driver.acionar_fallback_reset()
                registrar_status(caminho_planilha, paciente.row_index, "erro")
                relatorio.total_inconsistencias += 1
                if self.callback_progresso:
                    self.callback_progresso(i, total, paciente, f"Falha: {e}")

            relatorio.resultados.append(
                ResultadoItem(
                    item=paciente,
                    sucesso=sucesso_item,
                    motivo_falha=motivo_falha,
                    tempo_processamento=duracao_item,
                    interrompido=interrompido,
                )
            )

            # Checagem imediata pós-paciente
            if controle_execucao.deve_parar_apos_atual:
                logger.info("Encerrando execução conforme parada suave solicitada.")
                break

        relatorio.tempo_execucao_segundos = max(time.perf_counter() - inicio_lote, 0.1)

        # Despacho de telemetria agregada para o Sentinel
        if self.telemetry_service:
            try:
                self.telemetry_service.despachar_telemetria(relatorio)
            except Exception as e:
                logger.warning("Falha ao despachar telemetria para Sentinel: %s", e)

        return relatorio
