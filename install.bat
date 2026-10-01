@echo off
setlocal EnableDelayedExpansion
title Instalador 1-Click - OpenLEA (OftalmoPE Tech)

echo ===============================================================================
echo       INSTALADOR OFICIAL 1-CLICK - OPENLEA v1.0.0 (OFTALMOPE TECH)
echo ===============================================================================
echo.

set "TARGET_DIR=%LOCALAPPDATA%\Programs\OftalmoPE_Tech\OpenLEA"
set "TARGET_EXE=%TARGET_DIR%\OpenLEA.exe"
set "TARGET_ENV=%TARGET_DIR%\.env"
set "DESKTOP_DIR=%USERPROFILE%\Desktop"
set "START_MENU_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\OftalmoPE_Tech"
set "DOWNLOAD_URL=https://sentinel-oftalmope.onrender.com/download/windows/OpenLEA"

echo [1/4] Criando diretorios corporativos em:
echo       %TARGET_DIR%
if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"
if not exist "%TARGET_DIR%\logs" mkdir "%TARGET_DIR%\logs"
if not exist "%START_MENU_DIR%" mkdir "%START_MENU_DIR%"

echo.
echo [2/4] Baixando executavel oficial do Sentinel...
echo       URL: %DOWNLOAD_URL%
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('%DOWNLOAD_URL%', '%TARGET_EXE%')"
if not exist "%TARGET_EXE%" (
    echo [ERRO] Falha no download do executavel via PowerShell. Tentando curl...
    curl -L -o "%TARGET_EXE%" "%DOWNLOAD_URL%"
)

if not exist "%TARGET_EXE%" (
    echo [ERRO FATAL] Nao foi possivel baixar o OpenLEA.exe da central Sentinel.
    pause
    exit /b 1
)
echo       [+] Executavel baixado com sucesso!

echo.
echo [3/4] Configurando arquivo de ambiente corporativo (.env)...
if not exist "%TARGET_ENV%" (
    (
        echo # =====================================================================
        echo # OPENLEA - CONFIGURACOES DE AMBIENTE (OFTALMOPE TECH^)
        echo # =====================================================================
        echo SENTINEL_API_URL=https://sentinel-oftalmope.onrender.com
        echo SENTINEL_CLIENT_ID=oftalmope_hospital_gus
        echo SENTINEL_LICENSE_KEY=TRIAL-OFTALMOPE-202609
        echo HTTP_TIMEOUT=30
        echo TITULO_MWSUS=PIXEON SMART - PIXEON MEDICAL SYSTEM - Modulo SUS
        echo TITULO_JANELA_LEA=Laudo para Emissao de APAC (LEA^) (w_apac^)
        echo CID10_PADRAO=H409
        echo MOT_COBR_PADRAO=52
        echo S_APAC_AP_COD_PADRAO=21
    ) > "%TARGET_ENV%"
    echo       [+] Arquivo .env criado com sucesso.
) else (
    echo       [+] Arquivo .env existente preservado.
)

echo.
echo [4/4] Criando atalhos na Area de Trabalho e Menu Iniciar...
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%DESKTOP_DIR%\OpenLEA.lnk'); $s.TargetPath = '%TARGET_EXE%'; $s.WorkingDirectory = '%TARGET_DIR%'; $s.Description = 'OpenLEA - OftalmoPE Tech'; $s.Save()"
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%START_MENU_DIR%\OpenLEA.lnk'); $s.TargetPath = '%TARGET_EXE%'; $s.WorkingDirectory = '%TARGET_DIR%'; $s.Description = 'OpenLEA - OftalmoPE Tech'; $s.Save()"
echo       [+] Atalhos criados com sucesso!

echo.
echo ===============================================================================
echo   INSTALACAO CONCLUIDA COM SUCESSO!
echo   O OpenLEA ja pode ser executado diretamente pelo icone na Area de Trabalho.
echo ===============================================================================
echo.
pause
