"""
Módulo Central de Configurações e Constantes Globais - OpenLEA (OftalmoPE Tech).
Implementa resolução canônica de caminhos (ADR-014), mascaramento LGPD (ADR-003)
e conectores para o Admin Hub Sentinel (ADR-004 / ADR-005).
"""

import os
from pathlib import Path
import sys
from dotenv import load_dotenv

# =====================================================================
# RESOLUÇÃO CANÔNICA DE CAMINHOS (ADR-014: Suporte a PyInstaller e Script)
# =====================================================================
if getattr(sys, "frozen", False):
    # Executando empacotado via PyInstaller (.exe / standalone bin)
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    # Executando diretamente como script Python de desenvolvimento
    BASE_DIR = Path(__file__).resolve().parent.parent

# Carrega variáveis de ambiente prioritariamente da pasta canônica
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

# Diretório canônico de logs e filas offline persistentes
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)


# =====================================================================
# CONSTANTES DE METADADOS DA APLICAÇÃO (OpenLEA v1.0.0)
# =====================================================================
APP_NAME = os.getenv("APP_NAME", "OpenLEA")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
DEFAULT_ORG = "OftalmoPE_Tech"


# =====================================================================
# BLINDAGEM LGPD & SANITIZAÇÃO DE DADOS (ADR-003)
# =====================================================================
def mascarar_identificador(identificador: str | int | None) -> str:
    """Mascara o prontuário/registro do paciente para exibição segura em logs e consoles."""
    if not identificador:
        return "***"
    texto = str(identificador).strip()
    if len(texto) <= 3:
        return "***"
    return f"{texto[:2]}***{texto[-1]}"


def mascarar_nome(nome: str | None) -> str:
    """Mascara o nome do paciente exibindo apenas o primeiro nome e a inicial do sobrenome."""
    if not nome or not str(nome).strip():
        return "PACIENTE NÃO IDENTIFICADO"
    partes = str(nome).strip().split()
    if len(partes) == 1:
        return partes[0]
    return f"{partes[0]} {partes[1][0]}***"


def sanitizar_mensagem_erro(motivo: str | None, max_len: int = 250) -> str:
    """Sanitiza e trunca mensagens de erro para evitar quebras em persistência relacional."""
    if not motivo:
        return "Inconsistência não especificada"
    texto = str(motivo).strip().replace("\n", " ").replace("\r", "")
    if len(texto) > max_len:
        return texto[: max_len - 3] + "..."
    return texto


# =====================================================================
# CONFIGURAÇÕES DO ADMIN HUB SENTINEL (SaaS / LICENCIAMENTO / TELEMETRIA)
# =====================================================================
SENTINEL_API_URL = os.getenv("SENTINEL_API_URL", "https://sentinel-oftalmope.onrender.com").rstrip("/")
SENTINEL_CLIENT_ID = os.getenv("SENTINEL_CLIENT_ID", "oftalmope_hospital_gus").strip()
SENTINEL_LICENSE_KEY = os.getenv("SENTINEL_LICENSE_KEY", "TRIAL-OFTALMOPE-202609").strip()
HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "30.0"))

# Arquivos locais persistentes de licença e contingência offline
LICENSE_CACHE_FILE = LOGS_DIR / ".sentinel_license_cache.json"
DEFAULT_TELEMETRY_QUEUE_FILE = LOGS_DIR / ".sentinel_telemetry_queue.json"


# =====================================================================
# CONFIGURAÇÕES DO PIXEON SMART - MÓDULO SUS (MWSUS190 / LEA)
# =====================================================================
TITULO_MWSUS = os.getenv("TITULO_MWSUS", "PIXEON SMART - PIXEON MEDICAL SYSTEM - Módulo SUS")
TITULO_JANELA_LEA = os.getenv("TITULO_JANELA_LEA", "Laudo para Emissão de APAC (LEA) (w_apac)")

# Regra de Segurança Mandatória: ZERO fallback de Unidade.
# A Unidade DEVE vir da linha de cada paciente na planilha ou ser informada pelo operador.
UNIDADE_OBRIGATORIA = True

# Parâmetros SUS Padrão
CID10_PADRAO = os.getenv("CID10_PADRAO", "H409")
MOT_COBR_PADRAO = os.getenv("MOT_COBR_PADRAO", "52")
S_APAC_AP_COD_PADRAO = os.getenv("S_APAC_AP_COD_PADRAO", "21")

# Tempos de Espera e Pausas Operacionais (segundos)
PAUSA_CURTA = float(os.getenv("PAUSA_CURTA", "0.5"))
PAUSA_MEDIA = float(os.getenv("PAUSA_MEDIA", "1.5"))
PAUSA_LONGA = float(os.getenv("PAUSA_LONGA", "3.0"))

# Cores Hexadecimais para Pintura no OpenPyXL (ARGB)
COR_SUCESSO = "FF00B0F0"   # Azul Canônico (Sucesso)
COR_FALHA = "FFFF0000"     # Vermelho (Falha/Erro)
COR_AVISO = "FFFFC000"     # Amarelo (Interrompido/Aviso)
