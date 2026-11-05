# Safari suspension packaging

The closed Safari body now selects an explicit `SuspensionProfile::Safari`.
`addSuspension` defaults to `Legacy`, retaining the original open buggy's
pickup points, geometry, materials and articulation. Vehicle dimensions,
contact dynamics, wheel travel and the 20 mm body/tyre pad are unchanged.

## Front

The previous top at `(±0.38, 1.14, 1.13)` was above the actual bonnet, whose
local height there is approximately 1.1069 m. The visible objects were damper
eyes, seats and reservoir hardware penetrating the body.

Safari's front eye is at `(±0.38, 0.94, 1.35)`. The actual bonnet at the new
centre is approximately 1.0609 m. The original 54 mm outer-radius eye remains
full size. Putting the top in the axle's plane also keeps its pin axis exactly
fore/aft while the lower wishbone moves; this is a physical mount relocation.

The existing lower-arm pickup fraction remains 0.78. Its fore/aft bridge
connects the two wishbone legs at that same fraction. The eye-to-eye range is
0.673668–0.808013 m, giving 134.345 mm damper stroke for 220 mm wheel travel.
The motion ratio varies approximately 0.560–0.671. An 18 kN/m effective wheel
rate corresponds to roughly 40–57 kN/m at the coil with that leverage. This
is a leverage estimate; the visual coil is not an independently calibrated
material/unsprung-mass solver.

The fixed barrel is 420 mm long, beginning 120 mm from the upper eye. Its
shaft begins at local Y=0.54 m. The 134–268 mm eye-referenced extension includes
a 60 mm lower eye/stem allowance, leaving 74–208 mm exposed polished shaft.
The spring
and upper seat begin at Y=0.14; the lower seat remains 100 mm above the lower
eye. The shortest coil span is about 434 mm, giving roughly 62 mm pitch for
the unchanged seven turns and 24 mm wire diameter. The piston insertion,
seal/lower-seat space and coil-bind margins are checked across the full range.

Two rails continue from the existing rear hinge crossmember to the front
wishbone brackets. Fore/aft tower legs meet an inboard upper node; paired
gussets connect that node to actual clevis ears outside the bearing bore.
The support does not terminate through the eye's centre. The unshrunk pin,
spherical bearing and open-bore ear plates form a real attachment.

## Rear

The original rear routing crossed the flat cabin floor. A longer barrel alone
could not solve that. The body lane owns real floor apertures and sealed
shock-tower/wheelwell tunnels behind the seats; no draw-order hiding is used.

The upper eye remains `(±0.38, 1.14, -1.20)`, and the trailing-arm station
remains 0.78. A supported 60 mm inboard saddle on its crossbridge moves the
right lower eye to X=0.82 m, preserving the original Y/Z trajectory. The
right-foot equations are:

```
x = 0.82
y = 0.36 * 0.22 + (travel - 0.10) * 0.78
z = -0.30 - 0.78 * sqrt(1.05^2 - (travel - 0.46)^2)
```

The eye range is 0.872330–1.024406 m, or 152.077 mm stroke. A fixed 580 mm
barrel runs from local Y=0.12 to 0.70 m, leaving 172–324 mm eye-referenced
extension, or 112–264 mm exposed polished shaft after its eye/stem allowance.
The original 310 mm barrel could not contain the previous visible shaft.

At the actual correlated wheel poses, the conservative coil/seat envelope
has about 60.7 mm minimum clearance from the rendered rubber in the floor
region. This allows 20 mm motion/service room, a 5 mm tunnel wall and 20 mm
tyre room. A 40 mm saddle provided only about 44 mm, so it was rejected.
The test uses the actual revolved rubber profile and its empty rim interior,
rather than treating every point inside the rim as rubber.

The spherical upper bearing uses a fixed chassis pin. The lower clevis follows
the trailing arm; its bearing accommodates the remaining cone angle. Rear
tower struts tie the upper clevis ears to the existing rear frame rails at
X=±0.60, Y=0.38 and Z=-1.45/-1.05. The extension is connected to the actual
fork bridge with paired saddle braces.

## Hardware and validation

The Safari reservoir is mirrored outboard. It has a 280 mm body centred at
local Y=0.30, with caps at 0.15/0.45. The fluid passage is at Y=0.17; preload
rings are at 0.155/0.185/0.215. These attach to the new barrel instead of
floating at the previous neck positions. Eyes, wire, spring radius and pin
dimensions retain their original size. A 90 mm upper neck connects each eye
to the new barrel start. The lower rod ends before the pin bore and joins a
welded eye neck, rather than running through the spherical bearing centre.

The frozen body-lane interface is
`build/safari-suspension/rear-envelope-v4-FULL-SURFACE.json`, including per-height
20 mm padded envelopes and exact clevis-ear support tube endpoints. It samples
complete cylinder surfaces at no more than 5 mm axial spacing, plus pins,
clevises and necks, across 221 travel positions. The earlier v3 export sampled
only cylinder end rings and omitted a reservoir midsection; the actual-mesh
test caught the resulting tower intersection and v4 supersedes that export.
Its
moving route is fixed while the matching body apertures are authored.

`SafariSuspensionTest.hpp`, invoked by `RallyVehicle_test`, samples actual
moving mesh faces at at most 20 mm spacing through 77 travel positions and
41 front steering positions. It checks actual body/floor/tower distances,
rubber clearance, piston insertion, coil bind, seat/seal margin, pin attachment
and bearing articulation. New fixed support tubes and clevis plates are also
checked against actual body triangles. Legacy/default geometry is checked
separately and the existing padded tyre/body tests remain intact.

These checks establish sampled geometric packaging, not stress certification,
physical manufacture or native visual acceptance. The rear tunnel mesh must
pass the same tests after the body lane delivers it.
