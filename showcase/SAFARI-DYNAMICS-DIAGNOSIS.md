# Safari suspension replay diagnosis

Recorded input: `build/sessions/20261102-235806-999/drive.ride.csv`.
Native summary: the adjacent `drive.json`. This is a CPU diagnosis, not a
claim that a repaired vehicle has been played or accepted.

## Reproduction

The `safari_dynamics_probe` CMake target links the existing local threepp
library and opens no graphics/audio context. Run:

```powershell
& build/windows-gl/bin/Release/safari_dynamics_probe.exe `
  --csv build/sessions/20261102-235806-999/drive.ride.csv `
  --out build/sessions/20261102-235806-999/ride-probe --sweep
```

It calls the actual `RideDynamics` for its baseline. Before any experiments,
it checks a local parameterized copy at every input; maximum state divergence
is exactly zero. The 3,483 input rows cover 900 rendered frames, with both
120 Hz driving and 30 Hz idle rows. The probe uses the original reset at
`(0,90)`, heading `PI/2`, original terrain plus the existing 20 mm support pad,
and the unchanged Safari wheel dimensions/travel. Native and replay agree:

| Metric | Native | CPU replay |
|---|---:|---:|
| Maximum heave relative to road | 1.46689 m | 1.46689415 m |
| Maximum absolute roll | 0.7 rad | 0.699999988 rad |
| Maximum rendered wheel gap | 2.02993 m | 2.02992916 m |
| Maximum rendered penetration | 0.00351143 m | 0.00351142883 m |
| Bump corrections | 259 | 259 |

Heave/roll match the native driving-step sampling; gaps/penetration match its
frame-end sampling, including the post-finish idle step. Road-relative body
roll/pitch are measured from `inverse(roadQuaternion) * bodyQuaternion`.

## Findings

The controller does not overload the coupe laterally in this run. Maximum
input lateral acceleration is 9.66177 m/s², with a 95th percentile of 9.19892.
The nominal static tipping estimate is 15.5806 m/s². No lateral clamp is
justified by this evidence.

Terrain response dominates. The road bank reaches 0.30855 rad and the road
pitch reaches 0.31002 rad, so absolute body roll alone is an incomplete
measure. Baseline relative body roll reaches 0.81683 rad, with 186 steps at the
0.7 rad body limit, 3.008 s with all four contact flags false, and 5.708 s
with effectively zero total normal load. Peak summed spring load is 40.294 kN
against 6.082 kN static weight. The 17 cm sinusoidal ripple can reach about
2.31 Hz along the 18 m/s centerline; the shared heave natural frequency is
about 1.715 Hz. Its nominal peak vertical road acceleration is about 35.8 m/s².
These estimates are context; the replay ablations below are the causal check.

| Same recorded X/Z/heading path and timing | Max roll | Relative roll | Heave | Wheel gap | Bump corrections |
|---|---:|---:|---:|---:|---:|
| Original | 0.700 | 0.817 | 1.467 m | 2.030 m | 259 |
| No lateral moment | 0.700 | 0.870 | 1.466 m | 2.241 m | 104 |
| No inertial moments | 0.329 | 0.281 | 1.093 m | 1.610 m | 131 |
| Ripple removed, other terrain retained | 0.700 | 0.693 | 0.914 m | 1.450 m | 185 |
| Flat ground, original inertial inputs | 0.038 | 0.038 | 0.006 m | < 0.000001 m | 0 |

Two structural behaviors amplify the launches:

1. Longitudinal/lateral body moments continue even when all tyre normal loads
   are zero. At the first roll-limit event, zero-load roll rises from about
   0.465 to 0.700 rad while lateral input rises from 7.1 to 8.1 m/s². There is
   no tyre force to supply that roll moment while airborne.
2. The hard bump limiter resolves every low corner by lifting the entire
   chassis and discarding negative heave velocity. It leaves the angular
   velocity driving that corner downward. Repeated corrections can jack the
   whole body upward instead of responding to the corner impact through all
   three sprung-body axes.

Stiffness-only changes are ineffective. Local 36/54/72 kN/m trials all retain
the 0.7 rad roll limit and increase the heave/gap peaks. Several changes to
damping, CG, and inertia without addressing the two structural behaviors also
retain the roll limit. The original open buggy should retain its accepted
coefficients and behavior.

## Probe-only mechanical experiments

`--contact-torque` scales inertial body moments by total clamped normal spring
load divided by static weight, bounded to [0,1]. It does not invent a lateral
acceleration cap. `--coupled-bump` replaces heave-only penetration correction
with a unilateral inelastic contact projection/impulse acting on heave,
pitch and roll through effective mass. It estimates ground vertical velocity
from travel rate and body contact velocity. Twelve deepest-contact iterations
reduce residual penetration. These are local experiments, not shipping code.

| Probe experiment, original speed | Max roll | Relative roll | Heave | Wheel gap | All wheels airborne |
|---|---:|---:|---:|---:|---:|
| Contact moments only | 0.334 | 0.293 | 0.944 m | 1.230 m | 2.567 s |
| Coupled bump only | 0.700 | 0.791 | 0.843 m | 1.442 m | 0.808 s |
| Both, original coefficients | 0.334 | 0.264 | 0.750 m | 0.882 m | 1.642 s |
| Both, 3400/4800 Ns/m damping | 0.336 | 0.227 | 0.641 m | 0.752 m | 1.417 s |
| Both, roll/pitch inertia 240/300 kg m² | 0.323 | 0.193 | 0.632 m | 0.816 m | 1.108 s |

Both repairs together avoid the angular hard limits and reduce penetration to
about 25 micrometres in the baseline-coefficient trial. This is promising
mechanical evidence, not sufficient reason to pick unmeasured inertia or
double the dampers. The reduced model still prescribes horizontal motion and
heading; contact-dependent moments should eventually be paired with a driver
model that cannot generate tyre acceleration in free flight.

## Physically slower path comparison

The generated `drive-slow-*.ride.csv` diagnostics interpolate the recorded
path at 120 Hz with longer traversal time; inertial inputs scale with speed
squared. They do not merely suppress forces while keeping motion unchanged.
They are controlled CPU comparisons rather than recordings of the native
controller.

| Approximate cruise speed | Model | Relative roll | Heave | Wheel gap | All wheels airborne |
|---|---|---:|---:|---:|---:|
| 13.5 m/s | Original | 0.687 | 1.007 m | 1.712 m | 0.858 s |
| 13.5 m/s | Both repairs | 0.100 | 0.293 m | 0.400 m | 0.342 s |
| 12 m/s | Original | 0.238 | 0.395 m | 0.707 m | 0.283 s |
| 12 m/s | Both repairs | 0.082 | 0.211 m | 0.286 m | 0.100 s |
| 9 m/s | Original | 0.071 | 0.178 m | 0.187 m | 0 s |
| 9 m/s | Both repairs | 0.063 | 0.084 m | 0.170 m | 0 s |

Recommended integration sequence: keep the open buggy unchanged; implement a
Safari-specific contact response using the two measured mechanical fixes;
select a physically attainable speed through the rough sections; rerun the
original geometry/clearance checks and a supervised native lap with a fresh
recorded-input replay. Validate actual rear-ground probes, tyre/body pad,
spring settling, landing energy, no force when unsupported, yaw invariance,
and render-frequency independence. Review native motion before any video
acceptance claim. Dimensions, wheel travel, body geometry, and the existing
20 mm pad must remain intact.

## Integrated CPU candidate

The measured two-part repair is now selected through the explicit
`RideContactResponse::Projected` profile on Safari only. `Buggy` and the
optional `RideDynamics::reset` response default to `Legacy`; no dimensions
or coefficient heuristic selects the model. The Legacy calculation order,
coefficients and hard bump response remain intact. Game telemetry identifies
the selected profile as `rideModel`. The horizontal driver and cruise target
are unchanged for the first native comparison.

Both actual shipping profiles match the independent diagnostic copies at
every input with zero divergence, including velocities, loads, travel,
contact flags and bump counts. Run `--validate-projected --projected` to
repeat that check. The tracked fixture and provenance are under `testdata`.
`RallyVehicle_test` retains its existing checks and adds native Legacy/open
buggy golden metrics, projected rough-route penetration at every physics
update, unsupported moments, static support, stationary-ground impulse energy,
unforced drops/landing, response reset preservation, yaw invariance and
stationary-ground render-interval equivalence. The moving game uses an outer
120 Hz accumulator; the latter test is not a moving-route resampling proof.

The bump Jacobian uses the same rotated CG-to-hub arms as the reduced spring
torques. It is the three-axis diagonal-mass approximation, not a full rigid
body Jacobian including terrain gradients, tyre deformation, and COM-origin
coupling. Its inelastic impulse is dissipative for stationary ground in that
reduced mass metric. The estimated moving-road velocity can transfer energy
from prescribed horizontal motion; free-flight X/Z/yaw remain kinematic.
Contact forces/flags represent the pre-integration spring sample, while bump
projection updates the body afterward. No claim of a full tyre-force,
unsprung-mass, or conserved full-vehicle-energy solver is made.

The guarded native run `20261103-001725-073` reproduced the repaired replay:
0.334183 rad maximum roll, 0.749799 m heave, 0.882301 m wheel gap and
0.0000252724 m penetration. It completed the original 28.6496 s lap at the
unchanged speed, with zero contacts, exit code zero and empty stderr. The
53,100 selected rear-vertex samples stayed at least 0.188616 m above support.
These are render-boundary samples, not exhaustive swept collision checks.

An independent read-only mechanics reviewer found no blocking integration
defect. The 18 m/s route remains a severe rough-road demonstration; the Safari
scripted controller now targets 13.5 m/s, braking above 14.5 m/s, for the next
native motion review. Open-buggy targets and player controls remain unchanged.

The subsequent native30s segment `20261103-002743-808` at13.5m/s reached gate7
with0contacts, exit0 and empty stderr. It measured0.249874m heave,0.388738m wheel
gap and0.0000126362m penetration. Its CPU replay matches those values exactly.
Road-relative roll peaks at0.0983711rad(5.64degrees), pitch0.186414rad(10.68degrees);
absolute roll0.31913rad includes the banked road. All four contact flags were
airborne for0.166667s out of30s. No angular limit was hit. This is a course
segment, not a completed lap. Fresh native visual review still follows the
separate suspension packaging and body repair.
