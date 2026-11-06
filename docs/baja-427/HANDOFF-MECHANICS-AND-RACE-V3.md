# Baja mechanical repair and three-vehicle film — November 5, 2026

Completed the requested native race video with Safari, Baja 427 and the original buggy. The later feedback about the floating hitch and unnatural suspension was incorporated before final recording. Work remains local and uncommitted.

## Outputs

- `build/race-truck-film/Safari-Baja427-Original-Buggy.mp4`: 48 seconds, 1,440 native 960x600 frames at 30 fps, H.264/AAC. SHA256 `4989fb8cec0e7a5f0b03510ca01d4222d2e42c131c0673021768f608864c98ff`.
- `build/baja-427-v3/mechanical-review-sheet.jpg`: native hitch, front/rear service cutaways and underside. Individual PNGs and session bindings are alongside it.
- `build/baja-427-v3/Baja-427-Modular-v3.zip`: independent GLB, five original PNG maps, dimensions/pivots and import notes. No engine binary or temporary sampled audio.
- `build/race-truck-film/delivery-receipt.json`: exact output, source, model and session identities and verification scope.
- `build/race-truck-film/Safari-Baja427-Original-Buggy-proof/provenance.json`: frame hashes, logged controls, audio sources and assembly evidence.

## Truck changes

The receiver and bumper connect through frame extensions and a crossmember into the rails. The receiver is hollow, with pin bores and a stored pin; recovery eyes have mounting webs and pins. Added steering uprights, wishbone pivot forks, shock towers/clevises and rear suspension brackets. Rear dampers moved inboard to clear wheels. Calipers remain stationary while separate rotors spin. CV and prop shafts meet their bearings/differential. Hollow rear wheel houses, raised spare carriers and fitted straps remove observed cargo/tyre conflicts.

The adapter uses fixed-length front wishbones, a rigid rear axle with trailing/Panhard arcs and small elastic bushing articulation. Damper metal parts retain their lengths and telescope; only springs change axial length. A separate seven-coordinate vertical ride uses 2,200 kg sprung mass and the supplied workbook's wheel rates, gravity, tyre compliance, damping, bump stops and weight transfer. Authored hub travel is 0.268–0.52 m around 0.4 m rest. The race still has scripted planar motion; this is not complete coupled vehicle physics or a handling comparison.

Canonical GLB SHA256: `f3aea63858c923f1de2ae97a922341758a978a2ddc3215a0fffbbfde6ac0f72a`. 11,295,608 bytes, 246,048 triangles, 150 batched meshes, 218 nodes. Metres, +Y up, +Z forward; root Y=0.07 nominal static placement. Library manifest records actual bounds and interfaces. The receipt checks parity between source, library, current rally/bench copies and v3 package.

## Evidence and limits

Serialized geometry audit passes. Assembly audit matches 3,732 authored parts to actual serialized vertex ranges before checking selected mount connections and clearances: spare/wheel-house 32.7 mm, rear damper/wheel axial clearance 37.4 mm, receiver pin radial clearance 2.50 mm. These are targeted game-asset checks, not an exhaustive collision or structural certification.

Native CPU session `20261104-234925-078` passes 243 mechanical poses, rest, asymmetric bump, drop/settling and 30/120 Hz consistency. Maximum front rigid-arm error 8.94e-8 m; rear elastic joint displacement 6.17 mm; minimum telescopic engagement 47.4 mm. Acceleration/braking weight-transfer assertions also pass. Six explicit CPU tests passed in 27.17 seconds. Do not run the whole CTest preset directly: it includes GL checks outside the native supervisor; earlier incident retained in `build/race-film/VALIDATION-NOTE.md`.

Final race sessions: `20261104-235106-153` (720 frames), `20261104-235557-192` (720 warmup + 720 frames). Same signed binary `F68C9D34C0A7158CD954A45A7B0F4FD2BE9565CAF3F6977A915E360C54AC9965`, final truck and unchanged Safari body. Both exit 0/empty stderr; every first-take state matches second-take warmup. Minimum conservative planar envelope gap 0.385 m. Finish times: Safari 36.184 s, Baja 36.401 s, original 37.301 s; all subsequently brake to rest. Five invalid capture profiles reject before launch.

Picture is actual native capture without generated frames, scaling or interpolation. Audio is reconstructed from logged runtime bands/camera positions. Safari retains deeper low-RPM Dakar samples; original/truck use existing CC0 generic loops with lower truck RPM mapping. Measured -18.1 LUFS/-5.0 dBTP; full audiovisual decode passed. Six encoded samples match native sources within normal compression error; 16 native samples and four mechanical views were visually reviewed. Existing foliage flecks, sparse woodland, dust puffs and brief gate occlusion remain. Human sound, controls, enjoyment and handling acceptance remain open.

## Resume

Preserve `safari.jpg`, old 44-second film, v2 ZIP and `build/baja-427-v3/baseline`. Normal Safari/original launchers and defaults remain. Capture-only staging widens the road to 13 m at the same vertex/instance budgets. Native launches require signing and `Run-Evaluation.ps1`, 960x600/at most 30 fps, 2 GiB job, heartbeat/deadline/mutex and BelowNormal priority. No pause/active evaluation file was present at this lane's final check.

Concurrent **Build suspension playground** chat owns Playground*, coupled Bullet handling, its facility/UI and launcher. Preserve its shared CMake/supervisor additions and binary. `RallyBaja::present(position,orientation,travel,steering,spin,height)` remains stable. Rebuild/revalidate that target and cached model against the current hash before asserting current Baja acceptance there. Local assist: `build/suspension-playground/BAJA-V3-ASSIST-NOTE.md`. No cross-chat message was sent while the optional permission question remained unanswered.
