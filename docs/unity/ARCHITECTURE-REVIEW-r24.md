# Independent technical component review: cinder-unity-r24

November 9, 2026, Pacific Time. Reviewer: migration_review.

## Verdict and independence

**PASS for the exact r24 simulation regression, finite loaded mechanics, sampled rigid-bone batching/camera regression, inspected hero roof graphics-policy gate and final packet integrity/provenance.** No P0 or P1 defect was found within this stated scope. This is Level 1 prototype/restoration component evidence, not an 8/10 Level 2 art approval, whole-game approval or physical playtest.

The reviewer did not implement the simulation, mechanism posing, batching, camera fix, canvas gate or packaging enforcement. The reviewer authored the earlier build-time `SurfaceShaderDiagnostics` helper and provides no independent final shader-implementation approval here. This review used source inspection, file hashing, retained reports and the stated matched stills. No editor/player was launched by the reviewer.

## Exact binding

| Item | Independently checked result |
| --- | --- |
| Player | `builds/cinder-unity-r24/Cinder.exe` |
| SHA256 | `7d78c95234b8c21a2f2a48e544eb888f43d52612d0c8680c7d6319128caa256a` |
| Authenticode | Valid; Oliver Smith, thumbprint `B25FE021B4201A483139CB226ED21699B38356DE` |
| Source fingerprint | `0e57c2129876c7765692f3fd50d0cfe0cd3a02d73c826f93c48c89c2c1c86d97` |
| Implementation checkpoint | `0b3e518d7d2f9d73e641026db7bb059d58bfbb3f`; exact file identity is established by the source fingerprint above |
| Probe | `evidence/cinder-unity-r24/20261109-232331-362-Probe/` |
| Build receipt | Unity 6000.3.6f1, succeeded, zero errors, four warnings |
| Probe process | Normal completion, 20.3035282 seconds, peak working set 330,137,600 bytes |

The source-manifest fingerprint was independently recomputed. All **5,331** listed source files match disk. Twenty-two owning simulation/view/rig/module entries compared with r20 are unchanged. `RuntimeBatchProbe` and host/packaging sources changed to add the roof gate and are reviewed below. The independent calculations are retained in `build/cinder-independent-r24-binding.json`.

| Probe output | SHA256 / comparison |
| --- | --- |
| `probe.txt` | `30604ec0896f7c0b6824c5df44a9ee5dafaa7c70e412f5156571e9eb322eec1d`; byte-identical to r9 |
| `loaded-rig-probe.json` | `27c6db591ee3b36fb5c51ed98937af6b95e416b0f10fbea9b8456e2493997dd7`; byte-identical to r9 |
| `runtime-batch-probe.json` | `3ecb8c0b4255b18bf549fac86ede133f2c7ea549d31ca10a0a1f6773c0828539`; all previous 148 PASS lines preserved, plus six passing roof-policy checks |

The four recorded build warnings remain part of this binding; this is not a zero-warning build. Probe process timing is not a rendered performance verdict.

## Preserved technical gates

The exact player records **204/204 simulation, 495/495 loaded-rig and 154/154 runtime checks PASS**, with no FAIL lines. Informational roof readback lines are not counted as additional checks. The simulation/loaded reports retain the independently reviewed r9 regression behavior and scope; r9's rejected visual approval is not inherited.

The managed simulation remains separate from Unity view/host state, advancing double-precision state at 60 Hz with four 240 Hz substeps. Deep clone/restore, seeded replay, midpoint restore and runtime fingerprint regressions remain covered. Preserved donor tuning does not mean bitwise Bullet solver/handling parity.

The 495 raw mechanism checks cover finite attachment poses across all nine lowrider detail tiers with positive flexible-geometry presence. The authorized Luna view-only 10 mm shackle-pivot installation adaptation remains documented in `MECHANICAL-ADAPTATIONS.md`. Steering samples at -0.32/0/+0.32 rad and linked axle travel do not cover every independent four-corner state, full +/-0.48 rad steering or continuous swept-triangle clearance.

The unchanged batching gate compares actual compensated baked rigid skins against current authoritative hidden source vertices, including nonidentity Frame scale 1.15. Nine-tier displacement and hidden-source tripwires remain meaningful. Seven pose fixtures per tier and Nocturne's seven roof-cover visibility phases remain checked. Worst sampled world-position discrepancy remains 0.00003130 m against the unchanged 0.0002 m threshold. This is position/participation evidence, not GPU-normal or tangent-handedness verification.

The 24 camera-clearance checks remain unchanged: three cars, both 22-degree roll directions, exterior modes 0/1/2 and garage, after final framing overrides. Minimum sampled clearance remains approximately 0.35000032 m. They do not establish arbitrary terrain/building avoidance or cockpit comfort. Renderer counts remain distinct from draw calls and frame-time acceptance.

## Roof gate: measured Null split and mandatory graphics check

The retained r21/r22 failures established that a Null graphics device can report `HasProperty(_Cull)=false` and shader support false while reading the serialized float value zero. A later write registers the property. r24 does not manufacture its initial pass with a preflight write: each tier's initial and repeated read-only report still records unsupported shader/absent property metadata, `_Cull=0` and positive original cloth participation.

The structural gate exempts graphics metadata only when the actual device is `GraphicsDeviceType.Null`. It still requires the expected `Cinder/Canvas` shader identity, `_Cull=0`, all three cloth nodes, positive mesh/triangle population and enabled/active/not-force-off renderers. The source-policy negative control replaces the first shared canvas material with the wrong Body shader and `_Cull=2`; all three tiers reject the change and restore their original policy. This combined mutation proves rejection of that wrong-source policy; it does not independently isolate each predicate.

`InspectRoofCanvasGraphics` refuses a Null device. On a real graphics device the same gate additionally requires `HasProperty(_Cull)` and shader support. The normal capture host inspects the actual hero car periodically after rendering, writes `roof-render-NNNN.json`, and fails a normal-material capture if the graphics policy fails. It does not rely on the headless mutation to initialize materials in that fresh graphics process.

The inspected normal run is `evidence/cinder-unity-r24/20261109-232445-070-Capture/`: 870 frames, exact signed player, D3D11, camera 2, Nocturne mode 8 and roof-cycle control. All **29** periodic receipts pass with three active hero cloth renderers. At frame 420 roof phase is 1, all three are in the camera frustum, and each records supported `Cinder/Canvas`, `HasProperty=true`, `_Cull=0`, enabled/active, `forceRenderingOff=false` and renderer visibility true. Their total original cloth population is 4,274 triangles.

The packager requires graphics roof receipts from the actual final Nocturne role, every receipt successful on D3D11 with active hero and three cloth renderers, and at least one fully raised phase with all three sections in the frustum. This is enforced by rejection, not an informational log. Normal capture receipts must also match the final executable and reject material/colour/reflection diagnostic flags and controls.

**Coverage limit:** these real graphics receipts inspect `module.View.Car`, the hero tier. Mid/far retain source and Null structural policy plus the raw/posed mechanism checks; no all-tier GPU canvas visibility claim is made. The cloth geometry is preserved across detail tiers, but that fact does not turn hero rendering into a mid/far graphics run. Renderer visibility/frustum metadata also does not prove per-pixel opacity or correct shading.

## Matched roof contribution control

The reviewer opened the actual fully raised normal image `20261109-232351-864-Capture/frame-0000.png` and the same-build hidden-cloth control `20261109-232418-478-Capture/frame-0000.png`. Both pose receipts record tick 842 and fingerprint `a57d1df31e3bdbc3`. The normal view contains a continuous dark canopy surface; the hidden control exposes the upper frame and background. Thus a complete absence of hero canvas is not reproduced in this matched view.

The retained `roof-coverage-comparison.json` records a 4,267-pixel diagnostic mask with approximately 99.67% differing by more than three channel bytes between r24 normal and hidden cloth. This supports a rendered contribution. The mask includes glazing/lighting differences and is explicitly not triangle-level opacity proof. The control is diagnostic evidence and must not enter the final normal review film. Earlier failures and misread low-angle packets remain retained; neither property metadata nor this comparison supplies whole-car art approval.

## Final packet binding

The completed `evidence/cinder-unity-r24/review/packet.json` selects five normal-render source roles. Their actual runtime receipts all identify the exact signed r24 executable and normal completion. Their launch arguments contain no material, colour or local/sky-only reflection diagnostic flags; actual material receipts say `none` and render receipts record material control `none` and colour control false.

| Role | Actual selected source session |
| --- | --- |
| Garage | `20261109-232942-508-Capture` |
| UI | `20261109-232945-387-Capture` |
| Catrina | `20261109-233004-812-Capture` |
| Luna | `20261109-233043-279-Capture` |
| Nocturne | `20261109-232445-070-Capture` |

The selected Nocturne role is the independently inspected normal cycle, with all 29 expected periodic roof receipts at contiguous 30-frame intervals through frame 840. All pass; frame 420 supplies the fully raised in-frustum check. All 29 copied delivery receipts match their hashes. The actual UI receipt retains all ten passing scripted assertions covering car selection, entering Mercer, pause/settings without simulation advancement, return to garage and explicit quit/cancel. Script injection does not establish physical controller behavior.

All **62** delivered review files, **147** built-player files and **2,234** original source-evidence files were independently rehashed against the completed delivery manifest with no drift. The full source-manifest check was repeated after packet assembly: all 5,331 listed files still match. The packet records six stills and a silent 960x600/30 video with 2,070 frames over 69 seconds. Its packaging record says full decode PASS; this reviewer independently verified file hashes rather than repeating the media decode.

| Completed artifact | Independently verified SHA256 |
| --- | --- |
| `review/delivery-manifest.json` | `2a1dcd8e6d2eaace339cfb67fa0862485237c93d01c92cc54e8a7c746092900a` |
| `review/proof.mp4` | `fcfae11118690490ec3719ab8c67bcb7ce34862bd867a226d74517716f0321c2` |

These integrity checks bind the final local packet to the reviewed player and actual normal sessions. They do not supply independent whole-film visual approval or establish deployment. Publication identity still requires verification after transfer.

## Explicit limits

No GPU-normal angular/tangent test, shader-implementation approval, exhaustive opacity/clearance test or native-relative whole-scene fidelity approval is supplied here. Physical keyboard/controller response, handling feel, heard audio, comfort, comprehension, enjoyment and sustained handheld 1080p/60 remain unverified. The inspection fixtures are posed checks; the normal culture driver uses simulation inputs, while roof animation belongs to host/view state and needs pose receipts as well as the simulation-only replay. Publication identity must be rechecked after transfer. Any owning source/player change requires a new applicable binding.
