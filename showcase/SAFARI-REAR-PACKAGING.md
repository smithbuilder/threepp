# Safari rear assembly

The fictional rear engine, exhaust, protection and bumper are separate
assemblies. Each bank has three distinct primary pipes entering a real
three-aperture collector. Two axial necks enter a transverse two-in/two-out
silencer; two openings in its rear skin lead to short open rolled outlets.
There is no combined exhaust/diffuser or structural tube used as plumbing.

The engine cradle starts behind the cabin bulkhead and connects through
outriggers and triangulated supports to the existing lower chassis rails.
Rubber engine mounts support cast feet; the engine has a compact sump and
lower rear cast relief. The silencer has separate straps and rubber-isolated
hangers. A spaced heat shield and removable, forward-ending engine guard
protect different areas. Bumper loads return through their own supports.

An independent source review caught real intersections in the earlier rear:
exhaust through bumper/cradle tubes, headers through engine mounts, rubber
inside the silencer and a shield through frame members. The first repair
also exposed silencer/engine interference. Those geometries were repaired;
the clearance thresholds were retained.

The independently reviewed geometry in source `510D123A...D4A655C` passed
1,288 static checks and 20 open-passage rays. Its measured minima were:

| Pair | Minimum |
| --- | ---: |
| Hot tubular envelopes / structural tubes |27 mm|
| Hot pipes / unrelated solid surfaces |22.76 mm|
| Case and collector surfaces / unrelated solids |34.75 mm|
| Shield / frame |42.85 mm|
| Engine / cabin bulkhead |25 mm|
| Fixed frame / cabin bulkhead |41.8 mm|

A subsequent metadata-only clarification labels the Y=.755 body keepout
plane as nominal. It is not an actual body-floor measurement. Actual body,
tyre and suspension fit remain separate full-model checks.

`scripts/audit-safari-rear.py` reproduces the rear with the actual generator
primitives, without importing the whole body or opening graphics. It checks
actual generated paths, conservative tubular envelopes, triangle distances,
case pressure-volume keepout, collector/case bores and the actual fixed
bulkhead. It cross-checks authoring metadata against intercepted construction
calls. Named initial 50 mm engine-port joints receive local treatment;
actual header/head intersections remain prohibited and all outside portions
retain the thermal-clearance rule.

The canonical preparation wrapper runs the full auditor and binds its source
hashes to generation/promotion. A clean diagnostic subset returns a nonzero
code. Analytical fixtures, the failing historical geometry and a deliberately
changed source were independently checked as negative controls.

These are static game-model packaging checks. They do not establish a
production engine specification, load rating, thermal performance, internal
gas-flow simulation, moving collision proof or whole-vehicle visual acceptance.
