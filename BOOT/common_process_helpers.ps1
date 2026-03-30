function Get-PythonProcessesByCommandPatterns {
    param(
        [string[]]$Patterns
    )

    @(
        Get-CimInstance Win32_Process | Where-Object {
            $proc = $_
            $proc.Name -eq "python.exe" -and
            $proc.CommandLine -ne $null -and
            (
                (@($Patterns | Where-Object { $_.Length -gt 0 -and $proc.CommandLine -like $_ }).Count) -ge 1
            )
        }
    )
}

function Get-RootProcessesFromSet {
    param(
        [array]$Processes
    )

    $pidMap = @{}
    foreach ($proc in @($Processes)) {
        $pidMap[[int]$proc.ProcessId] = $proc
    }

    $roots = @()
    foreach ($proc in @($Processes)) {
        $parent = $null
        if ($pidMap.ContainsKey([int]$proc.ParentProcessId)) {
            $parent = $pidMap[[int]$proc.ParentProcessId]
        }
        if ($null -eq $parent) {
            $roots += $proc
        }
    }
    @($roots)
}

function Get-ProcessChainGroupsFromSet {
    param(
        [array]$Processes
    )

    $processes = @($Processes)
    $pidMap = @{}
    $childrenMap = @{}

    foreach ($proc in $processes) {
        $procPid = [int]$proc.ProcessId
        $parentPid = [int]$proc.ParentProcessId
        $pidMap[$procPid] = $proc
        if (-not $childrenMap.ContainsKey($parentPid)) {
            $childrenMap[$parentPid] = @()
        }
        $childrenMap[$parentPid] += $proc
    }

    $roots = @(Get-RootProcessesFromSet -Processes $processes)
    $groups = @()

    foreach ($root in $roots) {
        $queue = New-Object System.Collections.Queue
        $members = @()
        $queue.Enqueue($root)

        while ($queue.Count -gt 0) {
            $current = $queue.Dequeue()
            $members += $current
            $currentPid = [int]$current.ProcessId
            foreach ($child in @($childrenMap[$currentPid])) {
                $queue.Enqueue($child)
            }
        }

        $groups += [pscustomobject]@{
            RootProcess = $root
            RootProcessId = [int]$root.ProcessId
            Members = @($members)
            MemberPids = @($members | ForEach-Object { [int]$_.ProcessId })
            Count = @($members).Count
        }
    }

    @($groups)
}

function Get-ListenerPidsByPort {
    param(
        [int]$Port
    )

    @(
        Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique
    )
}
