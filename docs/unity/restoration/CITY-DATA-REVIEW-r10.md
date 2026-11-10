# Independent restored-city data review — r10 preparation

November 9, 2026, Pacific Time. Independent city evaluator; did not implement the city export, Unity material integration or renderer. This is an interim source/data review, not a visual acceptance or review of a new signed r10 player. No editor, player, native exporter, Blender process or graphics context was launched by this reviewer. Existing files were read and finite CPU checks were run in memory.

## Finding

**The frozen restored-city asset faithfully preserves the native export's non-ground geometry and its authored attributes. The ground reduction and material metadata claims reproduce. No geometry/content-parity blocker was found in this data inspection.** This is materially different from the simplified r9 kit: it is an offline conversion of `city::Block`, not a new approximation of its building masses.

The previous visual failure remains in force until the integrated signed player is captured and reviewed. No new visual score is assigned. Shader response, imported tangent space, visible texture orientation, screen-space fidelity, dynamic contact and measured submission budgets cannot be approved from a GLB alone.

## Exact reviewed asset

- Authoritative asset: `assets/unity/city/mercer-city.glb`, SHA256 `a2b02ee2922015cbbeb58af210fb599eede4aee60741ae059bc9e5df64d64673`.
- Manifest reviewed: `assets/unity/city/manifest.json`, SHA256 `097e50f829bcf700b09adfbad638c6121050f182e291d712bb6585d47589466b`.
- Material ledger: `assets/unity/city/materials.json`, SHA256 `16389d7533c7bb0bb3ee2901f15ca3d84ddebb133c406fc002eeae98ba9476c9`.
- Packaging source at review: `tools/cinder-city-export/package_city.py`, SHA256 `1adc88975128e5a7cddad516ba8927bdc933994c2c1bbfbfc74c058726015024`.
- Raw comparison: `build/cinder-city-export/native-v1/native-city.json` and its binary attributes/indices. Existing supervisor receipt `build/cinder-city-export/export-20261109-203819-812.json` records a normal CPU-only export with executable SHA256 `33C6D3C46EAFAD73E0C92D8EC1CF8C7B2CF0B737F170E321D96C8783832B945C`.

## Checks reproduced independently

| Claim | Independent result | Meaning and limit |
| --- | --- | --- |
| Native 566,118 triangles becomes 383,961 | Final GLB accessors contain exactly **383,961**, across **26 meshes / 25 materials** | Asset triangle count, not a runtime submitted-triangle measurement |
| All non-ground native content retained | All **24 static meshes / 333,798 triangles** match raw native position, normal, colour and index arrays bit-for-bit after vertex compaction; UVs match the explicitly documented V conversion | Includes detailed facades, window treatments, roof/service elements, streetside objects, context, boundary, trees and markings already assembled by the native constructor; no static decimation |
| Ground 232,320 becomes 50,163 | Actual final ground index accessors total **50,163**; total reduction is **182,157**, exactly the ground reduction | No unexplained reduction in other batches |
| Original grid height unchanged | Independently reconstructed all **116,865** original vertices and evaluated the final GLB triangles barycentrically; **maximum height difference 0 m** | Every original lattice point covered; 270,903 triangle/sample tests including shared edges |
| Linear colour error <=0.012 at original vertices | **0.007741659879684448**, matching the manifest | Finite lattice-vertex result, not a universal error bound at every point between vertices |
| Native source/texture identities retained | All five listed owning-source hashes match both frozen copies and current sources; all texture-file hashes match the manifest and original image files where applicable | Generated native leaf image is bound by its own output hash |
| Required geometry data present | Every mesh has finite POSITION, NORMAL, TEXCOORD_0 and COLOR_0 | No r9-style missing wall colour data or wrong foliage colour channel in this GLB |
| Exact native material metadata retained | All **25** definitions match raw native linear colour, roughness, metalness, normal axes, cutoff, sidedness, emission and colour/normal/roughness texture identities | Metadata parity; final Unity shader/import behavior remains a separate test |

`export_city.cpp` constructs the actual `playground::Terrain(true)` and `city::Block`, then serializes their material batches. The frozen `CityBlock.hpp` retains four-sided facades, frame/curtain/blind/AC/fire-escape construction, rooftop equipment, road wear, parking/drainage, benches/signals/signs/hydrants/bins, branching foliage, visible perimeter and fifteen surrounding building shells. These are source-backed inclusions, not inferred from a mesh total alone.

The reduction code subdivides by material and baked-colour tolerance, preserves nonflat half-metre cells and their original diagonal, and stitches flat-cell boundaries. Inspection supports that construction; this review did not perform an exhaustive triangle-intersection or all-edge topology proof. The exact lattice-height result and unchanged nonflat source cells support retaining the authoritative surface. `git diff -- Unity/Assets/Cinder/Scripts/Sim` was empty at review; Unity simulation/collision code is not replaced by this asset.

The existing `build/cinder-city-export/blender-verified-v1/verification.json` binds the same GLB and reports Blender 4.5.9 import checks for exact mesh identities/counts, colour layers, UV/material identities and finite bounds. It reports 27 Blender material datablocks while the GLB references 25 materials; unused Blender datablocks do not establish extra runtime material batches. This is a read receipt, not a render reviewed here.

## Budget interpretation

**383,961 city + 309,624 unchanged hero Catrina = 693,585 asset triangles**, leaving **6,415** against the 700,000 target before other submitted work. This is planning arithmetic only. It does not include the effect of visibility, shadow passes, material passes, interface work or the engine's submission counting. Twenty-six meshes and twenty-five material identities also do not prove <=300 draws.

The current `CinderView` source skips procedural visual-ground creation for the city and spawns `mercer-city`; this avoids intentionally drawing the old city ground underneath the restored ground. It disables static city shadow casting/receiving and enables ground shadow reception, consistent with retaining native baked static shade while allowing moving-car contact. Confirm those imported renderer settings and absence of duplicate terrain in the exact built player. The authoritative Sim terrain remains separate.

## Finite remaining issues

1. **P2 regeneration provenance gap.** The city manifest freezes the principal scene headers and exporter source, but does not bind `package_city.py`, procedural `include/threepp/extras/vegetation/TreeGenerator.hpp` / `TreeTextures.hpp`, or the linked native library/build identity that supplies geometry helpers. The output GLB is securely identifiable, and this is not evidence of current content loss. Add those hashes/build dependencies to a supplemental ledger before calling future regeneration fully reproducible. `materials.json` should also be bound in the candidate delivery/source manifest because Unity uses it to override interchange materials.
2. **Runtime budget remains unverified.** The complete city plus Catrina estimate is close to the triangle ceiling; count actual submitted triangles and draws on the final exact candidate. Keep native detail and use proper visibility/batching/distance policy if required; do not silently simplify the near street to hit the target.
3. **Final image parity remains unverified.** Data restoration does not prove material units/colour conversion, texture V orientation, cutout canopy, baked shade strength, specular filtering or dynamic tyre contact. The renderer/material implementer owns those controls, with a fresh independent image verdict afterwards.

## Required next evidence

After the shared guard allows a build/run, bind the signed candidate to this exact asset and material ledger. Compare native and new-player car-height coffee/workshop, full side and reverse street-end shots with recorded camera/FOV, car pose and sky/sun alignment. Include a close canopy/kerb/shop window view. Check restored facade depth, surrounding shells, road/parking/drainage detail, native leaf colour/texture and static shade without double-darkening. Confirm final triangle/draw measurements with actual player counters, not this planning sum. Retain the r9 failures and intermediate controls.

**Interim disposition: geometry/material data parity supported; visual gate still pending fresh signed-player evidence.**

## Addendum — sampler and provenance finalization

Independent read-only follow-up, November 9, 2026. The asset reviewed above is preserved at `build/_archive/city-sampler-v1/`. Its hash remains the historical binding for the original checks. The current authoritative GLB is now SHA256 **`5e72ee0027ded63d87e599b0e0af5e98be019f5d8c080602acff3e6022eb599d`**; current manifest SHA256 is `8de189b053be9b5aeb9d8921ebf56df1a805c4d8492e9b4671ce924c3b39095a`.

The entire current GLB binary chunk was independently compared byte-for-byte against preserved v1 and is identical. Only JSON `samplers` and texture sampler routing differ. Geometry, indices, normals, UVs, colours and embedded image bytes are therefore unchanged; the original 383,961-triangle count and finite ground-validation results carry forward. The native leaf colour texture now references ClampToEdge on both axes (`33071`); photographic/paint samplers retain Repeat. Final visible atlas orientation/filtering remains an image-review check.

All **ten** source entries match both their current owning files and frozen copies, including the packager and procedural TreeGenerator, TreeTextures, NoiseUtils and TextureBake dependencies. All **28** frozen texture hashes match; this now includes the four constructor-input photographs subsequently replaced by the final PBR maps. The linked `threepp.lib` hash and 76,693,922-byte size match the manifest's recorded dependency identity. The conversion-tool hash matches `995f300c0efd128e94d59b38fa544893d1c609472f10307bdad976a5869871a9`. **The identified P2 missing-provenance-identity gap is closed for this reviewed checkout and ledger.** A future regeneration must use those recorded dependencies; an identity record alone does not supply an unavailable compiled library.

`materials.json` remains byte-identical at SHA256 `16389d7533c7bb0bb3ee2901f15ca3d84ddebb133c406fc002eeae98ba9476c9`; retain its binding in the eventual player source/delivery manifest. The new existing Blender receipt, `build/cinder-city-export/blender-verified-cinder-unity-r10/verification.json`, reports success and independently matches the current GLB hash, 383,961 triangles and 26 meshes.

This addendum approves the updated **data binding**, not a player revision. Build attempts or a reduced shipping vehicle-art set do not change this city's geometry findings, and they do not establish a visual improvement. Final signed-player captures and runtime budget measurements remain required before another visual verdict.
