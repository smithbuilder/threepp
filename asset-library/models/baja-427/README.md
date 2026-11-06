# Baja427 modular mechanical refinement v3

Self-contained glTF2.0 GLB, metres, Y up, Z forward. Static model root Y=0.07 puts nominal tyres on ground. Embedded PBR textures, no threepp dependency.

Receiver and recovery hardware now connect through frame brackets and a towing crossmember. Front steering uprights, wishbone pivots, shock towers/clevises, rear axle tabs/perches, separate brake rotors/calipers, transfer case and slip driveshaft are modelled. Wheel houses are hollow; spare carriers and straps fit the actual tyre geometry above them.

Wheel steer groups:wheel.FL/FR/RL/RR.steer; child .roll rotates around X. Front uprights:front.L/R.upright. Rotors:brake.FL/FR/RL/RR.rotor rotate around local X with their wheel; calipers stay fixed. rear_axle is a rigid housing.

Front.L/R.coilover and rear.L/R.damper have separate .body/.shaft children. Keep their metal lengths fixed; rotate the parent toward the lower eye and slide .shaft. Front coilovers also have .spring,.upper_seat,.lower_seat; only the spring changes axial length. Rear.L/R.spring has .coil/.upper_seat/.lower_seat. See rig.mounts and rig.dampers in the manifest for rest endpoints. Front upper/lower arms rotate as rigid wishbones. Driveline.shaft has driveline.slip; front.L/R.halfshaft has .slip.

Tailgate hinge rotates around X. Spare.L/R.steer and cargo.spare_tiedowns can be hidden together. New spring/link/rotor names are part of revision3; adapters for revision2 should update their lookup list.

Authored travel0.268–0.52m is restricted by mesh clearance. The supplied workbook proposes more travel; this model does not claim that range. The optional C++ presentation adapter and reduced force-based ride are under showcase/, separate from these portable assets. Five original PNG maps supplied beside GLB:base colour sRGB, packed G-roughness/B-metalness and OpenGL normal maps linear.

Mechanical verification records live in the project under build/baja-427-v3. This remains a game asset, with approximate elastic rear bushing articulation.
