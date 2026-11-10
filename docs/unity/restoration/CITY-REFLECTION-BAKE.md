# Fixed local Mercer reflection bake

November 9, 2026, Pacific Time. Implementation lane, not an independent quality verdict.

`CityReflectionBake.Run(repositoryRoot)` builds a fixed city environment entirely on the CPU during the guarded Unity build. Call it after the faithful Mercer import, `NativeCityMaterials.Configure(root)` and `CinderSkyBake.Run()`, before the source manifest is frozen.

It creates a temporary additive editor scene and adds mesh colliders for all 26 faithful static city meshes on reserved layer 30. It refuses to bake if an existing active scene collider already uses that layer. Queries use only layer 30 in the default editor physics scene; no physics scene is simulated. Rays start at `(-31, 0.85, 65)` metres. The 512 x 256 linear floating-point panorama contains 131,072 rays. Native albedo, interpolated vertex shade, interpolated mesh normals, material colour/metallic factor, emission, alpha cutoff and the original HDR sky determine each sample. Cutout holes continue the ray; a 64-layer limit is counted. The work loop has a 140-second CPU deadline.

The output is `Assets/Resources/Cinder/city-reflection-filtered.exr`, imported as a 128-pixel specular-convolved HDR cubemap. The canonical panorama follows the Skybox/Panoramic longitude convention. The importer-facing pixels receive the measured -0.25 U correction for Unity's cylindrical cubemap convention. Six cardinal diagnostics compare the original panorama against the imported cube; this reports errors rather than assuming orientation equivalence. Sky misses use the same native inverse rotation as the visible sky bake. The city sign material's localized U correction is also applied when sampling its albedo.

`city-reflection-bake.json` records exact source hashes, probe origin, lighting values, ray/hit/cutout counts, maximum linear radiance, elapsed time and output hash. It explicitly records that the algorithm uses no GPU rendering and does not change simulation physics. Temporary scene objects, CPU-decoded images and global backface-query state are restored or released in `finally`.

At runtime, use the cubemap in a bounded `ReflectionProbe` in Custom mode, with box projection and the recorded origin. No `RenderProbe` or realtime refresh is required. The sky environment should remain the fallback outside the local volume. Clearcoat sampling must apply the same box-projection correction as the base reflection path.

This is an approximate single-bounce diffuse environment, not a matching implementation of the full Unity renderer, recursive GI or a measured photograph. It does not evaluate normal-map bump, reflected specular, transparent transmission or the car itself. It adds no invented light cards or artificial brightness boost. It cannot establish that Nocturne's finish is repaired before the new signed player is inspected.

Offline C# compilation passes. The first guarded r13 attempt exposed that Unity disallows creating a local-physics scene outside Play Mode. The implementation now uses an additive editor scene with layer-isolated queries and no simulation. A fresh guarded build must verify that path and the corrected cubemap import; final player images and movement remain the visual acceptance gate.


## Final disposition

This experimental local reflection is not the normal r24 player lighting. r13/r14 failed offline scene setup; r15 completed the CPU bake, but actual local-reflection comparisons darkened the cars and were rejected. It remains an opt-in diagnostic behind explicit flags. The published prototype uses corrected native sky lighting, native sun extraction and calibrated SH/reflection units. Do not treat this approximation as a successful final visual fix.
