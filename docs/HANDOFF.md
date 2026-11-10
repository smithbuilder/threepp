# Cinder Unity handoff

November 9, 2026, Pacific Time. Current signed player: **cinder-unity-r24**. Native-relative city, lighting and lowrider preservation repairs are independently supported in the inspected views. **Broader Level 2 art approval is not granted:** city 6/10, cars and lighting 7/10. Publish this as the explicitly authorized prototype, not a production-quality release.

## Needs you

No additional permission or product decision is pending. Oliver authorized commit, merge, GitHub main push and a new private-Patcher Cinder release. Physical controls, input feel, heard audio, comfort, comprehension, enjoyment and handheld 1080p/60 remain UNVERIFIED until he plays.

Publication checkpoint: full package prepared as `r-mwadnquf-eb902ae9`; GitHub integration and live signed selection verification are being completed. See `docs/DELIVERY.md` and the final publication receipt for the resulting state. The rejected r20 package was never uploaded and remains marked REJECTED.

## Play and scope

`PLAY-CINDER-UNITY.cmd` selects the current signed r24 player through the guarded runner. `START-HERE.md` has controls. The garage centers La Catrina, Media Luna and Nocturne: Mercer cruise, hydraulic/air sessions and workshop test grounds. Safari/buggy racing is deferred. Seven donor tune definitions and eight areas remain in pure simulation coverage; the three lowriders and their hero/mid/far art tiers ship.

Unity 6000.3.6f1, Built-in forward, Linear, D3D11, Windows x64, Mono, .NET Standard 2.1. The pure C# double simulation advances at 60 Hz with four 240 Hz internal substeps. View and host remain separate behind IGameModule. This preserves tuning and physical rules, not bitwise Bullet handling parity.

## What changed

- Faithful native Mercer export: all non-ground geometry and authored shade, 25 materials, 11 detailed buildings, 15 context shells, trees, furniture and road detail. Adaptive visual ground reduces city geometry from 566,118 to 383,961 triangles. Original lattice heights are exact; finite linear colour error is at most 0.007742. Simulation terrain is unchanged.
- Exact donor roughness/normal/coat values replace r9 clamps. Non-normal-mapped paint has a valid world coat normal. Display-space FXAA stabilizes fine chrome. Cameras clamp after framing overrides, fixing the underground three-wheel view.
- Original HDR sky convention, native one-sun extraction, calibrated diffuse SH and hybrid original mirror / sun-clamped rough reflections. C++/C# extractor fixtures match exactly. GPU reflection strength is 0.649902 for intended linear 0.65; sun RGB matches native units within 0.0004.
- One-weight rigid batches preserve real moving owners and switched roof covers. The omitted native two-sided canvas rule now has an explicit Standard fabric adapter. Headless structural tests and actual D3D checks are separate; normal/hidden cloth controls establish visible canvas contribution.

## Exact identity and evidence

Player SHA256: `7d78c95234b8c21a2f2a48e544eb888f43d52612d0c8680c7d6319128caa256a`.
Source fingerprint: `0e57c2129876c7765692f3fd50d0cfe0cd3a02d73c826f93c48c89c2c1c86d97`.
Runtime source commit: `0b3e518d7d2f9d73e641026db7bb059d58bfbb3f`.

Exact probes pass **204 simulation + 495 loaded-rig + 154 batching/camera/material checks**; ten scripted menu checks also pass. Sim and loaded reports remain byte-identical to r9. The prior 148 runtime checks remain; six native canvas-policy/tripwire checks were added. All nine detail tiers have finite sampled geometry/mechanics checks; runtime vertex error stays below 0.000032 metres. Twenty-four camera assertions preserve at least 0.35 metres clearance at both 22-degree rolls in a nonidentity host frame.

Real D3D proof covers the hero Nocturne canvas, with 29 periodic receipts: supported shader, declared Cull property, zero Cull value, three active renderers and all three parts in the camera frustum at full deployment. Mid/far have structural/source checks, not independently rendered tier acceptance. GPU normals and exhaustive continuous triangle clearance are not established.

`evidence/cinder-unity-r24/review/` contains six unchanged stills, a 69-second silent original-player clip, exact replays/pose receipts, full source/player/evidence hashes and a delivery manifest. `art-review/unity-r24/index.html` is the local gallery. The roof visibility controls are separate focused diagnostics; they do not enter the six-still main packet. The packager rejects diagnostic flags and requires real graphics roof receipts. Roof/service phases are host visual state; simulation replay inputs alone do not reproduce those phases, so retain periodic pose receipts and the driver arguments.

Independent final reports: `docs/unity/QUALITY-REVIEW-r24.md`, `ARCHITECTURE-REVIEW-r24.md`, and `docs/unity/restoration/*-REVIEW-r24.md`. Retain failed r9/r16/r17/r18/r20/r21/r22 evidence and corrected r20 review findings. An initially ambiguous low-angle canopy reading was resolved with matched hidden-cloth controls; do not infer visible coverage from pose values alone.

Build: zero errors and four retained shader compiler warning records (body/FXAA potentially-uninitialized diagnostics). Do not report zero warnings. Measured Catrina active geometry is 693,585 triangles and maximum draws 212 in the matched capped test; full action take peaks at 216 draws. This is an active geometry tally, not GPU all-pass submitted triangles. Final r24 versus r20 control: median 33.3465/33.3333 ms, p99 39.1596/34.9487 ms, external peak 435,875,840/437,104,640 bytes. The p99 is worse in this short PNG-IO/capped sample; no target-device performance approval follows.

## Remaining art and parity limits

The city needs populated/social character and a distinctive lowrider gathering destination. Fine chrome, reflection finish, glass/roof contrast and interior showcase remain P2 work. Native lamp-off/toggle and some service-removal helpers are not fully ported; current emissive defaults follow the GLB. Do not claim exhaustive native runtime-feature parity. The experimental CPU local-city reflection bake was rejected and is opt-in diagnostic only; normal play uses corrected sky lighting. Unity filtering/BRDFs remain different from native.

## Build, guards and preservation

Build a new unique revision through `RUN-BUILD-RUNNER.cmd -Revision cinder-unity-r25`, sign with the established Patcher signing helper, run the exact-player probe, then capture/package/review. Never reuse revision outputs. Publication procedure: `docs/unity/release/PATCHER-PUBLICATION.md`.

Automated runs remain hidden, silent, bounded and serialized: 960 x 600 / 30 fps, no MSAA, one 512 shadow, 2 GiB process job, 4 GiB free RAM, 15 GiB disk, cooldown, pauses, shared mutex and watchdog. Never clear a pause, kill another project or raise graphics caps. Guarded user play is five minutes.

`builds/` retains r24 and rejected-but-reviewed r20 control; older players are preserved under `build/_archive/players/`. Native C++ work, legacy launchers and other lanes' dirty vehicle files remain untouched and excluded from Unity commits. Videos stay local and off GitHub. No other project was modified.

Playbook task `cmw9qrsq000alle018qlbcxni`, verified seat `z2-codex@agents.playbook`. The canonical Windows helper shim invokes unavailable `py`; use its installed Python implementation with the existing Python 3.11 executable. No matching active Cinder Bridge thread was found; do not post to unrelated threads. For packaging from PowerShell 7, remove PSModulePath only from that process so child Windows PowerShell uses its own signature module. Keep actual signature verification enabled.
