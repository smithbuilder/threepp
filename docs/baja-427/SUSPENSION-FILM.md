# Baja suspension close-ups and optional boost — November 5, 2026

User requested truck close-ups over bumps, cabin shots, and a jump/booster for an arcade feel. Delivered46-second native film `build/truck-suspension-film/Baja427-Suspension-Cabin-Boost.mp4`, SHA256 `16d053b788309e277cbf3c841afed96297225030f425c85bad2b52054c12ed00`,11,182,885bytes/1380frames.

This uses the completed coupled Bullet playground, not the earlier race's reduced vertical ride. Current signed playground executable SHA256 `3F2BDFBFB84649675E8858CEA38840634E4FB3ED43F0AFBA649678EFB1271D9C`. Baja model remains the exactF3AEA638... v3 GLB; no geometry/texture/rig/package changes. Cabin view lowers smoked-glass opacity only while inside; exterior restores it. Portable local camera coordinates are in `DRIVER-AND-SUSPENSION-CAMERAS.json`.

Added close front/rear and driver's-eye cameras, labelled capture-only service cutaways and half-speed capture. Half-speed keeps240Hz integration and renders30 real states per playback second; no optical interpolation. Front/rear cutaway traces and exterior/cabin jump traces are bit-identical for every logged physics field. Bump views show roughly13–15cm of wheel movement. The two jumps produce41 fully airborne rendered states total, then return to four-wheel support upright. Boost is logged off during those fully airborne states.

Optional boost is isolated in engine-independent `showcase/PlaygroundArcade.hpp`:a2.5second energy budget,6second recharge, at most2x existing drive force, still limited by tyre grip. It requires at least2 supporting tyres, forward throttle, and no brake/handbrake. It applies no launch impulse, pose edit or air thrust. Default is off. In the playground enable **Arcade boost (hold B)** and hold B with throttle. Trail-assist filming pulses it before the first ramp.

Exact-build CPU acceptance session `20261105-101516-206` passes90 checks across3vehicles/8areas. All79 old baseline check values are unchanged. Added grounded acceleration, brake cancellation, absent airborne propulsion and boosted-ramp flight/upright landing checks. Five invalid new profiles reject with their intended guard reasons. An initial invalid test invocation was caught and retained separately; the final guard test uses named parameters and validates the expected rejection text.

Final movie sessions:

- `20261105-101709-774`:front complete,180recorded+120warmup.
- `20261105-101904-652`:front service half-speed,240recorded+240warmup.
- `20261105-101948-141`:rear service half-speed,240recorded+240warmup.
- `20261105-102102-759`:cabin whoops,180recorded+450warmup.
- `20261105-101546-066`:side boosted jumps,300recorded, movie uses30–299.
- `20261105-102226-633`:cabin boosted jumps, same300states/range.

All exit0/empty stderr at960x600/30fps, same signed binary/model, unchanged512px local shadow/2GiB job/heartbeat/deadline/mutex. Full audiovisual decode passed. Reviewed all six views and16 decoded samples covering every hard cut, airborne states and landing; maximum compression RGB mean error1.94/255. Audio is reconstructed generic engine/tyre/load-timed thumps, not endpoint recording, measured -18.0LUFS/-4.9dBTP. Cabin remains simple; hands-on feel, listening and long-session performance are not inferred from tests.

Movie assembler: `scripts/render-truck-suspension-review.py`; replay/source/hash evidence and baseline snapshots: `build/truck-suspension-film`. No native run/pause marker remains at completion. Preserve all previous films, v3 pack, `safari.jpg`, existing playground/world routes and dirty work. No commit, push or publication. Older playground delivery receipt remains historical; current build/film bindings are in `build/truck-suspension-film/delivery-receipt.json` and the current `latest-audit.json`.
