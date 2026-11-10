# Importer fixes and limitations

2026-11-09 Pacific. The donor and Unity adapter use the same numeric +Y up, +Z forward frame. Preserve winding with that identity mapping. The rejected r2 adapter flipped indices without reflecting geometry, which exposed inner faces; r3 corrected that defect.

The r4 adapter also converts glTF linear material color factors to Unity's color-property representation, preserves normal-map strength, and uses alpha fade for glTF BLEND. This follows the relevant behavior in Unity's [glTFast Built-in material generator](https://github.com/atteneder/glTFast/blob/main/Runtime/Scripts/Material/BuiltInMaterialGenerator.cs). The rejected r3 direct factor binding darkened paint and full-strength flake normals made it read dusty. Imported material and mesh names are preserved for mechanism and material bindings.

Built-in forward remains the target. The r5 body shader carries the donor clearcoat factor and roughness into a sharp second dielectric specular lobe with a Fresnel energy term. It remains a game approximation without physical refraction or thin-film interference. Transparent glazing uses an explicit alpha shader with bounded reflection, independently of Standard keyword variants. No URP/HDRP dependency is introduced. Independent player review owns visible acceptance.

City masonry uses metre-scaled UVs, authored storefronts and smooth branched canopy geometry. Lowrider detail reduction preserves flexible bellows, coils, leaves and roof cloth because their boundary stations are required for actual deformation and endpoint checks.

The r9 material clamps were rejected with the visual reassessment. Restoration imports the exact donor normal strength, roughness and clearcoat values. Role-isolated texture imports retain colour/data/normal conventions, original samplers and uncompressed packed metallic/smoothness values. The faithful native city uses its original 25 materials and all non-ground geometry; only the visual ground mesh is adaptively reduced within recorded height/colour limits. Static authored city shade remains in vertex colours. The simulation contact terrain is unchanged.

Restoration uses the original HDR sky, an offline specular-convolved cubemap with measured cardinal orientation, native ACES matrices/exposure and display-space FXAA. No extra realtime reflection passes or larger graphics caps are required. The interface camera stays outside the scene grade. Experimental CPU local-city reflections are diagnostic only because actual player comparison made dark paint less readable. Final signed-player reviews, rather than source values, own visible acceptance.


The native Nocturne constructor applies DoubleSide to canvas after GLB loading. The Unity adapter now preserves that rule with an explicit two-sided Standard fabric shader and backface normal handling, while retaining the original material values. Null-device shader metadata is not treated as graphics support; mandatory D3D receipts and matched hidden-cloth controls cover the final hero canvas. Native lamp-off/toggle parity remains partial and is not claimed.
