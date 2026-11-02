# Reproduce the viewing edit

The editable film source is here; generated footage and renders stay in the
ignored `build/cinder-film` folder. HyperFrames CLI is pinned to 0.9.3.
The local delivery is `build/cinder-film/Cinder-Forest-Rally-UI-Exhaust.mp4`.

Build the candidate with `Build-Playground.ps1`. For fresh footage, explicitly
run these supervisor commands one at a time from the repository root:

```powershell
.\Run-Evaluation.ps1 -Example timber_rally -Seconds 35 -Sequence -AutoDrive -Frames 240 -WarmupFrames 30 -View 0
.\Run-Evaluation.ps1 -Example timber_rally -Seconds 45 -Sequence -AutoDrive -Frames 180 -WarmupFrames 270 -View 2
.\Run-Evaluation.ps1 -Example timber_rally -Seconds 65 -Sequence -AutoDrive -Frames 180 -WarmupFrames 720 -View 1
```

Each command prints its distinct `build/sessions/<stamp>` directory. Keep the
watchdog, FPS/window/memory/disk checks; do not run raw graphics executables.
Copy this composition project into `build/cinder-film`, preserving any user
edits there. Run `node scripts/encode-rally-capture.mjs SESSION OUTPUT.mp4`
for each sequence, using output paths under `build/cinder-film/assets` named
`chase-final.mp4`, `side-final.mp4` and `finish-final.mp4`. Copy the finish
sequence's `frame_00179.png` to `assets/finish-frame.png`.

The encoder uses the same real recorded exhaust bands and captured powertrain
values as the native candidate. Capture keeps the Windows audio endpoint closed;
the video is labeled SCRIPTED GAMEPLAY / AUDIO REBUILT. This is not heard/native
input acceptance. Source audio receipts/license are in `showcase/assets`.

From `build/cinder-film`, run:

```powershell
npx.cmd --yes hyperframes@0.9.3 check --json --no-browser-gpu
npx.cmd --yes hyperframes@0.9.3 snapshot --review --no-browser-gpu
npx.cmd --yes hyperframes@0.9.3 preview --background
npx.cmd --yes hyperframes@0.9.3 render --output Cinder-Forest-Rally-UI-Exhaust.mp4 --fps 30 --workers 1 --no-browser-gpu --low-memory-mode --crf 18 --video-frame-format png --frames-cache-dir off
```

Inspect the review sheets and decoded final frames. Confirm full decode,
H.264/yuv420p video and AAC audio, duration 24 seconds and a fast-start MP4.
Do not publish or upload as a side effect of rendering.
