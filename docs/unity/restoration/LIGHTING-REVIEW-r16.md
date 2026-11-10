# Independent lighting review: r16

November 9, 2026, Pacific Time. This evaluator did not implement the reviewed rendering changes. Review uses actual signed-player captures, retained native references and source inspection. No editor/player launch, source change or asset change was performed by the evaluator.

**Lighting score: 7.0/10.** r16 demonstrates a substantial restoration from r9 and fixes r11's pastel overexposure. The city now has believable material separation, correctly readable signs, ground texture and coherent daylight. Catrina's rose paint and Media Luna's green body are recognizable and readable. Native-relative vehicle lighting is still incomplete, particularly Nocturne's broadside form and the stability of fine chrome highlights. This is not a paid-release visual approval or an instruction to target a predetermined score.

## Candidate and evidence binding

- Revision: `cinder-unity-r16`, Unity 6000.3.6f1, D3D11, Built-in forward, Linear.
- Executable SHA256, independently rehashed: `313F2FF325126FCF747837DA3273727D2BE9A383F2903F4D22BC7BEFD9F9ED49`.
- Source fingerprint from build receipt/manifest: `5de112ab561a2ad1a300fb0bcfc6f3f85b54445b0658a7acb80865a26e1cd161`.
- Build receipt reports success, zero errors and **two warnings**. Both logged warnings concern potentially uninitialized `ApplyFXAA` data on D3D11. A successful compile is not evidence that the warnings are harmless.
- Relevant current sources were individually hash-compared with the r16 manifest: Host, View, Body, Glass, ShopGlass, City/CityFoliage, Grade, FXAA, SkyBake, NativeCityMaterials, GlbImport, GraphicsSettings and QualitySettings all match.
- Inspected capture runtime receipts identify this executable and normal completion. Probe JSON reports 204 simulation, 495 loaded-rig and 124 runtime-batch checks passing. These checks support technical integrity within their scope, not a lighting verdict.

All capture links below are actual 960 x 600 player PNGs:

| Capture | Role |
| --- | --- |
| [Garage](../../../evidence/cinder-unity-r16/20261109-215203-580-Capture/frame-0000.png) | Front-door daylight and Catrina presentation |
| [Catrina street](../../../evidence/cinder-unity-r16/20261109-215216-323-Capture/frame-0000.png) | Rose paint, wheels, trim, ground contact |
| [Media Luna street](../../../evidence/cinder-unity-r16/20261109-215229-068-Capture/frame-0000.png) | Dark green paint, glazing and cabin |
| [Nocturne street](../../../evidence/cinder-unity-r16/20261109-215241-800-Capture/frame-0000.png) | Dark blue paint and body form |
| [City overview](../../../evidence/cinder-unity-r16/20261109-215255-343-Capture/frame-0000.png) | District shadow/material continuity |
| [Nocturne cabin](../../../evidence/cinder-unity-r16/20261109-215335-370-Capture/frame-0000.png) | Glass transmission and interior readability |
| [Catrina detail](../../../evidence/cinder-unity-r16/20261109-215338-275-Capture/frame-0000.png) | Near wheel/chrome/paint detail |
| [Colour control](../../../evidence/cinder-unity-r16/20261109-215150-843-Capture/frame-0000.png) | Output-transform check |

Native comparison references: [Nocturne street](../../nocturne/review/native/street-cruise.png), [Catrina studio](../../la-catrina/review/studio/front.png), [Catrina detail](../../la-catrina/review/studio/front-detail.png), [Mercer street](../../../build/city-realism/street-and-sky.png) and [Mercer overview](../../../build/city-realism/city-overview.png). Studio/city lighting and camera poses differ. These are readable-form and material-identity references, not a pixel-difference exposure test. r9 and r11 actual images were also inspected as historical controls.

## What is demonstrably restored

The replacement greybox impression is gone from the inspected corner. Masonry, stone bases, window treatments, awnings, tree silhouettes, asphalt wear and yellow paint now form a coherent district. Cream trim no longer blows out against black panes. The overview retains broad material/shadow consistency. Corner Coffee reads correctly; the sign correction has not visibly damaged its atlas row.

Sun intensity now accounts for the native physical-light versus Unity Standard normalization difference. The grade uses the native ACES matrices and exposure convention. HDR diagnostics for the inspected scene captures report ARGBHalf, linear input and ARGB32 sRGB output. The previous hypothesis of premature LDR clipping is unsupported by this evidence.

I independently sampled the colour-control image and evaluated native ACES plus exact sRGB on the CPU:

| Linear test input | Actual RGB bytes | CPU reference RGB bytes |
| --- | --- | --- |
| 0.003 grey | 0, 0, 0 | 1, 1, 1 |
| 0.18 grey | 126, 126, 126 | 126, 126, 126 |
| 1.0 white | 226, 226, 226 | 226, 226, 226 |
| 0.5 red | 200, 0, 2 | 200, 0, 6 |
| 0.5 green | 63, 196, 30 | 63, 196, 32 |
| 0.5 blue | 0, 0, 191 | 0, 0, 192 |

This supports correct single output encoding and the selected tone transform at six constant patches. Maximum chromatic deviation is four bytes in a small channel. It does not validate the entire HDR range, reflection BRDF or all scene lighting. The first control patch also loses its final one-byte distinction, so do not describe the test as exact across all six patches.

The sky bake explicitly uses a filtered 128 cube and compensates for the measured cylindrical-import quarter turn. The six saved cube/panorama cardinal comparisons have maximum relative error about 1.89%. That is useful evidence against the former gross orientation mismatch; it is not a complete angular or mip-level validation. The selected runtime uses the filtered sky cube. A rejected local-city cube is diagnostic material, not the approved solution and not necessary to explain this verdict.

## Remaining issues

### P1: Nocturne's city body still loses broad form to near-black paint

In the r16 street capture, the large door/rear-quarter side reads as a nearly uniform black-blue mass. Bright perimeter trim and wheel edges carry much of its silhouette. The native street reference shows broader grey-blue gradients across that same vehicle identity, separating side planes more clearly. The r16 hood has some value separation, so this is not a complete loss of paint colour; it is a remaining presentation deficit in a hero car.

The r16 cabin shot also puts much of the near dashboard into black while exterior windows become a relatively uniform grey sheet. The car remains recognizable and the road remains visible, but the interior is not yet as legible as the native references.

**Cause boundary:** fixed Trilight diffuse fill, sky-only reflection content, the custom coat/Standard response and viewing direction can all affect this result. Source inspection does not isolate their respective shares. The colour-control pass does not prove material-lighting parity. Do not globally raise exposure, repaint donor colours, reintroduce the rejected dark local probe or alter the simulation to address it.

**Finite next check:** one Nocturne broadside/three-quarter control with recorded camera, pose, world heading and unchanged output transform. Compare diffuse-fill-only versus reflection/coat-only controls, alongside the native readable-form target. Add a small grey/chrome/roughness control at the same position. Judge the broad panel gradients and cabin form while preserving Catrina/Luna and the existing road values. Retain every failed control. This issue remains open until those actual pixels demonstrate the intended form.

### P2: Fine chrome remains visibly noisy

Catrina's roof trim, wheel spokes and narrow body brightwork still show broken bright pixels at this profile; the near detail exposes very sharp wheel highlights. This is better than r9's indiscriminate sparkle, but the static images cannot establish temporal stability. The native reference also has finite-resolution brightwork, so zero aliasing is not the appropriate target.

The new post effect filters display-space data after tone mapping, and the custom Body filters smoothness in both direct and GI setup. Those source changes address real earlier defects. They do not themselves establish success. Inspect a short slow camera motion and static hold before calling the shimmer resolved. The two compiler warnings should be explained or eliminated in a subsequent candidate, with a same-frame comparison; do not silently relabel r16 as warning-free.

### P2: Glass remains a bounded approximation

The car Glass shader still uses fixed tint/reflection weighting, clamps reflection radiance and does not implement its exposed normal map. Current Luna glazing transmits enough cabin detail, which is a useful improvement. Nocturne's windshield and dash still need the targeted view described above. A general transmission system or screen-space reflection effect is not justified by this review; first correct the specific readability loss at bounded cost.

## Acceptance limits

The scene-level restoration is real and the major r11 overexposure is corrected. The lighting score remains 7.0/10 because native-relative dark hero-car form and fine-highlight stability remain weaker than the restored city. Do not use this report as a complete visual acceptance or paid-release sign-off while the P1 remains open.

No subjective handling, physical controls, heard audio, comfort, enjoyment or handheld 1080p/60 performance is established. These are short, capped still captures. The evaluator did not implement any reviewed surface, and the failed r9/r11 evidence must remain preserved.
