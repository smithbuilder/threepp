# Independent car review — r17

November 9, 2026, Pacific Time. Independent evaluator; no runtime/source edits or editor/player launch. The r16 failed report and captures remain preserved.

## Scoped verdict

**R17 visibly fixes the two concrete r16 failures in Luna's rear chase view and Catrina's right-three-wheel camera.** The rose/lace Catrina and sage/green Luna again communicate their authored identities from the tested views. This is demonstrated by the actual new images, rather than inferred from the source fix or probe totals.

**Native-relative restoration remains incomplete for Nocturne.** Its large side panels still lack the broad reflected gradient/form seen in the native reference. This is the remaining P1 in the current car-presentation review. It does not negate the completed fixes, and it does not make the native baseline photoreal or production finished.

| Car | Absolute presentation score / 10 | Current assessment |
| --- | --- | --- |
| La Catrina | **7.0** | Recognizable rich rose/two-tone finish, lace, ornament, real wire detail and readable signature stances. The previous camera failure is repaired in the reproduced frame. Surface/highlight texture and tiny brightwork remain somewhat coarse. |
| Media Luna | **7.0** | Sage roof/trunk, green fenders and warm cabin survive the previously broken rear chase angle as well as the menu front angle. The blanket blackout is repaired. Lower body remains darker/flatter than the native street reference under unmatched lighting. |
| Nocturne | **6.0** | Long black convertible identity, trim, wheels and visible interior survive. Broad side still reads as a near-uniform dark slab and needs a more useful reflection/value structure. |

These are subjective **absolute car-presentation** scores, not a pass target, an average to override defects, or paid-release approval. A label of reviewable prototype can accurately coexist with these limitations. The evidence does not justify an 8/10 or native-equivalent presentation claim across all three cars.

## Exact evidence and limits

Player SHA256: `20974CF14E1AEEE20631736FF1AE5FC67218745EB17E4C7D4E65BDC6FCF093D5`. Supplied source prefix: `1bb23f5...`. The coordinator reports 204 + 495 + 148 runtime probe checks PASS; I did not rerun them. Image judgment remains independent of those technical results.

Under `evidence/cinder-unity-r17/`, original PNGs individually opened for this completed scoped review:

| Session | Frames | Purpose |
| --- | --- | --- |
| `20261109-220327-600-Capture` | 0030, 0120 | Luna rear chase reproduction and front menu |
| `20261109-220347-049-Capture` | 0000 | Nocturne normal custom-material street view |
| `20261109-220359-766-Capture` | 0000 | Nocturne Standard-material diagnostic control |
| `20261109-220412-487-Capture` | 0000, 0180, 0240, 0360, 0480, 0600, 0779 | Complete 780-frame Catrina take, sampled at poses/driving/end |

Runtime receipts for all four listed sessions match the supplied SHA and report normal completion. The Nocturne control has a separate `material-control.json` describing its diagnostic material override; it is not a shipping-art acceptance image. Full probe/byte-binding validation belongs to the coordinator's technical packet.

Comparisons use native originals inspected in this independent lane: Catrina `docs/la-catrina/review/studio/side.png`, `front-detail.png`; Luna `docs/media-luna/review/native/street-cruise.png`, `rear-quarter.png`, `rear.png`; Nocturne `docs/nocturne/review/native/street-cruise.png`, `hero.png`, `cabin.png`. Cameras, light directions and feature pixel coverage differ. Catrina and Nocturne frozen sources previously matched native review receipts; Luna frozen `8aa58c...` differs from native receipt `66e3ef50...`, retaining a source-version confound.

This is sampled sequence inspection at 960 x 600. It is not a claim to have watched every frame in real time. Fine temporal shimmer, human controls/audio/enjoyment and target-device performance remain outside this evidence. The coordinator intentionally did not run further r17 Luna/Nocturne motion sessions while the Nocturne P1 remained open. Fresh r17 lift/roof/interior motion is therefore **UNVERIFIED**, not a pending review that can be assumed passed. This report is complete for the actual captured scope.

## Verified repairs

### Luna rear palette blackout — fixed in the reproduced view

R16 `20261109-215351-066-Capture/frame-0030.png` reduced the pale roof/trunk and green fenders almost to black. R17 `20261109-220327-600-Capture/frame-0030.png` clearly shows pale sage roof/trunk, green rear fenders, readable cabin and coherent chrome. This is a strong same-sequence visual correction. The frame no longer fails to communicate the two-tone design. The frame-0120 menu retains the front-side green/sage/ivory/warm-seat hierarchy.

The coordinator attributes this to writing the surface normal for the shader variant without a normal map. I did not implement that code; the diagnostic cause is reported provenance. The visible correction itself is independently confirmed.

### Catrina right-three-wheel camera loss — fixed in the reproduced frame

R16 `20261109-215410-479-Capture/frame-0360.png` was an unusable black underside-like view with no car. R17 `20261109-220412-487-Capture/frame-0360.png` presents the entire car, street, decorated hood and right-three-wheel stance. The car remains clearly framed rather than disappearing below the world. Samples 0180/0240 show the left stance; 0480/0600/0779 preserve the street/car framing through driving and reverse.

The repaired low view is visually useful because it also displays the lace and brightwork. This confirms the specific failure state is repaired; it does not establish arbitrary camera/terrain collision coverage or subjective ride acceptance.

## Remaining P1: Nocturne broad side form

The normal r17 street still (`220347-049/frame-0000.png`) is much better than the rejected r9 city/car presentation overall, but Nocturne's doors and rear flank remain nearly uniform dark panels bounded by bright trim. Native street `street-cruise.png` has a large soft charcoal gradient and readable upper shoulder; the very dark native studio `hero.png` also contains a long reflected band that models the side. The black paint is appropriate. Its failure to show useful large-scale reflected form in this selected street presentation is the defect.

The Standard-material diagnostic (`220359-766/frame-0000.png`) is even darker/flatter. It does **not** show that substituting Standard repairs the problem, and it does not isolate every variable: the control itself says Standard removes custom coat/GI/surface behavior and does not consume donor vertex color. The comparison weakens the hypothesis that the custom clearcoat alone causes the weak side form. Environment/reflection/light/camera/material interaction remains the useful diagnosis area; this review does not assert one root cause.

A controlled native-relative reflection test should show a broad side gradient while retaining black identity, then verify it in ordinary street views and rotations. Raising all black albedo until the car becomes gray or choosing a single flattering beauty angle would not establish that.

## Remaining P2

- Catrina's candy-highlight texture and tiny spokes/trim are still coarse at this profile. R16 closeups already showed real lace, fasteners and wire geometry; the restoration is no longer accurately described as deleted detail or universally broken chrome. A slow pan is still needed for temporal stability.
- Luna lower door/rear skirt remain relatively dark against its native street reference. It is a subtler issue than the now-fixed rear blackout, with lighting and source-version confounds.
- Nocturne burgundy seat color and forward cockpit are visible in the existing r16 packet, but a useful elevated bench/ribbing/belt view is still required before declaring complete interior preservation. R17's different player bytes do not inherit a fresh interior verdict automatically.
- Parked/lift contact reads better than r9; very dark underbody shadows can still merge cavities and rubber. Preserve loaded/lifted wheel separation through camera changes.

## Acceptance boundary

Two reproduced P1 defects are repaired. One native-relative car-presentation P1 remains. **This supports a candid restored prototype checkpoint with limitations, not complete visual restoration or paid-release approval.** No future build inherits this judgment; any further renderer/batching change needs its own bound images and reproduced states.
