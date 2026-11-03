"""CPU triangle fit audit for the live Safari cockpit and serialized/generated body.

Run with the existing Hermes Python, using -B. By default, decode the actual
serialized GLB; --generator is an explicit alternative after source freeze.
The generator, if requested, is imported under an audit module name; save() is
never called. This script writes only its JSON report. It checks triangle
intersections and exact feature distances, not AABB clearances. Bounds only
prune pairs whose distance cannot be minimal.

Example:
  python -B scripts/audit-safari-cockpit.py --out build/safari-model/cockpit-fit.json
  python -B scripts/audit-safari-cockpit.py --self-test
"""
from __future__ import annotations

import argparse
import base64
import contextlib
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import struct
import sys
import time
from types import SimpleNamespace

import numpy as np

sys.dont_write_bytecode = True
EPS = 1e-28
CONTACT_TOLERANCE = 1e-8
REPO = Path(__file__).resolve().parents[1]


def triangles(vertices, faces):
    return np.asarray(vertices, dtype=np.float64)[np.asarray(faces, dtype=np.int64)]


def rotate_x(points, angle):
    c, s = np.cos(angle), np.sin(angle)
    return np.asarray(points) @ np.array([[1, 0, 0], [0, c, -s], [0, s, c]]).T


def cylinder_z(cx, cy, cz, radius=.091, height=.05, segments=24):
    """Closed CylinderGeometry, 24 segments, rotated onto its Z axis.

    Duplicate seam/cap vertices do not change the triangles and are merged in
    this representation. Circumferential sample phase matches the native mesh.
    """
    p, f = [], []
    for z in (cz - height / 2, cz + height / 2):
        for a in np.arange(segments) * (2 * np.pi / segments):
            p.append((cx + radius * np.sin(a), cy + radius * np.cos(a), z))
    p.extend(((cx, cy, cz - height / 2), (cx, cy, cz + height / 2)))
    for i in range(segments):
        j = (i + 1) % segments
        f.extend(((i, j, segments + i), (j, segments + j, segments + i),
                  (2 * segments, j, i), (2 * segments + 1, segments + i, segments + j)))
    return triangles(p, f)


def torus(cx, cy, cz, radius, tube, radial_segments=6, tubular_segments=24, tilt_x=0):
    """The native TorusGeometry angular samples and face diagonals."""
    p, f = [], []
    for j in range(radial_segments):
        v = j * 2 * np.pi / radial_segments
        for i in range(tubular_segments):
            u = i * 2 * np.pi / tubular_segments
            p.append(((radius + tube * np.cos(v)) * np.cos(u),
                      (radius + tube * np.cos(v)) * np.sin(u), tube * np.sin(v)))
    p = rotate_x(p, tilt_x) + (cx, cy, cz)
    for j in range(radial_segments):
        for i in range(tubular_segments):
            a = j * tubular_segments + i
            b = j * tubular_segments + (i + 1) % tubular_segments
            c = ((j + 1) % radial_segments) * tubular_segments + i
            d = ((j + 1) % radial_segments) * tubular_segments + (i + 1) % tubular_segments
            # Native TorusGeometry joins a-d, not the alternative b-c diagonal.
            # Its non-planar quads make this relevant for exact closest points.
            f.extend(((c, a, d), (a, b, d)))
    return triangles(p, f)


def box(lo, hi):
    """BoxGeometry's six two-triangle planes, without duplicate vertices."""
    p = np.array([[x, y, z] for x in (lo[0], hi[0])
                  for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    f = []
    for axis in range(3):
        for value in (lo[axis], hi[axis]):
            a, b, c, d = np.flatnonzero(p[:, axis] == value)
            f.extend(((a, b, c), (b, d, c)))
    return triangles(p, f)


def disc(cx, cy, cz, radius=.085, segments=24):
    p = [(cx, cy, cz)]
    p.extend((cx + radius * np.cos(a), cy + radius * np.sin(a), cz)
             for a in np.arange(segments) * 2 * np.pi / segments)
    return triangles(p, [(0, i + 1, (i + 1) % segments + 1) for i in range(segments)])


def dot(a, b):
    return np.einsum('ij,ij->i', a, b)


def point_segment(p, a, b):
    d = b - a
    t = np.clip(dot(p - a, d) / np.maximum(dot(d, d), EPS), 0, 1)
    q = a + d * t[:, None]
    return dot(p - q, p - q), q


def point_triangle(p, tri):
    a, b, c = tri[:, 0], tri[:, 1], tri[:, 2]
    u, v = b - a, c - a
    n = np.cross(u, v)
    nn = dot(n, n)
    signed = dot(p - a, n)
    projected = p - n * (signed / np.maximum(nn, EPS))[:, None]
    w = projected - a
    uu, uv, vv, wu, wv = dot(u, u), dot(u, v), dot(v, v), dot(w, u), dot(w, v)
    denominator = uu * vv - uv * uv
    beta = (wu * vv - wv * uv) / np.maximum(denominator, EPS)
    gamma = (wv * uu - wu * uv) / np.maximum(denominator, EPS)
    inside = (beta >= 0) & (gamma >= 0) & (beta + gamma <= 1) & (nn > EPS)
    distances, points = [], []
    for x, y in ((a, b), (b, c), (c, a)):
        d, q = point_segment(p, x, y)
        distances.append(d)
        points.append(q)
    distances = np.stack(distances, axis=1)
    best = np.argmin(distances, axis=1)
    rows = np.arange(len(p))
    q = np.stack(points, axis=1)[rows, best]
    q[inside] = projected[inside]
    return dot(p - q, p - q), q


def segment_segment(p, q, r, s):
    u, v, w = q - p, s - r, p - r
    a, e, b, c, f = dot(u, u), dot(v, v), dot(u, v), dot(u, w), dot(v, w)
    denominator = a * e - b * b
    ss = np.where(denominator > EPS,
                  np.clip((b * f - c * e) / np.maximum(denominator, EPS), 0, 1), 0)
    tt = (b * ss + f) / np.maximum(e, EPS)
    ss = np.where(tt < 0, np.clip(-c / np.maximum(a, EPS), 0, 1),
                  np.where(tt > 1, np.clip((b - c) / np.maximum(a, EPS), 0, 1), ss))
    tt = np.clip(tt, 0, 1)
    ss = np.where(a <= EPS, 0, ss)
    tt = np.where(a <= EPS, np.clip(f / np.maximum(e, EPS), 0, 1), tt)
    tt = np.where(e <= EPS, 0, tt)
    ss = np.where(e <= EPS, np.clip(-c / np.maximum(a, EPS), 0, 1), ss)
    pa, pb = p + ss[:, None] * u, r + tt[:, None] * v
    return dot(pa - pb, pa - pb), pa, pb


def segment_triangle(p, q, tri):
    direction = q - p
    e1, e2 = tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]
    h = np.cross(direction, e2)
    determinant = dot(e1, h)
    valid = np.abs(determinant) > 1e-14
    inverse = np.where(valid, 1 / np.where(valid, determinant, 1), 0)
    ss = p - tri[:, 0]
    u = dot(ss, h) * inverse
    qq = np.cross(ss, e1)
    v, t = dot(direction, qq) * inverse, dot(e2, qq) * inverse
    valid &= (u >= -1e-10) & (v >= -1e-10) & (u + v <= 1 + 1e-10)
    valid &= (t >= -1e-10) & (t <= 1 + 1e-10)
    return valid, p + direction * t[:, None]


def triangle_pair_distances(a, b):
    """Every closest feature: vertex/face, edge/edge, and edge/face crossing."""
    distance = np.full(len(a), np.inf)
    pa, pb = np.empty((len(a), 3)), np.empty((len(a), 3))

    def keep(d, p, q):
        update = d < distance
        distance[update], pa[update], pb[update] = d[update], p[update], q[update]

    for i in range(3):
        d, q = point_triangle(a[:, i], b)
        keep(d, a[:, i], q)
        d, q = point_triangle(b[:, i], a)
        keep(d, q, b[:, i])
    for i in range(3):
        for j in range(3):
            keep(*segment_segment(a[:, i], a[:, (i + 1) % 3], b[:, j], b[:, (j + 1) % 3]))
    for i in range(3):
        hit, p = segment_triangle(a[:, i], a[:, (i + 1) % 3], b)
        keep(np.where(hit, 0, np.inf), p, p)
        hit, p = segment_triangle(b[:, i], b[:, (i + 1) % 3], a)
        keep(np.where(hit, 0, np.inf), p, p)
    return distance, pa, pb


def aabb_distances(amin, amax, bmin, bmax):
    gap = np.maximum(np.maximum(bmin[None] - amax[:, None], amin[:, None] - bmax[None]), 0)
    return np.einsum('ijk,ijk->ij', gap, gap)


def closest_meshes(a, b, b_names=None):
    """Globally closest triangles, with exact feature witnesses and crossings."""
    if not len(a) or not len(b):
        raise ValueError('Cannot audit an empty triangle mesh')
    amin, amax, bmin, bmax = a.min(1), a.max(1), b.min(1), b.max(1)
    lower_best, initial = np.inf, None
    for start in range(0, len(a), 64):
        lower = aabb_distances(amin[start:start + 64], amax[start:start + 64], bmin, bmax)
        i, j = np.unravel_index(np.argmin(lower), lower.shape)
        if lower[i, j] < lower_best:
            lower_best, initial = lower[i, j], (start + i, j)
    d, pa, pb = triangle_pair_distances(a[[initial[0]]], b[[initial[1]]])
    best, witness_a, witness_b = float(d[0]), pa[0], pb[0]
    best_ids = initial
    contacts, exact_pairs = 0, 0
    for start in range(0, len(a), 64):
        lower = aabb_distances(amin[start:start + 64], amax[start:start + 64], bmin, bmax)
        ia, ib = np.nonzero(lower <= best + CONTACT_TOLERANCE ** 2)
        ia += start
        for k in range(0, len(ia), 10000):
            ai, bi = ia[k:k + 10000], ib[k:k + 10000]
            d, pa, pb = triangle_pair_distances(a[ai], b[bi])
            exact_pairs += len(d)
            contacts += int(np.count_nonzero(d <= CONTACT_TOLERANCE ** 2))
            j = np.argmin(d)
            if d[j] < best:
                best, witness_a, witness_b = float(d[j]), pa[j], pb[j]
                best_ids = (int(ai[j]), int(bi[j]))
    result = {'minimumClearanceMetres': float(np.sqrt(max(best, 0))),
              'contactOrIntersection': bool(best <= CONTACT_TOLERANCE ** 2),
              'contactTrianglePairs': contacts, 'exactTrianglePairsTested': exact_pairs,
              'cockpitPoint': witness_a.tolist(), 'surfacePoint': witness_b.tolist(),
              'cockpitTriangle': int(best_ids[0]), 'surfaceTriangle': int(best_ids[1])}
    if b_names is not None:
        result['nearestSurfacePart'] = str(b_names[best_ids[1]])
    return result


def cockpit_parts(vertical_offset, gauge_z_offset):
    """Explicit RallyCockpit.hpp parameters, source hash recorded in report.

    Cylinder cap duplication and transform-equivalent torus winding do not
    affect fit. Housing, face and rim are separate checks, so the supporting
    dash overlap is not incorrectly reported as a body collision.
    """
    parts = {}
    for label, x in (('left', -.51), ('right', -.29)):
        y, z = 1.44 + vertical_offset, .438 + gauge_z_offset
        parts[label + '_gauge_housing'] = cylinder_z(x, y, z + .03)
        parts[label + '_gauge_face'] = disc(x, y, z)
        parts[label + '_gauge_rim'] = torus(x, y, z, .087, .006, 6, 48)
        # The C++ finish validator binds every added dial detail to this
        # principal envelope. Circumscribe the polygon, so its interior also
        # covers marks at arbitrary angles rather than only sampled vertices.
        parts[label + '_finished_detail_envelope'] = cylinder_z(
            x, y, z + .0235, .093001 / np.cos(np.pi / 48), .063002, 48)
    parts['dash_box'] = box((-.65, 1.27 + vertical_offset, .45),
                            (.65, 1.41 + vertical_offset, .63))
    parts['dash_finished_face_relief_envelope'] = box(
        (-.650001, 1.269999 + vertical_offset, .447999),
        (.650001, 1.410001 + vertical_offset, .450001))
    parts['steering_rim'] = torus(-.4, 1.28 + vertical_offset, .25,
                                  .185, .018, 12, 48, .28)
    wheel = cylinder_z(0, 0, 0, .203001 / np.cos(np.pi / 48), .050002, 48)
    parts['steering_finished_detail_envelope'] = rotate_x(wheel, .28) + \
        np.array([-.4, 1.28 + vertical_offset, .25])
    return parts


def convex_containment(envelope, surfaces):
    """Reject surface vertices contained by a closed convex fit volume.

    Boundary-crossing checks alone miss an entire triangle inside the volume.
    Combined with those checks, this classifies every way a triangle can enter
    a convex envelope. Bbox pruning keeps the plane query small.
    """
    e = np.asarray(envelope, float)
    center = e.mean(axis=(0, 1))
    normal = np.cross(e[:, 1] - e[:, 0], e[:, 2] - e[:, 0])
    normal /= np.linalg.norm(normal, axis=1)[:, None]
    normal[np.einsum('ij,ij->i', normal, center - e[:, 0]) > 0] *= -1
    planes = np.unique(np.round(np.c_[normal, -np.einsum('ij,ij->i', normal, e[:, 0])], 12), axis=0)
    low, high = e.min(axis=(0, 1)), e.max(axis=(0, 1))
    points = np.asarray(surfaces, float).reshape(-1, 3)
    ids = np.flatnonzero(np.all((points >= low-CONTACT_TOLERANCE) &
                               (points <= high+CONTACT_TOLERANCE), axis=1))
    hits = []
    for start in range(0, len(ids), 1024):
        batch = ids[start:start+1024]
        inside = np.all(points[batch] @ planes[:, :3].T + planes[:, 3] <= CONTACT_TOLERANCE, axis=1)
        hits.extend(batch[inside].tolist())
    return {'containedOrBoundaryCorners': len(hits),
            'firstContainedCorner': points[hits[0]].tolist() if hits else None,
            'convexPlanes': len(planes)}


def source_hashes(repo, asset, generator=None):
    paths = {asset, Path(__file__).resolve(), repo / 'showcase/RallyCockpit.hpp',
             repo / 'showcase/RallySafari.hpp',
             repo / 'showcase/RallySafariCockpitFinish.hpp',
             repo / 'showcase/RallySafariInterior.hpp'}
    if generator is not None:
        paths.update(generator.parent.glob('safari_*.py'))
        paths.update(generator.parent.glob('safari_*.json'))
    return {str(p.relative_to(repo)) if p.is_relative_to(repo) else str(p):
            hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths) if p.is_file()}


def import_body(generator, repo):
    sys.path.insert(0, str(repo / 'scripts'))
    sys.path.insert(0, str(generator.parent))
    spec = importlib.util.spec_from_file_location('safari_cockpit_fit_readonly', generator)
    module = importlib.util.module_from_spec(spec)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        spec.loader.exec_module(module)
    return module, log.getvalue()


def import_glb(path):
    """Decode mesh positions/indices and scene node transforms using NumPy.

    No image decoding, loader cache, authored source import or GLB writes.
    Byte-strided accessors and nested matrix/TRS transforms are supported.
    """
    encoded = path.read_bytes()
    magic, version, length = struct.unpack_from('<III', encoded)
    if magic != 0x46546C67 or version != 2 or length != len(encoded):
        raise ValueError('Expected an intact glTF2 binary asset')
    document, bin_chunks, offset = None, [], 12
    while offset < len(encoded):
        size, kind = struct.unpack_from('<II', encoded, offset)
        data = encoded[offset + 8:offset + 8 + size]
        if kind == 0x4E4F534A:
            document = json.loads(data)
        elif kind == 0x004E4942:
            bin_chunks.append(data)
        offset += 8 + size
    if document is None:
        raise ValueError('GLB has no JSON document')
    buffers, next_bin = [], 0
    for item in document['buffers']:
        uri = item.get('uri')
        if uri is None:
            buffers.append(bin_chunks[next_bin])
            next_bin += 1
        elif uri.startswith('data:'):
            buffers.append(base64.b64decode(uri.split(',', 1)[1]))
        else:
            buffers.append((path.parent / uri).read_bytes())
    types = {5120: '<i1', 5121: '<u1', 5122: '<i2', 5123: '<u2', 5125: '<u4', 5126: '<f4'}
    widths = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}

    def accessor(index):
        item = document['accessors'][index]
        if 'sparse' in item:
            raise ValueError('Sparse geometry accessor requires explicit audit support')
        view = document['bufferViews'][item['bufferView']]
        dtype = np.dtype(types[item['componentType']])
        count, width = item['count'], widths[item['type']]
        begin = view.get('byteOffset', 0) + item.get('byteOffset', 0)
        stride = view.get('byteStride', dtype.itemsize * width)
        data = buffers[view['buffer']]
        if begin + max(count - 1, 0) * stride + width * dtype.itemsize > len(data):
            raise ValueError('Accessor extends outside its buffer')
        return np.ndarray((count, width), dtype=dtype, buffer=data, offset=begin,
                          strides=(stride, dtype.itemsize)).copy()

    def local_matrix(node):
        if 'matrix' in node:
            return np.asarray(node['matrix'], float).reshape((4, 4), order='F')
        x, y, z, w = node.get('rotation', (0, 0, 0, 1))
        rotation = np.array([[1 - 2 * (y*y + z*z), 2 * (x*y - z*w), 2 * (x*z + y*w)],
                             [2 * (x*y + z*w), 1 - 2 * (x*x + z*z), 2 * (y*z - x*w)],
                             [2 * (x*z - y*w), 2 * (y*z + x*w), 1 - 2 * (x*x + y*y)]])
        m = np.eye(4)
        m[:3, :3] = rotation @ np.diag(node.get('scale', (1, 1, 1)))
        m[:3, 3] = node.get('translation', (0, 0, 0))
        return m

    parts = []

    def visit(index, parent):
        node = document['nodes'][index]
        transform = parent @ local_matrix(node)
        if 'mesh' in node:
            m = document['meshes'][node['mesh']]
            for primitive_index, primitive in enumerate(m['primitives']):
                if primitive.get('mode', 4) != 4:
                    raise ValueError('Non-triangle GLB primitive requires explicit support')
                p = accessor(primitive['attributes']['POSITION']).astype(np.float64)
                p = p @ transform[:3, :3].T + transform[:3, 3]
                f = (accessor(primitive['indices']).reshape(-1) if 'indices' in primitive
                     else np.arange(len(p))).astype(np.int64).reshape(-1, 3)
                name = m.get('name', node.get('name', 'mesh_' + str(node['mesh'])))
                if len(m['primitives']) > 1:
                    name += '.primitive_' + str(primitive_index)
                parts.append({'name': name, 'originalNames': m.get('extras', {}).get('originalParts', []),
                              'p': p, 'f': f, 'mat': primitive.get('material', -1)})
        for child in node.get('children', []):
            visit(child, transform)

    scene = document['scenes'][document.get('scene', 0)]
    for node in scene['nodes']:
        visit(node, np.eye(4))
    glass_ids = [i for i, material in enumerate(document.get('materials', []))
                 if material.get('name') == 'safari.smoky_glazing']
    if len(glass_ids) != 1:
        raise ValueError('Expected exactly one named Safari windshield material')
    return SimpleNamespace(M=SimpleNamespace(parts=parts), glass=glass_ids[0]), ''


def verify_cockpit_source(path):
    """Fail visibly if the audited native geometry or its transforms drift.

    The readable declarations explain the mirrored primitive assumptions. A
    whitespace-independent fingerprint of the complete builder also rejects
    added transforms/parenting changes that a list of declarations can miss.
    Revalidate the native geometry before updating this fingerprint.
    """
    source = ''.join(path.read_text().split())
    declarations = [
        'BoxGeometry::create(1.30f,.14f,.18f)', 'dash->position.set(0,1.34f,.54f)',
        'column->position.set(-.4f,1.28f,.25f)', 'column->rotation.x=.28f',
        'TorusGeometry::create(.185f,.018f,8,32)',
        'root->position.set(x,1.44f,.438f+gaugeDepthOffset)',
        'CylinderGeometry::create(.091f,.091f,.05f,24)', 'housing->position.z=-.03f',
        'CircleGeometry::create(.085f,24)', 'TorusGeometry::create(.087f,.006f,6,24)',
        'gauge(-.51f)', 'gauge(-.29f)',
        'cockpitRoot->position.y=verticalOffset', 'body.add(cockpitRoot)',
        'root->rotation.y=pi', 'housing->rotation.x=pi/2',
        'cockpitRoot->add(root)', 'root->add(housing)',
        'root->add(face)', 'root->add(rim)', 'column->add(c.steering)',
    ]
    missing = [item for item in declarations if item not in source]
    if missing:
        raise ValueError('RallyCockpit primitive contract changed; update audit: ' + repr(missing))
    start = source.index('inlineCockpitaddCockpit(')
    end = source.index('inlinevoidupdateCockpit(')
    if hashlib.sha256(source[start:end].encode()).hexdigest() != \
            '28a2c3e1ecaad936b5a59dfeedaa9429c3b4cb868df4a24a3162b7e47c2c7168':
        raise ValueError('Native cockpit builder changed; revalidate geometry/transforms before updating the audit fingerprint')


def header_fingerprint(path):
    # Git's Windows checkout may use CRLF. Normalize only line endings, while
    # retaining every source character, so that checkout policy cannot break
    # a reviewed geometry recipe or hide a semantic helper edit.
    return hashlib.sha256(path.read_text(encoding='utf-8').encode('utf-8')).hexdigest()


def verify_safari_placement(path, vertical, depth):
    """Bind the placement and untransformed asset to the reviewed integration."""
    source = ''.join(path.read_text().split())
    placement = re.search(r'addCockpit\(\*b\.body,([-.\d]+)f,([-.\d]+)f\)', source)
    if placement is None or not np.allclose([float(v) for v in placement.groups()],
                                            [vertical, depth], rtol=0, atol=1e-8):
        raise ValueError('Safari cockpit placement differs from audit parameters; review the integration')
    start = source.index('inlineBuggymakeSafari(')
    end = source.index('returnb;}', start) + len('returnb;}')
    if hashlib.sha256(source[start:end].encode()).hexdigest() != \
            'a3d95353081d949f709969ea3c474c474459b4e812bcd8c00b6fb61a925ccf07':
        raise ValueError('Safari integration changed; revalidate asset/parent transforms before updating the audit fingerprint')
    # This reviewed decorator preserves housing/face transforms, refines rim
    # samples, and validates all added details against the principal envelopes
    # above in RallyVehicle_test before asset preparation. Do not accept a
    # changed decorator merely because addCockpit itself remains unchanged.
    finish = path.parent / 'RallySafariCockpitFinish.hpp'
    if header_fingerprint(finish) != \
            '87d08812bba19b01aa4e79d60734b9819992a1a5bae8fcd7664da1ef78336819':
        raise ValueError('Safari cockpit finish changed; revalidate native geometry and its enclosing fit volumes')
    # Also bind helpers outside makeSafari and the cabin helper receiving its
    # body by reference. A builder-only fingerprint missed helper mutations.
    for name, expected in {
        'RallySafari.hpp': 'b48f67d2100dbb9d469be8c597d90a3876d84d1490949cdcdfb1e125d4d893f3',
        'RallySafariInterior.hpp': '328f1812f8f0eee67735c2dee9fb1a29de6984dd0337e733d300001e9594f87a',
    }.items():
        if header_fingerprint(path.parent / name) != expected:
            raise ValueError('Safari placement/helper source changed; revalidate construction: ' + name)


def surface_groups(module):
    groups = {'front_windscreen_glass': [], 'primary_bonnet': [], 'front_surround': [], 'cabin_lining': []}
    glass_id = getattr(module, 'glass', None)
    for part in module.M.parts:
        name = part['name']
        names = [name] + part.get('originalNames', [])
        front_screen = any(n == 'cabin.front_windscreen' or
                           n.startswith(('cabin.front_windscreen.', 'cabin.front_screen.')) for n in names)
        if front_screen and part['mat'] == glass_id:
            groups['front_windscreen_glass'].append(part)
        elif front_screen or any(n.startswith('cabin.front_window_gasket') for n in names):
            groups['front_surround'].append(part)
        if any(n.startswith('interior.cabin_lining.') for n in names):
            groups['cabin_lining'].append(part)
        if any(n.startswith('body.continuous_bonnet_shoulders_rear_deck.') for n in names):
            groups['primary_bonnet'].append(part)
    missing = [name for name, parts in groups.items() if not parts]
    if missing:
        raise ValueError('Required body surfaces missing; review explicit selectors: ' + repr(missing))
    result = {}
    for group, parts in groups.items():
        if parts:
            result[group] = (np.concatenate([triangles(p['p'], p['f']) for p in parts]),
                             np.concatenate([np.repeat(p['name'], len(p['f'])) for p in parts]))
    return result


def self_test():
    a = np.array([[[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]]])
    cases = [(a + (0, 0, 2), 2.),
             (np.array([[[.25, .25, -1], [.25, .25, 1], [.8, .25, 0]]]), 0.),
             (a + (.1, .1, 0), 0.)]
    for b, expected in cases:
        r = closest_meshes(a, b)
        assert abs(r['minimumClearanceMetres'] - expected) < 1e-10, r
        assert abs(np.linalg.norm(np.array(r['cockpitPoint']) - r['surfacePoint']) - expected) < 1e-10
    parts = cockpit_parts(-.25, -.025)
    assert {k: len(v) for k, v in parts.items()} == {
        'left_gauge_housing': 96, 'left_gauge_face': 24, 'left_gauge_rim': 576,
        'left_finished_detail_envelope': 192,
        'right_gauge_housing': 96, 'right_gauge_face': 24, 'right_gauge_rim': 576,
        'right_finished_detail_envelope': 192,
        'dash_box': 12, 'dash_finished_face_relief_envelope': 12,
        'steering_rim': 1152, 'steering_finished_detail_envelope': 192}
    inside = np.array([[[-.51, 1.19, .43], [-.509, 1.19, .43], [-.51, 1.191, .43]]])
    volume = parts['left_finished_detail_envelope']
    assert not closest_meshes(inside, volume)['contactOrIntersection']
    assert convex_containment(volume, inside)['containedOrBoundaryCorners'] == 3
    assert convex_containment(volume, inside + (0, 0, 1))['containedOrBoundaryCorners'] == 0
    return {'analyticDistanceAndCrossingCases': len(cases), 'primitiveTopologyCounts': 'passed'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group()
    inputs.add_argument('--glb', type=Path, help='Actual serialized GLB (default: showcase/assets/safari-body.glb)')
    inputs.add_argument('--generator', type=Path, help='Explicit source import alternative, after source freeze')
    parser.add_argument('--vertical-offset', type=float, default=-.25)
    parser.add_argument('--gauge-z-offset', type=float, default=-.025)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    checks = self_test()
    if args.self_test:
        print(json.dumps(checks, indent=2))
        return 0
    generator = args.generator.resolve() if args.generator else None
    asset = generator if generator else (args.glb or REPO / 'showcase/assets/safari-body.glb').resolve()
    verify_cockpit_source(REPO / 'showcase/RallyCockpit.hpp')
    verify_safari_placement(REPO / 'showcase/RallySafari.hpp',
                            args.vertical_offset, args.gauge_z_offset)
    hashes_before = source_hashes(REPO, asset, generator)
    started = time.monotonic()
    body, import_log = import_body(generator, REPO) if generator else import_glb(asset)
    groups = surface_groups(body)
    all_surface = np.concatenate([triangles(p['p'], p['f']) for p in body.M.parts])
    all_names = np.concatenate([np.repeat(p['name'], len(p['f'])) for p in body.M.parts])
    parts = cockpit_parts(args.vertical_offset, args.gauge_z_offset)
    report = {'createdUtc': datetime.now(timezone.utc).isoformat(),
              'evidence': 'CPU serialized/source triangle fit, not native visual acceptance',
              'inputMode': 'generator' if generator else 'serializedGLB',
              'inputPath': str(asset), 'generatorSaveCalled': False,
              'parameters': {'verticalOffset': args.vertical_offset, 'gaugeZOffset': args.gauge_z_offset,
                             'eyeBodyMetres': [-.4, 1.43, -.3]},
              'algorithm': 'segment/triangle crossings plus vertex/face and edge/edge closest features; AABB lower-bound pruning',
              'contactToleranceMetres': CONTACT_TOLERANCE,
              'finishedDetailScope': 'Exact housing/face/dash and refined rim triangles; added marks, spokes, fixings and face relief are conservatively enclosed by source-bound C++ validated principal volumes, not mirrored as exact detail triangles',
              'selfTests': checks, 'sourceHashes': hashes_before,
              'triangleCounts': {'cockpit': {k: len(v) for k, v in parts.items()},
                                 'surfaces': {k: len(v[0]) for k, v in groups.items()}},
              'surfaceParts': {k: sorted(set(v[1])) for k, v in groups.items()},
              'results': {}}
    if import_log:
        report['generatorImportLog'] = import_log
    for name, component in parts.items():
        report['results'][name] = {group: closest_meshes(component, surface, names)
                                   for group, (surface, names) in groups.items()}
    report['finishedEnvelopeContainment'] = {}
    for name, component in parts.items():
        if name.endswith('_envelope'):
            report['results'][name]['all_body_surfaces'] = closest_meshes(component, all_surface, all_names)
            report['finishedEnvelopeContainment'][name] = convex_containment(component, all_surface)
    hashes_after = source_hashes(REPO, asset, generator)
    report['sourceHashesUnchanged'] = hashes_before == hashes_after
    report['passed'] = report['sourceHashesUnchanged'] and not any(
        result['contactOrIntersection'] for component in report['results'].values()
        for result in component.values()) and not any(
        r['containedOrBoundaryCorners'] for r in report['finishedEnvelopeContainment'].values())
    if hashes_before != hashes_after:
        report['sourceHashesAfter'] = hashes_after
        report['invalidReason'] = 'Source changed during audit; rerun after source freeze'
    report['elapsedSeconds'] = time.monotonic() - started
    out = args.out or REPO / ('build/safari-model/cockpit-fit-' +
                              datetime.now().strftime('%Y%m%d-%H%M%S') + '.json')
    out = out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'report': str(out), **report}, indent=2))
    return 0 if report['passed'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
