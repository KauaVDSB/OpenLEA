"""
Leitor e Pintor de Planilhas Excel - OpenLEA (OftalmoPE Tech).
Processa planilhas com suporte a células mescladas, datas seriais do Excel e pintura OpenPyXL.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import openpyxl
from openpyxl.styles import PatternFill
from openpyxl.utils.datetime import from_excel

from core.config import COR_AVISO, COR_FALHA, COR_SUCESSO
from database.models import RegistroPaciente


def verificar_colunas(caminho_arquivo: str | Path) -> List[str]:
    """
    Verifica a existência das colunas essenciais no cabeçalho (linha 1).
    Retorna lista das colunas ausentes ('medico', 'data', 'unidade').
    """
    wb = openpyxl.load_workbook(caminho_arquivo, data_only=True)
    sheet = wb.active
    headers = [str(cell.value).strip().upper() for cell in sheet[1] if cell.value is not None]
    wb.close()

    faltam = []
    if not any(h in headers for h in ["MÉDICO", "MEDICO"]):
        faltam.append("medico")
    if not any(h in headers for h in ["DATA DE VALIDADE", "VALIDADE", "DATA", "DATA VALIDADE"]):
        faltam.append("data")
    if not any(h in headers for h in ["UNIDADE", "CONVÊNIO", "CONVENIO", "EMPRESA"]):
        faltam.append("unidade")

    return faltam


def carregar_fila_pacientes(
    caminho_arquivo: str | Path,
    medico_global: Optional[str] = None,
    data_global: Optional[str] = None,
    unidade_global: Optional[str] = None,
) -> List[RegistroPaciente]:
    """
    Carrega a lista de pacientes pendentes (sem preenchimento de cor).
    Suporta células mescladas propagando Médico, Data e Unidade linha a linha.
    REGRA DE SEGURANÇA: Zero fallback de unidade. Se ausente, lança ValueError.
    """
    caminho = Path(caminho_arquivo)
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo de planilha não encontrado: {caminho}")

    wb = openpyxl.load_workbook(caminho, data_only=True)
    sheet = wb.active

    # Mapeia colunas do cabeçalho
    headers: Dict[str, int] = {}
    for i, cell in enumerate(sheet[1]):
        if cell.value is not None:
            headers[str(cell.value).strip().upper()] = i

    def _achar_indice(nomes: Tuple[str, ...]) -> Optional[int]:
        for n in nomes:
            if n in headers:
                return headers[n]
        return None

    idx_reg = _achar_indice(("REG", "REGISTRO", "PRONTUARIO", "PRONTUÁRIO"))
    idx_consulta = _achar_indice(("CONSULTA", "PROCEDIMENTO"))
    idx_medico = _achar_indice(("MÉDICO", "MEDICO"))
    idx_data = _achar_indice(("DATA DE VALIDADE", "VALIDADE", "DATA", "DATA VALIDADE"))
    idx_unidade = _achar_indice(("UNIDADE", "CONVÊNIO", "CONVENIO", "EMPRESA"))

    fila: List[RegistroPaciente] = []

    # Memória de arraste para células mescladas ou informadas no início
    ultimo_medico_visto = medico_global
    ultima_data_vista = data_global
    ultima_unidade_vista = unidade_global

    for row_idx, row in enumerate(sheet.iter_rows(min_row=2), start=2):
        if idx_reg is None or row[idx_reg].value is None:
            continue

        celula_reg = row[idx_reg]
        val_reg = str(celula_reg.value).strip()
        if not val_reg:
            continue

        # Se a célula de registro já tiver cor preenchida, o paciente já foi processado
        fill = celula_reg.fill
        if fill and fill.fill_type is not None:
            cor_val = ""
            if fill.start_color:
                cor_val = str(
                    fill.start_color.rgb
                    or fill.start_color.index
                    or getattr(fill.start_color, "value", None)
                    or ""
                ).upper()
            if cor_val not in ("00000000", "FFFFFFFF", "NONE", ""):
                continue

        # 1. Resolução do Médico
        if idx_medico is not None and row[idx_medico].value:
            ultimo_medico_visto = str(row[idx_medico].value).strip().upper()

        # 2. Resolução da Data
        if idx_data is not None and row[idx_data].value:
            val_data = row[idx_data].value
            if isinstance(val_data, datetime):
                ultima_data_vista = val_data.strftime("%d%m%Y")
            elif isinstance(val_data, (int, float)):
                ultima_data_vista = from_excel(val_data).strftime("%d%m%Y")
            else:
                ultima_data_vista = (
                    str(val_data).strip().replace("/", "").replace("-", "")
                )

        # 3. Resolução da Unidade (Lendo da linha de CADA paciente)
        if idx_unidade is not None and row[idx_unidade].value:
            ultima_unidade_vista = str(row[idx_unidade].value).strip().upper()

        # Validações estritas de preenchimento
        if not ultimo_medico_visto:
            wb.close()
            raise ValueError(f"Linha {row_idx}: Médico não identificado. Preencha na planilha.")

        if not ultima_data_vista:
            wb.close()
            raise ValueError(f"Linha {row_idx}: Data de validade não identificada. Preencha na planilha.")

        if not ultima_unidade_vista:
            wb.close()
            raise ValueError(
                f"Linha {row_idx}: Unidade hospitalar não identificada na linha do paciente. "
                "Informe a unidade ou preencha a coluna 'UNIDADE'."
            )

        val_consulta = (
            str(row[idx_consulta].value).strip().upper()
            if idx_consulta is not None and row[idx_consulta].value is not None
            else "CONSULTA"
        )

        registro = RegistroPaciente(
            row_index=row_idx,
            reg=val_reg,
            consulta=val_consulta,
            medico=ultimo_medico_visto,
            unidade=ultima_unidade_vista,
            data_validade=ultima_data_vista,
        )
        fila.append(registro)

    wb.close()
    return fila


def registrar_status(
    caminho_arquivo: str | Path,
    row_index: int,
    status: str,
    max_col: int = 7,
) -> bool:
    """
    Pinta a linha do paciente com a cor de status correspondente:
    - 'sucesso': Azul
    - 'erro' / 'falha': Vermelho
    - 'aviso' / 'interrompido': Amarelo
    """
    caminho = Path(caminho_arquivo)
    if not caminho.exists():
        return False

    if status.lower() == "sucesso":
        cor = COR_SUCESSO
    elif status.lower() in ("erro", "falha"):
        cor = COR_FALHA
    else:
        cor = COR_AVISO

    try:
        wb = openpyxl.load_workbook(caminho)
        sheet = wb.active
        preenchimento = PatternFill(start_color=cor, end_color=cor, fill_type="solid")

        for col in range(1, max_col + 1):
            sheet.cell(row=row_index, column=col).fill = preenchimento

        wb.save(caminho)
        wb.close()
        return True
    except Exception:
        return False
