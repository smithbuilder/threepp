# Independent architecture and mechanics acceptance: cinder-unity-r9

November 9, 2026, Pacific Time. Reviewer: migration_review. This reviewer did not implement the simulation, loaded mechanism adapters or probes. This final review inspected retained evidence from the exact r9 player and independently checked its binding and regression results. No editor or player was launched by the reviewer while final captures were in progress.

## Verdict

**PASS for simulation architecture and the stated finite loaded-mechanism gate on cinder-unity-r9.** No P0 or P1 issue remains within this review's scope. The two P2 documentation/interface notes in the earlier r4 report have been corrected.

This verdict applies to technical architecture and sampled mechanical attachment. It is not a presentation score, a human handling verdict or a continuous mesh-clearance certification. The final presentation and gameplay review must identify its own exact r9 images, motion and interface evidence.

## Exact candidate binding

| Binding | Independently checked result |
| --- | --- |
| Player | `builds/cinder-unity-r9/Cinder.exe` |
| Player SHA256 | `5CF25D276D9331F1C6AA01994BD641586EDA28EC52EFCEAC31E1D54D3898448E` |
| Windows Authenticode | Valid |
| Probe session | `evidence/cinder-unity-r9/20261109-013642-689-Probe/` |
| Build | Unity 6000.3.6f1, succeeded, zero errors, zero warnings |
| Source fingerprint | `14fa13c91317ac7b710f8e5b320b6ebee8fd4ed1a9eb5408c321e99f603962af` |

The player file hash matches the runtime receipt and `latest-probe.json`. The reviewer independently recomputed the source fingerprint from the complete ordered manifest and obtained the same value. Twenty-eight selected simulation/view source, shader, assembly-definition, lowrider prefab and export-script entries also match the current files. The module source containing the corrected Nocturne label was checked separately against its r9 manifest entry. This was a selected owning-file validation, not independent rehashing of every generated asset in the source manifest.

The independent fingerprint calculation is retained in `build/cinder-independent-r9-binding.json`.

| Retained r9 output | SHA256 |
| --- | --- |
| `probe.txt` | `30604EC0896F7C0B6824C5DF44A9EE5DAFAA7C70E412F5156571E9EB322EEC1D` |
| `loaded-rig-probe.json` | `27C6DB591EE3B36FB5C51ED98937AF6B95E416B0F10FBEA9B8456E2493997DD7` |
| `runtime-receipt.json` | `C1969AFB40F8430DDA9E4BFC907FD5BB95A5C66887C8803F6C71BD6AA19CDC64` |

The guarded probe finished normally in 18.90 s and recorded peak working set 190,140,416 bytes. These are probe observations, not a rendered performance benchmark.

## Regression and mechanical gates

| Gate | Result |
| --- | --- |
| Pure simulation assembly | PASS. `noEngineReferences: true`; authoritative managed state and fixed-clock simulation remain separated from Unity presentation. |
| Simulation regression | **204/204 PASS.** The complete r9 Unity probe output is identical to r4, including all numeric results and fingerprints. |
| Loaded mechanism regression | **495/495 PASS.** The complete loaded-rig output is identical to r4, with no changed, missing or failing line. |
| Simulation/mechanism source continuity | PASS. Simulation sources, `RigMechanisms.cs`, `LoadedRigProbe.cs` and the LOD export script match the r4 reviewed hashes. |
| Three lowriders and three density tiers | PASS. Nine instantiated prefabs retain the positively measured flexible geometry and named attachment tests. |

The r4 report retains the independent geometry diagnosis, repair assessment and detailed metric values: `docs/unity/ARCHITECTURE-REVIEW-r4.md`. The exact byte-identical r9 probe and loaded-rig outputs preserve that finite mechanical result; visual shader polish did not change it.

Loaded evidence covers 243 split-travel poses, five panel/roof phases per tier, actual hub and damper attachment, rear links and driveshafts, hydraulic overlap and spring stops, Luna coil/leaf/shackle attachment and Nocturne bellows/roof connections. Bellows rings, coil stations, leaf eyes and canvas must have positive vertex populations. An empty comparison cannot pass.

The unchanged attachment tolerance is 0.0002 m. The largest reported roof actuator error is 0.00010640 m and roof rail error is 0.00010448 m. Other reported attachment errors remain in the low micrometre range within the stated sampled fixtures.

## Repairs and closed notes

- Nocturne's authored 0.001 hide scales are normalized before bind capture, and its bellows are identified through preserved authored part ancestry. The earlier roof gaps and zero-sample false-pass path remain corrected.
- Flexible bellows, coils, leaf packs and canvas retain their attachment stations in all density tiers.
- Luna's view-only shackle pivot correction remains explicitly documented. The earlier independent double-precision calculation confirms that a 0.010 m forward pivot relocation makes the legal full-droop leaf geometry feasible while preserving original shackle length and leaf chord. The simulation and donor files are unchanged.
- `MECHANICAL-ADAPTATIONS.md` now accurately says the Luna pivot moves inside the existing batched bracket volume; it no longer claims the bracket mesh moves.
- Nocturne mode 8 now reads `Demonstration`, matching its simulation behavior.
- The LOD transition receives the current pose before the newly selected tier becomes visible.

## Explicit limits

The loaded sweep uses left/right height samples at three fractions and steering at -0.32, 0 and +0.32 radians. Front and rear left/right heights share their fractions. It does not exhaust every independent four-corner combination, test the full runtime +/-0.48 radian steering envelope or establish continuous moving-mesh clearance. Named attachment checks do not prove strength, roadworthiness, detailed fluid behavior, deformable tyres or measured real-car dynamics.

The simulation is a managed replacement for Bullet, preserving the donor model and numbers rather than claiming bitwise donor numerical parity. Replay regression is established within the reviewed Unity runtime. Cross-runtime bitwise identity is not established.

Final visual presentation, scene budgets, sustained frame time, interface usability, audio quality and handheld performance require their separate evidence. Physical input feel, heard audio, comfort, comprehension and enjoyment remain **UNVERIFIED** until Oliver plays the candidate.
