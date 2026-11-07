[CmdletBinding()]
param([ValidateSet('Check','Snapshot','Preview','Render','AnimationMap')][string]$Stage)
$ErrorActionPreference='Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
$env:PRODUCER_BROWSER_GPU_MODE='software'
$env:PRODUCER_LOW_MEMORY_MODE='true'
$env:PRODUCER_EXPERIMENTAL_FAST_CAPTURE='false'
$taskCandidates=@((Join-Path (Get-Location) 'node_modules/hyperframes'))
$taskNpxCaches=@((Join-Path $env:LOCALAPPDATA 'npm-cache/_npx'),(Join-Path $env:USERPROFILE 'AppData/Local/npm-cache/_npx')) | Select-Object -Unique
foreach($taskNpxCache in $taskNpxCaches){
    if(Test-Path -LiteralPath $taskNpxCache){$taskCandidates+=@(Get-ChildItem -LiteralPath $taskNpxCache -Directory | Sort-Object Name | ForEach-Object {Join-Path $_.FullName 'node_modules/hyperframes'})}
}
$taskPackage=$taskCandidates | Where-Object {
    $taskPackageJson=Join-Path $_ 'package.json'
    (Test-Path -LiteralPath $taskPackageJson) -and ((Get-Content -LiteralPath $taskPackageJson -Raw | ConvertFrom-Json).version -eq '0.9.19')
} | Select-Object -First 1
if(-not $taskPackage){throw 'The pinned local HyperFrames 0.9.19 package is missing. No browser work was started.'}
$taskCli=Join-Path $taskPackage 'bin/hyperframes.mjs'
switch($Stage){
    'Check' {& node $taskCli check --no-browser-gpu --json}
    'Snapshot' {& node $taskCli snapshot --at '0.8,3,5.8,6.2,11,15.8,16.2,18.5,20.8,21.2,25,28.8,29.2,33,36.8,37.2,42.5,45,47.5' --output proof/snapshots --no-end --no-browser-gpu --json}
    'Preview' {& node scripts/preview-review.mjs}
    'Render' {& node $taskCli render --quality looks --fps 30 --workers 1 --no-browser-gpu --low-memory-mode --experimental-fast-capture=false --video-frame-format png --frames-cache-dir .hyperframes/frame-cache --output outputs/La-Catrina-Street-Show.mp4}
    'AnimationMap' {& node $taskCli keyframes . --runtime gsap --json}
}
exit $LASTEXITCODE
