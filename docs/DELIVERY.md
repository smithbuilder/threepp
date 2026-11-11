# Cinder r25 delivery

November 11, 2026, Pacific. A signed Unity lighting refinement adapted from Oliver's Windowseat assessment. Local tyre contact, restrained HDR highlight bloom, half-precision display filtering and static sub-byte output dither join the existing native city/PBR restoration. Simulation, sun, sky, diffuse/reflection calibration, lowrider menu and donor assets are preserved.

[Actual-player gallery and matched r24 comparison](../art-review/unity-r25/index.html). [Handoff](HANDOFF.md). [Adaptation brief](unity/LIGHTING-ASSESSMENT-ADAPTATION.md).

## Play

Run PLAY-CINDER-UNITY.cmd for the guarded signed r25 player. It opens the La Catrina/Media Luna/Nocturne garage. Choose Mercer cruising, hydraulics/air or workshop tests. Safari/buggy racing stays deferred. START-HERE.md lists controls. Patcher publication status and exact release are recorded in unity/release/PUBLICATION-r25.json once verified; prior r24 remains available for rollback.

## Independent verdict

Two independent visual evaluators support the scoped prototype refinement, with no demonstrated new P1 in their inspected output. Lighting remains **7/10**, cars **7/10**, city **6/10**. **Broader Level 2 art approval remains NOT MET.** Bloom still spills onto a few dark upholstery pixels; this is retained P2 finish work, with strength 0.10 as the reviewer's upper bound. These small effects do not resolve the city's generic storefronts, sparse social character or coarse foliage.

Reports: [lighting](unity/LIGHTING-VISUAL-REVIEW-r25.md), [quality](unity/LIGHTING-QUALITY-REVIEW-r25.md), [technical binding](unity/LIGHTING-TECHNICAL-REVIEW-r25.md). Reviewers sampled original sequence frames; no continuous whole-film visual approval is claimed.

## Exact package and checks

- Executable: builds/cinder-unity-r25/Cinder.exe, valid Authenticode signature.
- Player SHA256: `8c662a95e18c2c4bf2a478e7795b72d3fa2927d1d7d3dd9844596d5f427b7ae3`.
- Source fingerprint: `6ece4aa5250168c45f204df361b4f0d32f31dfc30bbde9ae3603cd93108c74b7`.
- Unity 6000.3.6f1 build: zero errors, four existing compiler warning records.
- Exact-player probes: 204 simulation, 495 rig and 154 runtime checks pass, byte-identical reports to r24. Ten scripted menu checks pass.
- Six original stills, silent 69-second/2,070-frame clip, full decode and source/player/evidence hashes: evidence/cinder-unity-r25/review/. Video remains off GitHub.
- Twenty-nine actual D3D hero roof checks pass. 280 periodic footprint vectors are finite/bounded; all eight sampled unsupported tyre weights are zero. This is finite evidence, not exhaustive raster/continuous-contact validation.
- Six control-patch samples retain exact display values; dither-only output differs by at most one byte. No proven perceptual banding gain is claimed.

## Paired conservative measurements

| Measure | r24 control | r25 |
| --- | ---: | ---: |
| Median frame interval | 33.3342 ms | 33.3425 ms |
| P99 frame interval | 42.4247 ms | 35.1378 ms |
| External peak process memory | 436,973,568 B | 426,602,496 B |
| Maximum draws | 216 | 219 |
| Active geometry tally | 693,585 triangles | 693,585 triangles |

Both exact players ran the same Catrina path/profile with identical final fingerprint. These short capped PNG-IO samples do not prove speed, GPU headroom, submitted triangle count or handheld 1080p/60 performance. Raw temporary colour storage rises approximately 4.896 MB. Existing graphics/resource guards remain binding.

Physical controls, input feel, heard audio, comfort, comprehension, enjoyment, target-device performance, mid/far rendered canvas acceptance and exhaustive native feature/handling parity remain UNVERIFIED. Old deliveries, failed reviews and captures remain preserved; r20 player was archived without deletion. Native dirty work is excluded from this change.
