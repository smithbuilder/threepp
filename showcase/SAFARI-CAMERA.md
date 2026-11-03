# Safari exterior camera clearance

The native film review found the chase camera crossing an overhead checkpoint
beam. A first hard clamp removed that intersection but produced a one-frame
push-in. The current Safari camera anticipates the crossing and retains an
immediate safety clamp.

`RallySafariCameraClearance.hpp` checks the eight real gate beams and sixteen
posts. Each frame prepares their inverse transforms and clearance-expanded
local boxes once. A fixed-size polygon clips the camera boom's continuous
0.55-second translational forecast against those boxes. The boom contracts
gradually, follows the existing independent 5/s unobstructed camera position,
then recovers. Observed target height change includes rising terrain in the
forecast. The final present-time clamp protects against prediction error.

The query uses 0.30 m world clearance and 0.02 m separation, with inverse-row
norms preserving clearance under scale. Invalid inputs, a target inside an
obstacle, and rejected forecasts are reported. No world/body transforms,
geometry, visibility, material, collision response or render targets change.
The original buggy retains its existing camera path. This covers the actual
gate boxes; it is not a general scene/foliage collision system.

The CPU suite exercises rotated/scaled boxes, finite segments, nearest
obstacles, current clearance, smooth release, cuts, rejected forecasts, no
compounding and a captured rising-ground path. Actual C++ results:

- Flat13.5m/s crossing: maximum fraction step0.039251;17 anticipation frames
  before the first full-boom obstruction;30,960 independent clearance samples.
- Captured rising-ground fixture: maximum step0.018164; former-snap interval
  maximum0.016507;16 anticipating frames before that interval.

The native probe also removes the banner plane and the original79-to80 snap.
Frame CSV records absolute boom fraction, forecast fraction and hard-clamp
flags; session telemetry records invalid/target-inside/rejected counts.
Continuous playback and human comfort remain separate from sampled evidence.

Portrait capture suppresses interactive race menus while keeping the native
inspection label. The normal interactive start/pause/results menus remain on
the race route. All capture profiles retain the960x600/30FPS/2GiB supervisor.
