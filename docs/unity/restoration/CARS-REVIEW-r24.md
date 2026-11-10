# Independent car review  -  r24

November 9, 2026, Pacific Time. Independent automotive visual evaluator. No implementation, asset edits or editor/player launch. This review opened the actual r24 PNGs, matched roof controls and native reference, and inspected relevant native runtime overrides. The earlier failed review packets remain preserved.

## Verdict

**The Nocturne canvas preservation defect is corrected in the inspected r24 evidence.** The raised normal roof differs visibly from the same-state hidden-cloth control, has opaque dark canvas over the cabin, and is supported by actual D3D11 renderer receipts and a bounded pixel-coverage comparison. The roof should not be judged from the low front frame alone: that projection makes the dark canopy unusually thin and easy to misread.

Luna's rear palette, Catrina's complete right-three-wheel framing and Nocturne's broad blue-gray flank gradient remain restored on the new bytes. **No remaining car-presentation P1 is observed in this finite r24 review scope.** That is a scoped finding, not a declaration of complete native runtime feature parity or overall project quality approval.

### Correction to the earlier review

This evaluator missed partial canvas culling in r20 despite opening roof-cycle frame 0420 and native `roof-up.png`. Treating `roofPhase == 1` as if it validated the drawn roof was an error. The r20 report now starts with an explicit rejection/correction, withdrawing its no-P1 and Nocturne complete-presentation judgment. Its successful body-reflection, Catrina and Luna observations remain valid within their scopes. R24 is judged from new evidence and does not rehabilitate the rejected r20 player.

## Absolute quality and native-relative restoration

| Car | Absolute visible presentation / 10 | Native-relative preservation |
| --- | --- | --- |
| La Catrina | **7.0** | Rose/pink separation, lace, gold ornament, wire detail, burgundy seating and signature stances remain recognizable. The camera and palette repairs persist. Finish and very fine brightwork retain prototype roughness. |
| Media Luna | **7.0** | Sage roof/trunk, green curved shell, ivory whitewall and warm cabin survive rear chase and front lift/lower views. Native identity is substantially preserved. Exact same-asset parity remains confounded by differing source identities. |
| Nocturne | **7.0** | Broad dark coachwork form, grille/wheels/glazing and visible interior survive. The omitted native two-sided canvas rule is now represented, and the controlled raised-roof images establish cloth contribution. Exact reflection and interior-showcase parity remain incomplete. |

These numerical ratings are absolute presentation judgments. The preservation column addresses a separate question: whether the native cars' character and visible features survive. Native itself is stylized prototype work. Restoring it does not confer an 8/10 score, a gauntlet-level pass, paid-release approval, physical handling acceptance or a judgment of city quality.

## Exact identity and inspected images

Player SHA256: `7D78C95234B8C21A2F2A48E544EB888F43D52612D0C8680C7D6319128CAA256A`.

Supplied source fingerprint: `0e57c2129876c7765692f3fd50d0cfe0cd3a02d73c826f93c48c89c2c1c86d97`. Coordinator reports 204 + 495 + 154 probe checks PASS; I did not rerun them. Every listed r24 session's runtime receipt was read: all match the player SHA and report normal completion. All are normal `control: none` except the deliberately hidden-cloth diagnostic.

Paths below are under `evidence/cinder-unity-r24/`. Listed original frames were opened individually:

| Session | Original frames inspected | Scope |
| --- | --- | --- |
| `20261109-232351-864-Capture` | 0000 | Normal fully raised side roof, phase 1 |
| `20261109-232418-478-Capture` | 0000 | Same-state hidden-cloth diagnostic, `roof-hidden` |
| `20261109-232445-070-Capture` | 0000, 0150, 0300, 0420, 0450, 0600, 0750, 0869 | Complete 870-frame Nocturne take, sampled through roof cycle |
| `20261109-232942-508-Capture` | 0000 | Catrina menu |
| `20261109-232945-387-Capture` | 0030, 0120 | Complete 180-frame input flow, sampled at Luna rear chase/menu |
| `20261109-233004-812-Capture` | 0000, 0060, 0240, 0360, 0540, 0779 | Complete 780-frame Catrina take, sampled at low/hop/both three-wheel/drive/end |
| `20261109-233043-279-Capture` | 0000, 0120, 0239 | Complete 240-frame Luna take, sampled at low/lift/lowered end |
| `20261109-233103-714-Capture` | 0000 | Overview, context only |
| `20261109-233116-424-Capture` | 0000 | Nocturne open-top street |

Also reopened: matched old-player `evidence/cinder-unity-r20/20261109-232527-188-Capture/frame-0000.png`, original r20 roof-cycle `223759-931-Capture/frame-0420.png`, and `docs/nocturne/review/native/roof-up.png`. Native front/side/wheel/cabin references were opened during the earlier independent reviews in this lane; their paths are preserved in those reports. This current matched roof judgment uses the reopened native roof image directly.

The review is at the existing 960 x 600 profile. Different native cameras/light directions and detail coverage remain confounds. Catrina/Nocturne frozen sources previously matched native receipts; Luna frozen `8aa58c...` differs from native receipt `66e3ef50...`. Sampled sequences are not a claim to have watched every frame in real time.

## Roof diagnosis and fix evidence

`showcase/NocturneRig.hpp:59` explicitly sets every canvas material to `Side::Double` after loading the GLB. The GLB alone does not encode that native application override. R20's single-sided material therefore failed to preserve the complete canopy appearance even while its pose/mesh checks passed.

The matched side view is more informative than the low frontal take. In r24 normal side `232351-864/frame-0000.png`, the dark canopy covers the cabin; in `232418-478/frame-0000.png`, removing cloth exposes the frame/open sky where that cover was. The matched old r20 side retains only part of the intended coverage. This supports **partial culling**, not the inaccurate statement that every canvas triangle or all roof geometry was absent.

`roof-coverage-comparison.json` records a mask of 4,267 canopy/glazing ROI pixels derived from an unchanged-geometry magenta control. Against hidden cloth, r24 differs over three bytes in 99.67% of the mask, median maximum-channel difference 60 bytes; old r20 differs in 40.47%, median 0. The diagnostic explicitly includes glazing/lighting effects and is **not triangle-level opacity proof**. It supports the visual normal/hidden comparison rather than replacing it.

I read the normal raised-state `roof-render-0000.json`: three canvas renderers, three frustum parts, phase 1.0, D3D11, shader `Cinder/Canvas` supported, cull 0, active/enabled and not forced off. Analysis of the completed cycle's 29 `roof-render-*.json` receipts found success, three canvas renderers and D3D11 in all 29; each includes supported `Cinder/Canvas`/cull-0 details, and the phase-1 sample reports three frustum parts. This proves substantially more about the actual rendering path than the original vertex-only gate, without certifying every pixel/angle.

Current `CinderCanvas.shader` uses explicit `Cull Off`, Standard PBS and face-dependent normal direction. The importer refresh selects it for the Nocturne canvas family. The observations establish r24's result; they do not establish which earlier intermediate revision first fixed it, nor do they require r24 to look different from an already-correct r23 control.

## Native runtime override audit

A bounded read of `NocturneRig.hpp`, `LunaRig.hpp`, `CatrinaRig.hpp` and the Unity importer/view adapters found:

| Native application behavior | Current Unity counterpart / limit |
| --- | --- |
| Nocturne canvas made double sided after load | Explicit canvas adapter, cull off and backface normal handling; new actual-render controls above. |
| Transparent materials disable depth writes and shadow casting | Glass shader/import path disables depth writing; transparent renderers disable shadow casting. |
| Deforming bags/cloth/leaves avoid stale native frustum bounds | Unity deform application recalculates mesh bounds; rigid batches use explicit enlarged bounds/update behavior. Actual roof receipts cover the tested roof states. This is not exhaustive arbitrary-view culling proof. |
| Roof slot-cover visibility, finish-panel rotation, window drop/door staging | Corresponding `PoseRoof`/`PosePanels` branches exist. The tested cycle is a finite visual check, not all service combinations. |
| Native Luna/Nocturne lamp-off state and toggles | **Additional bounded gap:** native helper functions override emission intensity and supply lamp toggles. Unity imports GLB emissive factors, but this code search found no equivalent per-car off/toggle adapter. Nocturne's native studio explicitly calls lamps off; frozen GLB lens emission factors are nonzero. Current daylight captures do not isolate how much this changes appearance. Record as P2/default-state or capability fidelity, not a newly proved P1 from these images. |
| Native wheel/skirt removal and service controls | Complete native service UI parity is not established by the current Unity menu/roof/panel evidence. Do not claim every native inspection feature has migrated. |

This audit identified no further canvas-like missing material-side override in the other two rig constructors. It is a bounded source review, not proof that no runtime difference exists anywhere in the native application.

## Remaining P2 and acceptance boundary

- Fine chrome/spoke highlights are busy at this resolution; candy highlight texture and environment reflections remain somewhat coarse. The earlier severe material collapse is repaired, but real-time shimmer has not been independently cleared.
- The low frontal roof witness is poor by itself. Keep the matched side normal/hidden proof in the final packet and a clearly legible roof-up still. The canopy can be present while a low view remains hard for a viewer to interpret.
- Forward cockpit and external burgundy seating were inspected in the previous packet; there is no new r24 elevated bench/belt/door-detail comparison here. Complete interior fidelity remains unverified rather than assumed from unchanged assets.
- Lamp/default-state and native service capabilities are explicit limits of runtime parity, as above. No new implementation was performed by this reviewer.
- Finite samples cannot certify continuous clearance, every intermediate roof overlap, all camera/terrain combinations or subjective handling. Human input, audio, enjoyment and target-device 1080p/60 remain separate.

**R24 supports a candid prototype restoration checkpoint for the inspected car presentation, with no observed car P1 in this scope and absolute quality around 7/10.** It does not restore the validity of r20's failed review or confer an overall project level/paid-release approval. Any later player bytes require their own evidence.
