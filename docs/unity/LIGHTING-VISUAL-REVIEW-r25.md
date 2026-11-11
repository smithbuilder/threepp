# Independent lighting visual review: r25

November 11, 2026, Pacific Time. This evaluator did not implement the reviewed surfaces. Review used actual signed-player captures, matched effect controls, pose/runtime receipts, source and the retained r24 reference. No editor/player launch or source/asset edit was performed by the evaluator.

**Disposition: scoped visual retention supported, with no new P1 requiring a retune in the inspected evidence. Absolute lighting quality remains 7.0/10.** Contact shading is small and localized. Dither is visually negligible. Bloom adds noticeable highlight spill in a few dark cabin pixels, but the supplied matched cockpit and exterior views retain the relevant forms and detail. This supports the bounded implementation, not a large visual-quality upgrade, an 8/10 overall-art claim or production readiness.

## Candidate binding

- Candidate: `cinder-unity-r25`, Unity 6000.3.6f1, Built-in forward, Linear, D3D11.
- Executable independently rehashed: `8c662a95e18c2c4bf2a478e7795b72d3fa2927d1d7d3dd9844596d5f427b7ae3`.
- Build source fingerprint: `6ece4aa5250168c45f204df361b4f0d32f31dfc30bbde9ae3603cd93108c74b7`.
- Inspected Host, Body, City, Grade and View source files individually match the candidate source manifest.
- Selected build receipt reports success, zero errors and four warnings. Existing potentially-uninitialized Body/FXAA diagnostics are not a warning-free build.
- Exact-player probe receipt reports 204 simulation, 495 loaded-rig and 154 runtime-batch checks passing. The visual verdict comes from pixels and matched controls, not those checks.
- The final [review packet](../../evidence/cinder-unity-r25/review/packet.json) binds six original stills, source captures, pose/replay records and a 69-second proof clip to this executable. I inspected the six stills and sampled source-sequence frames. I did not continuously watch all 2,070 proof frames or listen to audio. The packager's full-decode result is separate mechanical evidence.

## Matched controls

All five initial controls use Catrina, camera 1, 120 warmup frames and one retained frame. The recorded tick is 242 and fingerprint is `a3f51276e132957a` in every case. Their pre-grade centre RGB is identical. Runtime receipts identify the candidate executable, and the recorded lighting-control flags distinguish the experiments.

| Control | Actual frame |
| --- | --- |
| Normal | [073934-014](../../evidence/cinder-unity-r25/20261111-073934-014-Capture/frame-0000.png) |
| Legacy features off | [073950-835](../../evidence/cinder-unity-r25/20261111-073950-835-Capture/frame-0000.png) |
| Bloom off | [074007-654](../../evidence/cinder-unity-r25/20261111-074007-654-Capture/frame-0000.png) |
| Contact off | [074024-458](../../evidence/cinder-unity-r25/20261111-074024-458-Capture/frame-0000.png) |
| Dither off | [074041-262](../../evidence/cinder-unity-r25/20261111-074041-262-Capture/frame-0000.png) |

The legacy control disables the new features and restores the older display-buffer precision within r25. It is not byte-identical to the older executable.

I also inspected the [actual r24 player reference](../../evidence/cinder-unity-r24/20261111-074827-521-Capture/frame-0000.png), whose receipt binds executable SHA `7D78C95234B8C21A2F2A48E544EB888F43D52612D0C8680C7D6319128CAA256A`. Its camera/preset, tick 242 and fingerprint `a3f51276e132957a` match r25 normal. R25 retains its paint, lace, chrome, seat shapes and city readability in this direct comparison. The normal r25 image differs by more than three bytes in 11,003 pixels, with maximum 104 bytes and mean absolute channel difference 0.454 bytes. Many additional one-byte changes accompany precision/dither; those totals do not describe a broad washout.

R25 legacy versus actual r24 differs at 832 pixels at any magnitude, only 36 pixels above three bytes, maximum 30 bytes. Those larger differences fall in the background region x517-840, y62-253. The City shader's unconditional normal assignment is a plausible contributor to this small baseline difference, but this image pair does not isolate its cause. Effect-specific claims below therefore use matched controls within the same r25 executable. The performance control below also uses actual r24.

### Contact shading

Normal versus contact-off changes more than three bytes in 242 pixels, confined to the tyre/road region at image bounds x296-714, y378-440. Maximum local difference is 23 bytes and the changes are overwhelmingly darkening. This matches the intended small contact footprint; no broad oval or body-wide darkening was observed.

The implementation attenuates indirect light through City material occlusion, preserving the existing direct shadow and frozen native vertex shade. Only ground renderers receive its property block. Four posed tread/support samples drive the footprints; it does not write simulation state.

The [matched three-wheel normal](../../evidence/cinder-unity-r25/20261111-074429-377-Capture/frame-0000.png) and [contact-off control](../../evidence/cinder-unity-r25/20261111-074451-893-Capture/frame-0000.png) share fingerprint `053ee947b75fc00b`. Their recorded first wheel is unsupported and its footprint weight is zero. In the full Catrina take, frame 360 likewise records an unsupported second wheel with zero weight. The parked and raised-wheel views show no persistent contact spot under an unsupported tyre. This is finite observed support behavior, not exhaustive terrain/curb acceptance.

The gain is modest. It helps anchoring at the tread rather than supplying a new shadow system. Do not increase it into a general black undercar blob.

### Bloom and material retention

Bloom is extracted from scene-linear HDR with a soft knee and hue-preserving scalar radiance bound, using half/quarter-resolution targets. Three extra blits produce the glow, which is added before the existing NativeTone transform. Existing display-space FXAA remains after tone mapping. Sun, SH, reflection units and donor paint parameters were not retuned to make bloom appear.

There is no observed global washout. In the first matched pair, sampled ordinary wall and road regions are unchanged by bloom. Rose paint planes, gold lace, chrome strips and the green/blue vehicle identities remain readable in the final stills.

**Local spill was treated as a retention gate, not dismissed by a small whole-frame average.** At Catrina cabin pixel (496,274), normal RGB is 117/104/95 versus bloom-off 13/2/13, a 104-byte maximum-channel change. Adjacent pixels also brighten substantially. Near trim at (439,276), the green-channel increase is 96 bytes. These are real bright-halo contributions on dark material, not merely white glint cores. A hood-region comparison has mean maximum-channel difference about 5.75 bytes and p99 31 bytes.

In the actual exterior pair, that spill remains localized near highlights; the seats, trim boundaries and lace are still distinguishable. The [matched Nocturne cockpit normal](../../evidence/cinder-unity-r25/20261111-074358-554-Capture/frame-0000.png) and [bloom-off cockpit](../../evidence/cinder-unity-r25/20261111-074412-539-Capture/frame-0000.png) share fingerprint `8207c1a0031e6dae`. The steering ring, radio/dashboard shapes and outside view remain readable. The windshield-region p99 difference is one byte; the dashboard-region p99 is nine bytes. Maximum isolated differences reach 93 bytes, so those maxima must remain disclosed even though they do not create a broad veil in this view.

The supplied views do not demonstrate a P1 obscuration requiring another revision. Keep the current 0.10 bloom strength as an upper bound for this acceptance. If a future angle or motion take merges trim, lace or cabin features into glare, first reduce gain and/or move the extraction knee upward while preserving the calibrated light and tone chain. Do not solve that by changing donor paint, exposure or sky energy.

### Dither and precision

Normal versus dither-off differs by at most one output byte anywhere in the matched image; no pixel exceeds three bytes. The static, screen-anchored noise is not conspicuous in the inspected stills. The display intermediate now retains half precision through FXAA and dithers at final quantization.

This establishes a bounded effect, not a demonstrated large banding improvement: the supplied daylight image is not a demanding dark-ramp test. No claim of eliminated motion shimmer follows from the still comparison. The interface is composited after the post effect; dither is not authored into its text or controls.

## Final packet and sampled action evidence

I inspected the [garage](../../evidence/cinder-unity-r25/review/01-garage.png), [pause](../../evidence/cinder-unity-r25/review/02-pause.png), [quit](../../evidence/cinder-unity-r25/review/03-quit-confirmation.png), [Catrina stance](../../evidence/cinder-unity-r25/review/04-catrina-three-wheel.png), [Media Luna lift](../../evidence/cinder-unity-r25/review/05-media-luna-lift.png) and [Nocturne roof](../../evidence/cinder-unity-r25/review/06-nocturne-roof.png).

Additional sampled source frames include Catrina 120/360/540, Luna 180 and Nocturne 0/420/869. Rose lace and brightwork remain present during the raised stance and drive views. Luna retains emerald fender/body gradients. Nocturne retains grey-blue paint separation and visible deployed fabric. The added effects do not visually reopen the r24 preservation failures in those sampled frames. These observations do not establish temporal highlight stability at every frame or all camera/LOD combinations.

## Cost evidence and budget limits

The paired runs use the same machine, vehicle, world and fingerprint `972aede729b16d4d`:

| Measurement | r24 control | r25 |
| --- | --- | --- |
| Session | 20261111-074313-554 | 20261111-074334-547 |
| Median | 33.3342 ms | 33.3425 ms |
| p99 | 42.4247 ms | 35.1378 ms |
| Maximum measured draws | 216 | 219 |
| Active geometry | 693,585 triangles | 693,585 triangles |
| External peak working set | 436,973,568 bytes | 426,602,496 bytes |

The three-draw increase is consistent with the bloom passes. Geometry remains below 700,000 and draws below 300 in this measured case. The existing 960 x 600/30 fps, no-MSAA, one-512-shadow and 2 GiB process limits remain intact. Internal Unity working-set counters report zero here; the external runtime receipts supply the memory values.

These short samples include the frame cap and PNG IO. The lower observed r25 p99 and memory peak do not establish a performance improvement, spare GPU capacity, a sustained budget or handheld 1080p/60 readiness. They show no measured budget violation in this bounded comparison.

## Remaining P2 and verdict limits

- Fine chrome/grille aliasing and glare stability still need continuous motion assessment at intended viewing distance. Static controls cannot establish that no pumping or shimmer occurs.
- Bloom's strongest cabin spill is locally large despite its small full-frame effect. Preserve these controls as a future regression gate and do not increase gain without new comparisons.
- Four retained compiler warnings remain to be explained or removed in a subsequent candidate with fresh output comparison.
- Flat glazing, synthetic contact/facade finish and the district's lack of social character still set the broader art ceiling. These small lighting additions do not solve those product/art issues.

No new P1 was found within this inspected lighting scope. This review supports retaining the bounded effects while preserving the r24 native-relative restoration. It does not grant broader Level 2 art approval or production quality. Physical controls, handling feel, heard audio, comfort, enjoyment and target-device performance remain unverified.
