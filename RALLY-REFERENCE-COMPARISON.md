# Reference-led rally refinement

## What was actually inspected

The original Reddit video now plays in the connected Chrome browser. Reviewed
its early forest chase (approximately 6s and14s), rough corner18s, two-buggy
rear view33s and cockpit35s. Exposed suspension, tyre separation from body roll,
low spreading dust wakes and cockpit movement are useful visual targets.
The moving medium shots do not identify every pickup point or internal damper
setting. No claim is made to reverse-engineer its exact joint layout. The author
identifies PhysX Vehicle2 in a reply. Cinder uses its own reduced model.

https://www.reddit.com/r/TopologyAI/comments/1xlblst/

## Real references and decisions

| Reference | Evidence | Cinder implementation |
| --- | --- | --- |
| Polaris RZR Pro R Factory manufacturer specs | Front A-arms, rear boxed trailing arms, stabilizers, separate compression/rebound-controlled shocks | Keep front wishbones; give rear wheels a longitudinal trailing-arm arc, boxed fork and driveshafts |
| FOX bypass shock manual, pp2-3 | Reservoir/body/shaft hardware, distinct compression/rebound circuits, damping increases near travel ends | Add piggyback reservoir/adjustment rings, separate compression/rebound damping and progressive compression end zone |
| NVIDIA PhysX vehicle mechanical model | Per-corner suspension loads aggregate onto sprung rigid body; tire forces are a further model | Integrate heave/pitch/roll from four spring/damper forces; retain existing arcade horizontal handling |
| Original video | Low advecting dust wakes, readable exposed suspension | More fine dust, separate ballistic gravel and persistent contact-dependent tyre ribbons |

https://www.polaris.com/en-us/off-road/rzr/models/rzr-pro-r-factory/rzr-pro-r-factory-specs/
https://pvg-portal.ridefox.com/_context/fox/__uploads/_assets/605-00-097_REV_C.pdf
https://nvidia-omniverse.github.io/PhysX/physx/5.1.0/docs/Vehicles.html

These are game-art/engineering references, not real vehicle build instructions.
No branded CAD, photographs or manufacturer textures are shipped.

## Dynamic model and boundaries

620kg tuned sprung mass;18000N/m corner spring rate;1700/2400Ns/m compression/
rebound damping;2600N/m axle anti-roll coupling;540/460kgm2 pitch/roll inertia;
0.68m load-transfer lever. Fixed120Hz integration;0.52m open-buggy wheel
travel and0.22m Safari wheel travel, with separate dimensions per vehicle.
These are original gameplay tuning values, not measurements of the reference.
Spring loads release at droop; airborne wheels do not emit trails/spray. Travel
end zones add damping and progressive bump force. Hard bump projection is a
nonpenetration safeguard, counted in telemetry. Safari selects coupled heave/
pitch/roll contact projection and support-dependent input moments; the accepted
open buggy retains its Legacy response. Player controls remain unchanged.

The first native trial exposed a world/chassis torque-axis error; fixed before
delivery, with a regression that rotates the same flat-ground manoeuvre through
four headings. Displacement settling, weight-transfer direction, aggregate
static load, stationary30/120Hz equivalence, airborne release and landing are
CPU checked. The moving game advances through its own fixed120Hz accumulator.
Front wishbone and rear trailing-arm lengths stay constant throughout travel.

This is a three-axis sprung-body model with kinematic wheel contacts and rigid
tyres. It is not PhysX Vehicle2, an unsprung-mass solver, pneumatic tyres, real
friction/slip forces or crash/rollover physics. A tyre can now leave the ground;
positive gap is airborne travel, while negative gap measures penetration.

## Visual budgets

Original256px shared paint/metal/rubber albedo, roughness and normal maps,
about3MiB with mipmaps and no extra material draws. Missing custom UVs supplied.
Dielectric paint, dark coating, rubber and machined metal use separate settings.
Outdoor sky/ground replaces room-panel reflections; analytic sky matches the
single key light. Same512shadow map, focused20m frustum, light-space stabilization.
No extra postprocess, ray tracing or resolution increase.

Effects use fixed pools:192dust quads,64gravel instances,768tyre ribbon segments.
Dust advects/grows/fades; gravel follows gravity/bounces/expires; tyre marks stay
fixed to terrain and fade by32s. Reset clears all pools. GPU/memory/watchdog and
session limits remain mandatory. Scripted evidence is not physical acceptance.

## Second vehicle

The separate Safari coupe uses original geometry inspired by the rounded roof,
fastback and round lamps described/shown by Porsche. Its half-track is1.08m,
tyre radius0.49m and wheelbase2.70m, with shorter travel and separate suspension
packaging. These are original game-model dimensions rather than exact911
dimensions, handling or branding.
https://newsroom.porsche.com/en/press-kits/911-Dakar/The-design-and-the-interior.html

Rear packaging clarification: Oliver explicitly prioritizes realism over exact
reference specifications. The reference sheet guides style; its apparent combined
exhaust/undertray is not copied as an engineering assembly. The new rear revision
uses a separate engine/exhaust path, rubber-isolated silencer mounts, heatshield,
chassis-mounted protective bumper and serviceable engine bash plate. The plate
ends forward of the outlets. Pipes remain clear of wheel/suspension travel and
inside the rear bumper's projected extent. These are game-model packaging checks.
Porsche's [911 history](https://newsroom.porsche.com/en/press-kits/911-Dakar/The-history.html)
confirms the rear-engine architecture as general context; this fictional custom
buggy does not claim production Dakar dimensions or its suspension/powertrain.

Enamel detail uses an original built-in image_gen bitmap, sampled into authored
PBR atlases: showcase/assets/safari-enamel-wear-v1.png. Exact generation prompt
and source receipt are saved in the adjacent -PROMPT.md and -SOURCE.json files.
All review images and eventual driving footage are rendered by the game engine.

The repaired native original-speed lap20261103-001725-073 reduced peak roll from
0.7 to0.334rad and heave from1.467 to0.750m. The next13.5m/s native30s segment
002743-808 reduced heave to0.250m and wheel gap to0.389m, with zero contacts.
It reached checkpoint7; it is not a completed lap. Selected rear vertices stayed
at least0.189m above terrain support in both runs. These frame-boundary probes
are not exhaustive swept collision checks. Full-solver limitations and the
independent contact review are recorded inshowcase/SAFARI-DYNAMICS-DIAGNOSIS.md.
