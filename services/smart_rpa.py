"""
Automação Robótica de Processos (RPA) - Pixeon SMART Módulo SUS (MWSUS190 / LEA).
Executa o preenchimento automatizado de Laudos para Emissão de APAC (LEA) com verificação
estrita de parada imediata (ESC) e ZERO fallback de unidade hospitalar.
"""

import logging
import sys
import time
from typing import Any, Optional

from core.config import (
    PAUSA_CURTA,
    PAUSA_LONGA,
    PAUSA_MEDIA,
    TITULO_JANELA_LEA,
    TITULO_MWSUS,
)
from core.hotkeys import controle_execucao
from database.models import RegistroPaciente

logger = logging.getLogger("openlea.rpa")


class SmartRPADriver:
    """Controlador de automação para o Pixeon SMART / MWSUS."""

    def __init__(self, mock_mode: bool = False):
        self.mock_mode = mock_mode or (sys.platform != "win32")
        self.app: Any = None
        self.janela_lea: Any = None

    def conectar(self, timeout: int = 10) -> Any:
        """Conecta à janela do Módulo SUS do Pixeon SMART."""
        if self.mock_mode:
            logger.info("[MOCK] Conectado à janela simulada do MWSUS190.")
            self.janela_lea = "MOCK_WINDOW"
            return self.janela_lea

        try:
            from pywinauto import Application

            self.app = Application(backend="uia").connect(
                title_re=f".*{TITULO_MWSUS}.*", timeout=timeout
            )
            self.janela_lea = self.app.window(
                title_re=f".*{TITULO_MWSUS}.*"
            ).child_window(title=TITULO_JANELA_LEA, control_type="Window")
            self.janela_lea.wait("visible", timeout=timeout)
            self.janela_lea.set_focus()
            return self.janela_lea
        except Exception as e:
            logger.error("Falha ao conectar com Pixeon SMART MWSUS: %s", e)
            raise ConnectionError(
                f"Não foi possível localizar a tela do MWSUS/LEA: {e}"
            )

    def acionar_fallback_reset(self) -> None:
        """Desvia de erros não salvos retornando à tela inicial de forma defensiva."""
        if self.mock_mode or not self.janela_lea:
            logger.info("[MOCK] Fallback reset executado.")
            return

        try:
            self.janela_lea.set_focus()
            self.janela_lea.type_keys("{F9 6}{F4}{RIGHT}{ENTER}")
            time.sleep(PAUSA_MEDIA)
        except Exception as e:
            logger.warning("Erro durante fallback reset: %s", e)

    def _verificar_interrupcao(self) -> None:
        """Verifica se houve comando de interrupção imediata (ESC)."""
        if controle_execucao.deve_parar_imediato:
            raise InterruptedError(
                f"Operação cancelada pelo operador: {controle_execucao.motivo}"
            )

    def processar_paciente(self, paciente: RegistroPaciente) -> None:
        """
        Executa os passos de preenchimento da LEA no MWSUS para um paciente.
        REGRA DE SEGURANÇA: Unidade é estritamente obrigatória e obtida da linha do paciente.
        """
        if not paciente.unidade or not paciente.unidade.strip():
            raise ValueError(
                f"Linha {paciente.row_index}: Registro {paciente.reg} sem Unidade hospitalar definida. "
                "Operação abortada por segurança contra convênio incorreto."
            )

        self._verificar_interrupcao()

        if self.mock_mode:
            logger.info(
                "[MOCK RPA] Processando paciente Reg=%s, Medico=%s, Unidade=%s, Data=%s",
                paciente.reg,
                paciente.medico,
                paciente.unidade,
                paciente.data_validade,
            )
            time.sleep(0.05)
            self._verificar_interrupcao()
            return

        # Execução Real Windows UIA
        janela = self.janela_lea
        janela.set_focus()

        # 1. Registro e Busca (F4)
        self._verificar_interrupcao()
        janela.type_keys(f"{paciente.reg}{{F4}}")
        time.sleep(PAUSA_LONGA)

        # 2. Inicia novo registro (F10 -> F3)
        self._verificar_interrupcao()
        janela.type_keys("{F10}")
        time.sleep(PAUSA_MEDIA)
        janela.type_keys("{F3}")
        time.sleep(1.0)

        # 3. Seleção da Unidade (Obrigatória, sem fallback)
        self._verificar_interrupcao()
        janela.type_keys(f"{{TAB}}{{TAB}}{paciente.unidade}{{ENTER}}", with_spaces=True)
        time.sleep(1.0)

        # 4. Grava Unidade (F5)
        self._verificar_interrupcao()
        janela.type_keys("{F5}")
        time.sleep(1.5)

        # 5. Preenche Data de Emissão, Solicitante e Procedimento
        self._verificar_interrupcao()
        janela.type_keys(f"{paciente.data_validade}")
        time.sleep(0.5)

        janela.type_keys("{TAB}{TAB}")
        janela.type_keys(f"{paciente.medico}{{ENTER}}", with_spaces=True)
        time.sleep(0.5)

        janela.type_keys("{TAB}{TAB}{TAB}")
        janela.type_keys(f"{paciente.consulta}{{ENTER}}", with_spaces=True)
        time.sleep(0.5)

        # 6. Grava (F5) e Avança (F10)
        self._verificar_interrupcao()
        janela.type_keys("{F5}")
        time.sleep(2.0)
        janela.type_keys("{F10}")
        time.sleep(2.0)

        # 7. Preenche CID-10
        self._verificar_interrupcao()
        janela.type_keys(f"{paciente.cid10}{{TAB}}")
        time.sleep(0.5)
        janela.type_keys("{F5}")
        time.sleep(1.0)

        # 8. Navega para a Aba APAC (F10 3x)
        self._verificar_interrupcao()
        janela.type_keys("{F10 3}")
        time.sleep(1.0)

        # 9. Preenche Campos da APAC
        self._verificar_interrupcao()
        valid_ini = janela.child_window(title="sap_dt_valid_ini", control_type="Edit")
        valid_ini.click_input()
        janela.type_keys(f"{paciente.data_validade}")
        time.sleep(0.5)

        janela.child_window(title="sap_mot_cobr", control_type="ComboBox").click_input()
        janela.type_keys(f"{paciente.mot_cobr}")
        time.sleep(0.5)

        janela.child_window(title="sap_s_apac_ap_cod", control_type="ComboBox").click_input()
        janela.type_keys(f"{paciente.s_apac_ap_cod}")
        time.sleep(0.5)

        janela.child_window(title="sap_dt_ocorr", control_type="Edit").click_input()
        janela.type_keys(f"{paciente.data_validade}")
        time.sleep(0.5)

        # 10. Grava APAC Final (F5)
        self._verificar_interrupcao()
        janela.type_keys("{F5}")
        time.sleep(2.0)

        # 11. Retorna para Tela Inicial de Busca (F9 6x, F4)
        janela.type_keys("{F9 6}")
        time.sleep(1.0)
        janela.type_keys("{F4}")
        time.sleep(1.0)
