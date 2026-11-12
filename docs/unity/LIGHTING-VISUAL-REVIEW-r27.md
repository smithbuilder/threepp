# Independent lighting visual review: r27

November 11, 2026, Pacific. **Not approved: two P1 visual defects remain.** The sunset is a substantial art-direction change and r27 improves r26's shaded readability, but Media Luna loses its teal identity and road-repair overlays visibly interrupt the car shadow. A fresh candidate and matched comparisons are required. This is a rejection of inspected actual evidence, not a release-packet approval.

This evaluator did not implement the reviewed surfaces, modify runtime/assets or launch an editor/player. Review used normal signed-player captures, actual r25/r26 references, matched controls, pose receipts, source and a bounded benchmark. Sampled sequence frames are not continuous motion acceptance. The [r26 criteria](LIGHTING-REVIEW-CRITERIA-r26.md) remain applicable.

## Candidate and evidence binding

- Independently rehashed executable: `61ac0e86ba08dbbb2a0d0d58927d21dfe43690a8b5f5fdf2c505c044d8314a9f`.
- Recorded source fingerprint: `9acfc2dd623f56512d551832b300e9163e92ef6215acfb55d1343ccaef88e56e`.
- Normal stills inspected: [garage](../../evidence/cinder-unity-r27/20261111-203548-970-Capture/frame-0000.png), [Catrina close](../../evidence/cinder-unity-r27/20261111-203601-716-Capture/frame-0000.png), [city overview](../../evidence/cinder-unity-r27/20261111-203618-525-Capture/frame-0000.png), [Catrina three-wheel frame 360](../../evidence/cinder-unity-r27/20261111-203750-645-Capture/frame-0360.png), [Catrina drive frame 540](../../evidence/cinder-unity-r27/20261111-203750-645-Capture/frame-0540.png), [Luna frame 0](../../evidence/cinder-unity-r27/20261111-203829-145-Capture/frame-0000.png), [Luna frame 180](../../evidence/cinder-unity-r27/20261111-203829-145-Capture/frame-0180.png), [Nocturne roof frame 420](../../evidence/cinder-unity-r27/20261111-203849-580-Capture/frame-0420.png), [Nocturne frame 869](../../evidence/cinder-unity-r27/20261111-203849-580-Capture/frame-0869.png) and [Nocturne cockpit](../../evidence/cinder-unity-r27/20261111-204029-406-Capture/frame-0000.png).
- Lamp comparison: [on](../../evidence/cinder-unity-r27/20261111-203635-349-Capture/frame-0000.png) / [light contribution off](../../evidence/cinder-unity-r27/20261111-203652-169-Capture/frame-0000.png). Existing head emission remains visible in the latter. These controls demonstrate the illumination contribution independently of merely seeing a luminous fixture.

## P1: Luna palette and lower-panel readability

The actual normal [r25 Luna frame 180](../../evidence/cinder-unity-r25/20261111-074209-487-Capture/frame-0180.png) reads teal/emerald. The matching r27 frame reads navy with violet door/fender areas; the lower flank becomes almost black. Both pose receipts record tick 362 and fingerprint `89a96fa51296fff4`. This is an observed material-identity regression despite preserved material factors. The evening lighting can change a paint's appearance, but it still needs to preserve this vehicle's distinctive family in ordinary play.

The following medians quantify selected matched paint regions, excluding the principal chrome lines. The visual diagnosis does not depend on a whole-frame mean.

| Paint region, image bounds | r25 median RGB | r27 median RGB |
| --- | --- | --- |
| Door, x478-589/y270-309 | 33/77/84 | 43/36/63 |
| Rear fender, x720-774/y330-364 | 28/68/71 | 26/20/35 |
| Front fender, x253-292/y330-364 | 7/28/37 | 2/8/15 |
| Lower flank, x490-614/y365-384 | 6/44/51 | 0/9/17 |

Nocturne also moves from grey-blue to wine/plum with a peach hood, though its cockpit remains readable. Neutral paint can reflect strongly coloured light; the more consequential finding is the convergence of two distinct cars toward the same purple family and Luna's lost green/teal character.

**Cause status:** the new environment is the obvious changed input, but the evidence does not yet isolate reflected sky from diffuse SH/key contributions. `CinderSunsetBake.cs` authors a broad rose horizon, blue lavender and rose-to-muted-purple lower hemisphere. Those are plausible contributors to the direction-dependent reflected tint. A matched Luna reflection-off diagnostic would isolate that hypothesis. More blue diffuse fill alone must not be assumed to repair a reflection-driven palette shift.

**Required correction and validation:** adjust the shared lighting environment's neutral/cool balance, preserving the colourful sunward sky and original donor paint/roughness/metalness. Capture the same normal Luna frame 180 plus an ordinary second angle. The body should read as dark evening teal/emerald with discernible broad gradients, rather than navy/violet or a black lower silhouette. Verify Nocturne and Catrina in the same candidate; do not fix one car by introducing a new all-scene cast.

## P1: repair overlay punches a hole through the car shadow

In Catrina's raised frame 360, a conspicuous bright angular road polygon remains inside the otherwise dark car-shadow region, approximately x360-940/y420-475. A similar mismatch appears in the parked close view and Nocturne's scene. This can look like an ungrounded light pool even though the practical-light implementation uses actual surface BRDF evaluation.

**Source-proven cause:** the frozen city GLB has a `static.repair` node. `CityBlock.hpp::roadPatch` authors irregular eight-sided asphalt overlays at y=0.012. `CinderView.cs` sets every city renderer's `receiveShadows` to whether its name begins `ground.`. Consequently the ground receives the car's directional shadow, while the road overlay cannot receive it. The low evening sun exposes this pre-existing receiver-policy omission over a much larger area.

**Required correction and validation:** allow genuine road-repair overlays to receive the existing shadow, with no extra shadow map and no city shadow-casting expansion. Audit other road overlays by their actual geometry role; shared white/dark material names can include non-road parts and are not a sufficient blanket selection rule. Compare the same parked/raised Catrina and Nocturne frames. The shadow must continue over the repair polygon with its material texture still visible. Keep contact-AO support on road overlays consistent where applicable, without claiming that indirect AO replaces direct shadow receiving.

## Improvements worth retaining

The coloured sky, warm low key and cool shaded side create a recognizably different evening scene at normal gameplay scale. The wide frame remains navigable and reads as sunset before full darkness. The sky retains cloud/colour variation; there is no finding of a uniform orange post-filter or globally clipped sky.

R27's added cool fill produces real local improvements over r26: selected matched Catrina paint regions gain roughly 13/13/16 output bytes, left facade regions about 5/8/8, and a cabin region about 5/3/4. Catrina's lace, trim and body boundaries remain discernible in inspected raised/drive frames. The garage has a less concentrated white hood hotspot than the r26 menu, and its time-of-day text correctly says early evening. These improvements do not establish Luna preservation.

The lamp-on/off pair visibly changes actual pavement and nearby brick while fixture emission remains on. `CinderEveningLighting.cginc` evaluates a bounded distance/cone attenuation and Standard PBR BRDF with actual surface normal/material inputs. It is not a road decal or a flat emissive addition. Lamp strength is reduced to 28 in r27, and sunset bloom remains 0.06. Static building visibility is baked; dynamic lamp occlusion remains approximate. There is no claim of physically correct blocking under a moving car or by every small prop.

The Nocturne cockpit retains steering-ring, dashboard/radio and outside-view separation in the supplied normal frame. No broad bloom veil was observed there. A full new bloom-off set and continuous motion inspection remain appropriate after the two P1 corrections.

## Bounded cost evidence

The [r27 benchmark](../../evidence/cinder-unity-r27/20261111-203952-147-Benchmark/performance.json) records 180 frames, median 33.3396 ms, p99 34.6260 ms, maximum 219 draws and 693,585 active geometry triangles. Its fingerprint is `972aede729b16d4d`; the external runtime receipt records peak working set 462,172,160 bytes and normal completion. These are within the prescribed observed limits in this short run. Internal Unity memory is zero and is not substituted for the external measurement.

This capped 960 x 600/30 PNG-IO run does not isolate the eight lamp evaluations' GPU cost, prove spare headroom or establish target-device readiness. Preserve no MSAA, one 512 shadow, <300 draws, <700,000 active geometry and the 2 GiB job. Source fixes and successful probes cannot close the two actual visual defects without fresh signed-player evidence.
