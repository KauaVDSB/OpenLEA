#!/usr/bin/env bash
set -e

echo "==============================================================================="
echo "      INSTALADOR OFICIAL 1-CLICK - OPENLEA v1.0.0 (OFTALMOPE TECH)"
echo "==============================================================================="
echo

TARGET_DIR="$HOME/.local/share/oftalmope_tech/openlea"
TARGET_BIN="$TARGET_DIR/OpenLEA"
TARGET_ENV="$TARGET_DIR/.env"
DOWNLOAD_URL="https://sentinel-oftalmope.onrender.com/download/linux/OpenLEA"

echo "[1/4] Preparando diretórios corporativos em: $TARGET_DIR"
mkdir -p "$TARGET_DIR/logs"
mkdir -p "$HOME/.local/share/applications"

echo
echo "[2/4] Baixando binário oficial do Sentinel..."
echo "      URL: $DOWNLOAD_URL"
if command -v curl >/dev/null 2>&1; then
    curl -L -o "$TARGET_BIN" "$DOWNLOAD_URL"
elif command -v wget >/dev/null 2>&1; then
    wget -O "$TARGET_BIN" "$DOWNLOAD_URL"
else
    echo "[ERRO FATAL] curl ou wget não encontrados."
    exit 1
fi

chmod +x "$TARGET_BIN"
echo "      [+] Binário baixado e configurado como executável!"

echo
echo "[3/4] Configurando ambiente corporativo (.env)..."
if [ ! -f "$TARGET_ENV" ]; then
    cat << 'EOF' > "$TARGET_ENV"
# =====================================================================
# OPENLEA - CONFIGURACOES DE AMBIENTE (OFTALMOPE TECH)
# =====================================================================
SENTINEL_API_URL=https://sentinel-oftalmope.onrender.com
SENTINEL_CLIENT_ID=oftalmope_hospital_gus
SENTINEL_LICENSE_KEY=TRIAL-OFTALMOPE-202609
HTTP_TIMEOUT=30
TITULO_MWSUS=PIXEON SMART - PIXEON MEDICAL SYSTEM - Modulo SUS
TITULO_JANELA_LEA=Laudo para Emissao de APAC (LEA) (w_apac)
CID10_PADRAO=H409
MOT_COBR_PADRAO=52
S_APAC_AP_COD_PADRAO=21
EOF
    echo "      [+] Arquivo .env inicializado com sucesso."
else
    echo "      [+] Arquivo .env existente preservado."
fi

echo
echo "[4/4] Criando atalhos no Desktop e Menu de Aplicações..."
DESKTOP_ENTRY="[Desktop Entry]
Version=1.0
Type=Application
Name=OpenLEA
Comment=OpenLEA - OftalmoPE Tech
Exec=$TARGET_BIN
Path=$TARGET_DIR
Terminal=true
Categories=Office;Utility;
"

echo "$DESKTOP_ENTRY" > "$HOME/.local/share/applications/openlea.desktop"
chmod +x "$HOME/.local/share/applications/openlea.desktop"

if [ -d "$HOME/Desktop" ]; then
    echo "$DESKTOP_ENTRY" > "$HOME/Desktop/OpenLEA.desktop"
    chmod +x "$HOME/Desktop/OpenLEA.desktop"
    if command -v gio >/dev/null 2>&1; then
        gio set "$HOME/Desktop/OpenLEA.desktop" metadata::trusted true 2>/dev/null || true
    fi
fi

echo "      [+] Atalhos criados com sucesso!"

echo
echo "==============================================================================="
echo "  INSTALAÇÃO CONCLUÍDA COM SUCESSO!"
echo "  O OpenLEA já pode ser executado diretamente pelo menu ou terminal."
echo "==============================================================================="
