# Independent UX, observable gameplay and evidence review: r20

November 9, 2026, Pacific Time. Independent reviewer; did not implement the candidate, shaders, geometry, camera, input or packaging tools. No Unity editor/player was launched by this reviewer. Original PNGs, encoded samples, pose records, receipts, owning source and package files were inspected.

## Verdict

**FAIL for the complete observable feature set. Hold publication of r20.** A newly confirmed P1 remains: Nocturne's cloth canopy is absent in the fully raised roof state. The technical mechanism probes do not establish rendered cloth visibility.

| Aspect | Score / 10 | Scope |
|---|---:|---|
| Scripted menu/UX | **8.0** | Ten injected PadState transitions and visible controls. Physical device behavior and human usability are excluded. |
| Complete observable gameplay | **7.0** | Required roof presentation fails despite otherwise working lowrider actions. No average overrides the P1. |
| Overall art / Level 2 | **Not approved** | Separate city/car reports remain below 8; r9's withdrawn visual approval is not reused. |

My initial sampled inspection missed the absent canopy and provisionally described the mechanism sequence as complete. Direct comparison of the fully raised frame against the native roof-up reference establishes the failure. The provisional 8.2 observable-gameplay statement is withdrawn for r20. The final verdict in this report supersedes that interim message.

## Exact candidate

Player: `builds/cinder-unity-r20/Cinder.exe`.

SHA256: `59e549c1b31425c704dc2f035273628c016f4e0dac17b74bc9e418f3cb624347`.

Source fingerprint: `abce083872686ce28a7fc4b59ff766a9fda616fdf1d1e39d7d9beb9042792f4d`.

The player has a Valid Authenticode signature. The packet records 204 simulation + 495 loaded-rig + 148 runtime-batch checks, with ten scripted UI assertions. These are component/evidence results, not visual acceptance.

## P1: fully raised roof has no visible canopy

At `evidence/cinder-unity-r20/20261109-223759-931-Capture/pose-0420.json`, `roofPhase` is **1.0** at tick 842. The corresponding original `frame-0420.png`, copied as `review/06-nocturne-roof.png`, shows an open cabin with glazing and rigid frame members but no broad opaque cloth canopy. The native `docs/nocturne/review/native/roof-up.png` clearly has that dark cloth surface covering the raised roof. These cameras differ, but the presence/absence of the broad canopy is unambiguous.

R20 `frame-0450.png` shows cloth again at a partial roof phase. This supports checking sidedness/normal orientation rather than treating an endpoint/joint pass as visible coverage. Source inspection finds the native adapter explicitly sets every canvas material to `Side::Double` in `showcase/NocturneRig.hpp`, while the reviewed Unity import uses the GLB `doubleSided` flag. The coordinator is repairing that missing runtime policy in a new revision. I did not implement it or validate the future result.

Keep the failed r20 packet and unpublished package intact. A replacement needs its own player/source binding and actual fully raised cloth view, including normal-lit back faces through the fold. Do not relabel r20 evidence as validation of that change.

## Observed menu and other actions

I opened all six selected PNGs, plus these originals under `evidence/cinder-unity-r20/`:

| Session | Additional original frames inspected |
|---|---|
| `20261109-223641-498-Capture` | 0008, 0030, 0083: pad hints, Luna rear chase, settings |
| `20261109-223700-925-Capture` | 0060, 0240, 0510, 0630: actual front hop, left three-wheel, forward drive, reverse |
| `20261109-223739-453-Capture` | 0000, 0239: lowered start/end, in addition to selected raised hold |
| `20261109-223759-931-Capture` | 0000, 0300, 0420, 0450, 0869: open, intermediate, failing raised endpoint, partial return and open end |

All ten UI assertions were read. Car selection remains in the garage; entering drive advances the sim; pause/settings hold its tick; back, return to garage and quit/cancel transitions pass. Actual pause and quit buttons have visible text, and frame 8 displays pad wording. Settings expose frame limit, v-sync, display mode, invert look and sensitivity. This does not test physical InputManager mapping, persisted values after restart, complete mouse/keyboard parity or focus-loss behavior.

Catrina's front hop, both three-wheel states, forward steering and reverse are observable and agree with pose/input records. Its formerly broken right-three-wheel camera now retains the whole car. Luna's rear chase view retains pale sage roof/trunk and green body, repairing the reproduced r16 blackout. Its pump/hold/lower take returns to the lowered state with four supporting tires in every saved pose.

I read all **63 saved poses**: 26 Catrina, eight Luna and 29 Nocturne. Catrina includes the intended two-front noncontact hop and opposite front noncontact three-wheel states, then four-tire recovery and driving. Luna's model-root Y moves from about -0.0112 m to +0.1407 m and back to -0.0108 m, with four supporting tires in all eight records. Nocturne's records show mild all-corner air raise/hold/lower and the selected-corner action with four supporting tires in all 29 records. Its roof phase reaches one and returns, but the missing cloth means that phase record does not prove a successful complete rendered roof operation.

These findings support a useful technical prototype checkpoint, not a complete feature or visual approval. Separate r20 art reviews rate the city **6.0/10** and cars **7.0/10 each**; this lane does not replace those scores or average them into a passing whole-candidate result.

## Binding and encoder audit

- Independently rehashed **33/33 packaged review files**, **147/147 complete player files** including managed DLLs/data, and the **six selected still origins**. No hash mismatches.
- Recomputed the ordered source-manifest fingerprint and matched the value above. Nine selected owning host/view/sim/import/build/packaging source files matched the manifest when checked. This is not an independent rehash of all 5,327 build-source entries.
- The five normal review-role receipts identify the exact player and normal completion. Material controls read `none`, render controls are disabled, and the package builder now rejects diagnostic launch flags. Renderer diagnostics elsewhere in the revision directory are not rated as shipping presentation.
- Proof SHA256: `9a7a4726225a39f2fd91e941897a220e7c2e43dc986b2574f4c32578d2e274c2`, matching packet and manifest.
- Independent frame read: **2,070 frames, 69.000 seconds, 960 x 600, 30 fps**, one video stream, no audio stream. The packet records a passing full decode.
- Opened all three supplied extracted encoded samples. They retain Catrina hop/right-three-wheel and Nocturne framing/HUD without evident corruption. They do not cure the source canopy failure or establish that every encoded frame was visually inspected.

No file-binding/encoding defect was found in this scope. Mechanical packaging integrity is separate from publication suitability.

## Unpublished Patcher archive audit

The prepared r20 ZIP is **173,195,444 bytes**, SHA256:

`1736e88d6df46be71a249625d6899a3c17e0b1eae723f3685b1d8ed90ae7ee95`.

I streamed and hashed **147/147 ZIP file entries**, checking sizes/hashes against the inventory and the current built player; no mismatches or unsafe paths were found. Entry point is `Cinder.exe`, with only `-module cinder-drive` arguments. No private material/colour/reflection diagnostic is present in those launch arguments. This checked the archive/inventory and normal entry point; the coordinator had release-note wording edits pending, so the mutable manifest/release notes are not hash-approved by this report.

**Do not publish this otherwise correctly packaged r20 archive while the canopy P1 remains.** Authorization to publish a prototype does not make missing required rendered cloth an accepted feature. Root has explicitly held upload and is preparing a uniquely named corrected revision.

## Performance and human limits

Normal Catrina/Luna/Nocturne capture summaries report maximum measured draws 216/192/154 and listed triangles 693,585/583,929/683,557. These sampled takes are within the stated 300-draw and 700,000-triangle targets. This is not evidence about every view or the target handheld. Capture median/p99 intervals remain capped and include PNG I/O: Catrina 33.3324/34.0706 ms, Luna 33.3325/33.7282 ms, Nocturne 33.4506/36.1435 ms. External peak working sets are 415,969,280 / 360,169,472 / 401,940,480 bytes. Internal memory values remain zero and are not used as measurements.

**UNVERIFIED:** physical controller/keyboard feel, heard audio, comfort, comprehension, enjoyment, settings persistence after restart, full focus-loss behavior, long-session performance and 1080p/60 on the target device. No human playtest or listening claim is made. Even after the roof repair, below-8 visual findings keep Level 2 and paid-release acceptance open.
