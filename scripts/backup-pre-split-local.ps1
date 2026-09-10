# ============================================================
# Backup PRE-SPLIT - ElDojo (LOCAL Windows)
# Fecha: 2026-08-29
# Objetivo: Copia de seguridad DE LOS REPOS LOCALES antes del split
#           eldojo-mobile + eldojo-backend-api + eldojo (data layer)
# Uso: Ejecutar desde PowerShell como Administrador si hace falta
#      .\scripts\backup-pre-split-local.ps1
# ============================================================

$ErrorActionPreference = "Stop"

$BaseDir = Split-Path -Parent $PSScriptRoot  # carpeta raiz eldojo/
$ProjectsRoot = Split-Path -Parent $BaseDir   # trae_projects/
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$BackupDir = Join-Path $ProjectsRoot "_backups\pre-split-$Timestamp"
$OutputZip = Join-Path $ProjectsRoot "_backups\eldojo-pre-split-$Timestamp.zip"

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "ElDojo - Backup local PRE-SPLIT" -ForegroundColor Cyan
Write-Host "Timestamp: $Timestamp" -ForegroundColor Gray
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# 1) Crear directorios
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputZip) | Out-Null

# 2) Carpetas a resguardar (repos locales, excluye node_modules y .venv para peso)
$Projects = @(
    "eldojo-mobile",
    "eldojo-backend-api",
    "eldojo"
)

foreach ($Project in $Projects) {
    $Source = Join-Path $ProjectsRoot $Project
    if (-not (Test-Path $Source)) {
        Write-Warning "SKIP: No existe $Source"
        continue
    }

    $Dest = Join-Path $BackupDir $Project
    Write-Host "Copiando $Project ..." -ForegroundColor Yellow

    # Robocopia: /MIR espejo, /XD excluye dirs pesados, /NFL /NDL menos ruido, /R:3 /W:2
    $ExcludeDirs = @("node_modules", ".venv", "venv", "dist", ".next", ".expo", "__pycache__")
    $Args = @(
        $Source,
        $Dest,
        "/E",
        "/R:3",
        "/W:2",
        "/NFL",
        "/NDL",
        "/NP"
    )
    foreach ($Excl in $ExcludeDirs) { $Args += "/XD"; $Args += $Excl }

    & robocopy @Args | Out-Null
    $Exit = $LASTEXITCODE
    if ($Exit -ge 8) {
        throw "Robocopy fallo en $Project (exit=$Exit)"
    }
    Write-Host "  OK -> $Dest" -ForegroundColor Green
}

# 3) Snapshot puertos local (no VPS, solo info)
Write-Host ""
Write-Host "Guardando netstat local..." -ForegroundColor Yellow
$NetstatPath = Join-Path $BackupDir "local-netstat.txt"
Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
    Select-Object LocalAddress, LocalPort, OwningProcess, State |
    Sort-Object LocalPort |
    Format-Table -AutoSize |
    Out-File -FilePath $NetstatPath -Encoding UTF8
Write-Host "  OK -> $NetstatPath" -ForegroundColor Green

# 4) Hash md5/sha256 de cada repo (solo .git HEAD para confirmar integridad)
Write-Host ""
Write-Host "Guardando git heads..." -ForegroundColor Yellow
$GitHeadsPath = Join-Path $BackupDir "git-heads.txt"
"Heads locales al momento del backup $(Get-Date -Format o)" | Out-File -FilePath $GitHeadsPath -Encoding UTF8
foreach ($Project in $Projects) {
    $Repo = Join-Path $ProjectsRoot $Project
    if (Test-Path (Join-Path $Repo ".git")) {
        Push-Location $Repo
        $Branch = git branch --show-current
        $Head = git rev-parse HEAD
        $Tag = git tag --points-at HEAD
        Pop-Location
        "$Project | branch=$Branch | head=$Head | tags=$Tag" | Out-File -FilePath $GitHeadsPath -Append -Encoding UTF8
    }
}
Write-Host "  OK -> $GitHeadsPath" -ForegroundColor Green

# 5) Crear ZIP final
Write-Host ""
Write-Host "Comprimiendo backup a ZIP..." -ForegroundColor Yellow
if (Test-Path $OutputZip) { Remove-Item $OutputZip -Force }
Compress-Archive -Path (Join-Path $BackupDir "*") -DestinationPath $OutputZip -CompressionLevel Optimal -Force
$ZipSizeMB = [math]::Round((Get-Item $OutputZip).Length / 1MB, 2)
Write-Host "  OK -> $OutputZip  ($ZipSizeMB MB)" -ForegroundColor Green

Write-Host ""
Write-Host "===========================================" -ForegroundColor Green
Write-Host "Backup local COMPLETADO." -ForegroundColor Green
Write-Host "Taman~o zip: $ZipSizeMB MB" -ForegroundColor Gray
Write-Host "Ruta:       $OutputZip" -ForegroundColor Gray
Write-Host "===========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Recomendacion: Guardar este ZIP en almacenamiento externo / nube." -ForegroundColor Magenta
