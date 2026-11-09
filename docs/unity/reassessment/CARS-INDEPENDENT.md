# Independent car presentation reassessment

Reviewer: fresh automotive visual evaluation lane; November 9, 2026. Reviewed existing original-resolution PNGs and source only. No player/editor launch, implementation, asset modification, or gameplay judgment. The requested file is this lane's only change.

## Verdict

**The Unity r9 cars are a visible presentation step backward.** The recognizable silhouettes, moving-part concept, trim layout and much of the authored detail survive. The material hierarchy and presentation that made the native cars attractive do not survive as well. These images look like a technically functioning asset port still awaiting its automotive lighting/material pass.

My absolute rating for **the cars as presented in the inspected Unity images is 5/10**: recognizable and individually authored, with some good body reflections, but visibly noisy trim, weak ground contact, dark cabins, and inconsistent finish. This is an aesthetic judgment from stills, not a measured score or a release gate. The native work is also a stylized prototype rather than a photoreal benchmark; its advantage is clearer color/material separation and stronger visual grounding, not photographic fidelity.

Native-relative preservation: **shape/identity mostly retained; finish and showroom appeal materially regressed**. I would not report that the vehicle art has been preserved at equivalent visual quality. I also would not infer that the detailed donor meshes were deleted: distant/shadowed player views cannot establish that.

The handoff's earlier scores were not used as targets. Reading the handoff was required for scope/safety; its verdict does not substitute for this comparison.

## Evidence inspected

All paths below are repository-relative. Images were opened individually with the image-viewing tool, rather than judged from thumbnails or filenames.

| Vehicle | Unity r9 images | Native comparison images |
| --- | --- | --- |
| La Catrina | `art-review/unity-r9/01-garage.png`, `04-catrina-hop.png`; `evidence/cinder-unity-r9/20261109-014106-738-Capture/frame-0000.png`, `frame-0240.png` | `docs/la-catrina/review/studio/front.png`, `side.png`, `front-detail.png`, `wheel-detail.png`, `cabin.png` |
| Media Luna | `art-review/unity-r9/05-media-luna-lift.png`; `evidence/cinder-unity-r9/20261109-014145-481-Capture/frame-0000.png` | `docs/media-luna/review/native/hero.png`, `street-cruise.png`, `street-raised.png`, `wheel-and-grille.png`, `cabin-detail.png` |
| Nocturne | `art-review/unity-r9/06-nocturne-roof.png`; `evidence/cinder-unity-r9/20261109-014206-100-Capture/frame-0000.png`, `frame-0400.png` | `docs/nocturne/review/native/hero.png`, `street-cruise.png`, `roof-midcycle.png`, `cabin.png` |

`04-catrina-hop.png` is a right three-wheel pose, not the hop named by its filename. Its pose is not assessed as an error. Nocturne frame 400 shows a partially moving roof; it does not establish the whole roof motion's quality.

The opened native and Unity PNGs are 960 x 600. Native detail views still allocate much more of the image to the relevant part. Native studio lighting/cameras differ from Unity street lighting/cameras. Native Luna/Nocturne street images reduce the studio comparison bias, but are not matched-exposure or matched-pose controls. The strong conclusions below concern the visible result; exact causal attribution needs controlled shots.

The coordinating audit independently checked frozen-source identities: Catrina `8444aca...` and Nocturne `130a882...` match their native review receipts. Media Luna's frozen source `8aa58c...` differs from the native receipt's `66e3ef50...`; the Luna pair therefore also has a source-version confound. Its visible color/finish comparison remains useful, but it cannot prove identical geometry or assign every difference to the renderer.

## What changed visually

### La Catrina

The long coupe proportions, two-tone panel structure, wire wheels, low stance, door medallion, lace on the upper surfaces and side ornament are recognizable. The raw Unity side frame proves the principal shell and trim layout have not disappeared. Frame 240 also shows ribbed seats: a claim that the interior geometry is missing would be false.

The native `front.png` and `side.png` separate vivid rose upper paint, pale rose lower panels, gold/brown ornament, silver trim and rubber. Unity's shaded side becomes a dark plum stripe over a muted pink slab. The upper finish has some sheen, but the deliberate candy-paint richness is weaker. The lace is much less legible on the menu car. Different light explains part of this, but the equally large Unity side view still has visibly harsher, speckled brightwork than the native side view.

The native `wheel-detail.png` resolves individual spokes, a restrained metal rim and whitewall. Unity's wheel and beltline highlights break into blue-white flecks. The bumper has a broad pale patch that reads more like bright coated material than the native metal's dark/light structure. Native is not immaculate: its chrome also has aliasing and its surface texture is somewhat coarse. Unity amplifies those weaknesses.

### Media Luna

The distinctive fenders, rear skirt, split glazing, visor, long hood and front-lift identity survive. Unity's front-lift silhouette is convincing enough to identify the car. I see no evidence here of a changed overall wheelbase or shell scale.

The most useful comparison is native `street-raised.png` against Unity `05-media-luna-lift.png`. Native has readable teal paint, a lighter sage roof/frame, warm upholstery, an ivory whitewall and a darker tire. Unity's paint is nearly black petrol blue; the roof/frame is weakly separated; seats become grayish shapes behind gray glazing; the whitewall looks muddy beige. Both are street shots with similar vehicle image width, so this cannot be dismissed solely as a native close-up advantage. The fender contours still catch broad highlights, but the body/cabin/roof palette is compressed and less inviting.

The native hubcap is also sky-blue in the street shot, so a blue hubcap alone is not a port defect. The Unity hubcap's environment reflection does not compensate for the much darker body and weaker trim readability.

### Nocturne

The long rectangular convertible, grille, quad lamps, wire wheels, beltline and roof opening remain identifiable. The native studio hero is already extremely dark; it should not be treated as an ideal exposure reference. The native street shot is the more useful control.

Native `street-cruise.png` separates charcoal/blue-black body panels, burgundy seats, silver trim and the asphalt. Unity's open-top view presents an almost uniform navy side and a dark cabin hole. Burgundy seat color is not usefully readable in that player framing. This is a failure to present a preserved feature, not proof of missing upholstery. The native `cabin.png` shows why that feature matters: ribbed seats, belts, dashboard, wheel and door trim provide most of the open car's warmth and craft.

Unity's pale front bumper, sparkling grille and wire wheels attract more attention than the coachwork. Nocturne also has less screen space than native's studio hero or street shot, which contributes to the loss. The current open-roof image is not a convincing interior showcase.

## Prioritized defects

P1 here means a visible problem undermining the central lowrider presentation; P2 means a substantial polish or reviewability issue. These are visual priorities, not crash/safety severities.

| Priority | Observed defect and evidence | Consequence |
| --- | --- | --- |
| P1 | Dark cars and road lose material/value separation: Luna `05-media-luna-lift.png` versus native `street-raised.png`; Nocturne `06-nocturne-roof.png` versus native `street-cruise.png`. | Cars lose their authored palette and body form in the intended player setting. |
| P1 | Chrome/trim/grille/wire-wheel highlights become granular bright flecks. Clear in Unity Catrina `frame-0000.png`, three-wheel still, Nocturne front view; compare native Catrina `side.png` and native Luna `street-cruise.png`. | Fine craft reads as raster noise, while broad pale bumpers lose convincing metallic range. |
| P1 | Ground contact is weak in the Unity street shots. Tire contact patches and underbody shadow are hard to distinguish against the broad dark road; compare native Luna `street-raised.png` and Nocturne `street-cruise.png`. | Lift and three-wheel poses have less weight and spatial clarity. This is not evidence of an actual tire collision or suspension defect. |
| P2 | Cabins/glazing suppress warm interior identity: Luna gray panes/seats and Nocturne dark open cabin; Catrina raw frame 240 proves ribbing exists but receives little useful light. | Open tops and transparent glass fail to reward inspection of the interior. |
| P2 | Showroom framing undersells the assets. Garage Catrina is only roughly 370 pixels wide against large bright buildings; Nocturne uses roughly 530 pixels of width and hides the cabin at a low exterior angle. | Existing ornament/interior detail cannot carry the main-menu promise; this also limits review confidence. |
| P2 | Catrina's lace and gold trim lose readability while paint/trim acquires a rough digital texture. Native `front-detail.png`/`cabin.png` versus garage and three-wheel view. | The most individual decoration becomes secondary to generic shine. Controlled close-ups are required before declaring texture data lost. |

## Likely causes, with confidence limits

The current checkout supports several hypotheses. It is not a frame capture of GPU shader values, and this audit did not establish a complete source-to-r9 hash equivalence for each code line. Treat these as diagnostic leads to verify against the r9 source manifest, not retrospective proof of one root cause.

- `Host/StandaloneHost.cs:39-42,53` uses one warm directional light at intensity 2.4, trilight ambient, a custom sky reflection, low shadow settings, an 18 m shadow distance and no hardware MSAA. The visible bright sidewalk/dark-road division and dark car bodies are consistent with this global lighting balance. Increasing every material's base color would mask the problem rather than establish correct lighting.
- `Editor/CinderBuild.cs:24` imports the reflection cube at 128 pixels. The inspected host code uses a global sky reflection, with no local city reflection probe. Broad sky response is present, but it does not provide the street/storefront/ground structure that makes polished metal and lacquer visually grounded. This is a plausible contributor to pale/blue reflections, not proof that cube resolution alone caused glitter.
- `View/CinderGrade.shader` already applies tone mapping and an FXAA-like edge filter. Saying the build has no antialiasing at all would be incorrect. The observed tiny specular highlights still alias; postprocess edge smoothing does not by itself establish stable subpixel specular response. Still images cannot prove temporal shimmer.
- `Editor/GlbImport.cs:38,50-59` and generated vehicle materials retain clearcoat, normals and packed roughness/metal maps. Clearcoat is **not simply absent**. The refresh also clamps coat roughness to at least .10 and lacquer normal scale to .12, and caps high-metal smoothness at .86. `CinderBody.shader` applies the coat with the same `s.Normal` as the base surface. Compare base and coat normal/roughness behavior under a controlled light before attributing the appearance solely to missing maps.
- The importer caps image textures at 1024 and compresses them. That is a plausible loss source for narrow lace/ornament patterns, but the existing player framing and lighting also hide them. Verify original versus imported texture samples at equal scale before changing resolution globally.
- The importer has no `occlusionTexture` field and the body shader does not explicitly assign occlusion. This is a capability gap, **not evidence that these donor vehicles contained an AO map that the port dropped**. The observed weak contact/cavity shading could be addressed by a suitable lighting/contact solution; adding AO everywhere without diagnosis could just darken already dark cars.
- `View/CinderView.cs:70-75` gives the garage and general exterior a 48-degree field of view, uses a generic garage offset and horizontal aim shift for the menu. These are deliberate framing choices. They explain some detail loss without requiring an asset regression.

## Five repairs in order

1. **Establish one neutral vehicle presentation setup and repair the car/road exposure relationship.** Compare matte neutral, whitewall, black rubber, rose/teal/black paint and chrome together. Recover each vehicle's authored color separation in the actual street shadow as well as sun. Do not replace the paint palette with brighter guesses.
2. **Fix brightwork stability and metal range.** Test wire spokes, thin trim, grille and a large bumper at matched pixel scale, with stationary and moving cameras. Separate texture/geometry aliasing from specular aliasing; use a performance-bounded solution. Verify the existing edge filter and coat normals before adding effects.
3. **Restore contact and cavity depth.** Make loaded tire contact, underbody mass, wheel-well depth and lifted-wheel separation readable. Tune local shadow/contact behavior within the existing guard profile; do not simply raise all graphics caps or add a black disk that conceals the mechanism.
4. **Give glass and cabins a deliberate joint pass.** Show burgundy Nocturne/Catrina upholstery and warm Luna cabin through glazing without making glass disappear or become opaque gray. Compare pane overlap, reflections and ribbed upholstery at the same camera positions.
5. **Recompose the garage and inspect decoration close up.** Give the selected car enough pixels to sell its finish. Include a deliberate upper-surface/decor view for Catrina and open-cabin view for Nocturne. Validate lace/trim texture preservation here; increase source fidelity only where the matched view demonstrates a need.

## Matched-shot requirements for the next independent review

- Preserve these failed images and this report. Keep the same 960 x 600 review profile unless a separate performance profile is authorized. A high-resolution beauty render alone does not repair the player view.
- For each car, record front three-quarter, exact side, wheel/trim close-up, cabin, and the car's signature raised/open state. Match camera height, FOV, vehicle image width, body orientation, travel/roof state and light direction. Use a neutral ground/studio pair to isolate materials, then a matched street pair to assess the shipped presentation.
- Put Catrina lace/gold trim, Luna sage roof/ivory whitewall/warm seats, and Nocturne burgundy seats in deliberately comparable views. Every feature must be visibly readable, not merely confirmed by a mesh count.
- Include neutral exposure/color controls and unchanged source material samples. Record source GLB and imported material/texture identities. Establish which changes affect materials, lighting, grade and camera separately.
- Add a short fixed camera pan and slow car roll to judge brightwork stability; sampled stills cannot assess shimmer. Show loaded tires and a lifted wheel together. Record native-relative verdict and absolute quality independently, without prescribing a score the reviewer must reach.

These repairs can stay within the selected Unity Built-in route. The inspected evidence does not justify an engine/pipeline change or vehicle remodel. It does justify withdrawing any claim that r9 already preserves the native cars' presentation quality.
