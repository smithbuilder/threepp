# Cinder r28: Mercer early evening

November 11, 2026, Pacific. New sunset lighting for the existing lowrider city. Peach/lavender sky, low warm key, cool readable fill and warm street fixtures illuminate the same geometry. Car identities and driving rules remain intact. Original daylight is retained as a profile control.

[Actual-player gallery, daylight/sunset and lamp controls](../art-review/unity-r28/index.html). [Handoff](HANDOFF.md). PLAY-CINDER-UNITY.cmd selects the signed r28 player. The garage focuses on La Catrina, Media Luna and Nocturne; Mercer cruise, hydraulic/air sessions and workshop remain playable. Safari/buggy racing is deferred. Published to GitHub main/tag cinder-unity-r28 (candidate 9c808d7c) and private Patcher Cinder release r-mwd2tile-cd8ae582. Signed catalog/owner envelope, full inventory and streamed archive SHA256 verify; the other 13 selections are unchanged. [Receipt](unity/release/PUBLICATION-r28.json). Prior r25 remains available for rollback.

## Independent result

Lighting 7.5/10, car preservation 7/10, city art 6/10. Both independent visual reviewers support this prototype's early-evening direction with no remaining P1 in inspected scope. Broader Level 2 art remains NOT MET. Reports:[lighting](unity/LIGHTING-VISUAL-REVIEW-r28.md),[quality](unity/SUNSET-QUALITY-REVIEW-r28.md),[technical](unity/SUNSET-TECHNICAL-REVIEW-r28.md).

r27 was rejected for lost teal paint identity and bright road-repair shadow holes; both are corrected in r28 actual matched frames. Failed versions are retained. Remaining P2 includes coarse vertex/static/car shadows, approximate moving-object lamp occlusion, fine chrome/Nocturne front-quarter reflection flattening and nonexhaustive temporal shimmer/bloom checks. Generic city art/social identity remains separate unfinished work.

## Exact evidence

Signed player:builds/cinder-unity-r28/Cinder.exe, SHA256bbea8c386456dd9c07dd2348c5b2dd23618aa741bdba69dd14088990aead2aa8. Source fingerprintbaf3a961c9ac75792e9150a4d3c16e9c8ebb8f042252a78be594cb575fe9580e. Unity 6000.3.6f1 build0 errors/4 existing warnings.

204simulation+495rig+154runtime checks pass, plus10 scripted menu checks. Raw sim/rig outputs matchr25; runtime differences are only9transient material-ID lines. Source/geometry/material factors remain preserved where claimed, but actual frames decide visual retention. Normal packet has6 original stills and69silentseconds/2070 frames, full decode and delivery hashes.29 hero D3Dcanvasreceipts pass. Reviewers sampled frames; no continuous whole-clip/human acceptance is claimed.

| Paired capped measure | r25 | r28 |
| --- | ---: | ---: |
| Median frame interval |33.3414ms|33.3378ms|
| P99 frame interval |36.0492ms|35.0822ms|
| Maximum draws |219|219|
| Active geometry triangles |693585|693585|
| External peak process memory |436563968B|462155776B|

Both runs use the same final simulation fingerprint. Short960x600/30 PNG-IO observations do not prove isolated GPU performance or handheld 1080p/60. One512shadow/no MSAA/2 GiB job and other guards remain. No additional Light component/pass or city triangle is introduced;8bounded direct fixture calculations and additional vertex attributes still add cost.

Physical controls, feel, heard audio, comfort, comprehension, enjoyment, target-device performance, mid/far rendered canvas acceptance and exhaustive native handling/feature parity remain UNVERIFIED. Build/runtime/evidence files stay local; videos are off GitHub. Other lanes' native dirty work is preserved.
