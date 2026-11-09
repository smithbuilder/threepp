# Independent architecture and mechanics review: cinder-unity-r4

November 9, 2026, Pacific Time. Reviewer: migration_review. This reviewer did not implement the simulation, Unity view, mechanical adapters or probes. Review used the exact guarded r4 player's retained output, source inspection, independent hash checks and independent geometry calculations. The reviewer did not launch another editor or player while the builder captured evidence.

## Verdict and gates

**PASS for simulation architecture and the stated finite loaded-mechanism gate.** The previous roof and leaf failures were repaired with explicit geometry/setup changes. Their limits were not relaxed. This is not a presentation or human gameplay score.

| Gate | Verdict | Evidence and practical limit |
| --- | --- | --- |
| Engine-free simulation boundary | PASS | `Cinder.Sim.asmdef` has `noEngineReferences: true`; source uses managed math and state, with no renderer, input, file, audio or network API. |
| Deterministic Unity regression | PASS | 204 checks pass. The complete r4 Unity `probe.txt` is identical to both retained r1 and r2 Unity outputs. Simulation source hashes still match the prior independent CPU review. |
| Loaded lowrider mechanisms | PASS, finite scope | 495 checks pass across three lowriders and all three density tiers, with 243 split-travel poses and five panel/roof phases per tier. |
| Meaningful vertex/part presence | PASS | The gate now requires positive rubber, bearing-ring, coil, leaf-eye and canvas populations where applicable. Missing geometry cannot yield a zero-error pass. |
| Exported pivot ownership | PASS | Independent GLB inspection confirms every mid/far tier has exactly its hero's complete named hierarchy and TRS values, with no missing donor names or duplicate exported names. |
| Visual, gameplay and performance release gates | Outside this verdict | Require the final running-player image/motion, interface and same-machine performance review. Human feel and listening remain UNVERIFIED. |

No P0 or P1 architecture or sampled attachment blocker remains in the inspected r4 packet. Two P2 documentation/interface notes are recorded below.

## Exact candidate and provenance checks

The probe session is `evidence/cinder-unity-r4/20261109-000725-085-Probe/`. The session's runtime receipt and latest-probe pointer identify the same executable. Independently recomputed executable SHA256 is `DE4C5F629B6E17F4B5653032D17FC37C6EC64FCE935F3A263DCD95758DA48A9D`; Windows Authenticode status is **Valid**.

The build receipt records Unity **6000.3.6f1**, build success, zero errors and zero warnings. Its source fingerprint is `44889bb0718e280424e97842b97f63a97d1707bbfe9e22863eb052617f2e09b6`. The reviewer independently recomputed this fingerprint from the ordered source manifest and obtained the same value. Twenty-two selected simulation/view source, assembly-definition, prefab and export-script manifest entries were also checked against current files, with no mismatch. This was a selected owning-source check, not a claim to have independently hashed every generated asset in the manifest.

| Retained output | SHA256 |
| --- | --- |
| `probe.txt` | `30604EC0896F7C0B6824C5DF44A9EE5DAFAA7C70E412F5156571E9EB322EEC1D` |
| `loaded-rig-probe.json` | `27C6DB591EE3B36FB5C51ED98937AF6B95E416B0F10FBEA9B8456E2493997DD7` |
| `runtime-receipt.json` | `6DD71B4D4F6246C1EE0F1BC0102BDA385CBF9B3BC0AC5A55B91BC11456FAC090` |

The guarded probe finished normally in approximately 18.96 s and recorded peak working set 202,412,032 bytes. These are probe resource observations, not a rendered frame-time benchmark.

## Regression and replay assessment

The 204 Unity probe lines did not change from r1 or r2, including numeric output and the combined fingerprint:

`29f20c9f7faa5030-e4e5580f3add1225-e5ddf5327de4ed7a-e3e972074daf56d9-011bff4fbe06a122-eda2b48c1bc04a3f-80e224f3e63b22f1`

The earlier standalone Mono console review has slightly different floating-point totals and fingerprints despite matching simulation source hashes. It is a separate runtime baseline. Cross-runtime bitwise identity is not established; the reviewed Unity-runtime regression is unchanged. Source state/replay integrity, midpoint restore and clone isolation were independently reviewed earlier and remain applicable because the simulation sources are unchanged.

The pure C# model retains a 60 Hz outer tick with four fixed 240 Hz internal steps, authoritative state, physical spring/damper support, friction-limited tyre forces, relative-wind aero torque and preload-driven hydraulic/air rules. It replaces Bullet numerics. It does not establish bitwise donor parity or a measured real-vehicle digital twin.

## Loaded mechanical results

The report's 495 lines include presence checks, finite-geometry samples and attachment metrics; they are not 495 distinct physical systems. Each of the nine actual prefabs is instantiated and posed. Missing required transforms, empty flexible geometry, missing metric sets or absent bearing populations fail the gate.

| Vehicle, all three tiers | Largest material sampled errors |
| --- | --- |
| La Catrina | Hub 0.00000185 m; rear link 0.00000200 m; damper endpoint 0.00000393 m; spring seat 0.00000173 m. Compression-stop violation 0.00000015 m; hydraulic overlap violation zero. |
| Media Luna | Hub 0.00000304 m; coil bearing 0.00000194 m; leaf chord 0.00000077 m; shackle length 0.00000060 m; modeled leaf eye attachment 0.00000321 m. |
| Nocturne suspension | Hub 0.00000358 m; bellows ring 0.00000200 m; bag plate 0.00000107 m; rear link 0.00000370 m; damper endpoint 0.00000383 m. |
| Nocturne roof | Rail joint worst 0.00010448 m; actuator endpoint worst 0.00010640 m; rigid bow scale error zero. All five sampled phases remain within the unchanged 0.0002 m limit. |

For every Nocturne tier, each of four bellows has one positively identified rubber mesh and 49 sampled vertices on each bearing ring. Canvas vertex counts are 1,065, 1,074 and 456. Every Luna tier has 72 vertices at each end of each front coil and five vertices at each modeled front/rear leaf eye. These populations make the attachment measurements meaningful instead of accepting an empty comparison.

The split sweep uses three left/right heights and steering at -0.32, 0 and +0.32 radians. Front and rear left/right samples share their height fractions. It is not an exhaustive four-corner combination sweep and does not cover the runtime's full +/-0.48 radian steering envelope. The gate checks named attachments and flexible bearing stations, not continuous mesh collision or full lock clearance. Published scope must retain those limits.

## Repair assessment

**Nocturne roof:** Normalizing the authored 0.001 hide scales before capturing bind data removes the cause of the earlier compressed roof targets. The lift scales are also restored while posing. Loaded rail and actuator errors fell from visible centimetre/metre gaps to the small values above. The source and the unchanged thresholds support this as a real correction.

**Nocturne bellows and density tiers:** Semantic part ancestry now identifies rubber even when Unity renames material assets. Positive ring-population checks close the earlier false-pass path. The export script exempts bellows, coils, leaves and canvas attachment geometry from general collapse decimation. All nine loaded tiers pass the same mechanical gate. Independent static pivot evidence is `build/cinder-independent-lod-pivots-r4.json`.

**Media Luna leaf installation:** An independent double-precision reconstruction confirms the donor's geometric incompatibility at rear hub height 0.24 m. Keeping the original 1.5426340460 m leaf chord and 0.1204159458 m shackle length requires a rear segment of 0.6450346512 m. The original installation cannot reach below 0.6516894339 m, a 0.0066547826 m shortfall. Relocating the shackle pivot forward 0.010 m reduces its reachable minimum to 0.6421664641 m, making the target feasible. The loaded r4 gate then confirms chord, shackle and actual eye attachment without changing simulation tuning. The independent calculation and source binding are saved in `build/cinder-independent-r4-binding-and-install.json`.

The adaptation is reversible and limited to the Unity view. The donor source/GLB and simulation remain unchanged. This is a disclosed installation adjustment, not an assertion that the original donor mechanism closed correctly.

## Remaining P2 notes and unverified scope

1. The inspected mechanical adaptation text says the visible Luna bracket moves 0.010 m. In the frozen and staged donor GLBs, `frame.shackle_bracket` geometry is batched into the frame mesh and no such named transform exists. The adapter's transform-name loop therefore does not move that mesh. The measured correction moves the shackle pivot inside the existing 0.08 m long bracket volume. Documentation should say this, unless a later build introduces separately movable bracket geometry.
2. Nocturne mode 8 is labeled `Return to cruise` in the inspected HUD source, but the simulation's mode 8 runs its repeating demonstration. Rename the label or deliberately change the exposed mode selection in a later source revision. This does not invalidate the finite attachment checks above.

The earlier LOD first-frame pose issue is corrected in source: the newly selected tier receives its current pose and panel phase before becoming active.

Final player stills, uninterrupted sampled motion, interface behavior and performance comparisons belong to the separate presentation/gameplay review. The title's native rendering/UI/audio are adaptations, not automatically approved by the donor's old review scores. Physical controls, input feel, heard audio, comfort, comprehension, enjoyment and handheld behavior remain **UNVERIFIED** until Oliver plays the candidate.
