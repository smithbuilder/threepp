# Canonical Safari asset preparation

The reproducible canonical path is `scripts/prepare-safari-body.ps1`. Build the
CPU tools after changing the model/tests, then run the wrapper with an installed
Python interpreter (NumPy, SciPy and Pillow are required):

```powershell
cmake --build build/windows-gl --config Release --target RallyVehicle_test safari_ao_bake --parallel 2
.\scripts\prepare-safari-body.ps1 -Python 'C:\path\to\python.exe'
```

Omit `-Python` only when `Get-Command python` resolves the intended interpreter.
The Windows `py` launcher is not used. The wrapper performs no build, game/GPU
launch, signing or network work.

It snapshots the exact prior canonical GLB, JSON and optional AO receipt under a
new `build/safari-prepare/<unique-id>/previous` directory. It runs the full static
rear packaging gate in `scripts/audit-safari-rear.py`, including actual surface
fit, open exhaust passages and source/metadata consistency. Diagnostic subsets
cannot pass this gate. It then generates raw body
geometry, checks the isolated raw asset with `RallyVehicle_test`, bakes using that
raw GLB's actual SHA-256, checks the isolated AO candidate with the same CPU test,
and checks cockpit fit against both actual serialized assets with
`scripts/audit-safari-cockpit.py`. The cockpit check tests triangle crossings
and distances against the windscreen, structural surround, cabin linings and
primary body; it also guards the native primitive/placement contract. A
collision, missing surface group or source drift returns a failure. Only then
does the wrapper promote the candidate. Any caught failure restores the previous
three named files and verifies their hashes. Logs and candidates remain in the
unique ignored run directory; no recursive cleanup or candidate overwrite occurs.

The promoted `safari-body.json` keeps generator/source provenance and adds
`rawAsset` counts/hash. Its top-level bytes, vertices, triangles and image counts
are measured from the actual AO GLB. `safari-body-ao.json` records the compact AO
receipt, tool/binary identities and CPU results. These checks do not replace
supervised native review or establish visual acceptance.

**Running `generate-safari-body.py` alone overwrites canonical AO with the raw
model.** Use the full preparation wrapper to reproduce the finished asset. The
wrapper dynamically passes the newly generated raw hash; it does not pin an old
candidate hash. The lower-level packer still supports explicit disposable
candidates and `--reuse-values`; use a new output directory under `build/` and
`--expected-sha256` for that exact raw source. Existing candidate files require an
explicit `--force` and are never selected by the wrapper.

## What is baked

The C++ helper reads the actual GLB accessor/index buffers, asserts identity
static node transforms and one node per mesh, then builds one `threepp::BVH`.
OPAQUE physical geometry occludes; BLEND, MASK and named livery/decal/roundel/
legend meshes do not. BLEND and emissive materials do not receive AO. Every
remaining referenced vertex traces 16 deterministic cosine-weighted Hammersley
rays with a 0.002m origin offset and 0.25m maximum distance. Exact position/normal
duplicates reuse the query. Degenerate occluder triangles are omitted from the
ray structure, but remain unchanged in the output geometry.

The initial frozen experimental source had unreferenced zero-normal vertices
and pole/strap vertices whose normals were zero. Original normals are preserved byte-for-byte at every
triangle corner. AO queries alone use neighboring valid normals for these poles;
unreferenced or unrecoverable vertices receive neutral visibility. Counts are
recorded in the bake receipt. This does not repair source shading normals.

The result is hemisphere visibility, not a directional shadow. The atlas is a
standard glTF `occlusionTexture` at `texCoord:1`, `strength:0.5`. The actual loader
maps this to `uv2` and AO channel1. The existing shader scales indirect diffuse
and indirect specular occlusion; direct lighting and albedo stay unchanged.
The ambient multiplier is bounded to `[0.5,1]`.

## Atlas and approximation

Each receiving triangle is expanded to three independent corners, preserving
its position, normal, UV0, color and winding. A 2x2 cell of a shared 1024x1024
RGBA atlas holds its scalar field. UV1 stays at the three pixel centers
A=(0.5,0.5), B=(1.5,0.5), C=(0.5,1.5), relative to that cell. Min/mag filtering is
LINEAR, with no mipmaps; interpolation between these centers reads no adjacent
cell. The unused fourth pixel is `D=clip(B+C-A,0,1)`.

The default layout assigns the median-visibility triangle corner to A and the
low/high corners to B/C by permuting UV1 assignments only. Therefore D always
lies between the low/high values and does not clip. Bilinear interpolation then
equals the barycentric linear visibility field, apart from 8-bit quantization.
This introduces no geometry/UV0/color change. The maximum ambient-factor
quantization error is `0.5*(0.5/255)`, approximately 0.000981.

Triangles with byte-identical quantized A/B/C/D values share the same cell.
Each triangle retains its own stable corner permutation. All four texels,
including D, must match, so reuse preserves the previous bilinear field at
every barycentric point. Texture dimensions, filtering, passes and geometry
detail stay unchanged. Capacity applies to unique fields rather than triangle
count; receipts separately record triangle references, unique cells, reuse,
per-mesh new/reference counts and clipped triangle/unique-cell counts.

The packer re-reads the serialized GLB image and UVs, checking all four RGBA
texels and the local UV permutation for every receiving triangle. An
independent baseline comparison also checked both layouts, corner ties,
clipping, dense barycentric grids, hostile adjacent cells and every possible
cell-origin UV at1024. The capacity negative test rejects a new unique field
before mutating the lookup. These are CPU field-equivalence checks; native
rendering remains a separate check.

`--atlas-layout original` assigns corners in their original order and reproduces
v1. There D may clip. The bilinear error term is `(clippedD-D)*s*t`; because
`s+t<=1`, its visibility magnitude is at most `abs(clippedD-D)/4`. The receipt
records the actual count and bound. Prefer the default median layout.

This is vertex-sampled, local static-geometry AO. It cannot resolve sub-triangle
contact features, distant occlusion, animated suspension/wheel occlusion or
screen-space contact shadows. Sixteen samples can show sampling noise in tight
recesses. It does not establish realistic materials or artistic acceptance.

## Evidence produced

The helper writes `ao-values.json/.bin`, source identity, mesh occluder/receiver
flags, timings, peak process working set, ray count and visibility stats.
The packer writes the candidate GLB, `ao-atlas.png`, `AO-RECEIPT.json` and an actual
CPU `GLTFLoader` validation log. It re-reads the serialized delivery and verifies
all original triangle-corner attributes and total triangle count. It samples
atlas corners, edges and interiors against the original visibility field and
checks the measured error against the stated bound.

On the historical `51218c...` frozen source, the v2 candidate has 110 meshes, 98 AO receivers and the
same 187,902 triangles. It uses 148,158 atlas cells with zero fourth-pixel clips.
The bake made 92,224 unique vertex queries / 1,475,584 rays in 8.73s, with 47.35MB
peak helper working set. The 1K RGBA atlas is 4MiB raw; active geometry buffers
grow from 7,929,816 to 26,542,320 bytes, plus the atlas. Runtime process/VRAM cost
still requires the supervised native run. No GPU was used to prepare the asset.
