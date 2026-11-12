# Independent lighting visual review: r28

November 11, 2026, Pacific. **Disposition: supports retaining the revised early-evening city lighting as a prototype. Independent lighting score: 7.5/10. No remaining P1 was found in the inspected lighting evidence.** The colourful sunset, low warm key, readable shaded surfaces and illuminated street fixtures satisfy the requested approximate 6 PM scene before darkness. Both r27 P1s have actual-image closure. This is a lighting-scope verdict; it does not grant overall Level 2 art approval, production quality or human play acceptance.

This evaluator did not implement the reviewed surfaces, edit runtime/assets or launch an editor/player. Evidence consists of signed-player normal images, matched controls, sampled sequence frames, source and receipts. I did not continuously watch the 69-second proof or listen to audio. The packet's full-decode result is mechanical evidence.

## Exact candidate and review coverage

- Executable independently rehashed: `bbea8c386456dd9c07dd2348c5b2dd23618aa741bdba69dd14088990aead2aa8`.
- Source fingerprint: `baf3a961c9ac75792e9150a4d3c16e9c8ebb8f042252a78be594cb575fe9580e`.
- Inspected SunsetBake, CityEveningLighting, EveningLighting include, Body, City, Grade and View files individually match their source-manifest hashes. The build receipt reports success, zero errors and four warnings. Existing compiler warnings remain unresolved quality debt.
- Exact-player probe receipt reports 204 simulation, 495 loaded-rig and 154 runtime-batch checks passing. These do not substitute for visual review.
- The [final normal packet](../../evidence/cinder-unity-r28/review/packet.json) contains six original stills and a 2,070-frame/69-second, 960 x 600/30 silent clip. All six stills independently match their recorded source/destination hashes; the proof file independently matches its recorded hash. Packet receipts report valid signing and full decode.

I inspected all six packet stills: [garage](../../evidence/cinder-unity-r28/review/01-garage.png), [pause](../../evidence/cinder-unity-r28/review/02-pause.png), [quit](../../evidence/cinder-unity-r28/review/03-quit-confirmation.png), [Catrina stance](../../evidence/cinder-unity-r28/review/04-catrina-three-wheel.png), [Luna lift](../../evidence/cinder-unity-r28/review/05-media-luna-lift.png) and [Nocturne roof](../../evidence/cinder-unity-r28/review/06-nocturne-roof.png). Additional inspected normal evidence includes Catrina frames 540/720, Luna's matched frame 180, Nocturne frame 869, the normal city overview and cockpit, and street-drive frames 0/59/119. These are finite samples, not continuous motion approval.

## Requested time-of-day result

The [normal overview](../../evidence/cinder-unity-r28/20261111-204729-477-Capture/frame-0000.png) shows a peach/rose horizon with lavender/cool upper sky, a warm low-angle key and long car shadows. Shaded brick, tree masses, kerbs and road markings remain readable. The scene reads as daylight fading into evening rather than full night. The street remains navigable between fixture contributions.

The [same-state daylight control](../../evidence/cinder-unity-r28/20261111-205056-911-Capture/frame-0000.png) shares tick 242 and fingerprint `a3f51276e132957a` with the overview. The profile changes sky, key direction, static city shade and reflections together; the result is a substantial scene-direction change from the r25 daylight baseline. The normal garage also carries the warm light and correctly says early evening. The opposite-facing [cockpit view](../../evidence/cinder-unity-r28/20261111-205212-275-Capture/frame-0000.png) has a cooler sky and readable street, consistent with a directional sunset environment rather than a uniform scene tint.

The score reflects a coherent and visible improvement with practical material preservation. It is limited by coarse shadow/occlusion approximations, some flat or pale reflected surfaces, fine highlight aliasing and a city whose simple glazing/foliage/empty gathering spaces still constrain the overall art impression. An art-directed time-of-day profile is not an astronomical claim about a particular date and location at 18:00.

## Actual closure of the rejected r27 findings

### Luna's teal identity and lower-panel detail

The ordinary [r28 matched Luna view](../../evidence/cinder-unity-r28/20261111-204920-549-Capture/frame-0180.png) again reads as dark teal/emerald with an ivory roof, cream tyres and distinct curved fenders. Its door, rear fender and lower flank no longer collapse into the navy/violet family seen in r27. The sampled raised stance at frame 120 retains that identity and exposes readable wheel-well/mechanism separation.

R25, r27 and this r28 frame share tick 362 and fingerprint `89a96fa51296fff4`. The targeted r28 correction capture is pixel-identical to frame 180 of the full normal take. Selected matched paint-region medians demonstrate the change:

| Paint region | r25 RGB | Rejected r27 RGB | r28 RGB |
| --- | --- | --- | --- |
| Door | 33/77/84 | 43/36/63 | 35/62/76 |
| Rear fender | 28/68/71 | 26/20/35 | 25/53/58 |
| Front fender | 7/28/37 | 2/8/15 | 18/49/51 |
| Lower flank | 6/44/51 | 0/9/17 | 25/53/52 |

Region bounds are retained in the [rejected r27 review](LIGHTING-VISUAL-REVIEW-r27.md). The visual judgment is based on actual material identity and form, not unchanged PBR parameters or a global image mean. R28 deliberately changes broad anti-sun/lower-environment radiance toward neutral/cyan while retaining colour toward the sunset. That fixes the reflected palette without repainting Luna.

Nocturne likewise returns to a neutral grey/blue-grey family with a plausible warm hood. Catrina remains rose with visible gold lace, chrome and upholstery divisions during the sampled raised and drive views. The neutral lower environment makes some bumpers and lower paint panels pale; that is a remaining finish issue rather than the r27 identity loss.

### Road overlays receive the car shadow

In the [r28 Catrina three-wheel frame](../../evidence/cinder-unity-r28/20261111-204842-036-Capture/frame-0360.png), the road repair no longer forms the conspicuous bright angular hole within the car shadow. The same correction is present in [Nocturne frame 420](../../evidence/cinder-unity-r28/20261111-204941-030-Capture/frame-0420.png). The repair material remains discernible through its texture, with continuous shadow coverage.

The source now includes `static.repair` and other named road-overlay batches in `RoadReceiver`, alongside `ground.*`; casting remains off. This directly addresses the proven receiver omission from r27 without adding a shadow map. Some selected batches contain mixed geometry by material, so this should be described as the implemented receiver-role policy, not an exhaustive ground-only partition. Contact AO still uses its upward-normal/height gates.

The roof take's frame 420 records phase 1; all 29 retained real graphics roof receipts report success. The inspected roof sequence frames show no newly identified roof silhouette/material failure. Receipt success does not establish every camera angle or distant-LOD canvas appearance.

## Lamps illuminate the street

The matched [lamp-on](../../evidence/cinder-unity-r28/20261111-205023-250-Capture/frame-0000.png) and [light-contribution-off](../../evidence/cinder-unity-r28/20261111-205040-078-Capture/frame-0000.png) pair share tick 242/fingerprint `f9602a28cea82a52`. Fixture emission remains visible with the light contribution off. Turning the contribution on visibly warms nearby pavement, road and facade surfaces. A right-pavement region gains mean RGB about 28/22/11 output bytes, and a right-facade region about 15/12/8; a far-sky region is byte-identical. This demonstrates localized surface illumination independently of a luminous head or sky change.

The source evaluates eight fixed authored heads using distance/cone attenuation, baked static-building visibility and the actual surface's normal/albedo/metalness/smoothness through the Standard PBR BRDF. It executes in the existing base pass. Clearcoat sky IBL is guarded against extra ForwardAdd duplication. These are actual surface-light contributions rather than painted road-pool geometry. Sunset bloom is 0.06 and lamp strength 28.

The pools remain surface-bound in the inspected views. The 4-second [street approach](../../evidence/cinder-unity-r28/20261111-205155-450-Capture/frame-0000.png), sampled at frames 0/59/119, shows the fixtures and road contribution in changing vehicle/camera positions without a visible selection discontinuity in those samples. Continuous stability is not established from those three frames. The cockpit retains steering ring, dashboard/radio and outside-view separation, with no broad bloom veil observed.

## Cost evidence

The paired runs use the same final fingerprint `972aede729b16d4d`:

| Measurement | r25 control, 205113-734 | r28, 205134-194 |
| --- | --- | --- |
| Median | 33.3414 ms | 33.3378 ms |
| p99 | 36.0492 ms | 35.0822 ms |
| Maximum draws | 219 | 219 |
| Active geometry | 693,585 triangles | 693,585 triangles |
| External peak working set | 436,563,968 bytes | 462,155,776 bytes |

The actual [r28 performance receipt](../../evidence/cinder-unity-r28/20261111-205134-194-Benchmark/performance.json) and external runtime receipt show no observed prescribed-budget violation in this 180-frame comparison. The 960 x 600/30, no-MSAA, one-512-shadow and 2 GiB limits remain binding. Internal Unity memory reports zero here and is not used.

The run includes the frame cap and PNG IO. Nearly identical medians, a lower observed p99 and unchanged draw count do not measure the added shader work in isolation or demonstrate spare GPU headroom. Active geometry is not an all-pass submitted-triangle measurement. Target-device/higher-resolution performance remains unverified.

## Remaining P2 and verdict limits

- Dynamic lamp occlusion is approximate. Static building masks do not provide moving-car/bench/tree shadowing; light can remain beneath or through small occluders. Keep this limitation visible and avoid increasing lamp range/strength to make the scene more dramatic.
- Low-resolution long car shadows remain dense/coarse at shallow sun angles. The static city rebake approximates architectural visibility, with interpolation and a floor; it is not complete dynamic dusk GI.
- Bright neutral lower-environment reflections make some chrome/bumper surfaces and Catrina lower panels pale. Fine chrome/lace highlights also remain susceptible to aliasing at the accepted resolution. A later material/lighting finish pass needs matched actual views and continuous motion assessment.
- The corrected garage avoids r26's concentrated white hood hotspot, but specular highlights still move through the sampled driving frames. No claim of zero glare pumping or shimmer follows. The full new profile was not exhaustively sampled with bloom off.
- Four build warnings remain. Glazing, foliage and the district's social/architectural richness still constrain broader city quality.

The evidence supports this early-evening lighting revision at prototype scope with a 7.5/10 lighting assessment. Preserve the rejected r26/r27 evidence and matched controls. Physical input, handling feel, heard audio, comfort, enjoyment, continuous whole-film approval and production readiness remain unverified.
