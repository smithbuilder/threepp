# Cinder Forest Rally

An isolated successor to Timber Run. Launch `Launch-Cinder-Forest.cmd`, or choose
option 6 in `Explore-Examples.cmd`. The original driving study and gallery remain
available. This candidate is saved on `setup/windows-evaluation`.

## Play

- W / Up: accelerate. S / Down: brake and reverse. A / D: steer.
- Space: handbrake. C: cycle chase, close and side cameras.
- R: restart. P: pause. Escape: exit.
- Start Run + Sound: enable recorded exhaust and enter a three-second countdown.
- W starts a silent countdown; M enables/mutes exhaust. P opens the pause menu.
- Race Again restarts from results; Back to Grid returns to the start screen.
- Follow eight sectors to complete a timed lap. The timer starts when driving.

The supplied launcher enforces 960 x 600, at most 30 FPS, one process, 2 GiB
committed-memory limit, a 60-second session and the frame-heartbeat watchdog.
Any failed session pauses subsequent launches. No Windows driver or security
settings were changed.

## What changed

The track is narrower and follows a rolling heightfield. Photographic CC0 forest
floor and gravel albedo/normal maps replace the earlier flat surfaces. The verge
has wind-driven grass, instanced rocks, stakes, timber barriers, clustered trees
and a separate lower-detail distant forest. Static ground shading and one small
local sun shadow add depth without enabling ray tracing or heavy post-processing.

The original buggy now has shaped panels, a braced roll cage, engine details,
exhausts, tyre tread, wheel spokes and an authored number/livery. Steering uses
a damped bicycle model with lateral response; chassis heave, pitch and roll
follow spring/contact sampling. Wheel travel, lean, dust and a closer damped
camera make the motion more legible. Larger rocks and trunks have collisions.
The racing HUD now includes a live course map, RPM sweep, speed and automatic
gear, stopwatch/best time, next-checkpoint distance and eight checkpoint states.
Start, countdown, pause and results screens provide actual race actions. The
stopwatch and car stop at the single-lap finish; results offer Race Again and
Back to Grid. Best time is retained within the current process.

This remains custom arcade motion against an analytic heightfield and circular
obstacles. It is not a PhysX vehicle, a commercial game or a claim to match the
Dune Buggy reference's authored presentation.

## Evidence

The final 900-frame automated run completed one lap in **28.6496 simulated
seconds**, visiting the sectors in order with **zero contacts**. It exited zero
after **42.79 wall-clock seconds** under supervision, with approximately
**127 MiB sampled peak process working set**. This is not a GPU-memory reading or
an uncapped performance benchmark.

Final run: `build/sessions/20261101-222955-662` (capture, result, drive telemetry,
stdout and stderr). Side-camera capture: `20261101-192348-419`. The build passes;
the four Poly Haven texture hashes match the stored receipt. The former
harmonic engine sound has been replaced by three 48 kHz mono loops edited from
kyles' CC0 real dune-buggy recording. `RallyPowertrain.hpp` supplies shared
RPM/load/automatic-gear state, crossfades and shift cuts for instruments/audio.
Source, license, edits and hashes are in `showcase/assets/EXHAUST-SOURCE.json`.
No new Windows reset/display-driver events were found in this candidate pass.

A native window ran and exited cleanly at its 45-second limit. Computer-use
access timed out before any keys were injected, so physical keyboard feel,
controller support and heard audio are **unverified**. Scripted driving does not
close those acceptance gates. Longer-session system stability is also open.

Poly Haven texture provenance and license: `showcase/assets/LICENSE.md` and
`SOURCES.json`. Game geometry is original code/content; exhaust is derived from the credited
CC0 recording, and the Rajdhani racing font includes its SIL OFL license.
The game reads local assets and has no runtime download/API dependency.


## November 2 UI and exhaust revision

`RallyHud.hpp` draws the native racing overlay. The new gearbox is cosmetic: it
drives sound and instruments while motion remains the documented arcade model.
The old synthesized WAV remains a legacy asset; the candidate no longer plays it.
No new graphics features or higher rendering limits were introduced.

Capture sequences are explicit, bounded supervisor runs (`-Sequence`, up to 900
frames plus up to 900 warm-up frames, with the existing wall-clock deadline).
They require verified free disk space, and incomplete sequences pause launches.
CSV telemetry includes powertrain data. `scripts/encode-rally-capture.mjs` mixes
the same exhaust bands against those values for video without opening an audio
endpoint. Scripted captures label this replacement audio as AUDIO REBUILT.

The latest local video and its editable HyperFrames project are under
`build/cinder-film`. Human judgement of exhaust character, physical controls and
long-session stability remain separate from build/capture checks.

Final panel-free revision: native full-lap session
`build/sessions/20261102-062509-415` exited zero after 47.65 wall seconds,
with 135,659,520 bytes sampled peak working set. It completed all checkpoints,
recorded 28.6496 seconds and zero contacts, then stopped for results. The
native start and chase/side states were captured separately. Five selected
CPU tests passed, the supervisor's harmless timeout self-test passed, and
three exhaust hashes match their source receipts. Fresh UI review returned
ship after the subtle-treatment fixes. Physical input and heard audio remain
unverified. This replaces the earlier panel-backed HUD in the candidate.
