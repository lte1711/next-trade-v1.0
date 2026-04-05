$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ReleaseRoot = Join-Path $Root "release"
$PortableRoot = Join-Path $ReleaseRoot "portable"
$ZipPath = Join-Path $ReleaseRoot "merged_partial_v2_v1_portable.zip"

if (-not (Test-Path $PortableRoot)) {
    throw "Portable release not found. Run build_v1.ps1 first."
}

if (Test-Path $ZipPath) {
    Remove-Item -Force $ZipPath
}

$PortableItems = Get-ChildItem -Force $PortableRoot
if (-not $PortableItems) {
    throw "Portable release is empty: $PortableRoot"
}

Compress-Archive -Path $PortableItems.FullName -DestinationPath $ZipPath -CompressionLevel Optimal

Write-Host ""
Write-Host "Package complete:" -ForegroundColor Green
Write-Host "  Zip: $ZipPath"
