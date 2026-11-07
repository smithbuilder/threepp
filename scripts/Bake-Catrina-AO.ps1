[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
$taskPython=(Get-Command python.exe).Source
& $taskPython -X utf8 scripts/catrina_ao.py prepare
if($LASTEXITCODE){throw 'Cavity preparation failed'}
if(-not('ThreeppEvaluationJob' -as [type])){Add-Type -Path scripts/EvaluationJob.cs}
$taskExe=Join-Path (Get-Location) 'build/windows-gl/bin/Release/safari_ao_bake.exe'
foreach($taskGroup in @('body','wheels','lids')){
    $taskArgs=@((Join-Path (Get-Location) "build/la-catrina/ao/$taskGroup.glb"),(Join-Path (Get-Location) "build/la-catrina/ao/$taskGroup.json"))
    $taskJob=New-Object ThreeppEvaluationJob
    try{
        $taskProcess=Start-Process -FilePath $taskExe -ArgumentList $taskArgs -WindowStyle Hidden -PassThru -RedirectStandardOutput "build/la-catrina/ao/$taskGroup.stdout.log" -RedirectStandardError "build/la-catrina/ao/$taskGroup.stderr.log"
        $taskJob.Assign($taskProcess.Handle);$taskProcess.PriorityClass='BelowNormal'
        if(-not $taskProcess.WaitForExit(180000)){throw "$taskGroup CPU cavity bake exceeded its 180-second deadline"}
        if($taskProcess.ExitCode -ne 0){throw "$taskGroup CPU cavity bake failed; inspect logs"}
    }finally{$taskJob.Dispose()}
}
& $taskPython -X utf8 scripts/catrina_ao.py finish
if($LASTEXITCODE){throw 'Cavity cache retention failed'}
& $taskPython -X utf8 scripts/catrina_generate.py
if($LASTEXITCODE){throw 'Cavity asset export failed'}
