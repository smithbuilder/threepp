# SmithBuilder game prototype guidelines

Version 1, 2026-11-08. For every agent (Claude, Codex, Gemini, Cursor, anyone) prototyping a game for Oliver Smith / SmithBuilder LLC. Put a copy in each game repo as `docs/GAME-PROTOTYPE-GUIDELINES.md` and point `AGENTS.md` at it. Repo-specific rules live in that repo's `AGENTS.md`; this sheet is what every repo shares.

**Why this exists.** Prototypes get built in different engines by different agents and then the good ones get lifted into a bigger game (Windowseat today). The port is free when the prototype is built the same way every time: a pure simulation with a thin view, a standard module contract, standard input, standard evidence. Follow this and "move it into Windowseat" is a copy, not a rewrite.

---

## 1. Engine and target

| | Rule |
|---|---|
| Engine | **Unity 6000.3.6f1, Built-in render pipeline, forward, Linear colour, D3D11, Mono, .NET Standard 2.1.** The same version and pipeline as Windowseat and PADDLES. Do not upgrade the editor or switch pipelines (HDRP and URP were evaluated and rejected) without Oliver's say-so. |
| Other engines | Godot 4.x is allowed for a throwaway prototype when Oliver asks for it; keep its rules in a pure GDScript class (section 2) so the model can be transcribed to C# later. C++ (engine-threepp) is for engine work and vehicle assets, not for game prototypes. **If it might end up in Windowseat, build it in Unity.** |
| Platform | Windows x64 first. It must play well on the handheld (ROG Ally class: 1080p, gamepad, 60 fps) because that is where Oliver plays. Steam later; nothing in the code may assume a launcher or a network. |
| Frame rate | 60 fps cap by default, v-sync off, a setting to change both. Nothing may stomp `targetFrameRate` every frame. |
| Window | Borderless fullscreen at the desktop resolution by default, windowed and exclusive as settings, the choice saved. Pause on focus loss. Escape pauses; quitting asks first. |

## 2. The one rule: simulation and view are separate

Every game is two halves.

**The sim** is the game. It is pure C# (or a pure GDScript class) and it:
- steps at a fixed `Dt = 1/60` with its own tick counter; sim time is `Tick * Dt`, never the wall clock;
- keeps all state in one serialisable `State` class with `Clone()` and `Restore()`;
- takes one `Input` struct per step (axes as doubles −1..1 or 0..1, buttons as bools) and nothing else;
- uses its own seeded PRNG (never `UnityEngine.Random`), so the same seed and inputs give the same game;
- references **no** `UnityEngine`, `Godot`, camera, audio, file or network API; nothing in `Step` touches a MonoBehaviour;
- uses doubles where speeds or distances are large (aircraft, long tracks), floats are fine for small arenas;
- exposes `Fingerprint()` (a short string hashing the state) and appends to an `Events` list (sounds, impacts, pickups) that the view drains each frame;
- may use the engine's physics only if the result is **baked** at build time into a recording the sim plays back (the Windowseat race bake), or if the physics step is driven by the sim's fixed clock and its results are recorded for the probe. A live rigidbody that the sim merely watches is not deterministic and is not a sim.

**The view** draws the state. It owns meshes, materials, camera, particles, audio and HUD, reads `State` and `Events`, and writes nothing back. A view may be replaced wholesale by a host's (Windowseat's toon kits, lighting and sound) and the game is still the same game.

**The glue** is a small MonoBehaviour that runs the accumulator loop and feeds input:
```csharp
accumulator += Time.unscaledDeltaTime;            // unscaled: no Time.timeScale pauses
int catchUp = 0;
while (accumulator >= Sim.Dt && catchUp++ < 120) { sim.Step(input); accumulator -= Sim.Dt; }
view.Pose(sim.State); view.Drain(sim.Events);
```
Pausing stops the accumulator. Menus never touch `Time.timeScale`.

PADDLES (`FlightSim.cs`, `DogfightEncounter.cs`, `WarzoneBattle.cs`) is the reference implementation: about 2,400 lines of sim with no `UnityEngine` reference, seeded, replayable, and its whole Unity half is replaceable.

## 3. The module contract

Every game, or each mini-game inside one, implements this interface, so a host (a standalone scene, the arcade hub, a Windowseat daydream) can run it without knowing what it is. Keep these names.

```csharp
public interface IGameModule
{
    ModuleInfo Info { get; }                     // id (kebab-case), name, one-word verb, controls text, typical length in seconds
    void Enter(ModuleContext ctx);               // build the view, place the sim in the host's frame, seed
    void Tick(float dt, in PadState pad);        // run the accumulator loop with the host's pad state
    void Pose(Camera cam);                       // set the camera for this frame (the host owns the Camera object)
    void Hud(Rect bar);                          // one line of HUD into the host's lower bar (OnGUI or UI Toolkit)
    ModuleResult Result { get; }                 // null until the module is over; then lines + a tier
    void Exit();                                 // tear down everything Enter made
}
public sealed class ModuleContext { public Frame Frame; public System.Func<double> Clock; public int Seed; public IHostAudio Audio; public IHostWorld World; }
public struct Frame { public Vector3 Origin; public Quaternion Rotation; public float Scale; }   // sim space -> world
public struct PadState { public Vector2 Left, Right; public float LT, RT; public bool A, B, X, Y, LB, RB, Start, View; public bool ADown, BDown, StartDown; }
public sealed class ModuleResult { public string[] Lines; public int Tier; /* 0 none, 1 bronze, 2 silver, 3 gold */ public string Fingerprint; }
```
- The module is the glue layer, so UnityEngine types (`Vector2`, `Camera`, `Rect`) are allowed here; the sim behind it stays pure.
- `Frame` maps the sim's local origin (a carrier deck, a track, an arena) into the host's world. Sims never bake world positions in.
- `Clock` is the host's clock (ride time in Windowseat, real time standalone); the sim's own time is still ticks.
- A standalone build is a `StandaloneHost` scene: a camera, the HUD bar, a pad reader, and one module. The same module class runs inside Windowseat unchanged.
- Give every module a `-module <id>` launch flag so it can be run and probed on its own.

## 4. Input: gamepad first

The family uses Unity's Input Manager (not the new Input System) with these axis names: `Horizontal`, `Vertical`, `RightStickX`, `RightStickY` (4th and 5th joystick axes), `DPadX`, `DPadY` (6th and 7th), `LeftTrigger`, `RightTrigger`. Copy the block from Windowseat's `Unity/ProjectSettings/InputManager.asset` rather than retyping it. Buttons by Unity's Xbox layout: A = `JoystickButton0`, B = 1, X = 2, Y = 3, LB = 4, RB = 5, View = 6, Start = 7, left stick click = 8, right stick click = 9.

| Control | Pad | Keyboard / mouse |
|---|---|---|
| Move / steer / swim | Left stick | W A S D or arrows |
| Look / camera | Right stick (click to settle) | Right-mouse drag |
| Confirm / primary action | A | E, Enter, Space, left click |
| Back / cancel | B | Escape (also pause) |
| Secondary actions | X, Y | Q, F |
| Analog throttle / brake | RightTrigger / LeftTrigger | Shift / Ctrl |
| Pause | Start | Escape |
| Admin / god mode | View | F1 or backquote |
| Menu tabs | LB / RB | Q / E |
| Menus | Left stick and D-pad; A chooses, B goes back | Mouse hover selects, click activates, drag sets sliders |

Rules: every action has a pad and a keyboard binding; key hints switch to pad wording after the first pad press; hit targets are at least 44 px (a thumb on the handheld); HUD text is at least 24 px at 1080p; a settings screen offers invert look and look sensitivity. Controls are listed in `START-HERE.md` as a table like the one above.

## 5. Units, frames and time

- SI everywhere: metres, kilograms, seconds, radians in code (degrees only in inspectors and docs). Y is up. Vehicles and aircraft face +Z; wheels/pivots are named in the asset.
- Each sim has one documented local origin (carrier-local, track coordinates `s` along and `a` across, an arena centre). World placement is the host's `Frame`, never the sim's.
- Speeds in m/s, distances in metres, times in seconds, in code, in docs and in evidence file names. Ride, race and sea clocks are seconds from a documented zero.
- Sound from far away arrives late: delay cues by distance / 343 m/s.

## 6. Assets

- **Authored meshes, not primitives.** Build in Blender 4.5 by script (`tools/blender/<kit>/*.py`), export FBX or GLB into `Assets/<Game>/Art/<kit>/`, with `assets/<kit>/manifest.json` recording every piece: source, author, date, triangle count, parts and pivots, placement notes. Greybox is allowed in a prototype only if the build is labelled greybox.
- Named pivots for anything that moves: `Wheel_FR/FL/RR/RL`, `WingPivot_L/R`, `Canopy_Hinge`, `Burner_L/R`, `Rotor_Main`, `Door_L`. Separate meshes for separate motion.
- LODs for anything seen both near and far: hero / mid / far (for example 30k / 8k / 2k triangles). Instance crowds and swarms.
- Budgets: state the triangle and draw-call budget for the scene in the handoff and measure against it (Windowseat: about 0.6–0.7M merged triangles per stop, vehicles 15–20k near, 5k far).
- Colour: palettes are authored in linear and darker than the target because of the toon grade; check in the running player, not in Blender.
- Reusing another project's asset: **copy it, never write to that project.** Record where it came from in the manifest (`provenance.json` for audio). Prefer original designs; a real make, badge or famous silhouette is a redo later.
- Audio: synthesised placeholders are fine; real recordings and generated music go through `audio/provenance.json`. Route every sound through the sim's `Events` so a host can re-voice it. The brief for all audio is "pleasant to the ears": measure gains (LUFS), do not guess them.

## 7. Determinism, probes and evidence

- **A probe for every build.** `-probe` runs a scripted session headless (or minimised, silent, with a finite quit watchdog), prints `PASS ...` / `FAIL ...` lines plus the final `Fingerprint`, and exits 0 or 1. The probe output is the regression baseline: diff it against the last reviewed build and explain every changed line.
- Replays are an initial `State` plus the list of inputs. Keep the replay of every independent review.
- **Evidence is proportional.** Per review candidate: one runtime receipt (build id, pass/fail checks, a performance summary), three to six stills, one clip of at most 90 seconds. Deliveries add a manifest with hashes. Never overwrite old evidence to make it look like it validates a new build; refresh it and get a fresh verdict.
- **Independent review** for visual and gameplay gates: a second agent who did not build it scores presentation and gameplay out of 10 from the running build with a written report. Levels 1–4 (3 is the paid-release bar) gate on the weakest required aspect.
- **Human-only checks stay UNVERIFIED** (input feel, heard audio, comfort, comprehension, enjoyment) until Oliver plays. Say so in the handoff; do not claim them.
- **Performance** is measured, not estimated: a benchmark run against a back-to-back control run of the last reviewed build on the same machine (the PC is noisy). Record median and p99 frame time and peak working set.

## 8. Working on Oliver's PC

- **Do not take over the desktop.** Never open or focus a game, editor or browser window unless he asks; never go fullscreen or capture the cursor in an automated run. Headless or minimised, silent, with a quit watchdog.
- **Resource guards before every player or editor launch:** free RAM above 3–4 GB, free disk above 15 GB, no other Unity Editor or player running (Codex often builds another project on the same machine), a cool-down between runs, and a `PAUSE` file that halts the queue. The PC hard-locked once without them.
- Builds and checks go through the repo's scripted builder or request queue (`RUN-BUILD-RUNNER.cmd`, `evidence/_requests/`), never by hand in the editor.
- **Never delete his files.** Move to an `_archive/` folder and tell him; he deletes. Ask before touching anything outside the repo you were given.
- Never write to another project's folder (engine-threepp, PADDLES, the arcade siblings). Read, copy, record provenance.

## 9. Repo, git and docs

```
AGENTS.md            the rules for this repo (CLAUDE.md just says "follow AGENTS.md"); link this sheet
README.md / START-HERE.md   how to play: the build to run, the controls table, what is in it
docs/HANDOFF.md      the live state: where things stand, how to build and check, next steps, gotchas
docs/DELIVERY.md     per release: what is playable, files, hashes, review scores, what is UNVERIFIED
docs/GAUNTLET.md     the iteration loop and gates for this game
docs/GAME-PROTOTYPE-GUIDELINES.md   this sheet
Unity/               the project; Assets/<Game>/Scripts/{Sim,View,Host,Editor}
tools/               builders, probes, blender scripts, audio tools, runners
art-review/          storyboards, concept frames, proof renders, review sheets (committed, small)
assets/              kit manifests and provenance (committed); sources and exports as the repo dictates
evidence/            receipts, stills, clips, probes (out of git except selected PNG, JSON and reports)
builds/              out of git; keep the current candidate and the last reviewed one only
.agents/skills/      reusable procedures in the open Agent Skills format (SKILL.md + scripts + references)
PLAY-*.cmd           one double-click to play the selected build
```
- **Commit as you go.** Never leave work untracked at the end of a session. Windows checks out CRLF: commit from Windows git, or pass `-c core.autocrlf=true` from anywhere else. Never stage generated scenes or build output.
- One revision name per build (`<line>-rN`), never reused; tag the candidate that went to review or to Patcher; keep at most the current candidate plus the last reviewed build on disk.
- **Decisions table.** `AGENTS.md` carries "Decisions already made, do not relitigate without new evidence". Add to it when Oliver decides; never silently reopen one.
- **Found along the way.** A bug in another project goes in a note (path, symptom, suggested fix), not in a fix to that project.
- Plain language, dates in Pacific Time, metres and seconds. **No em dashes in anything a player reads** (HUD, menus, subtitles, debriefs, START-HERE) or in docs.

## 10. Planning before building

For a new stop, scene or mode: storyboard first (Windowseat has the `windowseat-storyboard` skill; follow its shape elsewhere): the ask word for word, an asset audit with verdicts, a timed route, numbered moments, concept frames, a cast table, sound notes, five to seven open calls with the recommendation first ("anything unpicked gets the recommended side"), and build phases with budgets. Oliver builds the recommendation; make it the version the frames show.

## 11. Agent etiquette

- Read `AGENTS.md`, then `docs/HANDOFF.md`, then the current source before changing anything. Keep the handoff current when you finish.
- When Oliver's intent is clear, act; do not re-ask. When a decision can't be undone and could go either way, stop and ask with a recommendation.
- Report in three to five lines: what it is, what changed, what needs him. Visuals first: he wants to see it (a still, a clip, a page), not read about it.
- Put blockers in a "Needs you" box at the top of the page or handoff: a folder to add, an asset you can't find, a decision.
- Be honest about what is unverified. A probe pass is not a playtest.

## 12. Making it Windowseat-ready

Windowseat hosts mini-games as **daydreams**: a sparkle on something in the window, a whiteout, 60–80 s of play, a stamp, back to the seat at the same ride second. Its `Daydream` class is the module contract in section 3 with Windowseat's world as the `IHostWorld`. A prototype becomes a daydream when it also:
- has **one verb** (DRIVE, SWIM, HOLD, HOP) and one goal with one twist; the player understands it inside two seconds without a tutorial;
- runs **45–90 s** with its finale in the last 10–15 s, and can end early without breaking;
- has **no fail state**: a result with tiers (bronze for finishing, silver for doing it well, gold for well plus the finale);
- enters and exits in under 3 s with **nothing loaded or unloaded**: the view is built from meshes that are already in the host (or small kits), the arena is bounded, the sim starts from a state the host hands it;
- takes its camera, light, audio and HUD from the host; exposes `Events` for sounds and effects;
- is **deterministic** with a `Fingerprint`, so the daydream probe line (`PASS daydream <id> returns to the seat at ride N`) is stable.

**Reusing an existing prototype (the donor triage).**

| Donor | What to do | Cost |
|---|---|---|
| Same engine, sim/view split already (PADDLES) | Copy the sim files verbatim, write a view on the host's kits, wrap in `IGameModule` | days |
| Same engine, rules tangled in MonoBehaviours | Extract the rules into a sim first (find where the state really lives), then as above | about a week |
| Another engine (Godot, engine-threepp) | Port the **model and its numbers** (tuning, curves, rules, state machines), not the code; GDScript transcribes to C# mechanically; PhysX vehicle tuning maps onto WheelCollider fields | days |
| Any | Embedding another runtime (a second process, a native plugin with its own physics world) | never |

Carry over, in order of value: tuning numbers and curves; rules and state machines; control schemes and assists; opponents and AI; recorded clips as feel references. Leave behind: rendering, UI, audio, scene and menu code. Do a 20-minute donor audit (pure vs tangled, lines of code, what it assumes about the world) before scheduling any port.

## 13. Definition of done for a prototype candidate

1. `PLAY-*.cmd` launches the selected build; `START-HERE.md` has the controls table and what is in it.
2. The probe passes and its diff against the last reviewed build is explained.
3. Evidence: receipt, three to six stills, one clip of at most 90 s; a manifest for deliveries.
4. `docs/HANDOFF.md` is current: state, how to build and check, next steps, gotchas, the UNVERIFIED list.
5. Manifests and provenance cover every asset and sound.
6. A performance number against a control run.
7. An independent review score with its report, for anything going to Oliver as a candidate.
8. Everything committed; builds and evidence out of git; nothing written to any other project.
