[CmdletBinding()]
param(
    [ValidateSet('timber_run','timber_rally','threepp_showcase','threepp_editor','showpiece','water','tree_demo','forest_demo')]
    [string]$Example = 'timber_run',
    [ValidateRange(5,300)][int]$Seconds = 60,
    [switch]$AcknowledgeIncident,
    [ValidateRange(1,3)][int]$Scene = 1,
    [switch]$Capture,
    [ValidateSet(1,2)][int]$CaptureScale = 1,
    [switch]$Sequence,
    [ValidateRange(0,900)][int]$WarmupFrames = 0,
    [switch]$AutoDrive,
    [switch]$PhysicsAudit,
    [string]$RideReplay = '',
    [ValidateRange(0,899)][int]$ReplayStartFrame = 0,
    [ValidateSet('revised','previous')][string]$SafariRideProfile = 'revised',
    [switch]$WheelInspect,
    [switch]$VehiclePortrait,
    [switch]$PortraitOrbit,
    [ValidateSet('front','side','rear','top','tail','rear-detail','front-detail')][string]$PortraitAngle = 'front',
    [ValidateSet('rear','front')][string]$PortraitLight = 'rear',
    [ValidateSet('forest','daylight')][string]$PortraitEnvironment = 'forest',
    [ValidateSet('default','stock','off')][string]$PortraitShadows = 'default',
    [ValidateSet('buggy','safari')][string]$Vehicle = 'buggy',
    [ValidateRange(0,3)][int]$View = 0,
    [ValidateRange(1,900)][int]$Frames = 90,
    [switch]$SelfTest
)
$ErrorActionPreference = 'Stop'
if ($PhysicsAudit -and ($Example -ne 'timber_rally' -or $Capture -or $Sequence -or $AutoDrive -or $SelfTest)) {
    throw 'PhysicsAudit is a CPU-only timber_rally audit and cannot be combined with graphics capture or driving.'
}
if ($RideReplay) {
    if ($Example -ne 'timber_rally' -or (-not $PhysicsAudit -and (-not $Sequence -or $WarmupFrames -ne 0 -or $VehiclePortrait))) { throw 'Suspension replay requires a CPU audit or native sequence without warmup/portrait.' }
    $RideReplay = (Resolve-Path -LiteralPath $RideReplay).Path
}
if ($ReplayStartFrame -and (-not $RideReplay -or $PhysicsAudit)) { throw 'ReplayStartFrame requires a native suspension replay.' }
if ($SafariRideProfile -eq 'previous' -and (-not $RideReplay -or $Vehicle -ne 'safari')) { throw 'Previous Safari tuning is available only for a matched suspension replay.' }
Set-Location -LiteralPath $PSScriptRoot
. (Join-Path $PSScriptRoot 'scripts/EvaluationHash.ps1')
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
        if ($PhysicsAudit) { $arguments += @('--physics-audit', ('"' + (Join-Path $session 'physics-audit') + '"')) }
        if ($RideReplay) { $arguments += @('--ride-replay', ('"' + $RideReplay + '"'),'--safari-ride-profile',$SafariRideProfile,'--replay-start',[string]$ReplayStartFrame) }
        if ($Sequence -and ($Capture -or $Example -ne 'timber_rally')) { throw 'Sequence recording is supported only for timber_rally, separately from a still capture.' }
        if ($CaptureScale -eq 2) {
            if ($Example -ne 'timber_rally' -or (-not $Capture -and -not $Sequence)) { throw 'The 1920x1200 profile is an explicit rally capture only.' }
            if ($Capture -and ($Frames -ne 1 -or $WarmupFrames -ne 0)) { throw 'The 1920x1200 inspection profile allows one still, without warmup.' }
            if ($Sequence) {
                if (($Frames+$WarmupFrames) -gt 180) { throw 'The 1920x1200 profile allows at most 180 total frames including warmup.' }
                $acceptanceFile=Join-Path $PSScriptRoot 'build/safari-model/whole-vehicle-acceptance.json'
                if ($Vehicle -ne 'safari' -or -not (Test-Path -LiteralPath $acceptanceFile)) { throw 'High-resolution video awaits whole-vehicle Safari acceptance.' }
                $acceptance=Get-Content -LiteralPath $acceptanceFile -Raw | ConvertFrom-Json
                $acceptedAsset=Join-Path $PSScriptRoot 'build/windows-gl/bin/Release/rally-assets/safari-body.glb'
                if ($acceptance.scope -ne 'whole_vehicle' -or $acceptance.overall -lt 8 -or @($acceptance.categoryScores).Count -ne 5 -or @($acceptance.categoryScores | Where-Object { $_ -lt 7 }).Count -gt 0 -or $acceptance.modelSha256 -ne (Get-EvaluationSha256 -LiteralPath $acceptedAsset) -or $acceptance.binarySha256 -ne (Get-EvaluationSha256 -LiteralPath $exe)) { throw 'This model and renderer build have not passed the fixed whole-vehicle visual gate.' }
                $weights=@(.25,.20,.20,.20,.15);$weighted=0.0
                for($i=0;$i -lt 5;$i++){ $weighted += [double]$acceptance.categoryScores[$i]*$weights[$i] }
                if($weighted -lt 8 -or [Math]::Abs($weighted-[double]$acceptance.overall) -gt .11){ throw 'The recorded whole-vehicle score does not meet the weighted quality gate.' }
            }
        }
        if ($Sequence) {
            $sequenceFreeBytes = (Get-PSDrive -Name ([IO.Path]::GetPathRoot($PSScriptRoot).TrimEnd(':\'))).Free
            if ($null -eq $sequenceFreeBytes) { throw 'Cannot verify free disk space in this launcher context; sequence recording was not started.' }
            if ($sequenceFreeBytes -lt 1GB) { throw 'Sequence recording requires at least 1 GiB free disk space.' }
        }
        if ($Capture -and $Example -notin @('threepp_showcase','timber_run','timber_rally','showpiece','tree_demo','forest_demo')) { throw 'This example has no supported supervised capture option.' }
        if ($AutoDrive -and $Example -notin @('timber_run','timber_rally')) { throw 'AutoDrive is available only for the driving demos.' }
        if (($WheelInspect -or $VehiclePortrait) -and ($Example -ne 'timber_rally' -or (-not $Capture -and -not $Sequence))) { throw 'Wheel inspection is an explicit rally capture/sequence profile only.' }
        if ($PortraitEnvironment -ne 'forest' -and -not $VehiclePortrait) { throw 'Daylight inspection environment requires a vehicle portrait capture.' }
        if ($PortraitShadows -ne 'default' -and -not $VehiclePortrait) { throw 'Shadow diagnostic controls require a vehicle portrait capture.' }
        if ($PortraitOrbit -and (-not $VehiclePortrait -or -not $Sequence -or $PortraitAngle -notin @('front','side','rear'))) { throw 'Portrait orbit is a front/side/rear inspection sequence only.' }
        if ($Example -eq 'threepp_showcase') { $arguments += @('--scene', [string]$Scene) }
        if ($Capture) { $arguments += @('--shot', ('"' + (Join-Path $session 'capture.png') + '"'), '--frames', [string]$Frames) }
        if ($CaptureScale -eq 2) { $arguments += @('--capture-scale','2') }
        if ($Sequence) { $arguments += @('--sequence', ('"' + (Join-Path $session 'frames') + '"'), '--frames',[string]$Frames,'--warmup',[string]$WarmupFrames) }
        if ($AutoDrive) { $arguments += '--autodrive' }
        if ($WheelInspect) { $arguments += '--wheel-inspect' }
        if ($VehiclePortrait) { $arguments += @('--portrait','--portrait-angle',$PortraitAngle,'--portrait-light',$PortraitLight,'--portrait-environment',$PortraitEnvironment,'--portrait-shadows',$PortraitShadows) }
        if ($PortraitOrbit) { $arguments += '--portrait-orbit' }
        if ($Example -eq 'timber_rally') { $arguments += @('--view',[string]$View,'--vehicle',$Vehicle) }
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
    $binarySha256=Get-EvaluationSha256 -LiteralPath $exe
    $rideReplaySha256=if($RideReplay){Get-EvaluationSha256 -LiteralPath $RideReplay}else{$null}
    $vehicleAssetSha256=$null
    $vehicleAsset=Join-Path $PSScriptRoot 'build/windows-gl/bin/Release/rally-assets/safari-body.glb'
    if ($Example -eq 'timber_rally' -and $Vehicle -eq 'safari' -and (Test-Path -LiteralPath $vehicleAsset)) { $vehicleAssetSha256=Get-EvaluationSha256 -LiteralPath $vehicleAsset }
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
    @{example=$Example;binarySha256=$binarySha256;vehicleAssetSha256=$vehicleAssetSha256;physicsAudit=[bool]$PhysicsAudit;graphicsStarted=(-not $PhysicsAudit -and -not $SelfTest);rideReplay=$RideReplay;rideReplaySha256=$rideReplaySha256;replayStartFrame=$ReplayStartFrame;safariRideProfile=$SafariRideProfile;scene=$Scene;view=$View;vehicle=$Vehicle;wheelInspect=[bool]$WheelInspect;vehiclePortrait=[bool]$VehiclePortrait;portraitOrbit=[bool]$PortraitOrbit;portraitAngle=$PortraitAngle;portraitLight=$PortraitLight;portraitEnvironment=$PortraitEnvironment;portraitShadows=$PortraitShadows;capture=[bool]$Capture;captureScale=$CaptureScale;renderWidth=(960*$CaptureScale);renderHeight=(600*$CaptureScale);sequence=[bool]$Sequence;requestedFrames=$Frames;warmupFrames=$WarmupFrames;selfTest=[bool]$SelfTest;reason=$reason;exitCode=$child.ExitCode;elapsed=$watch.Elapsed.TotalSeconds;peakObservedWorkingSetBytes=$peakMemory} |
        ConvertTo-Json | Set-Content -LiteralPath (Join-Path $session 'result.json')
    if ($SelfTest) {
        if ($reason -ne 'time limit' -or $watch.Elapsed.TotalSeconds -gt 10) { throw 'Supervisor self-test failed.' }
        Write-Output 'PASS: timeout killed the harmless child through the Windows job; no graphics were started.'
    } elseif (-not $normal) {
        if (-not $PhysicsAudit) { "Evaluation stopped: $reason. See $session. Graphics launches are paused." | Set-Content -LiteralPath $blocked }
        throw "Evaluation stopped: $reason. Logs: $session"
    } else { Write-Output "Evaluation exited cleanly. Logs: $session" }
} catch {
    # Preserve startup failures (including OS application-control blocks), which
    # happen before a child exists and therefore before the normal result file.
    try {
        @{example=$Example;vehicle=$Vehicle;error=$_.Exception.Message;binarySha256=$binarySha256;at=(Get-Date).ToString('o')} |
            ConvertTo-Json | Set-Content -LiteralPath (Join-Path $session 'failure.json')
    } catch { }
    throw
} finally {
    if ($job) { $job.Dispose() }
    if ($child -and -not $child.HasExited) { $child.Kill(); $child.WaitForExit(5000) | Out-Null }
    if (-not $SelfTest -and $locked -and (Test-Path -LiteralPath $active)) {
        if (-not $normal -and -not $PhysicsAudit) { 'The previous evaluation did not exit cleanly. See build/sessions.' | Set-Content -LiteralPath $blocked }
        Remove-Item -LiteralPath $active
    }
    Remove-Item Env:THREEPP_EVALUATION_MODE,Env:THREEPP_EVALUATION_SECONDS,Env:THREEPP_EVALUATION_HEARTBEAT -ErrorAction SilentlyContinue
    if ($locked) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
}
