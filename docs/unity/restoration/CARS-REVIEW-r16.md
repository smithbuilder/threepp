# Independent car review — r16

November 9, 2026, Pacific Time. Independent visual evaluator; no implementation or player/editor launch. Existing original PNG captures were inspected directly. This report evaluates r16 only and preserves the failed r9/r12 reports.

## Verdict and scores

**R16 substantially restores the cars' identity, but the full inspected presentation still has P1 failures.** Catrina's rose/lace/two-tone finish, Luna's sage/green/ivory palette and much of their fine modeling survive clearly. Trim is quieter and more continuous than r12. Parked street views have convincing ground contact. This is real progress, rather than a conclusion drawn from shader changes or test counts.

The wider capture packet exposes problems that the parked front-side views hide: Luna becomes almost black from the rear chase angle, including its pale roof, and Catrina's right-three-wheel take contains a frame where the car/world presentation disappears behind a black underside-like view. Nocturne's broad dark side still lacks the native car's useful reflected gradient.

| Car | Absolute presentation score / 10 | Native-relative assessment |
| --- | --- | --- |
| La Catrina | **6.0** | Strong recovery of identity, paint separation, lace and modeled detail; quieter chrome. The car finish in the parked street view alone is around 7, but the assessed presentation includes the failed right-three-wheel camera image. Native-relative finish is much closer, not yet demonstrated equivalent through the full intended action. |
| Media Luna | **5.5** | Front-side street palette, fender form, whitewall and cabin are much improved. The rear chase blackout is a major loss of authored identity in an ordinary driving view. Source-version and lighting differences limit an exact native parity claim, but do not make the blackout acceptable. |
| Nocturne | **6.0** | Silhouette, grille, wire wheels, glazing, dashboard and visible burgundy seating survive. Large flank is still too uniform/dark compared with native street and studio views; finish reads less deliberately modeled by reflected light. |

Scores are subjective absolute judgments of **all inspected car-presentation evidence**, not geometric fidelity metrics, a paid-release score, or targets to satisfy. The supplementary evidence lowers Catrina/Luna from what their parked street frames alone would merit. No average score overrides a P1. Native itself is stylized prototype art, not a photoreal gold standard.

## Evidence binding and scope

The supplied signed player SHA256 is `313F2FF325126FCF747837DA3273727D2BE9A383F2903F4D22BC7BEFD9F9ED49`. I checked this value in the runtime receipts for the menu, three street stills, overview, Nocturne cockpit, Catrina wheel detail, input flow and Catrina culture capture. Probe counts 204 + 495 + 124 PASS were supplied by the coordinator; I did not rerun them, and they are not visual acceptance evidence.

All session paths below are under `evidence/cinder-unity-r16/` and all listed images were opened individually:

| Session | Frames inspected | Purpose |
| --- | --- | --- |
| `20261109-215203-580-Capture` | 0000 | Catrina menu |
| `20261109-215216-323-Capture` | 0000 | Catrina street |
| `20261109-215229-068-Capture` | 0000 | Luna street |
| `20261109-215241-800-Capture` | 0000 | Nocturne street |
| `20261109-215255-343-Capture` | 0000 | City overview/vehicle context |
| `20261109-215335-370-Capture` | 0000 | Nocturne forward cockpit |
| `20261109-215338-275-Capture` | 0000 | Catrina rear wheel/side trim close view |
| `20261109-215351-066-Capture` | 0000, 0030, 0060, 0090, 0120, 0148 | Input/menu flow; rear chase Luna at frame 0030 |
| `20261109-215410-479-Capture` | 0000, 0120, 0240, 0360, 0540, 0720 | Catrina culture/driving sequence |
| `20261109-215448-942-Capture` | 0000, 0120, 0239 | Luna lower/lift/lower |
| `20261109-215509-400-Capture` | 0000, 0300 | Nocturne open/roof intermediate |

Native references reopened during this review:

- `docs/la-catrina/review/studio/side.png`, `front-detail.png`.
- `docs/media-luna/review/native/street-cruise.png`, `rear-quarter.png`, `rear.png`.
- `docs/nocturne/review/native/street-cruise.png`, `hero.png`, `cabin.png`.

Previous review of this lane also opened native Catrina wheel/cabin and Luna cabin detail; this verdict's direct comparison uses the reopened originals above. The coordinating source audit previously found Catrina `8444aca...` and Nocturne `130a882...` matched native review receipts. Luna frozen `8aa58c...` differs from native receipt `66e3ef50...`, so its pair has an asset-version confound. All main images are 960 x 600, but lighting, camera direction, body orientation and feature pixel coverage are not perfectly matched.

This is sampled still-sequence inspection. It does not establish full real-time temporal stability, handling feel, audio, physical device behavior, target-device performance or exhaustive mechanical clearance. A capture still in progress was not treated as a complete reviewed movie.

## What is demonstrably restored

**Catrina:** saturated rose upper paint and pale rose lower panels read separately; the native-like color design returns. Hood/roof lace, the gold side ornament, medallion, wire construction and fasteners are visibly present. The wheel/side-trim close view shows continuous metal bands and real spoke geometry, so the residual bright pixels do not justify a claim that detail was deleted or all chrome remains broken. The close view is deeply shadowed and cannot be used as a matched paint-color test against the native studio wheel view. The left-three-wheel frame 0240 is visually clear and substantially better grounded than r9.

**Luna:** sage roof/frame, deep green shell, ivory whitewall, warm seats and curved fenders are distinct in the street/lift views. Front lift frame 0120 exposes the suspension and retains readable wheel/body separation. Cabin glass transmits interior features without r9's uniform gray block. These improvements survive the lowered and lifted front-side views.

**Nocturne:** black/blue-black identity is appropriate; raising its whole albedo to gray would not establish better fidelity. Metal has more convincing dark/light range than r9. The forward cockpit shows dashboard, wood band, instruments, steering and clear glazing; there is no basis here to claim missing interior meshes. Burgundy bench color is visible from outside, but the packet has no native-matched elevated seat/ribbing/belt view.

## Remaining P1 findings

1. **Luna loses its palette in the ordinary rear chase view.** `20261109-215351-066-Capture/frame-0030.png` shows almost black body and roof, while street/lift/menu front views show green and pale sage. The pale roof becoming black is stronger evidence than a subjective preference for brighter dark paint. Native rear/rear-quarter references retain the pale roof/trunk and distinguishable green sides. Those native images are studio views, so this is not a calibrated renderer comparison; nevertheless the player view fails to communicate the authored palette. Diagnose with opposite-side neutral/exposure controls and check normals/lighting/reflection/material response rather than assuming a specific cause. The report does not assert which of those is wrong.

2. **Catrina's right-three-wheel capture loses useful world/car presentation.** `20261109-215410-479-Capture/frame-0360.png` is dominated by black underside-like texture and a pale gray lower band, with the car absent and the HUD still naming right three-wheel. The exact camera cause is unverified; the observed result is a P1 presentation failure. A finite pose/probe pass does not address it. Frame 0240 of the same take demonstrates the left-three-wheel pose can be presented clearly.

3. **Nocturne's broad flank lacks readable reflected form.** `20261109-215241-800-Capture/frame-0000.png` presents a nearly uniform dark door/rear quarter bounded by bright trim. Native `street-cruise.png` has a broad charcoal gradient and shoulder separation; even native black studio `hero.png` uses a long soft reflection to model the side. Black paint itself is not the defect. The useful large-scale reflection/value structure is absent in this selected street presentation. Different camera/light direction is a confound, so establish a matched reflected-band test before changing paint values.

## Remaining P2 and limits

- Wire wheels and very thin trims still have bright granular pixels, but the close Catrina view shows meaningful improvement. This is now a polish/stability question rather than a blanket P1 chrome failure. A controlled slow camera move is needed to assess shimmer; these sampled stills cannot certify its absence.
- Catrina still has a somewhat coarse/mottled highlight texture. Native also has textured candy paint. Judge equal-size paint/coat samples before removing intended flake or making it mirror smooth.
- Contact is stronger than r9 but very dark underbody shadows can merge cavities and tires. Lift views are readable; a full moving sequence should preserve that distinction through both sides and turns.
- Nocturne's visible seats are not a complete interior review. The forward cockpit cannot verify the bench ribbing, belts and door furniture shown in native `cabin.png`.

## Required next evidence

Keep this r16 packet. Fix and recapture the Luna rear chase blackout and Catrina right-three-wheel camera result using the same reproduction states. Show Nocturne's broad reflected side form under a controlled comparable environment. Retain all three parked street views, Catrina detail, Luna lift and cockpit comparisons after any renderer/batching change. Bind new images to their own final player bytes; these r16 results approve no future revision.

**Conclusion: meaningful restoration, incomplete native-relative fidelity, P1 remains.** A revised final acceptance claim is not supported by this complete inspected packet.
