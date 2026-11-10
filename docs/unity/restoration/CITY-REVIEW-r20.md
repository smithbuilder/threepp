# Independent city review — signed r20

November 9, 2026, Pacific Time. Independent city/environment evaluator. Did not implement the restored city, lighting, shaders, material import, batching or camera. No player/editor/exporter was launched by this reviewer; existing original PNGs, receipts and owning source were inspected.

## Verdict

**Native-relative city preservation is supported in the inspected r20 views. Absolute city presentation: 6.0/10.** Daylight readability is better than r16: road, stone base, glazing divisions, shaded masonry and car-side context separate more coherently. The missing-content regression from r9 has not returned.

No remaining **P1 omitted-city-content or broken-continuity defect** is established by this packet. However, the environment remains a generic, sparsely inhabited prototype. **This is not an 8/10 city and does not meet the Level 2 weakest-aspect presentation threshold.** Restoring native geometry and repairing light response do not waive the absolute quality requirement. This report grants neither whole-candidate visual acceptance nor paid-release approval.

This is a city score, not a new score for the cars or the game. Physical controls, heard audio, comfort, enjoyment and target-device performance remain outside this review.

## Exact candidate and source checks

- Player SHA256 independently checked: **`59E549C1B31425C704DC2F035273628C016F4E0DAC17B74BC9E418F3CB624347`**. Normal capture receipts below bind that executable and `cinder-unity-r20` with normal completion.
- Build receipt: Unity 6000.3.6f1, success, zero errors, four warnings; source fingerprint `abce083872686ce28a7fc4b59ff766a9fda616fdf1d1e39d7d9beb9042792f4d`.
- Exact-player probe receipt: **204 simulation + 495 rig + 148 runtime-batch checks**, success. These are technical checks, not an aesthetic pass.
- Ten inspected files individually match `evidence/cinder-unity-r20/source-manifest.json`: city GLB, material ledger, CinderView, City/CityFoliage shaders, NativeCityMaterials, CinderSkyBake, StandaloneHost, ambient-sh.json and environment-sun.json.
- The city GLB remains `5e72ee0027ded63d87e599b0e0af5e98be019f5d8c080602acff3e6022eb599d`; the earlier independent geometry/ground/provenance review still applies. This build is not a new by-eye city replacement.

The source now applies baked low-frequency HDR diffuse SH, native-sun-clamped environment data and the hemisphere contribution. Existing bake receipts report white-furnace error `5.841255e-6` and hemisphere error `7.450581e-9`; the separate CPU sun-extraction parity report covers four fixtures with zero maximum output difference. These support the conversion's tested components, not universal pixel parity. The SH ledger explicitly describes a low-frequency approximation to native diffuse PMREM. Normal runtime enables linear light intensity and encodes the intended linear reflection strength before Unity's API conversion. The experimental local reflection is still opt-in; it is not needed to explain or approve these normal images.

## Original images inspected

Paths below are under `evidence/cinder-unity-r20/`; all are normal rendering with `material-control.json` reporting `control: none`. Diagnostic direction/normal/cube/white/sun-control captures were not rated as finished presentation.

| Folder and frame | What was judged |
| --- | --- |
| `20261109-223346-926-Capture/frame-0000.png` | Default menu, Catrina and coffee/loft street composition |
| `20261109-223334-186-Capture/frame-0000.png` | Nocturne side, road/base/shop relationship and normal ambient response |
| `20261109-223613-062-Capture/frame-0000.png` | District overview: four-sided facades, rooftop detail, trees, furniture, junctions, boundaries and surrounding shells |
| `20261109-223615-943-Capture/frame-0000.png` | Nocturne driver view: forward street canyon, opposite facades, pavement edges, trees, sky and distant continuation |
| `20261109-223700-925-Capture/frame-0000.png`, `frame-0400.png`, `frame-0720.png` | Catrina normal/raised/reverse samples; street context survives the different car pose/framing |
| `20261109-223739-453-Capture/frame-0000.png` | Luna at the common frontage; daylight material and canopy relationship |

Also inspected the r20 Catrina rear-wheel close frame `20261109-223628-707-Capture/frame-0000.png`; it is a detail view, not sufficient city coverage. A paused UI-probe frame was not used to judge the normal scene's darkness.

Native reference images reopened: `build/city-realism/city-overview.png` and `docs/nocturne/review/native/street-cruise.png`. Earlier native street/Catrina references remain documented in the independent reassessment. Native and Unity cameras/headings, some poses and lighting differ. Consequently this review compares recognizable content, scale and readability; it does not claim a pixel-matched photometric or geometry experiment. The r16 controls are the exact earlier captures named in `CITY-REVIEW-r16.md`.

## Native-relative preservation and improvement

**Architecture and continuity:** Detailed masonry, window mullions and treatments, stone bases, projecting sills, parapets, roof equipment and fire escape remain present. The overview and cockpit view show a connected district with context behind the playable block, rather than the r9 sky-only gap. The local coffee sign reads correctly. No newly missing building face or district-context category appears in the packet.

**Street design and scale:** Kerb segmentation, parking, double yellow lines, crossings, drainage/street objects and road repairs continue to give the cars a credible metre scale. The overview agrees with the retained native layout. The cockpit shows enough street depth to support quiet cruising; racing gates or a larger map are not the missing quality ingredient.

**Light/material readability:** Compared with r16, dark shop divisions and road surfaces are less crushed, the stone base and pavement separate more clearly, and shaded car context is easier to read. The common frontage does not exhibit the glaring cream trim/flat paving opposition of r9. These are observed improvements. A particular CPU fixture pass does not, by itself, prove their cause or artistic quality.

**Foliage:** Native clustered branch/canopy geometry and cutout colour variation remain, and the daylight canopy is readable. It is still coarse, repeated and sometimes hard-edged; a low rear-detail angle exposes a pale flat-looking leaf mass against the dark facade. That is a remaining foliage presentation issue, not evidence that the restored native tree geometry disappeared.

## Why the city is still 6/10

1. **P2 — storefronts and destination have little authored life.** Long opaque blue-grey panes and repeated dark awnings dominate the closest street. There is little visual specificity suggesting what happens inside or why this particular corner is a destination. A convincing lowrider gathering place needs a composed coffee/workshop frontage and a deliberate parking/display spot, with a few specific details tied to the cars and culture. This does not require a crowd or traffic system.
2. **P2 — block variety and atmosphere remain limited.** Similar rectangular buildings, repeated window rhythm, broad clean pavement and simple context shells make the district look procedural and unoccupied. The current imagery shows successful restoration of an unfinished native environment, not a distinctive finished neighborhood.
3. **P2 — close canopy/road-wear finish is uneven.** Leaf masses and edges remain crude at low car angles; some repair patches read as conspicuous dark polygons rather than accumulated street wear. Refinement should be judged at cruising distance in the player, not in a top-down count or source recipe.
4. **P2 — whole-route presentation is not established.** The cockpit view improves directional coverage and sampled flow frames add pose variation, but this review did not watch a complete route or continuously inspect temporal edges. Do not claim every reverse street end or moving canopy/trim edge is approved.

These are finite art-quality deficits. Additional shader troubleshooting alone will not produce an 8/10 city. The next useful art milestone is one memorable, coherent gathering corner with a strong near-field composition, before expanding map scope.

## Runtime evidence limits

The 780-frame Catrina culture capture records median/p99 **33.3324/34.0706 ms**, **216 maximum draws** and **693,585 active scene triangles**; its external runtime receipt records **415,969,280 bytes** peak working set. The 240-frame Luna capture records **192 maximum draws** and **583,929 active triangles**. The Nocturne normal still records **154 draws / 683,557 triangles**, and the overview **169 / 450,326**.

These are conservative 960×600, 30 fps captures with PNG IO, not a target-device benchmark. The triangle counter is the View's active scene-geometry tally, not a GPU count of all material/shadow submissions. Snapshot counters and short capped flows cannot establish sustained 1080p/60, whole-route budgets or physical device stability. They are useful evidence within their recorded scope.

**Disposition: native city preservation supported, readability improved, original missing-content P1 closed in sampled views; absolute city quality 6.0/10, Level 2 presentation gate not met.** Retain all earlier failed packets and this exact-player evidence. Any next acceptance claim must be based on visibly improved art and fresh bound runtime evidence, not a requested score or an average that conceals this remaining weakness.
