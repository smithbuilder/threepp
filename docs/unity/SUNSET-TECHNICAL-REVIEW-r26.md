# Independent sunset technical review: r26 source checkpoint

November 11, 2026, Pacific. Reviewer: migration_review. Reviewed source checkpoint `7be72a57c9c218bb96e82da66a2ac607a5b1a616`. The reviewer did not implement these surfaces, did not edit runtime/bake source and did not launch an editor or player. The reviewer authored the earlier general Body shader-source dump helper; no generated dump supplies a GPU approval here.

**Source verdict: no remaining identified pre-build blocker in the corrected reviewed code. GPU rendering, cost, final exact-player binding and visual acceptance remain pending.** The observed r26 build receipt reports success, zero errors and four warnings, with source fingerprint `dea7b6c68d5771f8b921045bd2b241779056a9a2a46815cee20dffd2de258bdb`. Fourteen selected owning shader/include/host/view/bake/runner/packager entries were independently hashed against that manifest with no drift. This is a selected source check, not final whole-player/evidence verification.

## Intended change

The authorized direction is an authored approximately 6 pm Mercer scene that remains daylight-readable, not an astronomical clock or night simulation. New sun direction, radiance, sky palette, diffuse SH, fog and fixed street practicals are intentional art inputs. Native PBR material factors and tone-mapping/FXAA math remain the basis. Sunset bloom strength is explicitly 0.06; the daylight control retains r25's 0.10. This is a profile-strength adjustment, not a new post-processing pass.

Reviewed: `CityEveningLighting.cs`, `CinderEveningLighting.cginc`, Body/City/Canvas/CityFoliage shaders, `CinderView.cs`, `CinderGrade.cs`, `StandaloneHost.cs`, the runner/packager, `CinderSunsetBake.cs` and the new `CinderSunsetCityBake.cs`.

## Concrete findings and verified corrections

| Finding | Current source result |
| --- | --- |
| Authored lamp coordinates were compared directly with Unity world positions, failing a translated/rotated/scaled module frame | Host now transforms all eight fixture positions through the actual view Root and uses its up direction |
| Range/power scaling omitted the near-distance cutoff and attenuation floor | Power, range squared, minimum distance squared and attenuation floor now use the same uniform scale squared |
| Runtime fog disagreed with the authored sky recipe | Both now specify density 0.0015 and sRGB fog colour (0.66, 0.59, 0.64) |
| New wide camera 7 selects mid LOD, while the inherited Nocturne roof graphics check inspects hero only | Route limitation acknowledged: wide city views use Catrina; normal Nocturne roof proof uses hero camera 2. The hero gate is not waived |

The practical model's transform correction supports the positive uniform Frame convention. The sun, sky and SH remain standalone-host global environment inputs; this source review does not establish arbitrary rotated-shell environment parity or simultaneous independent city lighting profiles.

## Direct PBR and surface adapters

The common helper constructs direct `UnityLight` values and evaluates Unity's metallic PBR BRDF with a zero indirect term. It does not create Unity Light components, query a reflection cube once per lamp or use an emissive road overlay. The eight fixtures have finite range, downward cone shaping, distance attenuation and finite visibility inputs.

Manual practical evaluation is excluded from ForwardAdd, ShadowCaster and Meta paths. The Body coat's environment fetch is now excluded from ForwardAdd as well, preventing repeated coat IBL when an additive pass exists. Base-pass coating still evaluates both base and coat responses. This is eight authored fixtures, with up to sixteen direct BRDF evaluations on coated Body pixels; it must not be described as eight total shader evaluations everywhere.

The custom EveningStandard structure carries WorldPosition and two four-component visibility vectors. Its adapters populate those fields; City and Body unconditionally initialize tangent-space Normal before optional normal mapping. Canvas and CityFoliage explicitly flip the tangent-space normal for back faces. The common wrapper converts its ordinary material fields into the existing Standard lighting/GI functions. The names and fields are consistent with the custom surface-lighting pattern; the build receipt alone does not prove all generated normals/variants are correct on the GPU.

City/Foliage vertex adapters read `texcoord2` and `texcoord3`. The static bake writes `SetUVs(2)` and `SetUVs(3)`, matching those exact zero-based channels. It rejects occupied channels rather than silently overwriting preexisting data. Body and canvas use visibility one, explicitly accepting approximate dynamic occlusion rather than inheriting unrelated static UV values.

## Static bake and profile boundary

The sunset-city source creates a separate prefab and cloned meshes. It reverses the old analytic shade at the appropriate source query point before applying the new sun shade. Source geometry/normals/tangents/indices/bounds and all UV channels except the two newly reserved ones are compared unchanged, and shared materials are checked against the source. The original prefab is not the write target. Receipt/fingerprint guards preserve previous or partial outputs instead of silently rebuilding over them.

The bake's lamp masks use eleven building boxes at mesh vertices. They are linearly interpolated over the unchanged triangles. They do not establish per-pixel building occlusion, leaf silhouettes or shadows from moving cars/benches. Daylight-adapted ground reduction and the finite original colour approximation also remain limits. The five-ray static sun and soft canopy approximation are art-directed static shading, not a new physical contact surface.

The sky recipe removes the original photographic sun before authoring its own low sun and cloud palette. The visible sky and mirror mip zero include the new disc; diffuse SH and rough reflection mips use the disc-free authored panorama. The source contains white-furnace/hemisphere checks and records disc integration. Actual imported orientation, HDR decode, sun/reflection units, SH response and visible brightness still need exact-player controls. CPU recipe/calibration values are not GPU measurements.

## Host lifecycle and state

The lighting Apply call occurs during module reset/world selection, not in a per-frame light-spawn loop. It updates the single standalone host's sun, sky, fog, SH, cube and fixed lamp uniforms. Switching to the playground/daylight path applies the daylight environment and disables practicals. The owned sky material is reused across switches and disposed at application exit; the view's cloned emissive lamp materials are tracked in its owned list for disposal.

The lighting functions do not write simulation state, force, time, seeded randomness or contact data. The separate bounded `-lamp-review` capture option deliberately selects an initial Z=49 pose and updates the replay's initial state before recording. This is diagnostic initial-condition setup, not an unrecorded lighting force or a normal-play teleport. The runner restricts that option to bounded graphics runs, and the final packager rejects it along with `-city-lighting` daylight/lamps-off/emission-off controls. Thus diagnostic setup must stay outside normal delivery takes.

## Cost and evidence required

No extra shadow map, Unity Light, geometry pass or bloom level is introduced by the practical model. That does not make it free: every eligible shaded pixel has eight range/cone checks, and nearby coated Body pixels may run sixteen direct BRDF evaluations. Static visibility adds two float4 vertex streams and interpolators. These costs must be measured, including foliage and a close car at a live fixture; unchanged draw counts alone cannot establish success.

The sunset prefab and environment add packaged resources, while only the selected environment is instantiated. Runtime memory and editor bake/build peaks still require guarded receipts. Keep the existing 960x600/30, shadow, process and geometry/draw limits. No handheld 1080p/60 or uncapped GPU-time approval follows from a capped capture.

Required before acceptance: exact signed player/source binding; unchanged simulation/mechanism regressions; fresh D3D support and generated base/add variant checks; daylight control preserving the prior profile; matched lamps-off/emission-off at a fixture; palette/readability and moving highlights; shadow/visibility limitations visible in context; normal Nocturne hero roof proof; and paired capped performance. No source verdict approves sunset brightness, exposure, sky orientation, lamp leakage or the final scene's visual quality.
