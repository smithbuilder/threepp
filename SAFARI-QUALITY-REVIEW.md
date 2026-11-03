# Safari visual acceptance gate

User reference: local safari.jpg. The user explicitly requested an independent
scored reviewer and enough iteration to pass. Target fixed before review:
weighted overall >=8.0/10, every category >=7.0, no major missing feature.
Scores are independent visual judgements, not CPU tests. Each revision below
records its reviewer evidence separately.

| Category | Weight |
| --- | --- |
| Silhouette/proportions |25%|
| Body/arches/glazing |20%|
| Materials/texture |20%|
| Accessories/mechanical detail |20%|
| In-engine fit/lighting |15%|

## Current accepted candidate

The final model `82795FE6...71E93BE` and signed renderer
`78516EFC...3865424` pass the unchanged independent whole-vehicle static
gate at **exactly8.000/10**, categories **8.1/8.0/7.9/7.9/8.1**. All eleven
court views and three normal gameplay views were independently inspected.
No major or moderate visible defect was found; fine wear, seams and small
gauge lettering remain minor limitations. The exact-artifact report is
`build/safari-model/realism-review-final-7851.{json,md}`, with its hash bound
in `build/safari-model/whole-vehicle-acceptance.json`.

Replacement film sources independently pass bounded sampled motion/source
review, **7.7/10**, with no observed major or moderate defect. Sixty-one
native PNGs were viewed, including adjacent frames through the repaired
checkpoint-camera transition, changing dust and landing poses. This motion
score is separate from the static8.000 score; neither is a full physical
simulation or human handling acceptance claim. Reports:
`build/safari-film/MOTION-REVIEW-final-7851.md` and
`build/safari-film/motion-review-final-7851.json`.

The native22-second review film is encoded at960x600/30FPS as
`build/safari-film/Cinder-Safari-Realism.mp4`. Its five shots use660 original
threepp framebuffer images, without upscaling or interpolation. Exhaust
audio is reconstructed from the recorded RPM/load telemetry and the same
CC0 recorded loops used by the game; it is not an endpoint recording.
`build/safari-film/provenance.json` binds every source and the output hash.
Separate final-film review covers the actual encoded artifact. Independent
checks pass for the complete660-frame decode/order, native dimensions and
timing, fast-start MP4 layout and unclipped audio. Audio measures-18LUFS and
-6.3dBTP; these measurements do not establish subjective sound quality.
Final report: `build/safari-film/FINAL-FILM-REVIEW.md` and
`build/safari-film/final-film-review.json`. Continuous playback, human controls
and physical audio output were not evaluated by that CPU/sample review.

## Review history

- Primitive wide-chassis prototype:3.0/10 FAIL. Disconnected fender fins,
incorrect body/cabin proportions, empty rack, flat materials.
- Dense narrower mesh, forest views:provisional4.3/10 FAIL. No clear side view;
white nose slab, tent-like cabin, lamp caps, distorted911label, floating rack.
- Dense revision2, clear native court front114410-581/side114412-446/
rear114413-261:4.9/10 FAIL. Category scores4.5/5.0/3.5/6.0/6.0 respectively.
Readable decals, exposed skid and stronger grounding improved. Body silhouette,
flat materials/dark optics, high rack and spare still fail reference fidelity.
- Revised cabin/nose and localized material maps, native front221426-178/
side221458-476/rear221459-348:5.3/10 FAIL. Categories5.5/5.0/3.5/6.5/6.0.
Better coupe profile and equipment coverage; inflated front surfaces, segmented
window framing, plastic paint, flat lamp discs and unfinished rear fascia remain.
- Explicit front loft, welded trim, open cabin and neutral lenses, native
front222449-424/side222450-293/rear222451-126 plus front-lit222451-948:
5.2/10 FAIL. Categories5.0/4.5/4.0/6.5/6.0. The front became a wedge, glazing
lost optical presence, and a triangle-centroid rear cutout caused sawtooth edges.
An opaque lamp-bucket front cap was also found covering the chrome reflector.
- Shared primary shell with real apertures, hollow lamp buckets and recessed
rear band, native front223911-886/side223912-772/rear223913-592/front-lit223914-414:
5.7/10 FAIL. Categories5.5/6.0/4.5/6.5/6.0. Construction defects improve, but
long flat shoulders/squared ends, sparse surface detail and simplified trim remain.
- Measured shorter nose/tapered rear, image-authored enamel detail and bucket
seats, native front225929-694/side225930-658/rear225931-501/front-lit225932-329:
6.2/10 FAIL. Categories6.0/6.5/5.0/7.0/6.5. Proportions and detail improve;
front wing curvature, separate-blade ducktail, sparse finish and optics still fail.
- Integrated ducktail, revised rear packaging and layered surface finish,
native front232212-413/side232213-288/rear232214-108/front-lit232214-937:
6.4/10 FAIL. Categories6.5/6.5/5.5/7.0/6.5. Shoulder transitions, window joins,
visible hardware interference and synthetic-looking finish remain below the
fixed whole-vehicle threshold.
- Joined greenhouse, packaged coilovers/towers, corrected clear-lens shading
and ambient-only AO, native005949-526/010015-735/010016-651/010017-509/
010018-371: fresh independent6.775/10 FAIL. Categories7.0/6.3/6.2/7.3/7.1.
The scorer independently viewed all five native images and the reference.
Cabin panes still read as wedges; structural stamping, panel channels, paint
mapping and lamp optical construction remain below the target. The fixed
gate remains8.0 overall/all categories7.0.
- Structural window apertures, corrected fascia UVs and rebuilt optics,
native013701-741/013753-050/013754-232/013755-361/013756-486:
7.075/10 FAIL. Categories7.1/7.0/6.8/7.3/7.2. The window construction and
body continuity improve, but exposed interior paint, surface finish and
lamp-cover construction still miss the fixed threshold.
- Dark cabin linings, localized material wear, thin-glass compositing and
smooth optical covers, native021702-086/021703-296/021704-420/
021705-561/021706-685/021707-814/021708-946 plus021337-783:
7.320/10 FAIL. Categories7.1/7.3/7.4/7.4/7.5. All category minima now pass;
the weighted whole-car threshold does not. Broad simplified body shapes,
bare-bowl optics and schematic front recovery hardware remain. Model
SHA256 `908eb44ead77a1110054ef651a7f56d170eb34a711c782dd899666a63938c218`,
renderer SHA256 `afaad946017b080adea9a4f812eae2346b3489e56427167ccfaa967f509c2326`.
These scores are independent visual judgements, not engineering validation.

- Compound fenders/bonnet and rear hips, rebuilt front recovery equipment,
  repaired rear package and a road-matched open spare wheel, model
  `33D15E3D...63B8807`, renderer `AFAAD946...FC2326`:
  a new reviewer with no score history gives **6.97/10 FAIL**. Categories
  **7.6/6.5/6.2/7.4/7.0**. Native sessions032257-429,032329-994,
  032331-246,032332-380,032333-598,032334-745,032335-890,032346-458
  and032437-262 were inspected against the reference. Stance/identity improve,
  but banded/pinched panels, patchy glazing reflections, chrome-bowl lamp
  appearance and uniform finish remain below the fixed bar. The independent
  score is retained as given; it is not rounded or reconciled upward with the
  prior reviewer. Final video remains deferred.

- Continuous body/glass normals, fairer rear-quarter glazing, corrected
  cargo normals, rack feet, darker tyre dust and revised pressed-glass optics,
  model `0A3DC2B2...78F0054`, renderer `D21165C7...FC0F703`:
  independent review **7.495/10 FAIL**, categories
  **8.1/7.3/6.6/7.9/7.4**. All ten forest/daylight inspection views and three
  normal scripted chase/cockpit views were inspected against the reference.
  Repeated paint shading bands remain a major defect; stepped glazing edges
  and the unfinished mirror face also need repair. Reports are in
  `build/safari-model/realism-review-0a3d.{json,md}`. Both runtime/canonical
  model and executable hashes were independently verified. Matched native
  material-side controls subsequently identify the broad stripes as shadow
  self-comparison artifacts, rather than justification for further body
  deformation. Those diagnostic assets are not accepted or promoted.

- Receiver-plane shadow comparison, conforming window boundaries and seated
  reflective mirror inserts, model `40BFC407...2B6F6DE`, renderer
  `68AC2448...F0CADE`: **7.915/10 FAIL**, categories
  **8.1/7.8/7.9/7.9/7.8**. All eleven court views and three normal scripted
  chase/cockpit views were independently inspected. No major visible defect
  remains, but the weighted threshold is still unmet. The cockpit finish and
  glazing seal edges remain the clearest work. Reports:
  `build/safari-model/realism-review-40bf.{json,md}`. An independent matched
  shadow review separately confirms stripe removal and retained ground cast
  shadows; that bounded result does not add visual points or pass the car.

- Measured closed EPDM window seals and detailed animated cockpit, model
  `82795FE6...71E93BE`, renderer `723F7094...50FF9B9`: **8.000/10 PASS**,
  exactly, without rounding. Categories **8.1/8.0/7.9/7.9/8.1**. All fourteen
  native court/gameplay stills and exact identities were independently checked;
  no major or moderate visible issue remains in that gallery. Minor limits
  include small dial numerals, sparse seams and simplified fine wear. Reports:
  `build/safari-model/realism-review-8279.{json,md}`. This is a static visual
  pass. Initial film-source review separately rejected an inspection-menu pop
  and a chase-camera/banner intersection; replacement footage and motion
  acceptance are required before video delivery. Later renderer builds must
  rebind this acceptance to their exact artifact rather than inherit its hash.

Inspection court is capture-only. It uses the actual mesh/materials/engine and
same daylight system on a flat floor, with a visible native-inspection label.
It makes profile assessment possible without roadside obstructions; it does not
establish driving feel or normal-scene acceptance.

## Rear mechanical review

User clarification: mechanical realism takes priority over copying reference
specifications. The exhaust, protective frame/bumper and serviceable engine
bash plate are distinct connected components, without a combined diffuser.

A prior independent visual reviewer gave the rear only a narrow 8.0/10 PASS:
mechanical plausibility8.2, craft8.0. Native tail232215-763 and close rear
232216-607 show separate cradle, engine, headers, silencer, open outlets,
rubber-isolated hangers, shield stand-offs and bumper struts. Tips sit about
66mm inside the bumper rear face. The forward-ending bash plate clears the
outlets; the shield clears the silencer by53mm. Nonblocking tube-junction and
localized weld/wear refinement remains. This score does not pass the car.

That rear fit conclusion is superseded by the later independent dimensional
audit. It found an exhaust bend intersecting the right lower bumper strut
by about72mm, with additional header, collector, crossover and cradle-brace
interference. Those faults were missed in the images. The rear is not
accepted while these intersections remain. A separate author is repackaging
the headers/mergers and cradle around a protected exhaust corridor; the
independent reviewer will check the actual construction paths again before
export. New native images and a fresh visual review remain necessary.

The replacement rear source has now passed the independent static gate:
1,288 checks, zero failures and20 clear bore rays. It has true three-entry
collectors, a two-in/two-out case, corrected engine/mount clearances and an
upper cradle entirely behind the cabin bulkhead. This source result replaces
the earlier rear fit conclusion; it does not pass the current runtime asset
or the whole car. See `showcase/SAFARI-REAR-PACKAGING.md` for scope and measured
clearances. That source is now prepared and native-rendered as33D15E3D...63B8807;
raw and AO full-vehicle tyre/suspension/cockpit checks pass. Its contemporary
visual review still failed. Later8279 preparation repeats those construction
checks and now has the separate current visual pass recorded above.

The checkpoint asset SHA256 is
`51218c6700105876a909a9347e23ec0d70fea6c9ceaa7a0c7f77b6032d17dc14`:
110draw meshes,187902triangles,13embedded maps. It passes6468 padded tyre/body
poses and0.310311m actual eye clearance. The full native repaired-contact run
001725-073 completed the same original-speed lap with0contacts; see
`showcase/SAFARI-DYNAMICS-DIAGNOSIS.md` for measured motion and limitations.

## Material comparison and repair history

An independent matched native A/B review recommends the modest ambient-only AO
candidate at strength0.5. Front234631-009, rear001855-365 and detail001913-234
improve rack and mechanical overlap separation without visible broad stains,
halos or triangle artifacts at960x600. Fine artifacts remain resolution-limited.
This is an AO decision on the matched checkpoint, not whole-car acceptance.

The cowl/bonnet overlap, glass/seal boundaries, pole normals and cargo straps
have been repaired. Safari-specific supported pickups and usable damper
stroke resolve front coilover tops protruding through the bonnet. These
repairs pass all six CPU checks, including
6468 original padded tyre poses,20.3815mm moving hardware/body room,46.22mm
rubber room, usable damper stroke and preserved Legacy geometry. The native
model33D15E3D...63B8807 scored6.97FAIL at that review; CPU fit is not visual acceptance.

Matched flat-paint diagnostic010659-132 keeps geometry/normals/AO/lighting
but removes paint texture-response maps. Broad vertical streaks disappear.
Source inspection confirms rear fascia UV V collapses to one texture row,
with the same defect on the front vertical valance. Dedicated XY fascia
mapping fixed those texture streaks. Compound front wings/bonnet and rear
hips/deck were the next body pass. Separate CPU-only lanes replaced
simple recovery rings/plate with pinned shackles and a folded mounted pan,
and added restrained internal optical texture and physical lens edging.
The exhaust, bumper and separate serviceable protection plate retain their
reviewed distinct load paths and air gaps. Later repairs and acceptance are
recorded above; the rejected candidates and their evidence remain preserved.

## Execution state

The earlier unsigned-startup CodeIntegrity3033/3077 incident is resolved.
The user explicitly approved existing Azure signing for subsequent local
`timber_rally.exe` reviews and resuming guarded native trials. Valid publisher
signature, watchdog, deadline,30FPS,2GiB job and single-process guard remain.
No Windows security setting changed. The archived diagnosis is under
`build/incidents/application-control-20261102`.

All current evidence uses960x600. The separately proposed1920x1200 profile is
pending explicit approval after automatic review rejected raising the approved
resolution cap. No high-resolution frame has run. The native960x600 film
follows the passed static and sampled motion gates; final encoded-file QA
remains a separate report. No capture guard was relaxed for the film.
