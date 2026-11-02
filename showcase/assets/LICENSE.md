# Rally surface assets

`forest_ground_04` and `gravel_road` are Poly Haven assets released under CC0-1.0.

- https://polyhaven.com/a/forest_ground_04
- https://polyhaven.com/a/gravel_road
- License: https://polyhaven.com/license
- Legal deed: https://creativecommons.org/publicdomain/zero/1.0/

Only 1K diffuse and OpenGL normal maps are included. Original download URLs and
SHA-256 checksums are recorded in `SOURCES.json`. The files were checked against
the MD5 checksums supplied by Poly Haven's official API at acquisition.

The game loads these local files and makes no live calls to Poly Haven.

`cinder_engine.wav` is an original synthesized two-second mono engine loop,
created for this project from sine harmonics and soft clipping. It contains no
samples from third-party recordings and is covered by the repository MIT license.

## Recorded exhaust and racing font

The active rally audio uses three edited bands from **kyles**, "dune buggy muscle
car pass slow loud nearby full engine rev and trail off to right.wav":
https://freesound.org/people/kyles/sounds/413905/ — CC0-1.0.
https://creativecommons.org/publicdomain/zero/1.0/

The public HQ MP3 was trimmed, filtered, converted to mono 48 kHz PCM16 and
crossfaded into loops. Source/download URLs, processing and SHA-256 receipts are
in `EXHAUST-SOURCE.json`. Rebuild with `scripts/prepare-rally-audio.py`.
The old synthesized `cinder_engine.wav` is retained as a legacy asset and is no
longer played by the rally candidate.

Rajdhani SemiBold is by the Indian Type Foundry, under the SIL Open Font License
1.1. Font source: https://github.com/google/fonts/tree/main/ofl/rajdhani
The full license is included as `Rajdhani-OFL.txt`.
