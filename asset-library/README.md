# Portable environment and vehicle assets

Start with `catalog.json`. This folder is usable without threepp, C++, or this
game. Models use standard GLB/glTF 2.0 or OBJ, metres and Y up. PBR textures use
ordinary JPEG/PNG; environments use linear Radiance HDR. Each asset manifest
records its source, license, hashes, dimensions and material conventions.

For a new engine, import the model at its recorded scale. Use base colour as
sRGB and roughness/normal maps as linear data. The normal maps are OpenGL +Y;
engines using DirectX normal maps should invert the green channel. Material
manifests record real tile dimensions, so UV scale does not depend on this
game's road width. Roughness maps are grayscale replicated across RGB and may
be repacked into the consuming engine's preferred channel convention.

GLB trees have embedded PBR materials and textures, with separate LOD files.
Choose their screen-size thresholds in the consuming project. Do not assume
the Safari scene's instance scales are the physical size of the source plant.
The fieldstone OBJ's material binding is in its JSON manifest. Sky rotation,
sun lights, fog, grass placement, collision and surface blending are scene
decisions; the engine-specific adapters are in `showcase/`.

Poly Haven assets keep their CC0 license and author/source records. Original
fieldstone geometry uses the included repository MIT license. Temporary
Porsche exhaust samples live outside this library and are excluded from its
export archive.

`scripts/prepare-environment-library.py` refreshes the catalog and writes a
standalone ZIP under `build/fidelity-v1/`, including every model manifest in the
library. It does not require a running game or contact a service. Historical
archives remain evidence of their original checkpoint; regenerate the ZIP after
adding or updating assets before running `scripts/validate-environment-library.py`.
