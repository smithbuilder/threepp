# Current handoff — November 5, 2026

Read this first. This is the current local checkpoint for **Cinder / engine-threepp** at `C:/Users/oliver/Projects/engine-threepp`. The user's latest request was to prepare this handoff after delivering the truck close-up video. No further implementation is queued; take the next iteration brief from Oliver.

Integration target: `main`. Oliver authorized checking in all completed work on November 5, then clarified that videos should stay off GitHub. This checkpoint combines the local vehicle/environment work with the published playground source, including the later Baja cameras and optional boost. Its history continues from the pre-video playground commit `cca75b589fbd776ae5004263976a174ece49f558`; later source and documentation are consolidated without introducing video binaries into the new `main` history. The previous local base was `setup/windows-evaluation` at `06ec693469d8d71c86115cf393ebaccb5f5fc8c5`; the published playground tip was `ee63383fdd5b08ec8725a6f3933db9c78bbf0cee`. Preserve the user's `safari.jpg`, previous candidates, reference files and all evidence under `build/`. Do not reset/clean the tree or rebuild every target to get oriented.

The repository previously used `master`; it had no `main` branch. The existing branches are preserved. Final review movies are indexed under [videos/vehicle-reviews/](videos/vehicle-reviews/README.md) and remain local, along with the narrated showcase and its native video clips. Source, assets, editable video projects and evidence are checked in; video binaries, generated native executables, intermediate captures and ZIP packages remain local. The cancelled upload did not create remote `main`. The former complete local checkpoint is retained on `codex/local-video-checkpoint-836ddcfb`; do not push that backup. The previously published playground branch retains its prior video history; no existing remote history was rewritten.

Fresh integration checks: all 90 supervised CPU vehicle checks pass across 3 vehicles / 8 areas, the six selected CPU regression suites pass, and the serialized truck/assembly audits pass. Two file-handling suites initially hit access-denied errors in the tool's temporary folder and passed using `build/main-check/temp`. No graphics run or behavior change was needed. The portable-library validator exposed an old ZIP that predated Baja's addition; the old archive is preserved as `build/fidelity-v1/history/Cinder-Environment-Assets-4d76de7d8f07.zip`. A refreshed six-asset / 45-file archive passes validation (SHA256 `292ca3c4ea01af1b8f84953515ca14794f7a41b7f73a83f86147f43752b901af`). The earlier resume receipt and archive hashes below describe the pre-integration checkpoint.

## User direction and decisions

Oliver wants much higher visual quality for sky, trees, dirt/ground and vehicles. Current results are a prototype, not AAA acceptance. Assets must be modular and reusable outside this engine, with portable formats, scale/pivot/material metadata and sources/licenses. Original buggy and Safari remain useful comparison vehicles.

Safari exhaust was researched using actual Porsche 911 Dakar footage; Oliver selected **deeper at low RPM**. The Baja truck came from a separate modeling chat and three files in Downloads. He flagged a floating hitch/receiver, questionable component fit and suspension that did not move naturally. Those were repaired before the three-car race. His latest iteration requested close-up bump footage, first-person cabin views and a small arcade jump/boost; that is now delivered and optional boost is playable.

## Start here / launch routes

- `Launch-Playground.cmd`: world picker. Vehicle Tuning Playground, existing Safari forest demo, or original engine showcase.
- `Launch-Suspension-Playground.cmd`: shared physical playground, starts with Safari; choose **Baja 427** in the vehicle picker. Eight areas: pad, cross-axle ruts, bumps/whoops, steep hill, ridge, side slope, two ramp jumps and wind tunnel.
- `Launch-Safari.cmd`: existing Cinder forest experience. Its older controller remains separate from the playground.
- `Launch-Baja-427.cmd`: isolated model/rig inspection bench.

Playground: W/S pedals, A/D steering, Space handbrake, G reverse, R reset, P pause, C cameras, O orbit, H controls. New front/rear close-up and driver's-eye camera placement is calibrated for Baja. Enable **Arcade boost (hold B)**, then hold B with throttle. Boost defaults off, has up to 2.5 seconds of charge and a 6-second recharge. It multiplies grip-limited ground drive by at most 2, requires supporting tyres and cancels with brakes; no airborne thrust or authored launch trajectory. UI/physical input and subjective feel still need human review.

## Delivered artifacts

All paths below are relative to the project root. These files were checked to exist at handoff; exact hashes and current-source parity are in [the resume-state receipt](docs/handoffs/2026-11-05-resume-state.json).

| Output | Location |
| --- | --- |
| **Latest: 46-second suspension / cabin / boost reel** | `build/truck-suspension-film/Baja427-Suspension-Cabin-Boost.mp4` |
| Latest film proof, source/session hashes, review sheet and controls | `build/truck-suspension-film/README.md`, `delivery-receipt.json`, `encoded-review-sheet.jpg`, `proof/provenance.json` |
| Three-vehicle 48-second race | `build/race-truck-film/Safari-Baja427-Original-Buggy.mp4` |
| Original 44-second two-vehicle race | `build/race-film/Safari-vs-Original-Buggy.mp4` |
| Other lane's narrated 80-second playground showcase | `videos/playground-showcase/outputs/Vehicle-Playground-Showcase.mp4` |
| Reusable mechanical v3 truck / inspection views | `build/baja-427-v3/Baja-427-Modular-v3.zip`, `mechanical-review-sheet.jpg` |
| Reusable environment pack | `build/fidelity-v1/Cinder-Environment-Assets.zip`; live library `asset-library/` |
| Deeper Dakar audition / driving exhaust preview | `build/fidelity-v1/Dakar-Exhaust-Audition.wav`, `Dakar-Native-Drive-Exhaust.wav` |

Latest film timeline: 0–6s complete truck/front wheel; 6–14s front mechanism half speed; 14–22s rear axle half speed; 22–28s cabin over whoops; 28–37s exterior boosted jumps; 37–46s matching driver-view jumps/landing. Cutaways deliberately hide body/cargo/near wheel and are labelled. Native frames are 960x600 at 30 fps; half-speed shots advance the same 240 Hz simulation at half rate, with no frame interpolation. Audio is temporary reconstruction from logged controls, generic CC0 loops, tyre noise and procedural landing thumps, not endpoint recording.

## Current identities and verification

- Playground executable: `build/windows-gl/bin/Release/suspension_playground.exe`, SHA256 `3f2bdfbfb84649675e8858cea38840634e4fb3ed43f0afba649678efb1271d9c`. Signature verified valid at handoff.
- Current Baja GLB: `showcase/assets/baja-427.glb`, SHA256 `f3aea63858c923f1de2ae97a922341758a978a2ddc3215a0fffbbfde6ac0f72a`. Source, library and playground runtime copies match. V3 package SHA256 `36deaf7440867109855dc71e7f51abfb79d49050516bd3e4ceae1081fc0af0b1`.
- Latest movie SHA256 `16d053b788309e277cbf3c841afed96297225030f425c85bad2b52054c12ed00`; 11,182,885 bytes, 1,380 frames / 46 seconds, H.264/AAC.
- Exact-build CPU acceptance: `build/suspension-playground/latest-audit.json`, session `20261105-101516-206`: **90 checks across 3 vehicles / 8 areas**. All 79 prior baseline values are unchanged. Added checks cover grounded boost acceleration, brake cancellation, absent airborne propulsion and boosted jump/landing.
- Six final film sessions exited 0 with empty stderr and no discarded physics backlog; largest observed working set about 204 MiB. Source/model/binary bindings are in the latest film receipt. Front/rear service traces and exterior/cabin jump traces match exactly for every logged physics field. Jumps include 41 fully airborne rendered states total and finish upright with four supporting tyres.
- Full audiovisual decode passed; 16 decoded samples covering cuts, flight and landings match source frames with maximum mean RGB error below 1.94/255. Audio measured -18.0 LUFS / -4.9 dBTP. Five new invalid capture profiles reject for the intended reasons. See `baseline-physics-comparison.json` and `guard-validation.json` beside the film.
- These are technical/artifact checks. They do not establish human enjoyment, listening quality, physical controls, handling acceptance or sustained real-time performance. No tests or native graphics were rerun for this documentation-only handoff; file hashes, source snapshot, signature, receipts and guard state were refreshed.

**Receipt trap:** `build/suspension-playground/delivery-receipt.json` and older handoffs contain the prior ED6427... executable / 79-check baseline. They remain historical evidence. Use the current `latest-audit.json` and `build/truck-suspension-film/delivery-receipt.json` for the 3F2BDF... build.

## Architecture / edit map

| Area | Authoritative files / boundary |
| --- | --- |
| Shared coupled vehicle physics | `showcase/PlaygroundPhysics.hpp`: Bullet 3.25, one six-DOF chassis, 240 Hz clock, contact/suspension/tyre/aero forces. Current Baja total mass 2,480 kg. |
| Vehicle specifications / areas / acceptance | `PlaygroundVehicles.hpp`, `PlaygroundTerrain.hpp`, `PlaygroundAudit.hpp`; UI/cameras/capture in `suspension_playground.cpp`. Only selected visual model loads. |
| Optional reusable arcade rule | `showcase/PlaygroundArcade.hpp`: engine-independent charge/eligibility/drive multiplier, no rendering/Bullet dependency. |
| Truck source and portable rig | `scripts/baja427_generate.py`, `baja427_audit.py`, `baja427_assembly_audit.py`; standard GLB/5 PNG maps/manifests in `asset-library/models/baja-427/`. Metres, +Y up, +Z forward, nominal static root Y=0.07. |
| Truck presentation | `BajaGeometry.hpp`, `RallyBaja.hpp`; stable `present(position,orientation,travel,steering,spin,height)` receives authoritative physics. Fixed wishbones/axle and telescoping dampers. |
| Older race motion | `BajaRide.hpp` is the separate 2,200 kg sprung-mass reduced vertical system for the scripted forest race. **Not stepped in the coupled playground.** `rally.cpp` / `RallyRace.hpp` own capture-only race staging. |
| Environment / Safari voice | `RallyForest.hpp`, `RallyGround.hpp`, `RallyDressing.hpp`, `RallyLighting.hpp`; `RallySafariPowertrain.hpp`, `showcase/assets/SAFARI-EXHAUST-SOURCE.json`. |
| Films / launch guards | `scripts/render-truck-suspension-review.py`, `scripts/render-race-review.py`; `Run-Evaluation.ps1`, `Test-Suspension-Playground.ps1`, launchers, CMake files. |

Future games must expose **Vehicle Tuning Playground as a selectable world/mode** and reuse shared specifications/physics. Preserve `showcase/playground-world.json` and this world/vehicle separation. Do not silently replace the existing forest controller or add a separate showcase-only driving solver.

Truck v3 repairs include frame-connected bumper/hollow receiver/pin bores, recovery mount hardware, uprights/pivot forks/shock towers, rear link brackets, inboard rear dampers, connected driveline, stationary calipers/spinning rotors and fitted spare carriers/straps. Targeted serialized assembly and 243-pose native mechanical audits passed. Authored hub travel is 0.268–0.52 m around 0.4 m rest. This is a visual linkage approximation, not a multibody axle or certified structural model. See [mechanical checkpoint](docs/baja-427/HANDOFF-MECHANICS-AND-RACE-V3.md) and [latest film checkpoint](docs/baja-427/SUSPENSION-FILM.md).

Environment work delivered a 1K photographic HDR sky, matched lighting, PBR forest/gravel materials, mature conifer prototypes/LODs and improved grass/boulders within existing budgets. See `asset-library/README.md`, `catalog.json`, `build/fidelity-v1/environment-review/FINAL-REVIEW.md` and the archived handoff. Keep engine adapters separate from portable GLB/HDR/PNG/JPG/OBJ sources. Temporary Porsche personal-project samples are excluded from portable packs; preserve their exact provenance. Existing truck generic voice is not a real recording of this truck.

## Native-run safety and exact workflow

A prior full-system lock prompted strict limits. Read `SAFETY.md` before any native run. All launches go through **`Run-Evaluation.ps1`**, with signed executables, sequential single-process mutex, 960x600 / at most 30 fps, a 2 GiB job, BelowNormal priority, heartbeat and deadlines. Keep the 512-pixel local shadow and existing graphics budgets. Do not raw-launch executables, raise resolution, remove pause files or use `-AcknowledgeIncident` as a routine bypass. Diagnose a failed/stalled session before another launch.

At this handoff `EVALUATION-PAUSED.txt`, `build/GRAPHICS_PAUSED.txt` and `build/evaluation-active.json` are absent. Recheck them when resuming; a future session can change this state.

Build only the target being changed, with two workers and node reuse off; sign before execution, then refresh exact-build CPU acceptance before playground graphics. Existing local signing authorization/workflow is established. Current useful PowerShell commands from project root:

```powershell
$taskCmake = 'C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
& $taskCmake --build build/windows-gl --config Release --target suspension_playground --parallel 2 -- /nodeReuse:false
powershell -NoProfile -ExecutionPolicy Bypass -File C:/Users/oliver/Projects/patcher/scripts/sign-windows.ps1 -Executable C:/Users/oliver/Projects/engine-threepp/build/windows-gl/bin/Release/suspension_playground.exe
powershell -NoProfile -ExecutionPolicy Bypass -File Test-Suspension-Playground.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File Run-Evaluation.ps1 -Example suspension_playground -Vehicle baja -Scene 2 -View 4 -AutoDrive -Sequence -Frames 180 -WarmupFrames 120 -Seconds 100
```

Sequence recording needs at least 1 GiB free. Each process is bounded to at most 900 captured / 900 warmup frames and the supervisor's deadline; keep takes short. Changing the EXE invalidates its CPU launch receipt. The prior build is preserved under `build/truck-suspension-film/baseline/`.

**Never run bare `ctest --preset evaluation-windows`:** it includes five GL tests outside the native supervisor. This happened earlier, was disclosed, and is recorded in `build/race-film/VALIDATION-NOTE.md`. For ordinary CPU regressions use `powershell -NoProfile -ExecutionPolicy Bypass -File Build-Playground.ps1 -Action Test`, which explicitly excludes them. Python with NumPy/Pillow/SciPy is at `C:/Users/oliver/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe`; use `-X utf8` and read PowerShell JSON as `utf-8-sig`. ffmpeg/ffprobe are on PATH. Build/sign/capture tools have needed elevated tool execution in this environment; keep the same supervisor rather than bypassing it.

## Open quality work for the next brief

- Human review of the latest reel and hands-on movement is still needed. Match any follow-up before/after tests; CPU pass is not a natural-feel verdict.
- Cabin remains a simple dashboard and steering ring, without working instruments or driver animation. New close-up/cabin placement is tuned for Baja; validate other vehicles before promising equivalent camera quality.
- Safari trail assist stalls before the steep-hill crest and rolls back in the 80-second showcase. That remains a tuning target; general finite-state trail checks did not establish climb completion. Do not hide it by moving the camera or teleporting the car.
- Higher environment/vehicle fidelity remains the broader aspiration: sparse foliage/flecks, prototype dirt/detail, generic truck voice and simple cabin still need art/audio work. Safari true stationary idle / steady high-RPM source quality is not fully established. Keep Oliver's deeper-low-RPM choice.
- Bullet wheels use raycast/footprint and simplified grip with no separate unsprung mass, deforming tyre, soil deformation or full axle linkage dynamics. Frame-mounted visual components and targeted clearance checks do not prove exhaustive moving-mesh clearance. Sweep moving versus fixed geometry across full travel when changing mechanisms.

No active subagent/build/capture work is assigned by this checkpoint. Earlier separate playground/Baja chat ownership notes are history, not a live claim. Verify current ownership before another coordinated lane; no permission to message other chats was granted by this handoff request. Preserve local dirty work from every lane.

## Preservation / deeper history

Three copied inputs are in `docs/baja-427/references/`: `Baja-427-Master-Reference.jpg`, `Baja 427 Rally Truck Blueprint.png`, `Baja-427-Suspension-Baseline.xlsx`; originals in Downloads were untouched. Preserve v2 packages and baseline folders as well as the current v3 pack. The personal `safari.jpg` is untracked and must survive cleanups.

The previous complete handoff is preserved byte-for-byte in [SESSION-HANDOFF-HISTORY-2026-11-05.md](SESSION-HANDOFF-HISTORY-2026-11-05.md). Other evidence: `docs/handoffs/2026-11-05-resume-state.json`, `2026-11-05-worktree-status.txt`, `SUSPENSION-PLAYGROUND.md`, `SAFETY.md`, `docs/baja-427/` and each delivered film's proof folder. These checkpoint files describe observed local state; no fleet ledger or external chat status was refreshed during this documentation task.
