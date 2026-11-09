param([string]$Revision='cinder-unity-r9')
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'));Set-Location $root
$python=Join-Path $env:USERPROFILE 'AppData/Local/Programs/Python/Python311/python.exe'
if(-not(Test-Path $python)){$python=(Get-Command python -ErrorAction Stop).Source}
& $python tools/unity/stage_assets.py;if($LASTEXITCODE -ne 0){throw 'Asset staging failed'}
if(-not(Test-Path build/unity-assets/buggy/model.glb)){& powershell -NoProfile -ExecutionPolicy Bypass -File tools/unity/Run-Cinder.ps1 -Action Kit -Revision $Revision;if($LASTEXITCODE -ne 0){throw 'Authored kit export failed'}}
if(-not(Test-Path build/unity-assets/catrina-far/model.glb)){& powershell -NoProfile -ExecutionPolicy Bypass -File tools/unity/Run-Cinder.ps1 -Action Lods -Revision $Revision;if($LASTEXITCODE -ne 0){throw 'Lowrider density export failed'}}
& $python tools/unity/stage_assets.py;if($LASTEXITCODE -ne 0){throw 'Final staging failed'}
if(-not(Test-Path Unity/Assets/Resources/Cinder/Audio/engine.wav)){& $python tools/unity/make_audio.py;if($LASTEXITCODE -ne 0){throw 'Audio preparation failed'}}
