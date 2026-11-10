# Independent car review — r20

November 9, 2026, Pacific Time. Independent automotive visual evaluator. No implementation, asset edits, editor/player launches or changes to prior failed packets. Original player PNGs were opened directly; this report's only new file is this document.

## Correction after final roof inspection — r20 rejected

**The no-P1 and prototype-checkpoint conclusion below is withdrawn.** The evaluator opened roof-cycle frame 0420 and native `roof-up.png` but failed to identify incomplete canopy rendering at the fully raised state. Describing that frame as roof-up validation was an error: `roofPhase == 1.0` proves the requested pose, not that opaque canvas is actually drawn. The original report is preserved below as the failed review record.

Reinspection found a missing native runtime rule: `showcase/NocturneRig.hpp:59` forces canvas materials to `Side::Double` after GLB load. R20 retained single-sided canvas. The new matched old-player side capture `evidence/cinder-unity-r20/20261109-232527-188-Capture/frame-0000.png`, compared with the normal and cloth-hidden r24 controls, supports **partial canvas culling**, not complete absence of every roof component. Native `docs/nocturne/review/native/roof-up.png` clearly has the full opaque canopy. R20's mechanism/vertex tests did not prove rasterized coverage.

The shared diagnostic `evidence/cinder-unity-r24/roof-coverage-comparison.json` uses 4,267 canopy/glazing ROI pixels derived from the unchanged-geometry magenta control. Old r20 differs from the hidden-cloth control in only 40.47% of those pixels, with median maximum-channel difference 0 bytes; r24 differs in 99.67%, median 60 bytes. This supports the visual diagnosis but is not triangle-level opacity proof; the diagnostic explicitly includes glazing/lighting effects.

R20 therefore has a P1 Nocturne roof-preservation defect. Its Nocturne 7/10 complete-presentation judgment and no-P1 support for publication are invalidated. The body-reflection improvement and Catrina/Luna fix observations remain valid within their original scopes. R20 remains rejected and its packet must be retained; newer bytes require their own review. See `CARS-REVIEW-r24.md` for the later independent evaluation when available.

## Verdict

**The specific car-presentation P1 defects found in r16/r17 are resolved in the inspected r20 evidence.** Luna retains its green/sage palette from the rear chase angle. Catrina's right-three-wheel view keeps the whole car visible. Nocturne now has the broad blue-gray reflected gradient needed to read its dark flank. The cars' distinct identities and much of their native visual character are restored.

**No remaining car P1 was observed within this finite review scope.** This is not an assertion that every frame, camera angle, mechanical clearance or target device has been tested. It is also not an overall project, gauntlet-level or paid-release approval. City quality, physical input, handling feel, heard audio and enjoyment remain separate judgments.

## Absolute quality versus native-relative restoration

| Car | Absolute presentation quality / 10 | Native-relative restoration judgment |
| --- | --- | --- |
| La Catrina | **7.0** | **Mostly restored.** Rose upper paint, pale lower panels, gold ornament, lace, wire wheels and burgundy cabin are visibly identifiable. Both three-wheel poses and the actual hop retain the car's identity and framing. Finish/highlight texture and fine brightwork are still coarser than ideal. |
| Media Luna | **7.0** | **Mostly restored, with source-version confound.** Green curved shell, pale sage roof/trunk, ivory whitewall and warm seats survive front, rear and raised views. The broad dark-body/gray-cabin collapse of r9 and rear blackout of r16 are absent. Exact same-asset parity cannot be claimed because the native receipt and frozen port source differ. |
| Nocturne | **7.0** | **Materially restored from r17 and broadly consistent with the native street character.** Large panels now have a useful gradient rather than a uniformly dark silhouette outlined by chrome. Black/blue-black lacquer, grille, wheels, glazing and visible burgundy interior remain recognizable. Reflection shape and cabin coverage still differ from the native reference. |

The numerical scores describe **absolute visible car-presentation quality**. The restoration column is a separate preservation judgment, not a numerical score chosen to satisfy a threshold. Native work itself is stylized prototype art. Recovering that character does not automatically make the result an 8/10 product, photoreal rendering or release-ready game. These cars are appealing, individually authored prototypes with residual finish/readability limitations.

## Exact player and reviewed evidence

Player SHA256: `59E549C1B31425C704DC2F035273628C016F4E0DAC17B74BC9E418F3CB624347`.

Supplied source fingerprint: `abce083872686ce28a7fc4b59ff766a9fda616fdf1d1e39d7d9beb9042792f4d`. The coordinator reports 204 + 495 + 148 probe checks PASS. I did not rerun those tests or independently recalculate the complete source fingerprint. They are technical provenance, not the basis of the visual verdict.

All sessions below are under `evidence/cinder-unity-r20/`. I read all nine session runtime receipts: each reports the player SHA above and normal completion. Their `material-control.json` values are `control: none`; these are the normal presentation, not the Standard/neutral/other diagnostic overrides elsewhere in the directory.

| Session | Captured frame count | Original frames opened |
| --- | --- | --- |
| `20261109-223334-186-Capture` | 1 | 0000 — Nocturne street |
| `20261109-223346-926-Capture` | 1 | 0000 — Catrina menu |
| `20261109-223613-062-Capture` | 1 | 0000 — overview, context only |
| `20261109-223615-943-Capture` | 1 | 0000 — Nocturne forward cockpit |
| `20261109-223628-707-Capture` | 1 | 0000 — Catrina wheel/trim/lace detail |
| `20261109-223641-498-Capture` | 180 | 0030, 0120 — Luna rear chase and front menu within input flow |
| `20261109-223700-925-Capture` | 780 | 0000, 0060, 0120, 0240, 0360, 0540, 0779 — Catrina low, actual hop, both three-wheel states, drive and end/reverse |
| `20261109-223739-453-Capture` | 240 | 0000, 0120, 0239 — Luna lower, front hold/lift, lowered end |
| `20261109-223759-931-Capture` | 870 | 0000, 0150, 0300, 0420, 0450, 0600, 0750, 0869 — Nocturne open, intermediate roof states, roof-up and open end |

Catrina frame 0060 was selected from the pose receipts as the highest body Y within `Mode == 1` (front hop), rather than mislabeled from a three-wheel maximum. Nocturne frame 0420 has `roofPhase == 1.0`. These state records select useful actual images; they do not replace visual inspection.

During this r20 review I reopened these native originals:

- `docs/nocturne/review/native/street-cruise.png`, `hero.png`, `roof-up.png`, `cabin.png`.
- `docs/la-catrina/review/studio/front.png`, `wheel-detail.png`.
- `docs/media-luna/review/native/street-raised.png`.

The earlier independent reviews also inspected the same native side, rear, trim and cabin sets, as documented in their preserved reports. The r20 conclusions use both the reopened originals and the specific reproduced r16/r17 failure states.

All displayed captures are 960 x 600, but cameras, lighting direction, feature coverage and pose are not perfectly matched. The coordinating source audit previously found Catrina `8444aca...` and Nocturne `130a882...` matched their native receipts. Luna's frozen source `8aa58c...` differs from native receipt `66e3ef50...`; retain that confound in any exact parity claim.

## Resolution of the earlier defects

### Nocturne flank form — prior P1 resolved in these views

R17's normal street frame was a nearly uniform dark door/rear flank surrounded by bright trim. R20 `223334-186/frame-0000.png` has a broad blue-gray gradient across the side and a readable upper shoulder. It remains a dark car. Native `street-cruise.png` uses the same general cool charcoal/blue-black family and broad value structure; native studio `hero.png` is much blacker but also models the side with a soft band.

The new view addresses the actual requested defect. It is not useful to keep calling it the same P1 merely because the specular shape is not identical. R20 roof-sequence samples preserve the body form as panels move. The cool large sky reflection on the hood is stylized and could be refined, but it no longer erases the car's form or palette.

The coordinator attributes the change to corrected reflection intensity encoding and linear-light handling. That cause was not implemented by this evaluator; the independently supported claim is the visible before/after result. Rendering control probes belong in the technical/lighting report.

### Luna rear blackout — fix retained on the final bytes

`223641-498/frame-0030.png` has a pale sage roof/trunk and green rear fenders. The r16 near-black roof/body failure is absent. The front menu frame and the complete lift take's opened start/hold/end images keep the green/sage/ivory/warm-interior hierarchy. Native `street-raised.png` and the r20 lift both show a rounded green car, readable chrome, distinct whitewall and visible linkage in the front wheel opening.

### Catrina framing and identity — fix retained through signature states

`223700-925/frame-0360.png` shows the complete car, road, decorated hood and right-three-wheel stance. R16's unusable underside/world-loss frame is not reproduced. Frame 0240 presents the opposite three-wheel state; 0060 is an actual front hop with separated front tire/road and readable suspension space. No claim of physics feel or continuous clearance follows from those images.

The rose/pink separation, gold ornament, lace and ribbed burgundy cabin remain visible across the samples. The close wheel image confirms spoke geometry, rim fasteners, whitewall, side ornament and fine continuous trim. It is shadowed and framed differently from the native studio closeup, so it cannot prove an exact paint-color match. It does prove that the fine authored features are visibly present in the player.

## Remaining P2 finish and review limitations

1. **Fine brightwork remains busy.** Wire spokes and very thin trims still contain bright granular pixels at this profile. Native has some aliasing too. The long chrome bands are substantially quieter than r9/r12, and the closeup has real readable construction. This is a stability/polish issue, not the previous blanket P1 chrome failure.
2. **Paint and reflections are not fully matched.** Catrina's lower pink is brighter in the r20 street light than in native studio, its highlight texture can look coarse, and Nocturne's large sky reflection can look simple. Different lighting is a major confound. Retain controlled equal-scale material/reflection tests before changing donor colors or removing intended candy flake.
3. **Interior preservation is only partly showcased.** Nocturne's forward cockpit shows steering, instrument cluster, wood/dash band and transparent glazing. The exterior roof take shows burgundy seating. It does not match native `cabin.png`'s elevated bench/belt/door-trim view, so exhaustive interior fidelity is unproven. There is no visible evidence here that the interior was deleted.
4. **Contact is useful, still stylized.** Tires, raised wheels and underbody mass now read against the road. Very dark cavities and broad soft shadows can still merge details. These are finite sampled poses, not continuous mechanical or shadow validation.
5. **Temporal appearance remains limited evidence.** The takes were complete on disk and samples across all requested sequences were visually inspected. I did not watch all 2,070 frames in real time. The report does not certify the absence of shimmer, every intermediate roof overlap, comfort or smoothness. Human handling/audio/performance acceptance remains separate.

## Conclusion

The car-specific restoration objective has made substantial, evidence-backed progress. **Within the inspected normal r20 car captures, the previously identified P1 defects are fixed and no new P1 is observed.** Absolute quality remains about **7/10**, with the P2 work above. This supports a clearly labeled prototype checkpoint and a preserved comparison packet. It does not confer an overall level pass, complete pixel parity, 8/10 quality, human acceptance or paid-release approval, and future player bytes require their own evidence.
