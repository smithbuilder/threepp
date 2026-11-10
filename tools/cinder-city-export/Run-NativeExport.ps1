param([string]$Output='build/cinder-city-export/native-v1')
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'));Set-Location $root
$target=[IO.Path]::GetFullPath((Join-Path $root $Output));$expected=[IO.Path]::GetFullPath((Join-Path $root 'build/cinder-city-export'))+[IO.Path]::DirectorySeparatorChar
if(-not $target.StartsWith($expected,[StringComparison]::OrdinalIgnoreCase)){throw 'Export output must be inside build/cinder-city-export'}
if(Test-Path -LiteralPath $target){throw 'Preserve existing output; choose a new export folder'}
foreach($marker in @('PAUSE','EVALUATION-PAUSED.txt','build/GRAPHICS_PAUSED.txt','build/evaluation-active.json','Unity/PAUSE','evidence/PAUSE')){if(Test-Path (Join-Path $root $marker)){throw "Paused: $marker"}}
if(-not ('CinderExportMemory' -as [type])){Add-Type @'
using System;using System.Runtime.InteropServices;
public static class CinderExportMemory {
 [StructLayout(LayoutKind.Sequential)] public class Status {public uint Length=64,Load;public ulong Total,Available,PageTotal,PageAvailable,VirtualTotal,AvailableVirtual,Extended;}
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool GlobalMemoryStatusEx([In,Out] Status s);
 public static ulong Free(){var s=new Status();if(!GlobalMemoryStatusEx(s))throw new Exception("Cannot verify free RAM");return s.Available;}
}
'@}
$free=[CinderExportMemory]::Free();if($free -lt 4GB){throw 'Less than4GiB freeRAM'}
if(([IO.DriveInfo]::new([IO.Path]::GetPathRoot($root))).AvailableFreeSpace -lt 15GB){throw 'Less than15GiB free disk'}
$running=@(Get-Process -ErrorAction SilentlyContinue |Where-Object {if($_.ProcessName -eq 'Unity' -or $_.ProcessName -match '^(Cinder|Windowseat|PADDLES|suspension_playground|timber_rally|nocturne_film|switchback_film)$'){return $true};try{return $_.ProcessName -notlike 'UnityCrashHandler*' -and $_.Path -and (Test-Path -LiteralPath (Join-Path ([IO.Path]::GetDirectoryName($_.Path)) 'UnityPlayer.dll'))}catch{return $false}})
if($running.Count){throw 'Another editor or game running; defer export'}
if(-not ('ThreeppEvaluationJob' -as [type])){Add-Type -Path (Join-Path $root 'scripts/EvaluationJob.cs')}
$mutex=[Threading.Mutex]::new($false,'Local\ThreeppEvaluation-Supervisor');$locked=$false;$job=$null;$child=$null;$normal=$false;$peak=0;$watch=[Diagnostics.Stopwatch]::StartNew()
$exe=Join-Path $root 'build/cinder-city-export/export_city.exe'
$receipt=Join-Path $root ('build/cinder-city-export/export-'+(Get-Date -Format 'yyyyMMdd-HHmmss-fff')+'.json')
$inputRoot=$root;$inputMode='initial live native sources'
try{
 try{$locked=$mutex.WaitOne(0)}catch [Threading.AbandonedMutexException]{$locked=$true};if(-not $locked){throw 'Another supervised job active'}
 $stamp=Join-Path $root 'build/unity-last-run.txt';if(Test-Path $stamp){$elapsed=((Get-Date)-(Get-Item $stamp).LastWriteTime).TotalSeconds;if($elapsed -lt 10){Start-Sleep -Seconds ([int][Math]::Ceiling(10-$elapsed))}}
 $frozen=Join-Path $root 'assets/unity/city/textures'
 if(Test-Path -LiteralPath $frozen){
  $inputRoot=Join-Path $root ('build/cinder-city-export/frozen-inputs-'+(Get-Date -Format 'yyyyMMdd-HHmmss-fff'));$frozenTarget=Join-Path $inputRoot 'showcase/assets/city'
  if(Test-Path -LiteralPath $inputRoot){throw 'Preserve existing frozen-input output'}
  New-Item -ItemType Directory -Path $frozenTarget |Out-Null
  Get-ChildItem -LiteralPath $frozen -File |ForEach-Object {Copy-Item -LiteralPath $_.FullName -Destination $frozenTarget}
  $inputMode='frozen native city texture bytes'
 }
 $job=[ThreeppEvaluationJob]::new();if((Get-AuthenticodeSignature $exe).Status -ne 'Valid'){throw 'CPU exporter needs a valid Windows signature'};$child=Start-Process -FilePath $exe -ArgumentList @(('"'+$inputRoot+'"'),('"'+$target+'"')) -WindowStyle Hidden -PassThru -RedirectStandardOutput ($receipt+'.stdout') -RedirectStandardError ($receipt+'.stderr');$job.Assign($child.Handle);$child.PriorityClass='BelowNormal'
 while(-not $child.HasExited){$child.Refresh();$peak=[Math]::Max($peak,$child.WorkingSet64);if($watch.Elapsed.TotalSeconds -gt 180){throw 'CPU export watchdog exceeded'};if(Test-Path (Join-Path $root 'PAUSE')){throw 'PAUSE requested'};Start-Sleep -Milliseconds 300}
 $child.WaitForExit();if($child.ExitCode -ne 0){throw "CPU export exited $($child.ExitCode)"}
 if(-not(Test-Path (Join-Path $target 'native-city.json'))){throw 'Native city export missing'};$normal=$true
 Get-Content ($receipt+'.stdout')
}finally{
 if($job){$job.Dispose()};if($child -and -not $child.HasExited){$child.WaitForExit(5000)|Out-Null}
 @{action='CPU native city export';normal=$normal;seconds=$watch.Elapsed.TotalSeconds;peakWorkingSetBytes=$peak;output=$target;inputRoot=$inputRoot;inputMode=$inputMode;exeSha256=$(if(Test-Path $exe){(Get-FileHash $exe).Hash});noGraphics=$true}|ConvertTo-Json|Set-Content $receipt
 if($locked){$mutex.ReleaseMutex()};$mutex.Dispose();(Get-Date).ToString('o')|Set-Content (Join-Path $root 'build/unity-last-run.txt')
}
