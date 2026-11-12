# Independent sunset quality review: r28

November 11, 2026, Pacific. This evaluator did not implement the sunset sky, city shade bake, practical-light shader, host lighting or camera changes. No player/editor/exporter was launched. This review inspected existing actual player PNGs, finite sequence samples, periodic pose receipts, source bindings and paired runtime records.

## Verdict

**r28 delivers a visibly more deliberate early-evening lighting direction than r25. It reads as sunset before full darkness, with readable streets, warm sun-facing surfaces, cooler shade and existing lamps beginning to illuminate nearby surfaces. No new P1 is demonstrated in the inspected final evidence.**

| Aspect | Judgment | Meaning |
| --- | --- | --- |
| Lighting and evening art direction | **7.5/10** | Clear scene-wide improvement; coherent colour/mood and useful localized practicals, with approximate shadows and remaining reflection finish |
| Car identity/presentation preservation | **7.0/10** | Catrina rose/lace, Luna teal/sage/ivory and Nocturne dark flank/canvas survive; view-dependent bright reflections and fine chrome remain imperfect |
| City artwork/place quality | **6.0/10** | Restored native content is preserved, but repeated storefronts, coarse foliage and a generic, sparsely inhabited block remain |

These scores must not be averaged into a whole-candidate pass. **Broader Level 2 presentation remains below its 8/10 weakest-aspect target.** The requested evening direction is supported within this prototype review; paid-release quality, physical controls, heard audio, enjoyment and handheld performance are not approved here.

## Identity and controls

Player SHA256 independently checked: **`BBEA8C386456DD9C07DD2348C5B2DD23618AA741BDBA69DD14088990AEAD2AA8`**. The completed build records Unity 6000.3.6f1, zero errors, four warnings and source fingerprint **`baf3a961c9ac75792e9150a4d3c16e9c8ebb8f042252a78be594cb575fe9580e`**. Exact-player probe: **204 simulation + 495 rig + 154 runtime-batch checks**, success. The final packet records a Valid signature for that executable.

Fourteen inspected files individually match `evidence/cinder-unity-r28/source-manifest.json`: CityEveningLighting, StandaloneHost, shared evening-light shader include, CinderView, Body/City shaders, CinderGrade, both sunset bake implementations, sunset SH/profile ledgers, sunset city bake receipt and frozen city GLB/material ledger. Normal capture receipts bind this exact executable and profile `mercer-six-pm`. Explicit daylight/lamp controls are identified below rather than treated as ordinary product imagery.

The original r25 profile/stills remain the prior daylight presentation control. The matched r28 `daylight` mode isolates the profile inside the new executable; it is not claimed to be byte-identical to the r25 renderer.

## Actual images inspected

All take folders below are in `evidence/cinder-unity-r28/`, with prefix `20261111-` and suffix `-Capture`.

- All six final packet stills in `review/`, including normal garage, pause/quit, Catrina three-wheel, Luna lift and Nocturne roof view.
- Normal sky/street vista `204729-477/frame-0000.png` and its daylight control `205056-911/frame-0000.png`.
- Normal Catrina `204842-036`, Luna `204920-549` and Nocturne `204941-030` takes through final selected stills; additional Nocturne frames zero/450 were opened.
- Focused lamp-on `205023-250/frame-0000.png` versus lamp-illumination-off `205040-078/frame-0000.png`, emission retained. Both pose fingerprints are `f9602a28cea82a52`, tick 242. Their explicit lamp-review placement is focused evidence, not a normal delivery view.
- Normal street drive `205155-450/frame-0000.png`, `frame-0060.png`, `frame-0119.png`; normal cockpit `205212-275/frame-0000.png`.
- Normal Nocturne side `205346-520/frame-0000.png` and daylight front-quarter `205403-256/frame-0000.png`, bound to the same player. The daylight front-quarter and normal Nocturne frame 420 share fingerprint `a57d1df31e3bdbc3`, tick 842; the side has a different viewing angle.

The mechanical packet contains six stills and a 69-second clip. This evaluator inspected original stills and selected sequence frames, not continuous playback of the complete clip. That distinction limits any motion/stability claim.

## What improved and what survives

**Time of day and readable shade:** The sunset-facing vista has a warm peach horizon/cloud field and lavender/cooler upper transition. The opposite-facing cockpit retains a cooler blue sky rather than imposing an orange filter everywhere. Warm facades, cooler shaded windows and readable road between fixture pools create a credible early-evening relationship. The revised neutral/cyan-grey fill avoids r27's excessive plum cast. Shadow-side surfaces remain darker than daylight, but the street does not depend exclusively on lamps for visibility. Menu copy now says **EARLY EVENING**.

**Practicals:** The matched on/off pair visibly changes actual pavement and nearby facade brightness while leaving the fixture source present. Light belongs to the underside of the authored heads, and the localized ground/wall contribution does not wash the entire scene. Runtime records identify eight bounded fixtures. At intensity 28, they read as beginning to matter rather than the stronger r26 spotlight treatment. These observations establish visible surface illumination, not complete occlusion fidelity.

**Catrina:** Rose/magenta and pale lower panels remain distinct. The revised garage angle reduces r26's broad hood whiteout; the normal three-wheel still visibly retains gold lace and cabin form. Hood/roof reflections are still strong, and some menu ornament has lower contrast than daylight. This is P2 finish, not a claim of perfect hero-art preservation at every angle.

**Luna:** The rejected r27 navy/plum reading is resolved in the inspected r28 poses. Broad door/fender planes read teal again; roof/window frame remain pale sage/grey-green and whitewalls ivory rather than pink. Warm reflected edges retain the evening mood without replacing the car's base identity. Unchanged material factors alone were not accepted as proof: the actual frames establish this improvement.

**Nocturne:** The first front-quarter view appears much lighter/greyer than r25, with a peach hood reflection. The additional normal side confirms a substantial dark blue-black flank survives. Its pale front-quarter appearance is view-dependent reflected environment, not evidence of a completely repainted car. Burgundy cabin and visible canvas/deck stages remain distinguishable. Bright bumper/hood reflections and grey-looking quarter views remain P2 presentation limitations.

**Street and receiver repair:** Original facade detail, trees, street markings, kerbs, patches and context remain. The prominent bright repair/marking cutout inside the earlier long car shadow is absent in the selected r28 evidence. Source now enables reception on ground plus repair, white/yellow paint, asphalt and dark mixed batches while disabling city casting. Selected drive/stance frames do not expose a new obvious receiver hole. This is not an exhaustive test of every overlay or moving shadow edge.

Across the three full action takes, all **63 periodic contact receipts** have finite footprint values in [0,1], with zero extra contact weight at every sampled ungrounded wheel. Added contact remains separate from the sunset's long direct shadows. These finite samples do not prove transition smoothness between receipts.

## Remaining limits and P2 work

- **Static shadow approximation:** Building/canopy shade is an analytic vertex bake over unchanged adaptive ground; new low-sun boundaries interpolate across triangles reduced for daylight. Long shadows are directionally plausible in the inspected views but sometimes soft/coarse. They are not full dynamic building, leaf or bench shadows, nor a per-pixel sunset-shadow proof.
- **Lamp visibility:** City UV2/UV3 data represents vertex-sampled visibility against eleven building volumes. Interpolation, mixed receiver batches and unshadowed moving objects remain compromises. No complete car/bench/foliage occlusion or fixture self-shadowing claim is supported. Actual on/off evidence is stronger than an emission-only preview, but it does not remove these limits.
- **Reflection/highlight finish:** Catrina hood/roof contrast, Nocturne's pale quarter reflections and fine chrome can still dominate local material detail. There is no broad bloom veil in the selected normal views. This sunset's reduced bloom is not independently proven free of the earlier tiny dark-cabin spill at every angle.
- **Temporal coverage:** The drive samples show a stable-looking lighting relationship at start/middle/end, not proof of continuous no-pop lamp falloff or shimmer-free paint. Complete watched passage/roof/stance motion remains a stronger acceptance step.
- **City art:** Evening light adds mood but does not populate the street, differentiate repeated businesses or create a distinctive lowrider gathering destination. Those existing artwork limits remain separate from this lighting revision.

## Paired runtime evidence

Both matched 180-frame Catrina tests record fingerprint `972aede729b16d4d`, **693,585 active scene triangles**, **82 renderers** and **219 maximum draws**:

| Candidate and session | Median / p99 ms | External peak working set |
| --- | --- | --- |
| r25 `20261111-205113-734-Benchmark` | 33.3414 / 36.0492 | 436,563,968 bytes |
| r28 `20261111-205134-194-Benchmark` | 33.3378 / 35.0822 | 462,155,776 bytes |

The active geometry and observed draw totals are unchanged in this test; external peak rises by about 24.4 MiB. These are short capped 960×600/30 fps runs with PNG IO. They do not establish GPU headroom, a speedup, sustained whole-route budgets or handheld 1080p/60. Active geometry is not all-pass GPU triangle submission count. Existing one-512-shadow, serialized hidden/silent/watchdog/2 GiB guards remain binding.

**Disposition:** requested early-evening direction supported in the inspected exact r28 output; r27 Luna palette and earlier road receiver defects resolved in sampled views; no new concrete P1 demonstrated. Lighting 7.5/10, car preservation 7/10, city art 6/10. Broader art and human/device acceptance remain unmet or unverified as specified above.
