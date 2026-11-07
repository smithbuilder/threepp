# La Catrina film handoff

The encoded film and airborne poster are verified. Final source documentation has been restaged for `outputs/La-Catrina-Street-Show-Editable.zip`; its size, SHA256 and entry-verification result are recorded in the separate `proof/editable-archive-receipt.json` to avoid a circular self-hash. No vehicle model, native footage or simulation profile was changed during editing.

| Evidence | Verified result |
| --- | --- |
| Accepted model SHA256 | `8444acaabf320f15fc3157342f4d23baa0b03b701d99af365608f48c4c16cb3e` |
| Reviewer A | 8.020/10; report SHA256 `dc0724735ba1a1a9393d3a8204fb4eab25266588615a5d8ed3bf2d33fdd2a9be` |
| Reviewer B | 8.115/10; report SHA256 `2ad1a170211afac0143b3dca154e54ff5294bb3ecf98395153f58083669d77b5` |
| Native capture | Six sessions / 1,440 verified PNGs / 48 seconds; `native-captures.json` and `source-manifest.json` |
| Final MP4 | `outputs/La-Catrina-Street-Show.mp4`; 32,505,707 bytes |
| MP4 SHA256 | `4fa5666edd5ba07006919a328570d16da8246b558aeeec14880ff44a2990b72c` |
| Video | H.264, 960×600, 30 fps, 1,440 frames, 48.000 seconds |
| Audio | AAC, 48 kHz stereo; −20.1 LUFS integrated / −5.2 dB true peak |
| Poster | `outputs/La-Catrina-Street-Show.png`; 585,565 bytes; frame 310 / 10.333 seconds / hop clip frame 130 |
| Poster SHA256 | `db0749f72c335d7fcfce742cb17ca7507dcb27b3e33acc251473138a935ece25` |
| Delivery receipt SHA256 | `ae69a4fd5d52fc9c228b90fca7122aa34aa3cef73cdd0132a37e2a058a5f54c8` |
| Editable preview | Loaded native video and all six scene blocks; screenshot inspected; server stopped cleanly |
| Delivery verification | Full decode, black scan, fast-start and 28 source comparisons passed; maximum MAE 2.0765/255 |
| Independent final editorial review | PASS_WITH_LIMITATIONS; zero P0 / zero P1; `proof/independent-film-review.md` and `.json` |
| Editable ZIP | `outputs/La-Catrina-Street-Show-Editable.zip`; external integrity receipt: `proof/editable-archive-receipt.json` |

Timing is reveal 0–6 s, front hops 6–16 s, wheel detail 16–21 s, left three-wheel 21–29 s, right three-wheel 29–37 s, exit 37–48 s. The clips play at 1× with their native framing. The poster is an unchanged decoded frame selected after comparing the hop sequence.

The producer inspected all 19 individual pre-render snapshots, the editable preview screenshot, the three final contact sheets and the full-resolution poster candidates. The three-wheel section is the weakest lighting, with shaded body panels; lifted tires and the car remain visible. The original material response was preserved.

Sound uses the original project instrumental plus credited real CC0 engine and hydraulic recordings. Nine pump excerpts follow actual hydraulic-extension events. Native capture was silent; this is not a recording of the fictional car or a measured RPM model. Human listening, continuous real-time playback and physical vehicle validation are not claimed.

Browser work remained sequential under the shared mutex, software mode, one worker, 2 GiB per-process limit and 300-second deadline. The final render completed in 102.9 seconds (105.8 seconds for the supervised stage). Initial tool-cache and localhost access failures are retained in `proof/`; neither was treated as a passing check. No graphics failure or altered footage was used to obtain a pass.

Keep the full engine checkout and separate vehicle package for new native capture or the unmodified mechanical reproducer. The editable film archive contains the encoded media and provenance, not a complete engine build. Nothing was uploaded or published.
