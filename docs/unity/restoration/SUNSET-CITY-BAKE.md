# Separate sunset city vertex bake

November 11, 2026, Pacific. Implementation note, not independent visual acceptance.

`CinderSunsetCityBake.Run(root)` reads the faithful daylight Mercer prefab and writes a separate `Resources/Cinder/Generated/mercer-city-sunset/mercer-city-sunset.prefab`. Its 26 meshes are cloned. Materials and textures are shared with the original city; original mesh and prefab assets are never assigned new data.

The original 383,961 triangles, vertex positions, normals, tangents, bounds, indices and existing UV channels are checked against each clone. Only vertex RGB and two previously unused lamp-data channels change. Source alpha is retained. The bake refuses meshes that already occupy UV channels 2 or 3. A source fingerprint binds the frozen GLB, original imported prefab/mesh files, frozen CityLayout/CityBlock headers and the editor implementation. Existing output is reused only for that fingerprint and complete unchanged geometry; drift or partial output must be preserved before a new bake.

## Static sun shade

The original `CityLayout.hpp::shade` function is ported using its eleven building boxes and original tree/contact positions. The original query biases are significant: native contact-ground vertices use `position + (0, .025, 0)`, while static native parts use `position + normal * .04`. The bake removes that old factor from vertex RGB, preserving the other authored material tint, masonry-foot AO, canopy variation and road-colour factors. It multiplies the recovered colour by the new static shade.

The new sun direction is normalized `(0.70, 0.20, -0.685)`. Five deterministic light directions approximate a small solar disk with radius 0.0047 radians: the centre weighs 0.5 and four surrounding directions weigh 0.125 each. Fully blocked building shade has a 0.62 floor. Native analytic tree-canopy/contact functions retain their positions and parameters, with the canopy centroid following the new sun direction. This is not exact per-leaf shadow geometry or a physically complete penumbra model.

## Lamp visibility channels

The eight fixed head positions use native order: X `[-23.7, 23.7, -44.7, 44.7]`, each with Z `[49, 85]`. A head is 1.35 metres outward in X from its post at Y 5.24. For every city vertex, a segment starts at `position + normal * .02` and ends at each head. Intersection with any of the eleven original building volumes gives zero visibility; otherwise visibility is one.

The first four values are stored in mesh UV channel 2 (`v.texcoord2`), and the remaining four in UV channel 3 (`v.texcoord3`), as float4 data. This adds 32 raw attribute bytes per vertex without adding vertices, triangles, textures, lights or shadow maps. The runtime city shader must consume the same head order. Existing UV0/material texture coordinates are unchanged.

These masks describe vertex-sampled building occlusion only. Interpolation can soften visibility over a large triangle. They do not prove dynamic car, bench, foliage or fixture self-shadowing and do not replace the existing vehicle shadow map.

## Receipt and limits

`sunset-city-bake.json` records source hashes, input fingerprint, sun and lamp parameters, exact counts/bounds, per-mesh shade statistics and visible/occluded vertex counts for all eight lamps. It explicitly records that original assets/materials are preserved and that shade is vertex sampled.

The adaptive visual ground was originally reduced against daylight colours. Retaining its triangles means a new sunset shadow edge is interpolated between existing samples; this bake does not claim a universal per-pixel sunset-shadow bound. The pure simulation/contact mesh and all lowrider assets remain unchanged.

Offline compilation against Unity 6000.3.6f1 passes with zero errors and warnings. Guarded execution, source/output inspection and actual player stills/motion remain required before acceptance.
