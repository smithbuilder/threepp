# Independent batching and camera technical review: cinder-unity-r17

November 9, 2026, Pacific Time. Reviewer: migration_review. This reviewer did not implement the simulation, mechanical posing, rigid-bone batching or camera changes. The reviewer authored the build-time `SurfaceShaderDiagnostics` output helper, so this report does not provide independent final approval of material-shader behavior or shader-quality conclusions derived from that helper. No editor or player was launched by the reviewer.

## Verdict

**PASS for the exact r17 simulation regression, finite loaded mechanics, sampled rigid-bone batching and the stated camera-clearance regression.** No additional P0 or P1 defect was found within those component gates.

This is not visual acceptance. In particular, it does not certify lacquer, clearcoat, GI, transformed GPU normals/tangents, reflections or antialiasing. Oliver's native-relative fidelity gate and the fresh running-player presentation review remain necessary. Any later source/player revision requires its own binding; r17 evidence cannot validate an unbuilt future change.

## Exact binding

| Item | Independently checked result |
| --- | --- |
| Player | `builds/cinder-unity-r17/Cinder.exe` |
| SHA256 | `20974CF14E1AEEE20631736FF1AE5FC67218745EB17E4C7D4E65BDC6FCF093D5` |
| Authenticode | Valid |
| Probe session | `evidence/cinder-unity-r17/20261109-220307-090-Probe/` |
| Source fingerprint | `1bb23f528f6631314c2d4ff4e90ecac6958e0faa83c6c279fcc16798dbbb3fbe` |
| Build receipt | Unity 6000.3.6f1, succeeded, zero errors, two warnings |

The executable matches latest-probe and runtime receipts. The source fingerprint was independently recomputed from the complete ordered manifest and matched. Thirty-three selected owning source, shader, assembly-definition, prefab and export/helper entries matched their current disk hashes. This was a selected owning-file check, not independent rehashing of every generated asset in the manifest. The calculation is retained in `build/cinder-independent-r17-binding.json`.

| Retained output | SHA256 |
| --- | --- |
| `probe.txt` | `30604EC0896F7C0B6824C5DF44A9EE5DAFAA7C70E412F5156571E9EB322EEC1D` |
| `loaded-rig-probe.json` | `27C6DB591EE3B36FB5C51ED98937AF6B95E416B0F10FBEA9B8456E2493997DD7` |
| `runtime-batch-probe.json` | `F73CB2279B161822D0DC84B22F02950005EF7AF9DC5305C0C04D4CFF34339F7A` |
| `runtime-receipt.json` | `75A4FBBDAB0E7CBA028DCFDD84D63271B2C60BC1A6A028CF65924E82AC41FAB9` |

The guarded probe finished normally in 20.31 s and recorded peak working set 329,523,200 bytes. These are CPU probe observations, not a rendered frame-time or handheld-performance verdict. The two recorded build warnings must remain visible in the delivery record; this was not a zero-warning build.

## Reviewed component gates

| Gate | Result and scope |
| --- | --- |
| Pure simulation regression | **204/204 PASS.** Complete Unity probe output is byte-identical to the retained r9 baseline. |
| Raw loaded mechanics | **495/495 PASS.** Complete output is byte-identical to r9. The earlier finite attachment scope and documented installation adaptations remain applicable. |
| Runtime batching and camera regression | **148/148 PASS.** No FAIL lines; all nine actual detail tiers contain compared skinned batches. |
| Source/copy displacement tripwires | PASS. Each tier deliberately displaces a hidden source, detects the mismatch and restores the original agreement. |
| Hidden-source tripwires | PASS. Unexpectedly inactive source geometry produces a failure sentinel instead of silently accepting visible copied geometry. |
| Nocturne roof-cover participation | PASS. Actual original cover renderer/triangle participation is checked around the 0.02 phase threshold in every tier. |
| Exterior/garage camera regression | PASS. Twenty-four assertions cover three cars, both 22 degree roll directions and the stated camera modes in a nonidentity module frame. |

## Rigid-bone batching assessment

The optimization combines compatible materials, shadow modes and vertex-attribute masks while assigning every vertex exactly one actual rigid attachment bone. Flexible owned meshes and currently nonuniformly scaled owners remain outside the rigid skin batch. Activation-switched ancestry is also excluded, preserving Nocturne's roof-slot cover hiding behavior.

Vertices are combined into car space and use attachment bind matrices. Current source world geometry remains available beneath the authoritative hierarchy with its renderers disabled. The runtime invariant evaluates the actual baked skin rather than comparing against a construction-time copy.

The earlier r15 failure was a snapshot comparison-space error, independently isolated with known one-bone and actual-car scale controls. `BakeMesh(..., true)` supplies the compensated snapshot used before the full renderer transform. The nonunit Frame contract and 0.0002 m tolerance remain intact. See `docs/unity/SKINNING-SCALE-DIAGNOSIS-r15.md`; failed r15 evidence is preserved.

| Vehicle, hero/mid/far | Largest sampled world-position discrepancy |
| --- | ---: |
| La Catrina | 0.00003130 m |
| Media Luna | 0.00002919 m |
| Nocturne | 0.00002915 m |

All nine tiers exercise seven explicit view fixtures: neutral, hydraulic droop, bump, both split-travel/steer directions, half-open panels/roof and fully open panels/roof. These are posed inspection fixtures, not input-driven gameplay sessions. The translated/rotated/scaled host frame remains origin (12, 3, -8) m, rotation (7, 31, -3) degrees, scale 1.15.

Nocturne's hero covers submit 1,056 original triangles at phases 0 and 0.01, and zero at phases 0.02 through 1. Their original renderers remain enabled, with visibility inherited from the cover objects. Mid/far cover populations are also positive when closed and zero when open. This closes the specific ghost-cover issue that a position-only skin comparison could miss.

Budget accounting includes active SkinnedMeshRenderer triangles and excludes disabled original MeshRenderers. Renderer count is still not a draw-call count. This report does not infer that the measured draw target is met from the existence of fewer renderers.

## Camera-clearance assessment

The former terrain check could be bypassed when a native-style camera convention replaced the initially clamped camera position. The revised source chooses the final desired camera first, then applies a common terrain-frame clearance clamp. Garage placement uses the same function. It preserves at least 0.35 module metres and 0.35 world metres along module up for positive supported module scales.

The runtime tests pose each car at -22 and +22 degrees roll and inspect exterior camera modes 0, 1, 2 plus the garage camera. The smallest measured module-frame clearance is approximately 0.35000032 m. The corrected low-side views that would otherwise fall below the road actually reach the clamp, so the assertions exercise the regression rather than only checking already-high camera positions.

These tests use the level test-ground surface and the nonidentity module frame. They do not establish building occlusion avoidance, every possible vehicle attitude, every trail feature or cockpit-camera comfort. Mode 6 deliberately retains its in-cabin placement and is outside the exterior-clearance assertions.

## Normals, tangents and material limits

Source inspection confirms the batching path retains authored normal/tangent channels, groups unlike attribute masks separately and uses a single bone per rigid vertex. Its positional and visibility invariants are meaningful, but the retained 148-check packet does not measure baked-normal angular error, tangent handedness or actual GPU vertex-buffer output. A 0.00003130 m position result must not be described as GPU-normal verification.

The root's new shader diagnostics contain generated pass source, not a rendered fidelity verdict. The reviewer provided that diagnostic helper and therefore does not assign independent shader approval here. The observed r16 all-black paint packet remains a failed visual reference; a fresh independent visual reviewer must assess r17's corrected paint, the other cars, motion and reflections against native references.

## Remaining limits

The 495 mechanical checks retain finite samples with steering at -0.32, 0 and +0.32 radians. They do not exhaust every independent four-corner state, full +/-0.48 steering or continuous mesh clearance. The managed simulation preserves the donor model and tuning without claiming bitwise Bullet handling parity. Replay identity is established within the reviewed Unity runtime.

Physical controller/keyboard behavior, handling feel, heard audio, comfort, comprehension, enjoyment, sustained target-device performance and overall visual acceptance remain outside this component verdict and require their appropriate separate evidence or Oliver's playtest.
