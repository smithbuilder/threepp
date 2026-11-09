# Importer fixes and limitations

2026-11-09 Pacific. The donor and Unity adapter use the same numeric +Y up, +Z forward frame. Preserve winding with that identity mapping. The rejected r2 adapter flipped indices without reflecting geometry, which exposed inner faces; r3 corrected that defect.

The r4 adapter also converts glTF linear material color factors to Unity's color-property representation, preserves normal-map strength, and uses alpha fade for glTF BLEND. This follows the relevant behavior in Unity's [glTFast Built-in material generator](https://github.com/atteneder/glTFast/blob/main/Runtime/Scripts/Material/BuiltInMaterialGenerator.cs). The rejected r3 direct factor binding darkened paint and full-strength flake normals made it read dusty. Imported material and mesh names are preserved for mechanism and material bindings.

Built-in forward remains the target. The r5 body shader carries the donor clearcoat factor and roughness into a sharp second dielectric specular lobe with a Fresnel energy term. It remains a game approximation without physical refraction or thin-film interference. Transparent glazing uses an explicit alpha shader with bounded reflection, independently of Standard keyword variants. No URP/HDRP dependency is introduced. Independent player review owns visible acceptance.

City masonry uses metre-scaled UVs, authored storefronts and smooth branched canopy geometry. Lowrider detail reduction preserves flexible bellows, coils, leaves and roof cloth because their boundary stations are required for actual deformation and endpoint checks.

The accepted r9 presentation adaptation bounds coated normal strength to 0.12, keeps clearcoat roughness at least 0.10, and caps polished chrome gloss at 0.86 to reduce fine specular aliasing at the conservative review resolution. The existing scene grade includes edge smoothing; the separate interface camera keeps menu lettering crisp. Storefront glazing has bounded environment reflection with a dark interior tint. These are view-only approximations and do not change simulation output or donor GLBs.
