# La Catrina — native street motion review

The accepted round-11 vehicle passes this **sampled native-frame and recorded-contact review**. Six separately supervised city captures supply 48 seconds / 1,440 displayed frames at 960×600 and 30 FPS. The front-hop shots show real front-tyre flight and recovery; the left and right three-wheel shots show the intended front tyre lifted while the car drives on the other three. The automatic tour supplies driving inputs to the shared simulation; hydraulic preload and tyre forces produce the body motion.

## Exact evidence

- Model SHA256: `8444acaabf320f15fc3157342f4d23baa0b03b701d99af365608f48c4c16cb3e`.
- Driving executable SHA256: `dee326b1ba9736e3686660bce1a78b2d6b7e136fe6c78b9cff954f4a592c2203`.
- `videos/la-catrina-street-show/native-captures.json` binds every original PNG and encoded source clip to its native session, model and executable.
- `videos/la-catrina-street-show/source-manifest.json` verifies all 1,440 PNG hashes, six encoded clips, accepted-review hashes and each session's contact telemetry. Every session exited 0 and recorded a 240 Hz simulation with zero discarded backlogs.
- `build/la-catrina/native-review.json` collects the current model, static acceptance, CPU, mechanical and capture evidence. The first-delivery 24-second review is retained in `build/la-catrina/initial-delivery-records/`; it does not describe this artifact.

## Displayed driving and contact states

All measurements below exclude the 60-frame warmups, or 90-frame warmups for the two three-wheel shots. They describe 30 FPS samples of the 240 Hz solver. A missing tyre contact is inferred from the total contact count **and positive support loads at every other tyre**; zero wheel load alone is not treated as flight.

| Shot / native session | Displayed time / frames | Recorded path | Contact evidence |
|---|---:|---:|---|
| Reveal / `20261106-123108-529` | 6 s / 180 | 11.656 m | Four contacts in every displayed sample. |
| Front hop / `20261106-123132-325` | 10 s / 300 | 11.677 m | Both fronts absent with both rears supporting in 104 samples: 3.4667 s cumulative, longest continuous interval 0.6333 s. 185 four-contact samples occur after the first lift. |
| Wheel detail / `20261106-123204-120` | 5 s / 150 | 5.896 m | Both fronts absent with rear support in 56 samples: 1.8667 s cumulative, longest interval 0.6333 s. 83 four-contact samples occur after the first lift. |
| Left three-wheel / `20261106-123222-823` | 8 s / 240 | 7.601 m | Left front absent; right front and both rears positively loaded in all 240 samples. |
| Right three-wheel / `20261106-123248-768` | 8 s / 240 | 7.609 m | Right front absent; left front and both rears positively loaded in all 240 samples. |
| Exit / `20261106-123315-736` | 11 s / 330 | 21.203 m | Four contacts in every displayed sample. |

The full-precision measurements and continuous sample intervals remain in the source manifest. The shots are separate capture runs, so their distances are not one continuous route. Both hop clips end at different points in the repeating cycle; recovery is established by the recorded intervals within each clip, not a claim that every shot ends at rest.

## Opened frame samples

The following original PNGs were opened directly, using zero-based clip frame numbers (warmup already excluded from the stored images):

| Original frame | Visual observation |
|---|---|
| Hop `frame_00008.png` | Pre-flight four-wheel support, with the complete car framed. |
| Hop `frame_00018.png` | Both front tyres visibly clear the street; rear tyres support the pitched body and the front coils/arms remain visible. |
| Hop `frame_00040.png` | Return to a low, supported pose after the first hop. |
| Wheel `frame_00018.png` | Closer view of front tyre flight, wire wheels and the wheel opening. This camera intentionally frames a detail rather than the whole car. |
| Left `frame_00120.png` | Near left-front tyre lifted, opposite tyres supporting; exposed rear axle, coil and links remain connected. |
| Right `frame_00120.png` | Mirrored camera makes the right-front lift visible and exposes the connected rear spring/link assembly. |

The left/right shots pass through building shade and are darker than the hop shot. Their raised tyres and silhouette remain readable in the inspected images; no claim is made that every scene is brightly lit. Fine small joints remain limited by the native capture resolution.

## Mechanical and review limits

The 243-pose loaded rig audit and the independent round-11 source-geometry review are separate evidence for fixed arm lengths, rigid axle span, engaged rods, geometric ram-to-rail load paths and named sampled clearances. See [RIG.md](RIG.md). Three images of a mechanism cannot establish continuous clearance, and the finite automated samples do not certify every possible moving-mesh state.

The 8.020/10 and 8.115/10 independent reference-sheet scores establish static appearance for this exact model, not continuous motion quality. This motion review is frame sampling plus recorded-state analysis; it does not claim human keyboard/controller feel, uninterrupted human playback review, structural safety, real-car performance or long-session stability.

The separate final encoded-film review, `videos/la-catrina-street-show/proof/independent-film-review.json`, reports **PASS_WITH_LIMITATIONS and no P0/P1 blocker**. It inspected 28 decoded samples, three sheets and 16 native PNGs, including all five cut boundaries and a complete sampled hop cycle. It independently reproduced the 28 decoded samples exactly and recomputed the contact metrics from the CSVs. The shaded three-wheel shots remain its non-blocking visibility limitation. This expands the sampled evidence without claiming inspection of every encoded frame or continuous human playback.

The edited movie retains the native frames at normal speed. Its engine and pump sounds are **editorial reconstruction from credited real recordings**, combined with an original instrumental; the simulator capture is silent. Audio measurement does not establish human listening acceptance. Encoded-movie checks and the independent editorial review are recorded separately in `videos/la-catrina-street-show/REVIEW.md` and its `proof/` directory.
