Current mechanical v3 repair and three-vehicle film: [November 5 checkpoint](docs/baja-427/HANDOFF-MECHANICS-AND-RACE-V3.md). Portable model: `asset-library/models/baja-427`. Package and mechanical views: `build/baja-427-v3`. First-candidate details below are history; current counts/rig interfaces are in the library manifest.

# Baja 427 first vehicle candidate

Open [Launch-Baja-427.cmd](Launch-Baja-427.cmd) to try the separate native engine
test bench. The session closes after 60 seconds; Escape exits sooner.

The subagent authored the model locally from Oliver's supplied vehicle atlas.
It includes the ivory/ochre/vermilion livery, 427 roundel, six bronze-rimmed
off-road wheels, open cargo bed, spare carrier and straps, recovery gear,
tube bumpers, perforated skid plate, lights, and separate suspension parts.

This is a usable first art candidate with simplified, angular bodywork. It does
not match the reference's photographic finish. The bench exercises its moving
parts; the truck has no driving controller or complete suspension simulation yet.

## Try it

- Drag to orbit and scroll to zoom. Front, Side, Rear and Bed buttons change view.
- Steering slider turns the front wheels; Roll wheels or Space spins them.
- Tailgate slider or T opens the rear gate.
- Lights checkbox or L toggles emissive lamp surfaces.
- Bed spares hides both spare wheels and their tie-downs, leaving the carrier.
- H hides the controls; R restores the starting camera; Escape exits.

The launcher uses the existing 960x600, at most 30 FPS, 2 GiB process job,
BelowNormal priority, single-process guard, heartbeat and deadline. No graphics
limits were raised. The new executable is signed through the existing local
review workflow. No publication or installation was performed.

## Reusable asset

- [Self-contained GLB](showcase/assets/baja-427.glb)
- [Dimensions, materials and pivot manifest](showcase/assets/baja-427.json)
- [Modeling and rig guide](docs/baja-427/README.md)
- [Serialized geometry audit](docs/baja-427/CPU-AUDIT.json)
- [Native inspection package and previews](build/baja-427)

The GLB is 8,223,864 bytes, with 199,892 triangles, 103 batched meshes and two
embedded textures. Coordinates use metres, +Y up and +Z forward. The supplied
manifest records wheel, axle, tailgate and other joint locations. Place its root
at Y=0.07 for nominal flat ground. The tread extends another 1.5 mm below that
nominal alignment.

Final asset SHA256:
`62c0feb64f2c0a7584df86442004ed9d013ea3c3b011f35c642c7e300ccaf6f3`.

## Verification and limits

The serialized CPU audit passes finite attributes, index ranges, nondegenerate
triangles, winding, hierarchy, pivot names, texture decoding, geometry budgets
and static tyre alignment. A second audit loads the exported file through the
actual threepp GLTFLoader, checks dimensions and wheel placement/orientation,
and exercises steering/spin pivots, tailgate rotation, lamp toggles and cargo
visibility before creating any graphics or audio context.

Seven final guarded native captures cover front, side, rear and bed views plus
steered/spinning wheels, open gate, lamps off and removed spares. All exited 0;
their stderr logs are empty. The spinning-wheel take evaluates 30 native frames.
A ten-second run of the normal interactive launcher profile also exited cleanly
at its deadline. Physical input and subjective user acceptance remain untested.
Source sessions and exact executable/model identities are retained in
`build/baja-427/verification.json`. These are asset checks, not user acceptance
or proof of long-session performance.

Front control arms, coilovers, rear axle, springs, shocks and links are separate
groups. Their complete kinematic closure and steering/travel clearance remain
unverified. The bench does not expose suspension articulation. Lamps are
emissive materials without projected beams. Interior controls are simplified,
and the GLB has no animation clips. The current Safari and its executable,
assets, driving behavior and launchers were preserved.

## Build

Build only the `baja427_preview` target in `build/windows-gl`, Release, with two
workers. Its post-build step copies the GLB into the isolated `baja427-assets`
runtime folder. A changed executable must be signed using the established
review workflow before execution on this machine.

CPU-only native asset check:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ./Run-Evaluation.ps1 -Example baja427_preview -PhysicsAudit
```

Guarded still inspection:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ./Run-Evaluation.ps1 -Example baja427_preview -Capture -Frames 1 -View 0
```

View 0/1/2/3 selects front/side/rear/bed. Scene 1 is the complete default truck;
Scene 2 steers and spins the wheels, opens the tailgate and turns off emission;
Scene 3 removes the spares/tie-downs and opens the tailgate. Never bypass a pause
marker or run the executable directly for graphics checks.
