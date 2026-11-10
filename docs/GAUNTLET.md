# Cinder Unity candidate loop

2026-11-08 Pacific. Required player-facing scope is lowrider culture. Safari and buggy racing come later.

1. Read the shared guidelines, current handoff, exact donor source and user's latest direction.
2. Give each actual player build a unique `cinder-unity-rN` name. Preserve failing packets and the last reviewed control.
3. Run the pure simulation probe and loaded lowrider rig sweep, then explain every probe-line change against the previous reviewed baseline. First Unity candidate has no previously reviewed Unity baseline; retain the native references as donor comparisons, with scope differences stated.
4. Run hidden, silent, bounded captures through `tools/unity/Run-Cinder.ps1`; respect all pause markers, free RAM/disk, process exclusion, cool-down, memory job and watchdog.
5. Bind exact executable, managed code, meshes and source hashes. Per review: runtime receipt, three to six stills, a clip no longer than 90 seconds, and replay inputs. Deliveries add file hashes.
6. Have agents who did not author the reviewed work inspect the exact player evidence. Score presentation and observable gameplay out of 10 with written findings. Use the weakest required aspect; no averaging away a broken mechanism or menu.
7. Repair actionable findings and build a new revision. A prior source review, native review score or screenshot never validates changed bytes.

## Gates

| Level | Meaning | Gate |
| --- | --- | --- |
| 1 | Technical migration / greybox | Buildable module, pure fixed-clock model, meaningful probe. Explicitly incomplete where applicable. |
| 2 | Reviewable prototype target | All required mechanics and menu flows; fresh evidence, measured runtime, provenance; independent presentation and observable gameplay at least 8/10; no open P1. |
| 3 | Paid-release bar | Level 2 plus target-device 1080p/60, input/audio/comfort/comprehension/enjoyment validation by Oliver, complete UX and production assets. |
| 4 | Polished release target | Sustained platform validation, final sound/art/performance and regression coverage agreed for release. |

These levels are a project gate definition, not a claim that the port has attained them. Human-only aspects stay UNVERIFIED. The repository's conservative graphics profile cannot establish Level 3 performance.

## Required regression dimensions

Catalog and eight areas, exact tuning/dimensions, static support/weight/braking, grade hold/release, footprint and grip axes, actual flight and stable landing, no airborne drive/boost, wind-relative aero, hydraulics and speed interlocks, independent air channels, axle closure, full-state clone/restore/replay. Loaded rig tests additionally measure wheel attachments, dampers, rear links, ram seats, bellows rings and roof/coachwork endpoints. Host tests cover pad/menu bindings, settings, focus/pause, module frame placement and enter/exit cleanup.

## Native-relative visual gate, added November 9, 2026

Oliver rejected the r9 visual result. Its old presentation score is historical and cannot establish visual-fidelity acceptance. A functioning mechanism or menu does not compensate for a visibly degraded city, lighting or car finish.

- Freeze the native reference and candidate source/model identities. Audit actual content parity before rendering changes. Declare source-version differences, including the historical Luna comparison.
- Compare matched car state, camera transform/FOV, object pixel size, sun/sky direction, ground and resolution. Keep a neutral material setup and the actual Mercer street setup. Historical unmatched images can identify visible loss, but cannot isolate a shader cause.
- Evaluate city construction, lighting/grounding and each lowrider's finish/readability separately. No averaging a failed aspect into a single whole-prototype score. Reviewers first describe observed defects and native-relative preservation, without a requested passing score.
- Retain missing-content blockers and material/readability P1s until the exact new player proves them repaired. No acceptance from imported triangle counts, unchanged fingerprints, a brighter global grade, cropped hero shots or a different high-resolution beauty profile.
- Final evidence stays proportional: three to six stills plus <=90 seconds of original player motion per candidate packet, exact bindings and replays. Separate focused diagnostic packets may address a car or environment segment before the final whole-candidate packet.
- The current conservative resource/graphics guard and scene budgets remain binding. Restore static shade, calibrated material response and efficient authored detail before proposing extra real-time passes or higher caps. The r24 matched Catrina capture now measures 212 maximum draws and the full action take 216; retain the distinction between measured draw counts and active geometry versus GPU submitted triangles.

Current r24 state: finite technical checks pass and independent sampled native-relative preservation repairs are supported. City 6/10, cars and lighting 7/10 keep the broader Level 2 art gate NOT MET. The authorized Patcher publication is explicitly a prototype. Final reports and proof are in `docs/unity/`, `docs/unity/restoration/` and `art-review/unity-r24/`; rejected reassessment evidence remains intact.
