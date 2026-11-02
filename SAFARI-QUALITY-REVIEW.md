# Safari visual acceptance gate

User reference: local safari.jpg. The user explicitly requested an independent
scored reviewer and enough iteration to pass. Target fixed before review:
weighted overall >=8.0/10, every category >=7.0, no major missing feature.
Scores are visual judgement by /root/safari_reference_reviewer, not CPU tests.

| Category | Weight |
| --- | --- |
| Silhouette/proportions |25%|
| Body/arches/glazing |20%|
| Materials/texture |20%|
| Accessories/mechanical detail |20%|
| In-engine fit/lighting |15%|

## Review history (not accepted)

- Primitive wide-chassis prototype:3.0/10 FAIL. Disconnected fender fins,
incorrect body/cabin proportions, empty rack, flat materials.
- Dense narrower mesh, forest views:provisional4.3/10 FAIL. No clear side view;
white nose slab, tent-like cabin, lamp caps, distorted911label, floating rack.
- Dense revision2, clear native court front114410-581/side114412-446/
rear114413-261:4.9/10 FAIL. Category scores4.5/5.0/3.5/6.0/6.0 respectively.
Readable decals, exposed skid and stronger grounding improved. Body silhouette,
flat materials/dark optics, high rack and spare still fail reference fidelity.

Inspection court is capture-only. It uses the actual mesh/materials/engine and
same daylight system on a flat floor, with a visible native-inspection label.
It makes profile assessment possible without roadside obstructions; it does not
establish driving feel or normal-scene acceptance.

## Pending work

Lower roof/seating and shorter Safari-specific wheel travel; coherent compact
911-style surfaces; correct lamp optical read; loaded rack/spare proportion;
shape-specific weathering/material variation. Builder and independent reviewer
remain separate. No pass or finished delivery is claimed at these scores.


## Current frozen candidate and execution block

Latest geometry revision addresses the remaining ducktail/lamp-wing/shoulder/roof
transition issues identified in geometry-only review. No new visual score is
claimed.79static meshes,123000triangles;6.007MB originalGLB. It passes the unchanged
6468padded tyre/body poses and0.178499m actual eye-to-surface clearance. CPU wheel
size, spring settling and rigid-link checks also pass for the new dimensions.

Native review is paused by WindowsApplicationControl, CodeIntegrity3033/3077,
which rejected the unsigned freshlybuilt executable before any window opened.
The existing Azure signing workflow was found, but automatic approval review
rejected using that external service/publisher identity without explicit project
authorization. User approval is pending. No security setting was changed and no
alternate launch method was attempted. The current frozen source/model/executable
hashes are inbuild/safari-model/frozen-review-manifest.json.

The previous4.9score belongs to an older mesh. The current candidate remains
UNSCORED and cannot pass the8/10 gate until fresh native views and normal driving
are available. CPU painter previews are explicitly not native/PBR acceptance.
