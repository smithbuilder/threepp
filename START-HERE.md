# Cinder Unity

Current r9 is a technical prototype. Visual acceptance is withdrawn after the native comparison; city, lighting and car finish need restoration. See `docs/unity/reassessment/REASSESSMENT.md`.

The Unity migration centers on lowrider culture: La Catrina, Media Luna and Nocturne. Choose a car in the main garage, cruise Mercer, start a hydraulic session, or visit the workshop test grounds. Safari and buggy racing are deferred from this menu.

The current build/review state is in [the handoff](docs/HANDOFF.md). `PLAY-CINDER-UNITY.cmd` launches the selected signed Windows player through the resource guard. `RUN-BUILD-RUNNER.cmd` builds it with Unity 6000.3.6f1 without opening the editor.

## Controls

| Action | Gamepad | Keyboard / mouse |
| --- | --- | --- |
| Choose garage car | LB / RB | Q / E or arrow buttons |
| Move through menus | Left stick or D-pad | Mouse hover |
| Choose / confirm | A | Enter, Space or click |
| Back / pause | B / Start | Escape |
| Accelerate / brake | RT / LT | W / S or Shift / Ctrl |
| Steer | Left stick | A / D or arrow keys |
| Handbrake | A | Space |
| Hydraulic mode | Y | F |
| Reverse | RB while driving | G |
| Reset car | LB while driving | R |
| Camera | Left stick click | C |
| Look | Right stick | Right mouse drag |
| Settle camera | Right stick click | Choose camera again |
| Coachwork inspection while stopped | X | F1 |
| Nocturne soft top while stopped | View | T |

Settings offer saved display mode, frame limit, v-sync, invert look and sensitivity. The intended normal default is borderless at the desktop resolution, 60 fps, v-sync off. Automated reviews retain the repository's hidden 960 x 600 / 30 fps profile. Escape pauses; quitting asks first. Losing focus pauses play.

Workshop means the vehicle test grounds. The level pad is selected initially; all eight lanes remain in the simulation for migration checks. Hood/trunk/coachwork inspection is a schematic game mechanism. Audio cues are original quiet synthesized placeholders with measured gains in `assets/unity/audio-provenance.json`.

The new solver preserves donor tuning and physical rules, with four 240 Hz internal steps per 60 Hz game tick. It is a managed C# replacement for Bullet, not a promise of identical native handling. Existing C++ launchers, assets and other lanes' work remain available.

Human input feel, heard audio, comfort, comprehension and enjoyment remain UNVERIFIED until Oliver plays. A passing probe is not a playtest, and 1080p/60 handheld performance must be measured before claiming it.
