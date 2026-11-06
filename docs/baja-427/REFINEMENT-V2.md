# Baja 427 reference refinement v2

The three user-supplied Downloads files are copied unchanged under references/: Master Reference JPG, Rally Truck Blueprint PNG and Suspension Baseline XLSX. Downloads originals remain untouched. Prior geometry, maps, generator, audit and signed viewer are preserved under build/baja-427-v2/baseline.

Updated existing local model: sculpted integral hood crown and recessed louvers; rolled shoulder width; tapered, recessed honeycomb grille and bevel surround; rounded C lamps and inset projector barrels; painted window perimeter and split glazing; more neutral bronze wheels; original paint dirt, packed roughness/metalness and OpenGL normal maps. Corrected livery clearance against the new side contour, and top/front UV projections after native review exposed stretched paint dirt.

Portable deliverable: asset-library/models/baja-427/baja-427.glb, its JSON manifest and five PNG maps; no engine requirement. Named steering, rolling, axle, suspension, tailgate and cargo interfaces survive. build/baja-427-v2/Baja-427-Modular-v2.zip is the independent asset package. Launch-Baja-427.cmd opens the existing signed native asset bench.

Serialized audit passes: finite geometry, normals/winding, indices, hierarchy, stationary tyre ground alignment; 209,600 triangles, 104 mesh draws, five embedded maps. Native loader audit plus six guarded native views completed with exit zero and empty stderr at 960x600. Exact session/hash evidence is build/baja-427-v2/verification.json; final review-sheet.jpg includes all six views. No new graphics profile, binary or shadow setting was needed.

This remains a procedural game-asset approximation. Cab/door surfacing and tyre tread need further sculpting and richer authored wear to reach the reference's hero finish. No driving integration or full suspension kinematics is claimed. The workbook supplies proposed solver parameters for future driving work; those were read, but not silently applied to this visual-only bench.
