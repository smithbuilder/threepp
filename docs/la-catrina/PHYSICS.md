# La Catrina: hydraulic movement and validation

La Catrina uses the playground's existing Bullet chassis, terrain contacts and
240 Hz clock. Hydraulic commands change spring preload at the four corners.
Contact forces lift and rotate the car; the same rigid body then coasts through
flight and lands. The renderer consumes that body's pose and wheel travel.
There is no prescribed body bounce, airborne lift force or separate driving
controller.

## Tune and controls

The reference supplies the 5.33 m length, 2.02 m width, 3.0226 m wheelbase,
1.53/1.51 m front/rear tracks and 0.2891 m tyre radius. Mass (1,850 kg), centre
of mass (0.62 m high, 0.18 m behind the axle midpoint), springs, damping,
inertia and tyre grip are game-model estimates. Drive force goes to the rear
tyres; braking and lateral grip remain available at all contacting tyres.

The exterior and collider ends sit 0.19 m behind the axle midpoint, matching
the reference's longer rear overhang. The central underfloor keel and suspension
anchors stay fixed between the axles. Catrina's metal-underbody contact friction
is estimated at 0.30, allowing a grounded belly to slide over a ramp; this is
separate from tyre grip and is not a measured material coefficient. The other
four vehicles retain their prior 0.65 body-friction setting.

- **Cruise low:** the hydraulic valves return all spring seats to baseline.
- **Front hop:** the front circuit charges quickly, holds briefly, then dumps.
  Its 1.85-second valve cycle allows takeoff, flight, landing and recovery.
- **Three wheel — left up:** the left rear corner extends, transferring load
  onto the right front and both rear tyres. The left front wheel lifts.
- **Three wheel — right up:** the mirrored circuit lifts the right front.
- **Raised ride:** all four corners receive a modest equal extension.

Above 6 m/s (21.6 km/h), hydraulic extension retracts automatically. The
selected mode remains selected and can resume after speed falls below that
threshold. Three-wheel travel is intended for a slow street cruise.

`hydraulics.extension` is **wheel-rate-equivalent spring preload**, with a
maximum of 0.58 m. It is not the literal exposed piston length. The visual
actuator requests cup movement at a 0.42 ratio, then stops at the authored
ram travel and the coil's compression limit. Its fixed top-to-gland distance
and rigid shaft length are each 0.245 m. The casing skin starts 0.030 m below
the top pivot, leaving room for its spherical head; cup distance ranges from 0.280 to
0.430 m, with a 0.310 m rest distance. A signed 0.114 m cup-to-seat minimum
prevents the cup crossing the spring. This visual stop does not retune the
simulation's effective preload. Mechanical droop stays independent of that
preload: local hub Y cannot drop below -0.12 m at the front or -0.28 m at the
rear. Maximum local hub Y is 0.42 m. Nominal hubs sit near 0.2891 m.

## Verified behavior

The signed CPU session `build/sessions/20261106-122115-849` passed **183 checks
across five vehicles and eight test areas**. Its executable SHA256 is
`DEE326B1BA9736E3686660BCE1A78B2D6B7E136FE6C78B9CFF954F4A592C2203`.
This session opened no graphics or audio device and loaded model SHA256
`8444acaabf320f15fc3157342f4d23baa0b03b701d99af365608f48c4c16cb3e`.
These measurements refer to this exact recorded session; studio inspection
uses a separate executable and is not the source of these physics results.

Every one of the previous four-vehicle build's **137 recorded checks retained
identical pass status, value and threshold**. The baseline session is
`build/sessions/20261106-004743-039`; the comparison is saved in
`build/la-catrina/physics-comparison.json`.

| Behavior | Measured result |
| --- | --- |
| Front hop | Both front tyres genuinely airborne for 3.48332 seconds total during a 10-second repeated-hop test |
| Sampled front clearance | Up to 0.637 m average clearance under the front tyres; rear tyres retain support |
| Charge before first takeoff | Front load rises from about 7.99 kN to 29.40 kN in the 10 Hz trace before flight |
| Hop stability | Body up-vector stays above 0.969093, about 14.3 degrees maximum total tilt |
| Landing contact | Maximum ray-footprint penetration 4.86 mm during hydraulic hops |
| Recovery | Returns to four contacts; speed 0.00208 m/s after an eight-second recovery |
| Left and right three-wheel holds | Each holds exactly three physical contacts for 3.99582 seconds in the final four-second measurement window |
| Three-wheel driving | Each side travels 5.36 m in four seconds; all 40 recorded samples retain three contacts, and the lifted tyre carries zero load |
| Speed interlock | Engages at 8 m/s and fully retracts extension in the recorded one-second check |
| Airborne hydraulics | Gravity-driven fall; no measurable hydraulic translation or rotation beyond the stated tolerances |
| Replay | Identical final position and orientation for repeated fixed hydraulic inputs |
| Shared terrain stress | Both ramps leave the ground and land upright; peak tyre penetration 4.92 mm across the generic trails |
| City drive | 12 route-corner transitions, 414 m travelled within the world during the 115-second test; building collision stops the chassis |

Detailed data is in the session's `physics-audit/checks.csv`,
`physics-audit/physics.csv` and `physics-audit/catrina-hydraulics.csv`.
The hydraulic trace is sampled at 10 Hz, while acceptance counters run at
240 Hz. The check named “hydraulic charge increases front ground load” records
the maximum over the entire hop sequence, including sharp landing loads;
its 47.54 ratio is **not** a pump-pressure or launch-force measurement. The
pre-takeoff values above are taken separately from the first charge phase.

## Fidelity limits

The system is a coupled game model, not a measured lowrider digital twin.
Hydraulics use bounded valve schedules and effective spring preload, without
fluid compressibility, motor current, reservoir dynamics or measured pressure.
Tyres use finite ray footprints; there is no separate unsprung wheel mass,
tyre deformation or contact-patch elasticity. Suspension links and the rear
axle are visual kinematic approximations of the four contact queries, rather
than a constrained multibody suspension. The motion ratio is an authored
approximation, not a reconstructed production linkage.
The coil mesh compresses axially; wire-section deformation and exact turn-to-turn
contact are not simulated. Its solid-height allowance is an authored limit.

The automated results establish force-driven movement, repeatability and
bounded recovery. They do not establish physical-keyboard feel, naturalness
to a human observer, listening quality or long-session performance.
