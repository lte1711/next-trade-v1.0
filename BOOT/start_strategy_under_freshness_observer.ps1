$scriptPath = "C:\next-trade-ver1.0\tools\ops\observe_strategy_under_freshness_constraint.ps1"
Start-Process powershell -ArgumentList @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $scriptPath
) -WindowStyle Hidden
