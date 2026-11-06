# Current Baja 427 — mechanical v3

See [the current checkpoint](HANDOFF-MECHANICS-AND-RACE-V3.md) and [mechanical changes](MECHANICAL-V3.md). Current portable GLB/manifests/import notes: `asset-library/models/baja-427`; independent ZIP and native mechanical views: `build/baja-427-v3`. `CPU-AUDIT.json` now describes the v3 asset. The first-candidate modeling notes below are preserved history; their old counts, hashes and rig details are superseded by the library manifest.

---

# Baja 427 first vehicle candidate

Original local geometry and paint based on the supplied Baja 427 reference atlas.
No paid generation service, imported mesh, copied reference pixels, or manufacturer
logos were used. The asset is intended for a first in-engine trial and further art
iteration. The generator does not open a graphics context or audio device.

## Files

- `showcase/assets/baja-427.glb`: self-contained glTF 2.0, including both textures.
- `showcase/assets/baja-427.json`: dimensions, pivots, node/material names, counts,
  source/output SHA256 and stated limits.
- `showcase/assets/baja-427-livery.png`: original ivory/ochre/orange/vermilion paint
  and deterministic dust map, embedded in the GLB.
- `showcase/assets/baja-427-roundel.png`: authored 427 number roundel, also embedded.
- `scripts/baja427_generate.py`: reproducible CPU-only NumPy/Pillow generator.
- `scripts/baja427_audit.py`: serialized-file geometry/hierarchy/image audit.
- `docs/baja-427/CPU-AUDIT.json`: audit of the current GLB identity.

The reviewed-correction candidate is SHA256
`62c0feb64f2c0a7584df86442004ed9d013ea3c3b011f35c642c7e300ccaf6f3`.
It contains 199,892 triangles, 168,166 vertices, 103 batched mesh draws and 135
nodes in an 8,223,864-byte GLB. The two embedded maps decode to 3 MiB RGBA8.
The six complete wheels contribute most of the geometry. Tread blocks, bolts,
grille cells and coil turns are batched by parent, material and semantic group.

## What is included

The extended cab has a crowned roof, sloping windscreen, framed side and rear
glazing, seats/dashboard, wipers, side mirrors and visible door seams. The hood
has a raised center section and side vents. The continuous lower side panels
contain real open wheel arches with thick dark flares and rim hardware.

The open cargo bed has floor ribs, wheel tubs, rail caps, a hinged tailgate, twin
spare-wheel cradles and orange tie-downs, a tool case and traction boards. The
front carries tubular bumpers, a grille lattice, C-shaped light strips, amber
markers, guarded rally lamps, a perforated skid plate and red recovery shackles.
Rear light groups, receiver, bumper, ladder frame, driveshaft and exhaust are
separate from the live axle. Each of the six wheels has an authored tyre carcass,
three tread-block rows, sidewalls, a bronze rim/barrel, open spoke gaps, beadlock
bolts and lug nuts.

## Coordinate and rig interface

Metres, +Y up, +Z forward. Model root is `baja427`; `body` is its child. Place the
root at Y=0.07 for nominal level ground. The 0.94m tyres have small 1.5mm tread
protrusions below nominal radius, so their actual lowest point then lies at
Y=-0.0015. Ground alignment is a geometric check, not contact physics.

Wheelbase is 3.18m. Front hubs are `[-1.025,0.40,1.59]` and
`[1.025,0.40,1.59]` in body coordinates. The rear axle origin is
`[0,0.40,-1.59]`, with rear hub translations X=-1.025 and +1.025 relative to it.
The roof reaches 1.955m above nominal ground. Actual overall bounds, including
mirrors and rally-lamp guards, are 2.82m wide and 5.266m long. The reference's
5.10m overall target was approximate; bumper hardware adds about 0.17m.

| Group | Parent | Operation |
| --- | --- | --- |
| `wheel.FL.steer`, `wheel.FR.steer` | `body` | Rotate Y for steering; translate the group for travel |
| `wheel.RL.steer`, `wheel.RR.steer` | `rear_axle` | Follow the rigid axle; retain zero steering |
| `wheel.FL.roll`, `wheel.FR.roll`, `wheel.RL.roll`, `wheel.RR.roll` | Corresponding `.steer` | Rotate local X for tyre/rim spin |
| `rear_axle` | `body` | Translate for heave and rotate local Z for articulation |
| `tailgate.hinge` | `body` | Rotate local X from 0 to approximately -1.45 radians |
| `spare.L.steer`, `spare.R.steer` | `body` | Remove/hide complete spare wheels; keep their authored tilt |
| `cargo.spare_tiedowns` | `body` | Hide both orange wheel tie-downs and ratchets when unloading the spares |
| `front.L.lower_arm`, `front.L.upper_arm`, `front.R.lower_arm`, `front.R.upper_arm` | `body` | Separate control-arm pivot groups; exact original endpoints in JSON |
| `front.L.coilover`, `front.R.coilover` | `body` | Separate eye-origin coilover groups |
| `rear.L.spring`, `rear.R.spring`, `rear.L.damper`, `rear.R.damper` | `body` | Separate original spring and shock groups |
| `rear.L.lower_link`, `rear.L.upper_link`, `rear.R.lower_link`, `rear.R.upper_link`, `rear.panhard` | `body` | Separate locating-link groups |

Rig group names are unique. Static batched mesh names may repeat under different
wheel/suspension parents; retrieve moving groups by their exact group name.
Transforms on a `.roll` group affect tyre, rim and hardware together. Do not spin
the `.steer` group around Y as an approximation for wheel rotation.

The tailgate pivot is `[0,0.71,-2.407]` in body coordinates. Negative X rotation
lowers its top edge toward the rear. Tailgate geometry includes its inside ribs,
top rail, handle and hinge barrels. The rear lamps stay with the bed sides.

Materials whose `emissiveFactor` can be toggled are
`baja427.headlamp_emission`, `baja427.amber_emission`,
`baja427.taillamp_emission` and `baja427.rally_lens`. Emissive surfaces do not
create actual point/spot lights. Glass is alpha blended; the engine should turn
off depth writing on transparent materials, as in the existing Safari loader.

## Rebuild and validation

Use the existing actual Python interpreter with NumPy and Pillow. On this box:

```powershell
& 'C:\Users\oliver\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe' -B scripts/baja427_generate.py
& 'C:\Users\oliver\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe' -B scripts/baja427_audit.py
```

Generation also reads the installed `C:/Windows/Fonts/arialbd.ttf` font. A machine
with a different font path must point this one line at an equivalent bold font.
No font binary is copied into the asset. Regeneration replaces only `baja-427*`
outputs; do not regenerate during a native review whose evidence is tied to the
previous asset hash. The parent owns guarded native runs, signing and launchers.

The serialized CPU audit passed finite attributes, valid index ranges, normalized
normals, nondegenerate triangles, outward winding consistent with normals,
moving-part hierarchy/pivots, embedded PNG decoding, output hash/count parity,
draw/triangle budgets and level tyre alignment. A source regression also confirms
that the segment-to-basis helper does not modify the caller's length vector.
It opens no graphics context.

The first native review caught long floating strap ends and a rear pane rendered
against a solid painted wall. The correction copies the vector before basis
normalization, uses each true strap segment length, constructs an actual framed
rear-window opening, darkens glazing, and gives both wheel tie-downs their own
removable group. The front skid was also changed from thin webs to a broad sheet
with eight genuine round bores. The corrected GLB identity above supersedes the
first candidate for future engine trials.

A final native front review found missing skin between the bonnet and fenders
and above the windscreen. Painted shoulder strips now connect the side panels
to the bonnet with a narrow 4mm seam, a front brow closes the bonnet-to-fascia
edge, and a crowned painted header joins the upper windscreen edge to the exact
leading roof curve. The asset hash and audit above include those closures.

## Remaining limits

This is a first real-time art candidate. Paint has deterministic dust specks;
it has no photographic damage atlas, baked ambient occlusion or normal map.
Suspension groups represent the architecture in the sheet, but their travel and
steering envelopes have not been collision checked and they do not implement
complete kinematic closure. The Panhard rod is correctly separate with one
chassis endpoint and one axle endpoint; any articulation animation must update
its axle endpoint and preserve length rather than rotate the whole rod with the
axle. The front upright/steering link details and interior controls are simplified.

The GLB contains no animation clips or driving physics. Native appearance,
lighting, link motion under articulation and user handling need the separate
engine trial. A successful CPU audit does not establish those outcomes.
