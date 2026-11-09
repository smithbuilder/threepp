# Independent architecture and loaded-mechanism review: r2

November 8, 2026, Pacific Time. Reviewer: migration_review. The reviewer did not implement the simulation, view or loaded-rig probes. No editor or player was launched by this reviewer during this review.

## Current verdict

**CHANGES REQUIRED.** The r2 loaded probe caught a real roof-adapter regression. Simulation acceptance from the earlier independent 204-check run remains separate from this loaded-view gate. Do not present the failed r2 loaded receipt as passing.

The guarded r2 probe at `evidence/cinder-unity-r2/20261108-233429-491-Probe/` ran against executable SHA256 `0ACFF11EA8FF8843477866737D2B8FDFF3FAD4DEC36C6D4BB255B3A6726C7195`. Its loaded report contains 131 checks and nine FAIL lines, all for Nocturne roof phases. Maximum rail-joint error is 0.01305430 m and maximum actuator endpoint error is 0.68056101 m. Catrina, Luna and Nocturne suspension attachment checks in that report pass their finite sampled scope.

## Findings and required corrections

| Priority | Finding | Correction / verification |
| --- | --- | --- |
| P1 | The donor hides `roof_root` and both `roof_lift` parents with scale 0.001 in the stored asset. `RigMechanisms` initially captures car-space bind coordinates through those hidden scales. Later `PoseRoof` restores root scale 1 while still using the compressed bind targets. Lift parent scales are not restored as the donor adapter does. | Capture unscaled authored roof/lift bind data or normalize those hidden scales before recording bind coordinates. Repeat all phase checks without reducing their attachment standards. Inspect raised and folded roof geometry in the player. |
| P2 | Loaded probe initially instantiates only three hero prefabs; six mid/far rigs used by the view are not run. | Exercise all nine loaded prefabs with the base vehicle's mechanism adapter. Static node preservation alone is insufficient to prove deformed LOD geometry. |
| P2 | Bellows bearing-ring maximum error starts at zero and remains zero if no mesh is classified as rubber or no endpoint vertices match the selection tolerance. Decimated geometry makes this especially material. | Require actual rubber geometry and nonzero sampled top and bottom ring vertices for each bellows before accepting the error. |
| P2 | The view initially updates active LODs, then the camera changes the active tier. The new tier can appear for its first frame at its constructor or stale pose. | Pose the newly selected tier and panels before enabling it. Review a camera change that crosses the 12 m tier threshold. |

These were sent to the builders. The independent reviewer identified the hidden-scale cause by reading the exported GLB hierarchy and comparing the adapter with `showcase/NocturneRig.hpp`. Source changes and a fresh exact-build receipt are required to close the findings.

## LOD pivot preservation audit

The independent static export audit is `build/cinder-independent-lod-pivots-r2-final.json`. It parses GLB JSON directly and records the SHA256 of all nine inspected staged exports. It compares node names, parents and TRS values. For source-to-export comparisons it considers unique donor names and equivalent quaternion signs, avoiding ambiguity from repeated donor material leaf names.

- All nine exports retain donor names and unique named pivot parents. No duplicate names occur in the inspected exports.
- Each mid and far tier has exactly the same complete node hierarchy and TRS values as its hero export.
- Catrina and Luna unique-pivot transform differences from the donor are below 0.000001 m. Nocturne roof pivots shift by at most 0.000274 m during Blender re-export; the shift is shared by all tiers. This is not a mid/far pivot regression.
- The LOD export process preserves named objects and decimates their meshes separately, so wheel, arm, hydraulic, panel and roof object ownership can survive.

This verifies exported hierarchy, not loaded Unity mechanical deformation, moving clearances or visual quality. `assets/unity/lod-manifest.json` records pre-staging bytes; `stage_assets.py` materializes glTF defaults and therefore changes staged file hashes. A delivery must distinguish those stages and bind the imported staged bytes.

## Positive architecture observations and scope

`Cinder.Sim.asmdef` now sets `noEngineReferences: true`, so the pure-simulation boundary is enforced by compilation. Module entry settles the simulation before cloning the actual replay start state, then clears the elapsed tick and metrics. This provides a stable authored starting snapshot rather than hiding startup movement only in the view.

Loaded-rig checks inspect actual instantiated transforms and deformed vertex arrays. They are stronger than source-only formulas or finite-number checks and successfully exposed the roof regression. Their attachment scope is finite and does not include mesh collision sweeps, strength, physically measured vehicle behavior or human feel.

Final presentation and gameplay scores require the running candidate's independent visual packet. Audio listening, physical controls, comfort, comprehension and enjoyment remain **UNVERIFIED** until Oliver plays.
