param(
    [string]$ProjectRoot = "C:\next-trade-ver1.0",
    [string]$Phase9Dir = "C:\next-trade-ver1.0\reports\phase9_alpha_factory",
    [string]$OutDir = "C:\next-trade-ver1.0\reports\phase10_live_alpha_selection"
)

$ErrorActionPreference = "Stop"
$python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$pipeline = "C:\next-trade-ver1.0\BOOT\phase10_live_alpha_selection_pipeline.py"

if (-not (Test-Path $python)) { throw "PROJECT_VENV_PYTHON_NOT_FOUND: $python" }
if (-not (Test-Path $pipeline)) { throw "PHASE10_PIPELINE_NOT_FOUND: $pipeline" }

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
& $python $pipeline --phase9-dir $Phase9Dir --out-dir $OutDir

$summaryPath = Join-Path $OutDir "nt_phase10_honey_summary.txt"
if (Test-Path $summaryPath) {
    Write-Output "PHASE10_SUMMARY_PATH=$summaryPath"
    Get-Content $summaryPath
}



