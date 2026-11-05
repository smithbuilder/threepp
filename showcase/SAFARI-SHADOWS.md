# Safari receiver-plane shadow filtering

The repeated diagonal/row bands on the cream body were self-shadow artifacts.
The existing 512-pixel directional shadow map covers 20 metres: each texel
represents 39.0625 mm. Its five rotated Vogel samples each use a hardware
bilinear depth comparison. Comparing every sample against one receiver depth
lets a smooth sloping surface shadow itself. Smooth normals or more geometry
do not repair that sampling mismatch.

A matched native material-side control removed the bands without changing
geometry, textures, AO or lighting. It was diagnostic only: removing the
sun-facing caster sheets can also remove their shadows.

`RallySafariShadows.hpp` instead follows the receiver plane to each sample and
compares against the minimum plane depth at its four actual bilinear texel
centres. It accounts for sampler edge clamping. This preserves the existing
five hardware texture fetches, caster surfaces, culling, material depth state,
15 mm normal offset, depth bias, shadow map size, render targets and passes.
It adds fragment arithmetic and derivatives, rather than texture fetches.

Only materials belonging to the Safari car receive the explicit program-cache
define. Both initial selection and vehicle switching apply it before rendering.
The ordinary buggy retains stock filtering. The renderer library is unchanged;
the standard/physical shader copies retain literal stock includes outside the
opted-in PCF branch. Only directional-light comparisons use the derivative
helper; their visibility is uniform across the fragment quad. Derivatives run
before the per-pixel shadow-frustum branch.

The helper falls back to stock comparisons for an ill-conditioned projection,
a depth gradient exceeding .005 normalized depth per bilinear footprint, or a
reference correction exceeding .01 normalized depth. At the current projection,
all planar light-facing surfaces with normal/light cosine at least .1 fit the
slope caps, provided the projection Jacobian is valid.

`Build-Playground.ps1 -Action Test` exercises independent corner enumeration,
valid and degenerate plane projections, retained foreground occlusion and
ordinary-material isolation. Independent CPU reviews additionally checked
250,000 bilinear/clamp cases and 48 shader preprocessing configurations.
Native shadow-on/stock/off comparisons and moving captures remain necessary
for appearance and contact assessment.

This is a local planar approximation with a coarse shadow map. Curved surfaces,
near-parallel projections and reversed vertex normals can retain artifacts.
The stock vertex normal offset is not flipped for back-facing double-sided
fragments. A conservative bilinear reference can lose shallow occluders: its
additional contact-edge uncertainty is at most one texel per light-plane axis
(55.24 mm diagonally here), besides the retained stock offsets and filter disk.
It does not provide fine contact shadows, ray tracing or physical validation.

Capture-only `-PortraitShadows stock|off` provides matched controls through
`Run-Evaluation.ps1`; `default` uses the Safari correction. These options do
not alter the normal game UI or the approved 960x600 evaluation guard.
