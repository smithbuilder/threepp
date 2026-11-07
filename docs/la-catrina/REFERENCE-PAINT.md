# Reference-derived paint provenance

The current roof, hood and trunk paint textures contain transformed pixels from the user-supplied **La-Catrina-Master.jpg**. The side-spear scroll uses a two-pigment ornament mask derived from the same sheet. This supersedes the earlier all-original vector paint approach. The geometry and small vector cameos remain original. No external mesh was imported.

The source is `docs/la-catrina/references/La-Catrina-Master.jpg`, 4560×9413 pixels, SHA256 `62c46159d87f29348a35ecb07584d752cf3a15161b19c655968d0da96a42d750`. The user requested fidelity to this sheet. No independent public redistribution license is asserted for the supplied artwork.

`scripts/catrina_reference_paint.py` records the exact paint-only quadrilaterals in original source pixels. It rectifies the roof field, the two hood fields separately, and the single framed trunk field. Sampling the hood panels individually avoids the concave cowl boundary and prevents ventilation-slot or chrome pixels from entering the map. The resulting three maps are embedded at 1024×1024 pixels.

Processing is deterministic: bicubic quadrilateral rectification; a 35-pixel Gaussian illumination estimate with correction limited to 0.84–1.18; pigment alignment with protection for the champagne-gold color; a 90° rotation and horizontal mirror for model UV axes; and Lanczos resampling. The two hood fields are assembled on the central pink stripe. The roof has no added rectangular border; the trunk uses one framed panel, matching the atlas.

The maps are named `reference_roof_lace`, `reference_hood_lace` and `reference_deck_lace`. The asset JSON includes a `referencePaint` record containing the source hash, coordinates and processing. Source reproduction requires the exact supplied atlas as well as the six Python source files named and hashed in `sourceFiles`. Reproducing an asset with baked cavity shading also requires the matching geometry-bound cache under `docs/la-catrina/bakes`.

This process removes broad illumination differences but cannot reconstruct physically measured paint pigments or microscopic flake from a photographed/rendered reference. Material reflection and surface shape still come from the native model and its lighting.

The generator separately authors deterministic 1024 x 512 undercoat normal and
linear roughness maps (seed 196411, normal scale 0.32). These represent groups of
metallic flakes beneath the existing smooth clearcoat, without changing the
reference-derived pigment or ornament images. They do not claim measured flake
size or lacquer thickness. A controlled comparison retained identical round10
geometry, camera and lighting; three bounded native stills verified that the
response stays subtle. The generator records this layer as `candyFinish` in
the model manifest. The final visual score still depends on the complete frozen
model and its independent review.

Round06 preserves those exact paint sampling regions and processing. Its measured body and cabin offsets change the mesh dimensions and UV placement, not the source artwork. The original side-spear vector field moves to a 630mm center height with its cameo below the unchanged handle. Its UV origin follows the 190mm rearward body offset, so the ornament remains registered to the panels. Any baked cavity shading is stored separately in geometry-bound vertex color, not added to the paint maps. These are authoring and provenance notes, not an independent visual acceptance claim.

Round07 replaces the generic side-scroll repeat. The source box is `(510,2639,690,2648)` in original atlas pixels, between the door seam and cameo and inside the chrome borders. An ornament coverage mask is extracted as `clamp((G/R-.30)/.38,0,1)`, then mapped between authored cherry `(152,36,72)` and champagne `(211,171,117)` pigments. The field repeats at approximately 0.96m along the spear. This preserves the fine flowing ornament without copying a photograph's side-panel specular highlights. The lower-body color has a restrained authored transition from candy rose `(229,22,104)` to shell pink `(236,57,129)` below the spear; this is an intentional pigment choice, not a lighting bake. No new embedded image or larger texture is required.

The subsequent fit review found that the restrained approximation still reversed the reference's dark-upper/light-lower hierarchy. Round08 instead uses the sheet's explicitly labeled finish swatches: Candy median RGB `(183,37,99)` from source box `(3000,1675,3230,1700)`, and Shell pink `(247,143,180)` from `(3290,1675,3520,1700)`. Their transition falls beneath the side spear. Plain upper painted parts and top-map pigment alignment use the same Candy value. These source swatches are a more direct visual basis than shaded vehicle pixels, but they are still illustrative pigments rather than physically measured reflectance.

## Fine ornament revision after round08

The two completed independent reviews identified soft scrollwork and weak fine
linework. The next texture pass retains the same top-paint quadrilaterals while
separating their ornament from illustration lighting. A green/red chroma mask
retains broad gold strokes; positive local green-channel contrast recovers the
fine fan and radial lines. The combined coverage is remapped between labeled
Candy and Champagne `(203,162,108)`, with the latter verified at source box
`(3870,1675,4090,1700)`. Source grain is retained only as a bounded ±3 RGB
residual in the candy field. The exact formula is recorded in the model's
`referencePaint.processing` metadata.

The side scroll now comes from a paint-only quadrilateral in the main hero
image: upper-left `(1520,1330)`, lower-left `(1520,1356)`, lower-right
`(1970,1324)`, upper-right `(1970,1297)`. Its 450×27 source sample resolves
three times the former strip's height. Chrome borders and character medallions
are excluded. Chroma plus local contrast produces a champagne ornament mask
over a dark cherry field. Native review is required to establish the benefit
after this derivative is mapped onto the car; a sharper source image alone is
not a visual-acceptance result.
