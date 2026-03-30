$lockFiles = @(
    'C:\next-trade-ver1.0\logs\runtime\watchdog.lock',
    'C:\next-trade-ver1.0\logs\runtime\engine.pid'
)
foreach ($f in $lockFiles) {
    if (Test-Path $f) { Remove-Item $f -Force }
}
