# Independent batch and mechanics boundary review

November 9, 2026, Pacific Time. Reviewer: migration_review. Read-only implementation review. No player or editor was launched. This is not a visual score or candidate acceptance.

## Initial r11 findings

**P1: a moving Media Luna torque tube was eligible for rigid batching.** The built r11 view source, SHA256 `107b9212f2a1d80cc82a57d9866bd496923cc1960a3048ebf9624fcb5acd4c24`, omitted `torque_tube` from its moving-owner exclusions. Direct inspection of the staged GLB and the exact exclusion rules found:

- `driveline.luna.chassis_graphite` under `torque_tube` joined the same-material fixed cabin batch.
- `driveline.luna.warm_cast_iron` under `torque_tube` joined a fixed engine/exhaust batch.

The rigid combined copies therefore stayed fixed while `RigMechanisms` rotated only the hidden original tube renderers. This is a visible mechanics regression even if the original raw-prefab rig probe passes. Membership evidence is `build/independent-r11-batch-membership.json`.

**P2: shadow flags were lost during combination.** The first implementation disabled shadows on tiny source renderers, but newly combined renderers defaulted to shadow casting. Combining by material alone could therefore put those tiny surfaces back into a shadow-casting mesh.

The root builder was notified before visual acceptance. Pending source now excludes `torque_tube` and groups fixed pieces by both material and shadow-casting mode. These are appropriate source corrections. They require a fresh unique build and exact runtime verification; the original r11 probe does not validate source changed after that build.

## Integration gate needed

The existing 495-check loaded probe instantiates raw prefabs. It does not apply `CinderView.BatchFixedBody` and could not detect the frozen visible tube. The new pending `ValidateRigidBatches` compares every visible combined vertex against the corresponding original source vertex after authoritative posing. That is a meaningful functional invariant.

Run that invariant after real split-travel and panel/roof changes, with each hero/mid/far tier active. Bind geometry alone is insufficient. A vehicle with zero combined groups can legitimately pass if its source static pieces are already grouped by material; require nonempty rendered geometry and exercised pose/check counts rather than inventing a requirement for every vehicle to have a rigid batch.

## Independent positive checks

- The combination matrix `car.worldToLocalMatrix * source.localToWorldMatrix` correctly puts vertices in the new batch's car-local frame.
- All actual eligible same-material groups had matching vertex attribute masks, including authored normals, UVs and vertex colors. The current importer creates one MeshFilter per glTF primitive and one submesh per MeshFilter. Consequently `CombineInstance.subMeshIndex = 0` does not discard another submesh in these inspected assets. Assert that invariant if the importer later changes.
- `Mesh.CombineMeshes` retains the authored channels; bounds are recalculated. No normal recalculation is introduced that would intentionally replace the donor's authored normals.
- Disabled original renderers are skipped by `MeasureBudget`. Active hierarchy traversal also excludes inactive density tiers. The combined mesh's triangles are counted once, while original hidden copies are not counted as submitted geometry. MeshRenderer count still is not a measured draw-call count; use the render counter.
- The view updates a newly selected tier before enabling it. Chassis pose and panel phase carry through the density switch.
- Camera changes act on the host camera only. They do not write vehicle state. The city initial spawn remains a recorded initial-state adjustment at a flat road location rather than an animated vehicle trajectory.

These source observations do not establish measured draw-call savings or final visual quality. Preserve actual runtime budget results even if the new draw total remains above the target.

## Restored native ground versus physics

The restored city uses exported native mesh/material data rather than another runtime. The independent GLB check compares all ground vertices and triangle centroids against the unchanged C# half-metre sampled city surface:

| Ground | Triangles | Maximum vertex height difference | Maximum triangle-centroid difference |
| --- | ---: | ---: | ---: |
| Asphalt | 11,585 | 0 m | 0 m |
| Paving | 38,578 | 0.000016 m | 0.0000000036 m |

The 16 micrometre vertex maximum occurs at the simulation's outer grid clamp. This is not a material visible/collision discrepancy. The native exporter preserves non-flat curb cells and original diagonals while reducing redundant flat tessellation. Independent evidence is `build/independent-r11-city-surface.json`.

The simulation and rig source remain separate from the visual batching and ground restoration. Final acceptance still requires the corrected exact player's fresh probes, moving capture and native-relative visual review. Human handling, heard audio and continuous moving-mesh clearance remain UNVERIFIED.
