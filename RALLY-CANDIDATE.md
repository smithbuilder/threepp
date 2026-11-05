# Cinder Forest Rally

An isolated successor to Timber Run. Launch `Launch-Cinder-Forest.cmd`, or choose
option 6 in `Explore-Examples.cmd`. The original driving study and gallery remain
available. This candidate is saved on `setup/windows-evaluation`.

## Play

- W / Up: accelerate. S / Down: brake and reverse. A / D: steer.
- Space: handbrake. C: cycle chase, close, side and cockpit cameras.
- V: toggle cockpit and return to the last exterior camera.
- `Launch-Cockpit.cmd`: start directly in the driver-seat view.
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


## Buggy clearance, exhaust and dust repair

The accepted panel-free HUD and recorded exhaust audio are preserved. Geometry
now lives in `RallyBuggy.hpp`: wider axles, shorter side pods/open wheel bays,
low rear collector and one hollow rear outlet under the engine. Upper/lower
suspension links and shocks follow wheel travel. Tyres steer/spin below the
same chassis frame used by the body, with 0.16-0.68 m available local travel.
The rig uses four ground samples, feed-forward spring following and bounded
travel in the tilted chassis frame. It remains an analytic arcade rig.

The old fixed faceted blobs are gone. `RallyDust.hpp` emits soft camera-facing
quads at the rear tyre contact points by distance travelled. Each has its own
world velocity, lateral spread, upward drift, drag, growth, spin, opacity fade
and 0.85-1.25 second lifetime. Pausing freezes them; restarting clears them.
There are at most 96, in a single instanced draw, with depth testing and no
depth writes. No new textures, downloads, audio or graphics features are needed.

`RallyVehicle_test` uses the actual model's fixed mesh bounds and a conservative
union of all tyre positions over full steering and bump/droop. Minimum computed
separation is 0.17787 m. All 360 sampled course poses pass the analytic contact
check. Particle checks confirm displacement reaches the uploaded instance
matrices, opacity decreases in instance data, particles expire and reset, and
all shader includes resolve. These run without opening graphics or audio.

Final native full-lap session: `build/sessions/20261102-071334-921`. 900 frames,
one lap in 28.6496 simulated seconds, zero obstacle contacts, exit zero after
47.54 wall seconds, sampled peak working set 136,904,704 bytes. The analytic
support model reports max wheel-contact gap 0.000160217 m; this is not a
triangle-level tyre deformation or physical-suspension accuracy claim. Travel
stays within limits. It emitted 1,530 short-lived particles with up to 1.98 m/s
world velocity. Static model bounds and runtime telemetry are engineering
checks; subjective motion quality and physical driving feel remain human review.

Six CPU evaluation checks pass. A first dust shader used an unavailable include
name, exited through a caught exception (code 1), and triggered the supervisor's
pause. The include was corrected, a CPU regression check added, and one explicit
controlled resumed capture passed before normal supervised captures continued.
That failure's logs and archived pause marker remain local; no guard was removed
or relaxed. Current runs have empty stderr. No Windows settings were changed.

Updated footage: `build/cinder-film/Cinder-Forest-Buggy-Fixes.mp4`.


The arcade circular obstacle footprint was also increased to follow the wider
transverse wheel stance. Final post-adjustment native session
`build/sessions/20261102-072609-729` passed all 900 frames with the same lap,
contact/travel/dust metrics, exit zero in 43.43 wall seconds and 130,506,752
bytes sampled peak working set. Its final PNG hash exactly matches the final
frame used by the new video. Both pause and active-session markers are absent.
This remains a circular arcade obstacle approximation, not mesh collision.


## Cockpit and articulated coil-over revision

`RallyCamera.hpp` adds View 3. C cycles four views; V toggles cockpit/last exterior.
`Launch-Cockpit.cmd` uses the existing supervisor and its 60-second limit. The
camera is seat-mounted, with fixed 74-degree vertical FOV, a 0.055 m near plane,
partial roll stabilization and no extra shake or speed zoom. View transitions
snap deliberately so the camera does not travel through the body. The cage has
more headroom and a slim dash with physical steering wheel and live instruments.

`RallySuspension.hpp` replaces stretching rods with a kinematic parallel
wishbone arrangement. Wheels follow the fixed arm's arc; upper/lower joints,
pivot brackets and bolts, uprights, tie rods, damper eyes and lower-arm bridges
make the connections visible. Damper barrels retain fixed dimensions while
chrome shafts telescope. Seven-turn springs update helix pitch while preserving
wire diameter and circular cross section. Ideal Ackermann angles differentiate
the inside/outside front wheels. The camera/needle/steering animation uses the
actual gameplay state. Left/right keyboard mapping is corrected for this +Z
forward model; it is tested against cockpit screen-right geometry.

The support model remains arcade ground following. These are articulated
kinematics and geometric checks, not a full dynamic suspension/tyre simulation.
CPU checks cover rigid arm lengths over all travel, constant spring-wire
thickness, nonintersecting turns, fixed damper dimensions, swept tyre/body
clearance with Ackermann/arc movement, four camera modes and a seated eye that
stays outside bodywork. Current conservative minimum fixed-body clearance is
0.040629 m; all 360 course poses pass the analytic tyre-support check.

All six CPU tests passed. Final cockpit full-lap verification:
`build/sessions/20261102-075345-790`, 900 frames, lap 28.6496 simulated seconds,
zero obstacle contacts, exit zero after 42.58 wall seconds, sampled peak working
set 133,627,904 bytes. Maximum analytic support gap 0.000116765 m; suspension
travel stayed bounded. Physical controls/comfort and native heard audio remain
human acceptance checks. Capture stderr is empty and safeguards are unchanged.

Motion proof: `build/cinder-film/Cinder-Forest-Cockpit-Suspension.mp4`.


## Rounded off-road wheels

The earlier flat cylinders, single-row blocks and solid wheel faces were
stylized placeholders. `RallyWheels.hpp` now builds an original, unbranded
racing-style assembly: a rounded hollow tyre carcass with bulged sidewalls,
shaped shoulders, 240 staggered bevelled tread blocks, curved sidewall markings,
open barrel/recessed eight-spoke face, outer beadlock ring with 24 fasteners,
five lug nuts, hub cap, valve stem, brake rotor and stationary caliper.

The rolling radius stays 0.54 m. The conservative half-width is reduced from
0.23 m to 0.20 m to match the narrower mesh, with the same contact/support and
suspension code. Wheel geometry is shared and tread/fasteners/spokes are
instanced. No new textures, renderer features, resolution or shader effects.
The tyres are rigid graphics geometry under the existing arcade model; no
pneumatic deformation or full tyre-force simulation is claimed.

Visual references were the manufacturer's BFGoodrich Baja T/A KR tyre page
(39x13.50R17 among its dimensions) and Method's 101 Buggy Beadlock. These inform
profile/rim proportions and mechanical features, not exact branded replicas
or real-world fitment. Manufacturer photos stay in ignored local research
files; the game uses only original code-generated geometry and CINDER markings.

- https://www.bfgoodrichracing.com/race-tires/bfgoodrich-baja-t-a-kr/
- https://www.methodracewheels.com/products/buggy-beadlock-machined

The CPU rig test now audits every actual vertex, including each tread/spoke/
fastener instance, against the radius and width envelope. It verifies calipers
stay fixed when rims spin. Existing full steering/travel clearance, arm/spring,
camera and dust checks are retained. Current conservative wheel/body clearance
is 0.0668868 m. All six CPU checks pass. Capture-only `-WheelInspect` provides a
close native viewpoint under the same supervisor; it requires a still/sequence
capture and does not change C/V gameplay camera controls.


Final wheel verification: `build/sessions/20261102-090432-305`, 900 cockpit
frames, one 28.6496-second scripted lap, zero obstacle contacts and exit zero.
Maximum analytic support gap 0.000116825 m; travel 0.16-0.67995 m. Sampled peak
working set 133,939,200 bytes; 42.60 wall seconds. Stderr empty. Close-up and
side sequence captures also exited zero. Safety caps/watchdogs unchanged.
Physical driving and native heard sound remain unverified.

Wheel motion proof: `build/cinder-film/Cinder-Forest-Wheels.mp4`, 22 seconds.


## Reference-led dynamics, materials and second vehicle (under review)

`RallyDynamics.hpp` integrates sprung-body heave/pitch/roll at120Hz from four
spring/damper loads, acceleration/cornering weight transfer and axle anti-roll
coupling. Compression/rebound damping differ and increase near bump. Wheels can
reach droop and lose contact; hard bump projection prevents penetration. The
horizontal controller remains arcade handling, with rigid tyres and kinematic
wheel contact rather than an unsprung-mass/friction solver.

Front wishbones keep rigid lengths. Rear wheels now follow boxed trailing-arm
arcs with drive shafts; telescoping dampers have reservoir/adjustment hardware.
The CPU checks exercise settling, static weight support, transfer direction,
heading invariance, render-rate independence, airborne release/landing and rig
lengths. The same guarded launcher still owns every native graphics run.

Surface detail uses shared original albedo/roughness/normal maps, separate paint,
coating, rubber and machined-metal response. Outdoor reflections use localCC0
Epping Forest01 fromPolyHaven, documented inassets/ENVIRONMENT-SOURCE.json and
ENVIRONMENT-LICENSE.md. The same512shadow map now has focused20m coverage and
light-space texel stabilization. No runtime network access or extra postprocess.

Dust has192advecting/fading soft quads.64instanced gravel particles follow gravity
and bounce/expire.768terrain-fixed tyre ribbon segments respond to contact/slip
and fade within32seconds; restarts clear all pools. The coarse land mesh is cut
out below the finer road, so its ribbon can sit2cm above analytic support rather
than floating16cm over the tyre contact height.

The original open buggy remains the default. A separately selectable Safari
coupe uses its own narrower chassis/wheel dimensions, lower seating and shorter
travel. `Launch-Safari.cmd` chooses it directly; the grid'sVEHICLE action also
switches variants. Its original geometry/PBRasset is reproducible from
scripts/generate-safari-body.py. Userprovided safari.jpg is a visual target,
not a shipped texture/model. This vehicle is subject to the independent fixed
8/10 acceptance gate inSAFARI-QUALITY-REVIEW.md; no pass is implied by this section.

Actual body triangles, including real wheel openings, are checked against
finite tyre cylinders through6468sampled steering/travel poses with20mm padding.
This replaces whole-meshAABBs for the curved Safari arches, without exempting
parts. Actual scaled wheel vertices and the driver eye's distance to body
surfaces are also checked. Native inspection court is capture-only, with a
flat physical floor and neutral backdrop, same engine/mesh/daylight and explicit
inspection label; normal forest driving must be checked separately.
