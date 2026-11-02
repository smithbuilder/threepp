# Reproduce the cockpit / articulated suspension edit

Generated media and renders stay in ignored `build/cinder-film`. This source
project pins HyperFrames 0.9.3. Previous delivered MP4 files remain local.
Current delivery: `build/cinder-film/Cinder-Forest-Cockpit-Suspension.mp4`.

Build with `Build-Playground.ps1`. For fresh footage, run one supervisor at a time:

```powershell
.\Run-Evaluation.ps1 -Example timber_rally -Seconds 45 -Sequence -AutoDrive -Frames 300 -WarmupFrames 30 -View 3
.\Run-Evaluation.ps1 -Example timber_rally -Seconds 55 -Sequence -AutoDrive -Frames 240 -WarmupFrames 270 -View 2
```

Each prints its own `build/sessions/<stamp>`. Retain all process/FPS/window/disk
and watchdog checks. Copy this composition into `build/cinder-film`, preserving
any edits there. From the repo root, encode each session with:
`node scripts/encode-rally-capture.mjs SESSION OUTPUT.mp4`.
Use output names `build/cinder-film/assets/cockpit-drive.mp4` and
`build/cinder-film/assets/coilover-side.mp4`; copy the side sequence's
`frame_00239.png` to `assets/cockpit-end.png`.

Sound is rebuilt from recorded powertrain state using the same CC0 exhaust as
the native game. Capture opens no audio device and its disclosure is retained.
From `build/cinder-film`:

```powershell
npx.cmd --yes hyperframes@0.9.3 check --json --no-browser-gpu
npx.cmd --yes hyperframes@0.9.3 snapshot --review --no-browser-gpu
npx.cmd --yes hyperframes@0.9.3 preview --background
npx.cmd --yes hyperframes@0.9.3 render --output Cinder-Forest-Cockpit-Suspension.mp4 --fps 30 --workers 1 --no-browser-gpu --low-memory-mode --crf 18 --video-frame-format png --frames-cache-dir off
```

Inspect all review sheets and decoded final frames; verify full decode,
H.264/yuv420p/AAC 48k, 22-second duration and fast-start metadata. Do not publish
or upload as a side effect of making the local video. `COCKPIT-REVIEW.md` records
what the checks establish and what still needs human driving/hearing judgement.
