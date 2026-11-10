# Independent lighting review: r24

November 9, 2026, Pacific Time. The evaluator did not implement the reviewed rendering or material surfaces. This review inspected existing actual-player pixels, raw GPU diagnostic receipts, source and native references. No editor/player launch or runtime/asset edit was performed by the evaluator.

**Verdict: the native-relative lighting restoration is substantiated in the reviewed packet. Lighting quality: 7.0/10.** The rejected r9 environment/material loss, r11 overexposure, r16/r19 dark Nocturne reflection response and original partial roof-cloth culling are addressed. No unresolved P1 lighting defect was observed in the inspected final views. This is a bounded restoration verdict, not an 8/10 overall-art result, a Level 2 quality approval or paid-release readiness.

The city and cars still look like a prototype. Better scene data and correct light units have recovered their identity, but they have not supplied final art direction, richer glazing, natural contact shading or stable fine brightwork at all distances. Restoration and absolute product quality are separate judgments.

## Exact candidate and verification scope

- Player: `cinder-unity-r24`, Unity 6000.3.6f1, Built-in forward, Linear, D3D11.
- Executable independently rehashed: `7D78C95234B8C21A2F2A48E544EB888F43D52612D0C8680C7D6319128CAA256A`.
- Build/source fingerprint: `0e57c2129876c7765692f3fd50d0cfe0cd3a02d73c826f93c48c89c2c1c86d97`.
- Relevant current sources individually match the build manifest: Body, Canvas, Grade and host/view code; SkyBake, NativeEnvironmentSun and GlbImport; GraphicsSettings and QualitySettings.
- The exact-player probe receipt reports 204 simulation, 495 loaded-rig and 154 runtime-batch checks passing. Those checks are technical evidence within their finite scope, not the basis of the visual score.
- Build succeeded with zero errors and **four warnings**: potentially uninitialized `LightingCinder` and `ApplyFXAA`, each logged twice. Generated shader diagnostics are retained. Do not report a warning-free build.

Inspected final actual-player evidence:

| Capture | What was checked |
| --- | --- |
| [Garage](../../../evidence/cinder-unity-r24/20261109-232942-508-Capture/frame-0000.png) | Street daylight, rose paint, trim and front-door readability |
| [Catrina three-wheel stance](../../../evidence/cinder-unity-r24/20261109-233004-812-Capture/frame-0360.png) | Paint planes, cabin, brightwork and raised-car grounding |
| [Media Luna](../../../evidence/cinder-unity-r24/20261109-233043-279-Capture/frame-0180.png) | Emerald body gradients, rear skirt, chrome and glazing |
| [City overview](../../../evidence/cinder-unity-r24/20261109-233103-714-Capture/frame-0000.png) | District-scale material/shadow continuity |
| [Nocturne, open](../../../evidence/cinder-unity-r24/20261109-233116-424-Capture/frame-0000.png) | Restored broad grey-blue body form and cabin separation |
| [Nocturne, raised cloth](../../../evidence/cinder-unity-r24/20261109-232351-864-Capture/frame-0000.png) | Roof coverage and glass/cloth relationship |
| [Matched cloth-hidden control](../../../evidence/cinder-unity-r24/20261109-232418-478-Capture/frame-0000.png) | Whether fabric actually occludes the scene |
| [Roof sequence, deployed](../../../evidence/cinder-unity-r24/20261109-232445-070-Capture/frame-0420.png) | Coverage during the recorded roof sequence |

The 870-frame roof session completed normally and is bound to the candidate executable. I sampled frames 0, 180, 360, 420, 600 and 869, including stowed, travelling, deployed and returned states. This is sampled visual evidence, not a claim that every frame or every camera angle was individually inspected. Other capture receipts likewise identify the same executable and normal completion.

Native references re-used for direct visual assessment: [Nocturne street](../../nocturne/review/native/street-cruise.png), [Nocturne roof](../../nocturne/review/native/roof-up.png), [Catrina studio](../../la-catrina/review/studio/front.png), [Mercer street](../../../build/city-realism/street-and-sky.png) and [Mercer overview](../../../build/city-realism/city-overview.png). Camera handedness, pose and studio/street lighting differ. This establishes retained identity and readable form, not pixel-identical renderer parity.

## Why the earlier lighting P1s close

The final street has the native masonry, base stone, window treatments, canopy, foliage, road texture and markings. Sunlit trim and pavement no longer overwhelm the scene. The overview holds together rather than falling back to the r9 substitute-kit appearance. Catrina's candy rose and Media Luna's green retain deliberate paint value changes. Nocturne now has broad grey-blue side and hood gradients rather than relying mainly on narrow perimeter trim to describe a near-black mass. These are visible outcomes in the final captures, not conclusions inferred from material values alone.

The previous reflection-unit error is now verified on this exact player. In [the r24 cube-decode diagnostic](../../../evidence/cinder-unity-r24/20261109-233215-086-Capture/render-diagnostics.json), GPU `unity_SpecCube0_HDR.x` is **0.6499023**, close to intended linear 0.65. r19 returned about 0.37988 from the same intended value. The host now encodes that linear target for Unity's API once. This corrects a measured incident-reflection-light loss rather than repainting the donor or increasing global exposure.

The [r24 sun-radiance diagnostic](../../../evidence/cinder-unity-r24/20261109-233227-810-Capture/render-diagnostics.json) gives GPU RGB **0.9228516, 0.8041992, 0.6401367**. Independently evaluating native linear `0xfff0d9 * 2.9/pi` gives **0.9230987, 0.8043578, 0.6405121**. The small differences are consistent with half-precision readback. `lightsUseLinearIntensity` is enabled before light creation. Both unit-control runtime receipts identify the final executable and normal completion.

The native single-sun policy is represented explicitly: original HDR for background/mirror level zero, extracted/clamped source for diffuse and rough reflection levels, and no reinjection because the scene already has its authored directional sun. The managed extractor's four CPU fixtures match the frozen native implementation; the actual bake found the HDR sun, not merely a theoretical fixture. Diffuse SH uses the clamped source with a calibrated unit-furnace normalization; the native hemisphere contribution is added as the existing normal-dependent irradiance blend divided by pi. This avoids r18's unremoved-HDR-sun washout.

The grade/output transform was already checked using actual constant-colour controls earlier in the restoration. The final source binding confirms the same selected transform, but that earlier control is not relabelled as a new r24 capture. In the final scenes the diagnostics retain linear ARGBHalf input and sRGB ARGB32 output. These facts support the colour chain; they do not establish every BRDF, roughness mip or angle as identical to native. Unity's filtered cube and Standard-based material response still differ from the native full-resolution GGX strip atlas and DFG/multiscattering response.

## Roof finding, corrected by matched evidence

The original r20 partial cloth failure was real. The native Nocturne adapter applies its two-sided canvas rule after loading the donor; that rule was omitted in the initial port. The subsequent correction restores coverage in the r23/r24 evidence. Low-angle imagery after that correction was initially misread as continued absence because the dark fabric and tinted glazing have low contrast.

The matched hidden control resolves that ambiguity. I independently formed a conservative 4,150-pixel canopy mask from the retained magenta control, excluding most edge pixels. Relative to the matched r24 hidden-cloth image:

| Normal candidate | Mask pixels differing by more than 3 RGB bytes | Median maximum-channel difference |
| --- | --- | --- |
| Matched r20 control | 40.17% | 0 bytes |
| r23 | 99.95% | 61 bytes |
| r24 | 99.95% | 61 bytes |

The supplied [coverage receipt](../../../evidence/cinder-unity-r24/roof-coverage-comparison.json) uses a slightly wider 4,267-pixel mask and reaches the same conclusion. My independent mask corroborates it rather than reproducing its edge definition exactly. This is a rendered occlusion comparison, not exhaustive triangle-level opacity proof.

The entire r23 and r24 normal RGB arrays are identical, with zero differing pixels. Therefore r24's dedicated explicit-Cull-Off Canvas shader is a narrower material adapter with the same observed appearance; it is not evidence of a new visible improvement over r23. The final roof receipt identifies three active, enabled, supported Canvas renderers, all in view, at phase 1, with 4,274 triangles and authored colour/opaque queue. More importantly, actual normal-versus-hidden pixels establish coverage. The native two-sided-rule P1 is closed for the reviewed raised roof and sampled sequence.

## Remaining P2 work and limits

1. **Fine chrome and grille stability:** thin brightwork and dense wire wheels still produce hard, broken highlight pixels at 960 x 600. Display-space FXAA and filtered roughness help, but sampled stills do not prove temporal shimmer is gone. Assess a short slow camera move before any future claim of stable final brightwork.
2. **Glass and fabric readability:** large shop panes remain flat and repetitive. The raised Nocturne roof is opaque, but glass tint and dark cloth can visually merge from this camera. This is now a contrast/readability refinement, not a missing-geometry claim. Keep native cloth colour and opacity; use a targeted glass/material comparison if improving it.
3. **Contact and environment finish:** shadows ground the parked cars and the street is coherent, but contact softness, broad road repairs and facade treatment remain visibly synthetic. The native assets themselves set part of this ceiling. A faithful port is not automatically finished environment art.
4. **Compiler diagnostics:** explain or remove the four retained warnings in a later candidate, preserving the current packet and comparing output. No concrete visible failure was established from those warnings in this review; that does not justify silently ignoring them.

No new P1 lighting issue was found in the inspected final packet. The remaining work above does not erase the demonstrated restoration, and the demonstrated restoration does not elevate the absolute lighting score beyond 7.0/10. This report does not approve overall art, production quality or paid release.

Physical controls, input feel, heard audio, comfort, comprehension, enjoyment and handheld 1080p/60 remain unverified. The evaluation stayed within the existing capped capture profile. Preserve r9 and all rejected intermediate packets, including the original partial-roof evidence and the later controls that corrected the diagnosis.
