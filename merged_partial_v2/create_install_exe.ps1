$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$TradeRoot = "C:\trade"
$PortableRoot = Join-Path $Root "release\portable"
$InstallerPy = Join-Path $Root "installer_assets\install_from_package.py"
$BuildRoot = Join-Path $Root "release\install_exe_build"
$DistRoot = Join-Path $Root "release\install_exe_dist"
$FinalInstallExe = Join-Path $TradeRoot "install.exe"

if (-not (Test-Path $PortableRoot)) {
    throw "Portable payload directory not found: $PortableRoot"
}

New-Item -ItemType Directory -Force -Path $TradeRoot | Out-Null

if (Test-Path $BuildRoot) {
    Remove-Item -Recurse -Force $BuildRoot
}
if (Test-Path $DistRoot) {
    Remove-Item -Recurse -Force $DistRoot
}
if (Test-Path $FinalInstallExe) {
    Remove-Item -Force $FinalInstallExe
}

python -m PyInstaller `
  --noconfirm `
  --clean `
  --onefile `
  --name install `
  --workpath $BuildRoot `
  --distpath $DistRoot `
  --add-data "$PortableRoot;package_payload" `
  $InstallerPy

 $BuiltInstallExePath = Join-Path $DistRoot "install.exe"
if (-not (Test-Path $BuiltInstallExePath)) {
    throw "Installer exe was not created: $BuiltInstallExePath"
}

Copy-Item -Force $BuiltInstallExePath $FinalInstallExe

if (-not (Test-Path $FinalInstallExe)) {
    throw "Installer exe was not created: $FinalInstallExe"
}

Write-Host ""
Write-Host "Installer exe created:" -ForegroundColor Green
Write-Host "  $FinalInstallExe"
