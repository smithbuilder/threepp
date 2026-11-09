# Unity asset provenance

Original sources remain untouched in this repository. `manifest.json` binds the donor vehicle GLBs; `lod-manifest.json` binds offline density adaptations and records original source hashes. `tools/blender/cinder/create_kit.py` authors the missing buggy/Safari running gear and the city/test-gantry adaptation. This new geometry is not identical to the former C++ procedural art.

City surface images are copied from `showcase/assets/city/`; their source/license records remain in `photo-surfaces.json` and `source.json` there. Tree art and maps come from `asset-library/models/trees/` with its `asset.json` and original source records. HDR and ground sources remain in `asset-library/environments/kloofendal-partly-cloudy/` and `asset-library/materials/`. No audio samples from the donor's personal-project exhaust recordings are included.

The Unity adapter uses metres, Y up and +Z forward, preserves semantic glTF pivots, converts triangle winding, retains UVs/normals/vertex colors and translates metallic/roughness maps to Built-in material channels. Generated imports and scenes are excluded from git and reproducible from these tools and donor sources. Current hero/mid/far lowrider counts are measured by Blender in `lod-manifest.json`; runtime scene counts and draw statistics must come from actual player receipts.

`audio-provenance.json` records original synthesized placeholder cues with measured integrated LUFS and true peaks. Hearing quality remains UNVERIFIED.
