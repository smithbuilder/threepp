# Round 11 independent mechanical source geometry review

PASS — scoped sampled source-geometry review

Previous scoped mechanical checks independently rerun, plus exact coplanar-aware checks of revised ram-cover/wheelhouse blisters, arch/inner-apron skins, front end curtains, rail notches and tapered tower posts against actual fixed steel, ram/spring/seat motion, tyres, front wishbones/dampers and lid sweeps. Fixed tower-to-frame joints remain intentional load-path connections.

Source hashes unchanged: True. Pose hash unchanged: True.
Actual geometry: 3828 parts, 746922 triangles.
Updated surfaces: 671 parts; fixed steel: 298 parts.
Tyres: 972 rows / 243 native poses / 216 unique wheel transforms.
Original collision categories: 0; new exact triangle collision categories: 0.
Frame connectivity: 198/198 ram load-path parts reach modeled boxed rails.
Closed inner-lid vertical gaps: hood 14.971 mm; trunk 5.447 mm (within each lid's X/Z interpolation domain).

## Exact inputs

- `scripts/catrina_art.py`: `e56d7204a21c93ce2989e19bae0668aeb69db332dcc2fc2419d71f5fdf15be2f`
- `scripts/catrina_hardware.py`: `1e199514bf3678746439f168e87d4975abb511889560973df541a2d6d8802c18`
- `scripts/catrina_frame_pockets.py`: `58fc2e937c539f043d15fd4e54aafbdc41fc903f1a6b24ac9e473344ac4dee42`
- `showcase/CatrinaRig.hpp`: `fb4332956f75abccc533cf148215c72ba0b066493e3e7c6e13e10ac25d3b0efd`
- `scripts/catrina_generate.py`: `ea4d28489f2593ea7b2c480ca6625af7c73190c6579f325388073c785357f675`
- `scripts/baja427_generate.py`: `bde8456127da209318026ef8429563caee69ca27a9a8fcd354c1ba877afff70f`
- `scripts/catrina_reference_paint.py`: `b8265fc433b66139ddf4d3882b3700a2647b8462caaef982c05c22415cf57b1c`
- `build/sessions/20261106-101153-431/physics-audit/catrina-rig-poses.csv`: `6a385c98cca03763e041ac5c5842b62f5d16b0c80ba93c02935d6df6036f3604`

## Method

- Construct final M.parts in memory using catrina_art.install, shell, roof_and_glass, front_rear, interior, gear, trunk and catrina_hardware.add_hardware. No exported GLB, temporary audit marker, or author-reported PASS is used as collision geometry.
- Transform actual indexed mesh vertices with the complete authoring node hierarchy. Reconstruct moving assemblies from CatrinaRig.hpp conventions and native hub CSV; remove the known 0.6-radian rear wheel spin before deriving rear axle orientation.
- Use all 81 distinct left/right suspension pairs from 243 native steering poses. Front hub heights span -0.120 to 0.420 m; rear hub heights span -0.280 to 0.420 m. Steering-only duplicates do not alter the tested spring, ram, link or damper poses.
- Evaluate hydraulic commands 0, 0.29 and 0.58 with the actual signed cup stop, rigid barrel/rod/cup and rigid lower-seat transform. Spring mesh local Y alone follows spring length. Barrel and rigid lower seat need one test per suspension pose because their pose is independent of hydraulic command.
- Prune mesh pairs and edge/triangle pairs by AABB, then test non-coplanar segment/triangle intersections in both directions. Determinant tolerance is 1e-11; barycentric and segment parameter tolerance is 1e-6. Checks report actual surface crossings, not an arbitrary inflated marker envelope.
- Test all actual rear axle, rear lower/upper/Panhard links and both rear damper barrel/rod assemblies against all new rear frame casing parts across the same 81 suspension pairs.
- Build an adjacency graph from actual intersecting fixed ram structural and pin meshes, seed the actual boxed rails, then require every tested ram load-path part to reach a rail.
- Test fixed ram/frame steel against enclosure skins, closed lid vertical gaps within each lid domain, actual parcel shelf intersections, and actual hinge-owned lid parts at nine opening angles per lid.
- Independently test exact bracket triangles against front bush sleeves and formed arms with a coplanar-aware triangle separating-axis test. Axes include both face normals, all nine edge cross products, and each face's in-plane edge normals, with 1e-8 m projection tolerance.
- Test front-arm-owned actual meshes against both driveline.exhaust and engine.exhaust_collector at 65 evenly spaced front hub heights from -0.120 to 0.420 m. Test the exhaust against actual new frame casings, boxed rails and spring-pocket support geometry.
- Capture hashes before authoring and after all tests; require unchanged source files.
- Repeat the original checks from their runnable reproducer against freshly constructed current geometry; previous PASS values are not inherited.
- For changed cover/liner/arch/curtain/notch surfaces, apply the coplanar-aware triangle SAT to actual fixed steel, all sampled ram/coil/seat poses, actual tyre meshes transformed by the native spin-node quaternions, front arms/dampers at 65 heights, and both lids at nine angles. Part AABBs only prune candidates; every reported contact is an actual triangle pair.
- All 972 wheel rows from 243 native commands are represented; exactly repeated wheel transforms are deduplicated without dropping unique steering/articulation combinations. No tyre cylinder or inflated marker substitutes for the actual tyre mesh in these additional checks.
- Round 11 expands the coplanar-aware target list to the actual engine/trunk wheelhouse skins, curved front apron edge skins and every tapered ram member (posts, rail feet, risers, header crossbars and header sides). All are checked against actual tyres, spring/ram/seat transforms, front arms/dampers and hinge-owned lid meshes. Fixed steel is checked against the skins; member-to-member welded joints remain in the independent rail-connectivity graph.

## Intentional contacts excluded

- Hydraulic spherical inner-ball/outer-race fit is intentional. The inner ball is omitted from the moving/fixed rejection set; actual fixed transverse pins and spacers remain included.
- Cross-shaft and fastener seating on frame support tabs is intentional. Their bracket contacts are excluded; actual bush sleeves and formed-channel arm surfaces are tested without the frame owner's attachment-region mask.
- Coils attach to their own moving cup/seat and the tested arms attach to their own joints; intended assembly interfaces and cosmetic fastener contacts outside the stated scope are not treated as collisions.

## Limits

- Finite sampled source-geometry check, not a proof for every continuously varying or independent four-wheel state.
- General crossing checks detect non-coplanar surface intersections. Dedicated bracket SAT also handles coplanar triangle contact; the report does not claim a general solid-containment or watertightness proof.
- Ram-to-rail graph proves geometric connection to the modeled rails, not strength, fatigue life, manufacturability or roadworthiness.
- Previously reviewed unchanged driveline slip and damper articulation mechanics are not re-certified here. The new casing checks include actual rear dampers and link motion.
- No visual quality score or manufacturing certification is provided.
- Actual-tyre triangle tests in this report cover the listed changed surfaces. Broader serialized-model enclosure sampling and exported/baked asset/native-executable identity remain separate root-agent gates.
- Exact triangle SAT includes coplanar surface contact; it does not establish a general watertight solid-containment proof or a positive minimum separation for every pair.
- Nine lid angles and finite suspension/steering samples are diagnostic samples, not continuously swept collision detection.

## Reproduce

```powershell
python -B build/la-catrina/independent/round-11-mechanical-check.py
```

Script SHA256: `8e07402ad7311676e4b7b8c433ff7390905ea80e839a90075c01d4770f0db722`

Full pair counts, sample counts, source hashes before/after, collision findings and scope are in the companion JSON.
