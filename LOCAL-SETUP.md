# threepp evaluation

Fork: https://github.com/smithbuilder/threepp

Upstream: https://github.com/markaren/threepp

Reviewed baseline: `8518a6c22d051775c45dbd0c04a3ba92e92a5366` (master).
Local work is on `setup/windows-evaluation`; the upstream source is retained.

**Current status: graphics paused after Oliver reported a full-system lock.**
Read [SAFETY.md](SAFETY.md) before launching anything. No automatic graphics
retest is part of this handoff.

## What is built

- **Timber Run**: an original arcade driving study. Procedural forest and rolling
  dirt loop, original buggy, visible wheel/suspension motion, chase camera,
  dust, ordered checkpoints, lap timer and session best. W/A/S/D or arrows,
  Space handbrake, C camera, R restart, P pause, Escape exit. Handling is custom
  ground-following arcade motion, not a PhysX vehicle simulation.
- **Engine Playground**: three original scenes demonstrating animated metal
  sculpture/instancing, reflective water/atmospheric sky, and generated trees
  with generated bark and leaf textures. Drag to orbit, wheel to zoom, 1/2/3
  to switch, Space pause, R reset.
- Upstream **scene editor**, **showpiece**, **water**, **tree_demo**, and
  **forest_demo**, available through the example launcher once revalidated.

All original showcase art is procedural. Upstream example assets retain their
separate licenses. Use the supplied supervised launchers; raw executables bypass
the external watchdog and are not the supported evaluation entry point.

## Build and checks

Visual Studio 2022 C++ Build Tools and its bundled CMake are already installed.
The helper finds the installation without changing PATH or installing tools:

```powershell
powershell -ExecutionPolicy Bypass -File Build-Playground.ps1
powershell -ExecutionPolicy Bypass -File Build-Playground.ps1 -Action Test
powershell -ExecutionPolicy Bypass -File Run-Evaluation.ps1 -SelfTest
```

Configuration is tracked in the `evaluation-windows` CMake preset. Core
dependencies are vendored; examples/tests fetch `threepp_data` at commit
`9689df3c4fbecabf727855657b5ac610caa8776d` and Catch2 v3.4.0 on first build.
Build outputs, assets and local incident logs are excluded from Git.

Before the incident: ten selected engine regression executables passed, all
three original scenes rendered, two upstream examples rendered, and an automated
2,100-frame driving run completed one lap with zero tree contacts. This proves
the bounded software paths, not system stability or physical keyboard feel.
After the safeguard changes: the full selected build succeeds, five CPU-only
regressions pass, the supervisor's harmless-child timeout test passes, and a
paused-launch refusal is confirmed. Graphics were not rerun.

## Source review

This was a targeted source/build review, not an exhaustive security audit. No
obvious malicious install/startup/credential collection was found in the reviewed
build path. Core license is MIT; retain LICENSE and THIRD_PARTY.md when distributing.
The upstream asset collection has per-asset terms, including attribution and
no-derivatives restrictions in some entries and the Boston Dynamics Spot terms.
Do not treat all example assets as commercially reusable.

The optional USD loader constructs a shell `curl` command from asset URLs; it
is unsuitable for untrusted input without hardening. It is disabled here.
Editor Python scripts are executable code and are disabled. Vulkan, DLSS, FSR,
USD, FBX, RLtools and Python bindings are off; PhysX and Assimp are not installed.
The editor therefore has no PhysX play session or Python scripting in this build.

The Reddit reference is the author's Dune Buggy racer:
https://www.reddit.com/r/TopologyAI/comments/1xlblst/
The post text was read, but the video player failed and direct media access was
denied (403); the clip itself was not watched. The author describes it as an
offline film render with AI driving. Our small study is not claimed to match its
visual quality or feature scope.
