$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$SpecPath = Join-Path $Root "merged_partial_v2_v1.spec"
$ReleaseRoot = Join-Path $Root "release"
$BuildRoot = Join-Path $ReleaseRoot "build"
$DistRoot = Join-Path $ReleaseRoot "dist"
$PortableRoot = Join-Path $ReleaseRoot "portable"
$LauncherPath = Join-Path $PortableRoot "Launch Merged Partial V2 v1.bat"
$DashboardLauncherPath = Join-Path $PortableRoot "Open Merged Partial V2 Dashboard.bat"

if (Test-Path $BuildRoot) {
    Remove-Item -Recurse -Force $BuildRoot
}
if (Test-Path $DistRoot) {
    Remove-Item -Recurse -Force $DistRoot
}

New-Item -ItemType Directory -Force -Path $BuildRoot | Out-Null
New-Item -ItemType Directory -Force -Path $DistRoot | Out-Null

python -m PyInstaller `
  --noconfirm `
  --clean `
  --workpath $BuildRoot `
  --distpath $DistRoot `
  $SpecPath

$BuiltAppRoot = Join-Path $DistRoot "merged_partial_v2_v1"
if (Test-Path $PortableRoot) {
    Remove-Item -Recurse -Force $PortableRoot
}
Copy-Item -Recurse -Force $BuiltAppRoot $PortableRoot

$LauncherContent = @"
@echo off
setlocal
cd /d "%~dp0"
merged_partial_v2_v1.exe %*
"@
Set-Content -LiteralPath $LauncherPath -Value $LauncherContent -Encoding ASCII

$DashboardLauncherContent = @"
@echo off
setlocal
cd /d "%~dp0"
start http://127.0.0.1:8787
merged_partial_v2_v1.exe --dashboard --dashboard-port 8787
"@
Set-Content -LiteralPath $DashboardLauncherPath -Value $DashboardLauncherContent -Encoding ASCII

Write-Host ""
Write-Host "Build complete:" -ForegroundColor Green
Write-Host "  Dist:      $BuiltAppRoot"
Write-Host "  Portable:  $PortableRoot"
Write-Host "  Launcher:  $LauncherPath"
Write-Host "  Dashboard: $DashboardLauncherPath"
Write-Host "  Installer: $(Join-Path $Root 'install_v1.ps1')"
