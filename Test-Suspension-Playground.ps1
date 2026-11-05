[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
# This path returns before creating a window, renderer or audio device. Keep
# signing/building explicit, and retain every previous session as failure evidence.
$lines = & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'Run-Evaluation.ps1') -Example suspension_playground -PhysicsAudit -Seconds 120
$code=$LASTEXITCODE
$lines | Write-Output
if($code){throw 'The vehicle acceptance suite failed. Inspect the reported session; no graphics were started.'}
$sessionLine=@($lines | Where-Object { $_ -match '^Evaluation exited cleanly\. Logs: ' }) | Select-Object -Last 1
if(-not $sessionLine){throw 'The supervisor did not return its result location.'}
$session=$sessionLine -replace '^Evaluation exited cleanly\. Logs: ',''
$result=Get-Content -LiteralPath (Join-Path $session 'physics-audit/result.json') -Raw | ConvertFrom-Json
$execution=Get-Content -LiteralPath (Join-Path $session 'result.json') -Raw | ConvertFrom-Json
if($result.status -ne 'PASS' -or $execution.graphicsStarted){throw 'The expected CPU-only PASS receipt is missing.'}
$receiptDir = Join-Path $PSScriptRoot 'build/suspension-playground'
New-Item -ItemType Directory -Force -Path $receiptDir | Out-Null
Copy-Item -LiteralPath (Join-Path $session 'physics-audit/vehicle-specifications.json') -Destination (Join-Path $receiptDir 'vehicles.json')
@{session=$session;binarySha256=$execution.binarySha256;checks=$result.passed;vehicles=$result.vehicles;stations=$result.stations} |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'build/suspension-playground/latest-audit.json')
Write-Output ("PASS: {0} checks across {1} vehicles and {2} test areas." -f $result.passed,$result.vehicles,$result.stations)
