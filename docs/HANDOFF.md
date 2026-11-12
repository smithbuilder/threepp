# Cinder Unity handoff

November 11, 2026, Pacific. Current reviewed signed candidate: **cinder-unity-r28**. Mercer now has the requested approximately 6 PM look before darkness: colourful sunset, low warm sun, readable cool fill and existing streetlights illuminating nearby surfaces. Both independent visual reviews support prototype retention: **lighting 7.5/10, car preservation 7/10, city art 6/10**. Broader Level 2 art remains NOT MET.

## Needs you

No permission is pending. Physical controls, feel, listened audio, comfort, comprehension, enjoyment and handheld 1080p/60 remain UNVERIFIED. Reviewers inspected stills and sampled sequence frames, not continuous whole-film playback. Existing publication authorization covers the GitHub/private-Patcher update; live r25 stays selected until the new r28 publication receipt is verified.

## Play and profile

PLAY-CINDER-UNITY.cmd selects signed r28 explicitly through the resource guard. Refresh Patcher once publication is verified. START-HERE.md contains controls. The lowrider garage, Mercer cruise, hydraulic/air sessions and workshop are preserved; safari/buggy racing remains deferred. City uses the new evening profile; workshop/forest keep original daylight. This is fixed art direction, not a day/night or astronomical clock simulation.

Unity 6000.3.6f1, Built-in forward, Linear, D3D11, Windows x64, Mono, .NET Standard 2.1. Pure simulation, donor geometry and physical material factors are unchanged. Previous restoration/delivery details remain in docs/unity/HANDOFF-r25.md and DELIVERY-r25.md.

## Lighting implementation and rejected iterations

- Offline authored HDR sky retains licensed native cloud structure after old-sun removal. Peach/rose is concentrated sunward; the broad anti-sun/lower environment is neutral/cyan with a brighter urban-ground return, preserving metallic paint identity. Visible sky/mirror0 sun and analytic key share a direction/energy policy; diffuse SH/rough mips are disc-free. Original daylight remains intact.
- New sun direction normalized(0.70,0.20,-0.685), linear colour(1,0.62,0.35), intensity2.4/pi. Reflection strength remains linear0.65 through calibrated API encoding. A separately recorded constant cool SH fill(0.075,0.11,0.16) is authored ambient light, not a physically solved spatial bounce.
- Separate sunset city prefab clones26 meshes with383961triangles, preserving geometry/normals/existingUVs/materials. It replaces only old static directional shade, keeping authored AO/variation. Five-ray long shadows are approximate vertex shading over the existing adaptive ground. UV2/3 carry eight static building lamp-visibility weights.
- Eight original lamp heads gain warm HDR undersides and bounded normal/material-dependent direct PBR illumination in the existing base pass. No new Unity Light component, geometry, shadow map or ForwardAdd pass. Intensity28, range16module metres, smooth cone/cutoff, Frame-aware positions/up/distance scaling. Coated pixels can evaluate16 direct BRDFs. Static visibility is vertex/11-box based; moving car/bench/foliage occlusion is not fully shadow mapped.
- Road overlay batches repair / white / yellow / asphalt / dark now receive the existing directional car shadow and contact AO as well as ground.*. This fixes bright repair polygons inside car shadows. White/dark batches include some non-road pieces; height/normal gates localize contact AO. Static shadow casting stays off. Policy applies to both Mercer profiles.
- Sunset bloom0.06, existing native tone/displayFXAA preserved. New sunset garage angle avoids the strongest mirror-sun hood glare and the menu says EARLYEVENING. Fine highlight/Nocturne front-quarter flattening remainsP2.

r26 was retained as a borderline dark/glare experiment. r27 full packet was explicitly rejected on twoP1s: Luna became navy/plum and repair overlays punched holes through the car shadow. r28 closes both in matched actual frames; Nocturne side confirms dark blue-grey identity survives its pale reflected hood. Preserve all failed code/player/derivative/evidence packets. See SUNSET-ITERATION-r26.md, SUNSET-ITERATION-r27.md and LIGHTING-VISUAL-REVIEW-r27.md. No material repaint/exposure clamp was used to hide them.

## Exact identity and verification

Player SHA256: bbea8c386456dd9c07dd2348c5b2dd23618aa741bdba69dd14088990aead2aa8.
Source fingerprint: baf3a961c9ac75792e9150a4d3c16e9c8ebb8f042252a78be594cb575fe9580e.
Runtime implementation checkpoint:0ec89d0e, following7be72a57/5d4af194. Build succeeded with0 errors and4 retained Body/FXAA compiler warning records. No warning-free claim.

Exact204simulation +495loaded-rig +154runtime checks and10menu checks pass. Sim/loaded reports are raw byte-identical to r25. Runtime report changes9lines solely in transient material-instance IDs; normalization of only those IDs gives exact equality. All 18 Sim sources remain unchanged. Headless probes use world 0/daylight and do not prove the new sunset garage angle or receiver policy; actual frames do.

Independent technical audit verified5411source,147player,62delivery and2239original-evidence file hashes with no drift;70normal pose ticks/fingerprints match r25. All8 sampled unsupported tyre weights are zero;29 real D3D heroNocturne canvas checks pass. Mid/far GPU canvas and exhaustive continuous mechanical/lighting coverage remain unverified.

Normal packet:evidence/cinder-unity-r28/review,6 unchanged stills and one silent69 second/2070 frame original-player clip, full decode/source/player/evidence hashes. Gallery:art-review/unity-r28/index.html. Focused lamp-review drive is a diagnostic initialZ49, separate from the normal69 second packet; cockpit is a normal camera6 take. Packager rejects diagnostic flags. Reports:LIGHTING-VISUAL-REVIEW-r28.md, SUNSET-QUALITY-REVIEW-r28.md, SUNSET-TECHNICAL-REVIEW-r28.md.

## Cost, guards and next work

Paired Catrina mode1 r25/r28: median33.3414/33.3378ms, p9936.0492/35.0822ms, draws219/219, active geometry693585/693585. External peak436563968/462155776bytes (+25591808bytes). This is short capped960x600/30 PNG-IO evidence, not isolated GPU speed/headroom or handheld approval. City geometry/material count is unchanged, but new vertex attributes and shader work cost memory/bandwidth/ALU.

Existing hidden/silent/bounded/sequential guards stay binding:960x600/30,no MSAA,one 512 shadow,2 GiBprocess job,4 GiBfreeRAM/15 GiBdisk,cooldown,all pause markers,mutex/watchdog. Never clear a pause or kill another project. Build a new unique revision with RUN-BUILD-RUNNER.cmd -Revision cinder-unity-r29; sign, exact-probe, capture, review. Always pass Revision explicitly to the source runner (its old optional defaultr24 is archived). Do not edit manifest-listed sources after a final build and claim the old player covers them.

builds/ retains r25 control and r28. r24/r26/r27 players and failed CPU derivatives are archived under build/_archive. No user file was deleted. Other lanes' dirty native work remains untouched and excluded. Videos stay local/off GitHub. No other project was modified.

Remaining P2: coarse long/static shadows, approximate dynamic lamp occlusion, pale reflections/fine chrome/roof glass contrast and nonexhaustive temporal shimmer/bloom assessment. City still needs richer storefront/social character and better foliage. Native lamp-toggle/service helpers remain partial. This profile is not exhaustive native handling/feature parity or production art.

Playbook taskcmw9qrsq000alle018qlbcxni, own seatz2-codex@agents.playbook. Active Bridge threadgen-cinder-unity-r9-visual-regression-independent-native-com. Standard helper works; no service-account/key workaround. For packaging from PowerShell7, remove PSModulePath only from that process so child WindowsPowerShell uses its signature module; keep actual signature verification.
