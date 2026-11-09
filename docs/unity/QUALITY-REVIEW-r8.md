# Independent quality review: Cinder Unity r8

November 9, 2026, Pacific Time. Reviewer: independent quality agent. I did not author the simulation, Unity runtime, importer, shaders, art kit or motion adapters. I reported issues during earlier revisions and inspected the revised player evidence.

## Verdict

| Required aspect | Score | Result |
|---|---:|---|
| Whole-candidate presentation | **7.8/10** | Below the Level 2 threshold |
| Observable prototype gameplay | **8.2/10** | Pass within the scripted evidence scope |

**The full Level 2 quality gate is not passed.** The weaker required aspect is presentation. No new confirmed P1 remains in the observed r8 path. The remaining visual work is finite material/aliasing polish, not a request to add features or make this prototype a paid release.

The complete motion evidence materially improves the gameplay assessment over r6: it now demonstrates both three-wheel stances, ordinary steering/braking/reverse, Luna's entire pump/hold/lower sequence, and Nocturne's air system together with its full roof cycle. These were missing evidence in earlier packets, not presumed code failures. The final gameplay score applies to those observable actions and menu state transitions, not human enjoyment or physical input feel.

## Exact candidate and evidence

All runtime receipts cited below identify revision `cinder-unity-r8` and Windows player SHA256:

`CA37ABD950A2592DBEB3D2FCFBDA4532081706DB314B116F819BF0D3172CD865`

| Packet under `evidence/cinder-unity-r8/` | What I examined |
|---|---|
| `20261109-012513-955-Probe` | Runtime receipt; pure probe summary with 204 passing checks; loaded-rig summary with 495 passing checks. These are technical evidence, not a playtest. |
| `20261109-012533-553-Capture` | Actual main-menu frame 0 and receipt. |
| `20261109-012547-048-Capture` | Actual UI frames 8, 53 and 163, plus all ten scripted PadState assertions. Earlier review also established the intended settings/back and garage flow. |
| `20261109-012843-596-Capture` | Catrina frames 0, 90, 210, 330, 450, 510, 570, 630, 690 and 779; all 26 saved poses; runtime receipt, replay and performance summary. |
| `20261109-012914-949-Capture` | Luna frames 0, 45, 90, 135, 180 and 239; all eight saved poses; runtime receipt, replay and performance summary. |
| `20261109-012936-208-Capture` | Nocturne frames 0, 90, 180, 270, 360, 450, 540, 630, 720, 810 and 869; all 29 saved poses; completed runtime receipt, replay and performance summary. |

I inspected ordered samples, not every intervening rendered frame. The three uninterrupted source takes comprise 26 + 8 + 29 = **63 seconds**. The 180-frame UI sequence adds six seconds for **69 seconds total**. An encoded reel still requires its own output/hash/decoder verification; this report reviews the actual player frames and saved poses.

## Presentation assessment

The three authored cars remain distinct, complete and recognizable. Whole-car framing retains the tires and road-contact region. Transparent glazing now shows the cabin rather than an opaque cream sheet. The rose/plum coupe, dark teal Fleetline and long black convertible have different proportions, trim and stance behavior. The moving suspension hardware and roof assembly give the title a clear lowrider identity.

The warm orange/cream navigation has a consistent hierarchy and readable action names. The car card clears the vehicle. Pause and quit action labels are present, and pad hints appear after scripted pad activity. The original r4 blank-label defect is fixed. An intermediate r6 missing-label impression was disproved by direct pixel checks and native crops; it is not counted against r8.

The final storefront entrances, window reveals, awnings, readable outward-facing signs and continuous curb improve the street substantially. The r7 mirrored lettering and sawtooth material boundary are repaired. The footer is player-facing location/time text.

The picture still falls just below the requested prototype bar for two visible P2 reasons:

1. **Fine paint/chrome response is noisy at ordinary framing.** Catrina's long side shows grain across the paint and sparkling, jagged narrow trim/wire edges. This is especially apparent in the side-motion sequence. The body reads more muted burgundy than the donor's broad smooth lacquer mass. A finite next pass should reduce the high-frequency paint normal/specular response and stabilize the finest chrome detail at this actual player distance. Validate a standing and moving side view; do not hide the issue by moving the camera farther away.
2. **Existing shop glazing reads as opaque colored panels.** The new geometric reveals establish depth, but the large green-gray panes have little controlled reflection or darker interior separation. A restrained reflection/value treatment on the existing glass materials would better connect the storefronts to the detailed cars. No new crowds, buildings, modes or props are required.

These are Level 2 presentation findings. They are not a demand for photorealism, target-device testing or a paid-release art overhaul. Earlier simplified foliage and repeated upper windows remain prototype-level limits, but are not additional blockers requested here.

## Observable gameplay assessment

**Menu path:** ten assertions pass for car selection without launching, session entry, pause, settings while the sim tick stays fixed, back, return to garage and explicit quit/cancel. Actual r8 frames show the relevant controls rather than relying on log text alone. This uses injected PadState values through the runtime menu path; physical InputManager/controller mapping has not been established by this test.

**La Catrina:** saved pose 60 records both front tires noncontact during the hop. It subsequently recovers four contacts. Mode 2 reaches left-front noncontact while the other three tires support; mode 3 reaches the opposite front noncontact. The body and exposed hardware visibly respond. The later ordinary drive advances from approximately Z 65.22 m to Z 75.60 m, includes nonzero steering with lateral displacement, brakes, reverses to approximately Z 67.98 m and stops. Inputs and state agree with the displayed drive/reverse modes. The camera retains the complete car through these maneuvers.

**Media Luna:** the retained take now starts neutral. Front actuator values rise from zero to approximately 0.304 m, hold, then return to zero. Every one of the eight saved poses has four supporting tires. The side samples show the corresponding front body rise, exposed hydraulic hardware, hold and return. This resolves the r6 evidence gap where warmup consumed the entire lift.

**Nocturne:** all 29 saved poses have four supporting tires. Air actuator values move from zero to +0.055 m at all corners, hold, lower to -0.050 m, return, then raise the left front alone to approximately +0.0534 m while the other three remain zero. The view shows the mild resulting stance changes. Roof phase moves from approximately zero to one and back to zero with visible deck opening, articulated deployment, raised canopy and stowing/closure. The mechanism remains an authored schematic, not a claim of measured production linkage behavior.

Together these observations support the 8.2 gameplay score for a bounded lowrider prototype. They do not validate every free-driving situation, all terrain or long-session handling. The pure probe and loaded sweeps supply additional regression coverage within their stated finite scope.

## Performance and remaining verification

| r8 take | Median / p99 capture interval | External peak working set | Maximum capture draws |
|---|---:|---:|---:|
| Catrina 26 s | 33.3387 / 33.7136 ms | 295,059,456 bytes | 687 |
| Luna 8 s | 33.3353 / 33.5440 ms | 264,077,312 bytes | 587 |
| Nocturne 29 s | 33.3377 / 33.8757 ms | 283,815,936 bytes | 634 |

These are capped 960x600/30 captures with PNG I/O. They are not 1080p/60 or handheld benchmarks. The listed geometry is approximately 0.58-0.69 million triangles in these scenes. Capture draw counts exceed the storyboard's 300-draw target; retain the measured result rather than substituting renderer counts. The internal performance memory field is zero, so this table uses the external supervisor receipts. The same-machine r4/r6 control comparison remains documented in the review history; it is not an r8 release-performance claim.

**UNVERIFIED:** physical pad and keyboard/mouse feel, heard audio, comfort, comprehension, enjoyment, target-device 1080p/60, long sessions, settings persistence after restart and the complete focus-loss path. These human/platform checks do not explain the 7.8 presentation score; the two visible P2 items above do.

Earlier evidence and verdicts remain in `QUALITY-REVIEW-r1.md`. A later material or renderer revision needs fresh hash-bound views and motion evidence. Do not describe r8 as independently quality-approved while its presentation score remains below 8.
