$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$PortableRoot = Join-Path $Root "release\portable"
$SourceEnv = Join-Path $Root ".env.merged_partial_v2"

if (-not (Test-Path $PortableRoot)) {
    throw "Portable release not found. Run build_v1.ps1 first."
}

$InstallRoot = "C:\tradev1"
if (Test-Path $InstallRoot) {
    Remove-Item -Recurse -Force $InstallRoot
}
New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null
Copy-Item -Recurse -Force (Join-Path $PortableRoot "*") -Destination $InstallRoot

$ExampleEnv = Join-Path $InstallRoot ".env.merged_partial_v2.example"
if (-not (Test-Path $ExampleEnv)) {
    $ExampleEnv = Join-Path $InstallRoot "_internal\.env.merged_partial_v2.example"
}
$ActualEnv = Join-Path $InstallRoot ".env.merged_partial_v2"
if (Test-Path $SourceEnv) {
    Copy-Item -Force $SourceEnv $ActualEnv
}
elseif ((Test-Path $ExampleEnv) -and -not (Test-Path $ActualEnv)) {
    Copy-Item -Force $ExampleEnv $ActualEnv
}

$ExePath = Join-Path $InstallRoot "merged_partial_v2_v1.exe"
$LauncherPath = Join-Path $InstallRoot "Launch Merged Partial V2 v1.bat"
if (-not (Test-Path $ExePath)) {
    throw "Installed executable was not found: $ExePath"
}

$WshShell = New-Object -ComObject WScript.Shell

$DesktopShortcutPath = Join-Path ([Environment]::GetFolderPath("Desktop")) "Merged Partial V2 v1.lnk"
$DesktopShortcut = $WshShell.CreateShortcut($DesktopShortcutPath)
$DesktopShortcut.TargetPath = $(if (Test-Path $LauncherPath) { $LauncherPath } else { $ExePath })
$DesktopShortcut.WorkingDirectory = $InstallRoot
$DesktopShortcut.Description = "Merged Partial V2 v1 Auto Live"
$DesktopShortcut.Save()

$ProgramsDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Merged Partial V2"
New-Item -ItemType Directory -Force -Path $ProgramsDir | Out-Null
$StartMenuShortcutPath = Join-Path $ProgramsDir "Merged Partial V2 v1.lnk"
$StartMenuShortcut = $WshShell.CreateShortcut($StartMenuShortcutPath)
$StartMenuShortcut.TargetPath = $(if (Test-Path $LauncherPath) { $LauncherPath } else { $ExePath })
$StartMenuShortcut.WorkingDirectory = $InstallRoot
$StartMenuShortcut.Description = "Merged Partial V2 v1 Auto Live"
$StartMenuShortcut.Save()

Write-Host ""
Write-Host "Installation complete:" -ForegroundColor Green
Write-Host "  InstallRoot: $InstallRoot"
Write-Host "  Executable:  $ExePath"
if (Test-Path $LauncherPath) {
    Write-Host "  Launcher:    $LauncherPath"
}
Write-Host "  Desktop:     $DesktopShortcutPath"
Write-Host "  Start Menu:  $StartMenuShortcutPath"
Write-Host ""
Write-Host "Next step:"
if (Test-Path $SourceEnv) {
    Write-Host "  1. Existing local credentials were copied into the installed .env file."
    Write-Host "  2. Running the desktop shortcut or merged_partial_v2_v1.exe directly will start the installed auto-live mode."
}
else {
    Write-Host "  1. Edit $ActualEnv and add your role-based Binance testnet keys."
    Write-Host "  2. Running the desktop shortcut or merged_partial_v2_v1.exe directly will start the installed auto-live mode."
}
