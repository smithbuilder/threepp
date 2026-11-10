# Independent UX, observable gameplay and package review: r24

November 9, 2026, Pacific Time. Independent reviewer; did not implement the player, shaders, assets, cameras, simulation or packaging tools. No Unity editor or player was launched by this reviewer. Existing original PNGs, recorded inputs/state, render receipts and source/package files were inspected; encoded samples were decoded with CPU tools.

## Verdict and classification

| Aspect | Score / 10 | Scope |
|---|---:|---|
| Scripted menu/UX | **8.0** | Visible controls and ten injected PadState transitions, excluding human usability and physical-device behavior. |
| Observable gameplay | **8.2** | The bounded, recorded lowrider action path described below. |
| Whole-candidate visual / Level 2 | **Not approved** | City remains 6/10; cars and lighting remain 7/10 in their separate independent assessments. |

**No remaining P1 is established in this inspected UX/action/package scope. R24 is an honestly labeled prototype suitable for the explicitly authorized prototype publication, not a Level 2 or paid-release approval.** Gameplay/menu scores do not compensate for below-8 visual quality. R9's withdrawn visual approval is not reused.

The r20 roof failure is resolved within the reproduced state and sampled cycle. This conclusion uses actual side-view contribution controls and D3D render receipts in addition to poses. It is not inferred from technical probe counts or a low frontal image alone.

## Exact candidate binding

- Player: `builds/cinder-unity-r24/Cinder.exe`.
- SHA256: `7d78c95234b8c21a2f2a48e544eb888f43d52612d0c8680c7d6319128caa256a`.
- Source fingerprint: `0e57c2129876c7765692f3fd50d0cfe0cd3a02d73c826f93c48c89c2c1c86d97`.
- Independently checked Authenticode status: Valid.
- Technical packet records **204 simulation + 495 loaded-rig + 154 runtime-batch checks = 853**, plus ten scripted UI assertions. These checks are component evidence, not visual acceptance.

Independently rehashed **62/62 packaged review files**, **147/147 complete player files** including managed DLLs and data, and **six selected PNG origins**. No mismatches. The ordered source-manifest fingerprint was recomputed and matches the value above; this does not mean I independently rehashed all individual build-source files again.

All five normal review-role receipts identify this exact executable and normal completion. Their launch arguments contain no material/colour/sky-only/hidden-roof diagnostics; render controls read `materialControl: none` and `colourControl: false`. Separate deliberately hidden-cloth controls are used only as diagnostics, not substituted for normal presentation.

## Roof P1 repair and corrected interpretation

The earlier report's description of an absent canopy was too broad: matched side evidence establishes **partial canvas culling in r20**, not that every roof triangle or all roof geometry was absent. The low frontal camera is ambiguous because the canopy is shallow and near edge-on. It must not be the sole basis of a visibility verdict.

I opened r24 normal fully raised side `20261109-232351-864-Capture/frame-0000.png` and its same-state hidden-cloth control `20261109-232418-478-Capture/frame-0000.png`. The normal image has a dark canopy covering the cabin region that becomes open frame/glazing in the hidden control. The preserved native `docs/nocturne/review/native/roof-up.png` has the corresponding broad dark cover. The separate car reviewer also reopened the matched r20 side comparison and records its partial coverage.

`roof-coverage-comparison.json` reports 4,267 canopy/glazing ROI pixels: r24 differs from hidden cloth by more than three bytes in 99.67% of that mask, versus r20's 40.47%. This is supporting image evidence, not triangle-level opacity certification; the mask includes glazing and lighting effects. I read the comparison and opened the actual normal/hidden images rather than treating the percentage as a visual score.

The completed normal Nocturne cycle contains **29 mandatory `roof-render-*.json` receipts**. I checked all 29: success, Direct3D11, three canvas renderers, and three supported `Cinder/Canvas` material entries with cull 0 in each. At `roof-render-0420.json`, phase is 1.0, the main car is active and all three cloth parts are in the camera frustum, enabled and not forced off. The receipt lists 4,274 cloth triangles and actual world bounds. The explicit two-sided canvas policy now corresponds to the native application's runtime override rather than relying solely on the GLB flag.

This resolves the specific r20 P1. It does not certify all possible camera angles, every pixel or production roof mechanics. The roof path remains a schematic authored game mechanism. Failed r20 evidence remains preserved and was not relabeled.

## Fresh UX and action evidence

Packet: `evidence/cinder-unity-r24/review/packet.json`.

I opened all six selected original PNG copies, the normal/hidden raised-roof pair above, and these additional normal images:

| Session under `evidence/cinder-unity-r24/` | Additional frames opened |
|---|---|
| `20261109-232945-387-Capture` | 0030 and 0083, Luna rear chase and settings |
| `20261109-233004-812-Capture` | 0510 and 0630, forward steering and reverse |

I read all **63 saved action poses**: 26 Catrina, eight Luna and 29 Nocturne, plus selected input/contact records and all ten UI assertions. The visible controls and logs support car switching without starting, drive entry, pause/settings with a fixed sim tick, back, garage return and explicit quit/cancel. Pause/quit action labels are present. Settings expose display, cap, v-sync, invert look and sensitivity. These are injected PadState checks, not physical-controller mapping tests.

The action records and actual images support:

- **Catrina:** both front tires unload during the hop; opposite front tires unload in the two three-wheel modes; four contacts recover before ordinary driving. Nonzero steering/throttle produces forward/lateral movement, braking follows, reverse moves back and the car stops. The formerly broken right-three-wheel view retains the whole car in selected frame 360. That still is correctly named `04-catrina-three-wheel.png`, not a hop.
- **Luna:** neutral, front pump, hold and lower. Every saved pose retains four supporting tires. Root Y rises from approximately -0.0112 m to +0.1407 m and returns to -0.0108 m. The rear chase image retains the sage roof/trunk and green body instead of the old blackout.
- **Nocturne:** mild four-corner air raise/hold/lower and a selected-corner action, with four supporting tires in all 29 saved poses. The roof phase reaches one and returns during the full recorded cycle; the separate direct-render and side-control evidence establishes cloth participation at the formerly failing endpoint.

No general free-driving, all-camera or continuous-clearance certification is implied. Fine temporal shimmer, full panel interaction coverage, complete mouse/keyboard parity, focus-loss behavior and settings persistence after restart remain outside the inspected synthetic path.

## Encoder and evidence integrity

Proof: `evidence/cinder-unity-r24/review/proof.mp4`.

SHA256: `fcfae11118690490ec3719ab8c67bcb7ce34862bd867a226d74517716f0321c2`.

Independent frame read confirms **2,070 frames, 69.000 seconds, 960 x 600, 30 fps**, one video stream and no audio. The packet records a passing full decode. Source sequence is six seconds of UI, 26 seconds of Catrina, eight seconds of Luna and 29 seconds of Nocturne.

I independently CPU-decoded and opened proof samples at 8, 36 and 54 seconds. Catrina's hop, Luna's hold and Nocturne's raised-roof state retain their expected identity, framing and HUD without evident encoder corruption. The matched side/hidden control remains the useful canopy test; the frontal encoded sample alone is insufficient. This is sampled visual inspection plus complete mechanical frame counting, not visual inspection of every encoded frame.

Delivery-manifest SHA256: `2a1dcd8e6d2eaace339cfb67fa0862485237c93d01c92cc54e8a7c746092900a`.

## Private Patcher package audit

Prepared package: `evidence/cinder-unity-r24/patcher-package/`.

| Item | Independently checked result |
|---|---|
| Release ID | `r-mwadnquf-eb902ae9` |
| Version | `cinder-unity-r24` |
| Entry point / arguments | `Cinder.exe` with only `-module cinder-drive` |
| Archive bytes | 173,241,783 |
| Archive SHA256 | `ef54d45ab04b5cb50d71e7c66e1f4237a346fdacc37071f203d28ebac0d84eed` |
| Manifest SHA256 | `2476ae5e8b64fe870891abe70dd056b83dcbb8dce8e241a4424e591a67db5f22` |
| ZIP/inventory/build comparison | 147/147 file entries match hashes, sizes and current player files; no unsafe entry paths |

The final release notes explicitly call this a prototype, disclose city 6/10 and cars/lighting 7/10, retain human/handheld checks as unverified and identify source commit `0b3e518d7d2f9d73e641026db7bb059d58bfbb3f`. Actual line breaks were checked. There are no diagnostic material/render launch flags. No packaging blocker was found for the authorized prototype publication. This review does not assert that an upload has occurred or verify remote hub state.

## Performance and remaining quality bar

| Normal capture | Median / p99 interval | External peak working set | Maximum measured draws / listed triangles |
|---|---:|---:|---:|
| Catrina 26 s | 33.3370 / 34.0916 ms | 419,708,928 bytes | 216 / 693,585 |
| Luna 8 s | 33.3381 / 34.1675 ms | 368,168,960 bytes | 192 / 583,929 |
| Nocturne 29 s | 33.5686 / 37.3865 ms | 399,060,992 bytes | 154 / 683,557 |

These sampled captures meet the stated 300-draw and 700,000-triangle targets, not every possible scene/view. They remain capped 960x600/30 runs with PNG I/O, not target-device 1080p/60 measurements. Internal process-memory values are zero; external receipts supply the working sets above.

**Overall Level 2 remains unmet.** The independent city score of 6 and car/lighting scores of 7 cannot be averaged away by an 8.2 observable-gameplay score. Native-relative restoration and successful packaging do not raise absolute art quality automatically. The publication is an authorized prototype checkpoint with those limits, not an accepted paid-release product.

**UNVERIFIED:** physical input feel/mapping, heard audio, comfort, comprehension, enjoyment, sustained play, complete focus-loss behavior, settings persistence and target-handheld performance. No human playtest or listening claim is made. Any player/source/package byte change after these recorded hashes requires a fresh scoped verification.
