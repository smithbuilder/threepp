# Regenerates the original harmonic engine loop; no third-party samples.
$ErrorActionPreference='Stop'
$target=Join-Path $PSScriptRoot 'cinder_engine.wav'
$writer=New-Object System.IO.BinaryWriter([System.IO.File]::Create($target))
$rate=24000; $count=$rate*2
try {
    $writer.Write([Text.Encoding]::ASCII.GetBytes('RIFF')); $writer.Write([int](36+$count*2))
    $writer.Write([Text.Encoding]::ASCII.GetBytes('WAVEfmt ')); $writer.Write([int]16)
    $writer.Write([int16]1); $writer.Write([int16]1); $writer.Write([int]$rate)
    $writer.Write([int]($rate*2)); $writer.Write([int16]2); $writer.Write([int16]16)
    $writer.Write([Text.Encoding]::ASCII.GetBytes('data')); $writer.Write([int]($count*2))
    for($i=0;$i -lt $count;$i++) {
        $t=$i/[double]$rate; $phase=2*[Math]::PI*60*$t
        $pulse=[Math]::Sin($phase)+.45*[Math]::Sin(2*$phase)+.25*[Math]::Sin(3*$phase)+.12*[Math]::Sin(7*$phase)
        $rattle=.06*[Math]::Sin(2*[Math]::PI*1140*$t)*(.4+.6*[Math]::Pow([Math]::Sin($phase/2),2))
        $sample=.28*[Math]::Tanh($pulse*1.2)+$rattle
        $writer.Write([int16]([Math]::Round($sample*32767)))
    }
} finally { $writer.Dispose() }
