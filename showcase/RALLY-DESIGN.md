---
name: Cinder Forest Racing HUD
description: Floating native instruments for the existing single-lap gravel time trial.
colors:
  ivory: "#f6f4e9"
  quiet: "#dfe2d8f0"
  gold: "#e2c174"
  completed: "#bbd5be"
  line-understroke: "#09120f96"
  glyph-shadow: "#070d0bcd"
  checkpoint-pending: "#e8ecde5f"
  ribbon-track: "#f0f1e669"
  map-route: "#e9ebdce6"
  rpm-inactive: "#edefe264"
  action-underline: "#ebeee15f"
  transparent: "#00000000"
typography:
  speed: {fontFamily: Rajdhani, fontSize: 53px, fontWeight: 600}
  stopwatch: {fontFamily: Rajdhani, fontSize: 36px, fontWeight: 600}
  stage-title: {fontFamily: Rajdhani, fontSize: 25px, fontWeight: 600}
  label: {fontFamily: Rajdhani, fontSize: 14px, fontWeight: 600}
  compact: {fontFamily: Rajdhani, fontSize: 13px, fontWeight: 600}
  action: {fontFamily: Rajdhani, fontSize: 21px, fontWeight: 600}
  menu-title: {fontFamily: Rajdhani, fontSize: 38px, fontWeight: 600}
  result: {fontFamily: Rajdhani, fontSize: 58px, fontWeight: 600}
  countdown: {fontFamily: Rajdhani, fontSize: 94px, fontWeight: 600}
spacing: {menu-inset: 16px}
components:
  action: {backgroundColor: "{colors.transparent}", textColor: "{colors.ivory}", typography: "{typography.action}", width: 340px, height: 38px}
  action-hover-focus: {backgroundColor: "{colors.transparent}", textColor: "{colors.gold}"}
---
# Design System: Cinder Forest Racing HUD

## Overview
This documents only the native rally extension within the existing forest candidate. Its established direction is a small gravel time trial with floating warm ivory instruments, fine linework and restrained gold accents. Driving and the approaching road remain primary. It sets no engine-wide or older-demo design rules.
The user requested a subtler UI without black see-through backgrounds. This implemented direction replaces the former matte instrument faces; it does not establish a claim that the entire game meets AAA quality.

## Colors
Ivory carries current measurements and solid glyph interiors; quiet text carries supporting labels. Gold marks the current target, car marker, progress, focused actions and highest RPM ticks. Muted green marks completed checkpoint bars. Alpha values in the frontmatter preserve the actual draw-list colors.
Dark tokens serve only small glyph shadows and fine geometry under-strokes. They are never panel or scene backgrounds. Legacy ImGui button/window color assignments in `rally.cpp` are not visible theme tokens: the current windows use NoBackground and action rows override the fill to transparent.

## Typography
Bundle `Rajdhani-SemiBold.ttf` locally under `rally-assets`; Rajdhani SemiBold is licensed under the SIL Open Font License. Retain its license when redistributing. The font loads at 24px; custom text requests explicit pixel sizes. No alternate body family, line-height system or fallback is specified.
The token roles capture prominent repeated sizes. Additional observed sizes are checkpoint label 16px, distance 24px, gear 28px, GEAR label 11px, menu information 17px, start hint 15px and result heading 30px. Menu text defaults to 19px. Every custom glyph uses the same single offset shadow; do not draw repeated outlines around text.

## Layout
The target desktop surface is 960×600. Stage identity begins at (32,26), with its subtitle at y=55 and eight short checkpoint strokes at y=82. The timer anchors at width−200: label y=27, stopwatch y=46, best y=87. The navigation cue is centered around y=51–72.
The map center is (99,height−89) with world coordinates scaled by 0.55. The powertrain arc center is (width−119,height−70), radius 66. The progress ribbon is 192px long, centered at height−30, with checkpoint and normal-play sound status above it.
Menus/results use an invisible 416px-wide window at (48,162), with 16px padding and (8,10) item spacing. Content is left aligned; action hit areas are 340×38. Countdown floats centrally at y=225. Ready, pause and finish hide the inactive instruments, retaining stage identity and any scripted disclosure.
Anchors follow canvas dimensions; no mobile support or tested responsive breakpoint system is claimed.

## Elevation & Depth
There are no rectangular HUD backings, menu/result fills, scene veils, blur or filled gear badges. One glyph shadow sits at (+0.65,+1.2) pixels. Fine dark under-strokes protect map, RPM, checkpoint and ribbon geometry against foliage; they do not enclose instrument clusters. No extra postprocessing is introduced for the UI.

## Shapes
The course map uses a continuous route, small checkpoint circles and a triangular directional car marker. The RPM instrument has 30 ticks spanning 260 degrees: lit ticks are ivory, with gold at the highest ticks. Standard ticks use 1px strokes and every fifth tick 1.7px, over a 3px under-stroke. Map lines use 1.5px over a 4px under-stroke; progress uses a 1.5px gold stroke. No panel-radius system is visible.

## Components
- **Action rows:** floating ivory text above a 0.75px underline. Hover or focus turns text/underline gold, increases the underline to 1.5px and adds a small right chevron. Fills remain transparent while pressed; native button hit areas retain actual action wiring.
- **Stage and route:** eight bars show completed/current/pending states. The map uses the world route and actual position/heading; navigation reports real distance to the next checkpoint.
- **Timing and progress:** show `MM:SS.mmm`, session best or `--:--.---`, and route progress. Finish records the lap and stops the stopwatch; inactive instruments then hide behind the result state.
- **Powertrain:** speed is absolute velocity converted to km/h. Automatic gear, R for reverse, RPM and lit ticks use real powertrain data. No invented opponents or race positions appear.
- **Ready/countdown:** START RUN + SOUND begins a three-second countdown; actual controls are listed. Countdown is a large floating ivory numeral.
- **Pause:** RESUME, exhaust toggle, RESTART STAGE, BACK TO GRID and QUIT use the same understated action rows.
- **Results:** left-aligned completed lap, best session lap, eight checkpoints and contacts, followed by RACE AGAIN and BACK TO GRID.
- **Capture/status:** one quiet line reads SCRIPTED GAMEPLAY / AUDIO REBUILT. Capture audio is reconstructed from logged powertrain values without opening the Windows endpoint. Normal play shows SOUND OFF/ON near progress.

## Do's and Don'ts
- **Do** preserve floating solid glyphs, fine instrument strokes and restrained gold within the existing forest identity.
- **Do** derive displayed values and states from gameplay, freeze timing at finish and keep the central driving view clear.
- **Do** retain truthful scripted/audio disclosures; native buttons are visible, while physical input remains unverified.
- **Don't** restore black translucent panels, gear badges, text outlines or a dimmed scene veil.
- **Don't** promote these local HUD choices into global engine rules or claim mobile, physical-input or heard native-audio acceptance from scripted footage.

Source of truth: `showcase/RallyHud.hpp`, UI/state wiring in `showcase/rally.cpp`, and `showcase/RALLY-UI-DIRECTION.md`. This is an implementation snapshot, not a human acceptance certificate.
