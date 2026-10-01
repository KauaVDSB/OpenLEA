<#
.SYNOPSIS
    Instalador 1-Click PowerShell - OpenLEA (OftalmoPE Tech).
.DESCRIPTION
    Instala o OpenLEA no diretório canônico %LOCALAPPDATA%\Programs\OftalmoPE_Tech\OpenLEA,
    baixa o executável standalone do Sentinel Admin Hub e cria atalhos no Desktop e Menu Iniciar.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "      INSTALADOR OFICIAL 1-CLICK - OPENLEA v1.0.0 (OFTALMOPE TECH)            " -ForegroundColor White
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host ""

$TargetDir = Join-Path $env:LOCALAPPDATA "Programs\OftalmoPE_Tech\OpenLEA"
$TargetExe = Join-Path $TargetDir "OpenLEA.exe"
$TargetEnv = Join-Path $TargetDir ".env"
$DesktopDir = [Environment]::GetFolderPath("Desktop")
$StartMenuDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\OftalmoPE_Tech"
$DownloadUrl = "https://sentinel-oftalmope.onrender.com/download/windows/OpenLEA"

Write-Host "[1/4] Preparando diretórios corporativos..." -ForegroundColor Yellow
if (-not (Test-Path $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
if (-not (Test-Path (Join-Path $TargetDir "logs"))) { New-Item -ItemType Directory -Path (Join-Path $TargetDir "logs") -Force | Out-Null }
if (-not (Test-Path $StartMenuDir)) { New-Item -ItemType Directory -Path $StartMenuDir -Force | Out-Null }
Write-Host "      [+] Diretório: $TargetDir" -ForegroundColor Green

Write-Host "`n[2/4] Baixando executável oficial do Sentinel..." -ForegroundColor Yellow
Write-Host "      URL: $DownloadUrl"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Invoke-WebRequest -Uri $DownloadUrl -OutFile $TargetExe -UseBasicParsing
Write-Host "      [+] OpenLEA.exe baixado com sucesso!" -ForegroundColor Green

Write-Host "`n[3/4] Configurando ambiente corporativo (.env)..." -ForegroundColor Yellow
if (-not (Test-Path $TargetEnv)) {
    $EnvContent = @"
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
"@
    Set-Content -Path $TargetEnv -Value $EnvContent -Encoding UTF8
    Write-Host "      [+] Arquivo .env inicializado com sucesso." -ForegroundColor Green
} else {
    Write-Host "      [+] Arquivo .env existente preservado." -ForegroundColor Gray
}

Write-Host "`n[4/4] Criando atalhos na Área de Trabalho e Menu Iniciar..." -ForegroundColor Yellow
$WshShell = New-Object -ComObject WScript.Shell

$ShortcutDesktop = $WshShell.CreateShortcut((Join-Path $DesktopDir "OpenLEA.lnk"))
$ShortcutDesktop.TargetPath = $TargetExe
$ShortcutDesktop.WorkingDirectory = $TargetDir
$ShortcutDesktop.Description = "OpenLEA - OftalmoPE Tech"
$ShortcutDesktop.Save()

$ShortcutStart = $WshShell.CreateShortcut((Join-Path $StartMenuDir "OpenLEA.lnk"))
$ShortcutStart.TargetPath = $TargetExe
$ShortcutStart.WorkingDirectory = $TargetDir
$ShortcutStart.Description = "OpenLEA - OftalmoPE Tech"
$ShortcutStart.Save()

Write-Host "      [+] Atalhos criados com sucesso!" -ForegroundColor Green

Write-Host "`n===============================================================================" -ForegroundColor Cyan
Write-Host "  INSTALAÇÃO CONCLUÍDA COM SUCESSO!" -ForegroundColor Green
Write-Host "  O OpenLEA já pode ser executado diretamente pelo atalho na Área de Trabalho." -ForegroundColor White
Write-Host "===============================================================================`n" -ForegroundColor Cyan
