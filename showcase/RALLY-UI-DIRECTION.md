# Cinder Forest racing HUD refinement

Scope: extend the existing native C++ rally candidate. Preserve its gold,
warm-white and restrained-gold forest identity, vehicle, course and conservative rendering
limits. This is a local UI addition, not a new visual-world concept tournament.
Mode: Experience. Driving and the visible road are primary.

OWN-WORLD: a small gravel time-trial event. Live course map, eight checkpoint
states, lap stopwatch and best session time, speed, automatic gear and RPM.
There are no fictional opponents or invented race positions.

FORM: floating instruments in the corners, a compact navigation cue above the
road, a thin progress ribbon below. No rectangular background panels, including
menus/results. The car and road remain clear. Ready, countdown, pause and finish
are genuine race states with working actions; menus hide inactive instruments.

TYPE: locally bundled Rajdhani SemiBold (SIL OFL), 14-62 px for HUD information.
The normal 960x600 desktop game surface is the target; no mobile support claim.

COLOR/MATERIAL: floating ivory numerals, hairline course/RPM geometry and a
restrained gold accent. There are no black translucent backgrounds or filled
gear badges. A single restrained offset glyph shadow protects text against the
world; map lines have a fine dark under-stroke. Completed checkpoints use muted
green. No fake material, scene veil, blur or additional postprocessing.

MOTION/TRUTH: instruments derive from the same powertrain, route and driver
state used by gameplay. The stopwatch stops at the finish. Scripted footage has one quiet disclosure line. Three real CC0 exhaust loops blend by RPM/load and dip on shifts.
Capture audio is rebuilt from the logged powertrain values without opening the
Windows endpoint. Physical input and heard native audio remain human checks.

Quality bar: instantly recognizable racing instruments with clear current
values, readable against sky/foliage, correct route/finish states, and no UI
covering the central driving view. This does not claim reference-game parity.

Pinned brief: Oliver requested typical racing UI and real exhaust, then said:
"make the ui look more subtle. I'm not a fan of the black see-through backgrounds.
Keep it AAA." Restraint, floating type and fine strokes override the former
matte instrument-face direction. No claim that the entire game is AAA quality.
