# Reproduce the wheel refinement edit

Generated media/renders stay in ignored `build/cinder-film`. This source pins
HyperFrames 0.9.3. Older delivered films remain local. Current delivery:
`build/cinder-film/Cinder-Forest-Wheels.mp4`.

Build with `Build-Playground.ps1`. Run one supervisor at a time:

```powershell
.\Run-Evaluation.ps1 -Example timber_rally -Seconds 45 -Sequence -AutoDrive -Frames 240 -WarmupFrames 30 -View 2 -WheelInspect
.\Run-Evaluation.ps1 -Example timber_rally -Seconds 55 -Sequence -AutoDrive -Frames 300 -WarmupFrames 270 -View 2
```

Each prints its `build/sessions/<stamp>`. Keep all FPS/window/memory/disk and
watchdog checks. WheelInspect is a capture-only diagnostic, not a player view.
Copy this composition into `build/cinder-film`, preserving edits already there.
From the repo root, encode each session:
`node scripts/encode-rally-capture.mjs SESSION OUTPUT.mp4`.
Use `build/cinder-film/assets/wheel-detail.mp4` and
`build/cinder-film/assets/wheel-driving.mp4`. Copy detail `frame_00150.png` to
`assets/wheel-end.png`. Sound is rebuilt from game powertrain state using the
same CC0 exhaust. Native capture opens no audio device; disclosure is retained.

From `build/cinder-film`:

```powershell
npx.cmd --yes hyperframes@0.9.3 check --json --no-browser-gpu
npx.cmd --yes hyperframes@0.9.3 snapshot --review --no-browser-gpu
npx.cmd --yes hyperframes@0.9.3 preview --background
npx.cmd --yes hyperframes@0.9.3 render --output Cinder-Forest-Wheels.mp4 --fps 30 --workers 1 --no-browser-gpu --low-memory-mode --crf 18 --video-frame-format png --frames-cache-dir off
```

Inspect review sheets and decoded final frames; verify full decode,
H264/yuv420p/AAC48k, 22s duration and fast-start metadata. No upload/publication.
`WHEELS-REVIEW.md` records checks and remaining human acceptance boundaries.
Earlier `BUGGY-REVIEW.md` and `COCKPIT-REVIEW.md` are retained for context.
