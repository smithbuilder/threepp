[CmdletBinding()]
param(
    [ValidateSet('timber_run','timber_rally','threepp_showcase','threepp_editor','showpiece','water','tree_demo','forest_demo')]
    [string]$Example = 'timber_run',
    [ValidateRange(5,300)][int]$Seconds = 60,
    [switch]$AcknowledgeIncident,
    [ValidateRange(1,3)][int]$Scene = 1,
    [switch]$Capture,
    [switch]$Sequence,
    [ValidateRange(0,900)][int]$WarmupFrames = 0,
    [switch]$AutoDrive,
    [ValidateRange(0,2)][int]$View = 0,
    [ValidateRange(1,900)][int]$Frames = 90,
    [switch]$SelfTest
)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$logRoot = Join-Path $PSScriptRoot 'build\sessions'
New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
$blocked = Join-Path $PSScriptRoot 'build\GRAPHICS_PAUSED.txt'
$trackedPause = Join-Path $PSScriptRoot 'EVALUATION-PAUSED.txt'
$active = Join-Path $PSScriptRoot 'build\evaluation-active.json'
if (-not $SelfTest -and ((Test-Path -LiteralPath $trackedPause) -or (Test-Path -LiteralPath $blocked) -or (Test-Path -LiteralPath $active)) -and -not $AcknowledgeIncident) {
    throw 'Graphics launches are paused after a reported full-system lock. Read SAFETY.md. No demo was started. A deliberate controlled trial requires -AcknowledgeIncident.'
}
$verified = @('threepp_showcase','timber_run','timber_rally','showpiece','tree_demo','forest_demo')
if (-not $SelfTest -and $Example -notin $verified -and -not $AcknowledgeIncident) {
    throw 'This example has not completed the resumed evaluation. Use a validated profile from Explore-Examples.cmd.'
}
if (-not ('ThreeppEvaluationJob' -as [type])) { Add-Type -Path (Join-Path $PSScriptRoot 'scripts\EvaluationJob.cs') }
$mutex = New-Object System.Threading.Mutex($false, 'Local\ThreeppEvaluation-Supervisor')
$locked = $false
$child = $null
$job = $null
$normal = $false
$peakMemory = 0L
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
        if ($Sequence -and ($Capture -or $Example -ne 'timber_rally')) { throw 'Sequence recording is supported only for timber_rally, separately from a still capture.' }
        if ($Sequence) {
            $sequenceFreeBytes = (Get-PSDrive -Name ([IO.Path]::GetPathRoot($PSScriptRoot).TrimEnd(':\'))).Free
            if ($null -eq $sequenceFreeBytes) { throw 'Cannot verify free disk space in this launcher context; sequence recording was not started.' }
            if ($sequenceFreeBytes -lt 1GB) { throw 'Sequence recording requires at least 1 GiB free disk space.' }
        }
        if ($Capture -and $Example -notin @('threepp_showcase','timber_run','timber_rally','showpiece','tree_demo','forest_demo')) { throw 'This example has no supported supervised capture option.' }
        if ($AutoDrive -and $Example -notin @('timber_run','timber_rally')) { throw 'AutoDrive is available only for the driving demos.' }
        if ($Example -eq 'threepp_showcase') { $arguments += @('--scene', [string]$Scene) }
        if ($Capture) { $arguments += @('--shot', ('"' + (Join-Path $session 'capture.png') + '"'), '--frames', [string]$Frames) }
        if ($Sequence) { $arguments += @('--sequence', ('"' + (Join-Path $session 'frames') + '"'), '--frames',[string]$Frames,'--warmup',[string]$WarmupFrames) }
        if ($AutoDrive) { $arguments += '--autodrive' }
        if ($Example -eq 'timber_rally') { $arguments += @('--view',[string]$View) }
        if ($Example -in @('timber_run','timber_rally')) { $arguments += @('--telemetry', ('"' + (Join-Path $session 'drive.json') + '"')) }
        if ($Example -eq 'showpiece') { $arguments += @('--size','960x600','--samples','0','--no-gtao','--no-bloom','--no-outline') }
        if ($Example -in @('tree_demo','forest_demo')) { $arguments += '--gl' }
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
        try { $peakMemory = [Math]::Max($peakMemory, $child.WorkingSet64) } catch { }
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
    if ($Capture -and -not (Test-Path -LiteralPath (Join-Path $session 'capture.png'))) { $reason = 'capture missing' }
    if ($Sequence -and (@(Get-ChildItem -LiteralPath (Join-Path $session 'frames') -Filter 'frame_*.png' -ErrorAction SilentlyContinue).Count -ne $Frames)) { $reason = 'sequence incomplete' }
    $normal = ($reason -eq 'exited' -and $child.ExitCode -eq 0)
    @{example=$Example;scene=$Scene;capture=[bool]$Capture;sequence=[bool]$Sequence;requestedFrames=$Frames;warmupFrames=$WarmupFrames;selfTest=[bool]$SelfTest;reason=$reason;exitCode=$child.ExitCode;elapsed=$watch.Elapsed.TotalSeconds;peakObservedWorkingSetBytes=$peakMemory} |
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
