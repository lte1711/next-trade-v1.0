$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Windows.Forms

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ZipName = "merged_partial_v2_v1_0_1_portable.zip"
$ZipPath = Join-Path $ScriptRoot $ZipName

if (-not (Test-Path $ZipPath)) {
    throw "Portable package not found: $ZipPath"
}

$StageRoot = Join-Path $env:TEMP "merged_partial_v2_v1_install_stage"
if (Test-Path $StageRoot) {
    Remove-Item -Recurse -Force $StageRoot
}
New-Item -ItemType Directory -Force -Path $StageRoot | Out-Null

Expand-Archive -LiteralPath $ZipPath -DestinationPath $StageRoot -Force

$InstallRoot = "C:\tradev1"
if (Test-Path $InstallRoot) {
    Remove-Item -Recurse -Force $InstallRoot
}
New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null
Copy-Item -Recurse -Force (Join-Path $StageRoot "*") -Destination $InstallRoot

$ExampleEnv = Join-Path $InstallRoot ".env.merged_partial_v2.example"
if (-not (Test-Path $ExampleEnv)) {
    $ExampleEnv = Join-Path $InstallRoot "_internal\.env.merged_partial_v2.example"
}
$ActualEnv = Join-Path $InstallRoot ".env.merged_partial_v2"
if ((Test-Path $ExampleEnv) -and -not (Test-Path $ActualEnv)) {
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

[System.Windows.Forms.MessageBox]::Show(
    "Merged Partial V2 v1.0.1 installation completed.`n`nInstalled to: $InstallRoot",
    "Merged Partial V2 Installer",
    [System.Windows.Forms.MessageBoxButtons]::OK,
    [System.Windows.Forms.MessageBoxIcon]::Information
) | Out-Null
