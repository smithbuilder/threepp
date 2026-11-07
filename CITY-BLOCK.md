# Mercer City Block

A compact warehouse district for reviewing the vehicles in an urban environment.
Open **Launch-City-Block.cmd**, or select **4. Mercer City Block** in
**Launch-Playground.cmd**. The first view is **Street & sky**, a low, wide camera
that includes the vehicle, facades, tree silhouettes and photographic sky. Choose
**Overview** to see the whole block, or **Chase**, **Front**, or **Driver's eye** to inspect scale
from the street. **O** enables the mouse orbit camera; **H** hides the controls.

The vehicle picker uses the shared playground catalogue. **W/S** are throttle and
brake, **A/D** steer, **G** changes reverse, **Space** is the handbrake and **R**
returns to the selected starting point. **Block tour** follows a slow route around
the central block using the normal tyres and chassis. It is a simple preview
driver with no traffic avoidance. Select Mercer Street, Motor Works or South
crossing to move between the three starting points.

The scene contains a central mixed-use block, eleven nearby buildings, four marked
intersections and distant city shells beyond the playable boundary. The realism
revision adds photographed brick/plaster/asphalt/bark, normal and roughness maps,
facades built around recessed glazing, varied curtains/blinds, window air
conditioners, a steel fire escape, chipped road paint and irregular asphalt repairs.
Street trees use three branching broadleaf prototypes with cutout leaf clusters,
textured bark and varied heights/orientations. Storefronts, roof equipment, grates,
streetlights, benches, hydrants, drains, manholes and parking bays remain modular.
All shop names are fictional.

Building envelopes and visible perimeter walls are solid. Streets and bevelled
16 cm sidewalks use the exact same sampled triangle surface for drawing and
physics. Small decorative objects, foliage, signs, awnings and window trim do not
have separate collision shapes. Buildings are closed shells; no interiors,
pedestrians, traffic simulation, changing signals, night mode or working
streetlight illumination are included. Glazing is opaque with reflections.
This is an environment prototype for judging scale and visual direction.

The skybox is a locally packaged 1K photographic HDR panorama. The same HDR
supplies material reflections, with its rotation and brightest sky patch aligned
to the sun and baked building shadows. Low hemisphere fill preserves the contrast
between sunny facades and shaded recesses. No assets download during play.

Static meshes are merged into 25 material batches, with 566,118 triangles in the
realism revision, including the contact grid, distant shells and broadleaf trees.
The existing 232,320-triangle contact grid is unchanged. Fixed building shadows and
soft tree/contact shading are baked into static vertices. The existing single
512-pixel vehicle-local shadow supplies the moving vehicle shadow; there is no
changing sun or street-wide dynamic shadow map. The existing 960 x 600, 30 FPS, 2 GiB process, single-session,
heartbeat and deadline limits remain. The launcher allows a five-minute session.

## Reuse and editing

- `showcase/CityLayout.hpp`: metre-scale building footprints, collision recipes,
  sidewalk shape and preview route; no renderer dependency.
- `showcase/CityBlock.hpp`: merged facade and street geometry, materials and props.
- `showcase/assets/city/`: portable JPG/PNG materials and source metadata.
- `scripts/generate-city-materials.py`: deterministic material generator, seed 427.
- `scripts/generate-city-details.py`: original chipped paint and pavement relief.
- `scripts/fetch-city-surfaces.py`: prepare/checksum eighteen 1K CC0 PBR maps.
- `showcase/assets/city/photo-surfaces.json`: image URLs, authors, licenses and hashes.
- `showcase/city-world.json`: world entry point and integration metadata.
- `showcase/PlaygroundTerrain.hpp`, `PlaygroundPhysics.hpp`: shared sampled
  contact surface and coupled vehicle solver.

Rebuild only `suspension_playground` with two workers, sign through the established
workflow, then run `Test-Suspension-Playground.ps1`. Native previews must go through
`Run-Evaluation.ps1 -Example suspension_playground -World city`. Read `SAFETY.md`
before native runs. Existing forest and suspension worlds retain their entry points.

Original verification and images are under `build/city-block/`. The realism/skybox
revision uses `build/city-realism/`; its baseline preserves the preceding source
and textures. Exact verification and preview results belong to each delivery receipt.

The original November 5 city build passed **137 CPU checks across four vehicles**, including
18 city checks: surface/solid agreement, supported spawns, a complete physical
tour, finite motion within bounds and chassis collision with a building. The
original 90 vehicle results were compared with the preceding checkpoint. The
new coupe required the travel check to use its separate rear-axle limits; the
wind response check now measures change relative to vehicle weight. These are
verification changes, not new city-specific vehicle tuning.

Native review covers the overview, a six-second Baja drive, and a front view of
Switchback in the city. Human handling acceptance and sustained performance
remain open. See the final receipt for exact executable, asset and session hashes.

The realism/skybox build also passed all 137 checks. Its final native review
covers the new Street & sky starting view with Safari, the overview and a
six-second Baja drive. The fixed resolution, frame-rate, shadow and process
limits remain unchanged. `build/city-realism/delivery-receipt.json` binds those
previews to the signed executable and licensed surface/sky assets.

The 24-second Safari city-drive video is local at
`videos/safari-city-drive/outputs/Safari-City-Drive.mp4`. It follows one continuous
physical drive through three camera views, with reconstructed driving sound.
Editable project, source captures and verification are beside it; the movie and
derived audio are excluded from Git.
