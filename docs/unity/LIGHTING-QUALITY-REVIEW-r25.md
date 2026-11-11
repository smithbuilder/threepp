# Independent lighting integration review: r25

November 11, 2026, Pacific Time. Reviewer did not implement the contact AO, bloom, display precision, dither, city or car rendering. No player/editor was launched and no implementation file was edited. Assessment uses original player PNGs, matched controls, periodic pose receipts, source bindings and the paired capped test.

## Verdict and scope

**The small r25 lighting refinements preserve the reviewed r24 city/car/UI baseline in the inspected output. No P1 regression is demonstrated. Contact support is correctly gated in the finite recorded samples. Bloom has a real localized dark-cabin spill that remains P2 finish work.**

| Aspect | Current judgment | Reason |
| --- | --- | --- |
| Lighting/rendering | **7.0/10** | Calibrated daylight remains coherent; subtle local contact and highlight treatment, with small bloom halos/spill and unresolved fine specular finish |
| Car presentation | **7.0/10** | Authored palettes, trim, lace, interiors and visible roof stages survive; fine brightwork/glass/canvas readability remains imperfect |
| City/environment | **6.0/10** | Native content/readability preserved; repeated opaque storefronts, coarse foliage and weak gathering-place identity remain |

These are separate aspect judgments, not an average. **The broader Level 2 8/10 presentation threshold remains unmet.** This report supports the limited prototype refinement; it does not grant whole-game art, target-device performance, physical input, listened audio or enjoyment approval. It also does not claim the Windowseat assessment's wider stylised-art program was implemented.

## Exact binding

Player file independently hashed: **`8C662A95E18C2C4BF2A478E7795B72D3FA2927D1D7D3DD9844596D5F427B7AE3`**. Build receipt records Unity 6000.3.6f1, success, zero errors, four warnings, source fingerprint **`6ece4aa5250168c45f204df361b4f0d32f31dfc30bbde9ae3603cd93108c74b7`**. Exact-player probe reports **204 simulation + 495 rig + 154 runtime-batch checks**, success.

Ten inspected files match the r25 source manifest: CinderView, City/Grade/Body shaders, CinderGrade, StandaloneHost, frozen city GLB/material ledger and ambient/sun ledgers. Normal take receipts bind that executable, record normal completion and `lightingControl: none`; matched diagnostic controls are explicitly identified below. The source keeps the native tone transform and FXAA after display encoding, uses a half-precision intermediate, and places static half-byte-bounded dither at final display quantization. Interface rendering follows the world postprocess.

## Actual evidence inspected

All take folders below are under `evidence/cinder-unity-r25/`, prefixed `20261111-` and suffixed `-Capture`.

- Normal garage `074107-197/frame-0000.png`.
- UI `074111-071/frame-0090.png`, plus final packet pause/quit stills.
- Catrina `074130-473/frame-0000.png`, `frame-0360.png`, `frame-0720.png`.
- Luna `074209-487/frame-0180.png`, plus final packet lifted stance.
- Nocturne `074229-898/frame-0300.png`, `frame-0780.png`, `frame-0840.png`, plus final packet roof still.
- Static same-state controls: normal `073934-014`, legacy `073950-835`, bloom-off `074007-654`, contact-off `074024-458`, dither-off `074041-262`, all frame zero. Their pose fingerprints match `a3f51276e132957a`, tick 242.
- Cockpit normal `074358-554/frame-0000.png` and bloom-off `074412-539/frame-0000.png`; additional Catrina three-wheel angle `074429-377/frame-0000.png`.

The unchanged r24 six-still control was reopened earlier in this task. Final r25 packet stills were also inspected where listed. The packet contains a 69-second clip, but this reviewer sampled original sequence PNGs rather than continuously watching it; no continuous-motion acceptance follows.

### Additional actual-r24 same-camera control

Opened `evidence/cinder-unity-r24/20261111-074827-521-Capture/frame-0000.png` and compared it directly with r25 normal `073934-014/frame-0000.png`. Its normal runtime receipt binds the actual r24 executable `7D78C95234B8C21A2F2A48E544EB888F43D52612D0C8680C7D6319128CAA256A`. The r24, r25 normal and r25 legacy pose states are identical, fingerprint `a3f51276e132957a`, tick 242. The actual r24 view confirms preservation of palette, street shading, framing and detail; r25 normal's full-frame mean absolute RGB change is 0.454 byte, maximum 104, with 1,742 pixels exceeding 16 channel bytes.

**r25 legacy is not a byte-exact replacement for the actual r24 control:** it differs at 832 pixels, maximum 30 channel bytes, mean absolute RGB change 0.00135 byte, with three pixels exceeding 16 bytes. Retain that residual build/shader-variant difference as a comparison limit; its individual causes were not isolated here. Do not attribute every actual-r24-to-r25 pixel difference solely to the new effects. Within-r25 single-effect controls remain useful because they hold the candidate build constant. This additional control does not change the scores or localized-bloom finding.

## Contact support and preservation

Across **63 periodic pose receipts** (26 Catrina, eight Luna, 29 Nocturne), all footprint coordinates/weights are finite, weights stay within [0,1], and **every sampled ungrounded wheel has exactly zero added footprint weight**. Catrina samples cover two, three and four supported wheels; for example frame 360 records support `[true,false,true,true]` and weights `[1,0,1,1]`. Luna/Nocturne sample four supported wheels with weights one. Luna raising its body while its tyres remain on the road should not remove tyre contact shading.

The source derives small tread-oriented footprints from actual posed wheel/terrain proximity and applies them to upward-facing city ground, through indirect occlusion, rather than darkening the whole car/street or writing simulation state. Matched normal/contact-off images show a small local change, not an added broad black chassis ellipse: 685 pixels differ, 317 by more than two channel bytes, full-frame mean absolute difference 0.00342 byte. Edge filtering can make individual delta signs mixed; these image deltas are not a direct measurement of occlusion energy.

Observed normal frames retain Catrina's magenta/pale-rose/gold/lace separation, Luna's teal/sage/ivory palette and visible front hardware, Nocturne's blue-black body and burgundy cabin, and visible canvas/deck stages. Existing long static city shade, road/kerb/marking detail and façade divisions remain. Pause/quit darkening is intentional. UI labels, selection bars and controls remain crisp and do not bloom.

Finite receipt support and stills do **not** prove every contact transition is smooth between samples. A future slowly moving tyre/stance review should still check footprint popping/swimming and the interaction with direct shadows.

## Bloom spill: measured and judged

The reported Catrina cabin change reproduces exactly. In normal `073934-014` versus bloom-off `074007-654`, pixel **(496,274)** changes from **RGB (13,2,13)** to **(117,104,95)**: **+104/+102/+82** channel bytes. The bloom adds a small beige-grey spot over a dark purple cabin area beside fine bright trim. The cabin ROI x470–519/y250–299 has mean absolute change 2.20 bytes. Across the whole 960×600 frame, 1,435 pixels differ by more than 16 channel bytes, and 28 by more than 64; frame-wide mean is 0.142 byte.

**P2:** This local spill and the cockpit's softened chrome halos should remain recorded as a tradeoff/finish issue. A tiny frame-average difference does not make it disappear. Conversely, the single worst pixel does not establish a major failure: in the actual normal-size frames, the car palette and upholstery remain readable, most fine detail survives, and the cockpit does not show a broad milky windshield or cabin veil. The result does not warrant P1 from the evidence inspected here.

Recommended finish: reduce the dark-cabin contamination from extremely thin brightwork while retaining a modest light-source/glint halo. Recheck the same upholstery and steering-wheel/dashboard controls after any retune; do not compensate by darkening upholstery or changing the native light calibration. Keep these current controls as evidence.

## Display precision and dither

The matched normal/dither-off control has **maximum one-byte channel difference**, no pixels above two bytes, and mean absolute difference 0.161 byte. The source pattern is screen-anchored and independent of time. No obvious grain or colour shift is visible in the inspected normal output. This supports a bounded dither implementation; it does not prove a perceptually meaningful banding improvement across all sky/dark gradients. Broad matched gradients and a continuous slow camera move would be needed for that stronger claim.

## Paired runtime evidence

The matched 180-frame tests share fingerprint `972aede729b16d4d`, 693,585 active scene triangles and 82 renderers:

| Candidate | Median / p99 ms | Maximum draws | External peak working set |
| --- | --- | --- | --- |
| r24 control `20261111-074313-554-Benchmark` | 33.3342 / 42.4247 | 216 | 436,973,568 bytes |
| r25 `20261111-074334-547-Benchmark` | 33.3425 / 35.1378 | 219 | 426,602,496 bytes |

The extra three draws agree with the added bloom passes. The small median difference and improved sampled p99 do not establish GPU headroom or a speedup: these are noisy, short 960×600/30 fps captures with PNG IO. Internal process-memory counters are zero here; use the external receipts. The triangle value is an active geometry tally, not all-pass GPU submissions. No 1080p/60 or handheld approval is given, and existing guards remain binding.

**Disposition:** limited contact/bloom/display refinement supported with the localized bloom P2 explicitly retained; lighting 7/10, cars 7/10, city 6/10. The original native-content regression remains repaired, while the broader art gate remains below target.
