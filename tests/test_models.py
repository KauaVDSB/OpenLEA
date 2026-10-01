import pytest
from database.models import RegistroPaciente, ResultadoItem, RelatorioLote


def test_registro_paciente_unidade_obrigatoria():
    # Deve instanciar normalmente com unidade preenchida
    p = RegistroPaciente(
        row_index=2,
        reg="12345",
        consulta="CONSULTA",
        medico="DR. FULANO",
        unidade="HOSPITAL OFTALMO PE",
        data_validade="14082026",
    )
    assert p.reg == "12345"
    assert p.unidade == "HOSPITAL OFTALMO PE"

    # Deve falhar expressamente se a unidade estiver vazia (ZERO fallback)
    with pytest.raises(ValueError, match="Unidade hospitalar é obrigatória"):
        RegistroPaciente(
            row_index=3,
            reg="67890",
            consulta="CONSULTA",
            medico="DR. FULANO",
            unidade="",
            data_validade="14082026",
        )


def test_relatorio_lote_metricas():
    rel = RelatorioLote(
        total_itens=10,
        total_sucesso=8,
        total_inconsistencias=2,
        tempo_execucao_segundos=40.0,
        modo_simulacao=True,
    )
    assert rel.taxa_sucesso == 80.0
    assert rel.taxa_sucesso_percentual == 80.0
    assert rel.modo_simulacao is True
