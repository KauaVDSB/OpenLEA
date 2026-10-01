"""
Pipeline de Compilação Executável Standalone - OpenLEA (OftalmoPE Tech).
Empacota a aplicação em binário hermético para Windows (.exe) e Linux via PyInstaller (ADR-006).
"""

from pathlib import Path
import platform
import subprocess
import sys

BASE_DIR = Path(__file__).resolve().parent
DIST_DIR = BASE_DIR / "dist"
BUILD_DIR = BASE_DIR / "build"

APP_NAME = "OpenLEA"
APP_VERSION = "1.0.0"


def compilar() -> bool:
    """Executa a compilação standalone hermética."""
    is_windows = platform.system().lower() == "windows"
    extensao = ".exe" if is_windows else ""
    nome_saida = f"{APP_NAME}{extensao}"

    print("=" * 80)
    print(f"  BUILD STANDALONE PYINSTALLER - {APP_NAME.upper()} v{APP_VERSION} (OFTALMOPE TECH)")
    print("=" * 80)
    print(f"Sistema Operacional: {platform.system()} ({platform.machine()})")
    print(f"Destino: {DIST_DIR / nome_saida}\n")

    DIST_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--name",
        APP_NAME,
        "--distpath",
        str(DIST_DIR),
        "--workpath",
        str(BUILD_DIR),
        # Hidden imports do ecossistema OftalmoPE Tech
        "--hidden-import",
        "httpx",
        "--hidden-import",
        "dotenv",
        "--hidden-import",
        "openpyxl",
        "--hidden-import",
        "core.colors",
        "--hidden-import",
        "core.config",
        "--hidden-import",
        "core.hotkeys",
        "--hidden-import",
        "database.models",
        "--hidden-import",
        "database.excel_reader",
        "--hidden-import",
        "services.license_client",
        "--hidden-import",
        "services.telemetry_service",
        "--hidden-import",
        "services.heartbeat_service",
        "--hidden-import",
        "services.smart_rpa",
        "--hidden-import",
        "services.dispatcher",
    ]

    if is_windows:
        cmd.extend(["--hidden-import", "pywinauto"])

    arquivo_entrada = BASE_DIR / "main.py"
    cmd.append(str(arquivo_entrada))

    print(f"Executando comando: {' '.join(cmd)}\n")
    resultado = subprocess.run(cmd)

    if resultado.returncode == 0:
        caminho_final = DIST_DIR / nome_saida
        if not is_windows and caminho_final.exists():
            caminho_final.chmod(0o755)

        print("\n" + "=" * 80)
        print("  COMPILAÇÃO CONCLUÍDA COM SUCESSO!")
        print(f"  Executável pronto em: {caminho_final}")
        if caminho_final.exists():
            tamanho_mb = caminho_final.stat().st_size / (1024 * 1024)
            print(f"  Tamanho: {tamanho_mb:.2f} MB")
        print("=" * 80)
        return True
    else:
        print("\n[!] Falha na compilação do executável standalone.")
        return False


if __name__ == "__main__":
    sucesso = compilar()
    sys.exit(0 if sucesso else 1)
