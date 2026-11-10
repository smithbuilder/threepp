# Independent city review — signed r16

November 9, 2026, Pacific Time. City/environment evaluator; did not implement the restored city, shaders, materials, camera or vehicle batching. No player/editor/exporter was launched by this reviewer. This review inspects existing original player PNGs, native references, receipts and bound source.

## Verdict

**The missing-city-content regression is visibly repaired in the sampled r16 views. The city again resembles native Mercer rather than the simplified r9 test strip. Absolute environment presentation is 5.5/10.**

No remaining **P1 omitted-city-content or broken-world-continuity defect** is demonstrated by these frames. This closes the specific preservation failure identified in the r9 city review for the shown locations; it does not make this a high-quality finished city. Native Mercer itself is repetitive, empty and only lightly art-directed. Recovering that baseline cannot by itself satisfy an 8.0 weakest-aspect gate or establish paid-release quality. Do not translate this scoped restoration finding into overall visual acceptance.

There is no new whole-game or car score here. I have not validated motion readability, sustained performance, physical controls, heard audio or enjoyment.

## Exact evidence binding

The player file was hashed directly and matches **`313F2FF325126FCF747837DA3273727D2BE9A383F2903F4D22BC7BEFD9F9ED49`**. The supplied signed-player identity is consistent with all five inspected capture runtime receipts. Each records `cinder-unity-r16`, that executable hash and normal completion. The completed build receipt records Unity 6000.3.6f1, zero errors, two warnings and source fingerprint `5de112ab561a2ad1a300fb0bcfc6f3f85b54445b0658a7acb80865a26e1cd161`.

`latest-probe.json` and its runtime receipt bind the same executable and report **204 simulation, 495 rig and 124 runtime-batch checks**, success. These checks support technical identity/regression coverage, not the aesthetic rating.

Current city GLB/material ledger and the inspected View, City/CityFoliage shaders, NativeCityMaterials, GlbImport, CinderBuild and StandaloneHost source hashes were individually compared against `evidence/cinder-unity-r16/source-manifest.json`; all match. The staged city material receipt binds `assets/unity/city/materials.json` SHA256 `16389d7533c7bb0bb3ee2901f15ca3d84ddebb133c406fc002eeae98ba9476c9`. The city GLB remains SHA256 `5e72ee0027ded63d87e599b0e0af5e98be019f5d8c080602acff3e6022eb599d`, covered by the earlier independent data review and sampler/provenance addendum.

## Images opened

Each r16 path below ends in `/frame-0000.png` under `evidence/cinder-unity-r16/`.

| Capture folder | Visible evidence |
| --- | --- |
| `20261109-215203-580-Capture` | Garage/front door with Catrina, detailed coffee/loft frontage, legible coffee lettering, tree, parking, double yellow lines and connected background |
| `20261109-215216-323-Capture` | Catrina close street view: actual window subdivisions, recess/sill/base layering, shop canopy, kerb joints, parking paint and asphalt repair |
| `20261109-215229-068-Capture` | Luna at the same frontage: car-to-road scale, richer canopy silhouette, clear building/vehicle tonal separation and restored street elements |
| `20261109-215241-800-Capture` | Nocturne street view: intact full facade context, pavement edge, centre lines, repair patches and grounded placement |
| `20261109-215255-343-Capture` | District overview: all block faces, fire escape, rooftop equipment/parapets, junction crossings, furniture/trees, boundary and surrounding shells |

Native controls: `build/city-realism/street-and-sky.png`, `city-overview.png`, `docs/nocturne/review/native/street-cruise.png` and the original Catrina street frames in `build/sessions/20261106-123108-529/frames/`. These are historical references, not newly captured matched controls. Cameras, car positions/headings, some poses and lighting differ. The overview has particularly different framing. Content presence and gross readability can be compared; pixel colour/contrast differences do not isolate a renderer defect.

## Restoration findings

- **Architecture:** Photographic masonry has proper scale and variation again. Deep-looking dark reveals, mullions, curtains/blinds, selected AC units, sills, coping and fire escape replace the uniform r9 panes-on-boxes treatment. Roof equipment and connected facades are apparent in the overview. The dark storefronts remain simple but now have convincing architectural surrounds.
- **Street design:** Twin yellow lines, parking bays, segmented kerbs, crossings, road patches and visible furniture restore vehicle-scale cues. These are useful for slow cruising and parking; there is no need to turn the environment into a racing circuit. Tyre-scale street detail is visible even in the static car frames.
- **Continuity:** The overview visibly restores distant shells, perimeter treatment and a connected block layout. The shown coffee frontage no longer ends in the conspicuous r9 empty beige/sky gap. No full route or every reverse street-end angle was inspected; the claim is confined to the packet.
- **Materials and light:** Pavement and trim no longer flare against an almost-black simplified road/shop backdrop as in r9. Brick, stone base, road and markings have distinct surface character. Shop lettering reads correctly in the supplied view. Baked static shading survives while car contact is visibly present. These observations support successful integration; they do not prove exact native photometric parity.
- **Foliage:** Clustered, volumetric silhouettes and branching trunks replace r9's exposed branch fans and scattered green shards. The current shader uses textured cutout foliage with native colour data. Canopies still have hard dark edges and coarse leaf masses at this resolution, so “realistic trees” would overstate the result.
- **Lowrider context:** The improved street gives the cars a credible scale and setting, and the larger menu car is easier to appreciate. The cultural promise remains stronger in the menu wording and cars than in the place itself: this still looks like a quiet generic business block rather than a memorable gathering destination.

## Remaining quality work and limits

**P2 — storefront/place quality:** Large opaque dark panes have little interior or human-scale story. Repeated windows, similar buildings and clean wide sidewalks make the place feel unoccupied. A focused coffee/workshop corner with deliberate parking/display composition and a few specific authored details would matter more than more map area. A crowd/traffic system is not a prerequisite for that improvement.

**P2 — canopy and atmosphere:** Dense dark canopy masses, rigid repeated street trees and simple distant shells limit the scene's visual richness. Judge canopy highlights, cutout edges and street depth in the existing bounded motion clip before spending additional effects or raising any graphics limits.

**P2 — evidence coverage:** The packet proves the hero frontage and one overview. A slow route/reverse view is still needed to establish that less flattering angles do not expose new problems. The source/data audit supports retained content beyond the crop; it cannot replace observing runtime presentation there.

The evidence's one-frame counters report Catrina **693,585 scene triangles / 216 draws**, Luna **583,929 / 192**, Nocturne **683,557 / 154**, and overview **450,326 / 169**. Draw counters are marked available for these frames. The triangle value is the view's active scene-geometry tally; it is not a GPU measurement of all triangle submissions across shadow/material passes. The captures contain one frame and zero timing summaries, so these are bounded snapshot counters, not a performance benchmark. Do not infer 1080p/60 or sustained <=300 draws from them.

**Disposition: original city fidelity blockers repaired in the sampled signed r16 output; absolute city presentation remains 5.5/10 and broader quality acceptance is not granted by this report.** Keep r9 and intermediate failures. Any next verdict must refer to its exact player, preserve these comparison limits, and include actual movement and the remaining world angles.
