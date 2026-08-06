import openpyxl
from openpyxl.styles import PatternFill
from openpyxl.utils.datetime import from_excel
import datetime
from config import COR_SUCESSO, COR_FALHA

def verificar_colunas(caminho_arquivo):
    """Verifica se as colunas essenciais existem no cabeçalho."""
    wb = openpyxl.load_workbook(caminho_arquivo, data_only=True)
    sheet = wb.active
    headers = [str(cell.value).strip().upper() for cell in sheet[1] if cell.value]
    wb.close()
    
    faltam = []
    if "MÉDICO" not in headers and "MEDICO" not in headers:
        faltam.append("medico")
    if not any(h in headers for h in ["DATA DE VALIDADE", "VALIDADE", "DATA", "DATA VALIDADE"]):
        faltam.append("data")
    return faltam

def carregar_fila_pacientes(caminho_arquivo, medico_global=None, data_global=None):
    """Retorna uma fila de pacientes não processados, arrastando Médico e Data para células mescladas."""
    wb = openpyxl.load_workbook(caminho_arquivo, data_only=True)
    sheet = wb.active
    
    headers = {str(cell.value).strip().upper(): i for i, cell in enumerate(sheet[1]) if cell.value}
    
    idx_reg = headers.get("REG")
    idx_consulta = headers.get("CONSULTA")
    idx_medico = headers.get("MÉDICO", headers.get("MEDICO"))
    idx_data = headers.get("DATA DE VALIDADE") or headers.get("VALIDADE") or headers.get("DATA")
    
    fila = []
    
    # Memória de arraste para células mescladas
    ultimo_medico_visto = medico_global
    ultima_data_vista = data_global
    
    for row_idx, row in enumerate(sheet.iter_rows(min_row=2), start=2):
        if idx_reg is None or not row[idx_reg].value: 
            continue # Pula linhas vazias
            
        celula_reg = row[idx_reg]
        
        # LÓGICA DO LOG: Se tem cor, o paciente já foi processado (pula)
        fill = celula_reg.fill
        if fill and fill.start_color and fill.start_color.index != "00000000":
            continue 
            
        # Atualiza a memória do Médico se a célula atual não estiver vazia
        if idx_medico is not None and row[idx_medico].value:
            ultimo_medico_visto = str(row[idx_medico].value).strip().upper()
            
        # Atualiza a memória da Data se a célula atual não estiver vazia
        if idx_data is not None and row[idx_data].value:
            val = row[idx_data].value
            if isinstance(val, datetime.datetime):
                ultima_data_vista = val.strftime("%d%m%Y")
            elif isinstance(val, (int, float)):
                # Converte o número de série de data do Excel
                ultima_data_vista = from_excel(val).strftime("%d%m%Y")
            else:
                ultima_data_vista = str(val).strip().replace("/", "").replace("-", "")
                
        if not ultimo_medico_visto or not ultima_data_vista:
            raise ValueError(f"Linha {row_idx} sem Médico ou Data. Preencha na planilha.")
            
        fila.append({
            "row_index": row_idx,
            "reg": str(celula_reg.value).strip(),
            "consulta": str(row[idx_consulta].value).strip() if idx_consulta is not None else "",
            "medico": ultimo_medico_visto,
            "data_validade": ultima_data_vista
        })
            
    wb.close()
    return fila

def registrar_status(caminho_arquivo, row_index, status):
    """Pinta a linha inteira de Azul (Sucesso) ou Vermelho (Falha)."""
    wb = openpyxl.load_workbook(caminho_arquivo)
    sheet = wb.active
    
    cor = COR_SUCESSO if status == "sucesso" else COR_FALHA
    preenchimento = PatternFill(start_color=cor, end_color=cor, fill_type="solid")
    
    # Pinta as colunas A até F da linha do paciente
    for cell in sheet.iter_cols(min_col=1, max_col=6, min_row=row_index, max_row=row_index):
        cell[0].fill = preenchimento
        
    wb.save(caminho_arquivo)
    wb.close()