# Independent Unity quality review, r1

2026-11-08 Pacific. Reviewer: independent quality agent. I did not author the Unity sim, view, importer, host or Blender kit.

## Verdict

**No accepted candidate. Diagnostic presentation scores are recorded below; gameplay remains unscored pending motion and controls evidence.** Source inspection identifies concrete control and mechanical-view defects below. A successful compile or pure-sim probe cannot establish the presentation/gameplay gates.

The current player direction is lowrider car culture: La Catrina, Media Luna and Nocturne, with Cruise Mercer, Hydraulic Session and Workshop. Safari/buggy racing is deferred. The older seven-vehicle donor audit remains useful technical context; its entire catalog is not the current player-facing menu requirement.

## Source review findings

| Priority | Finding | Evidence and consequence | Required check or correction |
|---|---|---|---|
| P1 | E both confirms a garage action and chooses the next car | `StandaloneHost.ReadPad` sets `ADown` for E. `Navigate` invokes the focused menu action before checking E for `CycleCar(1)`. With Cruise Mercer focused, E starts driving and clears the garage page before car cycling can execute. Other focused actions can open a page or reset the model unexpectedly. | Give next-car selection an unambiguous binding, or exclude the car-cycle key from garage confirmation. Verify Q/E and LB/RB switch all three cars without starting a session. |
| P1 | Moving lowrider hardware is only partially posed | `CinderView.Pose` updates the wheels, selected front arms/uprights, rear axle and generic damper nodes. It does not update the donor's rear links, steering tie rods, driveshaft/slip sections, Catrina hydraulic members/coils or Nocturne bellows and bearing plates. These parts were dynamically updated in the native adapters and are central to the user's motion quality bar. | Capture wheel-off and low-side poses at cruise, raised, lowered and split travel. Port the relevant rigid-link and deforming-member adapters, or explicitly retain this as a partial migration rather than an accepted lowrider candidate. |
| P2 | Reset loses reverse synchronization | The host toggles its `reverse` field and copies it to `module.Reverse` on RB/G. `ResetModule` creates a module with default `Reverse=false` while retaining the host field. After resetting from reverse, the next RB/G toggles the host back to false, leaving the player in drive again. | Set both values consistently on reset. Verify reverse, reset, reverse as a user sequence. |
| P2 | Hydraulic modes have no meaningful on-screen names | Pause uses `HYDRAULICS / MODE N`; the driving HUD only says Y/F hydraulics and shows an unavailable boost percentage. A new player cannot tell hop, either three-wheel stance, raise, lower, hold or individual Nocturne corner selection apart. | Use vehicle-specific mode names and show the current mode in the HUD. Remove unused boost information from this lowrider menu or make it relevant through an explicit action. |
| P2 | Car-specific workshop interactions are not exposed | The imported donors contain hood/trunk pivots and Nocturne coach doors/top. The current host/view offers no panel or roof action, so Workshop currently means driving on the level test pad. | Describe Workshop honestly as test grounds for r1, or expose a small bounded inspection interaction with matching gamepad and keyboard actions. Do not imply the donor's complete coachwork interaction has migrated. |
| P2 | Mercer art is a visible fidelity risk | `create_kit.py` uses flat-color architecture, window cards and faceted tree clusters. `GroundMaterial` uses the gravel texture for city asphalt. The native Mercer references use photographic masonry/paving, signs, richer planting and controlled streetscape detail. | Inspect the exact player for a coherent lowrider setting. Bring over the available material provenance/texture sources as appropriate. Any visibly reduced environment should be called a migration prototype. |
| P3 | Garage orbit parameters are unused | The garage computes a slowly changing angle and passes it to `CinderView.Camera` with mode 2. Camera mode 2 ignores yaw/pitch. | Either use a true garage orbit or remove the unused orbit calculation. A fixed hero camera is acceptable if it shows the full selected car beside the menu. |

These findings are from source, not invented runtime observations. Line numbers may change during repairs; the named methods identify the reviewed behavior.

## Import and material inspection still required

The offline importer copies authored mesh geometry, vertex colors, UVs, hierarchy and common metallic/roughness/alpha parameters into Unity assets. Runtime inspection must still confirm front-face winding, texture orientation, normal-map direction, smoothness, dark paint reflections, decal cutouts, glass and wheel/brake ownership. The glTF animation clips are not imported; static panel/top state is not proof of interactive support.

For this lowrider focus, the important retained visual cues are La Catrina's rose paint, whitewalls and ornament; Media Luna's coherent cream/copper body and paired front lift; Nocturne's piano-black mass, chrome, oxblood cabin, narrow whitewalls and gentle independent air motion. No old native review score applies to the Unity renderer.

## Evidence needed for a scored verdict

1. Exact revision, executable and imported-source hashes, probe receipt and saved review replay.
2. Three to six fresh player stills covering the garage, ordinary Mercer driving, side profiles, hydraulic travel and wheel-ground contact. A side-by-side donor reference may assist comparison but cannot substitute for Unity evidence.
3. One uninterrupted clip no longer than 90 seconds showing all three lowriders, meaningful mode changes, grounded recovery and readable player UI. Include exact-build pose/telemetry records for interpreting motion.
4. A controls/menu exercise covering car switching, session selection, mode switching, reset/reverse, pause, focus loss, settings persistence and quit confirmation. Physical pad feel remains a human-only check.
5. Measured performance scope. Current 960x600/30 captures with PNG I/O are a bounded evidence run, not 1080p/60 or handheld validation. Record median and p99 frame time plus peak working set, compared against a back-to-back control on the same machine where a relevant reviewed control exists.

Presentation will be scored for silhouette/material coherence, environmental composition, readable UI and visible motion. Gameplay will be scored for observable session clarity, input/menu behavior, hydraulic response/recovery and repeatability. The weakest required aspect owns the quality verdict. Input feel, heard audio, comfort, comprehension and enjoyment stay **UNVERIFIED** until Oliver plays.

## Donor references inspected

- `docs/nocturne/review/native/passenger-hero.png` and `motion-sheet.jpg`: coherent black convertible, complete road-contact framing, mild raise/lower and independent-corner presentation.
- `docs/nocturne/review/final-visual.md` and `final-mechanics.md`: native-only 8.055/8.315 verdicts, including their scope and remaining aliasing/cabin/roof limits.
- `docs/la-catrina/HANDOFF.md`: native-only hop and both three-wheel stances, exact reviewed artifact bindings.
- Current GLB binary JSON: La Catrina 746,922 triangles; Media Luna 199,968; Nocturne 299,596. The scene budget must be measured with the selected hero and actual world, including all submitted passes.

## Review updates

### Diagnostic r2 packet

Observed `evidence/cinder-unity-r2/20261108-233606-706-Capture/frame-0000.png` directly with the image viewer. The sibling runtime receipt binds Windows player SHA256 `0ACFF11EA8FF8843477866737D2B8FDFF3FAD4DEC36C6D4BB255B3A6726C7195`, revision `cinder-unity-r2`, La Catrina, Mercer, mode 0, a normal exit and peak working set 242,610,176 bytes. The pose receipt is tick 0, so this is a paused garage diagnostic, not a driving demonstration.

**Diagnostic presentation: 3.8/10. Gameplay: UNSCORED. Verdict: fails presentation gate.** This score applies only to the observed r2 menu still and does not approve a release or assess unseen changes. The warm orange/cream menu hierarchy is coherent and readable. The surrounding image fails to present the car or its setting adequately:

- The nose and front-left tire sit behind the navigation panel. The garage card occupies the lower-right area immediately beside the rear/contact region. A lowrider hero should show its entire side silhouette and both near tires together.
- The body reads nearly black/maroon with broken bright edges and exposed inner surfaces rather than La Catrina's coherent candy-rose shell. The importer winding issue reported by the implementation agent is consistent with this observed appearance, but a corrected player is required to establish the fix.
- A large sky and empty tan horizon dominate the car side of the composition. Mercer storefronts, pavement, architectural detail and street scale are not visibly framing the lowrider. The image conveys a migration prototype rather than a lively lowrider street setting.

The next packet should first establish outward solid body surfaces and materially correct paint, then put a complete side/three-quarter hero entirely in the right-hand picture area with Mercer behind it. Place the garage name card below the vehicle footprint. Keep tire contact visible. Do not trade away the solid body/material repair for menu styling.

The one-frame performance file reports zero median/p99 and zero process memory internally. Those fields are not measurements suitable for a performance verdict. The external supervisor's peak-memory field remains useful for this bounded launch. There is no 1080p/60 or handheld acceptance.

### Source repair observations after the initial review

Current source excludes E from garage confirmation, synchronizes reverse on reset and names hydraulic modes in the HUD. These address the original source findings; interactive player behavior is still unverified. `RigMechanisms.cs` adds the moving linkage, spring/bellows and coachwork adapters that were absent in the initial view. I inspected its hierarchy/deformation code and the loaded-rig probe independently. Geometry gates must be interpreted narrowly: finite transforms/vertices do not prove clearance or bearing attachment, and the initial Catrina/Luna measurement sets cover fewer component endpoints than Nocturne. The implementation agent has been asked to clarify or expand that coverage. Root reports a failing Nocturne roof probe, so that gate remains open.

Keep this report and failed evidence when issuing a later revision; do not relabel the r2 frame as validation of a rebuilt player. A scored gameplay review still requires a running scripted session and recorded input/menu exercise.

### Diagnostic r3 packet

Observed `evidence/cinder-unity-r3/20261108-234614-791-Capture/frame-0000.png` directly and compared it with `build/la-catrina/round-11/studio/side.png`. The r3 runtime receipt binds player SHA256 `CDEF6BEAB48BBDC898A3F5A674642E1A6967B6DDC8AE822F2C186FD00143DE8E`, normal exit and peak working set 243,064,832 bytes.

**Diagnostic presentation: 5.9/10. Gameplay: UNSCORED. Verdict: still below the presentation bar.** The full car now fits in the picture area, the front and rear tires are visible, outward body panels form a coherent vehicle and the name card clears the car. These are observable improvements over r2, not merely source changes.

The setting is now visible, but oversized vertically stretched masonry, repeated flat-black windows and faceted spherical tree canopies make it feel like a test street. The masonry reads as metre-sized slabs relative to the 5.33 m car. World-scaled UVs, storefront bases, recognizable awnings/signage and smoother clustered foliage with branching trunks should establish human street scale. The car reads as muted dusty plum instead of the donor's glossy rose; inspect the long paint reflection band, chrome/rubber distinction and material brightness under the repaired street lighting. The windshield reads opaque beige/green in this still, so cabin visibility needs an actual glass/material check.

Preserve the repaired whole-car framing. This is still one paused menu still with a one-frame performance file; it cannot establish driving behavior, motion quality or performance. Root reports that the expanded rig probe is catching a Luna leaf constraint error and a Nocturne far-LOD bearing-sample loss. Those failures remain open until a fresh player probe and independent motion review demonstrate the repairs.

### Diagnostic r4 menu and scripted controls packet

Observed the main menu at `evidence/cinder-unity-r4/20261109-000856-086-Capture/frame-0000.png` and scripted flow frames 8, 13, 18, 53, 83, 93, 118, 163 and 168 at `evidence/cinder-unity-r4/20261109-000859-577-Capture/`. Both runtime receipts bind player SHA256 `DE4C5F629B6E17F4B5653032D17FC37C6EC64FCE935F3A263DCD95758DA48A9D`. The flow receipt exits normally and reports external peak working set 360,054,784 bytes. I read all ten `ui-probe.txt` assertions and the corresponding menu images. I also read the fresh loaded-rig report, which records 495 checks with `Success=true`.

**Diagnostic presentation: 6.1/10. Observable menu/session gameplay: 6.5/10, provisional. Verdict: no acceptance yet.** The presentation score describes only the observed menu/stationary frames. The gameplay score describes the scripted menu path and brief session entry, not hydraulic motion or human handling. More motion evidence is required for the complete gameplay gate.

The revised masonry now reads as smaller brickwork and storefront divisions give the street a clearer ground floor. All three cars can be distinguished and remain fully framed. The core menu is readable. However, the bright opaque-looking glazing and highly specular smooth tree spheres still undermine the authored car and street. La Catrina's paint remains more muted plum than the donor rose. The setting has little street furniture detail and its foliage reads as molded plastic. These are visible P2 quality defects, not proof that an asset alpha value or roughness parameter is numerically wrong.

**New P1, missing action labels:** pause frame 53 shows a highlighted orange action with no `KEEP CRUISING` text. Quit frame 163 shows a highlighted orange action with no `STAY HERE` text. The label is visible again by frame 168. `MenuCanvas.Item` replaces or reuses pooled text/images without restoring sibling draw order; a newly created fill can render above retained text. The renderer must preserve draw ordering and the exact UI sequence must be recaptured. Menu-state PASS lines do not catch an invisible control label.

**New P2, input hint activity coverage:** current hint detection does not include LT/RT, D-pad, vertical-stick-only movement, X/Y, Start or View. A common first throttle or hydraulic input can leave keyboard wording visible. `ScriptedUiPad` bypasses `ReadPad`, and the observed synthetic pad flow retains Q/E/F1 hints. Expand activity detection and check visible pad labels using the shared path.

The ten passing assertions establish injected PadState selection, session entry, pause, settings entry/return, garage return and quit/cancel state transitions. They do not establish physical controller/InputManager mapping, settings persistence across restart, focus-loss behavior, reset/reverse interaction, keyboard/mouse parity or human input feel. These remain unverified unless separately exercised.

The flow performance file reports median 33.3369 ms, p99 142.7155 ms, 549,856 listed triangles, 228 mesh renderers and maximum measured draw calls 776. It includes PNG I/O and menu/car changes and is not a 1080p/60 benchmark. Its internal memory field remains zero, so use the external supervisor's actual peak. The measured draw counter exceeds the storyboard's 300-draw target; renderer count is not a substitute for actual draw calls. Record this budget miss openly and measure a stable driving scene before acceptance.
