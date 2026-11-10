"""Bind a Cinder review packet to completed guarded capture sessions.

This helper never launches an editor or player. It copies selected evidence and
encodes the original PNG sequences without adding motion, captions, or audio.
Run with the repository's Python environment containing Pillow and ffmpeg.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = {"menu": 1, "ui": 180, "catrina": 180, "luna": 180, "nocturne": 870}
VEHICLES = {"menu": "catrina", "ui": "catrina", "catrina": "catrina", "luna": "media-luna", "nocturne": "nocturne"}
ERROR_PATTERN = re.compile(
    r"\b(?:FAIL\s|[A-Za-z]+Exception\b|Fatal\s+error|Crash!!!|Assertion\s+failed|"
    r"Shader\s+error|ERROR\s*[:\[]|Failed\s+to\s+(?:load|create|initialize))", re.I
)


class EvidenceError(RuntimeError):
    pass


def require(condition, message):
    if not condition:
        raise EvidenceError(message)


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as error:
        raise EvidenceError(f"Cannot read evidence JSON {path}: {error}") from error


def inside(path, parent):
    resolved = Path(path).resolve()
    require(resolved == parent or parent in resolved.parents, f"Path leaves its expected evidence location: {resolved}")
    return resolved


def relative(path):
    return path.relative_to(ROOT).as_posix()


def run(command, *, timeout=180, env=None, binary=False):
    result = subprocess.run(command, capture_output=True, text=not binary, timeout=timeout, env=env)
    if result.returncode:
        error = result.stderr.decode("utf-8", errors="replace") if binary else result.stderr
        raise EvidenceError(f"Evidence tool exited {result.returncode}: {command[0]}\n{error[-5000:]}")
    return result.stdout


def signature(exe):
    require(os.name == "nt", "The final packet needs a live Windows Authenticode check.")
    env = dict(os.environ, CINDER_REVIEW_EXE=str(exe))
    command = (
        "$s=Get-AuthenticodeSignature -FilePath $env:CINDER_REVIEW_EXE;"
        "[pscustomobject]@{status=[string]$s.Status;"
        "subject=$s.SignerCertificate.Subject;thumbprint=$s.SignerCertificate.Thumbprint}"
        "|ConvertTo-Json -Compress"
    )
    data = json.loads(run(["powershell", "-NoProfile", "-NonInteractive", "-Command", command], env=env, timeout=30).lstrip("\ufeff"))
    require(data.get("status") == "Valid", f"The exact player signature is not valid: {data.get('status')}")
    return data


def scan_logs(session):
    examined = []
    for name in ("player.log", "stdout.log", "stderr.log"):
        path = session / name
        require(path.is_file(), f"Missing runtime log: {path}")
        lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
        errors = [(n + 1, line) for n, line in enumerate(lines) if ERROR_PATTERN.search(line)]
        require(not errors, f"Runtime error in {path}: {errors[:5]}")
        examined.append(relative(path))
    return examined


def file_row(path):
    return {"path": relative(path), "bytes": path.stat().st_size, "sha256": digest(path)}


def image_checks(frames):
    try:
        from PIL import Image, ImageStat
    except ImportError as error:
        raise EvidenceError("Pillow is required to inspect captured frames. Use the installed Hermes Python environment.") from error
    minimum_mean, minimum_range = 255.0, 255
    for path in frames:
        with Image.open(path) as original:
            require(original.format == "PNG" and original.size == (960, 600), f"Unexpected capture format or dimensions: {path}")
            image = original.convert("RGB")
            gray = image.convert("L").resize((160, 100))
            low, high = gray.getextrema()
            mean = ImageStat.Stat(gray).mean[0]
            require(mean > 1.0 and high > 8 and high - low >= 8, f"Black or uniform capture frame: {path}")
            minimum_mean = min(minimum_mean, mean)
            minimum_range = min(minimum_range, high - low)
    return {"checkedFrames": len(frames), "minimumMeanLuma": minimum_mean, "minimumLumaRange": minimum_range, "dimensions": [960, 600]}


def select_pose(session, field):
    candidates = []
    for path in sorted(session.glob("pose-*.json")):
        match = re.fullmatch(r"pose-(\d{4})\.json", path.name)
        require(match is not None, f"Unexpected pose receipt name: {path}")
        pose = read_json(path)
        try:
            value = float(pose["state"]["Position"]["Y"] if field == "bodyY" else pose["roofPhase"])
        except (KeyError, TypeError, ValueError) as error:
            raise EvidenceError(f"Missing measured {field} in {path}") from error
        require(math.isfinite(value), f"Non-finite pose measurement: {path}")
        frame = int(match.group(1))
        require((session / f"frame-{frame:04d}.png").is_file(), f"Pose has no corresponding runtime frame: {path}")
        candidates.append((value, -frame, path, pose))
    require(candidates, f"No actual pose receipts in {session}")
    value, negative_frame, path, pose = max(candidates, key=lambda row: (row[0], row[1]))
    return {"frame": -negative_frame, "posePath": path, "pose": pose, "metric": field, "value": value}


def write_new(path, data):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", required=True)
    for role in EXPECTED:
        parser.add_argument(f"--{role}-session", required=True, type=Path)
    parser.add_argument("--catrina-frames", type=int, default=180, help="Expected original Catrina capture count, from 1 to 900; default 180.")
    parser.add_argument("--luna-frames", type=int, default=180, help="Expected original Media Luna capture count, from 1 to 900; default 180.")
    parser.add_argument("--output", type=Path, help="A new folder under evidence/<revision>; defaults to review. Existing folders are never overwritten.")
    args = parser.parse_args(argv)
    expected_counts = dict(EXPECTED)
    for role in ("catrina", "luna"):
        count = getattr(args, role + "_frames")
        require(1 <= count <= 900, f"Expected {role} capture count must be from 1 to 900.")
        expected_counts[role] = count
    require(sum(expected_counts[role] for role in ("ui", "catrina", "luna", "nocturne")) <= 90 * 30, "The original evidence sequences would exceed the 90-second proof limit.")
    require(re.fullmatch(r"cinder-unity-r\d+", args.revision), "Use an existing cinder-unity-rN revision.")
    revision_root = (ROOT / "evidence" / args.revision).resolve()
    require(revision_root.is_dir(), f"Revision evidence is missing: {revision_root}")
    output = inside(args.output if args.output else revision_root / "review", revision_root)
    require(not output.exists(), f"Review folder already exists. Preserve it and choose a new --output folder: {output}")
    require(output != revision_root, "The output must be a new child folder of the revision evidence.")
    exe = ROOT / "builds" / args.revision / "Cinder.exe"
    require(exe.is_file(), f"The selected player is missing: {exe}")
    exe_hash = digest(exe)
    signed = signature(exe)
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    require(ffmpeg and ffprobe, "ffmpeg and ffprobe must be installed before packaging.")
    ffmpeg_version = run([ffmpeg, "-version"], timeout=20).splitlines()[0]

    latest_path, build_path, sources_path = (revision_root / name for name in ("latest-probe.json", "build-receipt.json", "source-manifest.json"))
    latest, build, sources = (read_json(path) for path in (latest_path, build_path, sources_path))
    require(latest.get("success") is True and str(latest.get("exeSha256", "")).lower() == exe_hash, "The latest successful probe does not match this exact signed player.")
    require(build.get("revision") == args.revision and build.get("result") == "Succeeded" and build.get("errors") == 0, "The revision has no successful build receipt.")
    require(build.get("unity") == "6000.3.6f1", "The build does not use the pinned Unity editor.")
    require(sources.get("revision") == args.revision and sources.get("fingerprint") == build.get("sourceFingerprint"), "The source manifest is not bound to the build receipt.")
    source_rows = sources.get("files")
    require(isinstance(source_rows, list) and source_rows, "The build source manifest is empty.")
    ordered = sorted(source_rows, key=lambda row: row["path"])
    calculated = hashlib.sha256("\n".join(row["path"] + "\0" + row["sha256"] for row in ordered).encode("utf-8")).hexdigest()
    require(calculated == sources["fingerprint"], "The recorded build source manifest fingerprint is invalid.")
    for row in source_rows:
        path = inside(ROOT / row["path"], ROOT)
        require(path.is_file() and digest(path) == row["sha256"].lower(), f"Build source drift since the reviewed player: {row['path']}")

    probe_session = inside(latest["session"], revision_root)
    probe_receipt = read_json(probe_session / "runtime-receipt.json")
    require(probe_receipt.get("normal") is True and str(probe_receipt.get("exeSha256", "")).lower() == exe_hash, "The probe session runtime receipt does not match the player.")
    sim_probe, rig_probe = (read_json(probe_session / name) for name in ("probe.json", "loaded-rig-probe.json"))
    for label, report in (("simulation", sim_probe), ("loaded rig", rig_probe)):
        require(report.get("Success") is True and int(report.get("Checks", 0)) > 0, f"The {label} gate has not passed.")
        require(report.get("Lines") and all(not line.startswith("FAIL ") for line in report["Lines"]), f"The {label} report contains a failed check.")
    require(int(latest.get("simChecks", 0)) == sim_probe["Checks"] and int(latest.get("rigChecks", 0)) == rig_probe["Checks"], "Latest-probe check counts disagree with their actual reports.")
    batch_probe = read_json(probe_session / "runtime-batch-probe.json")
    require(batch_probe.get("Success") is True and int(batch_probe.get("Checks", 0)) > 0, "Runtime batched-geometry gate has not passed.")
    require(int(latest.get("runtimeBatchChecks", 0)) == batch_probe["Checks"], "Runtime batch check count disagrees with its report.")
    scan_logs(probe_session)

    sessions, metadata, input_paths = {}, {}, set()
    for role, expected in expected_counts.items():
        session = inside(getattr(args, role + "_session"), revision_root)
        require(session.is_dir(), f"Missing {role} session: {session}")
        require(session not in sessions.values(), f"Each evidence role requires its own original capture session: {role}")
        receipt = read_json(session / "runtime-receipt.json")
        require(receipt.get("action") == "Capture" and receipt.get("normal") is True and receipt.get("revision") == args.revision, f"The {role} capture did not finish normally for this revision.")
        launch_args = receipt.get("launchArguments", [])
        forbidden = {"-material-control", "-colour-probe", "-local-reflection-diagnostic", "-sky-reflections-only"}
        require(not forbidden.intersection(launch_args), f"Diagnostic flags cannot enter the {role} review take.")
        material_path, render_path = session / "material-control.json", session / "render-diagnostics.json"
        if material_path.exists():
            require(read_json(material_path).get("control") == "none", f"The {role} take uses a material diagnostic.")
        if render_path.exists():
            render = read_json(render_path)
            require(not render.get("colourControl", False) and render.get("materialControl", "none") == "none", f"The {role} take uses a render diagnostic.")
        require(receipt.get("vehicle") == VEHICLES[role] and receipt.get("world") == "city", f"Unexpected vehicle or world in {role} capture.")
        require(str(receipt.get("exeSha256", "")).lower() == exe_hash and Path(receipt.get("exe", "")).resolve() == exe.resolve(), f"The {role} capture is bound to another player.")
        frames = sorted(session.glob("frame-*.png"))
        require([path.name for path in frames] == [f"frame-{n:04d}.png" for n in range(expected)], f"The {role} capture must contain exactly {expected} contiguous frames starting at zero; found {len(frames)}.")
        performance = read_json(session / "performance.json")
        require(performance.get("revision") == args.revision and performance.get("frames") == expected, f"The {role} performance receipt has another revision or capture count.")
        for field in ("medianMs", "p99Ms", "peakWorkingSetBytes"):
            require(isinstance(performance.get(field), (int, float)) and math.isfinite(performance[field]) and performance[field] >= 0, f"Invalid {role} performance field {field}.")
        logs = scan_logs(session)
        metadata[role] = {"session": relative(session), "expectedFrames": expected, "runtimeReceipt": receipt, "performance": performance, "frameInspection": image_checks(frames), "logsScanned": logs}
        sessions[role] = session
        input_paths.update(path for path in session.rglob("*") if path.is_file())
    ui_lines = (sessions["ui"] / "ui-probe.txt").read_text(encoding="utf-8-sig").splitlines()
    require(len(ui_lines) == 10 and all(line.startswith("PASS ") for line in ui_lines), "The UI session needs all ten scripted checks passing.")
    require(any("Start pauses" in line for line in ui_lines) and any("quit requires explicit confirmation" in line for line in ui_lines), "The UI receipt does not cover pause and quit confirmation.")

    selections = [
        {"role": "menu", "frame": 0, "name": "01-garage.png", "reason": "Original garage menu capture"},
        {"role": "ui", "frame": 53, "name": "02-pause.png", "reason": "Scripted pause check at captured frame 53"},
        {"role": "ui", "frame": 163, "name": "03-quit-confirmation.png", "reason": "Scripted quit confirmation at captured frame 163"},
    ]
    for role, metric, name in (("catrina", "bodyY", "04-catrina-three-wheel.png"), ("luna", "bodyY", "05-media-luna-lift.png"), ("nocturne", "roofPhase", "06-nocturne-roof.png")):
        selected = select_pose(sessions[role], metric)
        selections.append(dict(selected, role=role, name=name, reason="Highest recorded " + metric + " from the original pose JSON receipts"))
    for role in ("catrina", "luna", "nocturne"):
        require((sessions[role] / "replay-last.json").is_file(), f"Missing retained gameplay replay for {role}.")
    input_paths.update(path for path in probe_session.rglob("*") if path.is_file())
    input_paths.update((latest_path, build_path, sources_path))
    input_rows = [file_row(path) for path in sorted(input_paths)]
    game_rows = [file_row(path) for path in sorted(exe.parent.rglob("*")) if path.is_file()]

    output.mkdir(parents=False, exist_ok=False)
    receipts = output / "receipts"
    receipts.mkdir()
    try:
        for role, session in sessions.items():
            for name in ("runtime-receipt.json", "performance.json", "replay-last.json", "ui-probe.txt"):
                source = session / name
                if source.is_file():
                    shutil.copy2(source, receipts / (role + "-" + name))
        for source in (latest_path, build_path, sources_path, probe_session / "probe.json", probe_session / "loaded-rig-probe.json", probe_session / "runtime-batch-probe.json", probe_session / "runtime-receipt.json"):
            shutil.copy2(source, receipts / ("probe-runtime-receipt.json" if source == probe_session / "runtime-receipt.json" else source.name))
        selected_rows = []
        for selected in selections:
            source = sessions[selected["role"]] / f"frame-{selected['frame']:04d}.png"
            target = output / selected["name"]
            shutil.copy2(source, target)
            row = {"role": selected["role"], "frame": selected["frame"], "file": target.name, "source": relative(source), "sourceSha256": digest(source), "sha256": digest(target), "reason": selected["reason"]}
            if "posePath" in selected:
                pose_target = receipts / (selected["role"] + "-selected-pose.json")
                shutil.copy2(selected["posePath"], pose_target)
                row.update(metric=selected["metric"], measuredValue=selected["value"], poseReceipt=relative(selected["posePath"]), poseReceiptSha256=digest(selected["posePath"]))
            selected_rows.append(row)

        video_roles = ("ui", "catrina", "luna", "nocturne")
        command = [ffmpeg, "-hide_banner", "-nostdin", "-v", "error", "-n"]
        for role in video_roles:
            command += ["-threads", "1", "-framerate", "30", "-start_number", "0", "-i", str(sessions[role] / "frame-%04d.png")]
        filters = ";".join(f"[{i}:v]setpts=PTS-STARTPTS,format=yuv420p[v{i}]" for i in range(4)) + ";" + "".join(f"[v{i}]" for i in range(4)) + "concat=n=4:v=1:a=0[out]"
        total_frames = sum(expected_counts[role] for role in video_roles)
        proof = output / "proof.mp4"
        command += ["-filter_complex_threads", "1", "-filter_complex", filters, "-map", "[out]", "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-threads", "2", "-pix_fmt", "yuv420p", "-r", "30", "-frames:v", str(total_frames), "-movflags", "+faststart", str(proof)]
        run(command)
        media = json.loads(run([ffprobe, "-v", "error", "-count_frames", "-show_streams", "-show_format", "-of", "json", str(proof)]))
        streams = media.get("streams", [])
        require(len(streams) == 1 and streams[0].get("codec_type") == "video" and streams[0].get("codec_name") == "h264", "The proof must contain one H.264 video stream and no fabricated audio.")
        video = streams[0]
        require(video.get("width") == 960 and video.get("height") == 600 and video.get("avg_frame_rate") == "30/1", "The proof changed the captured dimensions or frame rate.")
        require(int(video.get("nb_read_frames", 0)) == total_frames, "The encoded proof is missing captured frames.")
        duration = float(media["format"]["duration"])
        require(duration <= 90 and abs(duration - total_frames / 30) < .04, "The proof duration differs from the original capture sequences.")
        run([ffmpeg, "-nostdin", "-v", "error", "-threads", "2", "-i", str(proof), "-f", "null", "-"])

        # Verify that concurrent work did not change an input after its initial hash.
        for row in input_rows:
            require(digest(ROOT / row["path"]) == row["sha256"], f"Source evidence changed during packaging: {row['path']}")
        packet = {
            "revision": args.revision, "createdUtc": datetime.now(timezone.utc).isoformat(), "status": "mechanical-evidence-verified",
            "player": {"path": relative(exe), "sha256": exe_hash, "authenticode": signed},
            "build": build, "sourceManifest": {"path": relative(sources_path), "sha256": digest(sources_path), "fingerprint": sources["fingerprint"], "currentListedSourcesMatch": True},
            "gates": {"simulationChecks": sim_probe["Checks"], "loadedRigChecks": rig_probe["Checks"], "runtimeBatchChecks": batch_probe["Checks"], "uiChecks": ui_lines, "probeSession": relative(probe_session)},
            "sessions": metadata, "stills": selected_rows,
            "proof": {"file": proof.name, "sha256": digest(proof), "frames": total_frames, "fps": 30, "durationSeconds": duration, "dimensions": [960, 600], "sequence": [{"role": role, "frames": expected_counts[role], "seconds": expected_counts[role] / 30} for role in video_roles], "audio": "None. Original automated captures were silent.", "decode": "PASS", "ffmpeg": ffmpeg_version, "command": command},
            "limitations": ["Mechanical encoding and non-black frame checks do not establish visual approval or input feel.", "These captures are 960x600 at 30 fps with PNG output. They do not establish 1080p/60 handheld performance.", "Heard audio, comfort, comprehension, enjoyment and physical gamepad feel remain UNVERIFIED until Oliver plays.", "The source capture sessions and their original receipts remain intact."],
            "deliveryManifest": "delivery-manifest.json", "packagingTool": file_row(Path(__file__).resolve()),
        }
        write_new(output / "packet.json", packet)
        delivered = [{"path": path.relative_to(output).as_posix(), "bytes": path.stat().st_size, "sha256": digest(path)} for path in sorted(output.rglob("*")) if path.is_file()]
        write_new(output / "delivery-manifest.json", {"revision": args.revision, "algorithm": "SHA256", "playerSha256": exe_hash, "files": delivered, "sourceEvidence": input_rows, "builtGameFiles": game_rows, "buildSources": source_rows, "selfHashExcluded": True})
        print(json.dumps({"success": True, "review": relative(output), "stills": 6, "proofSeconds": duration, "proofFrames": total_frames, "playerSha256": exe_hash}, indent=2))
        return 0
    except Exception as error:
        if not (output / "FAILED.json").exists():
            write_new(output / "FAILED.json", {"status": "incomplete", "error": str(error), "sourcesPreserved": True, "action": "Preserve this partial folder and choose a new output after fixing the failure."})
        raise


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (EvidenceError, OSError, subprocess.SubprocessError, ValueError) as error:
        print("FAIL review packaging: " + str(error), file=sys.stderr)
        sys.exit(1)
