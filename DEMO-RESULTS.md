# Resumed demo evaluation

November 1, 2026. Launch `Explore-Examples.cmd` for the five conservative profiles.
Each interactive session lasts up to 60 seconds, at 960 x 600 and at most 30 FPS.
The supervisor, memory limit, heartbeat and failure lockout remain active.

| Demo | What it demonstrates | Resumed result |
|---|---|---|
| Engine Playground: Orbital Foundry | Animated instancing, polished metal, environment reflections | Captured; clean exit |
| Engine Playground: Tidal Outpost | Reflective animated water, generated wave normals, sky, moving boat | Captured; clean exit |
| Engine Playground: Little Woodland | Procedural tree geometry and bark/leaf textures | Captured; clean exit |
| Timber Run | Original car and forest loop, chase camera, wheels, dust, checkpoint HUD | Automated short drive captured; clean exit |
| Upstream materials showpiece | Imported car, PBR materials, transmission, instancing, coloured lights | Captured with expensive effects disabled; clean exit |
| Upstream tree workshop | Seeded tree generation and procedural textures | Captured; clean exit |
| Upstream forest | Terrain, instanced trees, wind-driven grass, flowers, shrubs | Captured with reduced density; clean exit |

The final observed working sets for the upstream tree, forest and materials
captures were approximately 121, 213 and 181 MiB respectively; the final driving
capture was approximately 95 MiB. These are sampled process working sets, not
GPU-memory measurements or performance benchmarks.

No new Windows unexpected-reboot or display-driver-reset events were found
during this resumed pass (checked from 18:03 Pacific). No demo was left running.
The selected native build and the supervisor's CPU-only cleanup self-test passed.

One launcher defect was found: the tree/forest backend option overwrote capture
arguments. The application idled until its bounded deadline. This was fixed,
and the corrected capture passed. The supervisor now rejects a capture request
if the expected image file is absent, even if the process returns zero.

Current screenshots and individual stdout/stderr/result records are retained
locally under `build/sessions`, including:

- `20261101-180913-126`: sculpture
- `20261101-180914-912`: water
- `20261101-180916-036`: woodland
- `20261101-181010-165`: driving
- `20261101-180843-938`: materials
- `20261101-180822-861`: tree
- `20261101-180830-999`: forest

These short captures do not establish long-session system stability or physical
keyboard/controller feel. The editor and the standalone upstream water program
remain outside the default validated list. Earlier full-effects captures and
the earlier full scripted lap are not current stability evidence.

The original demos are small engine studies. They are below the authored Dune
Buggy game's production scope; matching it would require a dedicated playable
slice and further art, motion, sound and handling work. The Reddit clip itself
could not be watched because its player/media access failed; only its post text
was read.
