# La Catrina

A candy-pink hydraulic coupe based on the supplied La Catrina reference sheet.
It uses the same driving physics as the other vehicles and can be selected in
both Mercer City Block and the Vehicle Tuning Playground.

The vehicle picker on `main` includes Safari, Original buggy, Baja 427 and
La Catrina. The [review evidence](docs/la-catrina/review/README.md) includes
the original evaluation records and the checks performed on the `main` build.

The frozen round-11 model earned **8.020/10 and 8.115/10** from two independent
reviewers comparing the original sheet and 16 native inspection views. This
meets the requested 8/10 static visual gate. The reports still identify coarse
close-up paint/ornament, angular trim transitions and simplified small details;
the pass does not claim a perfect match or human handling acceptance.

Watch the **48-second street film** at
`videos/la-catrina-street-show/outputs/La-Catrina-Street-Show.mp4`.
The MP4 and editable ZIP stay on the workstation. For the six local clips used
by the checked-in film project, see [Restoring the street film](videos/la-catrina-street-show/LOCAL-MEDIA.md).
It uses verified native city footage for front hopping and both three-wheel
glides at 960×600 / 30 FPS. Engine and pump sound is editorial reconstruction
from credited real recordings; the simulator capture itself is silent.

Open **Launch-La-Catrina.cmd** and choose:

1. **Drive the city** — manual driving and hydraulic switches.
2. **Watch the street show** — a slow city cruise cycling through front hops
   and both three-wheel stances.
3. **Suspension playground** — compare it with the other vehicles on the test pad.

Sessions retain the existing five-minute limit; open the launcher again for
another session. Escape exits.

| Control | Action |
| --- | --- |
| W / S | Throttle / brake |
| A / D | Steer |
| Space | Handbrake |
| G | Reverse |
| J | Front-hop cycle |
| K / L | Left / right three-wheel stance |
| U | Raise all four corners |
| N | Return to low cruise |
| F | Toggle the repeating hydraulic street show |
| R | Reset vehicle |
| C | Change camera |
| O | Orbit camera |
| H | Show or hide controls |
| P | Pause |

The **Hydraulics** menu offers the same switches. **Block tour** enables
automatic driving. **Open hydraulic bay** opens the trunk for inspection.
For the closest exterior view use **Street & sky** or the orbit camera.

Hydraulic pressure changes the spring-seat load. The chassis lifts through
tyre contact forces, then falls and lands under gravity. Three-wheel motion
uses asymmetric corner loading. The model is rear-wheel drive; an unloaded
tyre cannot supply grip. At higher road speed the hydraulics return low.

This is an estimated game suspension using raycast tyres, with rigid visual
links and a linked rear axle. It is not a full multibody hydraulic or tyre
simulation. Human judgment of handling and sustained performance remains pending.

Real component references inform the stamped-steel arms, supported hydraulic
rams, separate dampers, wire wheels, narrow rubber whitewalls and plum vinyl.
The frame routing, travel and many dimensions are custom game choices, with
their limits in `docs/la-catrina/REAL-WORLD-BASIS.md`. The roof, hood and trunk
paint and side-scroll mask contain transformed artwork from the supplied sheet;
the geometry is original. Public redistribution rights for that artwork are
not independently established.

The portable model is `asset-library/models/la-catrina/la-catrina.glb`.
Its source generator is `scripts/catrina_generate.py`; rig and hydraulic
adapters are in `showcase/CatrinaRig.hpp` and `showcase/CatrinaHydraulics.hpp`.
Run `Build-La-Catrina.ps1` to regenerate, audit, build and sign the local
playground through the established workflow.

Exact model acceptance and native evidence are recorded in
`docs/la-catrina/HANDOFF.md` and `build/la-catrina/native-review.json`.
Archive and fresh-source rebuild evidence belongs to
`build/la-catrina/delivery-receipt.json`; its model hash must match the accepted
artifact before it is used as verification.
