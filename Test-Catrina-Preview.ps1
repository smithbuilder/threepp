$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
. (Join-Path $PSScriptRoot 'scripts/EvaluationHash.ps1')
$taskStart=Get-Date
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'Run-Evaluation.ps1') -Example catrina_preview -PhysicsAudit -Seconds 60
if($LASTEXITCODE -ne 0){throw 'La Catrina preview CPU audit failed.'}
$taskSession=Get-ChildItem -LiteralPath build/sessions -Directory | Where-Object {$_.LastWriteTime -ge $taskStart.AddSeconds(-1)} | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if(-not $taskSession){throw 'Missing CPU review session.'}
$taskResult=Get-Content -LiteralPath (Join-Path $taskSession.FullName 'result.json') -Raw | ConvertFrom-Json
if($taskResult.example -ne 'catrina_preview' -or -not $taskResult.physicsAudit -or $taskResult.exitCode -ne 0){throw 'CPU review receipt mismatch.'}
@{binarySha256=$taskResult.binarySha256;modelSha256=$taskResult.vehicleAssetSha256;session=$taskSession.FullName;cpuOnly=$true;status='PASS'} | ConvertTo-Json | Set-Content -LiteralPath build/la-catrina/preview-audit.json
