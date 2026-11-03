[CmdletBinding()]
param([string]$Python)

# CPU-only canonical preparation. Requires already-built CPU tools; never
# builds, starts a game/renderer, signs software, or accesses the network.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$assetRoot = Join-Path $projectRoot 'showcase\assets'
$cpuTest = Join-Path $projectRoot 'build\windows-gl\bin\Release\RallyVehicle_test.exe'
$aoHelper = Join-Path $projectRoot 'build\windows-gl\bin\Release\safari_ao_bake.exe'
$generator = Join-Path $PSScriptRoot 'generate-safari-body.py'
$packer = Join-Path $PSScriptRoot 'bake-safari-ao.py'
$cockpitAudit = Join-Path $PSScriptRoot 'audit-safari-cockpit.py'
$rearAudit = Join-Path $PSScriptRoot 'audit-safari-rear.py'
if (-not $Python) {
    $pythonCommand = Get-Command python -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
} else {
    $pythonCommand = Get-Command $Python -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
}
if (-not $pythonCommand) { throw 'Python was not found. Pass -Python with the installed python.exe path; the py launcher is not used.' }
$pythonExe = $pythonCommand.Source
if ($pythonExe -match '\\Microsoft\\WindowsApps\\') {
    throw 'Pass -Python with the actual installed interpreter path; the Windows Store launcher alias is not used.'
}
foreach ($tool in @($cpuTest, $aoHelper, $generator, $packer, $cockpitAudit, $rearAudit)) {
    if (-not (Test-Path -LiteralPath $tool -PathType Leaf)) { throw "Required existing CPU tool is missing: $tool" }
}
if (Test-Path -LiteralPath (Join-Path $projectRoot 'build\evaluation-active.json')) {
    throw 'Finish the supervised native evaluation before preparing canonical assets.'
}

function Write-JsonFile($Path, $Value) {
    [IO.File]::WriteAllText($Path, (($Value | ConvertTo-Json -Depth 40) + "`n"), [Text.UTF8Encoding]::new($false))
}
function Invoke-CpuStep($Exe, [string[]]$Arguments, $Log, $Label) {
    & $Exe @Arguments > $Log 2>&1
    if ($LASTEXITCODE -ne 0) { throw "$Label failed (exit $LASTEXITCODE). See $Log" }
}
function Hash-File($Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }

# Inspect actual serialized geometry/images, rather than retaining raw generator
# counts after AO has expanded triangle corners and added its image.
$inspectGlb = @'
import hashlib, io, json, struct, sys
from pathlib import Path
from PIL import Image
p=Path(sys.argv[1]);b=p.read_bytes()
assert struct.unpack_from('<III',b)==(0x46546c67,2,len(b))
d=None;binary=None;at=12
while at<len(b):
 n,k=struct.unpack_from('<II',b,at);chunk=b[at+8:at+8+n]
 if k==0x4e4f534a:d=json.loads(chunk)
 if k==0x004e4942:binary=chunk
 at+=8+n
assert d is not None and binary is not None
primitives=[p for m in d['meshes'] for p in m['primitives']]
vertices=sum(d['accessors'][p['attributes']['POSITION']]['count'] for p in primitives)
triangles=sum(d['accessors'][p['indices']]['count']//3 if 'indices' in p else d['accessors'][p['attributes']['POSITION']]['count']//3 for p in primitives)
images=[]
for i,image in enumerate(d.get('images',[])):
 v=d['bufferViews'][image['bufferView']];o=v.get('byteOffset',0)
 with Image.open(io.BytesIO(binary[o:o+v['byteLength']])) as decoded:images.append(dict(index=i,name=image.get('name',''),width=decoded.width,height=decoded.height))
r=dict(sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),vertices=vertices,triangles=triangles,drawMeshes=len(d['meshes']),embeddedImages=len(images),imageMetadata=images,decodedTextureBytesRgba8=sum(i['width']*i['height']*4 for i in images))
Path(sys.argv[2]).write_text(json.dumps(r,indent=2)+'\n')
'@

$mutex = New-Object Threading.Mutex($false, 'Local\ThreeppSafariAssetPreparation')
$locked = $false
$mutated = $false
$priorFiles = @()
$run = $null
$stage = 'preflight'
try {
    try { $locked = $mutex.WaitOne(0) } catch [Threading.AbandonedMutexException] { $locked = $true }
    if (-not $locked) { throw 'Another Safari canonical preparation is running.' }
    $stamp = (Get-Date).ToString('yyyyMMdd-HHmmss-fff') + '-' + [Guid]::NewGuid().ToString('N').Substring(0,8)
    $preparationRoot = Join-Path $projectRoot 'build\safari-prepare'
    New-Item -ItemType Directory -Path $preparationRoot -Force | Out-Null
    $run = Join-Path $preparationRoot $stamp
    if (Test-Path -LiteralPath $run) { throw 'Preparation directory already exists; no files were changed.' }
    New-Item -ItemType Directory -Path $run | Out-Null
    Invoke-CpuStep $pythonExe @('-c', 'import sys,numpy,scipy,PIL; print(sys.executable)') (Join-Path $run 'python.log') 'Python dependencies'
    Invoke-CpuStep $aoHelper @('--self-test') (Join-Path $run 'helper-self-test.log') 'AO helper self-test'

    $previous = Join-Path $run 'previous'
    New-Item -ItemType Directory -Path $previous | Out-Null
    foreach ($name in @('safari-body.glb', 'safari-body.json', 'safari-body-ao.json')) {
        $path = Join-Path $assetRoot $name
        $exists = Test-Path -LiteralPath $path -PathType Leaf
        $entry = [ordered]@{name=$name;path=$path;existed=$exists;sha256=$null}
        if ($exists) { $entry.sha256 = Hash-File $path; Copy-Item -LiteralPath $path -Destination (Join-Path $previous $name) }
        $priorFiles += $entry
    }
    Write-JsonFile (Join-Path $run 'previous-files.json') $priorFiles

    $stage = 'rear mechanical static fit'
    Invoke-CpuStep $pythonExe @('-B', $rearAudit, '--out', (Join-Path $run 'rear-mechanical-fit.json')) (Join-Path $run 'rear-mechanical-fit.log') 'Rear mechanical static fit'
    $rearFit = Get-Content -LiteralPath (Join-Path $run 'rear-mechanical-fit.json') -Raw | ConvertFrom-Json
    if ($rearFit.status -ne 'pass' -or $rearFit.scope -ne 'rear source package static geometry' -or $rearFit.sourceSha256 -ne (Hash-File (Join-Path $PSScriptRoot 'safari_rear_assembly.py')) -or $rearFit.generatorSha256 -ne (Hash-File $generator) -or $rearFit.auditorSha256 -ne (Hash-File $rearAudit)) {
        throw 'Rear mechanical report is not a full passing check of the current authoring sources.'
    }

    $stage = 'raw generation'
    $mutated = $true # The generator writes the two canonical raw files.
    Write-Output "Generating raw Safari; rollback snapshot: $previous"
    Invoke-CpuStep $pythonExe @($generator) (Join-Path $run 'generator.log') 'Raw generation'
    $rawAssets = Join-Path $run 'raw-assets'
    New-Item -ItemType Directory -Path $rawAssets | Out-Null
    Copy-Item -LiteralPath (Join-Path $assetRoot 'safari-body.glb') -Destination $rawAssets
    Copy-Item -LiteralPath (Join-Path $assetRoot 'safari-body.json') -Destination $rawAssets
    $rawGlb = Join-Path $rawAssets 'safari-body.glb'
    Invoke-CpuStep $pythonExe @('-c', $inspectGlb, $rawGlb, (Join-Path $run 'raw-actual.json')) (Join-Path $run 'raw-inspection.log') 'Raw GLB inspection'
    $rawActual = Get-Content -LiteralPath (Join-Path $run 'raw-actual.json') -Raw | ConvertFrom-Json
    $rawMetadata = Get-Content -LiteralPath (Join-Path $rawAssets 'safari-body.json') -Raw | ConvertFrom-Json
    if ($rawMetadata.sourceHashes.'scripts/safari_rear_assembly.py' -ne $rearFit.sourceSha256 -or $rawMetadata.sourceHashes.'scripts/generate-safari-body.py' -ne $rearFit.generatorSha256) {
        throw 'Rear or generator source changed between mechanical verification and raw generation.'
    }
    if ($rawActual.vertices -ne $rawMetadata.vertices -or $rawActual.bytes -ne $rawMetadata.bytes -or $rawActual.triangles -ne $rawMetadata.triangles) {
        throw 'Raw generator metadata disagrees with serialized GLB counts.'
    }
    $stage = 'raw CPU vehicle checks'
    Invoke-CpuStep $cpuTest @($rawAssets) (Join-Path $run 'raw-vehicle-test.log') 'Raw CPU vehicle checks'
    Invoke-CpuStep $pythonExe @('-B', $cockpitAudit, '--glb', $rawGlb, '--out', (Join-Path $run 'raw-cockpit-fit.json')) (Join-Path $run 'raw-cockpit-fit.log') 'Raw serialized cockpit fit'

    $stage = 'AO bake and isolated candidate checks'
    $candidateAssets = Join-Path $run 'candidate-assets'
    $candidateGlb = Join-Path $candidateAssets 'safari-body.glb'
    Invoke-CpuStep $pythonExe @($packer, '--source', $rawGlb, '--output', $candidateGlb, '--helper', $aoHelper, '--expected-sha256', $rawActual.sha256, '--atlas-layout', 'median') (Join-Path $run 'ao-pack.log') 'AO bake and pack'
    Invoke-CpuStep $cpuTest @($candidateAssets) (Join-Path $run 'ao-vehicle-test.log') 'Isolated AO CPU vehicle checks'
    Invoke-CpuStep $pythonExe @('-B', $cockpitAudit, '--glb', $candidateGlb, '--out', (Join-Path $run 'ao-cockpit-fit.json')) (Join-Path $run 'ao-cockpit-fit.log') 'AO serialized cockpit fit'
    Invoke-CpuStep $pythonExe @('-c', $inspectGlb, $candidateGlb, (Join-Path $run 'output-actual.json')) (Join-Path $run 'output-inspection.log') 'AO GLB inspection'
    $outputActual = Get-Content -LiteralPath (Join-Path $run 'output-actual.json') -Raw | ConvertFrom-Json
    $receipt = Get-Content -LiteralPath (Join-Path $candidateAssets 'AO-RECEIPT.json') -Raw | ConvertFrom-Json
    if ($receipt.sourceSha256 -ne $rawActual.sha256 -or $receipt.candidateSha256 -ne $outputActual.sha256 -or $receipt.candidateBytes -ne $outputActual.bytes -or $outputActual.triangles -ne $rawActual.triangles) {
        throw 'AO receipt/output identity or triangle count mismatch.'
    }
    if (-not $receipt.invariants.unchangedAllOriginalTriangleCornerAttributes -or -not $receipt.invariants.originalSourceUnchanged -or $receipt.atlas.clippedFourthPixelCells -ne 0) {
        throw 'AO did not preserve the required attribute/atlas invariants.'
    }

    $toolSources = [ordered]@{}
    foreach ($relative in @('scripts/prepare-safari-body.ps1','scripts/bake-safari-ao.py','scripts/audit-safari-cockpit.py','scripts/audit-safari-rear.py','showcase/safari_ao_bake.cpp')) { $toolSources[$relative] = Hash-File (Join-Path $projectRoot $relative) }
    $rearFitSummary = [ordered]@{status=$rearFit.status;sourceSha256=$rearFit.sourceSha256;generatorSha256=$rearFit.generatorSha256;auditorSha256=$rearFit.auditorSha256;checkedPairs=@($rearFit.allChecks).Count;openBoreRays=@($rearFit.openBoreRays).Count;minimumHotStructureGap=$rearFit.minimumHotStructureGap;limits=$rearFit.limits}
    $compactReceipt = [ordered]@{
        version=1; method='Static geometry AO, cosine hemisphere; ambient only'
        rawAsset=$rawActual; outputAsset=$outputActual
        samples=$receipt.bake.samples; maxDistanceMetres=$receipt.bake.maxDistanceMetres; originBiasMetres=$receipt.bake.originBiasMetres; strength=$receipt.bake.strength
        atlas=$receipt.atlas; visibility=$receipt.visibility; invariants=$receipt.invariants
        bake=[ordered]@{occluderTriangles=$receipt.bake.occluderTriangles;uniqueQueries=$receipt.bake.uniqueQueries;rayQueries=$receipt.bake.rayQueries;queryNormalFallbackVertices=$receipt.bake.queryNormalFallbackVertices;unreferencedReceiverVerticesSkipped=$receipt.bake.unreferencedReceiverVerticesSkipped}
        toolSourceHashes=$toolSources
        cpuChecks=[ordered]@{rawVehicleExitCode=0;aoVehicleExitCode=0;rawCockpitFitExitCode=0;aoCockpitFitExitCode=0;actualGltfLoader='passed in AO packer';vehicleTestExeSha256=(Hash-File $cpuTest);aoHelperExeSha256=(Hash-File $aoHelper)}
        rearMechanicalFit=$rearFitSummary
        preparationLogDirectory=('build/safari-prepare/' + $stamp)
        nativeAcceptance='Not performed by this CPU-only preparation; supervised native review remains separate.'
    }
    # Keep authoring provenance at the top level, but make the active counts
    # describe the actual AO GLB and retain raw counts/hash explicitly.
    $finalMetadata = $rawMetadata
    foreach ($key in @('bytes','vertices','triangles','drawMeshes','embeddedImages','imageMetadata','decodedTextureBytesRgba8','sha256')) {
        $finalMetadata | Add-Member -NotePropertyName $key -NotePropertyValue $outputActual.$key -Force
    }
    $finalMetadata | Add-Member -NotePropertyName rawAsset -NotePropertyValue $rawActual -Force
    $finalMetadata | Add-Member -NotePropertyName preparation -NotePropertyValue 'scripts/prepare-safari-body.ps1' -Force
    $finalMetadata | Add-Member -NotePropertyName rearMechanicalFit -NotePropertyValue $rearFitSummary -Force
    $finalMetadata | Add-Member -NotePropertyName postprocess -NotePropertyValue ([ordered]@{method=$compactReceipt.method;sourceSha256=$rawActual.sha256;outputSha256=$outputActual.sha256;receipt='safari-body-ao.json';strength=$receipt.bake.strength;atlasTexCoord=1;toolSourceHashes=$toolSources}) -Force
    Write-JsonFile (Join-Path $run 'safari-body-final.json') $finalMetadata
    Write-JsonFile (Join-Path $run 'safari-body-ao.json') $compactReceipt

    $stage = 'canonical promotion'
    if ($rearFit.sourceSha256 -ne (Hash-File (Join-Path $PSScriptRoot 'safari_rear_assembly.py')) -or $rearFit.generatorSha256 -ne (Hash-File $generator) -or $rearFit.auditorSha256 -ne (Hash-File $rearAudit)) { throw 'Mechanical authoring sources changed during preparation; keep the previous canonical asset.' }
    Copy-Item -LiteralPath $candidateGlb -Destination (Join-Path $assetRoot 'safari-body.glb')
    Copy-Item -LiteralPath (Join-Path $run 'safari-body-final.json') -Destination (Join-Path $assetRoot 'safari-body.json')
    Copy-Item -LiteralPath (Join-Path $run 'safari-body-ao.json') -Destination (Join-Path $assetRoot 'safari-body-ao.json')
    if ((Hash-File (Join-Path $assetRoot 'safari-body.glb')) -ne $outputActual.sha256) { throw 'Canonical promotion hash mismatch.' }
    Write-JsonFile (Join-Path $run 'result.json') ([ordered]@{ok=$true;rawSha256=$rawActual.sha256;canonicalSha256=$outputActual.sha256;graphicsContext=$false;logs=$run})
    Write-Output "Prepared canonical Safari: $($outputActual.sha256). CPU checks passed; native review remains separate. Logs: $run"
} catch {
    $failure = $_.Exception.Message
    $rollbackFailures = @()
    if ($mutated) {
        foreach ($entry in $priorFiles) {
            try {
                if ($entry.existed) {
                    Copy-Item -LiteralPath (Join-Path $previous $entry.name) -Destination $entry.path
                    if ((Hash-File $entry.path) -ne $entry.sha256) { throw 'Restored hash differs.' }
                } elseif (Test-Path -LiteralPath $entry.path -PathType Leaf) {
                    Remove-Item -LiteralPath $entry.path # Only a newly created one of the three named canonical files.
                }
            } catch { $rollbackFailures += "$($entry.name): $($_.Exception.Message)" }
        }
    }
    if ($run) { Write-JsonFile (Join-Path $run 'result.json') ([ordered]@{ok=$false;stage=$stage;error=$failure;canonicalRestored=($mutated -and $rollbackFailures.Count -eq 0);rollbackErrors=$rollbackFailures;graphicsContext=$false}) }
    if ($rollbackFailures.Count) { throw "Safari preparation failed during $stage`: $failure. Rollback needs attention: $($rollbackFailures -join '; '). Snapshot: $previous" }
    if ($mutated) { throw "Safari preparation failed during $stage`: $failure. Previous canonical GLB/JSON/receipt restored exactly. Logs: $run" }
    throw
} finally {
    if ($locked) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
}
