# Vehicle Playground Showcase

Local film: **[Vehicle-Playground-Showcase.mp4](outputs/Vehicle-Playground-Showcase.mp4)**.
The 80-second narrated film uses actual 960 × 600, 30 FPS in-engine footage of
Safari, the original buggy and Baja 427 v3. It covers articulation ruts, repeated
bumps, steep grades, the narrow ridge, side slope, two Excitebike-inspired jumps
and the wind-test gantry. Recorded suspension compression drives the wheel bars.

The steep-hill shot deliberately reports that Safari stalls before the crest.
Wind footage shows a steady 20 m/s crosswind; the world also supports gusts.
The wind model uses estimated aerodynamic coefficients, not CFD. Hands-on
vehicle feel remains a review step even though the automated checks pass.

## Watch and edit

- [Exported-frame review sheet](outputs/Review-frames.jpg)
- [Review and limitations](REVIEW.md)
- [Delivery receipt](outputs/delivery-receipt.json)
- [Narration and chapter text](narration.json)
- [Exact shot ranges](edit-manifest.json)
- [Source sessions and hashes](source-manifest.json)

The editable HyperFrames composition is `index.html`, with six scene files in
`compositions/` and render assets under `assets/`. Video binaries are deliberately
excluded from `main`; a fresh checkout needs the original native clips copied
into `assets/video/` before preview or render. The delivered MP4 remains local
under `outputs/`. Audio, fonts, source and receipts are versioned. With the clips
available, preview from this folder:

```powershell
npm ci
npx.cmd --yes hyperframes@0.9.16 preview --background --no-open --no-browser-gpu --port 3016
```

Open `http://localhost:3016/#project/playground-showcase`. The **Edit with Framey**
button opens the HyperFrames desktop app. After edits there, run
`npx.cmd hyperframes catch-up` before editing the same files here.

To verify and render from this folder:

```powershell
npm run check -- --json
npm run render -- --quality delivery --no-browser-gpu --low-memory-mode --output outputs/Vehicle-Playground-Showcase.mp4
```

The CLI is pinned to 0.9.16 in `package.json`. This render uses one worker,
software browser capture and CPU encoding. It does not launch native graphics.
Capture of new native footage must continue to follow the repository's
`SAFETY.md` and guarded `Run-Evaluation.ps1` workflow.

`assemble.py` is the original composition generator; running it overwrites the
HTML and its audio mix settings. Preserve any manual edits first and reapply
the music carve recorded in `proof/carve.log` if regenerating. The local source
media and current assembled HTML are already prepared; no remote generation is
needed to rerender on this machine. The recorded voice files are included with
the project.

## Verification

The delivered MP4 is H.264/AAC, 80.000 seconds, 2,400 frames. Full decoding passes.
Decoded frames from every chapter were visually reviewed. Integrated audio is
−17.4 LUFS with −5.7 dBFS true peak. Sound was measured, not listening-reviewed.
See `proof/` for composition checks, render logs, snapshots and audio reports.

## Credits

Narration: fleet Voicebox, Kokoro `bm_george`. Native source footage is silent;
the film adds narration and music, with no simulated engine soundtrack.

Music: **Deliberate Thought**, Kevin MacLeod
([incompetech.com](https://incompetech.com)), licensed under
[Creative Commons: By Attribution 4.0](https://creativecommons.org/licenses/by/4.0/).
An excerpt was trimmed, normalized, faded, equalized and ducked under speech.
The film includes an on-screen credit. Include this credit in any published
description too. The fleet's source license record is
`assets/audio/MUSIC-ATTRIBUTION.md`.

Typography: Barlow and Barlow Condensed, SIL Open Font License, bundled with
`assets/fonts/OFL.txt`. Existing vehicle and terrain assets remain subject to
the repository's `THIRD_PARTY.md` records.
