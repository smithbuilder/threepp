# Independent lighting technical review: r25

November 11, 2026, Pacific. Reviewer: migration_review. Source checkpoints reviewed: `76e5e09e` and `1bdc5719`, against published r24. The reviewer did not implement these lighting changes and did not launch an editor or player. The reviewer previously authored the unrelated build-time Body surface-shader dump helper; no generated dump is used to approve these new effects.

**PASS for exact-build/source binding, preserved regression reports, recorded contact-state consistency, normal-packet provenance and the stated capped performance observations.** No remaining source-level blocker was found after the corrections below. This does not approve the lighting's appearance or establish GPU/handheld performance. Independent visual reviewers are still assessing localized bloom bleed; effect retention and visual acceptance remain undecided by this report.

## Exact finished build and packet

| Item | Independently checked identity |
| --- | --- |
| Player | `builds/cinder-unity-r25/Cinder.exe` |
| Player SHA256 | `8c662a95e18c2c4bf2a478e7795b72d3fa2927d1d7d3dd9844596d5f427b7ae3` |
| Authenticode | Valid; signer thumbprint `C4CCAF1984D06EC8FCA1213AE172003AC96EA211` |
| Source fingerprint | `6ece4aa5250168c45f204df361b4f0d32f31dfc30bbde9ae3603cd93108c74b7` |
| Source checkpoint | `1bdc57191d8a6423c2d77a75def6782ac17f9b7a`, following `76e5e09e` |
| Probe | `evidence/cinder-unity-r25/20261111-073912-888-Probe/` |
| Build receipt | Unity 6000.3.6f1, succeeded, zero errors, four retained warnings |
| Delivery manifest SHA256 | `a18062de6c8ad3400cf0744bfbf41814540c66c84bc8b642b92628069713f48c` |
| `review/proof.mp4` SHA256 | `84faa9584c8c70bfeb1ab6c460c8358a4af077d4deb9bb468311c1f06d4897be` |

The ordered source fingerprint was independently recomputed and matched. All **5,331** listed source files match disk. All **62** delivered review files, **147** complete player files and **2,234** original source-evidence files match the delivery-manifest hashes. The packet is under `evidence/cinder-unity-r25/review/`: six stills and 2,070 video frames, 69 seconds at 960x600/30, silent. Its retained packaging record says full decode PASS; this reviewer checked hashes rather than repeating the decode or approving the film's appearance.

## Regression and state consistency

The exact-player reports pass **204 simulation + 495 loaded mechanisms + 154 batching/camera/material checks** with no FAIL lines. All three complete JSON reports are byte-identical to r24. Simulation JSON SHA256 is `3531b32b67241dde1d202497b4f740fc2462865e50f5c010e4954038aefd8955`, loaded rig SHA256 is `27c6db591ee3b36fb5c51ed98937af6b95e416b0f10fbea9b8456e2493997dd7`, and runtime batch SHA256 is `3ecb8c0b4255b18bf549fac86ede133f2c7ea549d31ca10a0a1f6773c0828539`. The separate final UI receipt retains all ten passing scripted checks. This was not a zero-warning build.

All 18 manifest entries beneath the pure Sim directory are unchanged from r24. Across the actual final roles, all **70** periodic pose receipts have the same simulation tick/fingerprint as the corresponding r24 receipts. Their **280** recorded footprint vectors are finite with weights in [0,1]. All eight sampled ungrounded tyre entries in Catrina's stance sequence have zero footprint weight; the remaining 272 footprint entries are positive. This supports the view-only boundary and the sampled support logic, not every intermediate frame's shader result or shadow-transition smoothness.

The selected Nocturne take retains 29 passing real-D3D roof receipts, three active hero canvas renderers and a phase-1 sample with all three sections in the frustum. The inherited roof-visibility scope remains hero graphics plus mid/far source/headless checks, not all-tier GPU visibility.

## Scope and reference document

The supplied November 10 Windowseat assessment is a reference assessment, not an instruction to copy a toon train renderer or change Cinder's art direction. The adaptation brief, `LIGHTING-ASSESSMENT-ADAPTATION.md`, correctly retains native PBR/sky/reflection inputs, native tone mapping, display-space FXAA and the existing graphics caps. Cabin coupling, toon bands, tunnel exposure and additional atmospheric passes are outside this change.

Reviewed source: `CinderGrade.cs`, `CinderGrade.shader`, `CinderCity.shader`, `CinderView.cs`, and the diagnostic/pose/packaging wiring in `StandaloneHost.cs`, `Run-Cinder.ps1` and `package_review.py`. No simulation or donor asset change is part of this reviewed diff.

## Findings corrected before build

| Finding | Resolution verified in source |
| --- | --- |
| New City world-normal conversion used a surface normal written only under `_NORMALMAP`, repeating the earlier non-normal-map compiler hazard | `o.Normal=float3(0,0,1)` is now unconditional before the optional normal map and world-normal conversion |
| World-to-module normal conversion included inverse Frame scale, changing AO strength at valid nonunit scale | The transformed normal is normalized before extracting module-up alignment |
| Two dither samples used the same nested-linear hash at a translated pixel coordinate, giving a wrapped offset relationship rather than independent samples | The second hash now uses different dot and wrap coefficients |
| Every posed world paid 84 terrain samples despite having no Mercer contact receivers | `contactGround.Count==0` now exits before sampling |

These corrections are source-verified, not GPU-verified. The failed early source observations remain part of this review history rather than being silently omitted.

## Contact-lighting boundary

The four support footprints read authoritative travel, wheel pose, Grounded flags and the existing terrain surface. They do not write simulation pose, forces, contact flags, seeded randomness or replay state. The exported footprint array is cloned. Values are supplied through per-renderer property blocks to named Mercer ground receivers; they do not mutate shared material assets or global shader state. World positions are transformed back into the same module coordinate system as the simulated contact points. The corrected normal path supports the positive uniform Frame scale convention.

The shader modifies Standard's occlusion input only, leaving authored albedo/vertex shade, emission and direct-light/shadow inputs intact. Footprints use a bounded maximum rather than additive overlap; the source bound is at most 45 percent indirect reduction. Grounded false forces zero weight, and supported tread clearance fades its weight. This is a view approximation, not a new physical contact model. Running evidence must still check footprint placement, contact transitions, slopes and lifted/airborne tyres; a correct Grounded branch alone cannot establish pleasant or flicker-free motion.

Contact-off/legacy diagnostics intentionally continue to compute Mercer footprint receipts, preserving the same support data for matched A/B controls. They therefore do not isolate the CPU cost of contact sampling; performance comparisons must state that limit.

## Post chain, lifecycle and cost

Bloom is extracted from linear HDR before tone mapping. Per-sample scalar extraction/capping preserves the source RGB ratio before spatial mixing. The unchanged native tone transform and exposure scale follow bloom addition; display-space FXAA remains after tone/display encoding. This does not imply exact final pixel hue preservation: spatial mixing and the existing tone transform can change displayed chroma. Matched palette/glint/sky controls remain necessary.

The bloom adds three blits at half, quarter and half resolution. Temporary targets are released in `finally`, and the prior `GL.sRGBWrite` state is restored. The persistent material and optional chart texture retain destruction cleanup. Temporary bloom texture bindings are assigned before their sampling passes; no persistent frame history or temporal randomness is added. UI is rendered separately after the world grade.

At 960x600, raw temporary colour storage rises from approximately 2.304 MB for the old full-size ARGB32 display target to 7.200 MB for one ARGBHalf display target plus half/quarter/half bloom targets, excluding pool overhead. This is approximately 4.896 MB additional temporary colour storage. Display reads/writes also use higher bandwidth and bloom adds texture fetches. The source is bounded; it is not evidence that the extra passes fit the measured budget. Keep the existing capped test and process limits; do not infer GPU headroom from a 30 fps PNG capture alone.

## Dither check

The final display-space noise is static and bounded to half one display byte before saturation/output. A CPU float32 proxy over 960x600 pixels gives mean -0.000635 display bytes, minimum -0.499094, maximum +0.498750, standard deviation 0.204277 bytes versus ideal triangular 0.204124, and cross-hash correlation approximately 0.000098. This supports the corrected source distribution at the capped resolution; it is not GPU output, a temporal-motion test or visible banding improvement. Clipping near black/white can introduce local bias even with approximately zero-mean input noise. Matched gradients must decide whether the effect helps.

## Evidence controls

The bounded runner accepts only the listed lighting controls for graphics captures/benchmarks. The post render receipt records `lightingControl`; periodic pose receipts clone the four footprint values. The packager rejects both the `-lighting-control` argument and a non-`none` render-receipt lighting control in the normal packet. Thus a legacy/contact-off/bloom-off/dither-off diagnostic must not silently enter delivered normal evidence.

The actual five packet roles were independently checked: garage `20261111-074107-197-Capture`, UI `20261111-074111-071-Capture`, Catrina `20261111-074130-473-Capture`, Luna `20261111-074209-487-Capture`, and Nocturne `20261111-074229-898-Capture`. Every role records normal completion on the exact signed r25 player, no forbidden material/lighting/colour/reflection diagnostic flag, material control `none`, lighting control `none` and colour control false. Diagnostic controls do not enter this normal packet.

## Paired capped performance observations

| Matched Catrina mode-1 run | r24 | r25 |
| --- | ---: | ---: |
| Session | `20261111-074313-554-Benchmark` | `20261111-074334-547-Benchmark` |
| Median frame interval | 33.3342 ms | 33.3425 ms |
| P99 frame interval | 42.4247 ms | 35.1378 ms |
| Maximum recorded draws | 216 | 219 |
| Active geometry tally | 693,585 triangles | 693,585 triangles |
| External runner peak working set | 436,973,568 bytes | 426,602,496 bytes |

Both exact signed players completed normally; their performance receipts identify the same final simulation fingerprint `972aede729b16d4d`, 180 frames, 82 renderers and the same vehicle/world. The three added recorded draws agree with the three extra bloom blits and stay below the stated 300-draw cap. The active geometry tally stays below 700k, but is not all-pass GPU submitted triangles. The in-player performance JSON reports zero for peak working set in both runs; the table uses the external runner's actual process measurement.

These are short, 30 fps capped 960x600 PNG-IO observations, not isolated GPU timings or proof that r25 is faster. The lower observed P99 and process peak in one pair do not cancel the additional render-target storage/bandwidth calculated above. No sustained desktop or handheld 1080p/60 claim follows.

## Remaining acceptance boundary

Exact identity, preserved mechanics and sampled contact receipts are established within this report. Actual AO footprint shading, between-sample support transitions, gradient/dither improvement, halo width, palette preservation, bloom leakage and UI clarity still require the independent visual/rendered assessment. A material/state receipt is not a pixel-coverage or opacity test. The present 154-check runtime probe does not add a GPU angular-normal or contact-AO raster test.

Physical input feel, heard audio, comfort, enjoyment, native handling parity and target-device performance remain outside this technical verdict. Publication identity must be checked after transfer. An owning shader/view/player change requires a new build binding; these r25 results cannot approve an unbuilt adjustment.
