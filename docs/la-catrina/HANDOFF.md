# La Catrina — accepted model and street film

La Catrina is available locally as the fifth vehicle in Mercer City Block and the Vehicle Tuning Playground. The frozen round-11 model passed two independent comparisons against the original reference sheet: **8.020/10 and 8.115/10**, both above the requested 8/10 threshold without rounding up. The finished **48-second native street film** shows front hopping, a closer wheel view, left and right three-wheel driving, and a cruising exit.

## Open the result

- **Play:** `Launch-La-Catrina.cmd` offers manual city driving, the automatic street show and the suspension playground. Controls are in the repository-root `LA-CATRINA.md`; J hops, K/L select the three-wheel sides, U raises the car and N returns low. The hydraulic-bay checkbox opens the trunk.
- **Watch:** `videos/la-catrina-street-show/outputs/La-Catrina-Street-Show.mp4`.
- **Portable model:** `asset-library/models/la-catrina/la-catrina.glb`, with its material maps, manifest and provenance in the same folder.
- **Editable film project:** `videos/la-catrina-street-show/`, including the timeline, six native source clips, sound sources, provenance and verification records.
- **Reference and inspection:** `docs/la-catrina/references/La-Catrina-Master.jpg` and the 16 native views under `build/la-catrina/round-11/studio/`.

## Frozen artifact and independent review

| Artifact | SHA256 |
|---|---|
| Accepted model | `8444acaabf320f15fc3157342f4d23baa0b03b701d99af365608f48c4c16cb3e` |
| Geometry before baked shading | `3a34f488900e3ef36348753b32e570ef52c9c2b3ef0deaf89f79ab1eb25d1d3f` |
| Signed driving / physics executable | `dee326b1ba9736e3686660bce1a78b2d6b7e136fe6c78b9cff954f4a592c2203` |
| Separate inspection executable | `3123b9cf2570657b8c1e9a54c3f31160f2b2f81845e1b167e31432baa318f73a` |
| Finished MP4 | `4fa5666edd5ba07006919a328570d16da8246b558aeeec14880ff44a2990b72c` |
| Original reference sheet | `62c46159d87f29348a35ecb07584d752cf3a15161b19c655968d0da96a42d750` |

`build/la-catrina/independent/accepted-model.json` binds both separate review reports, the 16-view capture receipt and the independent mechanical report to the accepted asset. Reviewer A awarded 8.020/10 and reviewer B 8.115/10. Both inspected the original sheet and all 16 actual native images. This is a narrow static appearance pass. The reports retain pebbled close-up paint grain, coarse ornament, angular trim/panel transitions and simplified cabin or cover details as visible limitations. It is not a claim that the car exactly reproduces the sheet.

## Current verification

- **83 serialized asset checks pass:** 746,922 triangles, 242 mesh draws, 330 nodes and eight embedded images, each within the existing 1024-pixel texture limit. The portable and runtime models match the accepted hash.
- **183 shared CPU physics checks pass** across five vehicles and eight test areas in `build/sessions/20261106-122115-849`. Every one of the previous 137 check rows retains identical pass status, value and threshold; `build/la-catrina/physics-comparison.json` records the comparison.
- **243 loaded rig poses pass** in that same session. The actual GLB preserves fixed-length front arms, rear linkage closure and axle span, engaged rigid hydraulic/damper rods, seated lower spring cups, pin axes, bounded spherical-bearing articulation and rigid driveshaft members.
- **Targeted enclosure sampling passes** against all 972 exported wheel rows / 216 unique transforms, with 25 mm triangle sampling and a 6 mm tyre allowance. The hash-bound result is `build/la-catrina/enclosure-audit.json`.
- **Independent mechanical review passes its stated finite scope:** all 198 tested ram load-path parts connect geometrically to the modeled rails; the revised cover, wheelhouse, arch and tapered tower checks report no sampled intersections. `build/la-catrina/independent/round-11-mechanical.md` and `.json` retain the exact parts, poses, methods and limitations. This is not continuous collision detection, structural validation or manufacturing certification.
- **Six native city captures exit cleanly:** 1,440 displayed frames / 48 seconds, 240 Hz physics and zero discarded backlogs. Each session, original PNG, encoded source clip and telemetry file is bound in `videos/la-catrina-street-show/source-manifest.json` and summarized in `build/la-catrina/native-review.json`.

The 10-second hop shot contains 104 sampled front-pair noncontact frames with both rear tyres supporting: 3.4667 seconds cumulative, at most 0.6333 seconds per continuous interval, with 185 later four-contact recovery samples. Each three-wheel shot retains its intended three loaded tyres for all 240 displayed samples / eight seconds while travelling about 7.60 m. Both sides are filmed from their lifted-wheel side. Opened native samples show takeoff, recovery and visible connected axle/coil/link assemblies; the three-wheel shots are darker in building shade. [MOTION-REVIEW.md](MOTION-REVIEW.md) separates these sampled observations from the telemetry and full-precision records.

## Film verification and sound

The MP4 is 32,505,707 bytes, exactly 48.000 seconds, H.264 at native 960×600 / 30 FPS / 1,440 frames, with 48 kHz stereo AAC. `videos/la-catrina-street-show/proof/delivery-receipt.json` records clean full decoding, no 98%-black interval of at least 0.05 seconds, fast-start layout and 28 sampled frame correspondences to the original native clips. The edit preserves normal speed and the complete source frame, with no upscale, interpolation, replacement vehicle footage or color grade. Detail-camera framing belongs to the native shot itself.

The independent final film review is **PASS WITH LIMITATIONS, with no P0/P1 blocker**. Its reviewer opened all 28 decoded sample PNGs, three review sheets and 16 native PNGs, checked both sides of all five cuts and a complete sampled hop cycle, and independently reproduced all 28 decoded images pixel-for-pixel. `videos/la-catrina-street-show/proof/independent-film-review.md` and `.json` record the result. Darker three-wheel shots reduce fine undercarriage visibility but retain readable lifted wheels and silhouettes. This remains sampled film review, not uninterrupted human playback or audio listening.

The soundtrack combines the project's original Sunset Pulse instrumental with **editorial reconstruction from real recorded engine and lowrider hydraulic sounds**. The native simulator captures are silent. Sound credits, CC0 source pages, source hashes and processing are retained in the film project's `CREDITS.md` and `assets/audio/`. The final mix measures −20.1 LUFS integrated and −5.2 dBTP; these are measured levels, not a human listening review. The film project's `REVIEW.md` collects its delivery evidence and limitations.

## Components, materials and provenance

The original geometry presents a long hardtop coupe, four front lamps, six rear lamps, wire wheels with narrow rubber whitewalls, plum pleated vinyl, a boxed custom X-frame, stamped-channel front arms, a linked live rear axle, four supported hydraulic rams, four separate dampers, a sliding rigid driveshaft and a lined trunk with batteries and two motor/pump assemblies.

[REAL-WORLD-BASIS.md](REAL-WORLD-BASIS.md) records the researched construction sources and the limits of each comparison: Wolf/Crown arms and shock mounts, RideTech axle-location instructions, Hoppo's lowrider equipment and ram families, FK spherical bearings, a FOX damper construction example, Dayton/Truespoke wire wheels, Coker narrow-whitewall tyres, House of Kolor layered candy/flake finishes and PUI vinyl upholstery. Custom frame routing, ram/damper lengths, articulation limits and many mounting dimensions remain authored game choices. Product references do not validate installation, strength or tyre load capacity for a real hopping car.

Bare chrome/alloy, coated steel, rubber, glass, lamp lenses and vinyl use distinct material responses. The clear-coated candy finish combines reference-derived pigment/ornament maps with authored undercoat normal and roughness maps. **Roof, hood and trunk maps contain transformed pixels from the supplied reference; the side-scroll mask is also reference-derived.** [REFERENCE-PAINT.md](REFERENCE-PAINT.md) records source coordinates, color processing and the original hash. Geometry and small vector cameos are original; no external vehicle mesh is embedded. No independent public redistribution license is asserted for the supplied artwork.

## Reuse, scope and safeguards

The portable GLB is self-contained glTF 2.0 in metres, +Y up and +Z forward. It includes separate moving groups and hood/trunk service clips; physical driving and hydraulic motion use the supplied engine adapter. `scripts/catrina_generate.py` and its helpers reproduce the model from the exact reference and geometry-bound cavity cache. Python, NumPy, Pillow and SciPy are required. [MODEL.md](MODEL.md), [RIG.md](RIG.md) and [PHYSICS.md](PHYSICS.md) document the source files, coordinates, mechanics and measurable limits. Archive and fresh-source rebuild verification are tracked separately by `build/la-catrina/delivery-receipt.json` and `source-rebuild.json`; their model hash must match the frozen artifact above before they are used as evidence.

The shared Bullet chassis moves through tyre contact forces; hydraulic commands change effective spring preload. There is no prescribed chassis bounce or airborne hydraulic thrust. Visual links follow fixed-length arcs while the suspension queries remain straight ray footprints. Fluid behavior, unsprung masses, tyre deformation, fatigue, structural strength and measured real-car handling are outside this game model. Human keyboard/controller feel, uninterrupted human playback, listening quality and long-session stability remain unverified.

All native sessions retain 960×600, 30 FPS, one 512-pixel shadow, the 2 GiB job, deadline, heartbeat and sequential mutex. The first film preflight stopped before graphics because a PowerShell disk-space property was unavailable; the direct-volume fallback preserves unknown-space refusal and the minimum free-space check. No higher-resolution or unrestricted graphics acceptance is implied. Earlier first-delivery records remain under `build/la-catrina/initial-delivery-records/`; their 24-second capture and old asset hash are historical. This handoff records local artifacts and makes no external-publication claim.
