# Cinder publication process

Read-only process audit, November 9, 2026, Pacific Time. The last local source-tree check was at 8:40 PM PST. This document records the established publication route; writing it did not package, upload, select, launch, merge or push anything.

Oliver authorized restoration followed by committing, merging, pushing to GitHub and publishing to Patcher. The selected target is a new private Patcher product, `cinder`, titled `Cinder`. No additional identity decision is pending. Publish the newly restored and independently reviewed player, not the visually rejected r9 control.

## Verified live identity and access

- The configured private hub is `https://promaxgb10.tail3b2a94.ts.net:8444`.
- Its live catalog contained 13 products. All 14 main/build-line envelopes verified against the public key pinned in `C:/Users/oliver/Projects/patcher/src/desktop/config.json`.
- No product or build line matched Cinder, Rally, Lowrider or ThreePP. The owner-readable `games/` directory also contained no Cinder entry. There is no existing native Cinder Forest Rally catalog selection to replace on this hub.
- Use stable product ID `cinder` and a new main-line release. Do not repurpose another woodland or driving game's catalog identity. A new build line is unnecessary.
- Owner SSH alias `gb10` worked without an interactive prompt. The host runs Node 22.22.3 and had approximately 2.0 TB free on the data filesystem.
- Local Node 24.16.0 successfully imported the existing publisher and its installed dependencies. No install or Patcher checkout modification was required.
- The first Cinder release has no prior Cinder selection to roll back to. Subsequent releases can select an earlier intact signed Cinder release by its exact release ID.

These facts are point-in-time evidence. Re-read and verify the relevant signed catalog before publication and after promotion. A restricted-runner DNS failure is not evidence that Patcher is down; the same read-only calls succeeded with normal network access.

## Git target and large-file audit

The live GitHub remote is `https://github.com/smithbuilder/threepp.git`.

| Ref at audit | Commit | Meaning |
| --- | --- | --- |
| Local `codex/unity-lowrider-port` | `9725f51c72a4428a9dba70a732fb3925932d14b6` | Port plus acceptance withdrawal and restoration plan |
| Remote `main` | `f89e05778e05cff8e51c87af0d103a1509e3f210` | Established native La Catrina integration checkpoint |
| Remote default `master` | `8518a6c22d051775c45dbd0c04a3ba92e92a5366` | Older upstream engine branch; also an ancestor of the port |

The port was three commits ahead of `origin/main`. GitHub still reports `master` as its default. Target `main` explicitly when integrating this work. Do not change GitHub's default branch or silently use the default branch as a new integration decision.

The read-only audit inspected all 3,305 tracked files in `HEAD`, plus all 179 new blob objects reachable in `origin/main..HEAD`, including intermediate history. No tracked file or newly introduced blob exceeded 100 MiB. No video object was introduced in those three commits. The largest tracked file was the existing `showcase/assets/safari-body.glb`, 69,113,160 bytes. The frozen Catrina GLB was 35,648,880 bytes. This audit did not stage or modify native source, and it does not certify future restoration commits that did not yet exist.

Before pushing the final restored candidate, repeat the large-blob/video audit over the new commit range. Keep player builds, review MP4s, ZIP archives and generated captures out of GitHub. Stage only the intended Unity restoration, portable sources, documentation and selected small review evidence. Preserve every native lane's dirty work.

After scoped commits and final checks, a fast-forward update of `main` avoids checking out or resetting the dirty native tree:

```powershell
git fetch origin main
git merge-base --is-ancestor origin/main HEAD
if ($LASTEXITCODE -ne 0) { throw 'Remote main diverged. Review the integration before pushing.' }
git push origin HEAD:main
```

Recheck the remote tip afterward. Do not force-push or use `git add .` to collect unrelated native work.

## Portable player and signing

Publish the complete reviewed `builds/<revision>/` folder. The entry is `Cinder.exe`; its Unity data, Mono runtime, DLLs and required notices travel with it. Patcher launches the entry from the installed release directory. No launch path may depend on this checkout.

Keep ordinary player arguments to `['-module', 'cinder-drive']`. This opens the lowrider garage. Preserve the normal player settings and its default borderless behavior. Capture, probe, UI-probe, culture-flow, autoplay, silent, diagnostic and evaluation-watchdog flags belong only to bounded verification sessions and must not become the ordinary Patcher launch route.

The established Authenticode helper is:

```powershell
$patcherRoot = Join-Path $env:USERPROFILE 'Projects/patcher'
$cinderRoot = (Get-Location).Path
$revision = 'cinder-unity-rN' # Replace with the new reviewed revision.
$player = Join-Path $cinderRoot "builds/$revision/Cinder.exe"
powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $patcherRoot 'scripts/sign-windows.ps1') -Executable $player
```

The helper uses the existing Azure Artifact Signing setup, timestamps the executable, then verifies it with `signtool verify /pa /all`. It refuses missing inputs or unavailable login. Private signing material stays in its existing location. Do not copy it into the build, package, repository or chat.

Signing changes the executable bytes. Perform the exact-player probe, captures, performance comparison and final manifest binding after signing. Never substitute an older player or its receipts. `Run-Cinder.ps1` requires a valid signature and passing probe for the exact executable before graphics runs.

Automated validation continues through `tools/unity/Run-Cinder.ps1`: hidden, silent, serialized, bounded, with pause markers, the native evaluation mutex, no other editor/player, at least 4 GiB free RAM and 15 GiB disk, a 2 GiB process job, cool-down and watchdog. The existing 960 x 600 / 30 fps graphics caps remain binding. Publication does not authorize an unattended fullscreen playtest or a new high-resolution profile. Do not open Patcher or launch the game just to check publication.

## Artwork and version labels

The publisher's `--artwork` is a local `.png`, `.jpg`, `.jpeg` or `.webp` file. The bytes must match the declared format and be at most 96 KiB, or 98,304 bytes. It does not accept a URL and does not resize or compress automatically. An oversized image causes a safe error. A roughly 512-pixel-wide JPEG or WebP made from an actual still of the final reviewed player is appropriate. Save the prepared tile inside this repository and retain its source-frame/hash record. Do not use concept art or an older native capture to imply that the published Unity player already looks that way.

`--version cinder-unity-rN` is supported. Product display versions are bounded nonempty strings up to 80 characters, not semantic-version ordering keys. The launcher displays `manifest.version` directly. The live catalog already uses labels such as `shoreline-unity-r22`, `runaway-parade-r216` and `visual-main-v17`. The server follows explicit signed release selections rather than comparing those display labels.

Each publication receives a unique immutable `releaseId`, automatically generated unless `--release` is supplied. Record the actual generated ID. Never reuse a published ID for changed bytes, even if its display version is unchanged. If an upload fails after promotion may have completed, inspect the signed live selection before retrying.

## Prepare, inspect and upload

Use the existing Patcher scripts by absolute path. Keep all newly written package material in the Cinder workspace; do not write into the Patcher checkout.

```powershell
$package = Join-Path $cinderRoot "evidence/$revision/patcher-package"
$tile = Join-Path $cinderRoot "evidence/$revision/review/patcher-tile.jpg"
$notes = Join-Path $cinderRoot "evidence/$revision/release-notes.txt"

node (Join-Path $patcherRoot 'src/publisher/index.mjs') `
  --dir (Join-Path $cinderRoot "builds/$revision") `
  --game cinder --title Cinder --version $revision --entry Cinder.exe `
  --description 'Lowrider culture in Mercer. Cruise La Catrina, Media Luna and Nocturne, then work their hydraulics and air suspension.' `
  --args '["-module","cinder-drive"]' `
  --artwork $tile --notes-file $notes `
  --package-only --output $package
```

Use a new package directory. The publisher writes `archive.zip` and `manifest.json` exclusively and validates every archive member against the initial inventory. Inspect the package before uploading. `collectBuild()` rejects links, path escapes and case collisions, and automatically excludes Unity DoNotShip/debug folders, VCS folders, logs and debug symbols. That exclusion list is not a general secrets scan. Confirm the package contains only the portable player and required resources, with no source checkout, credentials, certificates, local databases, raw review footage or evidence folders.

The manifest schema is version 1. It contains `gameId`, immutable `releaseId`, title, description, display version, `platform: win32`, `arch: x64`, relative `.exe` `entryPoint`, argument string array, date, release notes, optional signed artwork, archive SHA-256/compressed and unpacked sizes, and a per-file relative path/size/SHA-256 inventory. The declared entry must exist and be nonempty. This new product omits `line` and `lineLabel`.

Upload exactly the inspected package:

```powershell
node (Join-Path $patcherRoot 'scripts/upload-prepared.mjs') $package
```

`uploadBuild()` uses the existing `gb10` owner SSH alias, creates a private incoming UUID directory, transfers the two prepared files with SCP, then invokes the server's `promote` command. The host revalidates the archive, signs the manifest with its resident Ed25519 key, stores an immutable release, and atomically moves only the selected product pointer. It does not deploy or restart the service. Failed validation leaves the old selection intact.

The private host paths are `/home/osmith/Projects/patcher` and `/home/osmith/.local/share/patcher`. No publisher token is required or bundled; owner SSH is the publication authority and players cannot publish through HTTP.

## Verification and rollback

After promotion, fetch `/api/catalog` again and verify the Cinder envelope against the same pinned public key. Compare exact game ID, release ID, version, entry, arguments, file inventory and archive hash with the inspected local package. The immutable archive route is `/api/releases/cinder/<release-id>/archive`.

The established `prepareCustomerRelease(package, { verifyPublished: true })` function in `patcher/scripts/prepare-customer-release.mjs` provides an additional read-only comparison: it validates the local archive and reads the exact signed remote envelope over owner SSH. Its CLI receipt writer is restricted to the Patcher checkout's `.local` folder, so do not call that writer for this task. Import the pure preparation function and retain its returned JSON in the Cinder evidence folder instead. That check neither promotes a public product nor changes any private selection.

For a later Cinder release, record the prior ID before publication. The existing rollback command revalidates the old archive and signature before moving the pointer:

```powershell
ssh -o BatchMode=yes gb10 'cd /home/osmith/Projects/patcher && PATCHER_DATA_DIR=/home/osmith/.local/share/patcher /home/osmith/.local/bin/node src/server/admin.mjs select cinder PRIOR-RELEASE-ID'
```

Version labels do not block rollback. Keep prior immutable releases and local evidence. Do not delete or edit release files, clear a live publication lock, or guess that an incomplete upload is safe to remove.

This is the private Patcher publication route. Public customer export is a separate exact-release approval route and is not performed by these commands. Normal player discovery is through Patcher Refresh; live catalog verification establishes publication without taking over the desktop. Installation on another PC, physical controls, heard audio, comfort and target-device performance remain separate checks.

## Owning process sources

- `C:/Users/oliver/Projects/patcher/docs/ONBOARDING.md`
- `C:/Users/oliver/Projects/patcher/docs/HOSTING.md`
- `C:/Users/oliver/Projects/patcher/src/publisher/index.mjs`
- `C:/Users/oliver/Projects/patcher/src/core/manifest.mjs`
- `C:/Users/oliver/Projects/patcher/src/server/admin.mjs`
- `C:/Users/oliver/Projects/patcher/scripts/sign-windows.ps1`
- `C:/Users/oliver/Projects/patcher/scripts/upload-prepared.mjs`
- `C:/Users/oliver/Projects/patcher/scripts/prepare-customer-release.mjs`

The current native and Unity safety rules remain in `SAFETY.md`, `AGENTS.md`, `docs/HANDOFF.md` and `tools/unity/Run-Cinder.ps1`.
