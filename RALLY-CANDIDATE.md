# Cinder Forest Rally

An isolated successor to Timber Run. Launch `Launch-Cinder-Forest.cmd`, or choose
option 6 in `Explore-Examples.cmd`. The original driving study and gallery remain
available. This candidate is saved on `setup/windows-evaluation`.

## Play

- W / Up: accelerate. S / Down: brake and reverse. A / D: steer.
- Space: handbrake. C: cycle chase, close and side cameras.
- R: restart. P: pause. Escape: exit.
- M: enable/mute the original synthesized engine sound. Sound starts off.
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
The stage HUD leaves the road visible and displays a completion time.

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
the four Poly Haven texture hashes match the stored receipt. The original
engine sound is a two-second 24 kHz mono PCM loop with a reproducible generator.
No new Windows reset/display-driver events were found in this candidate pass.

A native window ran and exited cleanly at its 45-second limit. Computer-use
access timed out before any keys were injected, so physical keyboard feel,
controller support and heard audio are **unverified**. Scripted driving does not
close those acceptance gates. Longer-session system stability is also open.

Poly Haven texture provenance and license: `showcase/assets/LICENSE.md` and
`SOURCES.json`. All game geometry and engine audio are original code/content.
The game reads local assets and has no runtime download/API dependency.
