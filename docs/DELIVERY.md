# Cinder Unity delivery: cinder-unity-r9

November 9, 2026, Pacific Time. Reviewable lowrider prototype, Level 2 under `docs/GAUNTLET.md`.

## Needs you

Play `PLAY-CINDER-UNITY.cmd` for a guarded five-minute visit. Physical gamepad/keyboard behavior, input feel, heard audio, comfort, comprehension and enjoyment remain **UNVERIFIED** until Oliver plays. Handheld 1080p/60 is also **UNVERIFIED**. Draw-call reduction and final art/audio remain production work.

## Playable scope

Unity 6000.3.6f1, Built-in forward, Linear, D3D11, Windows x64, Mono. The main garage centers La Catrina, Media Luna and Nocturne. Choose Cruise Mercer, the car's hydraulic/air session or Workshop / Test Grounds. Garage selection, pad/keyboard/mouse navigation, saved display/look settings, pause, focus pause, return to garage and quit confirmation are implemented. Safari and buggy racing are deferred from the menu as requested. The broader seven-car catalog and eight areas remain available for migration regression coverage.

The managed simulation ports donor numeric tuning and rules. It is not a claim of identical Bullet handling. Four 240 Hz substeps run inside each 60 Hz game tick. Pure state, seeded events, restore/fingerprint and replay input records are separate from Unity presentation. The lowrider mechanisms use authoritative physical poses. The original C++ project and other lanes' work are preserved.

## Exact files and hashes

| Item | Location / SHA256 |
| --- | --- |
| Double-click launcher | `PLAY-CINDER-UNITY.cmd` |
| Signed current player | `builds/cinder-unity-r9/Cinder.exe` |
| Player SHA256 | `5cf25d276d9331f1c6aa01994bd641586eda28ec52efceac31e1d54d3898448e` |
| Source fingerprint | `14fa13c91317ac7b710f8e5b320b6ebee8fd4ed1a9eb5408c321e99f603962af` |
| Full local packet | `evidence/cinder-unity-r9/review/packet.json` |
| Delivery manifest | `evidence/cinder-unity-r9/review/delivery-manifest.json` |
| Manifest SHA256 | `21eafee91d379b64fd4a7c3aa56e4299da3a87d5d36b4560be1f26efdbeb43d2` |
| Silent native proof | `evidence/cinder-unity-r9/review/proof.mp4` |
| Proof SHA256 | `ea6bd9b799ef7ff14f3ca55fe11479ae4c15ec4ad708c0b5ae13e279356868b3` |
| Selected committed stills | `art-review/unity-r9/` |

The still named `04-catrina-hop.png` is actually frame 360, Catrina mode 3 right three-wheel stance, selected by highest body height. Its legacy filename is imprecise; this is not labeled as a hop in the delivery. Actual hop motion is in the clip, including at eight seconds.

The full packet contains six unchanged source stills, exact-player receipts, all source/evidence/player file hashes and the 69-second proof clip. The clip concatenates six seconds of scripted menu flow, 26 seconds of Catrina driving/hydraulics, eight seconds of Luna lift/lower and 29 seconds of Nocturne air/roof operation. It contains 2,070 original 960 x 600 frames at 30 fps, with no generated motion or audio. Full encode/decode, frame count, non-black images and current-source hash checks pass. Three decoded samples were visually inspected against the source captures. Builds, raw evidence and videos stay out of git; the small selected stills and reports are committed.

## Independent review and regression

| Gate | Final result |
| --- | --- |
| Presentation | **8.0/10 PASS**, independent quality reviewer |
| Observable gameplay | **8.2/10 PASS**, same independent reviewer, finite scripted input paths |
| Architecture / sampled loaded mechanics | **PASS**, separate independent migration reviewer |
| Pure simulation | **204/204 PASS** |
| Loaded car mechanisms | **495/495 PASS**, nine hero/mid/far prefabs |
| Scripted menu / PadState flow | **10/10 PASS**; physical device remains unverified |
| Build | Zero errors, zero warnings; valid Windows Authenticode signature |

Reports: `docs/unity/QUALITY-REVIEW-r9.md`, `docs/unity/ARCHITECTURE-REVIEW-r9.md`. The reviewers did not implement the work they judged. No confirmed P0/P1 remains within their stated scope. Full r9 simulation and loaded-rig output is byte-identical to the independently reviewed r4 baseline. Against r8, all 63 saved culture-flow pose fingerprints match (26 Catrina, eight Luna, 29 Nocturne); the final changes affect materials and edge smoothing. The earlier r8 presentation score 7.8 failed; r9 is a fresh verdict on changed bytes.

Loaded attachment tests cover finite height/steering samples and roof/panel phases, not every continuous mesh clearance or full steering lock. The documented Luna shackle pivot adaptation is view-only, within the existing bracket, and donor files remain untouched. Paint/chrome microdetail and bright building edges still have visible polish limits at the conservative resolution. This is prototype acceptance, not a paid-release verdict.

## Measured performance against the reviewed control

Back-to-back same-PC Catrina city benchmark: 180 measured frames after 60 warmup frames, same view/mode. Control `evidence/cinder-unity-r8/20261109-014010-512-Benchmark`; candidate `evidence/cinder-unity-r9/20261109-014055-963-Benchmark`.

| Metric | r8 control | r9 current |
| --- | ---: | ---: |
| Median frame time | 33.3307 ms | 33.3314 ms |
| p99 frame time | 33.6110 ms | 33.6336 ms |
| External peak working set | 300,613,632 bytes | 298,438,656 bytes |
| Submitted scene triangles | 687,908 | 687,908 |
| Maximum reported draw calls | 687 | 685 |

Budget: <=700,000 submitted scene triangles and <=300 draws. Triangle budget met; **draw budget NOT met**. The short capped sample shows no material regression and does not establish spare frame budget, 1080p/60, sustained handheld behavior or production performance acceptance. PNG output and the conservative 30 fps cap are included. The internal Mono working-set counter returns zero; the external guard receipt supplies the real measurements. Draw counts include shadows/post/interface and are not the renderer count.

## Provenance, retention and next work

Frozen lowrider sources, authored environment scripts, detail-tier manifests, licenses and synthesized audio records are under `assets/unity/` and `tools/blender/cinder/`. Quiet audio gains are measured, but no listening approval is claimed. The final player source and shared guidelines are committed on `codex/unity-lowrider-port`. No publication or push was requested.

Only r8 control and r9 current remain under `builds/`. Earlier players and superseded generated imports were moved into `build/_archive/`; nothing was deleted. Failed evidence stays available. Use the build runner for a new unique revision, sign it, probe it, then obtain fresh evidence/review. Preserve all existing native/other-lane dirty work.
