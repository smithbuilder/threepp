param(
 [ValidateSet('Kit','Lods','RestoreCity','SkinScale','Build','Probe','Capture','Benchmark','Play')][string]$Action='Probe',
 [ValidatePattern('^cinder-unity-r[0-9]+$')][string]$Revision='cinder-unity-r20',
 [ValidateSet('safari','buggy','baja','switchback','catrina','media-luna','nocturne')][string]$Vehicle='catrina',
 [ValidateSet('playground','city','forest')][string]$World='city',
 [ValidateRange(0,7)][int]$Area=0,[ValidateRange(0,6)][int]$View=0,
 [ValidateRange(0,900)][int]$Frames=180,[ValidateRange(0,900)][int]$Warmup=120,
 [ValidateRange(0,8)][int]$Mode=0,[switch]$Drive,[switch]$Menu,[switch]$UiProbe,[switch]$Diagnostic,[switch]$RoofCycle,[switch]$CultureFlow,[switch]$SkyReflectionControl,[switch]$ColourProbe,
 [ValidateSet('','standard','ambient','reflection-off','reflection-direction','coat-normal','cube-lod0','cube-filtered','cube-decode','white-coat','sun-radiance')][string]$MaterialControl=''
)
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location -LiteralPath $root
foreach($p in @('PAUSE','EVALUATION-PAUSED.txt','build/GRAPHICS_PAUSED.txt','build/evaluation-active.json','Unity/PAUSE','evidence/PAUSE')) { if(Test-Path -LiteralPath (Join-Path $root $p)){throw "Launch paused by $p"} }
if($Frames+$Warmup -gt 900){throw 'At most 900 captured and warmup frames combined'}
$running=@(Get-Process -ErrorAction SilentlyContinue | Where-Object {if($_.ProcessName -eq 'Unity' -or $_.ProcessName -match '^(Cinder|Windowseat|PADDLES|suspension_playground|timber_rally|nocturne_film|switchback_film)$'){return $true};try{return $_.ProcessName -notlike 'UnityCrashHandler*' -and $_.Path -and (Test-Path -LiteralPath (Join-Path ([IO.Path]::GetDirectoryName($_.Path)) 'UnityPlayer.dll'))}catch{return $false}})
if($running.Count){throw ('Another editor or game is running: '+(($running|ForEach-Object {$_.ProcessName+' '+$_.Id}) -join ', '))}
if(-not ('CinderMemory' -as [type])) {Add-Type @'
using System;using System.Runtime.InteropServices;
public static class CinderMemory {
 [StructLayout(LayoutKind.Sequential)] public class Status {public uint Length=64,Load;public ulong Total,Available,PageTotal,PageAvailable,VirtualTotal,VirtualAvailable,Extended;}
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool GlobalMemoryStatusEx([In,Out] Status s);
 public static ulong Free(){var s=new Status();if(!GlobalMemoryStatusEx(s))throw new Exception("Cannot verify free RAM");return s.Available;}
}
'@}
$free=[CinderMemory]::Free();if($free -lt 4GB){throw 'Less than 4 GiB free RAM'}
$disk=[IO.DriveInfo]::new([IO.Path]::GetPathRoot($root)).AvailableFreeSpace;if($disk -lt 15GB){throw 'Less than 15 GiB free disk'}
if(-not ('ThreeppEvaluationJob' -as [type])){Add-Type -Path (Join-Path $root 'scripts/EvaluationJob.cs')}
$mutex=[Threading.Mutex]::new($false,'Local\ThreeppEvaluation-Supervisor');$locked=$false;$child=$null;$job=$null
$session=Join-Path $root ('evidence/'+$Revision+'/'+(Get-Date -Format 'yyyyMMdd-HHmmss-fff')+'-'+$Action);New-Item -ItemType Directory -Force $session | Out-Null
$stamp=Join-Path $root 'build/unity-last-run.txt';if(Test-Path $stamp){$elapsed=((Get-Date)-(Get-Item $stamp).LastWriteTime).TotalSeconds;if($elapsed -lt 10){Start-Sleep -Seconds ([int][Math]::Ceiling(10-$elapsed))}}
$timer=[Diagnostics.Stopwatch]::StartNew();$peak=0;$normal=$false
try{
 try{$locked=$mutex.WaitOne(0)}catch [Threading.AbandonedMutexException]{$locked=$true};if(-not $locked){throw 'Another supervised evaluation is active'}
 $deadline=180;$arguments=@();$exe=Join-Path $root ('builds/'+$Revision+'/Cinder.exe')
 switch($Action){
  'Kit' {$exe='C:/tools/blender-4.5.9-windows-x64/blender.exe';$arguments=@('-b','--threads','2','--python-exit-code','1','--python',('"'+(Join-Path $root 'tools/blender/cinder/create_kit.py')+'"'));$deadline=240}
  'Lods' {$exe='C:/tools/blender-4.5.9-windows-x64/blender.exe';$arguments=@('-b','--threads','2','--python-exit-code','1','--python',('"'+(Join-Path $root 'tools/blender/cinder/create_lods.py')+'"'));$deadline=600}
  'RestoreCity' {$exe='C:/tools/blender-4.5.9-windows-x64/blender.exe';$arguments=@('-b','--threads','2','--python-exit-code','1','--python',('"'+(Join-Path $root 'tools/blender/cinder/restore_city.py')+'"'),'--',('"'+(Join-Path $root 'assets/unity/city/mercer-city.glb')+'"'),('"'+(Join-Path $root ('build/cinder-city-export/blender-verified-'+$Revision))+'"'));$deadline=240}
  'SkinScale' {$exe='C:/Program Files/Unity/Hub/Editor/6000.3.6f1/Editor/Unity.exe';$arguments=@('-batchmode','-nographics','-projectPath',('"'+(Join-Path $root 'Unity')+'"'),'-executeMethod','Cinder.Editor.SkinningScaleProbe.Run','-logFile',('"'+(Join-Path $session 'editor.log')+'"'));$deadline=120}
  'Build' {$exe='C:/Program Files/Unity/Hub/Editor/6000.3.6f1/Editor/Unity.exe';$arguments=@('-batchmode','-nographics','-projectPath',('"'+(Join-Path $root 'Unity')+'"'),'-executeMethod','Cinder.Editor.CinderBuild.Run','-cinder-build',$Revision,'-logFile',('"'+(Join-Path $session 'editor.log')+'"'));$deadline=900}
  'Probe' {$arguments=@('-batchmode','-nographics','-probe','-module','cinder-drive');$deadline=120}
  'Play' {$arguments=@('-module','cinder-drive');$deadline=300}
  default {$arguments=@('-batchmode','-force-d3d11','-screen-fullscreen','0','-screen-width','960','-screen-height','600','-capture','-module','cinder-drive','-frames',[string]$Frames,'-warmup',[string]$Warmup,'-camera',[string]$View);$deadline=150}
 }
 if(-not (Test-Path $exe)){throw "Required application missing: $exe"}
 if($Action -notin @('Build','Kit','Lods','RestoreCity','SkinScale')){
  if((Get-AuthenticodeSignature $exe).Status -ne 'Valid'){throw 'Player needs a valid signature before execution'}
  if($Action -ne 'Probe' -and -not $Diagnostic){$pr=Join-Path $root "evidence/$Revision/latest-probe.json";if(-not(Test-Path $pr)){throw 'Run the exact-player probe first'};$accepted=Get-Content $pr -Raw|ConvertFrom-Json;if(-not $accepted.success -or $accepted.exeSha256 -ne (Get-FileHash $exe -Algorithm SHA256).Hash){throw 'Exact-player probe is missing or failed'}}
  if($Action -ne 'Play'){$arguments+='-silent'};$arguments+=@('-vehicle',$Vehicle,'-world',$World,'-area',[string]$Area,'-mode',[string]$Mode,'-evidence',('"'+$session+'"'),'-watchdog',[string]($deadline-5),'-logFile',('"'+(Join-Path $session 'player.log')+'"'));if($Drive){$arguments+='-autodrive'};if($Menu -or $UiProbe){$arguments+='-menu'};if($UiProbe){$arguments+='-ui-probe'};if($RoofCycle){$arguments+='-roof-cycle'};if($CultureFlow){$arguments+=@('-review-script','culture-flow')};if($SkyReflectionControl){$arguments+='-sky-reflections-only'};if($ColourProbe){$arguments+='-colour-probe'};if($MaterialControl){if($Action -notin @('Capture','Benchmark')){throw 'Material controls require a bounded graphics capture'};$arguments+=@('-material-control',$MaterialControl)}
 }
 $job=[ThreeppEvaluationJob]::new()
 $child=Start-Process -FilePath $exe -ArgumentList $arguments -WorkingDirectory $root -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $session 'stdout.log') -RedirectStandardError (Join-Path $session 'stderr.log')
 $job.Assign($child.Handle);$child.PriorityClass='BelowNormal'
 while(-not $child.HasExited){
  $child.Refresh();$peak=[Math]::Max($peak,$child.WorkingSet64)
  if($timer.Elapsed.TotalSeconds -gt $deadline){throw 'Watchdog deadline exceeded'}
  if(Test-Path (Join-Path $root 'PAUSE')){throw 'PAUSE requested'}
  Start-Sleep -Milliseconds 500
 }
 $child.WaitForExit();$code=$child.ExitCode;$normal=$code -eq 0
 if(-not $normal){throw "Process exited $code. Read $session"}
 if($Action -in @('Capture','Benchmark')){if(@(Get-ChildItem $session -Filter 'frame-*.png').Count -ne $Frames){throw 'Capture frame count incomplete'}}
 if($Action -eq 'Probe'){$rig=Get-Content (Join-Path $session 'loaded-rig-probe.json') -Raw|ConvertFrom-Json;$sim=Get-Content (Join-Path $session 'probe.json') -Raw|ConvertFrom-Json;$batch=Get-Content (Join-Path $session 'runtime-batch-probe.json') -Raw|ConvertFrom-Json;if(-not $rig.Success -or -not $sim.Success -or -not $batch.Success){throw 'Simulation or loaded rig gate failed'};@{success=$true;exeSha256=(Get-FileHash $exe -Algorithm SHA256).Hash;session=$session;simChecks=$sim.Checks;rigChecks=$rig.Checks;runtimeBatchChecks=$batch.Checks}|ConvertTo-Json|Set-Content (Join-Path $root "evidence/$Revision/latest-probe.json")}
 Write-Output "PASS $Action $session"
}finally{
 if($job){$job.Dispose()};if($child -and -not $child.HasExited){$child.WaitForExit(5000)|Out-Null}
 @{launchArguments=$arguments;action=$Action;revision=$Revision;vehicle=$Vehicle;world=$World;area=$Area;mode=$Mode;normal=$normal;elapsedSeconds=$timer.Elapsed.TotalSeconds;peakWorkingSetBytes=$peak;freeRamBefore=$free;freeDiskBefore=$disk;exe=$exe;exeSha256=$(if(Test-Path $exe){(Get-FileHash $exe -Algorithm SHA256).Hash});utc=(Get-Date).ToUniversalTime().ToString('o')}|ConvertTo-Json|Set-Content (Join-Path $session 'runtime-receipt.json')
 New-Item -ItemType Directory -Force (Split-Path $stamp)|Out-Null;(Get-Date).ToString('o')|Set-Content $stamp
 if($locked){$mutex.ReleaseMutex()};$mutex.Dispose()
}
