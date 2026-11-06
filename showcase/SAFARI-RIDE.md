# Safari sprung body and wheel response

The Safari candidate uses seven vertical degrees of freedom: body heave,
pitch and roll, plus one unsprung wheel height per corner. Horizontal driving
is still the rally game's arcade bicycle model. This is not a full rigid-body,
driveline or rotational tyre simulation.

The original open buggy retains Legacy response. Projected remains available
for comparison. Independent stationary-ground tests found that its inferred
road velocity can mistake body motion for moving ground and add kinetic energy
in a bump impulse. Passing simple drop tests did not detect that defect.

## Mechanical profile

`RallySafariRide.hpp` has920kg sprung mass and38kg per wheel,1072kg total;
pitch/roll inertias are950/650kg m2. The previous film used1800/950kg m2,
which gave its body a slower pitch/roll response than the open buggy.
The chosen CG is680mm high and250mm
rearward of the body reference. These are fictional game tuning values,
not measured specifications of the reference car.

The body rotates around its CG. Its returned chassis origin therefore moves
in X/Z as well as Y; rendering must use the complete `ride.chassis` vector.
Front/rear springs are22.5/31.5kN/m with appropriate static axle preloads.
Rest travel is380mm, giving approximately45% sag within the unchanged
280-500mm mechanical travel. The dimension record's410mm reference remains
unchanged for existing geometry and Legacy callers. No suspension geometry
or reviewed clearance envelope is enlarged. Available extension from rest
increases from70mm to100mm; the body rests30mm lower than the previous film.

Spring, damper and tyre forces are separate. Rebound damping can pull down on
the body and lift a finite-mass wheel, rather than being discarded by a
nonnegative suspension-force clamp. `springForces` may be negative;
`forces` exposes nonnegative tyre normal loads for traction and effects.
The revised wheel-equivalent damper has2100/5000Ns/m low-speed compression/
rebound slopes up to350mm/s, then500/1100Ns/m slopes. Its impact-speed slope
decreases rather than doubling as the previous4200/6400Ns/m profile did.
This retains slow body control while freeing rapid wheel compression/extension.
`SafariRideTuning::previous()` retains the exact old profile for diagnosis.

Tyre contact has220kN/m stiffness and1500Ns/m damping, bounded at45mm
compression. The visible rubber mesh does not deform; this remains a bounded
tyre/loose-soil penetration approximation. Its negative contact gap must not
be described using the earlier Projected model's10micrometre penetration
claim. Mechanical wheel travel remains inside the existing geometry sweep.

A sampled rolling crown queries the actual road over the tyre footprint.
It uses three axial rows and nine circumferential samples, with an approximate
shoulder crown. It is not an exact mesh collision or a triangle-ray test of
every tread block. Wheel joints still follow the existing rigid arm geometry.

## Contact integration

The state integrates at360Hz. Input position and heading interpolate between
calls so a render frame does not apply a full position change in one substep.
Ground constraints include the body/tyre-support Jacobian; only prescribed
planar motion contributes external moving-road velocity. A body roll or
support-radius change cannot masquerade as an external rising floor.

Bump and droop transfer momentum between the body and a finite38kg wheel.
Ground and internal constraints alternate in a unilateral solve. A wheel
at ground position but already separating is never treated as an infinite
mass partner. Static-ground impulses are checked for dissipation.

## Surface and scope

The old17cm sine at49km/h demanded1.5-2.1g of vertical road acceleration,
near the body's natural modes. The seven-DOF prototype bounced more on that
surface, despite dissipating energy in flat/inclined tests. Those failures
remain in `build/safari-ride-iteration`; they are not presented as a repair.

The Safari stage now grades the actual visible road to45mm centre ripple,
blending back to the old rough shoulders, with hills and banks retained.
Original rough-stage geometry and replay fixtures remain available. This is
an explicit scene change. Contact height comes from the rendered road/land
triangles; analytic terrain differed by up to61-67mm in measured route queries.

The signed review executable can run `runSafariRideAudit` before creating any
Canvas/audio/renderer. `Run-Evaluation.ps1 -Example timber_rally -PhysicsAudit`
uses that CPU-only path and writes its results under the guarded session.
It checks static loads, finite-wheel passive impulses, unsupported moments,
render cadence, flat/inclined drops, travel/compression and damping power,
then records four30s shared-controller scenarios. CPU invariants, native
motion review, human controls and subjective audio remain separate checks.

The earlier signed6A924C58 review take is
`build/sessions/20261103-080423-871`:600native frames, no contacts or hard bump
corrections, actual travel282.39-494.13mm and minimum rear ground room249.438mm.
The independent changing-frame review accepts the one remaining crest hop and
settling recovery on this graded stage. Its source evidence is in
`build/safari-iteration-v2/review-final-6a9`. This is separate from the earlier
body-art score and does not claim subjective handling or heard audio quality.
The user subsequently rejected its boat-like body motion and stiff suspension;
that earlier PASS does not establish acceptance of the current motion brief.

## Matched original-buggy comparison, November4

`Run-Evaluation.ps1 -PhysicsAudit -RideReplay <drive.ride.csv>` runs the original
Legacy buggy, exact previous Safari and current Safari over identical prescribed
planar inputs, on the same rendered45mm road mesh. Native sequence replay uses
the same path and common camera. This isolates suspension response; it is not a
human-controls test or proof of the closed-loop driving controller.
`-ReplayStartFrame` advances prior physics on the CPU before the first captured
image, and `-WheelInspect` gives the existing wheel/arch inspection camera.

The exact signed97BEB25B selected audit is
`build/sessions/20261104-065816-439/physics-audit/matched-comparison.json`.
Relative-to-road pitch RMS decreases from.025154 to.016009radians; all-air time
from.300s to.0167s. Individual tyres can still lift, rather than being glued to
the road. Original Legacy uses much more available travel and kinematic tyres;
its near-zero contact gaps are not proof of more accurate physical contact.

On the same rounded70mm single-wheel bump at6m/s, wheel compression is40.30mm
versus39.86mm, body lift9.92mm versus13.50mm, actual damper stroke33.84mm and
settling.322s. An early criterion demanding10% greater peak wheel compression
was rejected as an overshoot-sensitive proxy. Its failure is retained in
`build/safari-suspension-v3/criterion-refinement.json`. The regression instead
requires retained wheel response, reduced body lift, real damper stroke and
prompt recovery, alongside the existing travel/passivity/compression checks.
Two CPU tuning sweeps and the rejected soft first candidate remain preserved.
Actual changing native images still require independent review.

## Rear support repair

The new service cutaway deliberately removes body/arch/cabin/interior skins and
the right rear wheel for inspection. Engine, exhaust, chassis, arms and actual
shock eyes/shaft/coil remain visible. Normal driving retains the complete car.
This exposed an old fixed brace piercing the solid upper spring seat; a body-skin
clearance test alone had missed moving-versus-fixed-rig interference.

The rear tower now uses braced 45 mm tubes and 6 mm mitre fishplates around the
seat sweep, meeting the existing chassis rail/crossmember and unchanged upper
clevis. The lower forward approach passes above the rotating axle. The full
221-pose actual-triangle-to-support-capsule regression checks both rear corners,
including opposed wheel travel, full seats/coils/eyes/necks, arms, joints and
axles. It also verifies the fishplates are inside the checked support envelope.
It retains the original seat-collision fixture and the first repair's close-axle
fixture, rather than weakening the gates to accept either.

Final C++ minima: upper seat 13.00 mm, coil 34.87 mm, upper eye 6.31 mm,
drive axle 32.85 mm, other hardware 15.92 mm; existing body/tower room remains
at least 20.38 mm and rubber room 46.22 mm. The finite capsule includes the tube
caps conservatively. It is a rigid game-geometry check, not a chassis-flex,
fatigue, crashworthiness or fabrication certification.
Original failures, source hashes, scripts, predictions and actual C++ logs are
preserved under `build/safari-suspension-v3/packaging-audit`.

No road, body asset, audio, normal camera or original Legacy tuning changed in this
retune. Coil span, shaft insertion, arm ends and pins already used live wheel
contacts; the original buggy exposes them while the Safari's arches conceal
much of their movement. The force model uses wheel-equivalent rates, not a
finite-element simulation of the visible coil wire.

## Afternoon controls and environment iteration

The suspension profile and actual collision heights remain unchanged.
`safariPedalAcceleration` repairs the old full-braking-force reverse propulsion
and hard cutoff chatter: S brakes, then provides bounded low-speed reverse;
W recovers forward motion. CPU checks cover opposing pedals, reverse settling
and forward recovery. Reverse pedal demand also feeds the cosmetic audio.

The signed 88FE candidate completed a 37.5925-second scripted lap with zero contacts
in session 20261104-131227-078. Travel was 0.301934–0.500000 m, minimum rear room
.216406m, with 18 finite stop corrections and 3 camera hard clamps. This is bounded
automated evidence, not physical handling acceptance. Environment and recorded
Dakar voice changes are described in SESSION-HANDOFF.md. The original Legacy
response remains covered by its replay.
