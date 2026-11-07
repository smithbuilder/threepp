# Restoring the street film

The repository carries the editable timeline, licensed audio, fonts, poster,
review images and delivery records. The six native MP4 clips, final movie and
editable ZIP are retained on the workstation. Their SHA-256 digests are in
`native-captures.json`, `proof/delivery-receipt.json` and
`proof/editable-archive-receipt.json`.

For a fresh checkout, copy the six files under `assets/video/` from
`outputs/La-Catrina-Street-Show-Editable.zip` into the same location here.
`python verify_render_gate.py` checks their hashes and the accepted model
reviews. The [project instructions](README.md) describe the supervised preview
and render commands. The delivered MP4 is a separate local file at
`outputs/La-Catrina-Street-Show.mp4`.

The editable ZIP also preserves `Source/project/`, a snapshot of the full
engine sources used for the recording. Native recapture uses the full engine
checkout and its local build inputs. The original 1,440 native PNGs and
capture-session directories remain in the workstation's `build/sessions/`.
