# External Profit Strategy Bootstrap
# Author: CANDY (data_validation + execution)
# Constitution: NEXT-TRADE v1.2.1
# Purpose: Execute external profit strategy modules

param(
    [string]$ProjectRoot = "C:\next-trade-ver1.0",
    [switch]$Verbose = $false
)

# Script configuration
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# Paths
$ToolsRoot = Join-Path $ProjectRoot "tools"
$ExternalStrategyRoot = Join-Path $ToolsRoot "external_strategy"
$MarketFilterModule = Join-Path $ExternalStrategyRoot "market_filter_module.py"
$SignalQualityGate = Join-Path $ExternalStrategyRoot "signal_quality_gate.py"

# Logging
$LogDir = Join-Path $ProjectRoot "logs"
$BootstrapLogFile = Join-Path $LogDir "external_strategy_bootstrap.log"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    Write-Host $logEntry
    
    # Append to log file
    try {
        Add-Content -Path $BootstrapLogFile -Value $logEntry -ErrorAction SilentlyContinue
    }
    catch {
        Write-Warning "Could not write to log file: $BootstrapLogFile"
    }
}

function Test-Prerequisites {
    Write-Log "Testing prerequisites..."
    
    # Check Python installation
    try {
        $pythonVersion = python --version 2>&1
        Write-Log "Python found: $pythonVersion"
    }
    catch {
        Write-Log "Python not found or not accessible" "ERROR"
        return $false
    }
    
    # Check module files exist
    $requiredFiles = @(
        $MarketFilterModule,
        $SignalQualityGate
    )
    
    foreach ($file in $requiredFiles) {
        if (-not (Test-Path $file)) {
            Write-Log "Required file not found: $file" "ERROR"
            return $false
        }
        Write-Log "Found required file: $file"
    }
    
    # Check log directory exists
    if (-not (Test-Path $LogDir)) {
        Write-Log "Log directory not found: $LogDir" "ERROR"
        return $false
    }
    
    Write-Log "Prerequisites check passed"
    return $true
}

function Invoke-MarketFilter {
    Write-Log "Executing market filter module..."
    
    try {
        $process = Start-Process -FilePath "python" -ArgumentList $MarketFilterModule -Wait -PassThru -NoNewWindow
        $exitCode = $process.ExitCode
        
        if ($exitCode -eq 0) {
            Write-Log "Market filter module completed successfully"
            return $true
        }
        else {
            Write-Log "Market filter module failed with exit code: $exitCode" "ERROR"
            return $false
        }
    }
    catch {
        Write-Log "Error executing market filter module: $_" "ERROR"
        return $false
    }
}

function Invoke-SignalQualityGate {
    Write-Log "Executing signal quality gate module..."
    
    try {
        $process = Start-Process -FilePath "python" -ArgumentList $SignalQualityGate -Wait -PassThru -NoNewWindow
        $exitCode = $process.ExitCode
        
        if ($exitCode -eq 0) {
            Write-Log "Signal quality gate module completed successfully"
            return $true
        }
        else {
            Write-Log "Signal quality gate module failed with exit code: $exitCode" "ERROR"
            return $false
        }
    }
    catch {
        Write-Log "Error executing signal quality gate module: $_" "ERROR"
        return $false
    }
}

function Show-Results {
    Write-Log "Generating execution summary..."
    
    $outputDir = Join-Path $ExternalStrategyRoot "output"
    $marketFilterStatus = Join-Path $outputDir "market_filter_status.json"
    $gateDecisionsLog = Join-Path $outputDir "external_gate_decisions.jsonl"
    $filteredSignalsDir = Join-Path $outputDir "strategy_signals_filtered"
    
    Write-Log "=== EXECUTION SUMMARY ==="
    Write-Log "Project Root: $ProjectRoot"
    Write-Log "External Strategy Root: $ExternalStrategyRoot"
    Write-Log "Output Directory: $outputDir"
    
    if (Test-Path $marketFilterStatus) {
        Write-Log "Market filter status: AVAILABLE"
        try {
            $status = Get-Content $marketFilterStatus | ConvertFrom-Json
            Write-Log "Market decision: $(if ($status.global_allow) { 'ALLOW' } else { 'BLOCK' })"
            Write-Log "Equity: $($status.metrics.equity)"
            Write-Log "Realized PnL: $($status.metrics.realized_pnl)"
            Write-Log "Drawdown: $($status.metrics.drawdown)"
        }
        catch {
            Write-Log "Could not parse market filter status" "WARNING"
        }
    }
    else {
        Write-Log "Market filter status: NOT FOUND" "WARNING"
    }
    
    if (Test-Path $gateDecisionsLog) {
        Write-Log "Gate decisions log: AVAILABLE"
        try {
            $lastDecision = Get-Content $gateDecisionsLog | Select-Object -Last 1 | ConvertFrom-Json
            Write-Log "Last gate decision: $($lastDecision.summary.total_signals) total, $($lastDecision.summary.allowed_signals) allowed, $($lastDecision.summary.blocked_signals) blocked"
        }
        catch {
            Write-Log "Could not parse gate decisions log" "WARNING"
        }
    }
    else {
        Write-Log "Gate decisions log: NOT FOUND" "WARNING"
    }
    
    if (Test-Path $filteredSignalsDir) {
        $filteredCount = (Get-ChildItem $filteredSignalsDir -Filter "*.json").Count
        Write-Log "Filtered signals: $filteredCount files"
    }
    else {
        Write-Log "Filtered signals directory: NOT FOUND" "WARNING"
    }
    
    Write-Log "=== END SUMMARY ==="
}

# Main execution
try {
    Write-Log "Starting External Profit Strategy Bootstrap"
    Write-Log "Project Root: $ProjectRoot"
    
    # Test prerequisites
    if (-not (Test-Prerequisites)) {
        Write-Log "Prerequisites check failed" "ERROR"
        exit 1
    }
    
    # Execute market filter
    if (-not (Invoke-MarketFilter)) {
        Write-Log "Market filter failed" "ERROR"
        exit 2
    }
    
    # Execute signal quality gate
    if (-not (Invoke-SignalQualityGate)) {
        Write-Log "Signal quality gate failed" "ERROR"
        exit 3
    }
    
    # Show results
    Show-Results
    
    Write-Log "External Profit Strategy Bootstrap completed successfully"
    exit 0
}
catch {
    Write-Log "Bootstrap failed with exception: $_" "ERROR"
    exit 99
}
