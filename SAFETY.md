# Conservative evaluation after a full-system lock

November3 movement/audio revision: the signed game has a CPU-only
`Run-Evaluation.ps1 -Example timber_rally -Vehicle safari -PhysicsAudit` mode
that returns before Canvas/audio/renderer construction. It uses the same
process/memory/deadline supervision. New physics, camera, tyre-contact and audio
work adds no GPU targets or higher-resolution profile. All native trials remain
sequential960x600/30FPS/2GiB. The first film and failed prototypes are retained.

The actual CMD launcher exposed an unavailable Windows PowerShell Get-FileHash
script module. SHA256 now streams through the built-in framework with verified
identical hashes; no profile or security-policy change is needed. The diagnosed
pre-process pause is archived under `build/incidents/launcher-hash-20261103`.
The successful native launcher smoke is `20261103-080132-589`; it verifies start,
sound-toggle/cockpit controls and a driving-key event, not human handling feel.

Update: Oliver authorized continuing the examples. Seven scenes across five
executables completed short supervised captures on November 1 after the guards
were installed. The validated conservative profiles are available through
`Explore-Examples.cmd`; each run defaults to 60 seconds. The editor and the
standalone upstream water example remain outside the default validated list.
The separate Cinder Forest Rally candidate subsequently passed a bounded full
scripted lap with rock/tree collisions and a single 512-pixel local shadow map.
No live keyboard feel or long-session stability acceptance is claimed.

Oliver reported that the entire computer hard locked during this evaluation on
November 1, 2026. Unrestricted graphics testing remains paused. Do not interpret a successful build,
earlier screenshots, or a scripted lap as proof that this machine is stable.

Windows recorded an unexpected shutdown (Kernel-Power 41 / EventLog 6008) and a
subsequent boot at 17:43 Pacific. The cause is unconfirmed. WER also replayed
GPU watchdog reports referencing older September dump files; those do not prove
that the new demo caused a GPU timeout. No current dump was identified.
Local diagnostic records are under `build/incident` and are not committed.

## Safeguards now implemented

- All supplied launchers go through `Run-Evaluation.ps1` and refuse to start while
  the tracked `EVALUATION-PAUSED.txt` or local `build/GRAPHICS_PAUSED.txt` exists.
  The initial tracked pause was replaced by `EVALUATION-LIMITED.txt` after the
  authorized trials. Only the five validated conservative profiles launch by
  default. Nothing automatically restarts a failed demo.
- The supervisor permits only one evaluation at a time. It logs stdout, stderr,
  outcome and elapsed time in a separate `build/sessions/<timestamp>` folder.
- A Windows job limits each process to 2 GiB of committed memory and kills the
  child when the supervisor exits. Assignment failure stops the launch.
- Evaluation sessions default to 60 seconds (maximum 300). The engine exits at
  the requested deadline; a separate process enforces an additional hard timeout.
- A rendered-frame heartbeat is checked by the supervisor: 20-second startup
  budget and 8-second stall budget. A failed or stalled session pauses launches.
- The evaluation environment caps windows at 960 x 600, disables window MSAA,
  limits rendering to at most 30 FPS, and stops rendering while unfocused or
  minimized. Escape closes the application.
- Our two demos also cap frames when launched directly, use smaller targets,
  disable shadows/bloom/MSAA, and reduce the driving forest to 180 trees.
- Cinder Forest Rally is an isolated additional candidate. It retains the same
  frame/window/process/time limits, uses a single 512-pixel shadow map confined
  to the nearby road/car, and excludes alpha-tested canopy from that shadow
  pass. Its 180 detailed trees are supplemented with 240 simpler distant trees
  and 9,000 grass blades. The older demo profiles remain unchanged. Sound is
  opt-in with M or the explicit Start Run + Sound button; capture runs do not
  open an audio device. Three small real-recorded exhaust loops replace the
  former synthesized loop. Sequence recording verifies free disk space and
  the requested output frame count; it retains the same process/watchdog caps.
- The upstream materials showpiece disables MSAA, shadows, GTAO, bloom and outlines.
  The forest profile reduces terrain resolution, grass to 6,000 blades, tree
  density, bushes and flowers. These changes apply only in the evaluation environment.
- Builds use two parallel jobs. `Build-Playground.ps1 -Action Test` currently runs
  only the six selected CPU tests. Automated GPU captures are disabled.

These measures reduce load and bound a user-mode process. A watchdog cannot
guarantee recovery from a kernel-level GPU/driver lock, power fault, or hardware
failure. Windows driver/security/timeout settings have not been changed.

## Validation and next controlled check

The timeout/job cleanup self-test uses a sleeping PowerShell child; it does not
open a graphics context. Bounded graphics captures now pass; live-input and
long-session acceptance remain pending. Earlier captures in `build/captures` are
from the pre-guard configuration. Current captures are in `build/sessions`.

A normal validated demo uses the supervisor, never a raw executable:

```powershell
.\Run-Evaluation.ps1 -Example threepp_showcase -Seconds 60
```

Any failed or stalled session reinstates a local pause marker. Investigate that
session's logs before another run; no automatic retry is performed.

The buggy repair keeps the same graphics limits. Its dust uses 96 soft instanced
quads (one draw) rather than opaque-looking faceted puffs, with bounded particle
lifetimes. The CPU-only RallyVehicle test checks actual fixed model bounds
against the full tyre envelope, course contacts and particle render-buffer
movement/fade. It is included in the evaluation test preset.

The cockpit/suspension revision retains the same evaluation limits. View 3 adds
a fixed-FOV driver camera; the CPU rig tests also cover the new arm arc, coil
geometry, camera seat and steering/input mapping. No driver, timeout, MSAA,
shadow-map or postprocessing limits were raised.


## Current reference refinement

Resolution/FPS/Windowsjob/deadline/heartbeat limits remain unchanged. Native runs
stay sequential. New effects have fixed pools:192dust quads,64gravel instances,
768short-lived tyre segments. The new Safari asset and1KHDRprobe load locally;
no runtime asset downloads or new graphics backend. Capture results record
executable/model hashes so visual reviews identify their actual artifact.

`-VehiclePortrait -PortraitAngle front|side|rear|top|tail|rear-detail|front-detail` is a capture-only diagnostic
court, never a replacement gameplay camera. It uses the actual vehicle geometry,
materials and daylight on a flat support plane for unobstructed comparison.
CPU testing opens no graphics/audio context; native captures use the supervisor.
`-PortraitEnvironment daylight` selects the existing procedural sky/ground
reflection environment for inspection only. The default `forest` uses the
accepted HDR probe; normal play remains on that default. This changes no
texture/framebuffer budget or per-frame render pass, and results record the selection.
`-PortraitShadows stock|off` is a matched inspection-only control for the
Safari receiver-plane shadow repair. `default` retains the Safari correction;
normal gameplay and the original buggy keep their selected rendering paths.
These controls use the same capture size, process guard and deadline.


Current execution gate (November2): WindowsApplicationControl rejected the fresh
unsigned timber_rally.exe before process startup (CodeIntegrity3033/3077).
This was not a new graphics hang.
The user approved the existing Azure workflow for current and subsequent local
review builds. Signing succeeded; Authenticode, timestamp and the expected
Oliver Smith publisher verify. Automatic approval review separately rejected
the incident-acknowledged native launch because of residual disruption risk
after the prior full-computer lock. The user explicitly approved resuming guarded
native trials. Signed capture221426-178 exited0 with empty stderr,168747008bytes
sampled peak memory and1.18seconds wall time. That startup-only pause is archived
with resolution inbuild/incidents/application-control-20261102. Side/rear captures
also exited0. No Windows security setting changed; all graphics caps remain.

The optional1920x1200 capture profile is implemented but has not been run.
Automatic approval review rejected raising the explicitly approved960x600 cap
after the earlier hard lock. A separate user approval is pending; its absence
does not authorize higher resolution. Current native work remains960x600.
If approved, the first trial is one still. Higher-resolution video additionally
requires whole-vehicle review>=8.0/all five categories>=7.0 on the exact runtime
asset and renderer executable hashes, and at most180total frames including
warmup. The2GiB/30FPS/watchdog/mutex limits remain. A rear-only visual pass
cannot satisfy that whole-vehicle gate. `-PortraitOrbit` is a capture-only
front/side/rear sequence with a bounded20degree camera move; it does not
change the playable cameras or raise the frame/resolution limits.
