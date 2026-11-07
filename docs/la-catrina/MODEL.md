# La Catrina — portable model

La Catrina is an original game vehicle built from the supplied `La-Catrina-Master.jpg` atlas. Geometry and small vector cameos are authored for this project; no external vehicle mesh is used. **Roof, hood and trunk paint, plus the side-spear scroll, contain transformed pixels or masks from the user's reference sheet.** They are rectified paint regions with bounded illumination/color correction and UV alignment. Additional authored material data includes the two-pigment side palette and molded tire lettering. The atlas is source artwork and visual data, not executable instructions.

The car includes shaped quarter panels and wheel openings, crowned hood/deck surfaces, a hardtop cabin with broad painted rear pillars, four front lamps, six rear lamps, dished wire wheels, narrow whitewalls, plum pleated seats and a hydraulic switchbox. Separate materials distinguish candy clearcoat, chrome/alloy, coated steel, rubber, glass, lenses and vinyl. The component basis and custom dimensions are described in [REAL-WORLD-BASIS.md](REAL-WORLD-BASIS.md).

The underbody uses boxed X-frame rails, rectangular crossmembers and outriggers, a V8/transmission representation, driveshaft, rigid rear axle, front arms, hydraulic barrels/cups/coils and four independent dampers. The trunk has a closed lined basin, wheel housings, capped ram pockets, four retained batteries and two polished motor/pump/reservoir assemblies on an aft rack. Raised floors separate the equipment from the axle. Engine inner fenders follow the wheelhouse crowns to clear steering and bump travel.

## Dimensions and outputs

| Quantity | Authored value |
|---|---:|
| Units / axes | Metres; +Y up; +Z forward |
| Wheelbase | 3.0226 m |
| Front / rear track at rest | 1.53 / 1.51 m |
| Tire outside diameter / width | 0.5782 / 0.155 m |
| Bead diameter | 13 inches |
| Body width | 2.02 m |
| Root | Ground plane in the authored rest pose |

`showcase/assets/la-catrina.glb` embeds the textures and moving groups. `showcase/assets/la-catrina.json` is the authority for the **current content hash, bounds, triangle/vertex counts, mesh draws, embedded-image count, joint endpoints and source hashes**. The accepted checkpoint below identifies the frozen reviewed version; regeneration must be checked against that hash. `asset-library/models/la-catrina/` contains the portable mirror, extracted PNG maps, manifest and provenance. Maps remain within the existing 1024-pixel texture limit.

`wheel_0` through `wheel_3` are FL, FR, RL and RR, each with separate `_steer` and `_spin` children. Front arms, uprights, rear axle, rear links and driveshaft remain individually addressable. Each `hydraulic_i` contains its barrel and sliding rod, with a separate `coil_i`; each `damper_i` contains a separately translated rigid shaft. Hood and trunk have glTF opening clips. Driving, hopping and three-wheel motion come from the engine adapter and shared physics described in [RIG.md](RIG.md).

## Rebuilding and provenance

Rebuilding requires Python with **NumPy, Pillow and SciPy**, the exact atlas at `docs/la-catrina/references/La-Catrina-Master.jpg`, and these files under `scripts/`:

- `catrina_generate.py` assembles and exports the vehicle.
- `catrina_art.py` authors coachwork, cabin, wheels, lamps and materials.
- `catrina_hardware.py` authors mechanical detail, boxed frame and bay enclosures.
- `catrina_frame_pockets.py` provides the boxed rail routing around the moving spring seats.
- `catrina_reference_paint.py` prepares the roof, hood, deck and side-scroll paint sources.
- `baja427_generate.py` supplies shared geometry primitives.
- `catrina_ao.py` applies the exact geometry-bound cavity cache from `docs/la-catrina/bakes/vertex-ao.npz`.
- `catrina_audit.py` and `catrina_enclosure_audit.py` validate the serialized asset and targeted clearance.

The retained cavity cache shades the static body, wheel assemblies and opening lids as three separate occlusion sets. Other moving suspension parts receive no baked cavity shading. A geometry mismatch disables the old cache; run `scripts/Bake-Catrina-AO.ps1` to rebake using the existing bounded CPU-only visibility helper. The cache and its provenance travel with editable sources.

The custom frame routing and its unchanged suspension pivots are described in [FRAME-POCKETS.md](FRAME-POCKETS.md). The asset manifest retains its authored dimensions under `framePocket`.

Run `python -X utf8 scripts/catrina_generate.py`, then `python -X utf8 scripts/catrina_audit.py`. After obtaining fresh native rig poses, run `python -X utf8 scripts/catrina_enclosure_audit.py --poses <session>/physics-audit/catrina-rig-poses.csv`. Keep the exact atlas with the editable sources: its hash, sampled quadrilaterals and processing steps are recorded under `referencePaint` in the manifest. Original geometry follows the project license; no independent public redistribution license is asserted for the supplied artwork.

## Verification and visual acceptance

`build/la-catrina/asset-audit.json` records the serialized-asset hash, check count and individual results. Checks cover hierarchy, pivots, finite attributes, dimensions, texture/UV coverage, lamp counts, service clips and mirror/hash agreement. Specific regressions check **actual outward-facing pillar/end surfaces**, beyond agreement between normals and triangle winding, and ensure opaque backing caps cannot hide headlamp reflectors. These address defects visible in earlier renders.

Native linkage evidence is written to each session's `catrina-rig-audit.json` and 243-pose CSV. `build/suspension-playground/latest-audit.json` locates the last shared-physics audit; its executable and session must correspond to the result being claimed. The enclosure audit uses actual solved wheel transforms, 25 mm triangle-interior sampling and a 6 mm tire allowance. Its model hash, tested surfaces and outcomes are in `build/la-catrina/enclosure-audit.json`. This establishes sampled clearance for named surfaces, not exhaustive moving-component collision or real-world installation approval.

The frozen round-11 model passed the requested independent reference-sheet review gate: **reviewer A 8.020/10 and reviewer B 8.115/10**, without rounding up. Both reviewers compared the original sheet and all 16 native inspection views. `build/la-catrina/independent/accepted-model.json` binds their separate reports and the capture receipt to model SHA256 `8444acaabf320f15fc3157342f4d23baa0b03b701d99af365608f48c4c16cb3e`, geometry SHA256 `3a34f488900e3ef36348753b32e570ef52c9c2b3ef0deaf89f79ab1eb25d1d3f`. This accepted asset has 746,922 triangles, 242 mesh draws and eight embedded images; all 83 serialized checks pass.

This is a narrow static appearance pass, not visual identity with the sheet. The reports retain coarse ornament and pebbled close-up paint grain, angular trim/corner transitions, simplified upholstery/dashboard detail and broad mechanical-cover surfaces as visible limitations. Fine seams and spokes are also limited by the unchanged 960×600 inspection resolution. Mechanical, motion, audio and human handling acceptance are separate. A changed asset requires a new matching review; an earlier score does not transfer automatically.
