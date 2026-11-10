# Independent architecture, mechanics and batch review: cinder-unity-r12

November 9, 2026, Pacific Time. Reviewer: migration_review. The reviewer did not implement the simulation, posing adapters, batching or probes. This review used source inspection, retained exact-player output and independent file/fingerprint checks. No editor or player was launched by the reviewer.

## Verdict

**PASS for the stated technical architecture, finite mechanics and sampled runtime batching gates on r12.** The visible torque-tube regression identified in the initial r11 batching implementation is closed in the inspected replacement and its new integration gate. No P0 or P1 blocker remains within this review's technical scope.

This does not restore visual acceptance by itself. Oliver rejected r9's city, lighting and cars. The restored r12 presentation still needs the separate native-relative visual and motion review. No visual score is assigned here.

## Exact player and source binding

| Item | Checked binding |
| --- | --- |
| Player | `builds/cinder-unity-r12/Cinder.exe` |
| Player SHA256 | `C7F95E7658BE0AB8A867144B1EC437BD4142FBA4D8EA45847C3E6DE216F79A3A` |
| Authenticode | Valid |
| Probe session | `evidence/cinder-unity-r12/20261109-211027-114-Probe/` |
| Build result | Unity 6000.3.6f1, succeeded, zero errors, zero warnings |
| Source fingerprint | `2623905e6e6db4310c776a45ca80f49ba362fb109a379f07246fd197aef85a71` |

The reviewer recomputed the executable hash and checked it against both latest-probe and runtime receipts. The complete ordered source-manifest fingerprint was independently recomputed and matched. Thirty-three selected owning simulation/view sources, shaders, assembly definitions, lowrider prefabs, city-export files and the host matched their manifest hashes on disk. This was a selected owning-file check, not independent rehashing of every generated asset in the manifest. The independent calculation is retained in `build/cinder-independent-r12-binding.json`.

| Exact retained output | SHA256 |
| --- | --- |
| `probe.txt` | `30604EC0896F7C0B6824C5DF44A9EE5DAFAA7C70E412F5156571E9EB322EEC1D` |
| `loaded-rig-probe.json` | `27C6DB591EE3B36FB5C51ED98937AF6B95E416B0F10FBEA9B8456E2493997DD7` |
| `runtime-batch-probe.json` | `A3F67C7BA2DF051DCC9904551C2FFA02068CC1902D6F36BF78038410794A9936` |
| `runtime-receipt.json` | `C4CB5F8DCF7ACF5C30C980CB9CB0E693459B675A7F93C4387F6D742E784DD494` |

The guarded probe finished normally in 19.85 s with recorded peak working set 274,427,904 bytes. These are probe resource observations, not a rendered performance benchmark.

## Gates and source continuity

| Gate | Independent result |
| --- | --- |
| Pure simulation boundary | PASS. The simulation assembly forbids Unity references; authoritative state and fixed-clock rules remain separate from presentation. |
| Simulation regression | **204/204 PASS.** Complete output is unchanged from the retained r9 Unity baseline. |
| Raw loaded-rig mechanics | **495/495 PASS.** Complete output is unchanged from r9. The finite attachment scope and prior geometric repairs remain applicable. |
| Runtime optimized geometry | **94/94 PASS.** All nine tiers have actual merged geometry, seven posed fixtures and a successful displaced-source tripwire. |
| Rig mathematics continuity | PASS. The inspected adapter diff adds pose-binding tracking and flexible-mesh identity queries; its geometric posing calculations are unchanged. |

The raw loaded-rig gate alone could not validate batching. It instantiates unoptimized prefabs. r12 correctly adds a separate gate that constructs the actual `CinderView`, applies its production combination policy, and compares the visible optimized copies against the still-posed original source geometry.

## Batch ownership and lifecycle assessment

The replacement groups by actual rigid attachment transform, material, shadow mode and vertex-attribute mask. Initial posing and panel/roof endpoints register queried attachment transforms before combination. The nearest registered ancestor becomes the combined mesh's parent. A moving wheel, torque tube, door, damper or roof member can therefore contain a local rigid batch that follows that member rather than a fixed copy under the chassis.

Flexible meshes owned by the rig's deformation adapter are excluded from combination. Their live vertex arrays continue to be updated. Material and shadow grouping preserve the tiny-part shadow exclusions rather than silently enabling shadows on the new renderer. The combination matrix maps each original source into its selected owner's local frame, and combined bounds are recalculated.

The current importer creates one submesh per MeshFilter. The inspected combine groups use compatible authored normal, tangent, color and UV channels; grouping by attribute mask also prevents unlike channel sets being merged accidentally. This review does not assert support for an arbitrary future multi-submesh importer without an explicit submesh check.

Disabled originals remain available as posed reference geometry. `MeasureBudget` excludes their disabled renderers, includes enabled combined geometry once, and omits inactive tiers through active hierarchy traversal. The newly selected tier is posed before it is made visible. Combined meshes and live deformation meshes are registered for teardown along with the view hierarchy.

## Functional runtime evidence

The gate uses a translated, rotated and scaled host frame: origin (12, 3, -8) m, rotation (7, 31, -3) degrees and scale 1.15. It exercises neutral, hydraulic droop, bump, both split-travel/steering directions, half-open panels/roof and fully open panels/roof. These are explicit posed inspection fixtures, not claims of driven input replay.

For each fixture it compares every visible combined vertex, in world space, with the current disabled source vertex under its authoritative attachment hierarchy. This would reveal a moving source accidentally frozen into a fixed batch. The comparison is not merely a check against the construction-time pose.

| Vehicle, each hero/mid/far tier | Active batches per tier | Worst sampled world-vertex difference |
| --- | ---: | ---: |
| La Catrina | 27 | 0.00001621 m |
| Media Luna | 20 | 0.00001717 m |
| Nocturne | 19 | 0.00001712 m |

All nine tiers actually participate in merged-geometry comparisons. Each displaced-source tripwire moves a hidden original source by 0.010 m locally, observes approximately 0.0115 m world-space disagreement, restores it in a `finally` block and observes the original small error again. This demonstrates that the validator detects a deliberate source/copy mismatch instead of accepting an empty batch set or a permanently zero comparison. The unchanged tolerance is 0.0002 m.

## Restored city and simulation surface

The city restoration is an offline export of native geometry and material data; it does not embed the C++ runtime. Independent staged-GLB checks compared all 11,585 asphalt and 38,578 paving triangles against the unchanged simulation's sampled surface. Maximum triangle-centroid difference was 0.0000000036 m. The maximum vertex difference was 0.000016 m at the outer simulation grid clamp. Evidence is `build/independent-r11-city-surface.json`; the same restoration source is retained in r12.

Camera changes operate on the host camera. The recorded city initial spawn and the separate frame mapping do not introduce a view-driven vehicle trajectory. Visual city materials and lighting require their own native-relative assessment.

## Explicit limits

The 495 raw-rig checks retain their finite split-travel and panel-phase scope, with steering samples at -0.32, 0 and +0.32 radians. They do not cover every independent four-corner combination, the complete runtime +/-0.48 radian steering envelope or continuous moving-triangle clearance. The additional seven batching fixtures verify visible copy/attachment equivalence in those poses; they do not expand the underlying mechanical clearance claim.

The simulation replaces Bullet numerics rather than claiming bitwise donor handling parity. Stable replay is established within the reviewed Unity runtime, not across all runtimes or platforms. Authored tuning and installation approximations remain documented.

The runtime batch gate validates geometry ownership and sampled vertex positions. Actual draw-call and frame-time targets must be measured in the running player; MeshRenderer count is not a draw-call measurement. Visual fidelity, physical input feel, heard audio, comfort, comprehension, enjoyment and target handheld performance remain outside this verdict and UNVERIFIED until the appropriate separate review or human playtest.
