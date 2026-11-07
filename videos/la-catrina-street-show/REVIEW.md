# Film review

The encoded 48-second film passes the producer's visual and technical review. The [independent final review](proof/independent-film-review.md) is **PASS_WITH_LIMITATIONS**, with zero P0 and zero P1 findings. It independently inspected all 28 decoded samples, all three final sheets and 16 native PNGs; a fresh decode matched every sampled PNG pixel. The report binds the final MP4, source, native manifest, delivery receipt and poster. Its JSON SHA256 is `9561bda77ff044283282894178d1d413a5eb12594ad4d3ec2b19bd776cbd7297`.

The producer inspected all 19 individual 960×600 snapshot PNGs at 0.8, 3, 5.8, 6.2, 11, 15.8, 16.2, 18.5, 20.8, 21.2, 25, 28.8, 29.2, 33, 36.8, 37.2, 42.5, 45 and 47.5 seconds. Every scene has its intended source picture, and the short titles clear the car. The 15.8-second full-car snapshot and 18.5-second detail show the front lift; the 21–37-second shots show the intended left and right three-wheel poses.

The bounded editable preview loaded the 48-second composition, six scene blocks and both audio tracks. Its screenshot `proof/preview-editor.png` was inspected. The server returned HTTP 200 and stopped explicitly after review. This was a headless visual/readiness check, not continuous playback or listening acceptance.

After rendering, the producer inspected `proof/La-Catrina-Review.jpg`, `proof/La-Catrina-Seams.jpg` and `proof/La-Catrina-Hop-Motion.jpg`. The cut sheet contains no blank transition. The hop sequence shows compression, front-pair lift and recovery at normal speed. Full-resolution decoded frames 310 and 360 were compared for the poster; frame 310 at 10.333 seconds has the clearest front-pair road separation and preserves the complete body. The poster is an exact copy of that decoded PNG.

Technical checks passed:

- Both independent reference-sheet scores exceeded eight: 8.020 and 8.115, bound to exact model `8444acaabf320f15fc3157342f4d23baa0b03b701d99af365608f48c4c16cb3e`.
- All 1,440 source PNG hashes and six encoded clip hashes match their native receipts. All 240 Hz summaries report zero discarded backlogs; post-warmup motion gates pass.
- Front-pair noncontact with loaded rear support totals 3.467 seconds in the hop shot and 1.867 seconds in the detail, each with later four-contact recovery. Both three-wheel clips sustain the intended missing front contact with the other three tires loaded for eight seconds.
- HyperFrames check reports zero errors or warnings for lint, runtime, layout, contrast and audio. Its optional motion audit was disabled; motion evidence comes from native telemetry and the inspected images.
- Final video is 48.000 seconds, H.264 960×600/30 fps, 1,440 frames. Full decoding has no errors; no 98%-black interval lasts 0.05 seconds; fast-start metadata is present.
- All 28 decoded frame comparisons match the appropriate native source within the declared tolerance. Maximum mean pixel difference is 2.0765/255; only title areas in the two title scenes are masked.
- AAC audio is 48 kHz stereo, −20.1 LUFS integrated and −5.2 dB true peak. It combines the project's original instrumental with credited real engine/hydraulic recordings. Nine pump excerpts align to actual extension changes.

The weakest section is the shaded three-wheel pair at 21–37 seconds. The candy paint is darker and less vivid than in the sunny hop shot, although the body, wheel separation and suspension remain readable. This native lighting is retained without a grade. The close wheel shot intentionally frames the front corner tightly; no post-production crop or enlargement is applied. No P0/P1 defect was observed in the inspected evidence.

Limitations: finite sampled visual checks do not establish every intermediate pose. Tire noncontact is inferred from contact count and loaded supporting tires, not zero load alone. The vehicle uses simplified raycast suspension and visual linkage adapters, not a roadworthiness or manufacturing simulation. Sound was measured but not human listened; the soundtrack is editorial reconstruction, not native simulator audio. No claim of continuous real-time playback review is made.

Evidence: `source-manifest.json`, `source-package-manifest.json`, `proof/check.log`, `proof/check-execution.json`, `proof/snapshot-execution.json`, `proof/preview-session.json`, `proof/preview-execution.json`, `proof/render-execution.json` and `proof/delivery-receipt.json`. Initial cache/localhost failures remain as explicitly failed logs, followed by passing supervised checks.
