[CmdletBinding()]
param(
    [ValidateSet('timber_run','threepp_showcase','threepp_editor','showpiece','water','tree_demo','forest_demo')]
    [string]$Example = 'timber_run',
    [ValidateRange(5,300)][int]$Seconds = 60,
    [switch]$AcknowledgeIncident,
    [switch]$SelfTest
)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$logRoot = Join-Path $PSScriptRoot 'build\sessions'
New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
$blocked = Join-Path $PSScriptRoot 'build\GRAPHICS_PAUSED.txt'
$active = Join-Path $PSScriptRoot 'build\evaluation-active.json'
if (-not $SelfTest -and ((Test-Path -LiteralPath $blocked) -or (Test-Path -LiteralPath $active)) -and -not $AcknowledgeIncident) {
    throw 'Graphics launches are paused after a reported full-system lock. Read SAFETY.md. No demo was started. A deliberate controlled trial requires -AcknowledgeIncident.'
}
if (-not ('ThreeppEvaluationJob' -as [type])) { Add-Type -Path (Join-Path $PSScriptRoot 'scripts\EvaluationJob.cs') }
$mutex = New-Object System.Threading.Mutex($false, 'Local\ThreeppEvaluation-Supervisor')
$locked = $false
$child = $null
$job = $null
$normal = $false
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
$session = Join-Path $logRoot $stamp
New-Item -ItemType Directory -Path $session -Force | Out-Null
$heartbeat = Join-Path $session 'heartbeat.txt'
$watch = [Diagnostics.Stopwatch]::StartNew()
try {
    try { $locked = $mutex.WaitOne(0) } catch [System.Threading.AbandonedMutexException] { $locked = $true }
    if (-not $locked) { throw 'Another evaluation is running. Close it first.' }
    $job = New-Object ThreeppEvaluationJob
    if ($SelfTest) {
        # Harmless CPU-only child. Exercises the SAME timeout and job cleanup.
        $exe = (Get-Command powershell.exe).Source
        $arguments = @('-NoProfile','-NonInteractive','-Command','Start-Sleep -Seconds 30')
        $deadline = 2
    } else {
        $exe = Join-Path $PSScriptRoot "build\windows-gl\bin\Release\$Example.exe"
        if (-not (Test-Path -LiteralPath $exe)) { throw 'Build the evaluation first with Build-Playground.ps1.' }
        $arguments = @()
        if ($Example -in @('tree_demo','forest_demo')) { $arguments = @('--gl') }
        $deadline = $Seconds + 5
        $env:THREEPP_EVALUATION_MODE = '1'
        $env:THREEPP_EVALUATION_SECONDS = [string]$Seconds
        $env:THREEPP_EVALUATION_HEARTBEAT = $heartbeat
        @{example=$Example;started=(Get-Date).ToString('o');seconds=$Seconds;supervisor=$PID} |
            ConvertTo-Json | Set-Content -LiteralPath $active
    }
    $launch = @{FilePath=$exe;WorkingDirectory=$PSScriptRoot;WindowStyle='Hidden';PassThru=$true;
        RedirectStandardOutput=(Join-Path $session 'stdout.log');RedirectStandardError=(Join-Path $session 'stderr.log')}
    if ($arguments.Count) { $launch.ArgumentList = $arguments }
    $child = Start-Process @launch
    $job.Assign($child.Handle)
    $child.PriorityClass = 'BelowNormal'
    $reason = 'exited'
    while (-not $child.HasExited) {
        if ($watch.Elapsed.TotalSeconds -ge $deadline) { $reason='time limit'; break }
        if (-not $SelfTest) {
            if ((Test-Path -LiteralPath $heartbeat)) {
                if (((Get-Date) - (Get-Item -LiteralPath $heartbeat).LastWriteTime).TotalSeconds -gt 8) { $reason='heartbeat stalled'; break }
            } elseif ($watch.Elapsed.TotalSeconds -gt 20) { $reason='startup heartbeat missing'; break }
        }
        Start-Sleep -Milliseconds 250
        $child.Refresh()
    }
    $job.Dispose(); $job=$null
    if (-not $child.WaitForExit(5000)) { throw 'The supervised child did not terminate.' }
    $normal = ($reason -eq 'exited' -and $child.ExitCode -eq 0)
    @{example=$Example;selfTest=[bool]$SelfTest;reason=$reason;exitCode=$child.ExitCode;elapsed=$watch.Elapsed.TotalSeconds} |
        ConvertTo-Json | Set-Content -LiteralPath (Join-Path $session 'result.json')
    if ($SelfTest) {
        if ($reason -ne 'time limit' -or $watch.Elapsed.TotalSeconds -gt 10) { throw 'Supervisor self-test failed.' }
        Write-Output 'PASS: timeout killed the harmless child through the Windows job; no graphics were started.'
    } elseif (-not $normal) {
        "Evaluation stopped: $reason. See $session. Graphics launches are paused." | Set-Content -LiteralPath $blocked
        throw "Evaluation stopped: $reason. Logs: $session"
    } else { Write-Output "Evaluation exited cleanly. Logs: $session" }
} finally {
    if ($job) { $job.Dispose() }
    if ($child -and -not $child.HasExited) { $child.Kill(); $child.WaitForExit(5000) | Out-Null }
    if (-not $SelfTest -and $locked -and (Test-Path -LiteralPath $active)) {
        if (-not $normal) { 'The previous evaluation did not exit cleanly. See build/sessions.' | Set-Content -LiteralPath $blocked }
        Remove-Item -LiteralPath $active
    }
    Remove-Item Env:THREEPP_EVALUATION_MODE,Env:THREEPP_EVALUATION_SECONDS,Env:THREEPP_EVALUATION_HEARTBEAT -ErrorAction SilentlyContinue
    if ($locked) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
}
