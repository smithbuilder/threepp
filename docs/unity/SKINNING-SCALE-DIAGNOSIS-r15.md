# Independent diagnosis of the r15 skinning scale failure

November 9, 2026, Pacific Time. Reviewer: migration_review. Read-only source, retained-output and mathematical review. The reviewer did not launch an editor/player or implement the correction.

## Finding

**The r15 comparison applies host scale twice to `BakeMesh(..., false)` output.** The failed probe does not demonstrate a bad bind pose. Controlled measurements show that scale-compensated `BakeMesh(..., true)` output, followed by the renderer's `TransformPoint`, agrees with the posed originals at nonunit host scale. Independently evaluated single-weight skinning matrices also agree with those originals.

Keep the host Frame scale contract, the nonunit tests and the 0.0002 m tolerance. Correcting the API comparison space is justified by the controls below. Reducing the tests to scale one or increasing the tolerance would not be justified.

## Independent evidence before the control

From the staged car geometry, the reviewer computed the radius from car origin to the largest opaque vertices. Applying one extra scale factor predicts a world-space error of `s * (s - 1) * radius` when `s = 1.15`:

| Car | Predicted extra-scale error | Observed r15 neutral error |
| --- | ---: | ---: |
| La Catrina | 0.52631347 m | 0.52630496 m |
| Nocturne | 0.54515897 m | 0.54516721 m |

Agreement within approximately nine micrometres strongly identified an extra uniform factor instead of an arbitrary suspension deformation. Independent values for all nine tiers are retained in `build/r15-independent-scale-radius.json`. This radius comparison alone did not identify whether the error arose in skinning or in the probe's conversion space; the controlled fixture resolved that distinction.

## Controlled API and matrix measurements

The actual control is `build/SkinningScaleProbe/20261110-054647-049/measurements.json`, produced by the guarded Unity 6000.3.6f1 CPU diagnostic. The reviewer inspected `SkinningScaleProbe.cs` and all 16 known-fixture rows plus 24 actual-car rows. The report's `finite` flag only claims populated finite output. This review examined the error columns rather than treating that flag as geometry acceptance.

The known fixture has three vertices, one unit-weight bone, independently moved/rotated bone phases, a translated/rotated host and scales 1, 0.8, 1.15 and 2. The reference is the original source transform. The analytic skinning reference evaluates the actual bind matrix and current bone matrix directly. Actual-car rows cover all three heroes at scales 1 and 1.15 in neutral and split-travel/steer/half-panel poses.

| Known fixture, neutral | `false` then full TransformPoint | `false` then rotation/translation only | `true` then full TransformPoint |
| --- | ---: | ---: | ---: |
| Scale 0.8 | 0.40388355 m | 0.00000024 m | 0.00000048 m |
| Scale 1.15 | 0.43543616 m | 0.00000174 m | 0.00000117 m |
| Scale 2 | 5.04854488 m | 0.00000219 m | 0.00000219 m |

The moved-bone fixture produces the same pattern. At scale one both conversions agree because there is no extra scale to apply.

Across the actual hero-car rows:

- `true` followed by full TransformPoint has maximum error **0.00003130 m**.
- Analytic single-weight skinning versus posed source has maximum error **0.00002443 m**.
- `false` followed by full TransformPoint reproduces the approximately 0.477 to 0.554 m failures at scale 1.15.
- `false` followed by rotation/translation only returns the expected small errors.
- No compared source was inactive in these control rows.

This isolates a snapshot conversion convention. It does not require changing the source vertices, bind poses, bone weights, attachment transforms or simulation.

## API contract and correction

The installed 6000.3.6f1 CoreModule XML and [Unity's 6000.3 BakeMesh reference](https://docs.unity.com/en-us/engine/6000.3/script-reference/unityengine/skinnedmeshrenderer/bakemesh) describe `useScale` as scale compensation. The earlier source-review assumption that `false` automatically supplies unscaled local vertices for a full TransformPoint conversion was incorrect. The earlier source review has been corrected explicitly.

For the existing validator, `BakeMesh(..., true)` supplies the compensated local snapshot needed before applying the renderer's full transform. The controlled analytic and actual-car errors support this conversion without waiving the Frame mapping.

The construction algebra remains coherent: vertices are first combined into car space, and each bind pose maps from that space into the attachment's bind frame. Current bone world matrices then reproduce the source's posed world coordinates. Common host translation, rotation and scale are not supposed to be applied a second time to an already scaled snapshot.

## Evidence binding and remaining gate

Control output SHA256: `574AF615B5C0D23929BF77E3F833A6830A8EAE86E0D21EC16721AC4311088279`.

Inspected control source SHA256: `FF224D823FFF6E51AF29EBBB51BEDD43A5D836E03BA913CF62556862B10D6C3B`.

The failed r15 packet remains historical failure evidence. A fresh candidate must still pass the complete nine-tier runtime gate using the corrected conversion, retain its displacement/visibility tripwires and receive visual review.

These controls are CPU snapshots and analytic matrix checks. They do not directly read back GPU vertex positions or measure a rendered scaled silhouette. There is no demonstrated GPU double-scale defect in this evidence, but exact GPU appearance remains the responsibility of the fresh running-player visual packet. No visual score or release approval is assigned here.
