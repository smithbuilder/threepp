# Independent architecture review: cinder-unity-r1

November 8, 2026, Pacific Time. Reviewer: migration_review. This reviewer did not implement the simulation, host or view. This is a CPU and source review, not a visual or human playtest score.

## Final simulation re-review

**PASS for the pure simulation architecture and its stated CPU regression scope.** A fresh independent compilation of the revised source and a new CPU execution passed **204 of 204 checks**, exit 0. This clears the simulation blockers below. It is not final visual/gameplay acceptance of the Unity title.

The contact solver now uses actual kinematic wheel orientation and actual hub position for footprint sampling and friction axes. Catalog and station definitions are immutable to public consumers; returned arrays are copies and internal hot paths avoid those allocations. The jump fixture uses lane-following pedals and steering rather than an unsteered straight-line command, preserving actual physical takeoff and landing. Its threshold was not reduced. The complete course finishes beyond z = 182 m upright on four tyres. New checks exercise actual feature centers, hydraulic modes and interlocks, trapped fluid, parked air suspension and kinematic traction axes.

Final independent evidence:

| Artifact | SHA256 |
| --- | --- |
| `build/cinder-independent-probe-final.exe` | `39BED0001A917B1DC3696AA6346493C0586257ACE3AC12CA086AA9E7A06C9AB8` |
| `build/cinder-independent-probe-final.txt` | `BF53BB8407113729FDAD56846B89FED5634D32405F2974633F18FBB8EA1930D4` |
| `build/cinder-independent-source-hashes.json` | `F172A8C79864107709FD85B7AD33D2DB2765B3FC0C4452C176C0DD8C923DC3D8` |

The source hash manifest identifies each compiled simulation source. Earlier failure evidence remains separate. Final combined fingerprint is `405edc5fae408904-ddb2147991c1e354-46b8856fb2c38a90-00e2f0bedccf703d-ffcf2ca9b5e986dd-322d244038d8df63-b4a17b1d8e393cd9`.

The view findings below still require the root builder's correction and loaded-player review. The donor's complete numerical/visual behavior, final runtime performance and the running module's host placement remain outside this CPU verdict.

## Findings retained from first review

**Original verdict: changes required.** The managed simulation is a credible migration of the donor model and numbers. It has the required engine-free boundary, a 60 Hz tick with four fixed 240 Hz internal steps, deep state copies, seeded PRNG, replay input records and a fingerprint of authoritative state. It replaces Bullet numerics rather than promising bitwise donor parity.

Fresh independent compilation and execution returned exit 1: **157 of 158 checks passed**. The blocking check was `FAIL baja two physical jumps flights=1 air seconds=0.383333`. Evidence is `build/cinder-independent-probe.txt`. The author was notified and was investigating; a passing earlier run must not be reused as evidence for the changed solver.

## Findings

| Priority | Finding | Required outcome |
| --- | --- | --- |
| P1 | The independently compiled candidate fails the two-jump Baja fixture. | Repair the trajectory/contact regression and rerun the unchanged meaningful jump gate. Bind evidence to the revised sources and executable. |
| P1 | At initial source review, tyre footprint and friction axes used analytic steering yaw even for Luna and Nocturne. The donor uses their actual kinematic wheel rotation, including camber, tie-rod toe and axle roll. | Use the same kinematic rotation for visible tyre, sampled footprint and friction axes. Add a split-travel and steering fixture. The author reports this fix has been made; the subsequent independently run candidate is the one with the jump failure above. |
| P1 | The initial Unity view puts Baja and Catrina rear axle assemblies at zero lateral displacement, nominal longitudinal position and roll alone. Wheels use the full axle kinematics. | Pose the entire axle from the same `AxlePose.Center` and `Rotation` as the wheels. Validate moving links and rams against the loaded Unity meshes. Otherwise their apparent mechanical connection is not established. |
| P2 | Publicly mutable catalog entries, station definitions and solid arrays can affect later steps without changing `State` or its fingerprint. | Make simulation definitions immutable or snapshot and fingerprint mutable tuning in state. Prevent one host or module instance from changing another instance's rules. |
| P2 | Four-second area stability checks exercise the starts of courses, not their complete routes. Only Baja has the explicit two-jump completion fixture. | Retain the narrow wording of current checks. Add targeted course/landing coverage and baseline comparisons before claiming the donor's full acceptance suite has migrated. |
| P2 | The first mechanism probe checks one rear split-travel pose for closure and does not itself test Catrina three-wheel stances or the speed interlock. | Incorporate meaningful coverage for the actual exposed modes and travel limits. Independent supplemental checks below already demonstrate some of these behaviors. |

## Independent supplemental verification

The reviewer compiled the current pure C# sources using the Mono compiler shipped with the installed Unity 6000.3.6f1 editor, then ran only CPU console programs. No editor, player, graphics context or audio device was launched.

- A 9 by 9 rear travel grid covered authored travel ranges. Worst Catrina four-link closure error was 0.000001673 m; worst Nocturne error was 0.00000001154 m. No nonfinite hub positions were seen. Actual hub heights agree with requested rear heights within numerical precision.
- Front hub sweeps used both steering locks and eleven heights. Largest target difference was about 0.006254 m for Switchback and 0.000766 m for Baja. These retain authored rigid-pivot effects; the contact solver must use actual hub coordinates rather than assume exact requested height. Luna and Nocturne differences were below 0.000003 m.
- Catrina modes 2 and 3 each settled on three loaded tyres, with the expected opposite front tyre airborne. Body up components were approximately 0.947 and 0.961.
- Catrina at 7 m/s activated the hydraulic speed interlock and retained zero commanded hop preload.
- Nocturne held raised height within 0.000088 m over two seconds and settled in park with four contacts and an upright body.

Raw supplemental results are `build/cinder-independent-sweep.txt` and `build/cinder-independent-mechanisms.txt`. Supplemental harnesses are local evidence under `build/`; they are not gameplay implementation.

## Architecture strengths and limits

All simulation source reviewed references `System` only. State contains the chassis pose and velocities, wheel travel/load/spin/contact results, actuator values and phase, input mode, boost, wind, seed, tick and accumulated metrics. Clone isolates the arrays. Restore recreates the deterministic terrain and clears transient output events. Internal scratch impulses are reset before use each substep, so they need not be persisted. Events are transient outputs and do not alter subsequent simulation steps.

The seven-vehicle catalog and eight-area terrain preserve the donor's tuning and sampled collision surface recipes. The physical spring, damping, Coulomb grip, relative-wind aero and actuator preload approach is substantially stronger than a planar or animation-driven replacement. Full donor numerical equivalence has not been established. The native donor's 266-check suite is not replaced merely by a smaller probe passing.

This report does not establish rendered material parity, complete moving-rig closure, frame rate, memory behavior, host frame placement in a running player, input usability or Windowseat integration. Independent visual and gameplay review must use the final running candidate and its exact evidence. Human feel, heard audio, comfort, comprehension and enjoyment remain **UNVERIFIED**.
