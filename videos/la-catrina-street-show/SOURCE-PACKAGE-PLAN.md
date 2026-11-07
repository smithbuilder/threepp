# Editable archive contents

The accepted model, native captures and encoded film are verified. Finalized source documentation and evidence have been restaged. The archive is `outputs/La-Catrina-Street-Show-Editable.zip`; its verified size, SHA256 and entry count are stored separately in `proof/editable-archive-receipt.json`. Staging still refuses to proceed unless the exact acceptance and native-source gates pass.

| Group | Contents | State |
| --- | --- | --- |
| Edit | Root HTML, six scene HTML files, edit manifest and build scripts; 48 seconds | Verified |
| Media | Six encoded 960×600/30 fps native clips, full frame at 1× | All 1,440 original PNG hashes and clip hashes verified |
| Sound | Original Sunset Pulse source/edit, credited CC0 engine and lowrider recordings, processed action track and provenance | Complete; nine telemetry-aligned pump excerpts; measured sound, no listening acceptance |
| Fonts/runtime | Barlow font files, OFL license and local GSAP runtime | Included |
| Visual review | Accepted-model receipt, studio receipt and 16 hash-verified images, both independent reviews as JSON and readable Markdown | Included; exact-model scores 8.020 and 8.115 |
| Mechanical review | Verified mechanical JSON/Markdown, unmodified same-prefix check script, model manifest and geometry/source binding | Included; reproducer retains full-checkout dependencies stated in the manifest |
| Reference | Unchanged original `La-Catrina-Master.jpg` under `Source/reference/` | Hash verified |
| Native evidence | Per-shot result receipt, `drive.json`, `drive.json.csv`, stdout/stderr, model/binary identity | Included |
| Source context | Capture/supervisor scripts, vehicle presentation/hydraulic excerpts and material/rig/physics/frame-pocket notes | Final documentation restaged |
| Film checks | Check/snapshot/preview receipts, preview screenshot and clean stop, decoded sheets, full decode/audio/source-correspondence evidence and independent final review | Complete; independent PASS_WITH_LIMITATIONS, no P0/P1 |
| Handoff | README, credits, specification, storyboard, review and handoff | Complete; ZIP integrity is recorded externally to avoid a circular self-hash |

The ZIP excludes installed dependencies, render caches, raw native PNG sequences, rejected generic whoosh, duplicate final MP4 and the separate vehicle GLB package. The encoded clips and audio make the edit self-contained. New driving capture and the unmodified mechanical reproducer require the full engine checkout and vehicle package, including the source/pose dependencies recorded in the mechanical report.

`ARCHIVE-MANIFEST.json` lists every included file, size and SHA256. Packaging checks each stored entry after creation; the external integrity receipt is written only after that check passes.
