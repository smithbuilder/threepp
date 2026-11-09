# Cinder visual reassessment and restoration brief

November 9, 2026, Pacific Time. Current evaluated player: `cinder-unity-r9`.

## Decision

**Oliver is right: city, lighting and car presentation have regressed. Visual acceptance is withdrawn.** The existing Unity simulation and menu work do not establish a faithful visual migration. The earlier 8.0/10 presentation approval was too generous and addressed the wrong comparison: whether a functional prototype looked presentable, rather than whether the migration preserved the native title's visible quality.

[Open the unchanged-image comparisons](../../../art-review/unity-reassessment/index.html).

No new fixed player is delivered by this assessment. No editor/game was launched. No runtime, source model, shader, material or native file was changed. This work delivers three fresh independent reports, original-image comparisons, an ordered repair brief and corrected acceptance documentation. The 204 simulation checks, 495 finite loaded-mechanism checks and scripted menu results remain historical technical evidence, within their documented limits.

## What the fresh evaluators found

The evaluators were newly assigned separate lanes and did not author the reviewed surfaces. They inspected actual player PNGs, native references and owning source. Previous scores were not targets; this is not a re-vote by the earlier presentation reviewer.

| Lane | Fresh judgment | Main finding |
| --- | --- | --- |
| [City and environment](CITY-INDEPENDENT.md) | Unity environment 3.5/10; native environment 5.5/10 | Eleven building masses survive, but much of the original facade construction, street detail, foliage and surrounding district was replaced or omitted. Native itself remains unfinished. |
| [Car presentation](CARS-INDEPENDENT.md) | Current cars 5/10 | Silhouettes and identity largely survive. Palette separation, lacquer/metal readability, cabin warmth and ground contact regress. |
| [Lighting and rendering](LIGHTING-INDEPENDENT.md) | Substantial native-relative regression; no numerical rating requested | Lost authored static shading and several PBR inputs, reflection filtering/orientation mismatch, and a different light/output chain compound the content loss. |

The scores describe different scopes and must not be averaged into a whole-game grade. The source-based findings explain visible loss; individual pixel-level causes still need isolated experiments. Native-relative preservation and absolute visual quality remain separate questions.

## The missing pieces, in plain language

1. **Mercer has become a simpler stage.** Building positions were copied, but the facade kit was rebuilt as boxes, thin dark panes and bright trim. Real window surrounds/openings, varied blinds/curtains, roof/service detail, street furnishings, drainage, parking/road wear, boundary treatment and fifteen distant building shells were not faithfully carried over. Slow lowrider cruising exposes these omissions.
2. **The street lost much of its authored light and surface response.** Native building/tree shade and contact variation were baked into static colours. The replacement city ground uses white vertex colour, the new walls do not carry that native shading, and several road/pavement/facade roughness and normal inputs are unassigned or unstaged. Reusing a brick photo alone does not preserve a material.
3. **The cars no longer read with the same richness.** Teal, rose, ivory whitewalls, silver trim and burgundy upholstery compress into dark body/cabin masses with bright granular chrome. The bodies look less grounded. The detailed models should be diagnosed under controlled light before anyone remodels or repaints them.
4. **Reflections and the light/output chain need calibration.** The visible sky is rotated independently from the reflection cube; the cube has no explicit specular convolution. Unity's current grade is a different transform from native, and the lighting balance also differs. The images show the problem, but do not isolate how much each change contributes.
5. **Trees and framing undersell the cars.** The native branching/canopy system was replaced by sparse geometric leaves; authored leaf variation is in COLOR_1 while the importer reads COLOR_0. The menu gives the hero car relatively few pixels, while the bright flat buildings compete with it. This is an asset and presentation problem as well as a shader problem.

The reports explicitly avoid false diagnoses: HDR, tone mapping, an FXAA-like filter, clearcoat and car vertex-colour import already exist. There is no evidence that whole interiors or the car meshes were deleted. The current images do not prove flipped winding, a missing car AO texture, a tangent-space bug or premature HDR clipping. Those claims require focused diagnostics.

## Evidence and comparison limits

Exact r9 executable SHA256: `5CF25D276D9331F1C6AA01994BD641586EDA28EC52EFCEAC31E1D54D3898448E`.

The fresh city/lighting lanes checked the current owning source against the r9 source manifest. The city lane also checked native `CityBlock.hpp` and `CityLayout.hpp` against the dated native-realism receipt. Car reviewers opened individual native and raw Unity PNGs, not just the final compressed clip. The gallery copies three native references unchanged and references three unchanged committed r9 stills; `art-review/unity-reassessment/comparison-manifest.json` records their SHA256 values.

These are historical 960 x 600 captures, with different cameras, sun directions, background and some poses. They demonstrate content/readability loss but are not a photometric or geometry-parity test. Catrina and Nocturne frozen GLB hashes match their relevant native receipts. Media Luna's frozen GLB differs from the older native receipt, so that pair also has a source-version confound. Do not attribute every Luna difference to the renderer. The Catrina file named `04-catrina-hop.png` is actually the right three-wheel stance.

## Ordered restoration work

### 1. Establish exact visual controls

Freeze donor/source identities and deterministic parked/raised states. Record camera position, target/FOV, car pixel size, sun direction, sky/reflection heading, exposure, material identities and resolution. Make a neutral car/material control plus a matched Mercer corner. Capture raw pre-grade floating-point values and a neutral/colour/roughness chart only in focused diagnostics. Do not change several lighting/material variables in one experiment.

### 2. Recover one complete Mercer corner

Restore the coffee/workshop corner, its four-sided facade construction, street, kerb, tree and visible surrounding context from the native source data. Prefer an offline export of the existing merged geometry, UVs, material identities and static shade/colour, verified through the Blender 4.5 asset pipeline, over another simplified by-eye kit. Keep native sources untouched and no second engine at runtime. Preserve the shared collision surface and pure simulation.

Use faithful normal/roughness/albedo assignments and metre scale. Restore static shade without doubling it with the realtime building shadow. Prove the corner at car height before replicating it across the district. Account explicitly for each omitted content category; no silent scope reduction to meet the budget.

### 3. Calibrate reflections, materials and output

Validate a specular-filtered environment, roughness-dependent mips and consistent sky/reflection orientation before increasing cube size. Compare the unchanged car under equivalent studio light and on the restored corner. Isolate the output transform, then light balance, then clearcoat/normal and glass behavior. Recover rose/teal/black paint, ivory whitewalls and warm upholstery without brightening base colours to compensate for an incorrect lighting chain.

### 4. Restore weight and fine detail

Restore tyre/chassis grounding and cavity readability within the existing single 512-pixel shadow/resource limits. Separate static street shade from moving-car contact. Check broad chrome gradients and thin spokes/trim in motion; the existing edge filter does not establish specular stability. Recover leaf variation, clustered canopy, bark and inexpensive light/shadow integration. Then restore road wear, benches, signs, hydrants, bins, parking/drains and a deliberate coffee/workshop place to park and display hydraulics.

### 5. Recompose the lowrider front door and review the whole street

Give the selected car enough screen space to sell its finish. Include Catrina decoration, Luna two-tone/whitewall palette and Nocturne's open warm cabin. Restore street continuity and reverse views, not only a flattering hero crop. Keep Safari/buggy racing deferred. One compelling gathering corner should work before expanding map scope or adding unrelated effects.

## Budget and change boundaries

Remain on Unity 6000.3.6f1, Built-in forward, Linear, D3D11. Keep runtime changes in View/Editor/art authoring. Preserve Sim, donor files, recorded poses and the physical contact surface. No engine/pipeline change is justified by these findings.

Retain guarded hidden/silent/bounded 960 x 600 / 30 fps evaluation, 2 GiB job, memory/disk checks, process exclusion, shared mutex, cool-down and watchdog. This brief does not authorize wider graphics limits. Prefer offline static work and batching before adding realtime passes.

The scene targets remain <=700,000 submitted triangles and <=300 draws. r9 measured 687,908 triangles and 685 draws, so draw reduction is still required. The native city reports 566,118 triangles including its contact grid; adding an unchanged 309,624-triangle Catrina suggests about 875,742 before visibility/detail management. This arithmetic is a planning warning, not a measured new Unity scene. Use visibility, batching and authored distance tiers to preserve near-field fidelity within the budget rather than deleting defining street content. Measure actual candidate results before acceptance.

## Next acceptance packet

Focused diagnostic packets may isolate one corner or car. The final whole-candidate packet stays at three to six stills and <=90 seconds of original player motion, exact source/build/asset hashes and replay inputs. Suggested six final frames:

1. Matched coffee/workshop frontage with Catrina and readable pavement/kerb.
2. Matched full side plus reverse street end showing facade/context continuity.
3. Catrina lacquer/lace/gold trim at useful pixel size.
4. Luna raised stance with teal/sage paint, ivory whitewalls and loaded/lifted contact region.
5. Nocturne open cabin with burgundy upholstery and clear glazing/body separation.
6. Close street/tree/brightwork view proving material scale, canopy and chrome treatment.

Use the short motion clip for a slow car roll/camera move, stance changes and wider street continuity. Keep failed A/B controls. Review city, lighting and each car separately; describe preservation/remaining defects before scores. A technical pass or a favorable generic prototype score cannot waive a native-relative visual blocker. Human input feel, heard audio, comfort, comprehension, enjoyment and handheld 1080p/60 remain UNVERIFIED.

## Review process correction

The preceding r8-to-r9 reviews concentrated on local improvements inside an already simplified replacement. That confirmed a small improvement over r8, not an acceptable migration from native. Mechanical probes were useful but did not test art. Main-menu usability and clever moving parts cannot carry a city/material failure. The original reports, tag, builds and packets remain unchanged for history; this reassessment supersedes their broad presentation-acceptance claim.

Current state: **technical port available; visual-fidelity gate FAIL; restoration brief ready**. No fixed-build or gameplay-improvement claim is made. Playbook reassessment task: `cmw9qrsq000alle018qlbcxni`, owner `z2-codex`. No active Cinder/Unity Bridge thread was found, and no unrelated thread was used.
