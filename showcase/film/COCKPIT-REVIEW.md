# Cockpit and suspension review

22 seconds, 960x600, 30 FPS. Two-second opening, ten seconds cockpit, eight
seconds exterior, two-second intentional hold on a side frame. Actual native
footage with the accepted HUD and recorded-exhaust mix. No upscale, grade,
voice, music, generated gameplay or upload.

The interior was refined after the first capture: cage/roof headroom increased,
dash slimmed, instrument pods raised and their ticks kept in front of housings.
The cockpit stays at the seat with partial roll stabilization, fixed 74-degree
FOV and no artificial shake. V toggles cockpit/last exterior; C cycles four.
Physical wheel and instrument needles follow actual game steering/speed/RPM.

All composition checks passed with zero errors and zero warnings. Beat, phone
and all three cut strips were inspected. Fresh-context review saw no P0/P1:
road/checkpoint clear in sampled cockpit poses, no obvious inside-mesh artifacts
or major intersections, springs/dampers/links distinct, no sampled blank cut.
Weakest proof: small exterior components need real motion/closer inspection to
judge detailed joint behavior. Secondary HUD is small on the phone sheet; no
mobile support claim. The 12-second cut intentionally rewinds simulation 11 to
9 seconds for a camera comparison. Final still is an intentional reading hold.

Six CPU checks passed, including fixed wishbone lengths, constant spring wire
thickness, nonintersecting coil turns, rigid damper barrel, Ackermann steering,
full tyre/body envelopes, seated-eye/body clearance, camera toggling and correct
left/right input relative to the forward-facing cockpit. Full cockpit lap in
20261102-075345-790 passed 900 frames, all gates, zero contacts and normal exit.

These are kinematic suspension visuals driven by arcade ground following.
Stills and geometric/scripted checks cannot accept comfort, physical controls,
full dynamic suspension realism or enjoyment. No reference-game parity claim.

Capture keeps native sound endpoint closed. Same CC0 exhaust bands are rebuilt
from RPM/load/shift telemetry, with the existing capture disclosure. Audio is
measured rather than heard. Native heard sound remains unverified here.

Delivery verified: 22.000 seconds, 960x600 H.264/yuv420p at 30 FPS, stereo
AAC 48k, 19,503,163 bytes. Full decode passed with an empty error log; decoded
contact sheet and final frame were inspected. MP4 moov precedes mdat for fast
start. Audio measures -16.3 LUFS / -5.5 dBTP / zero clipped samples; silence
occurs only in the planned 0-2s title and 20-22s hold. Receipts are local.
