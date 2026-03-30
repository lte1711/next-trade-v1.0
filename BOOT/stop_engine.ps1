$targets = Get-CimInstance Win32_Process | Where-Object {
    $_.Name -eq 'python.exe' -and (
        $_.CommandLine -match 'run_multi5_engine\.py' -or
        $_.CommandLine -match 'profitmax_v1_runner\.py'
    )
}
$targets | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
