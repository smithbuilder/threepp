# Cinder Unity handoff

November 9, 2026, Pacific Time. Current player: `cinder-unity-r9`. **VISUAL ACCEPTANCE WITHDRAWN.** Oliver identified a regression in the city, lighting and cars. Fresh independent native-relative reviews confirm it. The technical simulation/finite mechanism results remain valid within their scope. r9 is a technical prototype and regression control, not an accepted visual replacement for the native title.

## Needs you

No additional decision or access is needed for the reassessment. Visual restoration is required before another acceptance claim. Physical pad/keyboard behavior, input feel, heard audio, comfort, comprehension and enjoyment also remain UNVERIFIED. Target-device 1080p/60 remains UNVERIFIED under the conservative 960 x 600 / 30 fps profile.

Start with `docs/unity/reassessment/REASSESSMENT.md` and `art-review/unity-reassessment/index.html`. Three fresh evaluators own the car, city and lighting reports. The November 9 reassessment changes documentation and evidence references only; it does not deliver a fixed player or change simulation/assets.

## What this is

A Unity 6000.3.6f1 Windows x64 port focused on lowrider culture. The garage offers La Catrina, Media Luna and Nocturne; cruise Mercer, use the car's hydraulic/air session or drive the workshop test grounds. Safari and buggy racing are deferred from the player-facing menu, as Oliver requested. The seven donor vehicle tunes and eight areas remain in regression coverage. The optional developer forest preview is not a port of the legacy forest controller.

The C++ engine, native launchers, other lanes' dirty source and donor models are preserved. Three frozen lowrider GLBs under `assets/unity/sources/` make the front-door port reproducible without the other lanes' uncommitted files. No other project was modified. Earlier r1-r7 players are preserved under `build/_archive/players/`; `builds/` keeps only r8 control and r9 current.

## Architecture and verified scope

- `Unity/Assets/Cinder/Scripts/Sim/`: pure C# doubles, seeded state, 60 Hz game ticks with four 240 Hz internal substeps. `Cinder.Sim.asmdef` forbids engine references. State clone/restore and full fingerprints are tested.
- `Host/`: standard `IGameModule` contract, standalone accumulator, copied Windowseat Input Manager axes, gamepad/keyboard/mouse UI, saved settings, focus pause and quit confirmation.
- `View/`: authoritative wheel and chassis pose, physical linkage adapters, separate render detail tiers, explicit glazing, lacquer response and camera-space interface. Shader polish never changes the simulation.
- The managed solver retains tuning and physical rules; it is not a claim of bitwise Bullet handling parity. Human handling approval is pending.

The last exact player probes pass 204 simulation checks plus 495 loaded-rig checks across all nine lowrider tiers. The scripted PadState/menu flow passes ten assertions. This does not prove physical device input. Loaded mechanics use finite sampled travel/steering, not exhaustive continuous triangle clearance; see the independent reports for limits.

`docs/unity/MECHANICAL-ADAPTATIONS.md` documents the explicit 10 mm Media Luna shackle-pivot installation correction and Nocturne hidden-scale/bellows fixes. Donor files remain untouched. Failed roof, leaf, material, framing and menu packets remain under `evidence/`; older players/imports are preserved under `build/_archive/`.

Player SHA256: `5CF25D276D9331F1C6AA01994BD641586EDA28EC52EFCEAC31E1D54D3898448E`. Source fingerprint: `14fa13c91317ac7b710f8e5b320b6ebee8fd4ed1a9eb5408c321e99f603962af`. Full delivery details are in `docs/DELIVERY.md`.

## Build, check and play

Use `PLAY-CINDER-UNITY.cmd` for the selected signed player. The guarded play visit is bounded to five minutes. Controls are in `START-HERE.md`. The intended normal default is desktop borderless, 60 fps, v-sync off; automated review stays hidden, silent and bounded.

For a new revision, run `RUN-BUILD-RUNNER.cmd -Revision cinder-unity-r10`. The preparation helper stages frozen sources and creates missing authored kits/detail tiers. The build refuses a used revision name and never opens the editor UI. Signing uses the established local Patcher signing helper, then run `tools/unity/Run-Cinder.ps1 -Action Probe -Revision <new-id>` before any capture/play. The exact-executable probe receipt is required by the launch guard.

Do not launch another editor/player while another Unity workload is active. All runs use the shared native evaluation mutex, process exclusion, 4 GiB free RAM / 15 GiB disk checks, 2 GiB process job, cool-down, pause markers and watchdog. Never clear pause files or delete old outputs to force a run.

## Review and evidence

The final packet is `evidence/cinder-unity-r9/review/`: six stills, a 69-second silent native proof clip, raw session bindings and hashes. Replays contain initial state and actual fixed-tick inputs. The input-only culture flow covers hop, both three-wheel stances, forward/steer/brake/reverse, Luna pump/hold/lower and Nocturne air/roof motion. This is regression evidence, not a human playtest.

The back-to-back control is the last fully reviewed r8 player on the same PC. Frame times include the 30 fps cap and PNG IO, so they cannot establish 1080p/60. Use external runtime-receipt working-set measurements; Unity Mono's internal Process.PeakWorkingSet64 returns zero here. Measured draw calls include shadow/post/UI work; renderer count is not draw-call count. Scene budget: <=700,000 submitted triangles and <=300 draws. Matched Catrina city result: 687,908 triangles, 685 maximum draws, so the triangle target is met and the draw target is NOT met. Current r9 versus r8: median 33.3314 versus 33.3307 ms, p99 33.6336 versus 33.6110 ms, external peak 298,438,656 versus 300,613,632 bytes. No material regression is established in this capped, short test. Draw reduction remains an optimization target; this is not performance acceptance for a paid release.

Historical r9 review: presentation 8.0/10 and observable gameplay 8.2/10; independent architecture PASS. Its broad presentation approval is superseded by Oliver's rejection and the fresh native-relative reassessment. It did not establish visual fidelity to the donor. Do not claim Level 2 acceptance while the reassessment P1 art issues remain. Original reports and evidence are retained unchanged: `docs/unity/QUALITY-REVIEW-r9.md`, `docs/unity/ARCHITECTURE-REVIEW-r9.md`. See `docs/GAUNTLET.md` for the amended visual gate.

## Provenance and coordination

Asset and audio records are under `assets/unity/`. Audio is original synthesized placeholder material with measured gains; automated takes are silent and listening is UNVERIFIED. Portable environment sources retain their original license records. Video files and player builds stay out of git.

Playbook doctor succeeded using normal network access: own seat `z2-codex@agents.playbook`, GB10 endpoint healthy. No matching Unity migration ticket existed. Assist notes `cmw8z79u100a7le01wb9avswr` and final `cmw92u1gp00afle01gea8pe5e` on the related native Nocturne task record the separate port without changing its ownership/status. No unrelated Bridge thread was used. Local source is on `codex/unity-lowrider-port`; native dirty work is intentionally outside this port's commits.

Packaging note: when launching `package_review.py` from PowerShell 7, remove `PSModulePath` only from that shell process environment first. Windows PowerShell then uses its own signature-check module. The helper must still report a Valid signature; never bypass the check.
