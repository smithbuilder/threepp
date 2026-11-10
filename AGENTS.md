# Cinder repository instructions

Follow [the shared prototype guidelines](docs/GAME-PROTOTYPE-GUIDELINES.md).
Read [the current handoff](docs/HANDOFF.md) before editing.

## Decisions already made, do not relitigate without new evidence

| Date (Pacific) | Decision |
| --- | --- |
| 2026-11-08 | Oliver requested migrating this driving title to Unity, following the shared guidelines, with independent reviewers. |
| 2026-11-08 | Unity 6000.3.6f1, Built-in forward, Linear, D3D11, Windows x64, Mono, .NET Standard 2.1. |
| 2026-11-08 | Main menu centers on lowrider car culture: La Catrina, Media Luna, Nocturne. Safari / buggy racing comes later. |
| 2026-11-09 | Oliver rejected r9 city, lighting and cars as a visual step backward. Compare against native references and restore fidelity before another visual acceptance claim. |
| 2026-11-09 | Oliver authorized the restoration followed by commit, merge, GitHub main push and a new Cinder release on the private Patcher hub. |
| Existing | Preserve C++ engine work and all other lanes' uncommitted vehicle work. Videos stay off GitHub. |

The Unity port lives in `Unity/`; donor C++ and assets remain intact. Do not stage unrelated work. Build and run through `tools/unity/Run-Cinder.ps1`. Automated runs are hidden, silent, bounded and serialized. Check all pause markers and available resources before every editor or player launch. Existing `SAFETY.md` graphics caps remain binding; high-resolution performance acceptance needs a separately authorized evaluation profile.

Independent reviewers must not implement the surfaces they judge. Keep failed review packets. A partial port or probe pass is not a quality-approved candidate.
