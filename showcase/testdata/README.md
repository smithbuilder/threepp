# Ride regression fixture

`safari-native-18mps.ride.csv` contains the native game's ride-model inputs
from a supervised standard 900-frame Safari autodrive lap, before the
projected contact repair. It was copied byte-for-byte from session
`20261102-235806-999/drive.ride.csv` on 2026-11-03. Its SHA-256 is
`A7004F808497FD0996F7166B2C9C7FC6B83C2F842072CBEC9022CC1A482EFCFB`.

The ten columns are frame, driving flag, simulation time, dt, local game X/Z,
heading, steer angle, longitudinal acceleration, and lateral acceleration.
There are 3,483 rows, including 120 Hz driving inputs and 30 Hz post-finish
idle inputs. Coordinates refer to the procedural game course; they contain
no real-world locations or personal data.

Initial ride reset: X=0, Z=90, heading=PI/2. Support height is the existing
`rally::height(X,Z) + 0.02`. Vehicle dimensions, suspension travel, mass and
spring/damping coefficients are unchanged. Cruise target was approximately
18 m/s; the fixture retains the actual acceleration and turning transients.

`RallyVehicle_test` checks the recorded Legacy metrics and the accepted open
buggy response, then checks that Projected avoids the former angular limits
and chassis jacking while maintaining contact tolerance. The standalone
`safari_dynamics_probe --validate-projected --projected --csv <fixture>`
also compares every live state against its independent diagnostic solver.
These are CPU regression checks, not native-input or human acceptance.
