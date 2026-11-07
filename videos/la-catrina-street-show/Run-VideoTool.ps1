[CmdletBinding()]
param([ValidateSet('Check','Snapshot','Preview','Render','AnimationMap')][string]$Stage='Check',[ValidateRange(0,60)][int]$LockWaitSeconds=60)
$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
$taskRepo=(Resolve-Path -LiteralPath '../..').Path
if(-not('ThreeppEvaluationJob' -as [type])){Add-Type -Path scripts/EvaluationJob.cs}
$taskProof=Join-Path $PSScriptRoot 'proof'
New-Item -ItemType Directory -Force -Path $taskProof | Out-Null
$taskLog=Join-Path $taskProof ($Stage.ToLower()+'.log')
$taskErrorLog=Join-Path $taskProof ($Stage.ToLower()+'.stderr.log')
$taskGateArguments=@((Join-Path $PSScriptRoot 'verify_render_gate.py'))
if($Stage -in @('Preview','Render')){$taskGateArguments+='--require-checks'}
if($Stage -eq 'Render'){$taskGateArguments+='--require-preview'}
$taskGateOutput=& python @taskGateArguments
if($LASTEXITCODE -ne 0){throw 'Film preflight has not passed. No browser work was started.'}
$taskGate=$taskGateOutput | ConvertFrom-Json
$taskJob=New-Object ThreeppEvaluationJob
$taskMutex=New-Object System.Threading.Mutex($false,'Local\ThreeppEvaluation-Supervisor')
$taskLocked=$false
$taskProcess=$null
$taskStarted=Get-Date
$taskPreviousSupervised=$env:THREEPP_FILM_SUPERVISED
try{
    try{$taskLocked=$taskMutex.WaitOne($LockWaitSeconds*1000)}catch [System.Threading.AbandonedMutexException]{$taskLocked=$true}
    if(-not $taskLocked){throw 'Another supervised evaluation is active. No browser work was started.'}
    if(Test-Path -LiteralPath (Join-Path $taskRepo 'build/evaluation-active.json')){throw 'A native evaluation marker remains present. No browser work was started.'}
    if((Test-Path -LiteralPath (Join-Path $taskRepo 'build/GRAPHICS_PAUSED.txt')) -or (Test-Path -LiteralPath (Join-Path $taskRepo 'EVALUATION-PAUSED.txt'))){throw 'Evaluation is paused. No browser work was started.'}
    $taskStarted=Get-Date
    $taskDeadline=$taskStarted.AddSeconds(300)
    $env:THREEPP_FILM_SUPERVISED='1'
    $taskProcess=Start-Process -FilePath (Get-Command powershell.exe).Source -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $PSScriptRoot 'scripts/VideoTool-Child.ps1'),'-Stage',$Stage) -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput $taskLog -RedirectStandardError $taskErrorLog
    $taskJob.Assign($taskProcess.Handle);$taskProcess.PriorityClass='BelowNormal'
    while(-not $taskProcess.HasExited){
        if((Get-Date) -gt $taskDeadline){throw "$Stage exceeded its 300-second deadline"}
        Start-Sleep -Seconds 1
        $taskProcess.Refresh()
    }
    $taskProcess.WaitForExit()
    if($taskProcess.ExitCode -ne 0){throw "$Stage failed with exit $($taskProcess.ExitCode). Inspect $taskLog and $taskErrorLog"}
    @{stage=$Stage;status='PASS';authoringSha256=$taskGate.authoringSha256;modelSha256=$taskGate.modelSha256;elapsedSeconds=((Get-Date)-$taskStarted).TotalSeconds;browserGpu='software';workers=1;nativeResolution='960x600';fps=30;deadlineSeconds=300;memoryLimitBytesPerProcess=2147483648;mutex='Local\ThreeppEvaluation-Supervisor';maximumLockWaitSeconds=$LockWaitSeconds;markerCheckedAfterLock=$true;stdout=$taskLog;stderr=$taskErrorLog} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskProof ($Stage.ToLower()+'-execution.json'))
    Write-Output "$Stage passed. Logs: $taskLog"
}finally{$env:THREEPP_FILM_SUPERVISED=$taskPreviousSupervised;$taskJob.Dispose();if($taskLocked){$taskMutex.ReleaseMutex()};$taskMutex.Dispose()}
