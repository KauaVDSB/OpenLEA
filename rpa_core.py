from pywinauto import Application
import time
from config import TITULO_MWSUS, PAUSA_CURTA, PAUSA_MEDIA, PAUSA_LONGA

def conectar_tela_lea():
    app = Application(backend="uia").connect(title_re=f".*{TITULO_MWSUS}.*", timeout=10)
    janela_lea = app.window(title_re=f".*{TITULO_MWSUS}.*").child_window(title="Laudo para Emissão de APAC (LEA) (w_apac)", control_type="Window")
    janela_lea.wait('visible', timeout=10)
    janela_lea.set_focus()
    return janela_lea

def acionar_fallback_reset(janela_lea):
    """
    Desvia de erros não salvos retornando à tela inicial de forma agressiva.
    """
    janela_lea.set_focus()
    janela_lea.type_keys("{F9 6}{F4}{RIGHT}{ENTER}")
    time.sleep(PAUSA_MEDIA)

def processar_lea_paciente(janela_lea, dados_paciente):
    """
    Executa os passos de preenchimento dinamicamente.
    """
    reg = dados_paciente['reg']
    consulta = dados_paciente['consulta']
    medico_alvo = dados_paciente['medico']
    data_validade = dados_paciente['data_validade']
    
    janela_lea.set_focus()
    
    print(f"Preenchendo o registro: {reg} e buscando (F4)...")
    janela_lea.type_keys(f"{reg}{{F4}}")
    print("Aguardando o carregamento dos dados do paciente no banco...")
    time.sleep(PAUSA_LONGA) 
    janela_lea.type_keys("{F10}")
    time.sleep(PAUSA_MEDIA)
    
    print("Iniciando novo registro (F3)...")
    janela_lea.type_keys("{F3}") 
    time.sleep(1)

    print("Selecionando Unidade...")
    janela_lea.type_keys("{TAB}{TAB}HOSPITAL OFTALMO PE{ENTER}", with_spaces=True)
    time.sleep(1)

    print("Gravando unidade (F5)...")
    janela_lea.type_keys("{F5}")
    time.sleep(1.5) 

    print("Preenchendo Emissão, Solicitante e Consulta...")
    janela_lea.type_keys(f"{data_validade}")
    time.sleep(0.5)
    
    janela_lea.type_keys("{TAB}{TAB}") 
    janela_lea.type_keys(f"{medico_alvo}{{ENTER}}", with_spaces=True)
    time.sleep(0.5)
    
    janela_lea.type_keys("{TAB}{TAB}{TAB}") 
    janela_lea.type_keys(f"{consulta}{{ENTER}}", with_spaces=True)

    print("Gravando (F5) e avançando (F10)...")
    janela_lea.type_keys("{F5}")
    time.sleep(2)
    janela_lea.type_keys("{F10}")
    time.sleep(2)

    print("Preenchendo CID-10...")
    janela_lea.type_keys("H409{TAB}")
    time.sleep(0.5)
    janela_lea.type_keys("{F5}")
    time.sleep(1)

    print("Navegando para a aba APAC...")
    janela_lea.type_keys("{F10 3}")
    time.sleep(1)

    print("Preenchendo dados da APAC...")
    valid_ini = janela_lea.child_window(title="sap_dt_valid_ini", control_type="Edit")
    valid_ini.click_input()
    janela_lea.type_keys(f"{data_validade}")
    time.sleep(0.5)
    
    janela_lea.child_window(title="sap_mot_cobr", control_type="ComboBox").click_input()
    janela_lea.type_keys("52") 
    time.sleep(0.5)
    
    janela_lea.child_window(title="sap_s_apac_ap_cod", control_type="ComboBox").click_input()
    janela_lea.type_keys("21")
    time.sleep(0.5)
    
    janela_lea.child_window(title="sap_dt_ocorr", control_type="Edit").click_input()
    janela_lea.type_keys(f"{data_validade}")
    time.sleep(0.5)
    
    print("Gravando APAC final (F5)...")
    janela_lea.type_keys("{F5}")
    time.sleep(2)

    print("Retornando para a tela inicial de busca (F9 6x, F4)...")
    janela_lea.type_keys("{F9 6}") 
    time.sleep(1)
    janela_lea.type_keys("{F4}")
    time.sleep(1)

    print(f"LEA do paciente {reg} finalizada com sucesso! Pronto para o próximo.")