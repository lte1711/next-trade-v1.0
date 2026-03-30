#Requires -Version 5.1
# CANDY write_json() Same-Path Race Test Runner
# STEP-CANDY-SAME-PATH-RACE-VERIFY-1: 동일 경로 경합 검증

$ErrorActionPreference = "Stop"

# PATH CONFIG - PHASE A에서 확인된 실제 경로
$projectRoot = "C:\next-trade-ver1.0"
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
$testScript = Join-Path $projectRoot "tools\validation\candy_write_json_same_path_race_test.py"
$logFile = Join-Path $projectRoot "tools\validation\same_path_race_test.log"

# EXECUTION CONFIG
$testName = "CANDY_SAME_PATH_RACE_TEST"
$startTime = Get-Date

Write-Host "=== CANDY Same-Path Race Test Runner ===" -ForegroundColor Green
Write-Host "Project Root: $projectRoot"
Write-Host "Python Executable: $pythonExe"
Write-Host "Test Script: $testScript"
Write-Host "Log File: $logFile"

# PRE-EXECUTION CHECKS
Write-Host "`n=== Pre-Execution Checks ===" -ForegroundColor Yellow

if (-not (Test-Path $pythonExe)) {
    Write-Error "Python executable not found: $pythonExe"
    exit 1
}

if (-not (Test-Path $testScript)) {
    Write-Error "Test script not found: $testScript"
    exit 1
}

# Create validation directory if not exists
$validationDir = Join-Path $projectRoot "tools\validation"
if (-not (Test-Path $validationDir)) {
    New-Item -ItemType Directory -Path $validationDir -Force | Out-Null
    Write-Host "Created validation directory: $validationDir"
}

# Clean up any existing target file
$targetFile = Join-Path $projectRoot "tools\validation\same_path_race_target.json"
if (Test-Path $targetFile) {
    Remove-Item $targetFile -Force
    Write-Host "Cleaned existing target file: $targetFile"
}

# EXECUTION
Write-Host "`n=== Execution ===" -ForegroundColor Yellow

try {
    # Change to project root directory
    Set-Location $projectRoot
    
    # Run test with confirmed Python path
    $env:PYTHONPATH = "$projectRoot"
    
    Write-Host "Executing: $pythonExe $testScript" -ForegroundColor Cyan
    
    $process = Start-Process -FilePath $pythonExe -ArgumentList $testScript -Wait -PassThru -NoNewWindow
    
    if ($process.ExitCode -eq 0) {
        Write-Host "Test completed successfully" -ForegroundColor Green
        
        # Verify output files
        $outputFiles = @(
            "tools\validation\same_path_race_test_result.json",
            "tools\validation\same_path_race_test_complete_result.json",
            "tools\validation\same_path_race_test.log"
        )
        
        Write-Host "`n=== Output Files Verification ===" -ForegroundColor Yellow
        $allFilesExist = $true
        
        foreach ($file in $outputFiles) {
            $fullPath = Join-Path $projectRoot $file
            if (Test-Path $fullPath) {
                $size = (Get-Item $fullPath).Length
                Write-Host "✓ $file ($size bytes)" -ForegroundColor Green
            } else {
                Write-Host "✗ $file (MISSING)" -ForegroundColor Red
                $allFilesExist = $false
            }
        }
        
        # Check target file status
        if (Test-Path $targetFile) {
            $targetSize = (Get-Item $targetFile).Length
            Write-Host "✓ Target file exists ($targetSize bytes)" -ForegroundColor Green
        } else {
            Write-Host "✗ Target file missing" -ForegroundColor Red
        }
        
        if ($allFilesExist) {
            Write-Host "`n=== All output files verified ===" -ForegroundColor Green
        } else {
            Write-Host "`n=== Some output files missing ===" -ForegroundColor Red
            exit 1
        }
        
    } else {
        Write-Error "Test failed with exit code: $($process.ExitCode)"
        exit $process.ExitCode
    }
    
} catch {
    Write-Error "Execution failed: $($_.Exception.Message)"
    exit 1
}

# POST-EXECUTION SUMMARY
$endTime = Get-Date
$duration = $endTime - $startTime

Write-Host "`n=== Execution Summary ===" -ForegroundColor Yellow
Write-Host "Start Time: $startTime"
Write-Host "End Time: $endTime"
Write-Host "Duration: $($duration.TotalSeconds) seconds"

# Log the execution
$logEntry = @"
========================================
CANDY Same-Path Race Test Execution
Test Name: $testName
Start Time: $startTime
End Time: $endTime
Duration: $($duration.TotalSeconds) seconds
Exit Code: $($process.ExitCode)
Python Path: $pythonExe
Test Script: $testScript
Target File: $targetFile
========================================
"@

Add-Content -Path $logFile -Value $logEntry -Encoding UTF8

Write-Host "`n=== Same-path race test execution completed ===" -ForegroundColor Green
exit 0
