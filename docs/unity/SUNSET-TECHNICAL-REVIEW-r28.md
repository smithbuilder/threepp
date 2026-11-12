# Independent sunset technical review: r28

November 11, 2026, Pacific. Reviewer: migration_review. The reviewer did not implement the reviewed runtime, shaders, bakes or receiver correction, and did not launch an editor/player. Only this report was written. The reviewer authored the earlier Body shader-source dump helper; no dump is used as independent GPU-normal or shading proof.

**PASS for the stated source/derivative boundary, exact build and packet integrity, preserved finite regressions, recorded support-state consistency and capped performance observations.** No new source-level blocker was found in the r28 delta. This is not whole-scene visual approval, exhaustive GPU/shadow correctness, Level 2 art approval or physical play acceptance. Independent visual judgments on palette and the repair-shadow hole remain separate from these technical conclusions.

## Exact identity

| Item | Independently verified result |
| --- | --- |
| Implementation checkpoint | `0ec89d0ec97a9db7f739953d08b8928ef1aa806c` |
| Player | `builds/cinder-unity-r28/Cinder.exe` |
| Player SHA256 | `bbea8c386456dd9c07dd2348c5b2dd23618aa741bdba69dd14088990aead2aa8` |
| Authenticode | Valid; thumbprint `C4CCAF1984D06EC8FCA1213AE172003AC96EA211` |
| Source fingerprint | `baf3a961c9ac75792e9150a4d3c16e9c8ebb8f042252a78be594cb575fe9580e` |
| Build receipt | Unity 6000.3.6f1, succeeded, zero errors, four retained warnings |
| Probe | `evidence/cinder-unity-r28/20261111-204558-946-Probe/` |
| Normal review packet | `evidence/cinder-unity-r28/review/` |
| Delivery-manifest SHA256 | `cc471c7f4aaa22f40cf5f992ec9b5e8a2c56034445b8f81118344fddc0128dfa` |
| Proof-video SHA256 | `32d1dfc8efb94ce0ed41c03d2f35eacb48a18a0f8cd2cd69b829ed1764e357db` |

The ordered source fingerprint was independently recomputed. All **5,411** listed source files match disk. All **147** complete player files, **62** delivered review files and **2,239** original evidence files match their delivery-manifest hashes. The exact executable agrees with probe, final capture and benchmark receipts. This is local integrity/provenance; publication requires verification after transfer. Four warnings remain, so this is not a zero-warning build.

The normal packet records six original stills and a silent 960x600/30 video: 2,070 frames, 69 seconds. Its packaging receipt records full decode PASS. This reviewer independently checked the hashes rather than repeating the decode or approving the whole film's appearance. Rejected r26 and r27 evidence and written failure findings remain retained; passing mechanics does not retrospectively approve those candidates.

## r28 source and derivative boundary

The r27-to-r28 implementation delta changes the authored broad anti-sun/lower environment palette and the city receiver selection. It does not repaint cars or alter the metallic/roughness/coat response, key light, tone transform or BRDF implementation. **361** selected core shader/Grade/Sim/host-lighting/material entries match the r27 manifest exactly, including all inspected material files and the pure simulation entries.

Archived r27 versus r28 recipe comparison confirms unchanged sun direction/colour/irradiance, Unity key intensity, environment strength, sky radiance scale, disc size/edge, fog, constant city bounce and source HDR identity. Native-hemisphere and constant-bounce coefficient arrays are exactly unchanged. Environment SH changes intentionally because the disc-free sky palette changes. The recipe's authoring-source, visible EXR and ambient-panorama hashes match the actual files.

The recorded white-furnace error is approximately 0.00000584, hemisphere error 0.00000000745 and constant-bounce error zero. These are offline numerical calibration checks, not measurements of the displayed palette or GPU units. The bounce remains an authored omnidirectional constant fill, not spatially solved or occluded city bounce.

The new lower urban return and reduced anti-sun rose contribution feed both the reflection derivative and diffuse environment integration. Thus the correction acts through lighting while retaining material factors. Whether the resulting reflected paint reads teal/blue-grey in every relevant view is a visual acceptance question, not established by unchanged factors alone.

## Named receiver policy

`RoadReceiver` matches `ground.*`, `static.repair`, `static.white`, `static.yellow`, `static.asphalt` and `static.dark`. The current prefab contains the two ground names and five named static batches. The view enables existing vehicle-shadow reception on these matches and supplies the same contact-lighting property block to them. All city batch shadow casting remains off, preserving the existing authored static-shade approach.

This is a **named-batch receiver policy**, not a pure ground-only geometric selection. In particular, white and dark material batches include non-road geometry. Their matching parts can now receive the vehicle's directional shadow. The contact approximation additionally checks module-up alignment, contact height, footprint extent and authoritative support weight; these restrict its effect but do not prove that every non-road element is untouched. The selection also applies to the daylight Mercer control, not solely the sunset prefab.

No geometry, contact surface, collision or simulation state is changed by this policy. It adds no Light component or shadow map. It can add shadow sampling/contact-loop work to additional visible fragments and property-block updates to more batches. Unchanged draw count alone cannot measure that work.

The existing headless runtime probe constructs a world-0 test view. Its preserved 154 checks therefore do not directly test the new Mercer receiver selection or prove the repair's rasterized shadow closure. Fresh actual graphics evidence and the independent visual report must carry that conclusion.

## Regression comparison, without hiding differences

The exact player passes **204 simulation + 495 loaded mechanisms + 154 runtime batching/camera/material checks**, with no FAIL lines. The ten final scripted UI assertions also pass. The probe process completes normally in 20.3397535 seconds, with external peak working set 331,980,800 bytes.

| Complete report | SHA256 | Comparison with r25 |
| --- | --- | --- |
| `probe.json` | `3531b32b67241dde1d202497b4f740fc2462865e50f5c010e4954038aefd8955` | Raw byte-identical |
| `loaded-rig-probe.json` | `27c6db591ee3b36fb5c51ed98937af6b95e416b0f10fbea9b8456e2493997dd7` | Raw byte-identical |
| `runtime-batch-probe.json` | `15276fdb6a89f9a07016f7603849b2569eba8a2ffeef9ba6866d23ff56c79b07` | Nine text-line differences, all transient material instance IDs |

The reviewer independently confirmed that replacing **only** occurrences matching ` id=-?\d+` makes the entire runtime JSON exactly equal to r25. No threshold, result, metric, count or other text was normalized. The raw report is retained and is not described as byte-identical. This agrees with `evidence/cinder-unity-r28/probe-comparison.json`.

Inherited finite limits remain: posed mechanisms are not continuous swept-triangle clearance; skinned position comparison is not GPU-normal/tangent verification; the 24 camera assertions do not exercise the newer sunset garage branch; hero roof graphics receipts do not establish all-tier GPU visibility; and the managed solver is not bitwise Bullet handling parity.

## Normal capture provenance and state

| Actual selected role | Original session |
| --- | --- |
| Garage | `20261111-204746-282-Capture` |
| UI | `20261111-204832-479-Capture` |
| Catrina | `20261111-204842-036-Capture` |
| Luna | `20261111-204920-549-Capture` |
| Nocturne | `20261111-204941-030-Capture` |

All five roles record normal completion on the exact signed r28 player, no forbidden diagnostic argument, material/lighting controls `none` and colour control false. Their actual city receipts identify `mercer-six-pm`, city control `none`, eight practicals and scalar 28 at the identity frame. These are the normal roles selected by the completed packet, not substituted daylight or lamps-off controls.

All **70** periodic pose receipts match r25's corresponding tick/fingerprint. All **280** footprint vectors are finite and have weights in [0,1]; all eight sampled ungrounded Catrina tyres have zero weight. This supports the unchanged simulation and sampled support boundary, not every between-sample shadow transition. Nocturne retains 29 passing hero D3D roof receipts with three active cloth sections and a fully raised in-frustum sample. Roof phase remains host/view state and is not reproduced by the simulation-only replay alone.

The additional `20261111-205155-450-Capture` is a 120-frame Catrina camera-7 autodrive with **`-lamp-review`**, selecting a recorded diagnostic initial Z=49 pose. It is a focused diagnostic drive, distinct from the normal 69-second packet; the packager forbids that flag in normal delivery roles. The separate `20261111-205212-275-Capture` is a normal completed Nocturne camera-6 cockpit still after warmup, with no diagnostic flag. Both receipts bind to the exact r28 player. They are separate supplemental evidence, not additional frames silently inserted into the normal film.

## Paired capped cost

| Matched Catrina mode-1 test | r25 | r28 |
| --- | ---: | ---: |
| Session | `20261111-205113-734-Benchmark` | `20261111-205134-194-Benchmark` |
| Median interval | 33.3414 ms | 33.3378 ms |
| P99 interval | 36.0492 ms | 35.0822 ms |
| Maximum recorded draws | 219 | 219 |
| Active geometry tally | 693,585 triangles | 693,585 triangles |
| External peak working set | 436,563,968 bytes | 462,155,776 bytes |

Both exact signed players complete normally with 180 captured frames, warmup 60, 82 renderers and fingerprint `972aede729b16d4d`. Draws and active geometry remain within the stated capped scene limits. Geometry is an active tally, not all-pass GPU submitted triangles. The in-player JSON reports zero memory peak in both runs; the table uses external runner measurements.

The r28 process peak is 25,591,808 bytes higher in this pair. The short 30 fps capped PNG-IO run is not isolated GPU timing and does not establish speed improvement or headroom. The eight practical range/cone checks, up to two direct BRDF responses per coated pixel and added receiver sampling still have shader cost. The fixed midpoint benchmark is not an exhaustive worst-case car-under-lamp or foliage stress profile. No sustained desktop/handheld 1080p/60 approval follows.

## Remaining acceptance boundary

This report establishes exact local identity, a bounded and explained implementation delta, preserved finite mechanics and actual normal evidence provenance. It does not independently approve sunset brightness, every reflected paint view, lamp leakage, contact/shadow opacity, static interpolation, UI composition or the final film's visual quality. Physical controls, handling feel, heard audio, comfort and enjoyment remain unverified. Later owning source/player changes require their own applicable binding; transfer/publication needs a final identity check.
