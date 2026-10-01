"""
Cliente de Licenciamento, Handshake e Kill-Switch Remoto - OpenLEA (OftalmoPE Tech).
Valida vigência, versão mínima instalada e integridade da sessão corporativa via Sentinel (ADR-004).
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sys
from typing import Any, Tuple
import httpx

from core.config import (
    APP_NAME,
    APP_VERSION,
    HTTP_TIMEOUT,
    LICENSE_CACHE_FILE,
    SENTINEL_API_URL,
    SENTINEL_CLIENT_ID,
    SENTINEL_LICENSE_KEY,
)

logger = logging.getLogger("openlea.license")


class LicenseClient:
    """
    Cliente de comunicação com o Sentinel para validação de licenças corporativas do OpenLEA.
    """

    def __init__(
        self,
        api_url: str = SENTINEL_API_URL,
        client_id: str = SENTINEL_CLIENT_ID,
        license_key: str = SENTINEL_LICENSE_KEY,
        app_name: str = APP_NAME,
        app_version: str = APP_VERSION,
        cache_file: Path = LICENSE_CACHE_FILE,
    ):
        self.api_url = api_url.rstrip("/")
        self.client_id = client_id
        self.license_key = license_key
        self.app_name = app_name
        self.app_version = app_version
        self.cache_file = cache_file
        self.session_token: str | None = None

    def verificar_handshake(self) -> Tuple[bool, str, dict[str, Any]]:
        """
        Executa o handshake inicial contra o Sentinel.
        Retorna (autorizado: bool, mensagem: str, dados: dict).
        """
        payload = {
            "client_id": self.client_id,
            "license_key": self.license_key,
            "app_name": self.app_name,
            "app_version": self.app_version,
            "platform": sys.platform,
        }
        url = f"{self.api_url}/api/v1/sentinel/handshake"

        try:
            with httpx.Client(timeout=HTTP_TIMEOUT) as client:
                resp = client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    status = data.get("status")
                    if status == "AUTHORIZED":
                        self.session_token = data.get("session_token")
                        self._gravar_cache(data)
                        return True, data.get("message", "Sessão autorizada."), data
                    elif status == "UPDATE_REQUIRED":
                        return False, "Atualização obrigatória pendente.", data
                    else:
                        return False, data.get("message", "Acesso não autorizado."), data
                else:
                    return self._fallback_cache(f"Servidor Sentinel retornou HTTP {resp.status_code}")
        except Exception as e:
            logger.warning("Falha de rede ao contatar Sentinel: %s. Tentando contingência offline...", e)
            return self._fallback_cache(f"Falha de conexão com a central: {e}")

    def _gravar_cache(self, data: dict[str, Any]) -> None:
        """Armazena os dados validados de licença no cache local."""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            self.cache_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning("Não foi possível salvar cache de licença: %s", e)

    def _fallback_cache(self, motivo: str) -> Tuple[bool, str, dict[str, Any]]:
        """Verifica se há autorização válida em cache local para contingência offline."""
        if not self.cache_file.exists():
            return False, f"{motivo}. Sem cache de licença disponível.", {}

        try:
            data = json.loads(self.cache_file.read_text(encoding="utf-8"))
            expires_at = data.get("expires_at")
            if expires_at:
                dt_exp = datetime.fromisoformat(expires_at)
                if dt_exp.tzinfo is None:
                    dt_exp = dt_exp.replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) <= dt_exp:
                    self.session_token = data.get("session_token")
                    return True, "Operando em contingência offline com licença válida.", data
            return False, f"{motivo}. Licença offline expirada.", {}
        except Exception as e:
            return False, f"{motivo}. Falha ao ler cache local ({e}).", {}
