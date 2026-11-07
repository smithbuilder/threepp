[CmdletBinding()]
param([switch]$BakeCavities)
$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
$catPython=(Get-Command python.exe -ErrorAction Stop).Source
$catCmake='C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
& $catPython -X utf8 scripts/catrina_generate.py
if($LASTEXITCODE){throw 'La Catrina model generation failed'}
if($BakeCavities){
    & powershell -NoProfile -ExecutionPolicy Bypass -File scripts/Bake-Catrina-AO.ps1
    if($LASTEXITCODE){throw 'La Catrina cavity shading failed'}
}
& $catPython -X utf8 scripts/catrina_audit.py
if($LASTEXITCODE){throw 'La Catrina model checks failed'}
& $catCmake --build build/windows-gl --config Release --target suspension_playground catrina_preview --parallel 2 -- /nodeReuse:false
if($LASTEXITCODE){throw 'Vehicle playground build failed'}
Copy-Item -LiteralPath showcase/assets/la-catrina.glb -Destination build/windows-gl/bin/Release/playground-assets/la-catrina.glb
Copy-Item -LiteralPath showcase/assets/la-catrina.glb -Destination build/windows-gl/bin/Release/catrina-assets/la-catrina.glb
$catSigner=Join-Path $env:USERPROFILE 'Projects/patcher/scripts/sign-windows.ps1'
& powershell -NoProfile -ExecutionPolicy Bypass -File $catSigner -Executable (Join-Path $PSScriptRoot 'build/windows-gl/bin/Release/suspension_playground.exe')
if($LASTEXITCODE){throw 'Vehicle playground signing failed'}
& powershell -NoProfile -ExecutionPolicy Bypass -File $catSigner -Executable (Join-Path $PSScriptRoot 'build/windows-gl/bin/Release/catrina_preview.exe')
if($LASTEXITCODE){throw 'La Catrina review signing failed'}
& powershell -NoProfile -ExecutionPolicy Bypass -File Test-Catrina-Preview.ps1
if($LASTEXITCODE){throw 'La Catrina review rig checks failed'}
& powershell -NoProfile -ExecutionPolicy Bypass -File Test-Suspension-Playground.ps1
if($LASTEXITCODE){throw 'Vehicle physics checks failed'}
$catReceipt=Get-Content -LiteralPath build/suspension-playground/latest-audit.json -Raw | ConvertFrom-Json
& $catPython -X utf8 scripts/catrina_enclosure_audit.py --poses (Join-Path $catReceipt.session 'physics-audit/catrina-rig-poses.csv')
if($LASTEXITCODE){throw 'La Catrina enclosure clearance checks failed'}
Write-Output 'La Catrina built and checked. Open Launch-La-Catrina.cmd.'
