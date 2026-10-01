"""
Serviço de Telemetria e Coletor de Métricas de Lote - OpenLEA (OftalmoPE Tech).
Implementa conformidade LGPD Zero PII (ADR-003), fila local persistente offline (ADR-008),
expurgo por TTL (5 dias) e despacho de métricas agregadas ao Admin Hub Sentinel.
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid
import httpx

from core.config import (
    APP_NAME,
    APP_VERSION,
    DEFAULT_TELEMETRY_QUEUE_FILE,
    HTTP_TIMEOUT,
    SENTINEL_API_URL,
    SENTINEL_CLIENT_ID,
    sanitizar_mensagem_erro,
)
from database.models import RelatorioLote

logger = logging.getLogger("openlea.telemetry")


class TelemetryService:
    """
    Despachante resiliente de métricas para o Sentinel Dashboard.
    Garante que falhas temporárias de rede não percam dados de produtividade e ROI.
    """

    def __init__(
        self,
        api_url: str = SENTINEL_API_URL,
        client_id: str = SENTINEL_CLIENT_ID,
        app_name: str = APP_NAME,
        app_version: str = APP_VERSION,
        queue_file: Path = DEFAULT_TELEMETRY_QUEUE_FILE,
        session_token: Optional[str] = None,
    ):
        self.api_url = api_url.rstrip("/")
        self.client_id = client_id
        self.app_name = app_name
        self.app_version = app_version
        self.queue_file = queue_file
        self.session_token = session_token

    def construir_payload_telemetria(self, relatorio: RelatorioLote) -> Dict[str, Any]:
        """
        Gera payload de telemetria agregada 100% livre de PII (ADR-003).
        Apenas contadores, tempos agregados e motivos de erro anonimizados/sanitizados.
        """
        contador_erros: Dict[str, int] = {}
        for res in relatorio.resultados:
            if not res.sucesso and res.motivo_falha:
                motivo_limpo = sanitizar_mensagem_erro(res.motivo_falha, max_len=250)
                contador_erros[motivo_limpo] = contador_erros.get(motivo_limpo, 0) + 1

        erros_resumo = [
            {"motivo": mot, "quantidade": qtd}
            for mot, qtd in contador_erros.items()
        ]

        tempo_total = max(relatorio.tempo_execucao_segundos, 0.1)
        tempo_medio = (
            tempo_total / relatorio.total_itens if relatorio.total_itens > 0 else 0.0
        )

        return {
            "client_id": self.client_id,
            "session_token": self.session_token or "offline_contingency",
            "app_name": self.app_name,
            "app_version": self.app_version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "modo_operacao": "SIMULACAO" if relatorio.modo_simulacao else "LIVE",
            "metricas": {
                "lote_id": relatorio.lote_id,
                "total_pacientes": relatorio.total_itens,
                "sucessos": relatorio.total_sucesso,
                "inconsistencias": relatorio.total_inconsistencias,
                "tempo_total_segundos": tempo_total,
                "tempo_medio_por_laudo": tempo_medio,
                "erros_resumo": erros_resumo,
            },
        }

    def _carregar_fila(self) -> List[Dict[str, Any]]:
        """Carrega a fila local persistente se o arquivo existir."""
        if not self.queue_file.exists():
            return []
        try:
            content = self.queue_file.read_text(encoding="utf-8").strip()
            if not content:
                return []
            return json.loads(content)
        except Exception as e:
            logger.warning("Falha ao ler fila local de telemetria: %s", e)
            return []

    def _salvar_fila(self, fila: List[Dict[str, Any]]) -> None:
        """Salva a fila de telemetria no disco."""
        try:
            self.queue_file.parent.mkdir(parents=True, exist_ok=True)
            self.queue_file.write_text(json.dumps(fila, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            logger.error("Falha ao persistir fila local de telemetria: %s", e)

    def expurgar_por_ttl(self, dias: int = 5, fila: Optional[List[Dict[str, Any]]] = None) -> int:
        """
        Remove registros com status 'SENT' há mais de N dias corridos (ADR-008).
        Registros 'PENDING' nunca são excluídos até serem entregues com sucesso.
        """
        salvar_ao_final = False
        if fila is None:
            fila = self._carregar_fila()
            salvar_ao_final = True

        agora = datetime.now(timezone.utc)
        limite_segundos = dias * 86400
        itens_filtrados = []
        removidos = 0

        for item in fila:
            if item.get("status") == "SENT":
                sent_at = item.get("sent_at")
                if sent_at:
                    try:
                        dt = datetime.fromisoformat(sent_at)
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        if (agora - dt).total_seconds() > limite_segundos:
                            removidos += 1
                            continue
                    except Exception:
                        pass
            itens_filtrados.append(item)

        fila[:] = itens_filtrados
        if salvar_ao_final and removidos > 0:
            self._salvar_fila(itens_filtrados)
        return removidos

    def tentar_reenvio_pendentes(self) -> int:
        """
        Varre a fila local e retransmite registros em status 'PENDING' para o Sentinel.
        Retorna o total de lotes transmitidos com sucesso nesta execução.
        """
        fila = self._carregar_fila()
        if not fila:
            return 0

        enviados = 0
        url_endpoint = f"{self.api_url}/api/v1/sentinel/telemetry"

        with httpx.Client(timeout=HTTP_TIMEOUT) as client:
            for item in fila:
                if item.get("status") != "PENDING":
                    continue
                payload = item.get("payload", {})
                try:
                    resp = client.post(url_endpoint, json=payload)
                    if resp.status_code in (200, 201, 204):
                        item["status"] = "SENT"
                        item["sent_at"] = datetime.now(timezone.utc).isoformat()
                        enviados += 1
                    else:
                        item["ultimo_erro"] = f"HTTP {resp.status_code}: {resp.text[:100]}"
                except Exception as e:
                    item["ultimo_erro"] = str(e)[:100]

        if enviados > 0:
            self.expurgar_por_ttl(dias=5, fila=fila)
            self._salvar_fila(fila)
        return enviados

    def despachar_telemetria(self, relatorio: RelatorioLote) -> bool:
        """
        Despacha a telemetria de um lote para o Sentinel.
        Caso ocorra sucesso, persiste com status 'SENT'.
        Caso ocorra falha de rede, enfileira com status 'PENDING' para auto-flush posterior.
        """
        self.tentar_reenvio_pendentes()
        payload = self.construir_payload_telemetria(relatorio)

        item = {
            "id": str(uuid.uuid4()),
            "status": "PENDING",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "sent_at": None,
            "tentativas": 0,
            "ultimo_erro": None,
            "payload": payload,
        }
        fila = self._carregar_fila()
        fila.append(item)

        url_endpoint = f"{self.api_url}/api/v1/sentinel/telemetry"
        try:
            with httpx.Client(timeout=HTTP_TIMEOUT) as client:
                resp = client.post(url_endpoint, json=payload)
                if resp.status_code in (200, 201, 204):
                    item["status"] = "SENT"
                    item["sent_at"] = datetime.now(timezone.utc).isoformat()
                    self.expurgar_por_ttl(dias=5, fila=fila)
                    self._salvar_fila(fila)
                    return True
                else:
                    item["tentativas"] = 1
                    item["ultimo_erro"] = f"HTTP {resp.status_code}: {resp.text[:100]}"
                    self._salvar_fila(fila)
                    return False
        except Exception as e:
            item["tentativas"] = 1
            item["ultimo_erro"] = str(e)[:100]
            self._salvar_fila(fila)
            return False
