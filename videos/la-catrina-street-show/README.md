# La Catrina / Street Show

The 48-second street film is rendered and verified: six native shots, 960×600 at 30 fps, with music and reconstructed engine/hydraulic sound. The captured model passed two independent reference-sheet reviews at **8.020/10** and **8.115/10** before production capture.

- Workstation film at `outputs/La-Catrina-Street-Show.mp4`. [Restore the footage in a fresh checkout](LOCAL-MEDIA.md).
- [Airborne poster](outputs/La-Catrina-Street-Show.png), decoded frame 310 at 10.333 seconds
- Workstation editable archive at `outputs/La-Catrina-Street-Show-Editable.zip`, with per-file hashes in `ARCHIVE-MANIFEST.json`. Archive integrity is recorded separately in `proof/editable-archive-receipt.json`.

The sequence is a rolling reveal, repeated front hops, a wheel/suspension close view, left and right three-wheel glides, and a low cruising exit. Each clip retains its complete native frame and normal speed. Opening and closing titles stay clear of the car; no text covers the tricks.

All 1,440 native frame hashes passed. The 240 Hz simulation reported no discarded backlogs. The hop and detail clips contain 3.467 and 1.867 seconds of front-pair noncontact with loaded rear support, followed by four-contact recovery. Each three-wheel glide sustains the intended missing front contact with the other three tires loaded for its full eight seconds. These are sampled simulation results, accompanied by visual frame review; they are not measured real-car performance.

The final MP4 passed full decoding, exact duration/dimension/frame-count checks, a black-frame scan and 28 sampled comparisons to the native clips. The largest mean pixel difference was 2.0765/255 after H.264 re-encoding. Audio measures −20.1 LUFS integrated and −5.2 dB true peak. The producer inspected all 19 pre-render snapshots, the editable preview, and the final review/seam/hop sheets. Independent final editorial evidence is linked from `REVIEW.md`.

The three-wheel shots at 21–37 seconds are shaded and less vivid than the sunny hop section. The car and lifted wheels remain readable. The simulator uses simplified raycast suspension and visual linkage adapters. Sound is an editorial reconstruction from the project's original Sunset Pulse instrumental and credited CC0 engine/lowrider recordings, with nine pump excerpts aligned to measured extension changes. Human listening and continuous real-time playback review are not claimed.

`source-manifest.json`, `source-package-manifest.json` and `proof/delivery-receipt.json` bind the accepted model, reviews, mechanical report, footage, sound and output. `Source/` retains the original reference sheet, the accepted studio receipt and its 16 images, both visual reviews, the mechanical review/reproducer, native receipts and source context. Full engine source and the separate vehicle package remain necessary to recapture a different drive or rerun the mechanical reproducer.

To rebuild from the verified source clips:

1. Run `python build_action_audio.py`, then `python build_composition.py`.
2. Run `python verify_sources.py` to verify the native inputs and restage review/source evidence from the engine checkout.
3. Run `npm run check` and `npm run snapshot`; inspect every output image.
4. Run `npm run preview`, inspect `proof/preview-editor.png`, and confirm its clean stop. The user has already requested the finished film, so the review does not require another approval question.
5. Run `npm run render`, then `python verify_delivery.py`; review the decoded frames and resolve findings.
6. Update the review/handoff documentation, restage finalized source documents and run `python package_editable.py`.

All browser stages invoke the installed pinned HyperFrames 0.9.19 package directly. They use the shared evaluation mutex, software rendering, one worker, a 2 GiB per-process Job and a 300-second deadline. The render requires current check, snapshot and preview receipts for the same composition/media digest. The bounded preview opens the local editor in an isolated headless Chrome client, records its loaded video and screenshot, then stops the server explicitly. No preview is left running after delivery. Local-server execution required an approved run outside the initial network restriction; the supervisor limits remained active.

You can also keep editing in the [HyperFrames desktop app](https://hyperframes.studio/studio/download?os=windows&src=cli). Nothing was published externally.
