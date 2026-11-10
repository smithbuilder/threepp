# Independent rigid-bone batching source review

November 9, 2026, Pacific Time. Reviewer: migration_review. Read-only source review; no editor or player launch. Exact binary/runtime acceptance is pending a fresh revision's retained probe and native-relative visual packet.

## Finding caught during implementation

**P1 visibility ownership:** Combining geometry across bones does not preserve per-part GameObject visibility. Nocturne's two opaque `roof_slot_cover` pieces are hidden by `PoseRoof` once roof phase reaches 0.02. A SkinnedMeshRenderer under the active car would continue rendering those vertices even when the source bone GameObject became inactive. A position-only source comparison would not detect the unwanted visible surfaces.

Direct staged-GLB inspection confirmed both slot covers are opaque `nocturne.piano_black` pieces with matching vertex attribute masks, so they were actual eligible combination members, not a hypothetical future case.

The builder has added explicit visibility-binding registration and excludes any source below an activation-switched ancestor. Initial panel endpoint posing registers the cover visibility bindings before batching. This is an appropriate source correction. Retain a runtime closed/open visibility check in addition to the positional invariant.

## Source assessment after that correction

No further P0/P1 defect was found in the inspected rigid-bone construction. The following choices are internally consistent:

- Positions are combined in car-local space. Each source's actual rigid attachment becomes its single bone, with weight 1 for every vertex belonging to that source. Bind pose `bone.worldToLocalMatrix * car.localToWorldMatrix` maps car-space bind vertices into that attachment's bind frame.
- Materials, shadow modes and vertex attribute masks are grouped separately. Flexible owned meshes remain outside the rigid skin batches. Current nonuniformly scaled owners remain ordinary mesh renderers.
- A single-weight bone preserves rigid movement; it does not blend between attachments or prescribe vehicle motion. The simulation and rig calculations remain authoritative.
- The original posed mesh hierarchy remains present, with original renderers disabled. The probe compares the actual `SkinnedMeshRenderer.BakeMesh(..., false)` result against current source world vertices, then applies the renderer transform. The nonidentity translated/rotated/scaled host-frame fixture is material to detecting a bad bind-space or scale calculation.
- Budget accounting includes active SkinnedMeshRenderer mesh triangles and excludes disabled original MeshRenderers. It does not substitute renderer count for the actual draw counter.
- A finite conservative local bound and `updateWhenOffscreen` avoid relying on stale skinned bounds during the reviewed poses. Their correctness still needs the ordinary camera and panel/roof capture, including open doors and roof deployment.

The existing source displacement tripwire remains valuable. A fresh exact build must run it on each actual density tier and complete all post-pose vertex comparisons. Do not reuse r12's rigid-copy probe as evidence for r13's skinning implementation.

## Remaining validation limits

A baked-position invariant does not prove transformed normals/tangents, material response, shadow appearance or visibility. Skinned geometry must therefore receive the native-relative visual/motion review, especially chrome, lacquer, roof covers, wheel rotation and moving suspension. The nonuniform-scale exclusion currently checks the selected owner's local scale at construction; future changes that animate such scale from an initially uniform pose require renewed analysis of normal handling.

The FXAA source uses a display-encoded linear-format temporary, then decodes its filtered result back to linear for the final target. That two-pass encoding sequence is consistent with filtering display-space contrast. Actual capture color/orientation and aliasing must still be checked; source inspection alone does not establish visual improvement. The extra 960 x 600 ARGB32 target is approximately 2.3 MB and does not change the existing resolution, frame-rate or shadow caps.

## Correction after the r15 scale-control failure

The earlier assumption that `BakeMesh(..., false)` supplies an unscaled local snapshot suitable for an immediate `TransformPoint` comparison was incorrect. r15's nonidentity-frame test exposed an extra scale factor. The installed Unity 6000.3.6f1 API documentation and the [Unity 6000.3 BakeMesh reference](https://docs.unity.com/en-us/engine/6000.3/script-reference/unityengine/skinnedmeshrenderer/bakemesh) describe the boolean as scale compensation. A source-only endorsement of the original comparison did not establish that API behavior.

Independent static radii predict the observed Catrina and Nocturne failures within approximately nine micrometres when one extra 1.15 scale factor is applied. Preserve the failed r15 evidence and verify true/false/manual-skinning controls at nonunit host scales before accepting a revised validator. The host Frame contract must not be reduced to unit scale to make the gate pass. This correction changes the interpretation of the probe API, not the reviewed bind-pose algebra.

No visual score, draw-budget pass, handling acceptance or release approval is assigned by this source review.
