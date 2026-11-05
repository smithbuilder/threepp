# Showcase review — November 5, 2026

The chosen film is a proving-ground walkthrough: introduce the three vehicles,
show contact and body movement, expose difficult terrain, compare jumps, then
show wind forces and the reusable testing world. A complete three-vehicle test
matrix would be repetitive for this length; a stunt reel would give the jumps
more attention than the suspension and wind work. The walkthrough fits the 80-second running time. Native footage plays at normal speed with restrained labels and music.

## Observed picture

The chapter images read as three distinct off-road vehicles in one dirt proving
ground. The wheel bars identify recorded compression; ramps make takeoff and
landing visible; the wind gantry and arrows indicate the direction of the
simulated crosswind. No fabricated gameplay or before/after comparison appears.

Reviewed beat and phone sheets, five chapter-cut strips, final midpoint frames,
and eight frames decoded from the delivered MP4. The decoded review sheet is
`outputs/Review-frames.jpg`. The final export's terrain banner sits at the top,
leaving the hill vehicle's wheels visible. The compression bars use the recorded
sample at each exact endpoint, correcting the initial one-sample lag.
An eight-frame motion sheet at 42.0–43.4 seconds also shows Safari's landing,
rebound and settling in sequence (`proof/jump-motion.jpg`).

The weakest shot is the distant ridge view: it explains narrowness and height,
but offers little detail of individual wheel movement. A future capture could
pair it with a close view from the same run. Small native HUD figures are
secondary diagnostics, best read at desktop size. Main chapter titles carry
the film at small sizes; narration carries the detailed explanation.

A separate visual reviewer found no P0 in the supplied sheets. Their P1 notes
were phone-size diagnostics, small gauges, the distant ridge vehicle, and a
more specific final feedback request. These remain deliberate limits of this
desktop review export: the native HUD preserves capture context, gauge detail
is readable at native size, the wide ridge shows the course scale, and the
closing narration asks for hands-on feedback. A phone-focused version should
use larger gauges and labels, a closer ridge shot, and the explicit cue
“Feedback on suspension, grip and landings.” The reviewer assessed stills,
not continuous motion or sound.

## Measured verification

- HyperFrames composition check: pass, zero errors. Runtime, layout, contrast,
  craft and audio checks pass. Fourteen sampled text contrasts pass. Automated
  motion inspection was disabled; motion was assessed through footage samples.
- Retained 13 lint warnings: 11 describe nonzero media starts inside scenes,
  which intentionally use composition-local time; two flag four labels sharing
  a chapter track, which intentionally follow the four short shots.
- Delivered export: 960 × 600, 30 FPS, 2,400 frames, 80.000 seconds, H.264/AAC.
  Full-file decoding completes without errors. The render used one software
  capture worker and CPU encoding.
- Audio: −17.4 LUFS integrated, −5.7 dBFS true peak. Narration and music exist
  throughout their planned ranges, with room below clipping. **Sound was
  measured, not heard.** No human listening or physical driving review occurred.
  HyperFrames' separate signal analysis reports −17.3 LUFS and zero clipped
  samples; its only detected silence is the intended final half-second fade.

## What the film establishes

The footage comes from the final signed playground build and the current Baja
model. Source frame and session hashes are in `source-manifest.json`; exact cuts
are in `edit-manifest.json`. The 79 physics checks and six regression suites
are prior verified playground results, not tests invented by the video project.

The longer hill capture found a limitation: Safari stalls before the crest.
The film calls that out as remaining tuning work. The wind chapter shows steady
20 m/s crosswind; repeatable gusts are supported by the world but not shown in
this footage. Aero coefficients remain estimates and raycast wheels simplify
tire contact. The film does not certify subjective naturalness or replace
hands-on acceptance.
