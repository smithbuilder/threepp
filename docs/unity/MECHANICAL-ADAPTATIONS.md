# Unity mechanical adaptations

November 9, 2026, Pacific Time. These are explicit Unity view adaptations. The original donor files and the deterministic vehicle simulation remain unchanged by these corrections.

## Media Luna rear leaf installation

The loaded r3 mechanical gate found a real geometric incompatibility in the donor installation at the legal rear droop endpoint, with both rear hub heights at 0.24 m. The rear axle saddle, fixed front leaf eye and fixed rear shackle bracket could not close the original leaf centreline chord with the original shackle length. The inherited donor presentation code clamped its circle intersection and left a 0.00665462 m loaded chord discrepancy. An independent double-precision calculation measured the infeasibility as 0.00665478 m.

For that pose the rear chord target is 0.64503465 m. The original shackle circle permits a minimum saddle-to-eye distance of 0.65168943 m. No choice of its existing angle can close that gap.

The Unity adapter relocates each fixed rear shackle pivot forward by 0.010 m along model +Z. The pivot locations change from `(±0.50, 0.42, -2.20)` m to `(±0.50, 0.42, -2.19)` m. The existing 0.08 m mounting bracket is batched into the frame mesh and remains unchanged; the corrected pivot lies inside its existing volume. Both rigid shackle members retain their original 0.12041595 m length. The original leaf centreline chord remains the constraint; each rendered rear leaf eye follows the solved shackle eye and the front eye stays fixed on the frame. No chassis position, axle motion, tyre contact, spring rate, hydraulic input or simulation state is changed by this view correction.

The implementation is `LunaLeafBracketCorrection` and `PoseLunaLeaf` in `Unity/Assets/Cinder/Scripts/View/RigMechanisms.cs`. It changes instantiated Unity meshes and transforms only. The C++ donor, source GLB, source generator and imported prefab asset remain available without this installation correction.

The loaded gate retains its 0.0002 m limits for leaf chord conservation, shackle length and modeled leaf-eye attachment. Both actual eye vertex populations must exist. The r3 failure evidence is retained. The corrected build requires a fresh loaded probe and independent review before acceptance.

## Nocturne bellows and roof

Nocturne uses 0.001 local scales to hide the authored roof and roof-lift casings at rest. The adapter restores those three scales to one before capturing bind coordinates, as the donor posing code does. Treating those hide scales as physical dimensions had produced incorrect roof target points. This correction changes visibility setup, not authored dimensions or mechanism lengths.

Bellows rubber is identified by its authored glTF part hierarchy as well as the source material name. Unity can replace a generated material object's name with its asset filename. The loaded gate therefore also requires a positive rubber-mesh count and nonzero lower and upper bearing-ring vertex samples for each of the four bellows. A zero-sample comparison cannot pass.

Flexible bellows, coils, leaf packs and roof canvas must preserve their attachment stations in every mesh-density tier. Their meshes are exempted from general collapse decimation; rigid body panels and other suitable parts can still use the normal density tiers. Every hero, mid and far lowrider prefab is checked independently by the loaded gate.
