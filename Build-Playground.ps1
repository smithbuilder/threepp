[CmdletBinding()]
param([ValidateSet('Build','Test','Capture')][string]$Action = 'Build')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
$vs = & $vswhere -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath |
    Where-Object { Test-Path -LiteralPath (Join-Path $_ 'Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe') } |
    Select-Object -First 1
if (-not $vs) { throw 'Visual Studio 2022 C++ Build Tools are required.' }
$cmake = Join-Path $vs 'Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'
if (-not (Test-Path -LiteralPath $cmake)) { $cmake = (Get-Command cmake -ErrorAction Stop).Source }
$ctest = Join-Path (Split-Path $cmake) 'ctest.exe'
if ($Action -eq 'Build') {
    & $cmake --preset evaluation-windows "-DCMAKE_GENERATOR_INSTANCE=$vs"
    if ($LASTEXITCODE) { throw 'Configuration failed.' }
    & $cmake --build --preset evaluation-windows
    if ($LASTEXITCODE) { throw 'Build failed.' }
} elseif ($Action -eq 'Test') {
    # Graphics are intentionally excluded after a reported full-system lock.
    & $ctest --preset evaluation-windows --timeout 180 --exclude-regex '^GL(Renderer|PostProcessing|ShadowMap|TextureNameReuse|SurveyFixes)_test$'
    if ($LASTEXITCODE) { throw 'Tests failed.' }
} else {
    throw 'Automatic graphics capture is paused after a reported full-system lock. See SAFETY.md; no GPU workload was started.'
}
