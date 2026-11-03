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
pitch/roll inertias are1800/950kg m2. The chosen CG is680mm high and250mm
rearward of the body reference. These are fictional game tuning values,
not measured specifications of the reference car.

The body rotates around its CG. Its returned chassis origin therefore moves
in X/Z as well as Y; rendering must use the complete `ride.chassis` vector.
Front/rear springs are22.5/31.5kN/m with appropriate static axle preloads.
Rest travel is350mm, giving approximately32% sag within the unchanged
280-500mm mechanical travel. The dimension record's410mm reference remains
unchanged for existing geometry and Legacy callers. No suspension geometry
or reviewed clearance envelope is enlarged.

Spring, damper and tyre forces are separate. Rebound damping can pull down on
the body and lift a finite-mass wheel, rather than being discarded by a
nonnegative suspension-force clamp. `springForces` may be negative;
`forces` exposes nonnegative tyre normal loads for traction and effects.
Low/high speed damper slopes differ, with stronger rebound than compression.

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

The final signed6A924C58 review take is
`build/sessions/20261103-080423-871`:600native frames, no contacts or hard bump
corrections, actual travel282.39-494.13mm and minimum rear ground room249.438mm.
The independent changing-frame review accepts the one remaining crest hop and
settling recovery on this graded stage. Its source evidence is in
`build/safari-iteration-v2/review-final-6a9`. This is separate from the earlier
body-art score and does not claim subjective handling or heard audio quality.
