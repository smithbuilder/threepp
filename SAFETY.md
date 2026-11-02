# Evaluation paused after a full-system lock

Oliver reported that the entire computer hard locked during this evaluation on
November 1, 2026. Graphics testing is paused. Do not interpret a successful build,
earlier screenshots, or a scripted lap as proof that this machine is stable.

Windows recorded an unexpected shutdown (Kernel-Power 41 / EventLog 6008) and a
subsequent boot at 17:43 Pacific. The cause is unconfirmed. WER also replayed
GPU watchdog reports referencing older September dump files; those do not prove
that the new demo caused a GPU timeout. No current dump was identified.
Local diagnostic records are under `build/incident` and are not committed.

## Safeguards now implemented

- All supplied launchers go through `Run-Evaluation.ps1` and refuse to start while
  the tracked `EVALUATION-PAUSED.txt` or local `build/GRAPHICS_PAUSED.txt` exists.
  New clones retain this paused state. Nothing automatically restarts a failed demo.
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
- Builds use two parallel jobs. `Build-Playground.ps1 -Action Test` currently runs
  only the five selected CPU tests. Automated GPU captures are disabled.

These measures reduce load and bound a user-mode process. A watchdog cannot
guarantee recovery from a kernel-level GPU/driver lock, power fault, or hardware
failure. Windows driver/security/timeout settings have not been changed.

## Validation and next controlled check

The timeout/job cleanup self-test uses a sleeping PowerShell child; it does not
open a graphics context. Native graphics and live-input acceptance remain pending
after this incident. Earlier captures in `build/captures` are from the pre-guard
configuration and are not current stability evidence.

A deliberate later trial can use the following command, starting with only ten
seconds and one simple scene, after the machine is otherwise ready. It must not
be run automatically as part of setup or a build:

```powershell
.\Run-Evaluation.ps1 -Example threepp_showcase -Seconds 10 -AcknowledgeIncident
```

This acknowledgment only permits that one supervised trial. The pause marker
remains in place. Remove it only after graphics stability has been established.
