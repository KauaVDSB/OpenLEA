"""
Módulo de Heartbeat em Background e Kill-Switch Remoto - OpenLEA (OftalmoPE Tech).
Executa sinal periódico de sessão, reenvia telemetria offline pendente e gerencia
suspensão remota com Grace Period conforme políticas corporativas (ADR-004, ADR-008).
"""

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
import logging
import threading
from typing import Any, Optional

import httpx

from core.config import SENTINEL_API_URL, SENTINEL_CLIENT_ID

logger = logging.getLogger("openlea.heartbeat")


class HeartbeatService:
    """
    Serviço não-bloqueante de sinal de vida (Heartbeat) e controle de sessão remota.
    Executa em thread daemon, garantindo que o faturador receba avisos amigáveis em caso
    de suspensão e que eventos pendentes de telemetria sejam despachados automaticamente.
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        session_token: Optional[str] = None,
        client_id: Optional[str] = None,
        telemetry_service: Optional[Any] = None,
        intervalo_segundos: float = 300.0,
        on_kill_switch: Optional[Callable[[str, Optional[datetime]], None]] = None,
    ) -> None:
        self.api_url = (api_url or SENTINEL_API_URL).rstrip("/")
        self.session_token = session_token
        self.client_id = client_id or SENTINEL_CLIENT_ID
        self.telemetry_service = telemetry_service
        self.intervalo_segundos = intervalo_segundos
        self.on_kill_switch = on_kill_switch

        self.kill_switch_ativado: bool = False
        self.kill_switch_motivo: Optional[str] = None
        self.kill_switch_deadline: Optional[datetime] = None

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def verificar_estado_seguro(self, agora: Optional[datetime] = None) -> tuple[bool, Optional[str]]:
        """
        Verifica se a execução pode continuar ou se o prazo do Kill-Switch expirou.
        Returns:
            Tupla (pode_continuar, mensagem_aviso).
        """
        if not self.kill_switch_ativado:
            return True, None

        now = agora or datetime.now(timezone.utc)
        if self.kill_switch_deadline and now < self.kill_switch_deadline:
            restante_min = max(0, int((self.kill_switch_deadline - now).total_seconds() / 60))
            aviso = (
                f"Atenção: Notificação de suspensão recebida ({self.kill_switch_motivo}). "
                f"Período de carência (Grace Period) ativo: {restante_min} minuto(s) restante(s)."
            )
            return True, aviso

        motivo = self.kill_switch_motivo or "Revogação administrativa"
        mensagem_bloqueio = f"Sessão bloqueada: {motivo}. Prazo de carência expirado."
        return False, mensagem_bloqueio

    def tick(self, agora: Optional[datetime] = None) -> tuple[bool, Optional[str]]:
        """
        Executa um único ciclo de verificação:
        1. Tenta retransmitir telemetria acumulada na fila offline;
        2. Envia POST de heartbeat ao Sentinel;
        3. Avalia comandos remotos (Kill-Switch) e atualiza prazos de carência.
        """
        now = agora or datetime.now(timezone.utc)

        # 1. Reenvio automático de telemetria pendente
        if self.telemetry_service and hasattr(self.telemetry_service, "tentar_reenvio_pendentes"):
            try:
                self.telemetry_service.tentar_reenvio_pendentes()
            except Exception as e:
                logger.debug("Tentativa de reenvio de telemetria pendente no heartbeat: %s", e)

        # 2. Requisição de Heartbeat ao Sentinel
        payload = {
            "session_token": self.session_token,
            "client_id": self.client_id,
            "timestamp": now.isoformat(),
        }

        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.post(f"{self.api_url}/api/v1/sentinel/heartbeat", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("kill_switch") is True:
                        self.kill_switch_ativado = True
                        self.kill_switch_motivo = data.get("message", "Sessão suspensa remotamente pelo Sentinel.")
                        grace_min = int(data.get("grace_period_minutes", 0))

                        if grace_min > 0:
                            self.kill_switch_deadline = now + timedelta(minutes=grace_min)
                        else:
                            self.kill_switch_deadline = now

                        if self.on_kill_switch:
                            try:
                                self.on_kill_switch(self.kill_switch_motivo, self.kill_switch_deadline)
                            except Exception as cb_err:
                                logger.warning("Erro no callback de kill-switch: %s", cb_err)

                        return self.verificar_estado_seguro(now)
        except Exception as err:
            logger.debug("Sentinel inalcançável no heartbeat (%s). Mantendo operação sob contingência.", err)

        return self.verificar_estado_seguro(now)

    def _loop_heartbeat(self) -> None:
        """Loop executado em segundo plano pela thread daemon."""
        while not self._stop_event.is_set():
            self._stop_event.wait(self.intervalo_segundos)
            if not self._stop_event.is_set():
                pode_continuar, msg = self.tick()
                if not pode_continuar:
                    logger.warning("Kill-Switch definitivo atingido em background: %s", msg)
                    break

    def start(self) -> None:
        """Inicia o monitoramento periódico em background."""
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop_heartbeat, daemon=True, name="SentinelHeartbeatThread")
        self._thread.start()
        logger.info("Serviço de Heartbeat e Kill-Switch iniciado em background.")

    def stop(self) -> None:
        """Para o monitoramento periódico graciosamente."""
        self._stop_event.set()
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("Serviço de Heartbeat finalizado.")
