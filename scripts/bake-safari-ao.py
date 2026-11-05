"""Offline geometry AO candidate; source GLB and albedo/direct light stay untouched.

Requires existing NumPy/Pillow and the locally built CPU safari_ao_bake helper.
The candidate is written only under ignored build/. No graphics context or API.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import io
import json
from pathlib import Path
import struct
import subprocess
import time
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
FROZEN_SHA256 = "51218c6700105876a909a9347e23ec0d70fea6c9ceaa7a0c7f77b6032d17dc14"
DTYPES = {5120: "i1", 5121: "u1", 5122: "<i2", 5123: "<u2", 5125: "<u4", 5126: "<f4"}
COMPONENTS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_glb(path: Path):
    data = path.read_bytes()
    assert len(data) < 128 * 1024 * 1024, "GLB exceeds offline preparation bound"
    assert struct.unpack_from("<III", data) == (0x46546C67, 2, len(data)), "Expected GLB2"
    at = 12
    document, binary = None, None
    while at < len(data):
        size, kind = struct.unpack_from("<II", data, at)
        assert at + 8 + size <= len(data), "Truncated GLB chunk"
        chunk = data[at + 8:at + 8 + size]
        if kind == 0x4E4F534A:
            document = json.loads(chunk)
        elif kind == 0x004E4942:
            binary = chunk
        at += 8 + size
    assert document is not None and binary is not None
    return data, document, binary


def read_accessor(document, binary, index):
    accessor = document["accessors"][index]
    assert "sparse" not in accessor, "Sparse accessors need a separate preparation stage"
    view = document["bufferViews"][accessor["bufferView"]]
    assert view.get("buffer", 0) == 0
    dtype = np.dtype(DTYPES[accessor["componentType"]])
    components = COMPONENTS[accessor["type"]]
    stride = view.get("byteStride", dtype.itemsize * components)
    offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    return np.ndarray((accessor["count"], components), dtype=dtype, buffer=binary,
                      offset=offset, strides=(stride, dtype.itemsize)).copy()


def write_glb(path: Path, document, binary: bytearray):
    document["buffers"][0]["byteLength"] = len(binary)
    encoded = json.dumps(document, separators=(",", ":"), allow_nan=False).encode()
    encoded += b" " * ((-len(encoded)) % 4)
    packed = bytes(binary) + b"\0" * ((-len(binary)) % 4)
    total = 12 + 8 + len(encoded) + 8 + len(packed)
    path.write_bytes(struct.pack("<III", 0x46546C67, 2, total)
                     + struct.pack("<II", len(encoded), 0x4E4F534A) + encoded
                     + struct.pack("<II", len(packed), 0x004E4942) + packed)


def assign_cell_slots(quantized_quads, lookup, capacity):
    """Share only byte-identical four-texel fields, across all receiving meshes.

    A triangle keeps its own corner permutation. Equal A/B/C/D texels therefore
    give exactly the same bilinear field at every barycentric coordinate, with
    no extra approximation beyond the existing 8-bit quantization.
    """
    quads = np.asarray(quantized_quads)
    assert quads.dtype == np.uint8 and quads.ndim == 2 and quads.shape[1] == 4
    unique, inverse = np.unique(quads, axis=0, return_inverse=True)
    keys = [row.tobytes() for row in unique]
    missing = [key for key in keys if key not in lookup]
    assert len(lookup) + len(missing) <= capacity, "AO atlas unique-field capacity exceeded"
    for key in missing:
        lookup[key] = len(lookup)
    unique_slots = np.asarray([lookup[key] for key in keys], dtype=np.int64)
    return unique_slots[inverse], unique_slots, unique


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "showcase/assets/safari-body.glb")
    parser.add_argument("--output", type=Path, default=ROOT / "build/safari-ao-v1/safari-body.glb")
    parser.add_argument("--helper", type=Path, default=ROOT / "build/windows-gl/bin/Release/safari_ao_bake.exe")
    parser.add_argument("--expected-sha256", default=FROZEN_SHA256)
    parser.add_argument("--reuse-values", type=Path, help="Use already baked values matching the exact source hash")
    parser.add_argument("--atlas-layout", choices=("median", "original"), default="median",
                        help="Median corner at A avoids fourth-pixel clipping; original reproduces v1")
    parser.add_argument("--force", action="store_true", help="Replace this named disposable candidate only")
    args = parser.parse_args()
    started = time.perf_counter()
    source = args.source.resolve()
    output = args.output.resolve()
    assert output.is_relative_to((ROOT / "build").resolve()), "Candidates must remain under ignored build/"
    assert source != output, "Never overwrite source GLB"
    assert args.force or not output.exists(), "Candidate exists; choose a new version or explicitly --force"
    raw, original, original_binary = load_glb(source)
    source_hash = sha(raw)
    assert source_hash == args.expected_sha256.lower(), "Frozen source identity changed"
    assert len(original["buffers"]) == 1 and not original.get("animations") and not original.get("skins")
    for node in original["nodes"]:
        assert not any(k in node for k in ("matrix", "translation", "rotation", "scale")), "Bake transforms first"
    output.parent.mkdir(parents=True, exist_ok=True)
    values_path = args.reuse_values.resolve() if args.reuse_values else output.parent / "ao-values.json"
    if not args.reuse_values:
        with (output.parent / "bake-stdout.log").open("w") as out, (output.parent / "bake-stderr.log").open("w") as err:
            subprocess.run([str(args.helper.resolve()), str(source), str(values_path)], stdout=out, stderr=err, check=True)
    bake = json.loads(values_path.read_text())
    assert bake["sourceSha256"] == source_hash and not bake["graphicsContext"]
    assert bake["samples"] == 16 and abs(bake["strength"] - .5) < 1e-6
    values_file = values_path.parent / bake["valuesFile"]
    assert values_file.resolve().parent == values_path.parent.resolve(), "Unexpected AO buffer path"
    values = np.fromfile(values_file, dtype="<f4")
    assert np.all(np.isfinite(values)) and np.all((values >= 0) & (values <= 1))

    document = copy.deepcopy(original)
    binary = bytearray(original_binary)
    atlas_size = 1024
    atlas = np.full((atlas_size, atlas_size, 4), 255, dtype=np.uint8)
    cells_per_row = atlas_size // 2
    cell = 0
    cell_lookup = {}
    receiver_triangles = 0
    clipped_unique_slots = set()
    clipped_cells, max_cross_error = 0, 0.
    original_triangles, output_triangles = 0, 0
    duplicated_vertices, receiver_meshes = 0, 0
    ao_materials = set()
    per_mesh = []
    visibility_corners = []
    invariant_count = 0

    def add_view(data: bytes, target=None):
        binary.extend(b"\0" * ((-len(binary)) % 4))
        view = {"buffer": 0, "byteOffset": len(binary), "byteLength": len(data)}
        if target is not None:
            view["target"] = target
        binary.extend(data)
        document["bufferViews"].append(view)
        return len(document["bufferViews"]) - 1

    def add_accessor(array, template):
        accessor = copy.deepcopy(template)
        accessor.pop("sparse", None)
        accessor.pop("byteOffset", None)
        accessor["count"] = len(array)
        accessor["bufferView"] = add_view(np.ascontiguousarray(array).tobytes(), 34962)
        document["accessors"].append(accessor)
        return len(document["accessors"]) - 1

    for record in bake["meshes"]:
        mi, pi = record["mesh"], record["primitive"]
        original_primitive = original["meshes"][mi]["primitives"][pi]
        primitive = document["meshes"][mi]["primitives"][pi]
        assert original_primitive.get("mode", 4) == 4 and not original_primitive.get("targets")
        assert original_primitive["material"] == record["material"]
        ids = read_accessor(original, original_binary, original_primitive["indices"]).reshape(-1).astype(np.int64)
        assert len(ids) % 3 == 0
        tri_count = len(ids) // 3
        original_triangles += tri_count
        output_triangles += tri_count
        if not record["receiver"]:
            per_mesh.append({"name": record["name"], "triangles": tri_count, "receiver": False})
            continue
        receiver_meshes += 1
        receiver_triangles += tri_count
        ao_materials.add(record["material"])
        begin, count = record["floatOffset"], record["vertexCount"]
        assert begin + count <= len(values) and int(ids.max(initial=0)) < count
        visibility = values[begin:begin + count][ids].reshape(-1, 3)
        visibility_corners.append(visibility.reshape(-1))
        for name, accessor_index in original_primitive["attributes"].items():
            assert name != "TEXCOORD_1", "Source already has UV1; choose a new preparation stage"
            source_attribute = read_accessor(original, original_binary, accessor_index)
            duplicated = source_attribute[ids]
            assert np.array_equal(source_attribute[ids], duplicated), f"Changed {name} values"
            if name in ("POSITION", "NORMAL", "TEXCOORD_0", "COLOR_0"):
                invariant_count += 1
            primitive["attributes"][name] = add_accessor(duplicated, original["accessors"][accessor_index])
        primitive.pop("indices", None)
        duplicated_vertices += len(ids)

        # UV1 may relabel the three corners without changing triangle winding
        # or any original attribute. Putting median visibility at A guarantees
        # D=B+C-A lies between the low/high corner values, avoiding clipping.
        corner_order = (np.argsort(visibility, axis=1, kind="stable")[:, [1, 0, 2]]
                        if args.atlas_layout == "median" else np.tile(np.arange(3), (tri_count, 1)))
        a, b, c = np.take_along_axis(visibility, corner_order, axis=1).T
        raw_d = b + c - a
        d = np.clip(raw_d, 0, 1)
        clipped_cells += int(np.count_nonzero(raw_d != d))
        # With D=B+C-A, bilinear interpolation equals linear triangle AO.
        # Clipping D adds (clippedD-D)*s*t; s+t<=1 bounds s*t by1/4.
        max_cross_error = max(max_cross_error, float(np.max(np.abs(d - raw_d), initial=0)) * .25)
        fields = np.rint(np.stack((a, b, c, d), axis=1) * 255).astype(np.uint8)
        first_new_cell = len(cell_lookup)
        slots, unique_slots, unique_fields = assign_cell_slots(fields, cell_lookup, cells_per_row ** 2)
        cell = len(cell_lookup)
        clipped_unique_slots.update(slots[raw_d != d].tolist())
        x = (slots % cells_per_row) * 2
        y = (slots // cells_per_row) * 2
        unique_x = (unique_slots % cells_per_row) * 2
        unique_y = (unique_slots // cells_per_row) * 2
        for channel, (dx, dy) in enumerate(((0, 0), (1, 0), (0, 1), (1, 1))):
            atlas[unique_y + dy, unique_x + dx, :3] = unique_fields[:, channel, None]
        coords = np.empty((tri_count, 3, 2), dtype="<f4")
        coords[:, 0, :] = np.stack((x + .5, y + .5), axis=-1) / atlas_size
        coords[:, 1, :] = np.stack((x + 1.5, y + .5), axis=-1) / atlas_size
        coords[:, 2, :] = np.stack((x + .5, y + 1.5), axis=-1) / atlas_size
        uv = np.empty_like(coords)
        uv[np.arange(tri_count)[:, None], corner_order] = coords
        primitive["attributes"]["TEXCOORD_1"] = add_accessor(uv.reshape(-1, 2), {"componentType": 5126, "type": "VEC2"})
        per_mesh.append({"name": record["name"], "triangles": tri_count, "receiver": True,
                         "visibilityMin": float(visibility.min()), "visibilityMean": float(visibility.mean()),
                         "atlasTriangleReferences": tri_count,
                         "atlasUniqueCellsReferenced": len(unique_slots),
                         "atlasFirstNewCell": first_new_cell,
                         "atlasNewCellCount": cell - first_new_cell})

    png = io.BytesIO()
    Image.fromarray(atlas, "RGBA").save(png, format="PNG", optimize=True)
    png_bytes = png.getvalue()
    image_view = add_view(png_bytes)
    document.setdefault("images", []).append({"name": "safari.geometry_ambient_occlusion", "bufferView": image_view, "mimeType": "image/png"})
    document.setdefault("samplers", []).append({"magFilter": 9729, "minFilter": 9729, "wrapS": 33071, "wrapT": 33071})
    document.setdefault("textures", []).append({"name": "safari.geometry_ambient_occlusion", "source": len(document["images"]) - 1, "sampler": len(document["samplers"]) - 1})
    for mi in sorted(ao_materials):
        assert "occlusionTexture" not in document["materials"][mi], "Source already has authored AO"
        document["materials"][mi]["occlusionTexture"] = {"index": len(document["textures"]) - 1, "texCoord": 1, "strength": .5}
    document.setdefault("asset", {}).setdefault("extras", {})["safariOfflineAO"] = {
        "sourceSha256": source_hash, "samples": 16, "maxDistanceMetres": bake["maxDistanceMetres"],
        "originBiasMetres": bake["originBiasMetres"], "strength": .5, "atlasSize": atlas_size}
    write_glb(output, document, binary)

    # Re-read the actual delivery and compare every original triangle-corner
    # attribute value. This checks serialization, not just the in-memory arrays.
    output_raw, decoded, decoded_binary = load_glb(output)
    max_sampled_error, sampled_points = 0., 0
    ao_image = decoded["images"][-1]
    assert ao_image["name"] == "safari.geometry_ambient_occlusion"
    ao_view = decoded["bufferViews"][ao_image["bufferView"]]
    image_start = ao_view.get("byteOffset", 0)
    embedded_png = decoded_binary[image_start:image_start+ao_view["byteLength"]]
    assert embedded_png == png_bytes, "Serialized AO image changed"
    decoded_rgba = np.array(Image.open(io.BytesIO(embedded_png)).convert("RGBA"))
    decoded_atlas = decoded_rgba[:, :, 0] / 255.
    sample_weights = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1], [1/3, 1/3, 1/3],
                               [.2, .3, .5], [.5, .5, 0], [0, .5, .5]], dtype=float)
    for record in bake["meshes"]:
        mi, pi = record["mesh"], record["primitive"]
        before = original["meshes"][mi]["primitives"][pi]
        after = decoded["meshes"][mi]["primitives"][pi]
        ids = read_accessor(original, original_binary, before["indices"]).reshape(-1).astype(np.int64)
        for name, index in before["attributes"].items():
            expected = read_accessor(original, original_binary, index)
            actual = read_accessor(decoded, decoded_binary, after["attributes"][name])
            if record["receiver"]:
                expected = expected[ids]
            assert np.array_equal(expected, actual), f"Repacked {record['name']} changed {name}"
        if record["receiver"]:
            uv = read_accessor(decoded, decoded_binary, after["attributes"]["TEXCOORD_1"]).reshape(-1, 3, 2)
            begin, count = record["floatOffset"], record["vertexCount"]
            visibility = values[begin:begin + count][ids].reshape(-1, 3)
            # Check the complete serialized four-texel field, not only samples.
            # This proves cell reuse preserves the old quantized interpolation
            # everywhere, including between the finite sample points below.
            order = (np.argsort(visibility, axis=1, kind="stable")[:, [1, 0, 2]]
                     if args.atlas_layout == "median" else np.tile(np.arange(3), (len(visibility), 1)))
            a, b, c = np.take_along_axis(visibility, order, axis=1).T
            expected_fields = np.rint(np.stack((a, b, c, np.clip(b+c-a, 0, 1)), axis=1)*255).astype(np.uint8)
            origin = np.floor(uv.min(axis=1)*atlas_size).astype(np.int64)
            ox, oy = origin.T
            expected_uv = np.stack((origin+.5, origin+[1.5, .5], origin+[.5, 1.5]), axis=1)/atlas_size
            assert np.array_equal(np.take_along_axis(uv, order[:, :, None], axis=1), expected_uv), "AO corner permutation or cell-center UV changed"
            actual_fields = np.stack([decoded_rgba[oy+dy, ox+dx]
                for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1))], axis=1)
            assert np.array_equal(actual_fields[:, :, :3], np.repeat(expected_fields[:, :, None], 3, axis=2)), "Cell reuse changed a quantized triangle AO field"
            assert np.all(actual_fields[:, :, 3] == 255), "AO atlas alpha changed"
            for weights in sample_weights:
                coordinates = np.einsum("tvc,v->tc", uv, weights) * atlas_size - .5
                pixel = np.floor(coordinates).astype(int)
                fraction = coordinates - pixel
                x0, y0 = pixel.T
                x0 = np.clip(x0, 0, atlas_size - 1)
                y0 = np.clip(y0, 0, atlas_size - 1)
                x1, y1 = np.minimum(x0 + 1, atlas_size - 1), np.minimum(y0 + 1, atlas_size - 1)
                dx, dy = fraction.T
                sampled = ((decoded_atlas[y0, x0] * (1-dx) + decoded_atlas[y0, x1] * dx) * (1-dy)
                           + (decoded_atlas[y1, x0] * (1-dx) + decoded_atlas[y1, x1] * dx) * dy)
                expected = visibility @ weights
                max_sampled_error = max(max_sampled_error, float(np.max(np.abs(sampled - expected), initial=0)))
                sampled_points += len(sampled)
    assert max_sampled_error <= max_cross_error + .5 / 255 + 1e-6, "AO atlas interpolation exceeds stated bound"
    assert original_triangles == output_triangles
    assert sha(source.read_bytes()) == source_hash, "Source changed during preparation"
    with (output.parent / "loader-validation.log").open("w") as log:
        subprocess.run([str(args.helper.resolve()), "--validate", str(output)], stdout=log, stderr=subprocess.STDOUT, check=True)
    all_visibility = np.concatenate(visibility_corners)
    report = {
        "version": 1, "sourceSha256": source_hash, "candidateSha256": sha(output_raw),
        "sourceBytes": len(raw), "candidateBytes": len(output_raw), "meshCount": len(original["meshes"]),
        "originalTriangles": original_triangles, "candidateTriangles": output_triangles,
        "receiverMeshes": receiver_meshes, "duplicatedReceiverVertices": duplicated_vertices,
        "materialCount": len(document["materials"]), "aoMaterials": sorted(ao_materials),
        "atlas": {"width": atlas_size, "height": atlas_size, "rawRgbaBytes": atlas.nbytes,
                  "embeddedPngBytes": len(png_bytes), "usedCells": cell, "capacityCells": cells_per_row ** 2,
                  "triangleReferences": receiver_triangles,
                  "reusedTriangleCells": receiver_triangles - cell,
                  "cellReuse": "byte-identical quantized A/B/C/D fields; each triangle retains its corner permutation",
                  "minFilter": "LINEAR(9729), no mipmaps", "texCoord": 1,
                  "cornerAssignment": args.atlas_layout,
                  "clippedFourthPixelCells": len(clipped_unique_slots),
                  "clippedFourthPixelTriangles": clipped_cells, "maximumBilinearVisibilityErrorBound": max_cross_error,
                  "sampledCornerAndInteriorPoints": sampled_points,
                  "maximumMeasuredVisibilityInterpolationError": max_sampled_error,
                  "maximumAmbientFactorErrorBound": max_cross_error * .5 + .5 / 255 * .5},
        "visibility": {"min": float(all_visibility.min()), "mean": float(all_visibility.mean()),
                       "max": float(all_visibility.max()), "quantiles": np.quantile(all_visibility, [0, .1, .5, .9, 1]).tolist(),
                       "fractionBelow1": float(np.mean(all_visibility < 1)), "fractionBelowHalf": float(np.mean(all_visibility < .5))},
        "invariants": {"unchangedTriangleCount": True, "unchangedAllOriginalTriangleCornerAttributes": True,
                       "positionNormalUv0Color0MeshesVerified": invariant_count,
                       "originalSourceUnchanged": True, "noAlbedoDirectLightChanges": True,
                       "unchangedQuantizedTriangleAoFields": True,
                       "identityNodeTransforms": True},
        "bake": {k: v for k, v in bake.items() if k != "meshes"},
        "packSeconds": time.perf_counter() - started,
        "graphicsContext": False, "meshes": per_mesh,
    }
    (output.parent / "AO-RECEIPT.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    Image.fromarray(atlas, "RGBA").save(output.parent / "ao-atlas.png")
    print(json.dumps({k: report[k] for k in ("candidateSha256", "candidateBytes", "candidateTriangles", "receiverMeshes", "packSeconds")}))


if __name__ == "__main__":
    main()
