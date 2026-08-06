import sys
import tkinter as tk
from tkinter import filedialog
from excel_logger import carregar_fila_pacientes, registrar_status, verificar_colunas
from rpa_core import conectar_tela_lea, processar_lea_paciente, acionar_fallback_reset

def selecionar_arquivo_planilha():
    """Abre uma janela nativa do Windows para selecionar a planilha."""
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True) 
    
    print("Aguardando seleção do arquivo...")
    caminho_arquivo = filedialog.askopenfilename(
        title="Selecione a Planilha de Pacientes (.xlsx)",
        filetypes=[("Planilhas Excel", "*.xlsx"), ("Todos os arquivos", "*.*")]
    )
    root.destroy()
    return caminho_arquivo

def executar_robo():
    print("=== INICIANDO OPENLEA ===")
    
    arquivo_planilha = selecionar_arquivo_planilha()
    
    if not arquivo_planilha:
        print("\n[AVISO] Nenhum arquivo selecionado. Encerrando execução.")
        sys.exit()
        
    print(f"Arquivo selecionado: {arquivo_planilha}")
    
    # 1. Verificação Inteligente da Planilha
    faltam = verificar_colunas(arquivo_planilha)
    medico_global = None
    data_global = None
    
    # Pede entrada manual APENAS se as colunas não existirem
    if "medico" in faltam:
        print("\n[ALERTA] A coluna 'MÉDICO' não foi encontrada na planilha.")
        medico_global = input("Digite o nome EXATO do médico para todo o lote: ").strip().upper()
        
    if "data" in faltam:
        print("\n[ALERTA] A coluna 'DATA' não foi encontrada na planilha.")
        data_global = input("Digite a data para todo o lote (ex: 14082026): ").strip()
    
    print("\nLendo planilha e filtrando pacientes...")
    try:
        fila = carregar_fila_pacientes(arquivo_planilha, medico_global, data_global)
    except Exception as e:
        print(f"\n[ERRO FATAL] Falha ao ler a planilha. Detalhe: {repr(e)}")
        sys.exit()
    
    if not fila:
        print("\nTodos os pacientes já estão coloridos (processados) ou a tabela está vazia.")
        return

    print(f"\nTotal a ser processado (pacientes sem cor): {len(fila)}")
    
    # Pausa de segurança
    input("Deixe o MWSUS aberto na tela principal da LEA e pressione ENTER para conectar...")
    janela_lea = conectar_tela_lea()

    # 2. Motor de Loop
    for paciente in fila:
        print(f"\n[{paciente['row_index']}] INICIANDO | REG: {paciente['reg']} | Médico: {paciente['medico']}")
        try:
            # Roda o RPA
            processar_lea_paciente(janela_lea, paciente)
            
            # Pinta a planilha de Azul
            registrar_status(arquivo_planilha, paciente['row_index'], "sucesso")
            print("[SUCESSO] Logado em AZUL na planilha.")
            
        except Exception as erro:
            print(f"\n[FALHA] Erro detectado no paciente {paciente['reg']}: {repr(erro)}")
            
            # Tenta contornar e resetar a tela
            acionar_fallback_reset(janela_lea)
            
            # Pinta a planilha de Vermelho
            registrar_status(arquivo_planilha, paciente['row_index'], "erro")
            print("[RESET] Sistema reposicionado. Logado em VERMELHO.")

if __name__ == "__main__":
    executar_robo()