# Unity migration storyboard

2026-11-08 Pacific. Revision line: cinder-unity-r1.

## Ask, word for word

"Alright, I have a real challenge for you. We need to push this title over to Unity. Follow the guideliness that have been written. Think it'll be possible? If so, have independent reviewers to ensure we meet the quality bar, thanks."

## Donor audit

Seven vehicles: Safari, Original buggy, Baja 427, Switchback 27, La Catrina, Media Luna, Nocturne. Eight test lanes, Mercer City Block, and a separate legacy forest controller. Shared Bullet 6DOF physics runs at 240 Hz, with tyre footprints, spring and damper forces, limited contact grip, bump stops and aerodynamic torque. Portable boost and actuator models are reusable rules. Rendering/UI are C++ specific and must be replaced. Native performance and old review scores do not validate Unity.

Six GLBs carry authored vehicle art. Safari is body-only; buggy and Safari running gear need an authored mesh export. Large hero art needs LOD and batching before handheld acceptance. Portable tree, stone, HDR and terrain materials can be copied. All source files remain untouched.

## Recommended open calls

1. Keep all seven vehicles in one catalog and one solver. Recommended.
2. Keep distinct playground, Mercer and forest choices. Recommended. Record legacy-controller differences explicitly.
3. Preserve exact tuning and use four 240 Hz internal steps under the 60 Hz simulation clock. Recommended.
4. Use pure C# 6DOF contact physics rather than embedding Bullet or a second runtime. Recommended. Solver parity is a review gate, never assumed.
5. Keep reviewed hero meshes and add lower-detail authored exports. Recommended. Do not silently present primitives as finished cars.
6. Use the same module for standalone and host integration, with frame placement. Recommended.
7. Keep current conservative graphics automation caps. Recommended. Target 1080p/60 remains unverified until separately permitted and measured.

Unpicked calls use the recommended side.

## Later user direction, binding for the player-facing port

"once done, build out a main menu for our new unity project. However, focus it on the lowriders. We'll introduce the safari / buggy racing part later. For now, car culture with the lowriders kind of sets the game a part from just a normal racing game."

The main garage contains La Catrina, Media Luna and Nocturne. Cruise Mercer, Hydraulic Session and Workshop / Test Grounds are the front-door activities. Racing, Safari and buggy are deferred from the menu. The broader catalog remains available only for migration regression checks and explicit development launch flags. Earlier whole-donor audit notes are technical context, not a requirement to put racing in this menu.

## Timed review route and numbered moments

0-10 s: garage card, world and vehicle selection, complete vehicle silhouette.
10-25 s: playground whoops, low side view, visible contact and per-wheel travel.
25-40 s: Baja jump, actual flight, landing and recovery.
40-55 s: Mercer boulevard, La Catrina hop/three-wheel stance.
55-70 s: Media Luna paired front lift, Nocturne independent corner movement.
70-85 s: forest drive, pause/settings, return to garage.
Concept/reference frames: donor review sheets in docs/nocturne/review, docs/la-catrina/review and docs/switchback/review. Fresh Unity frames must replace reference-only frames before verdict.

## Cast, sound and budgets

All seven cars are selectable heroes, only the selected hero loaded. City kit: eleven buildings, street trees, curbs and markings. Forest: bounded loop with reusable conifers and stones. Audio is event-routed with synthesized placeholders only until provenance and listening review; automated evaluation is silent. Far cues are scheduled at distance / 343 m/s.

Scene target: <=700,000 submitted triangles, <=300 draws, 512 px local shadows under the current evaluation profile. Hero/mid/far LODs need measured counts. No performance verdict from estimates.

## Phases and gates

1. Freeze donor inputs and establish controls/module/sim contract.
2. Port numeric model and meaningful regression probes including replay/restore.
3. Import authored art and connect authoritative moving pivots, build worlds.
4. Build a hidden bounded Windows player, capture fresh evidence and control comparison.
5. Independent architecture, visual and gameplay review; repair failures, new revision and fresh evidence. Human feel/audio/comfort/comprehension/enjoyment remain UNVERIFIED.
