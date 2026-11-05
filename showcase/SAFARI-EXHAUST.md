# Safari recorded exhaust voice

The first native film used the open buggy's cosmetic engine profile. At
13.5 m/s (48.6 km/h), its second-gear mapping settled around5847RPM at30%
throttle, selecting almost entirely the upper recording. That made a modest
cruise read like a sustained high rev. Correct encoding and unclipped levels
did not establish a convincing sound.

The Safari now has its own `RallySafariPowertrain.hpp` and three recorded
`safari_exhaust_*.wav` assets. The old `Powertrain` and its three
`cinder_exhaust_*.wav` files remain unchanged. The presentation gearbox uses
the actual0.49m tyre radius, a4.7 final drive and five ratios to derive coupled
RPM from road speed. The same cruise settles near2670RPM in second. Load
changes the shift threshold; cooldown and distinct downshift thresholds prevent
cruise hunting. Flywheel/load smoothing and a short smooth shift dip provide
different acceleration, loaded pull and lift-off states. This remains an
instrument/audio model, not a new longitudinal engine/tyre force simulation.

The voice retains real recorded pressure pulses. A lower idle, textured
midrange pull and louder upper pass come from the existing CC0 recording by
kyles. Original tuning moves their nominal register, keeps broad low exhaust
body, and retains useful recorded rasp on load. A fourth-order42Hz highpass
rejects microphone/wind/subsonic energy; restrained broad EQ avoids making the
entire voice a muffled bass layer. Mild250ms envelope control reduces the
recorded microphone pass-by swell without flattening combustion texture.
Each band has a240ms equal-power circular join, DC removal and a-5dBFS peak
ceiling. No synthesized oscillator, subharmonic, noise layer or unrelated
rumble is added. The source vehicle/RPM was not measured: this is a fictional
car voice, not a matched production Porsche flat-six recording.

`scripts/prepare-safari-exhaust.py` reproduces the assets from the retained
local source and checks its hash and all original buggy hashes. It records
processing, source ranges and actual output hashes in
`assets/SAFARI-EXHAUST-SOURCE.json`. It can also mix a supplied CSV of exact
C++ band pitch/gain controls. The runtime and native review film should use
the same `SafariPowertrain::band` output, rather than duplicate its model in
an independent audio renderer.

CPU review evidence is under `build/safari-audio-iteration`. The12-second
equal-loudness preview includes idle, acceleration/upshift, cruise, lift,
reapplication and deceleration. Both versions measure-18LUFS. The new version
measures-6.1dBTP, with42.4% energy at35-150Hz versus27.4% before, and10.5%
at500-2000Hz versus2.0% before. Its full-spectrum power centroid is226Hz
versus214Hz: the additional recorded rasp means a single centroid statistic
does not describe the lower engine register. These measurements establish
band balance, control behavior and headroom; they do not certify subjective
listening, native endpoint output, synchronization by ear or human acceptance.

`SafariPowertrainTest.hpp` covers tyre-radius agreement, low cruise RPM,
unchanged old response, no gear hunting under cruise pulses, settled30/60/120Hz
behavior, idle/mute/load response and bounded gain across RPM/load/shift states.
The test runs without opening audio or graphics devices.
