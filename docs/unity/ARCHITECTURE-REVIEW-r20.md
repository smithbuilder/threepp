# Independent technical component review: cinder-unity-r20

November 9, 2026, Pacific Time. Reviewer: migration_review.

## Verdict and independence

**PASS for the exact r20 simulation regression, finite loaded mechanics, sampled rigid-bone batching, stated camera-clearance regression and recorded capture provenance.** No new P0 or P1 defect was found within these component gates. This is not whole-game quality approval or visual acceptance.

The reviewer did not implement the simulation, mechanism posing, rigid-bone batching, camera fix or runtime driver. The reviewer authored the build-time `SurfaceShaderDiagnostics` helper, so this report supplies no independent approval of shader implementation or shader conclusions derived from that helper. The present work inspected source, hashed files and inspected retained reports. No editor or player was launched by this reviewer.

## Exact build binding

| Item | Independently checked result |
| --- | --- |
| Player | `builds/cinder-unity-r20/Cinder.exe` |
| Player SHA256 | `59e549c1b31425c704dc2f035273628c016f4e0dac17b74bc9e418f3cb624347` |
| Authenticode | Valid; Oliver Smith, thumbprint `A08442661C5E0FB332E3B5532382393E49D2D701` |
| Source fingerprint | `abce083872686ce28a7fc4b59ff766a9fda616fdf1d1e39d7d9beb9042792f4d` |
| Probe | `evidence/cinder-unity-r20/20261109-223313-644-Probe/` |
| Build receipt | Unity 6000.3.6f1, succeeded, zero errors, four warnings |
| Probe process receipt | Normal completion, 20.3277327 seconds, peak working set 329,543,680 bytes |

The executable agrees with latest-probe, probe-runtime and final capture receipts. The ordered source-manifest fingerprint was independently recomputed. All **5,327** listed source files were rehashed against disk with no drift. All **147** whole-player files and **33** delivered review-packet files were rehashed against the final delivery manifest with no discrepancy. This does not replace signature verification or hashing after any subsequent publication/transfer.

Twenty-three owning simulation, view, rig, runtime-probe and module source entries were also compared against the r17 source manifest and are unchanged. The final lighting, host and build work is bound by the r20 fingerprint; its material behavior is outside this independent component verdict.

The independent calculation and capture-argument details are retained in `build/cinder-independent-r20-binding.json`. Final review media and receipts are under `evidence/cinder-unity-r20/review/`. Four compiler-warning records remain in the build receipt; this is not a zero-warning build.

| Retained probe output | SHA256 and comparison |
| --- | --- |
| `probe.txt` | `30604ec0896f7c0b6824c5df44a9ee5dafaa7c70e412f5156571e9eb322eec1d`; byte-identical to r9 |
| `loaded-rig-probe.json` | `27c6db591ee3b36fb5c51ed98937af6b95e416b0f10fbea9b8456e2493997dd7`; byte-identical to r9 |
| `runtime-batch-probe.json` | `f73cb2279b161822d0dc84b22f02950005ef7af9dc5305c0c04d4cff34339f7a`; byte-identical to r17 |

## Component gates and their limits

| Gate | Result |
| --- | --- |
| Pure managed simulation | 204/204 PASS; seven donor vehicle definitions and eight areas retain prior regression coverage |
| Loaded mechanisms | 495/495 PASS across the actual three lowriders and all nine detail tiers |
| Runtime batching and camera | 148/148 PASS; 148 PASS lines, no FAIL lines |
| Actual source displacement / hidden-source tripwires | Each of nine tiers detects intentional source disagreement and restores agreement |
| Roof-slot visibility | Actual Nocturne cover participation checked at seven phases in each detail tier |
| Exterior / garage cameras | 24 clearance assertions across three cars, both 22-degree rolls, exterior modes 0/1/2 and garage |

The architecture remains a pure managed simulation behind a separate Unity view and module host. The simulation uses double state at 60 Hz with four 240 Hz substeps, deep state clone/restore, seeded input replay and runtime fingerprints. Its custom solver replaces Bullet numerics. Preserved tuning and regression behavior do not establish bitwise Bullet handling parity.

The 495 loaded checks retain the previously reviewed finite attachment scope and documented installation adaptations in `MECHANICAL-ADAPTATIONS.md`. In particular, Luna's authorized view-only 10 mm shackle-pivot installation correction resolves the donor closure incompatibility; it does not silently change the pure simulation or donor asset. The checks sample 27 travel/steering poses per tier and panel/roof phases, with positive flexible-geometry presence counts. They do not exhaust independent four-corner combinations, full +/-0.48 rad steering, continuous swept-triangle clearance or every driven terrain state.

The rigid-bone path groups compatible material, shadow and vertex-attribute masks, preserves actual rigid attachment owners and excludes deforming geometry, nonuniform owners and activation-switched ancestry. Original source hierarchy geometry remains available as independently posed comparison truth with its renderers disabled. The invariant compares an actual compensated `BakeMesh(..., true)` snapshot in world space against those current sources. It does not merely compare two construction-time copies.

All nine tiers exercise neutral, droop, bump, both split/steer directions, half-open and open fixtures in a translated, rotated module frame with scale 1.15. The largest sampled discrepancy is 0.00003130 m for Catrina, 0.00002919 m for Luna and 0.00002915 m for Nocturne, below the unchanged 0.0002 m threshold. Source-displacement and visibility tripwires make the check sensitive to frozen or ghosted source geometry. Nocturne covers have positive closed participation and zero participation from phase 0.02 through 1. The failed frozen-tube, ghost-cover and r15 snapshot-space packets remain retained; earlier failures were not waived.

The camera fix applies clearance after final camera framing overrides. In the retained 24 assertions the minimum clearance is approximately 0.35000032 m. The tests use the level test-ground surface and a nonidentity frame. They establish the former low-side/rolled-camera regression only, not universal building avoidance, every attitude/terrain combination or cockpit comfort. Cockpit mode 6 remains outside this exterior gate.

Budget measurement includes active skinned triangles and excludes disabled source renderers and inactive detail tiers. Renderer count is not draw-call count; this component review does not infer a frame-time or draw-budget pass from fewer renderers.

## Normal-render capture provenance and runtime driver

The final packet records six stills and a 2,070-frame, 69-second video. The five source roles below all finished normally against the exact signed r20 executable. Their launch arguments contain none of `-material-control`, `-colour-probe`, `-local-reflection-diagnostic` or `-sky-reflections-only`. Each actual material receipt says `none`, and each render receipt records material control `none` and colour control `false`.

| Role | Original capture | Evidence |
| --- | --- | --- |
| Garage | `20261109-223346-926-Capture` | One original frame, menu flag |
| UI | `20261109-223641-498-Capture` | 180 frames; all ten scripted UI assertions PASS |
| Catrina | `20261109-223700-925-Capture` | 780 frames; 1,560 retained fixed-tick inputs, modes 0/1/2/3 |
| Luna | `20261109-223739-453-Capture` | 240 frames; 480 retained fixed-tick inputs, modes 0/1/2 |
| Nocturne | `20261109-223759-931-Capture` | 870 frames; 1,740 retained fixed-tick inputs in mode 8, plus roof cycle |

The recordings use bounded D3D11 960x600/30 capture with silent audio. Catrina and Luna use the `culture-flow` review driver. Source inspection confirms that it generates ordinary `SimInput` values and steps `VehicleSim`, recording each fixed-tick input into `SimReplay`. It does not assign a desired chassis pose during the recorded sequence. Catrina includes 360 positive-throttle ticks, 300 positive-brake ticks and 390 reverse ticks. Luna's lift sequence changes modes while parked; it contains no pedal driving. Nocturne uses its real demonstration mode and host roof-cycle control, also without pedal driving. These are distinct capabilities and should be described that way.

All three retained replays include an initial state at tick zero and the complete recorded input list. Periodic pose receipts include current simulation state, input and fingerprint. The roof is a view mechanism: its phase is recorded in pose receipts, but is not encoded in `SimReplay`'s simulation-only input stream. A replay alone therefore does not reproduce Nocturne's roof-cycle capture. No new independent playback of these three exact capture replays was performed here; the 204-check runtime gate separately tests seeded replay and midpoint restore.

The scripted UI assertions cover car cycling without starting, entering Mercer, pause, settings without advancing simulation, back navigation, return to garage, quit confirmation and cancel. They exercise the actual host UI state machine with injected pad state, not a physical controller. The packager rejects diagnostic flags and checks receipts before composing the packet. Hash integrity and those controls establish provenance, not visual quality or physical input acceptance.

## Explicit exclusions

The retained batching checks measure positions and visibility. They do not measure transformed GPU-normal angular error, tangent handedness, GPU vertex-buffer output or shaded-normal parity. Generated shader pass dumps are diagnostic source, not GPU proof. This report does not approve lacquer, clearcoat, GI, reflections, sky, tone mapping, antialiasing or native-relative art fidelity. Fresh independent visual review must assess those surfaces and motion against the native references; r9's rejected visual approval is not restored by these probe results.

Physical keyboard/controller behavior, handling feel, heard audio, comfort, comprehension, enjoyment, sustained target-device performance and handheld 1080p/60 remain outside this verdict. Final publication identity must also be checked after transfer. Any change to the owning implementation or player requires its own build binding and applicable checks.
