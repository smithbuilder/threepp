# Cinder lighting refinement

November 11, 2026, Pacific. Oliver asked to apply useful findings from the supplied November 10 Windowseat lighting assessment. That document is a reference assessment, not a request to turn Cinder into a toon train scene. Published r24 is the preserved control.

## Adaptation

| Assessment finding | Cinder decision |
| --- | --- |
| Inconsistent post chains and clipped source glow | Keep the existing native ACES and display-space FXAA. Experiment with a single restrained HDR bloom before the grade: half/quarter resolution, three extra blits, soft knee, scalar extraction/radiance cap to retain source hue. No exposure or sun retuning. |
| Flat surfaces, missing occlusion/reflections | Native normal/roughness/coat, HDR reflection and baked city vertex shade already exist. Add only four small, support-aware tyre footprints to ground indirect lighting. No extra geometry, light, shadow or draw pass. |
| Gradient quantization | Preserve display-encoded colour in half precision through FXAA, then apply static triangular dither bounded to half one display byte before final output. Do not claim a visible banding improvement without a matched gradient comparison. |
| AA after outlines | Already addressed by display-space FXAA; Cinder has no contour pass. |
| Flat 8-bit sky | Cinder already uses the original HDR sky, native single-sun extraction and calibrated diffuse/reflection units. Preserve them. |
| Cabin coupling, tunnel exposure, toon bands, character rim | Not applicable to this lowrider refinement. |
| Height haze/cloud shadows/water | Deferred. Additional effects must answer an observed Cinder problem and fit the measured budget. |
| No recent target-device baseline | Pair the candidate with unchanged r24 on this PC under existing limits. ROG Ally 1080p/60 remains unverified. |

## Review gates

Preserve Catrina magenta/lace/gold, Luna teal/ivory and Nocturne blue-black/canvas detail. Reject general washout, broad halos, opaque black contact blobs, shading under an airborne tyre or new UI softness. Contact shading affects only Mercer ground indirect light and fades with clearance; the sim, native static shade and direct shadow remain authoritative.

Use identical camera/pose controls with `-LightingControl legacy`, `bloom-off`, `contact-off`, `dither-off`, plus normal captures. Diagnostic controls cannot enter a delivery packet. Store posed footprint/support data with periodic replay receipts. Inspect parked, hopping, three-wheel, raised suspension, roof and moving chrome views, then obtain fresh independent verdicts. Independent reviewers do not implement these surfaces.

Budget stays 960 x 600 / 30 fps, no MSAA, one 512 shadow, 2 GiB process job, 300 draws and 700k active triangles. UI renders separately after the world grade. No simulation files or donor assets change. The attachment is not evidence that this implementation works; exact-player captures and measurements decide retention.
