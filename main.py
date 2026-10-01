"""
Ponto de Entrada Principal - OpenLEA v1.0.0 (OftalmoPE Tech).
Automação Corporativa para Emissão de Laudos de APAC (LEA) no Pixeon SMART (MWSUS190).
Implementa:
- Handshake imediato no boot e Kill-Switch remoto via Admin Hub Sentinel (SaaS-First / SSOT - ADR-004);
- Telemetria de produtividade e ROI 100% Zero PII com fila offline (ADR-003, ADR-008);
- Teclas de atalho para Parada Imediata (ESC) e Parada Suave (P) (ADR-013);
- Validação estrita de Unidade Hospitalar (ZERO fallback);
- Multi-Sheet Session Loop (ADR-010);
- Pintura automatizada no Excel (Azul = Sucesso, Vermelho = Erro, Amarelo = Interrompido).
"""

import logging
from pathlib import Path
import sys
import time
from typing import Optional

from core.colors import (
    BOLD,
    CYAN,
    RESET,
    aviso,
    destaque,
    erro,
    header,
    info,
    sucesso,
)
from core.config import (
    APP_NAME,
    APP_VERSION,
    LOGS_DIR,
    mascarar_identificador,
)
from core.hotkeys import controle_execucao
from database.excel_reader import carregar_fila_pacientes, verificar_colunas
from database.models import RegistroPaciente
from services.dispatcher import BatchDispatcher
from services.heartbeat_service import HeartbeatService
from services.license_client import LicenseClient
from services.smart_rpa import SmartRPADriver
from services.telemetry_service import TelemetryService

# Configuração de auditoria local (logs em arquivo, terminal limpo)
_log_file = LOGS_DIR / "app.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(str(_log_file), encoding="utf-8"),
    ],
)
logger = logging.getLogger("openlea.main")


def exibir_banner():
    """Exibe o cabeçalho oficial do sistema."""
    print("=" * 80)
    print(f"  {header(f'{APP_NAME.upper()} v{APP_VERSION}')} — OFTALMOPE TECH")
    print("  Emissão Automatizada de Laudos APAC (LEA) no Pixeon SMART (MWSUS190)")
    print("=" * 80)


def selecionar_arquivo_planilha() -> Optional[Path]:
    """
    Abre diálogo nativo do Windows para selecionar a planilha.
    Possui fallback automático para entrada via linha de comando se headless.
    """
    if len(sys.argv) > 1 and Path(sys.argv[1]).exists():
        return Path(sys.argv[1]).resolve()

    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        caminho = filedialog.askopenfilename(
            title="Selecione a Planilha de Pacientes (.xlsx)",
            filetypes=[("Planilhas Excel", "*.xlsx"), ("Todos os arquivos", "*.*")],
        )
        root.destroy()
        if caminho:
            return Path(caminho).resolve()
    except Exception:
        pass

    # Fallback para console
    try:
        print("\nInforme o caminho do arquivo de planilha (.xlsx):")
        entrada = input("> ").strip().strip('"').strip("'")
        if entrada and Path(entrada).exists():
            return Path(entrada).resolve()
    except (EOFError, KeyboardInterrupt):
        return None

    return None


def selecionar_modo_operacao() -> bool:
    """
    Prompt seguro de seleção de modo de operação.
    Padrão: Produção Real no Windows (Live), Simulação no Linux.
    Retorna True para Simulação Segura e False para Produção Real.
    """
    if sys.platform != "win32":
        print(aviso("\nAmbiente não-Windows detectado. Operação forçada em MODO SIMULAÇÃO SEGURA."))
        return True

    print(f"\n{BOLD}Selecione o modo de operação:{RESET}")
    print(" [1] Produção Real (Live: Preenchimento automático no MWSUS e pintura da planilha)")
    print(" [2] Simulação Segura (Dry-Run: Validação dos dados e testes sem cliques no MWSUS)")

    try:
        escolha = input("\nEscolha uma opção [1/2] (Padrão: 1): ").strip()
    except (EOFError, KeyboardInterrupt):
        escolha = "1"

    if escolha == "2":
        print(info("MODO ATIVO: SIMULAÇÃO SEGURA (--dry-run)"))
        return True

    print(sucesso("MODO ATIVO: PRODUÇÃO REAL (MWSUS190)"))
    return False


def exibir_resumo_fila(fila: list[RegistroPaciente]):
    """Exibe painel resumido da auditoria prévia da planilha."""
    medicos = sorted(list(set(p.medico for p in fila)))
    unidades = sorted(list(set(p.unidade for p in fila)))
    datas = sorted(list(set(p.data_validade for p in fila)))

    print(f"\n{BOLD}{CYAN}--- RAIO-X DO LOTE CARREGADO ---{RESET}")
    print(f" Total de Pacientes Pendentes: {destaque(str(len(fila)))}")
    print(f" Unidade(s) Identificada(s)  : {', '.join(unidades)}")
    print(f" Médico(s) Solicitante(s)    : {', '.join(medicos)}")
    print(f" Data(s) de Validade         : {', '.join(datas)}")
    print("-" * 50)
    print(" Amostra inicial dos primeiros pacientes:")
    for p in fila[:5]:
        reg_mascarado = mascarar_identificador(p.reg)
        print(f"   • Linha {p.row_index:3d} | Reg: {reg_mascarado} | Unidade: {p.unidade} | Méd: {p.medico[:15]} | Dt: {p.data_validade}")
    if len(fila) > 5:
        print(f"   ... e mais {len(fila) - 5} paciente(s) na fila.")
    print("-" * 50)


def main():
    """Ciclo de vida principal da aplicação OpenLEA."""
    exibir_banner()

    # =========================================================================
    # 1. HANDSHAKE IMEDIATO SENTINEL (SAAS-FIRST / SSOT - ADR-004)
    # Executado na largada absoluta, antes de qualquer operação ou leitura de arquivo.
    # =========================================================================
    print(info("Validando licença corporativa junto ao Admin Hub Sentinel (SaaS-First)..."))
    license_client = LicenseClient()
    autorizado, msg_lic, dados_lic = license_client.verificar_handshake()

    if not autorizado:
        print(erro(f"\n[BLOQUEIO DE LICENÇA / EXECUÇÃO]: {msg_lic}"))
        try:
            input("\nPressione ENTER para encerrar a aplicação...")
        except (EOFError, KeyboardInterrupt):
            pass
        sys.exit(1)

    print(sucesso(f"Licença Autorizada: {msg_lic}"))

    # =========================================================================
    # 2. INICIALIZAÇÃO DE TELEMETRIA E HEARTBEAT EM BACKGROUND
    # =========================================================================
    telemetry_svc = TelemetryService(session_token=license_client.session_token)
    heartbeat_svc = HeartbeatService(
        session_token=license_client.session_token,
        telemetry_service=telemetry_svc,
    )
    heartbeat_svc.start()

    try:
        lote_num = 1
        while True:
            # Checa se o Sentinel enviou suspensão remota via Heartbeat
            seguro, aviso_sentinel = heartbeat_svc.verificar_estado_seguro()
            if not seguro:
                print(erro(f"\n[BLOQUEIO REMOTO SENTINEL] {aviso_sentinel}"))
                break
            elif aviso_sentinel:
                print(aviso(f"\n[AVISO SENTINEL] {aviso_sentinel}"))

            print(f"\n{BOLD}{CYAN}=== PROCESSAMENTO DE LOTE #{lote_num} ==={RESET}")

            print("\nSelecione a planilha Excel de pacientes (.xlsx)...")
            caminho_arquivo = selecionar_arquivo_planilha()

            if not caminho_arquivo:
                if lote_num == 1:
                    print(aviso("Nenhum arquivo selecionado. Encerrando aplicação."))
                    break
                else:
                    print(aviso("Nenhum arquivo selecionado."))
                    try:
                        opcao = input("\nDeseja tentar novamente? [S/N] (Padrão: N): ").strip().upper()
                    except (EOFError, KeyboardInterrupt):
                        opcao = "N"
                    if opcao == "S":
                        continue
                    break

            print(info(f"Arquivo selecionado: {caminho_arquivo.name}"))

            # Validação do cabeçalho da planilha
            colunas_ausentes = verificar_colunas(caminho_arquivo)
            medico_global = None
            data_global = None
            unidade_global = None

            if "medico" in colunas_ausentes:
                print(aviso("\n[ATENÇÃO] A coluna 'MÉDICO' não foi localizada no cabeçalho."))
                try:
                    medico_global = input("Informe o nome EXATO do médico solicitante para o lote: ").strip().upper()
                except (EOFError, KeyboardInterrupt):
                    break

            if "data" in colunas_ausentes:
                print(aviso("\n[ATENÇÃO] A coluna 'DATA DE VALIDADE' não foi localizada no cabeçalho."))
                try:
                    data_global = input("Informe a data de validade para o lote (ddmmaaaa): ").strip().replace("/", "").replace("-", "")
                except (EOFError, KeyboardInterrupt):
                    break

            if "unidade" in colunas_ausentes:
                print(erro("\n[ALERTA DE SEGURANÇA] A coluna 'UNIDADE' não foi localizada no cabeçalho."))
                print(aviso("Para evitar abertura de LEA para o convênio incorreto, NÃO HÁ UNIDADE PADRÃO."))
                try:
                    unidade_global = input("Informe a UNIDADE/CONVÊNIO EXATO para o lote (ex: HOSPITAL OFTALMO PE): ").strip().upper()
                    if not unidade_global:
                        print(erro("Unidade é obrigatória! Operação cancelada para este lote."))
                        continue
                except (EOFError, KeyboardInterrupt):
                    break

            # Carregamento dos pacientes pendentes (sem cor)
            try:
                print(info("Lendo planilha e filtrando pacientes pendentes de emissão..."))
                fila = carregar_fila_pacientes(
                    caminho_arquivo=caminho_arquivo,
                    medico_global=medico_global,
                    data_global=data_global,
                    unidade_global=unidade_global,
                )
            except Exception as e:
                print(erro(f"Erro ao ler a planilha: {e}"))
                continue

            if not fila:
                print(aviso("\nNenhum paciente pendente encontrado na planilha (todos já processados ou lista vazia)."))
                try:
                    cont = input("\nDeseja processar outra planilha? [S/N] (Padrão: N): ").strip().upper()
                except (EOFError, KeyboardInterrupt):
                    cont = "N"
                if cont == "S":
                    lote_num += 1
                    continue
                break

            # Exibe Raio-X do lote
            exibir_resumo_fila(fila)

            # Seleciona modo de operação
            modo_simulacao = selecionar_modo_operacao()

            # Painel de teclas de atalho de interrupção
            print(f"\n{BOLD}{CYAN}--- CONTROLES DE INTERRUPÇÃO E SEGURANÇA ---{RESET}")
            print(f" • Pressione {destaque('[ESC]')} a qualquer momento para {erro('PARADA IMEDIATA DE EMERGÊNCIA')}.")
            print(f" • Pressione {destaque('[ P ]')} a qualquer momento para {aviso('PARADA SUAVE')} (pausa após o paciente atual).")
            print("-" * 50)

            # Inicialização do Driver RPA
            driver = SmartRPADriver(mock_mode=modo_simulacao)

            if not modo_simulacao:
                try:
                    input("\nDeixe o MWSUS aberto na tela principal da LEA (w_apac) e pressione ENTER para iniciar...")
                except (EOFError, KeyboardInterrupt):
                    break

                try:
                    print(info("Conectando à tela do MWSUS190..."))
                    driver.conectar()
                    print(sucesso("Conexão com Pixeon SMART MWSUS190 estabelecida com sucesso!"))
                except Exception as e:
                    print(erro(f"Falha ao conectar ao MWSUS: {e}"))
                    try:
                        tentar_sim = input("\nDeseja executar em modo simulação para teste? [S/N] (Padrão: N): ").strip().upper()
                    except (EOFError, KeyboardInterrupt):
                        tentar_sim = "N"
                    if tentar_sim == "S":
                        modo_simulacao = True
                        driver = SmartRPADriver(mock_mode=True)
                    else:
                        continue

            # Callback de progresso em console
            def callback_progresso(idx: int, total: int, paciente: RegistroPaciente, status_txt: str):
                reg_mask = mascarar_identificador(paciente.reg)
                pct = (idx / total) * 100
                print(f" [{idx:3d}/{total:3d}] ({pct:5.1f}%) Reg: {reg_mask} | Unidade: {paciente.unidade} -> {status_txt}")

            # Inicializa escuta de teclado
            controle_execucao.resetar()
            controle_execucao.iniciar_listener_teclado()

            print(f"\n{BOLD}Iniciando processamento do lote...{RESET}\n")

            dispatcher = BatchDispatcher(
                driver=driver,
                telemetry_service=telemetry_svc,
                callback_progresso=callback_progresso,
            )

            relatorio = dispatcher.executar_lote(
                caminho_planilha=caminho_arquivo,
                fila=fila,
                modo_simulacao=modo_simulacao,
            )

            controle_execucao.parar_listener_teclado()

            # Sumário de Execução
            print(f"\n{BOLD}{CYAN}=== SUMÁRIO DE EXECUÇÃO DO LOTE #{lote_num} ==={RESET}")
            print(f" Arquivo Processado     : {destaque(caminho_arquivo.name)}")
            print(f" Total de Pacientes     : {relatorio.total_itens}")
            print(f" Emitidos com Sucesso   : {sucesso(str(relatorio.total_sucesso))}")
            print(f" Inconsistências/Falhas : {erro(str(relatorio.total_inconsistencias)) if relatorio.total_inconsistencias > 0 else '0'}")
            print(f" Tempo Total de Execução: {relatorio.tempo_execucao_segundos:.1f} segundos")
            tempo_medio = relatorio.tempo_execucao_segundos / relatorio.total_itens if relatorio.total_itens > 0 else 0
            print(f" Tempo Médio por Paciente: {tempo_medio:.1f} segundos")
            print(f" Taxa de Sucesso        : {relatorio.taxa_sucesso:.1f}%")
            print("=" * 80)

            # Pergunta se deseja processar outra planilha
            try:
                continuar = input(f"\n{BOLD}Deseja processar outra planilha nesta sessão? [S/N] (Padrão: N): {RESET}").strip().upper()
            except (EOFError, KeyboardInterrupt):
                continuar = "N"

            if continuar != "S":
                break

            lote_num += 1

    finally:
        heartbeat_svc.stop()

    print(info("\nSessão do OpenLEA finalizada com sucesso. Obrigado!"))
    try:
        input("\nPressione ENTER para fechar a aplicação...")
    except (EOFError, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    main()