# Current handoff — November 5, 2026: truck close-ups, cabin and boost

Completed the new46-second native truck suspension/cabin/boost film. Start with [the current checkpoint](docs/baja-427/SUSPENSION-FILM.md). Movie: `build/truck-suspension-film/Baja427-Suspension-Cabin-Boost.mp4`. Optional playable boost and new cameras are in the existing selectable playground; boost defaults off. Exact current signed binary is3F2BDFBF..., unchanged v3 truckF3AEA638...,90 CPU checks pass and all79 baseline values are unchanged. Final six movie takes exit0/empty stderr. Full decode, matched replays and16 encoded image samples pass. Current receipt: `build/truck-suspension-film/delivery-receipt.json`.

Prior films, truck pack and playground binary/receipts are preserved. No active native evaluation or pause marker remains. Earlier delivery sections below contain historical executable/receipt identities.

---

# Previous handoff — November 5, 2026: selectable vehicle tuning world

The suspension-playground lane is complete locally. Start with
[SUSPENSION-PLAYGROUND.md](SUSPENSION-PLAYGROUND.md). `Launch-Playground.cmd` now
offers Vehicle Tuning Playground, the existing Safari forest demo, or the engine
showcase; `Launch-Suspension-Playground.cmd` opens the tuning world directly.

The requested narrated showcase is now at
`videos/playground-showcase/outputs/Vehicle-Playground-Showcase.mp4` (80 seconds,
960×600/30 FPS). Editable source, source hashes, transcript, review and verification
receipt are under `videos/playground-showcase/`. Seven fresh supervised captures
plus three final jump takes supply the footage. Longer video capture exposed a
remaining issue: Safari's assisted steep-hill run stalls before the crest and
rolls back. The film explicitly labels this as a tuning target; the automated
checks do not establish that Safari completes that climb. No physics changes
were made as part of the video task.

- Safari, original buggy and the current Baja v3 use the shared 240 Hz coupled
  Bullet rigid-body/suspension/tire model. Eight selectable areas cover pad,
  articulation ruts, bumps/whoops, steep climb/descent, curved narrow ridge,
  side slope, two Excitebike-inspired jumps and wind testing with gusts.
- The final signed executable is `build/windows-gl/bin/Release/suspension_playground.exe`,
  SHA256 `ED6427E687AD00437D1CF34320EF313796530C212A5422A8CE5BBD1062642ED8`.
  Current Baja runtime model matches source `F3AEA63858C923F1DE2AE97A922341758A978A2DDC3215A0FFFBBFDE6AC0F72A`.
- `Test-Suspension-Playground.ps1` passes 79 CPU physics checks for every catalog
  entry. The exact-build receipt gates native launch. Six existing CPU checks
  also passed. The six final native sessions exited 0 with empty stderr at
  960×600/30 FPS; all three completed both jumps upright. Evidence, hashes,
  scope and preview pointers are in `build/suspension-playground/delivery-receipt.json`.
- Repairs include coupled movement/steering, low-speed brake friction, step
  timing, full-vehicle inertia, shaped bumper collision hulls, and physical
  bump-stop contact impulses to prevent the original deep tire burial on landing.
- Only the selected visual model loads. Vehicle specs and areas are catalogued
  in `showcase/PlaygroundVehicles.hpp` and `PlaygroundTerrain.hpp`. Future games
  must expose this as a selectable world/mode and reuse the shared specs/physics,
  rather than implement a separate showcase-only motion controller. The launch
  contract is `showcase/playground-world.json`.
- Wind is estimated directional quadratic drag and pressure-centre torque,
  not CFD. Wheels remain raycast approximations without explicit unsprung mass
  or deformation; visual arm/axle paths approximate the physics queries. No
  subjective handling or sustained real-time performance acceptance is claimed.
- The direct Windows UI approval timed out; a guarded 180-second playable run
  still exited cleanly. Picker clicks and physical controls remain unverified.
  No graphics pause or active evaluation remains. No commit/push/publication.

Preserve the independent Baja/race work, previous candidates and user safari.jpg.
The repaired Baja mechanical rig is consumed through its `present` adapter;
its independent vertical solver is not stepped by this coupled world.

---

# Completed parallel handoff — November 5, 2026: repaired Baja and three-vehicle film

Completed the 48-second native Safari/Baja 427/original buggy race after repairing the unsupported hitch and suspension assembly/motion. Start with [the current checkpoint](docs/baja-427/HANDOFF-MECHANICS-AND-RACE-V3.md). Film: `build/race-truck-film/Safari-Baja427-Original-Buggy.mp4`. Reusable model: `build/baja-427-v3/Baja-427-Modular-v3.zip`. Mechanical images: `build/baja-427-v3/mechanical-review-sheet.jpg`. Exact checks: `build/race-truck-film/delivery-receipt.json`.

Concurrent suspension playground work owns coupled physics and its UI. Preserve its files/shared supervisor and CMake changes. This lane is complete; no native evaluation remains active at this checkpoint. Earlier sections are history, not current artifact identities.

---

# Race film and Baja truck handoff — November 4, 2026, evening

Historical two-car/v2 delivery. The November 5 checkpoint above supersedes these state claims; artifacts remain preserved.

Completed the user’s actual native head-to-head race video, then the added request to recover the Baja truck/reference files from Downloads and improve the model. All work is local; no commit, push or publication.

- Video: `build/race-film/Safari-vs-Original-Buggy.mp4` —44seconds,1320 native960x600 frames at30fps,H264/AAC;58,586,961bytes. SHA256 `4844ac4b3d4a0fdc29ffaa0c855832252755aecfda8f5067d4b154cd74084657`.
- Both actual existing vehicles race together: Safari compliant ride, original buggy Legacy ride, independent wheels/suspension/powertrain. Capture-only `-RaceOriginalBuggy` requires Safari+AutoDrive+Capture/Sequence at scale1; rejects portrait/replay/inspection/high-resolution. Normal gameplay retains its road and controls.
- Staged AI uses original-buggy catch-up governor, lanes+/-2.15m and8.6m road width at the same road vertex/index budget. Existing stones and matching colliders move beyond the two-car corridor; same pools. This is a scripted race film, not a fair acceleration/handling benchmark.
- Final signed binary SHA256 `268C127170A0E9D4075FF2339DCEFF37C953D0CA750261EF72F49EBC0FF482E6`. Safari body remains `82795FE6EA71DA661D85D43FDA9C932226E9E3B5E53089C16F53271D271E93BE`. Prior signed game is backed up at `build/race-film/baseline-timber_rally.exe`.
- Native final sessions:20261104-160435-748 (660recorded),20261104-160632-451 (660warmup+660recorded), both exit0/empty stderr. Second warmup matches every first-take state exactly. Minimum conservative 2D envelope separation0.400923m. Safari37.159031s, original37.475765s. Both finish; Safari obstacle contacts0.
- Audio: both cars’ actual per-frame logged bands, continuous sample phases and camera-relative stereo; reconstructed, not endpoint recording. Safari retains user’s deeper-low-RPM Dakar v2 samples, original retains CC0 buggy WAVs. Movie -18.1LUFS/-3.7dBTP. Exact sources/credits in proof provenance. Temporary Porsche samples excluded from portable packs.
- Checks: full video/audio decode/count/resolution/continuity pass;16 native frames and6 decoded samples inspected, including the take join. Four invalid race profiles reject before launch. All11 preset tests passed30.82s, but the direct ctest preset mistakenly included five small GL checks outside supervision; disclosed in chat and `build/race-film/VALIDATION-NOTE.md`. Do not repeat that command; use Build-Playground.ps1 -Action Test or explicit CPU-only exclusion. All subsequent game captures remained signed, sequential and supervised.
- Film limitations: existing sparse woodland/foliage flecks, regular dust puffs and abrupt arcade stopping remain visible. No AAA/human sound/handling/real-time performance acceptance claim. Read `build/race-film/VISUAL-REVIEW.md`, `README.md`, `delivery-receipt.json`, and proof provenance.

Truck:

- Found3 files in Downloads and copied unchanged to `docs/baja-427/references`: master reference JPG, truck blueprint PNG, suspension baseline XLSX. Source/copy SHA matches in `build/baja-427-v2/input-receipt.json`; originals untouched.
- Refined the existing original procedural model rather than replacing its modular interfaces: sculpted integral hood/recessed louvers, tapered recessed honeycomb grille, deeper projectors/C lights, wider window frames/split glazing, more neutral bronze, original dirt/roughness/normal maps, corrected top/front UVs and livery clearance.
- Self-contained GLB `asset-library/models/baja-427/baja-427.glb`, SHA256 `3055f1f63f4ef9489561257386a9c118ad93e6550d2cc9be8025cfcc315efe77`. Independent ZIP `build/baja-427-v2/Baja-427-Modular-v2.zip`; native front/side/rear/bed/steering/unloaded images and `verification.json` beside it. `Launch-Baja-427.cmd` opens signed existing native visual bench. Current runtime GLB matches source/library/package. Library catalog now includes vehicle; prior environment ZIP was preserved.
-209600triangles/104draws/5embedded maps; serialized finite/winding/index/hierarchy/ground checks and native loader/bounds/pivot/lamp audit pass. Six native views exit0/empty stderr. Preserved baseline asset/maps/authoring/audit/signed viewer in `build/baja-427-v2/baseline`.
- Rig scale/pivots remain meters/Yup/Zforward,3.18m wheelbase/.94m tyre diameter. Independent steer/roll/axle, suspension visual groups, tailgate, spares/tiedowns. Standard glTF2.0, no threepp dependency. Generator rebuilding uses NumPy/Pillow/SciPy and an authored427 font mask.
- Still a procedural visual approximation needing more cab/door/tread sculpting to match reference hero quality. No truck driving or full suspension closure was added. Workbook proposed solver coefficients were read but not applied to visual-only bench. See `docs/baja-427/REFINEMENT-V2.md`.

Keep all SAFETY.md guards and existing signature requirements. No active native evaluation or pause flag remains at this handoff. Preserve user safari.jpg and prior/rejected candidates.

---

# Safari fidelity handoff — November 4, 2026, afternoon

This current section supersedes the historical morning handoff below. The user
requested separate sky, vegetation and ground agents, better Safari behavior
and actual 911 Dakar exhaust, then specified modular assets reusable outside this
engine. After hearing the first audition, the user chose **deeper low RPM**.

## Current local delivery

- `Launch-Safari.cmd` uses the existing guarded launcher.
- Signed executable SHA256: `88FE0870014A8D63F234C0F028EE601A7E1C25DEEFA04EB8F30B16D0D097BEA9`.
- Body remains `82795FE6EA71DA661D85D43FDA9C932226E9E3B5E53089C16F53271D271E93BE`.
- Native preview: `build/fidelity-v1/Safari-Fidelity-Preview.png`.
- Portable bundle: `build/fidelity-v1/Cinder-Environment-Assets.zip`, SHA256
  `4d76de7d8f076b51b87c25fe8941150026b244015d8225f01e7780f9482721ea`.
- Import notes/catalog: `asset-library/README.md` and `asset-library/catalog.json`.
- Deeper 24-second audition: `build/fidelity-v1/Dakar-Exhaust-Audition.wav`.
- Reconstructed 20-second driving exhaust: `build/fidelity-v1/Dakar-Native-Drive-Exhaust.wav`.
- Exact bindings: `build/fidelity-v1/delivery-receipt.json`.
- Reviews: `build/fidelity-v1/environment-review/FINAL-REVIEW.md` and
  `build/fidelity-v1/audio-review/exact-output-review.json`.

Source is uncommitted on `setup/windows-evaluation`, based on `06ec6934`.
Nothing was pushed or published. Preserve the original buggy, personal
`safari.jpg`, previous 36-second movie and `build/fidelity-v1/baseline` EXE/WAVs.
Separate concurrent Baja427 work appeared in this workspace; its files and
supervisor/CMake additions were preserved. Do not attribute or stage that work
as part of this Safari iteration.

## Changes and reusable assets

Safari now has photographic 1K HDR sky/matched lighting, corrected longitude
seam filtering, less uniform fog, metre-scaled forest/gravel PBR materials,
scanned roughness, stronger soil/worn-lane variation, 1,000 tufts using the same
9,000 grass blades, and a portable smooth 56-triangle fieldstone replacing 70.
Terrain/collision positions and rock instance transforms are unchanged.

The final forest uses actual mature-fir authored boughs with restored UVs.
All 27,952 near foliage triangles remain; only wood was simplified. Combined
near prototypes are 40,883 triangles versus the original 41,744; the selected
far prototype is 1,028 versus 1,920. Counts remain 180 near / six draws and 240 far / two draws.
Portable GLBs retain their true 14.08–14.55m source heights; game instance scale
and placement stay in the adapter. All embedded maps are 1K/8-bit. Far trees use
complete adult silhouette bakes.

The initial needle-decimated and enlarged-sapling candidates were visually
rejected. Their models, captures and receipts remain under
`build/fidelity-v1/rejected-needle-lod` and earlier session folders. Do not reuse
their intermediate checks as final art approval.

The library contains standard HDR/JPEG/PNG/OBJ/GLB, source/license/hash/units/PBR
metadata, LODs and source recipes. No threepp binary or C++ is needed for import.
`scripts/prepare-environment-library.py` creates the bundle;
`scripts/validate-environment-library.py` checks its resources and integrity.
Porsche audio is temporary personal-project material, excluded from this pack.

## Controls and exhaust

Brake input now transitions smoothly into limited reverse propulsion; W
recovers forward motion. The old brake-force/reverse-cutoff chatter is gone.
Suspension tuning, body, road heights and the original Legacy response were
not retuned in this afternoon pass.

The voice uses actual Porsche Dakar driving/coast footage instead of the slowed
muscle-car source. Deeper low-RPM EQ follows user feedback. Phase-selected loop
joins reduce the idle swell. Idle remains provisionally coast-derived; no true
stationary-idle or steady high-RPM take was established. Exact source windows,
processing and hashes are in `showcase/assets/SAFARI-EXHAUST-SOURCE.json`.
Captured audio previews reconstruct runtime band controls before the listener's
0.75 master volume; they are not endpoint recordings.

## Verification and remaining boundary

Six CPU checks passed in 25.62 seconds, including actual GLB/PBR import, original/new
geometry budgets, unchanged collision surfaces, rooted grass, shared materials,
reverse recovery and existing mechanical regressions. See
`build/fidelity-v1/final-cpu-tests.log`.

Native sessions `20261104-131001-203` and `20261104-131227-078` use exact 88FE,
exited 0 and have empty stderr. The latter rendered 1,300 frames (700 warmup plus
600 recorded), completing one 37.5925-second scripted lap with zero obstacle contacts.
Minimum rear room was 0.216406 m; travel 0.301934–0.500000 m, 18 finite stop corrections
and 3 camera hard clamps over the full route. Peak sampled working set was
399,933,440 bytes. Rendering/capture took 87.30 wall seconds; this does not establish
real-time gameplay performance.

Fresh independent review inspected 53 source-bound native frames and adjacent
strips. Verdict: improved usable environment iteration; no major new defect
observed within scope. Mature structures remain coherent and the sky streak is
absent. Sparse woodland, simple distant proxies, isolated leaf flecks and
unverified continuous foliage shimmer/fine shadow crawl remain. No new
whole-car score, A/AAA quality or user acceptance is claimed.

Latest 24-second audition SHA256:
`26e416e395a49b395fc912b6ec015b9c5c5239c730d3254637cd67012c4438aa`.
Independent data review confirms correct source windows/hashes, -21.5 LUFS /
-8.1 dBTP, no clipping or silent 50 ms windows. Subjective listening, physical
controls, handling feel and long-session stability remain open.

The portable ZIP passes source/reference/license/hash checks, embedded 1K/8-bit
GLB resource checks and archive integrity. Selected runtime library files match
the canonical library, and original buggy audio hashes remain unchanged.

Next useful art work: denser composed undergrowth, true ground-material
blending, additional mature species, and coverage-preserving foliage/LOD work.
Keep current delivery and failure evidence when taking new feedback.

Existing safeguards and signing authorization below remain: sequential root
trials, 960×600, at most 30 FPS, 2 GiB job, heartbeat/deadline/supervisor. Higher
resolution remains unapproved. No new pause, graphics failure or driver/security
change occurred in this work. No memory update was requested or made.

---

# Previous morning handoff — historical delivery

Start the next session here. This document supersedes the older work-in-progress instructions in `build/ACTIVE-TASK.md` and the historical sections of the delivery checkpoints.

## Where we stopped

Oliver asked to end this session with a handoff. The latest suspension iteration and requested in-engine scene are complete and delivered. No build, capture, render, review or repair is still running or required for that delivery. Wait for the next brief or Oliver's feedback before starting another iteration.

The last implementation commit is **`06ec693469d8d71c86115cf393ebaccb5f5fc8c5`**, `Refine Safari ride and repair rear shock-tower clearances`, on **`setup/windows-evaluation`**. It saves 14 source/documentation files locally. Nothing was pushed, uploaded or published.

At handoff, source matches that commit. This handoff is a new file; the handoff pointer is in ignored `build/ACTIVE-TASK.md`. **`safari.jpg` is Oliver's personal untracked reference image: never stage, overwrite or delete it.** Preserve the branch, accepted launchers and original buggy.

## Start here next time

1. Read this document, then inspect `git status --short` and the current commit. Preserve any newer user work.
2. Watch [the delivered native scene](build/safari-suspension-v3/Cinder-Safari-In-Engine-Scene.mp4), or read its exact-file review below. Do not rebuild or rerender merely to recover context.
3. Read Oliver's new feedback. The remaining acceptance questions are subjective handling, suspension feel and exhaust character. Existing automated and scoped visual PASS results do not settle those questions.
4. If changes are requested, identify whether they concern body motion, wheel/rig motion, camera motion, materials or sound before changing several systems together. Keep the current delivery and failure evidence intact.

Suggested next-session prompt:

> Continue the Safari rally project in `C:\Users\oliver\Projects\engine-threepp`. Read `SESSION-HANDOFF.md` first. Preserve the current delivery, original buggy, personal `safari.jpg` and graphics safeguards. Review my latest feedback before changing anything. Do not treat old reviews as approval of new builds or increase graphics load without the required authorization.

## User intent and quality bar

The project began as a safety review and local setup of [markaren/threepp](https://github.com/markaren/threepp), then grew into original buggy and Safari-inspired racing demos. The Safari target is the attached `safari.jpg`: recognizable 911-like body lines, believable off-road wheels/suspension, roof cargo, realistic rear engine/exhaust/frame/bumper packaging and refined materials. It need not reproduce the reference's implausible exhaust/diffuser arrangement.

Oliver prefers subtle racing UI without black translucent panels, a cockpit camera, deep and powerful recorded exhaust, moving dust/trails, credible wheel travel and visible mechanical work. The external benchmark is the embedded game video in [this Reddit thread](https://www.reddit.com/r/TopologyAI/comments/1xlblst/comment/19s01gx949elf/?context=1&screen_view_count=5). Reopen and inspect the actual reference if it becomes relevant; this handoff is not a substitute for viewing it.

The latest complaint was that the Safari moved like a boat and its suspension looked too stiff. Oliver requested comparison with the original open buggy, continued iteration, then an in-engine rendered scene when done. The previous November 3 motion PASS was reopened by that feedback; do not defend it as user acceptance.

## Exact current delivery

| Item | Local path |
| --- | --- |
| Guarded playable Safari | [Launch-Safari.cmd](Launch-Safari.cmd) |
| Signed executable | `build/windows-gl/bin/Release/timber_rally.exe` |
| Canonical body | `showcase/assets/safari-body.glb` |
| Identical runtime body | `build/windows-gl/bin/Release/rally-assets/safari-body.glb` |
| Final 36-second movie | [Cinder-Safari-In-Engine-Scene.mp4](build/safari-suspension-v3/Cinder-Safari-In-Engine-Scene.mp4) |
| Scene manifest | [scene-sources-final.json](build/safari-suspension-v3/scene-sources-final.json) |
| Scoped motion/mechanism review | [FINAL-REVIEW.md](build/safari-suspension-v3/review-independent/corrected-mechanism-9184/FINAL-REVIEW.md) |
| Distinct final encoded-file review | [FINAL-SCENE-REVIEW.md](build/safari-suspension-v3/FINAL-SCENE-REVIEW.md) |
| Detailed delivery history | [DELIVERY-CHECKPOINT.md](build/safari-suspension-v3/DELIVERY-CHECKPOINT.md) — its top completion entry supersedes older pending/held entries |

These identities were freshly verified when writing this handoff:

```text
EXE SHA256:
9184E0FDF1D0FC0BCE8B5792A4358B67DD8CEF31AADE0EBD6AD2422009B86F1F
Authenticode: Valid, Oliver Smith

Canonical AND runtime safari-body.glb SHA256:
82795FE6EA71DA661D85D43FDA9C932226E9E3B5E53089C16F53271D271E93BE

Final movie SHA256:
5431A3FEF979242C3AC6D6803C01556AEBAECD75A04F067FD4ADB512082678A7
Final movie size: 41,816,572 bytes
```

The movie contains **1,080 actual threepp framebuffer frames at native 960×600 / 30 FPS**, H.264 High/yuv420p with faststart and 48 kHz stereo AAC. No upscale, frame interpolation or generated imagery was used.

| Movie time | Content | Native session under `build/sessions/` |
| --- | --- | --- |
| 0–6 s | Front inspection orbit | `20261104-075832-112` |
| 6–10 s | Rear inspection orbit | `20261104-080041-384` |
| 10–30 s | Actual normal scripted driving | `20261104-080232-924` |
| 30–36 s | Explicitly labelled suspension service cutaway | `20261104-075620-955` |

All four sessions use the exact current executable/body above, exited 0 and have empty stderr. This is a montage, not a continuous full lap. Audio is reconstructed from the same recorded exhaust WAVs using runtime-logged pitch/gain, **not endpoint recording**. Final audio measures −19.7 LUFS / −3.0 dBTP with no clipping or 50 ms silence windows. Subjective listening remains unverified.

## What the latest iteration changed

### Safari body and wheel response

`showcase/RallySafariRide.hpp` now has per-instance `SafariRideTuning`; reset preserves the selected tune. The previous profile remains available only for matched diagnostics. The original open buggy's Legacy response is preserved.

- Sprung mass 920 kg plus four 38 kg wheels; total 1,072 kg, unchanged.
- Pitch/roll inertias **950/650 kg·m²**, previously 1,800/950.
- Rest travel **0.38 m**, previously 0.35; unchanged mechanical limits 0.28–0.50 m give 100 mm extension and 120 mm compression.
- Front/rear springs remain 22.5/31.5 kN/m.
- Low-speed compression/rebound damping is **2,100/5,000 N·s/m** to 0.35 m/s; high-speed slopes are **500/1,100**. The previous high-speed slopes were 4,200/6,400, which resisted rapid wheel movement.

The model has seven vertical degrees of freedom at 360 Hz. Horizontal motion is still the arcade bicycle controller; this is not a full rigid-body/driveline/rotational tyre simulation. Tyre contact permits up to 45 mm bounded penetration, but the visible tyre mesh does not deform.

Matched original buggy / exact previous Safari / revised Safari diagnostics use the same recorded path, speed, camera and actual 45 mm graded road. The original buggy has 520 mm available travel versus the Safari's 220 mm and is not physical ground truth. The grading was an explicit earlier scene change; this iteration did not smooth the road again.

On the matched full path, pitch RMS fell from 0.025154 to 0.016009 rad, maximum contact gap from 0.207959 to 0.127031 m, and all-air time from 0.300 to 0.016667 s. An isolated 70 mm wheel bump retained approximately 40 mm wheel compression while reducing body lift from 13.50 to 9.92 mm. **The visual improvement is subtler than those percentages**; absolute crest pitch is still dominated by the road.

An initial softer tune failed the full route and was rejected. An initial test demanding 10% more peak compression was also rejected as an overshoot proxy; that failure and the criterion refinement remain preserved. Current tests require retained wheel response, improved body isolation, actual shaft work, bounded recovery and the existing physical invariants. Do not hide the failed candidates or describe these checks as global energy conservation.

### Real rear support interference repaired

The fixed forward rear shock-tower brace intersected the actual solid upper spring seat in **221/221** travel poses. The first repaired tower cleared the seat but left only **4.17 mm** drive-axle clearance at full bump; it was rejected.

The final tower routes around the rear/inboard side of the coilover with chassis triangulation and contained fishplates. Its lower brace routes above the drive axle. The final C++ 221-pose sweep reports minimum clearances of **13.001 mm seat, 34.875 mm coil, 6.313 mm upper eye and 32.853 mm axle**. The original and first-repair failures are explicit regression fixtures. These are game geometry checks, not manufacturing/fatigue certification.

Authoritative final sweep log: `build/safari-suspension-v3/packaging-audit/final-corrected-cpp-LastTest.log`. The folder preserves source snapshots, rejected routes and independent audit scripts/results. The body GLB was unchanged; the repaired live support geometry is in C++.

### Honest mechanism visibility

Normal closed bodywork hides much of the coilover. Safari `-WheelInspect` is now a capture-only service cutaway with body and right rear wheel removed, explicitly disclosed in the native HUD. Engine, exhaust, frame and actual moving suspension remain. The complete car remains in normal play; the original buggy inspection route is unchanged. Do not present the cutaway as ordinary driving or proof that the closed car communicates motion as clearly as the open buggy.

## Verification and remaining limits

- Six selected CPU tests passed after the final repair in 25.70 s: `RallyVehicle`, `Vector3`, `Matrix4`, `GLTFLoader`, `ObjectLoader`, `SceneArchive`.
- Independent motion/mechanism review **PASS within scope**: changing adjacent frames and extrema show seated eyes/pins, working spring/shaft and clear supports. All 39 CSV columns across 600 final normal frames exactly match the previously reviewed tune take; the final cutaway also binds to the matched replay.
- Final normal 20 s trial: no obstacle contacts, next gate 5, approximately 13.5 m/s, travel 0.301934–0.498399 m, maximum gap 0.122181 m, two finite-mass travel-stop corrections and no camera hard clamps. This is not a full lap or physical-control acceptance.
- Independent final-file QA **PASS within scope**: clean full decode, all 1,080 encoded frames bound to native sources, correct cuts/labels/format and measured audio envelope. Minor white HUD contrast limitations remain against bright foliage/sky.
- **Not established:** Oliver's acceptance, subjective handling or heard exhaust quality, long-session stability, continuous-player review, physical controller feel or higher-resolution quality.
- An older whole-car art review scored exactly 8.000 on an older renderer. **Do not transfer that numeric score to the current executable.** Current reviews are scoped motion/mechanism and exact-file technical PASS results.

Useful source/docs: [SAFARI-RIDE.md](showcase/SAFARI-RIDE.md), [SAFARI-QUALITY-REVIEW.md](SAFARI-QUALITY-REVIEW.md), [SAFETY.md](SAFETY.md), `RallySafariRide.hpp`, `RallySuspension.hpp`, `SafariRideTest.hpp`, `SafariSuspensionTest.hpp`, `RallyRideReplay.hpp`, `SafariRideComparison.hpp`, `RallyHud.hpp` and `rally.cpp` under `showcase/`.

The historical matched comparison is `build/safari-suspension-v3/Safari-Suspension-Comparison-Clean.mp4` (18 s, silent). It predates the final support repair; use it for motion comparison, not current geometry identity. November 3 v2 movies and earlier intermediate captures are preserved history, not the current delivery.

## Safety and standing authorization — preserve exactly

Oliver previously reported a **full computer hard lock**. The cause remains unconfirmed. Existing guards reduce load and bound a user-mode process; they cannot guarantee recovery from a driver/kernel/hardware lock.

Oliver explicitly approved continued **guarded native review trials** and existing **Azure signing of current/subsequent local review builds** under his publisher identity. Do not ask for those same approvals again. No publication is authorized by the signing approval.

Native GPU trials must remain sequential, owned by the primary/root agent, and launched through `Run-Evaluation.ps1` or the supplied guarded launchers. Keep **960×600, at most 30 FPS, 2 GiB Windows job, BelowNormal priority, heartbeat, deadline and single-process guard**. Do not raw-launch the executable, change graphics/security/driver/timeout settings, or remove a new pause flag to retry.

**Higher resolution / CaptureScale 2 / HD was not approved.** A previous automatic approval review rejected increased graphics load. The later phrase “in either fidelity” was not treated as specific higher-load authorization. Do not use supersampling, tiled rendering or MSAA as a workaround. Report the exact rejection and seek specific approval if a future requested action still requires it; continue unaffected work meanwhile.

At handoff verification, `build/GRAPHICS_PAUSED.txt`, `EVALUATION-PAUSED.txt` and `build/evaluation-active.json` were absent. No new lock or GPU hang occurred during the final trials. Check current state before any future launch; do not assume these observations remain current indefinitely.

## Commands if a new change warrants them

No rerun is needed just to resume. `Launch-Safari.cmd` uses the guarded 60 s Safari route. For CPU-only physics work, the signed game's `-PhysicsAudit` returns before Canvas/audio/renderer construction; do not revive blocked unsigned ad-hoc probes.

```powershell
# Guarded CPU-only audit (no GPU context):
powershell -NoProfile -ExecutionPolicy Bypass -File .\Run-Evaluation.ps1 -Example timber_rally -Vehicle safari -PhysicsAudit

# Build only when source changes justify it; two workers, no node reuse:
& 'C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe' --build build/windows-gl --config Release --target timber_rally RallyVehicle_test --parallel 2 -- /nodeReuse:false

# Relevant CPU checks after a change:
& 'C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/ctest.exe' --test-dir build/windows-gl -C Release -R '^(RallyVehicle|Vector3|Matrix4|GLTFLoader|ObjectLoader|SceneArchive)_test$' --output-on-failure --parallel 2

# Existing approved signing workflow, after a successful changed build:
powershell -NoProfile -ExecutionPolicy Bypass -File C:/Users/oliver/Projects/patcher/scripts/sign-windows.ps1 -Executable C:/Users/oliver/Projects/engine-threepp/build/windows-gl/bin/Release/timber_rally.exe
```

On this box MSBuild workers previously stalled at CheckingFileGlobs inside the sandbox; the successful build used the normal `require_escalated` tool mechanism. This does not authorize bypassing a denial. Verify the exact new signature with the helper/signtool before native execution, and bind new capture/review evidence to the changed binary and asset hashes.

For matched replay, `-RideReplay` accepts `build/sessions/20261103-080423-871/drive.ride.csv`; `-SafariRideProfile previous` is diagnostic-only. Native replay requires `-Sequence`, zero warmup, no portrait, and can use `-ReplayStartFrame 420` / `-WheelInspect`. Read current script parameters before composing a new run. Existing encoder: `scripts/render-safari-review.py`; silent comparison assembler: `scripts/render-ride-comparison.py`. Keep the native-engine workflow; no AI video replacement is needed.

## Coordination and access context

Previously requested independent reviewers completed the current work. Do not spawn new agents merely to recover context. Retain unbiased fresh review for materially changed work when requested; do not reuse an earlier exact-artifact PASS for a changed build.

The previous Playbook doctor reached the canonical service, but the own-seat secret grant was denied and fallback credentials resolved to `claude@agents.playbook` instead of expected `z2-codex@agents.playbook`. The helper correctly refused writes. No wrong-account write, duplicate project or bypass was attempted; this is historical access context, not a new live diagnosis. Run the helper's doctor before reporting a current access issue and obey its identity checks. Never copy credentials into this document, chat, logs or commits.

No memory update was requested or made. This is a project-local handoff. No new implementation or native execution was performed to write it.
