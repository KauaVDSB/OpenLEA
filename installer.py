"""
Instalador Oficial Corporativo - OpenLEA (OftalmoPE Tech).
Instala a aplicação no caminho padrão corporativo %LOCALAPPDATA% (Windows) ou XDG (Linux),
cria atalhos na Área de Trabalho e Menu Iniciar, e baixa a versão oficial do Sentinel se necessário (ADR-007).
"""

import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import urllib.request

APP_NAME = "OpenLEA"
APP_VERSION = "1.0.0"
DEFAULT_ORG = "OftalmoPE_Tech"

# Credenciais e parâmetros padrão corporativos
DEFAULT_ENV_CONTENT = (
    "# =====================================================================\n"
    f"# {APP_NAME.upper()} - CONFIGURAÇÕES DE AMBIENTE (OFTALMOPE TECH)\n"
    "# =====================================================================\n"
    "SENTINEL_API_URL=https://sentinel-oftalmope.onrender.com\n"
    "SENTINEL_CLIENT_ID=oftalmope_hospital_gus\n"
    "SENTINEL_LICENSE_KEY=TRIAL-OFTALMOPE-202609\n"
    "HTTP_TIMEOUT=30\n"
    "TITULO_MWSUS=PIXEON SMART - PIXEON MEDICAL SYSTEM - Módulo SUS\n"
    "TITULO_JANELA_LEA=Laudo para Emissão de APAC (LEA) (w_apac)\n"
    "CID10_PADRAO=H409\n"
    "MOT_COBR_PADRAO=52\n"
    "S_APAC_AP_COD_PADRAO=21\n"
)


def obter_diretorio_instalacao_padrao() -> Path:
    """Retorna o caminho per-user corporativo (%LOCALAPPDATA%\\Programs\\OftalmoPE_Tech\\<App> ou XDG no Linux)."""
    if platform.system().lower() == "windows":
        local_app_data = os.getenv("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "Programs" / DEFAULT_ORG / APP_NAME
        return Path.home() / "AppData" / "Local" / "Programs" / DEFAULT_ORG / APP_NAME
    # Padrão XDG para Linux
    return Path.home() / ".local" / "share" / DEFAULT_ORG.lower() / APP_NAME.lower()


def obter_caminho_executavel_instalado() -> Path:
    """Retorna o caminho canônico do executável dentro da pasta de instalação."""
    pasta = obter_diretorio_instalacao_padrao()
    extensao = ".exe" if platform.system().lower() == "windows" else ""
    return pasta / f"{APP_NAME}{extensao}"


def criar_atalhos_windows(destino_exe: Path, destino_app: Path) -> tuple[bool, bool]:
    """Cria atalhos .lnk na Área de Trabalho e Menu Iniciar no Windows."""
    desktop_sucesso = False
    menu_sucesso = False

    desktop_dir = Path.home() / "Desktop"
    appdata_roaming = os.getenv("APPDATA")
    start_menu_dir = (
        Path(appdata_roaming) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / DEFAULT_ORG
        if appdata_roaming
        else None
    )

    def _criar_shortcut(atalho_path: Path) -> bool:
        vbs_script = f"""
Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{atalho_path}"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "{destino_exe}"
oLink.WorkingDirectory = "{destino_app}"
oLink.Description = "Sistema {APP_NAME} - OftalmoPE Tech"
oLink.Save
"""
        vbs_temp = destino_app / f"create_shortcut_{atalho_path.stem}.vbs"
        try:
            vbs_temp.write_text(vbs_script, encoding="utf-8")
            subprocess.run(["cscript", "//Nologo", str(vbs_temp)], check=True, capture_output=True)
            vbs_temp.unlink(missing_ok=True)
            return True
        except Exception:
            vbs_temp.unlink(missing_ok=True)
            return False

    if desktop_dir.exists():
        atalho_desktop = desktop_dir / f"{APP_NAME}.lnk"
        desktop_sucesso = _criar_shortcut(atalho_desktop)

    if start_menu_dir:
        start_menu_dir.mkdir(parents=True, exist_ok=True)
        atalho_menu = start_menu_dir / f"{APP_NAME}.lnk"
        menu_sucesso = _criar_shortcut(atalho_menu)

    return desktop_sucesso, menu_sucesso


def criar_atalhos_linux(destino_exe: Path, destino_app: Path) -> tuple[bool, bool]:
    """Cria atalhos .desktop na Área de Trabalho e Menu XDG no Linux."""
    conteudo_desktop = (
        "[Desktop Entry]\n"
        "Version=1.0\n"
        "Type=Application\n"
        f"Name={APP_NAME}\n"
        f"Comment=Sistema {APP_NAME} - OftalmoPE Tech\n"
        f"Exec={destino_exe}\n"
        f"Path={destino_app}\n"
        "Terminal=true\n"
        "Categories=Office;Utility;\n"
    )

    desktop_sucesso = False
    menu_sucesso = False

    desktop_dir = Path.home() / "Desktop"
    if desktop_dir.exists():
        atalho_desktop = desktop_dir / f"{APP_NAME}.desktop"
        try:
            atalho_desktop.write_text(conteudo_desktop, encoding="utf-8")
            atalho_desktop.chmod(0o755)
            try:
                subprocess.run(["gio", "set", str(atalho_desktop), "metadata::trusted", "true"], check=False, capture_output=True)
            except Exception:
                pass
            desktop_sucesso = True
        except Exception:
            pass

    apps_dir = Path.home() / ".local" / "share" / "applications"
    try:
        apps_dir.mkdir(parents=True, exist_ok=True)
        atalho_menu = apps_dir / f"{APP_NAME.lower()}.desktop"
        atalho_menu.write_text(conteudo_desktop, encoding="utf-8")
        atalho_menu.chmod(0o755)
        menu_sucesso = True
    except Exception:
        pass

    return desktop_sucesso, menu_sucesso


def executar_instalacao(
    origem_exe: Path | None = None,
    destino_customizado: Path | None = None,
    criar_atalhos: bool = True,
) -> bool:
    """Executa o fluxo completo de instalação corporativa."""
    destino_app = destino_customizado or obter_diretorio_instalacao_padrao()
    logs_dir = destino_app / "logs"
    env_file = destino_app / ".env"

    is_windows = platform.system().lower() == "windows"
    ext = ".exe" if is_windows else ""
    nome_binario = f"{APP_NAME}{ext}"
    destino_exe = destino_app / nome_binario

    print("=" * 80)
    print(f"  INSTALADOR OFICIAL - {APP_NAME.upper()} v{APP_VERSION} (OFTALMOPE TECH)")
    print("=" * 80)
    print(f"Diretorio de Instalacao: {destino_app}\n")

    destino_app.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    exe_origem_final: Path | None = None
    if origem_exe and origem_exe.exists():
        exe_origem_final = origem_exe
    else:
        candidatos = [
            Path.cwd() / nome_binario,
            Path.cwd() / "dist" / nome_binario,
            Path.home() / "Downloads" / nome_binario,
        ]
        for c in candidatos:
            if c.exists() and c.is_file():
                exe_origem_final = c
                break

    if exe_origem_final and exe_origem_final.resolve() != destino_exe.resolve():
        print(f"-> Copiando executavel de: {exe_origem_final} ...")
        shutil.copy2(exe_origem_final, destino_exe)
        if not is_windows:
            try:
                destino_exe.chmod(0o755)
            except Exception:
                pass
        print(f"   [+] Executavel configurado em: {destino_exe}")
    elif not destino_exe.exists():
        print("-> Binario local nao encontrado. Baixando versao oficial do Sentinel...")
        plataforma_rota = "windows" if is_windows else "linux"
        url_download = f"https://sentinel-oftalmope.onrender.com/download/{plataforma_rota}/{APP_NAME}"
        try:
            urllib.request.urlretrieve(url_download, destino_exe)
            if not is_windows:
                try:
                    destino_exe.chmod(0o755)
                except Exception:
                    pass
            print("   [+] Download concluido com sucesso!")
        except Exception as e:
            print(f"   [!] Erro ao baixar da central: {e}")
            return False

    if not env_file.exists():
        print("-> Inicializando arquivo corporativo (.env)...")
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(DEFAULT_ENV_CONTENT)
        print("   [+] Arquivo .env criado com sucesso.")
    else:
        print("-> Arquivo .env existente preservado.")

    if criar_atalhos:
        if is_windows:
            print("-> Criando atalhos oficiais no Windows...")
            d_ok, m_ok = criar_atalhos_windows(destino_exe, destino_app)
            if d_ok:
                print("   [+] Atalho criado na Area de Trabalho com sucesso.")
            if m_ok:
                print("   [+] Atalho criado no Menu Iniciar com sucesso.")
        else:
            print("-> Criando atalhos oficiais no Linux (XDG .desktop)...")
            d_ok, m_ok = criar_atalhos_linux(destino_exe, destino_app)
            if d_ok:
                print("   [+] Atalho criado na Area de Trabalho com sucesso.")
            if m_ok:
                print("   [+] Atalho criado no Menu de Aplicacoes com sucesso.")

    print("\n" + "=" * 80)
    print("  INSTALACAO CONCLUIDA COM SUCESSO!")
    print(f"  Aplicativo pronto em: {destino_exe}")
    print("=" * 80)
    return True


if __name__ == "__main__":
    sucesso = executar_instalacao()
    if platform.system().lower() == "windows":
        input("\nPressione ENTER para concluir o instalador...")
    sys.exit(0 if sucesso else 1)
