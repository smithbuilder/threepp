# Vehicle Tuning Playground

November5 close-up/boost update: **90 physics checks pass**, with all79 baseline values unchanged. New truck front/rear suspension and driver's-eye cameras, optional ground boost, and a [46-second native review film](build/truck-suspension-film/Baja427-Suspension-Cabin-Boost.mp4). Exact current build/verification: [truck close-up checkpoint](docs/baja-427/SUSPENSION-FILM.md) and `build/truck-suspension-film/delivery-receipt.json`. The previous playground/showcase delivery below is preserved history.

Enable **Arcade boost (hold B)** in the controls and hold B with throttle. It uses a2.5second charge, recharges in6seconds and increases ground drive through the existing grip model. Boost defaults off; airborne motion and landings remain physics-driven. C/the camera picker now also offers suspension close-ups and driver's eye. The new camera placement is calibrated for Baja427.

Previous baseline verification (November 5, 2026): **79 physics checks, six existing CPU
regressions and six supervised native review sessions passed**. Exact executable,
asset and source identities are in
[`build/suspension-playground/delivery-receipt.json`](build/suspension-playground/delivery-receipt.json).
Both jumps were captured for all three vehicles; the wind test, ridge and Baja
articulation also have native captures. Direct picker clicks and subjective
hands-on feel remain unverified after the app-control approval timed out.

Open **Launch-Playground.cmd** and choose **Vehicle Tuning Playground**, or open
**Launch-Suspension-Playground.cmd** directly. Select Safari, Original buggy or
Baja 427, then choose a test area. This is a free-driving test world, with no race
timer, checkpoints or opponents.

## Test areas

| Area | What it reveals |
| --- | --- |
| Level pad | Rest height, acceleration squat, brake dive and settling |
| Cross-axle ruts | Independent wheel movement, articulation and unloading |
| Bumps and whoops | Damper response over repeated short and long bumps |
| Steep climb / descent | Approximately 32-degree peak grade, gravity and brake hold |
| Narrow ridge | A curved 3.6 m crown with steep shoulders |
| Side slope | Approximately 22 degrees, downhill load transfer and grip |
| Jump line | Two Excitebike-inspired takeoff ramps, lower landing slopes and runout |
| Wind tunnel | An open test gantry, steady cross/head/tail wind and repeatable gusts |

The jump assist starts at 10 m/s (36 km/h). Approach speed is adjustable. The
vehicle actually leaves the ground: no launch impulse, animation trajectory or
in-air steering assistance is applied. Landing forces act on the same body and
suspension as normal driving. Wind arrows indicate the applied uniform airflow;
they are not calculated streamlines around the body.

## Controls

- W throttle, S brake, A/D steer, Space handbrake; G selects forward/reverse.
- R resets; P pauses; C cycles chase/low-side/front/overview cameras.
- O enables mouse orbit; H hides or restores the controls.
- Trail assist uses the pedals and steering to repeat an approach. It brakes at
  the end of a test lane. Quarter speed makes suspension movement easier to see.
- Wind tunnel controls select airspeed, direction, gusts and brake hold.
- Each wheel shows compression from droop and supporting load. An unloaded wheel
  cannot produce tire traction.

The guarded launcher keeps the existing 960×600, 30 FPS, 512-pixel local shadow,
2 GiB process, heartbeat and deadline limits. The direct launcher allows a
five-minute visit; Escape exits immediately. It requires a passing CPU acceptance
receipt for the exact executable before opening a graphics context.

## What changed physically

The old rally modes combine a planar arcade driving controller with separate
vertical ride systems. This playground uses one six-degree-of-freedom Bullet
rigid body for translation and rotation, with suspension and tire forces at four
contact patches. Gravity, steering, braking, slip, weight transfer, airborne
motion and landings therefore affect the same body.

The setup has a fixed 240 Hz physics clock, per-vehicle mass/CG/inertia/springs/
dampers/travel/grip, a sampled tire footprint, contact loading and
friction limited by each wheel's supporting load. The displayed terrain and
collision terrain use the same triangles. The wind gantry's visible beams and
solid collision shapes also share one recipe.

This pass repaired low-speed friction and integration timing that caused parked
vehicles to creep, inertia calculated from undersized collision boxes that made
takeoffs rotate too quickly, and flat nose collision boxes that struck ramps
before the front tires could climb them.

The current Baja v3 mechanical rig is a presentation adapter: its wishbones,
uprights, telescopic dampers and solid rear axle receive the coupled solver's
pose and travel. Its separate legacy vertical solver is not run here. The
original race demos and their published/captured work remain separate.

## Repeatable verification

Run **Test-Suspension-Playground.cmd**, or:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Test-Suspension-Playground.ps1
```

The CPU path returns before creating a window, renderer, loading vehicle models,
or opening an audio device. It checks all registered vehicles and retains:

- `checks.csv`: named requirements, values, thresholds and pass/fail results.
- `physics.csv`: per-vehicle/per-trail positions, speeds, contact counts, travel
  and loads during the stress runs.
- `vehicle-specifications.json`: the exact SI vehicle specifications used.
- `result.json`: suite summary, vehicle count and area count.

The supervisor places these under `build/sessions/<session>/physics-audit` and
binds the session to executable and asset hashes. The helper publishes a current
receipt and vehicle catalog under `build/suspension-playground`. Failed sessions
are retained; a subsequent pass never erases the failure evidence.

The suite covers weight balance, four-wheel support, drop settling, ballistic
fall, absent airborne propulsion, steep-grade hold/release, steering, side-slope
grip and sliding, deterministic input replay, airspeed-squared drag, relative
airflow, crosswind load transfer, aerodynamic torque, gusts, mechanical travel,
and completion of both jumps upright. Automated results do not establish human
handling acceptance or sustained real-time performance.
The landing stress runs also check actual tire penetration against the sampled
footprint: the worst observed value across these fixtures was about 30 mm,
within the 35 mm numerical-contact tolerance. The mesh does not deform a tire.

## Adding vehicles and worlds

`showcase/PlaygroundVehicles.hpp` is the shared vehicle catalog. Dimensions,
mass, center of gravity, inertia, spring/damper rates, grip, drive force, collision
clearances and aerodynamic coefficients belong there. The picker and CPU suite
enumerate that catalog. A new body needs a visual adapter that consumes the
solver's chassis pose, per-wheel travel, steering and rotation; it must not
introduce another independent driving or terrain-following controller.

`showcase/PlaygroundTerrain.hpp` owns the test-area catalog and the surface used
for both rendering and collision. New driving areas automatically enter the
bounded trail stress loop; specialist fixtures should add their own measurable
acceptance criteria. The wind and jump fixtures demonstrate that pattern.

Only the selected visual model is loaded. Adding a long vehicle list must not
load every mesh and texture at startup. New vehicle IDs are accepted by the
supervisor only after they appear in the exact build's passing test catalog.

**Future games must expose “Vehicle Tuning Playground” as a selectable world or
mode and use the shared vehicle specifications and coupled physics.** Keep a
world/mode choice separate from the vehicle choice. Vehicles must be tested in
real terrain, not only posed in an asset viewer. `showcase/playground-world.json`
records the current guarded launch route and module boundaries.

Current Cinder Forest remains an older demo with its older controller. Selecting
it in the hub does not silently replace that controller with this new solver.

## Fidelity boundary

This is a tunable, physically coupled game model, not a measured vehicle digital
twin. Bullet raycast wheels have no separate unsprung mass or deformable tire;
the tire grip model is simplified, and the authored arm arcs/rigid rear axle are
visual approximations of straight suspension queries. There is no complete
drivetrain, tire thermodynamics, soil deformation, multibody axle solver or CFD.
Wind uses directional quadratic drag and an estimated center of pressure.
Vehicle coefficients are engineering estimates, not measured OEM data.

These limits do not require changing the renderer. They identify the next
physics components to improve if a specific test or hands-on feedback exposes
a remaining problem. Bullet 3.25 is pinned by source hash; only its CPU libraries
are linked. See THIRD_PARTY.md and the copied Bullet license.
