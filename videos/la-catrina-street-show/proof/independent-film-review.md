# Independent final film review

**PASS WITH LIMITATIONS — no P0 or P1 film blocker found.**

Reviewed the delivered 48-second, 960 x 600, 30 fps MP4. This decision covers film framing, trick visibility, sampled visual continuity, cut boundaries, titles, source correspondence and recorded motion. It does not rescore the car model.

Final MP4 SHA-256: `4fa5666edd5ba07006919a328570d16da8246b558aeeec14880ff44a2990b72c`
Source manifest SHA-256: `67e0cbc2c3c7bbdbe41eb1a86bf371d5eb43cc40e24ebfd3be9fae6097c9ee7d`
Native capture manifest SHA-256: `567fadde1a5b474668b4fcc5ef301914f739919c9b24d7dcab98cbca23505c4a`

Viewed all **28 unique decoded sample PNGs individually at native resolution**, all three review sheets, and 16 original native PNGs. The sample count is 28, because frame 330 belongs to both the overview and hop strip. Reviewed both sides of all five cuts; the hop strip covers frames 300–360 every 10 frames. The full evidence paths and hashes are in `independent-film-review.json`.

The title is readable in the opening and closing shots. The front-pair hop clearly lifts, lands and recovers; the close-up keeps its front wheel completely framed. The left and right glides visibly retain their lifted wheel and exposed suspension. No missing, detached or teleporting wheel, gross mesh discontinuity, blank sample or accidental cut error was observed. The wheel-detail camera intentionally excludes part of the rear body; it retains the relevant wheel.

Independent decoding of the exact final MP4 reproduced all 28 saved PNGs pixel-for-pixel. Their mapped native PNG hashes match the capture manifest. Recomputed differences against the encoded clips range from 1.08746 to 2.07651 out of 255; against native PNGs they range from 2.56347 to 3.90795, consistent with encoding loss. Title regions were excluded only from the two title-shot numerical comparisons and were inspected visually.

| Shot | Native travel | Supported lift samples |
|---|---:|---|
| reveal | 11.66 m | Four contacts throughout |
| hop | 11.68 m | 104/300 front pair |
| wheel | 5.90 m | 56/150 front pair |
| left | 7.60 m | 240/240 left front |
| right | 7.61 m | 240/240 right front |
| exit | 21.20 m | Four contacts throughout |

These values were recomputed independently from post-warmup CSV rows. A supported lift requires the stated contact count and positive loads on every support tire; zero load by itself was not accepted as flight. No sampled frame has zero contacts. Maximum within-shot chassis movement is 0.06810 m per frame and maximum orientation change is 2.12651 degrees per frame.

The three-wheel shots are noticeably darker than the reveal/hop; their silhouette and lifted wheels remain readable, while fine undercarriage detail is weaker. This is a non-blocking film limitation.

The poster is the inspected airborne frame 310 and is pixel-identical to sample-008.png (SHA-256 `db0749f72c335d7fcfce742cb17ca7507dcb27b3e33acc251473138a935ece25`).

Limits:

- This is independent sampled-frame film QA, with a complete sampled hop cycle and all five cut boundaries; it is not continuous human playback or a visual inspection of every encoded frame.
- Sound was not listened to. Loudness, peak and decode measurements do not establish listening quality, timing feel or subjective audio acceptance.
- Contact/load data are 30 fps samples from the native 240 Hz raycast solver. Visual wheel clearance is additionally evidenced by inspected images; the telemetry is not a real-world mechanical validation.
- The film contains six separately captured shots with deliberate camera/location resets at cuts. It does not claim an uninterrupted single drive.
- The model and research are not rescored by this review. This pass does not independently validate reference fidelity, real component specifications, attribution or media licensing.
- Native delivery is 960 x 600 at 30 fps; fine chrome and undercarriage detail remain limited by that resolution and the scene lighting.

The delivery receipt reports a clean full decode, no nearly-black interval at least 0.05 seconds, and measured audio of -20.1 LUFS / -5.2 dBTP. **Audio was not listened to, and continuous human playback was not established.**
