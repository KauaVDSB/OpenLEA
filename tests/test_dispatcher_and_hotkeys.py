from pathlib import Path
from unittest.mock import MagicMock
import openpyxl
import pytest

from core.hotkeys import controle_execucao
from database.models import RegistroPaciente
from services.dispatcher import BatchDispatcher
from services.smart_rpa import SmartRPADriver


@pytest.fixture
def planilha_dispatcher(tmp_path: Path) -> Path:
    arquivo = tmp_path / "planilha_exec.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["REG", "CONSULTA", "MÉDICO", "DATA DE VALIDADE", "UNIDADE"])
    ws.append(["111", "CONSULTA", "DR. SILVA", "15092026", "HOSPITAL OFTALMO PE"])
    ws.append(["222", "CONSULTA", "DR. SILVA", "15092026", "HOSPITAL OFTALMO PE"])
    wb.save(arquivo)
    wb.close()
    return arquivo


def test_dispatcher_executa_lote_completo_mock(planilha_dispatcher: Path):
    driver = SmartRPADriver(mock_mode=True)
    dispatcher = BatchDispatcher(driver=driver)

    fila = [
        RegistroPaciente(
            row_index=2,
            reg="111",
            consulta="CONSULTA",
            medico="DR. SILVA",
            unidade="HOSPITAL OFTALMO PE",
            data_validade="15092026",
        ),
        RegistroPaciente(
            row_index=3,
            reg="222",
            consulta="CONSULTA",
            medico="DR. SILVA",
            unidade="HOSPITAL OFTALMO PE",
            data_validade="15092026",
        ),
    ]

    controle_execucao.resetar()
    relatorio = dispatcher.executar_lote(
        caminho_planilha=planilha_dispatcher,
        fila=fila,
        modo_simulacao=True,
    )

    assert relatorio.total_itens == 2
    assert relatorio.total_sucesso == 2
    assert relatorio.total_inconsistencias == 0
    assert relatorio.taxa_sucesso == 100.0


def test_dispatcher_interrupcao_emergencia(planilha_dispatcher: Path):
    driver = SmartRPADriver(mock_mode=True)
    dispatcher = BatchDispatcher(driver=driver)

    fila = [
        RegistroPaciente(
            row_index=2,
            reg="111",
            consulta="CONSULTA",
            medico="DR. SILVA",
            unidade="HOSPITAL OFTALMO PE",
            data_validade="15092026",
        ),
        RegistroPaciente(
            row_index=3,
            reg="222",
            consulta="CONSULTA",
            medico="DR. SILVA",
            unidade="HOSPITAL OFTALMO PE",
            data_validade="15092026",
        ),
    ]

    controle_execucao.resetar()
    controle_execucao.solicitar_parada_imediata("ESC pressionado")

    relatorio = dispatcher.executar_lote(
        caminho_planilha=planilha_dispatcher,
        fila=fila,
        modo_simulacao=True,
    )

    # O loop deve abortar imediatamente na checagem
    assert relatorio.total_sucesso == 0
    assert relatorio.total_inconsistencias >= 1
    assert any(r.interrompido for r in relatorio.resultados)
