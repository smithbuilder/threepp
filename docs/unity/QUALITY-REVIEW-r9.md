# Independent quality review: Cinder Unity r9

November 9, 2026, Pacific Time. Reviewer: independent quality agent. I did not author the candidate simulation, runtime, importer, art, shaders or motion adapters. I inspected the actual player evidence and reported the defects repaired in preceding revisions.

## Verdict

| Required review aspect | Score | Verdict |
|---|---:|---|
| Whole-candidate presentation | **8.0/10** | Pass for a reviewable lowrider prototype |
| Observable prototype gameplay | **8.2/10** | Pass within the recorded scripted path |

**The independent visual and observable-gameplay review gates pass for this exact candidate.** The weaker score is 8.0; no score was rounded up to meet the threshold. No confirmed P1 remains in the inspected path. This is not paid-release acceptance, target-device performance approval or a human playtest. The original draw-call budget remains unmet and must be disclosed separately.

## Exact bytes and scope

Candidate revision: `cinder-unity-r9`.

Windows player SHA256, independently computed from `builds/cinder-unity-r9/Cinder.exe` and matched to the runtime receipts:

`5CF25D276D9331F1C6AA01994BD641586EDA28EC52EFCEAC31E1D54D3898448E`

I inspected these packets under `evidence/cinder-unity-r9/`:

| Packet | Evidence examined |
|---|---|
| `20261109-013642-689-Probe` | Pure probe summary: 204 checks, Success true. Loaded-rig summary: 495 checks, Success true. These remain technical checks, not a playtest. |
| `20261109-013702-326-Capture` | Actual main-menu frame 0 and exact-build runtime receipt. |
| `20261109-013715-816-Capture` | UI frames 8, 53 and 163; all ten scripted PadState PASS assertions; performance summary. |
| `20261109-014106-738-Capture` | Catrina frames 0, 60, 210, 330, 510, 630 and 779; all 26 saved pose fingerprints/state summaries; completed runtime receipt and performance summary. |
| `20261109-014145-481-Capture` | Luna frames 0, 60, 120 and 210; all eight saved pose fingerprints/state summaries; completed runtime receipt and performance summary. |
| `20261109-014206-100-Capture` | Nocturne frames 0, 150, 330, 420, 630 and 869; all 29 saved pose fingerprints; completed runtime receipt and performance summary. |
| `20261109-014055-963-Benchmark` | Exact r9 performance/control receipt and summary, compared with the immediately preceding r8 control. |

The three uninterrupted motion takes total 63 seconds. The six-second UI flow brings the review source to 69 seconds. I inspected ordered samples and every saved pose fingerprint, not every intervening rendered image. A final encoded reel and delivery manifest require their own hashes and decode verification; those packaging steps are not certified by this source-frame review.

## Before and after the two r8 findings

**Paint/chrome stability:** compared with the same r8 framing, r9's broad Catrina side reads as a more continuous lacquer surface. The grille, fine wheel detail, windshield surround and narrow trim have less harsh single-pixel edge sparkle. The smoothing softens the smallest details somewhat, but keeps the silhouette, stance changes and major material boundaries legible. The UI remains crisp because it is rendered separately. These actual standing and moving views address the previous blocking paint/chrome presentation finding sufficiently for the prototype bar.

**Existing shop glass:** the facade panes now read as darker recessed glazing with a controlled reflection/value response rather than broad flat green cards. The recessed doors/window frames, awnings, outward-facing signs and continuous curb remain intact. This is a restrained material correction on the existing setting, not an increase in scene scope.

Those observed repairs account for the presentation increase from r8's 7.8 to r9's 8.0. The standard was not changed. The title still has simplified upper windows, sparse street dressing, some bright facade-edge breakup and fine chrome/wire aliasing at 960 pixels. These are visible polish limits, but do not prevent the reviewed prototype from clearly presenting its three authored lowriders, their motion and the Mercer setting.

## Presentation and player flow

The garage has a clear lowrider direction: coherent warm orange/cream navigation, three distinct cars, complete vehicle framing and a card below the vehicle. Glazing shows the cabin, tire/contact regions stay visible and no implementation status appears in the player footer. Pause frame 53 displays `KEEP CRUISING`; quit frame 163 displays `STAY HERE`. Frame 8 displays LB/RB/X hints. The ten state assertions agree with the observed car-switch, session, pause/settings/back, garage and quit/cancel path.

The earlier r4 blank-label defect remains valid history and is repaired. An intermediate r6 full-frame impression of missing Settings/Quit was disproved with native crops and pixel checks; it is not counted as a defect here. Review history is preserved in `QUALITY-REVIEW-r1.md` and `QUALITY-REVIEW-r8.md`.

## Observable gameplay

The fresh r9 takes retain the complete r8 review coverage:

- **Catrina:** front hop with both front tires noncontact, recovery, opposite three-wheel stances with the intended front tire unloaded, ordinary forward motion, steering, braking, reverse and a final stop. The body, wheels and exposed hardware visibly agree with the changing stance. Saved poses reach approximately Z 75.60 m after starting near Z 65 m, then reverse to approximately Z 67.98 m and stop.
- **Luna:** neutral, paired front pumping, raised hold and lowering. All eight saved poses have four supporting tires. Body height moves from approximately -0.0112 m at the initial root to approximately +0.1407 m in the raised hold and returns to approximately -0.0108 m. These are model-local root positions, not a claim of measured real-vehicle lift.
- **Nocturne:** mild four-corner air raise/hold/lower, recovery and a left-front-only action, alongside a complete roof deployment/stowing sequence. The deck, roof and supporting members operate as a visible assembly and the final view returns to roof-down with the deck closed. The authored roof remains a schematic game mechanism.

I compared each r9 saved pose fingerprint against the corresponding r8 run: Catrina **26/26**, Luna **8/8** and Nocturne **29/29** match. Final run fingerprints also match: Catrina `9d474af219ecea68`, Luna `0ad7e41cf9f2599b`, Nocturne `1469b7c98bb350d9`. This supports the stated presentation-only revision without assuming unchanged gameplay from source text alone.

The 8.2 gameplay score is for these observable prototype actions, repeatable inputs and menu transitions. Physical controller mapping, tactile response and free-driving enjoyment remain unverified. The loaded rig sweeps add finite attachment/deformation evidence; they do not prove continuous mesh clearance or real mechanical engineering fidelity.

## Measured performance and limits

The back-to-back same-PC hop benchmark retained identical simulated final fingerprint `972aede729b16d4d`:

| Metric | r8 control `20261109-014010-512-Benchmark` | r9 `20261109-014055-963-Benchmark` |
|---|---:|---:|
| Median frame interval | 33.3307 ms | 33.3314 ms |
| p99 frame interval | 33.6110 ms | 33.6336 ms |
| External peak working set | 300,613,632 bytes | 298,438,656 bytes |
| Maximum measured capture draws | 687 | 685 |
| Listed scene triangles | 687,908 | 687,908 |

There is no meaningful speed change in this capped capture workload. The r9 full takes report:

| Take | Median / p99 capture interval | External peak working set |
|---|---:|---:|
| Catrina 26 s | 33.3329 / 33.7784 ms | 302,825,472 bytes |
| Luna 8 s | 33.3388 / 33.7101 ms | 269,344,768 bytes |
| Nocturne 29 s | 33.3309 / 34.1045 ms | 286,748,672 bytes |

All runs are bounded 960x600/30 captures with PNG I/O. The original 300-draw target is **not met**. Renderer counts must not replace the measured draws. The internal performance JSON memory field is zero, so this report uses the external supervisor receipts. The review score does not waive that budget miss or establish 1080p/60, handheld or long-session performance.

**UNVERIFIED:** physical gamepad and keyboard/mouse feel, heard audio, comfort, comprehension, enjoyment, complete focus-loss behavior, settings persistence across restart, sustained play and target-device performance. No old native model score is used as Unity acceptance. Later changes to the renderer, imported assets or player bytes invalidate this exact-candidate verdict until fresh evidence is reviewed.

## Final packaging addendum

Independently rehashed all **32 delivery-manifest package files** and found no mismatches. All **six selected stills** match their original runtime PNGs and the packet hashes byte for byte. The player binding agrees with the exact r9 hash above. This rehash scope is the 32 packaged files and six still origins; I did not independently repeat hashing every one of the manifest's thousands of generated build-source entries.

The proof clip SHA256 is:

`ea6bd9b799ef7ff14f3ca55fe11479ae4c15ec4ad708c0b5ae13e279356868b3`

It matches both `review/packet.json` and `review/delivery-manifest.json`. An independent `ffprobe` frame read counts **2,070 decoded video frames**, **960 x 600**, **30/1 fps**, **69.000 seconds**, and one video stream with **no audio stream**. The packaging packet also records a passing complete decode.

Viewed the extracted encoded frames in `evidence/cinder-unity-r9/decoded-inspection/` at 8, 36 and 54 seconds. They show the correct Catrina hop, Luna raised hold and Nocturne roof state, retaining the source framing, car identity, HUD and contact region. No visible corruption, identity substitution or cropping was found in these samples. This is sampled visual inspection plus a complete mechanical frame read, not a claim that every encoded frame was visually examined.

One P2 packaging naming issue was identified: `04-catrina-hop.png` is actually source frame 360, mode 3, the **right three-wheel stance at highest recorded body-root Y**, not a hop. `docs/DELIVERY.md` now explicitly records that correction, resolving the misleading presentation while retaining the immutable packet filename/hash for history. Use the same accurate label in the art-review index. The encoded clip's 8-second sample shows a genuine front hop. This metadata correction does not change player bytes, evidence pixels or the score.

**Packaging audit passes within this scope; scores remain 8.0 presentation and 8.2 observable gameplay.** No listening review or human playtest is claimed.
