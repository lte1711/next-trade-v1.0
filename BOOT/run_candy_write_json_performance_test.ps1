#Requires -Version 5.1
# CANDY write_json() Performance Test Runner
# PHASE C: 확인된 Python 경로 기반 실행 스크립트

$ErrorActionPreference = "Stop"

# PATH CONFIG - PHASE A에서 확인된 실제 경로
$projectRoot = "C:\next-trade-ver1.0"
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
$testScript = Join-Path $projectRoot "tools\validation\candy_write_json_performance_test.py"
$logFile = Join-Path $projectRoot "tools\validation\run_candy_write_json_performance_test.log"

# EXECUTION CONFIG
$testName = "CANDY_WRITE_JSON_PERFORMANCE_TEST"
$startTime = Get-Date

Write-Host "=== CANDY Performance Test Runner ===" -ForegroundColor Green
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

# EXECUTION
Write-Host "`n=== Execution ===" -ForegroundColor Yellow

try {
    # Change to project root directory
    Set-Location $projectRoot
    
    # Run the test with confirmed Python path
    $env:PYTHONPATH = "$projectRoot"
    
    Write-Host "Executing: $pythonExe $testScript" -ForegroundColor Cyan
    
    $process = Start-Process -FilePath $pythonExe -ArgumentList $testScript -Wait -PassThru -NoNewWindow
    
    if ($process.ExitCode -eq 0) {
        Write-Host "Test completed successfully" -ForegroundColor Green
        
        # Verify output files
        $outputFiles = @(
            "tools\validation\concurrency_test_result.json",
            "tools\validation\write_latency_report.json", 
            "tools\validation\memory_usage_report.json",
            "tools\validation\integrity_check_report.json",
            "tools\validation\performance_test_complete_result.json"
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
CANDY Performance Test Execution
Test Name: $testName
Start Time: $startTime
End Time: $endTime
Duration: $($duration.TotalSeconds) seconds
Exit Code: $($process.ExitCode)
Python Path: $pythonExe
Test Script: $testScript
========================================
"@

Add-Content -Path $logFile -Value $logEntry -Encoding UTF8

Write-Host "`n=== Test execution completed successfully ===" -ForegroundColor Green
exit 0
