from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from database.models import RegistroPaciente, RelatorioLote, ResultadoItem
from services.license_client import LicenseClient
from services.telemetry_service import TelemetryService


def test_license_handshake_authorized(tmp_path: Path):
    cache_file = tmp_path / ".license_cache.json"
    client = LicenseClient(
        api_url="https://mock.sentinel",
        client_id="test_client",
        license_key="TEST-KEY",
        cache_file=cache_file,
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "status": "AUTHORIZED",
        "session_token": "token_xyz123",
        "message": "Licença autorizada até 2026-10-13",
        "expires_at": "2026-10-13T23:59:59+00:00",
    }

    with patch("httpx.Client.post", return_value=mock_resp):
        autorizado, msg, data = client.verificar_handshake()
        assert autorizado is True
        assert client.session_token == "token_xyz123"
        assert cache_file.exists()


def test_license_fallback_cache_valid(tmp_path: Path):
    cache_file = tmp_path / ".license_cache.json"
    future_date = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    cache_file.write_text(
        json.dumps(
            {
                "status": "AUTHORIZED",
                "session_token": "cached_token_999",
                "expires_at": future_date,
            }
        ),
        encoding="utf-8",
    )

    client = LicenseClient(
        api_url="https://offline.sentinel",
        cache_file=cache_file,
    )

    # Simula falha total de rede
    with patch("httpx.Client.post", side_effect=Exception("Network down")):
        autorizado, msg, data = client.verificar_handshake()
        assert autorizado is True
        assert client.session_token == "cached_token_999"
        assert "contingência offline" in msg


def test_telemetry_payload_zero_pii(tmp_path: Path):
    queue_file = tmp_path / ".telemetry_queue.json"
    service = TelemetryService(
        api_url="https://mock.sentinel",
        client_id="oftalmope_hospital_gus",
        queue_file=queue_file,
        session_token="token_mock",
    )

    paciente = RegistroPaciente(
        row_index=5,
        reg="778899",
        consulta="CONSULTA",
        medico="DR. EXEMPLO",
        unidade="HOSPITAL OFTALMO PE",
        data_validade="14082026",
    )

    relatorio = RelatorioLote(
        lote_id="lote_001",
        total_itens=1,
        total_sucesso=1,
        total_inconsistencias=0,
        tempo_execucao_segundos=15.5,
        resultados=[
            ResultadoItem(item=paciente, sucesso=True, tempo_processamento=15.5)
        ],
    )

    payload = service.construir_payload_telemetria(relatorio)

    # Validações Zero PII (ADR-003)
    payload_str = json.dumps(payload)
    assert "778899" not in payload_str
    assert "DR. EXEMPLO" not in payload_str
    assert payload["client_id"] == "oftalmope_hospital_gus"
    assert payload["metricas"]["total_pacientes"] == 1
    assert payload["metricas"]["sucessos"] == 1
