# Cinder Unity handoff

November 11, 2026, Pacific. Current reviewed signed player: **cinder-unity-r25**. Oliver asked to incorporate the useful principles from his supplied Windowseat lighting assessment. The limited refinement is independently supported. **Level 2 art remains NOT MET: lighting 7/10, cars 7/10, city 6/10.** Local highlight spill onto dark upholstery remains P2 finish work.

## Needs you

No permission is pending. Physical controls, input feel, heard audio, comfort, comprehension, enjoyment and handheld 1080p/60 remain UNVERIFIED. Reviewers inspected original stills and sampled sequence frames; they did not continuously watch the whole clip. Automated full decode is separate evidence.

GitHub/private Patcher publication is being finalized under Oliver's existing authorization. r24 remains the live selection until the r25 publication receipt is verified. Check `docs/unity/release/PUBLICATION-r25.json` for the completed transfer. Prior r24 release is `r-mwadnquf-eb902ae9` and is retained for rollback.

## Play and scope

`PLAY-CINDER-UNITY.cmd` explicitly selects r25 through the guarded runner. The source runner's optional default remains r24 as a preserved control; pass `-Revision` explicitly. The menu centers La Catrina, Media Luna and Nocturne, Mercer cruising, hydraulic/air sessions and workshop tests. Safari/buggy racing stays deferred. See START-HERE.md for controls and art-review/unity-r25/index.html for the matched comparison, six original stills and local silent 69-second proof.

Unity 6000.3.6f1, Built-in forward, Linear, D3D11, Windows x64, Mono, .NET Standard 2.1. Pure simulation and donor assets are unchanged. Seven tune definitions/eight areas retain probe coverage; only three lowrider art families ship. Prior restoration details and limits remain in docs/unity/HANDOFF-r24.md and DELIVERY-r24.md.

## What changed

- Four small tyre footprints affect only Mercer ground indirect light. Actual posed tread samples and authoritative support flags set the position/strength; height/normal gates restrict bleed, and unsupported tyres get zero weight. No added geometry, light, shadow map or render pass. Per-renderer properties respect the host Frame; non-city worlds skip the work.
- Soft-knee HDR bloom uses half/quarter-resolution targets and three extra blits before the unchanged native tone transform. Scalar extraction/capping preserves source RGB ratios before spatial mixing. Strength is 0.10, considered an upper bound by the reviewer. Dark cabin spill is real: one Catrina control pixel changes by 104 bytes; paired cockpit views show no broad veil. It is P2, not claimed absent.
- Display-encoded colour stays half precision through existing FXAA. Static output dither is bounded to half a display byte. The actual dither-only comparison changes output by at most one byte; six sampled control-patch interiors match legacy. No demonstrated perceptual banding improvement is claimed.
- Sun, HDR sky, diffuse SH, reflection strength, original PBR material factors and exposure remain calibrated. The Windowseat cabin/toon/contour/tunnel changes do not apply. Extra atmosphere, moving cloud shadows and new lamp behavior are deferred.

## Exact identity and proof

Signed player SHA256: `8c662a95e18c2c4bf2a478e7795b72d3fa2927d1d7d3dd9844596d5f427b7ae3`.
Source fingerprint: `6ece4aa5250168c45f204df361b4f0d32f31dfc30bbde9ae3603cd93108c74b7`.
Runtime implementation commits: `76e5e09e`, `1bdc5719`.

Build succeeded: zero errors, four existing Body/FXAA compiler warning records. The first restricted build stalled/crashed in local licensing before output; its failed log is retained. The guarded retry with existing licence access succeeded. No pause was cleared, no other project killed, no graphics cap raised.

Exact probes pass **204 simulation + 495 loaded-rig + 154 runtime checks**, plus ten scripted menu checks. All three probe JSONs are byte-identical to r24. The technical reviewer rehashed 5,331 sources, 147 player files, 62 delivery files and 2,234 original evidence files without drift. All 18 Sim manifest entries are unchanged. All 70 final periodic poses match r24 ticks/fingerprints; all 280 footprint vectors are finite/bounded and all eight sampled unsupported tyre weights are zero. Sampling is not continuous GPU contact-coverage proof.

`evidence/cinder-unity-r25/review/` contains six unchanged stills, a 2,070-frame/69-second silent original-player clip, exact receipts/replays and delivery hashes. Twenty-nine real D3D hero Nocturne canvas receipts pass. Mid/far GPU canvas acceptance remains unverified, as in r24. The packager rejects diagnostic material/lighting/colour/reflection controls. The separate actual-r24 same-camera take has identical state; r25 legacy mode is not byte-exact to r24 (832 changed pixels, maximum 30 bytes). Do not substitute the legacy switch for the actual player control.

Independent reports: docs/unity/LIGHTING-VISUAL-REVIEW-r25.md, LIGHTING-QUALITY-REVIEW-r25.md and LIGHTING-TECHNICAL-REVIEW-r25.md. Keep prior failed packets/reviews.

## Measured limits

Matched Catrina capped runs, r24 then r25: median 33.3342 / 33.3425 ms; p99 42.4247 / 35.1378 ms; external peak 436,973,568 / 426,602,496 bytes; maximum draws 216 / 219. Both tally 693,585 active geometry triangles and the same final fingerprint. This is a short 960 x 600 / 30 fps PNG-IO test, not isolated GPU timing, all-pass submitted triangles or evidence that r25 is faster. Bloom adds approximately 4.896 MB raw temporary colour storage and more bandwidth despite the lower observed process peak in one pair.

Automated runs stay hidden, silent, bounded and serialized: 960 x 600 / 30, no MSAA, one 512 shadow, 2 GiB process job, at least 4 GiB free RAM/15 GiB disk, cooldown, pause checks, shared mutex and watchdog. User play stays five minutes. Build a new unique revision with `RUN-BUILD-RUNNER.cmd -Revision cinder-unity-r26`, sign, probe, capture and get fresh review. Do not edit source-manifest-listed files after a final build and claim that build covers the edits.

## Remaining work and preservation

The city still needs a distinctive social gathering place, richer storefront character and better foliage. Fine chrome/glass/canvas finish remains P2. Native lamp-off/toggle and some service-removal helpers are partial. The rejected local-city reflection bake stays opt-in diagnostic. No exhaustive native feature, Bullet handling, moving clearance or subjective quality acceptance follows.

builds/ now retains r24 control and r25; r20 was preserved under build/_archive/players/cinder-unity-r20. No user file was deleted. Other lanes' dirty native source/assets are untouched and excluded from commits. Videos stay local/off GitHub. No other project was modified.

Playbook task cmw9qrsq000alle018qlbcxni, verified seat z2-codex@agents.playbook. The standard helper now works. Active Bridge thread: gen-cinder-unity-r9-visual-regression-independent-native-com. For Python packaging from PowerShell 7, remove PSModulePath only from the packaging process so child Windows PowerShell uses its signature module; keep verification enabled.
