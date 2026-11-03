"""Read-only CPU source audit. Does not import the full body or export assets.

Centreline/capsule distances are conservative pipe envelopes. Actual generated
stations query authored solid triangles; the separately reported silencer
check uses actual authored case triangles. These are geometry checks,
not automotive certification or a full swept/dynamic collision proof.
"""
import argparse
import ast
import hashlib
import json
import math
import heapq
import re
import sys
import time
from pathlib import Path

import numpy as np
from scipy.spatial import ConvexHull

ROOT = next(path for path in Path(__file__).resolve().parents
            if (path/'scripts/generate-safari-body.py').is_file())
parser = argparse.ArgumentParser()
parser.add_argument('--out', type=Path)
parser.add_argument('--source', type=Path, default=ROOT/'scripts/safari_rear_assembly.py')
parser.add_argument('--quick-tubes', action='store_true', help='Diagnostic subset, never a full pass.')
parser.add_argument('--fixtures-only', action='store_true')
args = parser.parse_args()

generator = ROOT/'scripts/generate-safari-body.py'
rear = args.source.resolve()
rear_bytes = rear.read_bytes()
generator_bytes = generator.read_bytes()
audit_bytes = Path(__file__).read_bytes()
started = time.monotonic()
required = {'basis', 'cylinder', 'ellipsoid', 'box', 'torus', 'polyline', 'plate'}
tree = ast.parse(generator_bytes.decode())
definitions = [node for node in tree.body if
               isinstance(node, ast.FunctionDef) and node.name in required or
               isinstance(node, ast.ClassDef) and node.name == 'Model']
ns = dict(np=np, math=math, TAU=math.tau)
exec(compile(ast.Module(body=definitions, type_ignores=[]), str(generator), 'exec'), ns)
model = ns['Model']()
ns['M'] = model
line_records, pipe_records = [], []
primitives = {}
for name in required:
    original = ns[name]
    if name == 'cylinder':
        def cylinder(name, a, b, radius, material, *tail, _fn=original, **kw):
            line_records.append(dict(name=name, points=np.asarray([a, b], float), radius=radius))
            return _fn(name, a, b, radius, material, *tail, **kw)
        primitives[name] = cylinder
    elif name == 'polyline':
        def polyline(name, points, radius, material, *tail, _fn=original, **kw):
            line_records.append(dict(name=name, points=np.asarray(points, float), radius=radius))
            return _fn(name, points, radius, material, *tail, **kw)
        primitives[name] = polyline
    else:
        primitives[name] = original

tree = ast.parse(rear_bytes.decode())
found = False
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == 'pipe':
        statement = next(i for i, statement in enumerate(node.body)
                         if isinstance(statement, ast.Assign)
                         and any(isinstance(target, ast.Name) and target.id == 'points'
                                 for target in statement.targets))
        node.body.insert(statement+1, ast.parse(
            '_pipe_records.append(dict(name=name, control=np.asarray(control,float), points=points.copy(), outer=outer))'
        ).body[0])
        found = True
assert found, 'Pipe authoring API changed; review the audit before using it.'
rns = dict(_pipe_records=pipe_records)
exec(compile(ast.fix_missing_locations(tree), str(rear), 'exec'), rns)
metadata = rns['build_rear_assembly'](model, primitives,
    {key: 0 for key in ['frame', 'alloy', 'steel', 'cast', 'rubber', 'soot', 'weld']})

# Reproduce the actual generator's fixed cabin bulkhead without importing
# unrelated body authoring. This protects engine/pipe packaging as well as
# the rear module's internal fit, while root still runs full vehicle tests.
generator_tree = ast.parse(generator_bytes.decode())
bulkhead_call = next(node for node in ast.walk(generator_tree)
                     if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                     and node.func.id == 'box' and node.args
                     and isinstance(node.args[0], ast.Constant)
                     and node.args[0].value == 'interior.rear_bulkhead')
first_bulkhead = len(model.parts)
ns['box']('interior.rear_bulkhead', ast.literal_eval(bulkhead_call.args[1]),
          ast.literal_eval(bulkhead_call.args[2]), 0,
          ast.literal_eval(bulkhead_call.args[4]))
bulkhead_parts = model.parts[first_bulkhead:]



def segment_pair(a, b, c, d):
    """Exact closest positions for two finite segments, including endpoints."""
    v, w, r = b-a, d-c, a-c
    aa, ee, ff = float(v@v), float(w@w), float(w@r)
    if aa <= 1e-20 and ee <= 1e-20:
        s = t = 0.0
    elif aa <= 1e-20:
        s, t = 0.0, np.clip(ff/ee, 0, 1)
    else:
        cc = float(v@r)
        if ee <= 1e-20:
            t, s = 0.0, np.clip(-cc/aa, 0, 1)
        else:
            bb = float(v@w)
            denominator = aa*ee-bb*bb
            s = np.clip((bb*ff-cc*ee)/denominator, 0, 1) if denominator > 1e-20 else 0.0
            t = (bb*s+ff)/ee
            if t < 0:
                t, s = 0.0, np.clip(-cc/aa, 0, 1)
            elif t > 1:
                t, s = 1.0, np.clip((bb-cc)/aa, 0, 1)
    p, q = a+v*s, c+w*t
    return float(np.linalg.norm(p-q)), p, q

def closest_polylines(first, second):
    return min((segment_pair(a, b, c, d)
                for a, b in zip(first[:-1], first[1:])
                for c, d in zip(second[:-1], second[1:])), key=lambda result: result[0])

def closest_triangle(points, triangle):
    """Vector point/triangle closest positions, including all edge regions."""
    a, b, c = triangle
    ab, ac = b-a, c-a
    n = np.cross(ab, ac)
    n2 = float(n@n)
    if n2 < 1e-20:
        return None
    p = points-((points-a)@n/n2)[:, None]*n
    v0, v1, v2 = ab, ac, p-a
    d00, d01, d11 = v0@v0, v0@v1, v1@v1
    d20, d21 = v2@v0, v2@v1
    denominator = d00*d11-d01*d01
    u = (d11*d20-d01*d21)/denominator
    v = (d00*d21-d01*d20)/denominator
    inside = (u >= 0) & (v >= 0) & (u+v <= 1)
    candidates = [p]
    for x, y in [(a, b), (b, c), (c, a)]:
        edge = y-x
        t = np.clip((points-x)@edge/(edge@edge), 0, 1)
        candidates.append(x+t[:, None]*edge)
    ds = np.stack([np.sum((points-q)**2, axis=1) for q in candidates])
    ds[0, ~inside] = np.inf
    choices = ds.argmin(0)
    index = ds[choices, np.arange(len(points))].argmin()
    return float(np.sqrt(ds[choices[index], index])), points[index], candidates[choices[index]][index]


def segment_triangle(a, b, triangle):
    p, q, r = triangle
    direction, e1, e2 = b-a, q-p, r-p
    h = np.cross(direction, e2)
    determinant = float(e1@h)
    if abs(determinant) > 1e-14:
        inverse = 1/determinant
        v = a-p
        u = float(v@h)*inverse
        j = np.cross(v, e1)
        w = float(direction@j)*inverse
        t = float(e2@j)*inverse
        if 0 <= u <= 1 and 0 <= w and u+w <= 1 and 0 <= t <= 1:
            point = a+t*direction
            return 0.0, point, point.copy()
    values = [closest_triangle(np.asarray([a, b]), triangle)]
    values.extend(segment_pair(a, b, c, d) for c, d in [(p, q), (q, r), (r, p)])
    return min((value for value in values if value is not None), key=lambda result: result[0])


def verify_distance_fixtures():
    fixtures = [
        (([-1, 0, 0], [1, 0, 0], [0, -1, 0], [0, 1, 0]), 0),
        (([0, 0, 0], [1, 0, 0], [0, 0, .2], [1, 0, .2]), .2),
        (([0, 0, 0], [1, 0, 0], [2, 0, 0], [3, 0, 0]), 1),
        (([0, 0, 0], [0, 0, 0], [1, -1, 0], [1, 1, 0]), 1),
        (([-1, 0, 0], [1, 0, 0], [0, -1, .05], [0, 1, .05]), .05),
    ]
    for points, expected in fixtures:
        actual = segment_pair(*(np.array(p, float) for p in points))[0]
        assert abs(actual-expected) < 1e-12, (actual, expected)
    triangle = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], float)
    assert segment_triangle(np.array([.2, .2, -1]), np.array([.2, .2, 1]), triangle)[0] == 0
    assert abs(segment_triangle(np.array([.2, .2, 1]), np.array([.3, .3, 1]), triangle)[0]-1) < 1e-12
    return dict(segmentPairs=len(fixtures), segmentTriangles=2, passed=True)

fixtures = verify_distance_fixtures()

def box_distance(lo_a, hi_a, lo_b, hi_b):
    return float(np.linalg.norm(np.maximum(np.maximum(lo_a-hi_b, lo_b-hi_a), 0)))

def triangle_pair(first, second):
    values = [segment_triangle(a, b, second)
              for a, b in zip(first, np.roll(first, -1, axis=0))]
    values.extend((distance, b, a) for distance, a, b in
                  (segment_triangle(a, b, first)
                   for a, b in zip(second, np.roll(second, -1, axis=0))))
    return min(values, key=lambda value: value[0])

class MeshQuery:
    """Small CPU BVH over actual authored triangles, with exact leaf tests."""
    def __init__(self, parts):
        self.triangles = np.concatenate([p['p'][p['f']].astype(float) for p in parts])
        self.names = np.concatenate([[p['name']]*len(p['f']) for p in parts])
        self.lo = self.triangles.min((0, 1))
        self.hi = self.triangles.max((0, 1))
        self.nodes = []
        self._build(np.arange(len(self.triangles)))

    def _build(self, indices):
        triangles = self.triangles[indices]
        node = dict(lo=triangles.min((0, 1)), hi=triangles.max((0, 1)))
        index = len(self.nodes)
        self.nodes.append(node)
        if len(indices) <= 8:
            node['indices'] = indices
        else:
            centers = triangles.mean(1)
            axis = np.ptp(centers, axis=0).argmax()
            ordered = indices[np.argsort(centers[:, axis])]
            middle = len(ordered)//2
            node['children'] = (self._build(ordered[:middle]), self._build(ordered[middle:]))
        return index

    def _query(self, shape, triangle=False, ceiling=float('inf')):
        low, high = shape.min(0), shape.max(0)
        result = (ceiling, None, None, None)
        queue = [(box_distance(low, high, self.lo, self.hi), 0)]
        while queue:
            bound, index = heapq.heappop(queue)
            if bound >= result[0]:
                continue
            node = self.nodes[index]
            if 'indices' in node:
                for i in node['indices']:
                    value = (triangle_pair(shape, self.triangles[i]) if triangle else
                             segment_triangle(shape[0], shape[1], self.triangles[i]))
                    if value[0] < result[0]:
                        result = (*value, str(self.names[i]))
            else:
                for child in node['children']:
                    sub = self.nodes[child]
                    lower = box_distance(low, high, sub['lo'], sub['hi'])
                    if lower < result[0]:
                        heapq.heappush(queue, (lower, child))
        return result

    def polyline(self, points):
        result = (float('inf'), None, None, None)
        for a, b in zip(points[:-1], points[1:]):
            value = self._query(np.asarray([a, b]), ceiling=result[0])
            if value[0] < result[0]:
                result = value
        return result

    def mesh(self, other):
        result = (float('inf'), None, None, None)
        for triangle in other.triangles:
            value = self._query(triangle, triangle=True, ceiling=result[0])
            if value[0] < result[0]:
                result = value
        return result

def outside_box_segments(points, low, high):
    """Retain every exact segment portion outside a narrow named interface."""
    result = []
    for a, b in zip(points[:-1], points[1:]):
        v = b-a
        enter, leave = 0., 1.
        for axis in range(3):
            if abs(v[axis]) < 1e-14:
                if a[axis] < low[axis] or a[axis] > high[axis]:
                    enter, leave = 2., -1.
                    break
            else:
                limits = sorted(((low[axis]-a[axis])/v[axis], (high[axis]-a[axis])/v[axis]))
                enter, leave = max(enter, limits[0]), min(leave, limits[1])
        if enter > leave or leave < 0 or enter > 1:
            result.append(np.asarray([a, b]))
        else:
            if enter > 1e-12:
                result.append(np.asarray([a, a+v*enter]))
            if leave < 1-1e-12:
                result.append(np.asarray([a+v*leave, b]))
    return result

def outside_box_surface(parts, low, high):
    """Exact triangle clipping; a port exception excludes no outside wall."""
    triangles = []
    planes = []
    for axis in range(3):
        normal = np.zeros(3)
        normal[axis] = 1
        planes.extend([(normal, high[axis]), (-normal, -low[axis])])

    def clip(polygon, normal, offset, outside=False):
        result = []
        for a, b in zip(polygon, np.roll(polygon, -1, axis=0)):
            da, db = float(a@normal-offset), float(b@normal-offset)
            in_a, in_b = (da > 0, db > 0) if outside else (da <= 0, db <= 0)
            if in_a:
                result.append(a)
            if in_a != in_b:
                result.append(a+(b-a)*(da/(da-db)))
        return np.asarray(result)

    for part in parts:
        for triangle in part['p'][part['f']].astype(float):
            interior = triangle
            for normal, offset in planes:
                if len(interior) < 3:
                    break
                exterior = clip(interior, normal, offset, outside=True)
                if len(exterior) >= 3:
                    triangles.extend([exterior[[0, i, i+1]] for i in range(1, len(exterior)-1)])
                interior = clip(interior, normal, offset)
    if not triangles:
        return []
    points = np.asarray(triangles).reshape(-1, 3)
    return [dict(name=parts[0]['name']+'.outside_named_root', p=points,
                 f=np.arange(len(points)).reshape(-1, 3))]

def narrow_port_region(pipe, part_name):
    match = re.fullmatch(r'rear\.exhaust\.bank_header\.(-?1)\.(\d)', pipe['name'])
    if match is None:
        return None
    side, port = map(int, match.groups())
    allowed = (part_name == f'rear.engine.cylinder_bank.{side}' or
               part_name.startswith(f'rear.engine.cooling_fin.{side}.') or
               part_name == f'rear.engine.cast_port_boss.{side}.{port}' or
               part_name == f'rear.engine.exhaust_port_flange.{side}.{port}' or
               part_name.startswith(f'rear.engine.port_flange_bolt.{side}.{port}.'))
    if not allowed:
        return None
    start = pipe['points'][0]
    end = start+np.array([side*.050, 0, 0])
    low, high = np.minimum(start, end), np.maximum(start, end)
    low += [-.001, -.040, -.040]
    high += [.001, .040, .040]
    return low, high

def ray_hits(origin, end, parts):
    triangles = np.concatenate([p['p'][p['f']].astype(float) for p in parts])
    direction = np.asarray(end)-origin
    e1, e2 = triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0]
    h = np.cross(direction, e2)
    determinant = np.einsum('ij,ij->i', e1, h)
    mask = np.abs(determinant) > 1e-12
    inverse = np.zeros_like(determinant)
    inverse[mask] = 1/determinant[mask]
    s = origin-triangles[:, 0]
    u = np.einsum('ij,ij->i', s, h)*inverse
    q = np.cross(s, e1)
    v = q@direction*inverse
    t = np.einsum('ij,ij->i', e2, q)*inverse
    return int(np.count_nonzero(mask & (u >= -1e-9) & (v >= -1e-9) &
                               (u+v <= 1+1e-9) & (t > 1e-7) & (t < 1-1e-7)))

# Fixtures cover face-interior crossing, finite edges, clipping, and an
# intentionally intersecting stand-in pair as a negative control.
flat = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], float)
crossing = np.array([[.2, .2, -1], [.2, .2, 1], [.3, .3, 1]], float)
assert triangle_pair(flat, crossing)[0] == 0
assert abs(triangle_pair(flat, flat+[0, 0, .025])[0]-.025) < 1e-12
clipped = outside_box_segments(np.array([[-2, 0, 0], [2, 0, 0]]), np.array([-1, -1, -1]), np.array([1, 1, 1]))
assert len(clipped) == 2 and np.allclose(clipped[0], [[-2, 0, 0], [-1, 0, 0]]) and np.allclose(clipped[1], [[1, 0, 0], [2, 0, 0]])
assert segment_pair(np.array([-1., 0, 0]), np.array([1., 0, 0]), np.array([0., -1, 0]), np.array([0., 1, 0]))[0]-.045-.033 < .020
clip_fixture = [dict(name='fixture', p=np.array([[-2., 0, 0], [2., 0, 0], [0, 2., 0]]), f=np.array([[0, 1, 2]]))]
clipped_surface = outside_box_surface(clip_fixture, np.array([-1., -1, -1]), np.array([1., 1, 1]))
assert len(clipped_surface) == 1
triangles = clipped_surface[0]['p'][clipped_surface[0]['f']]
area = sum(np.linalg.norm(np.cross(t[1]-t[0], t[2]-t[0]))/2 for t in triangles)
assert abs(area-2) < 1e-10, area
fixtures.update(trianglePairs=2, regionClips=1, exactSurfaceClip=1, negativeControl=True)
if args.fixtures_only:
    print(json.dumps(fixtures))
    sys.exit(0)

def emit(name, other, result, pipe_radius=0, other_radius=0, method='spline-envelope/tube'):
    distance, a, b = result[:3]
    return dict(hotPart=name, otherPart=other, method=method,
                centerDistance=distance,
                hotRadius=pipe_radius, otherRadius=other_radius,
                surfaceGap=distance-pipe_radius-other_radius,
                hotPoint=None if a is None else a.tolist(),
                otherPoint=None if b is None else b.tolist())

structures = [r for r in line_records if r['name'].startswith(
    ('rear.frame.', 'rear.bumper.', 'rear.engine.mount_stud.', 'rear.heat_shield.'))]
checks = []
contract_failures, interface_regions, flow_proofs = [], [], []
audit_metadata = metadata.get('clearanceAudit')
hot_paths = pipe_records
if audit_metadata:
    hot_paths = [dict(name=p['name'], points=np.asarray(p['points'], float), outer=float(p['radius']))
                 for p in audit_metadata['hotPaths']]
    indexed = {p['name']:p for p in hot_paths}
    for pipe in pipe_records:
        counterpart = indexed.get(pipe['name'])
        if (counterpart is None or counterpart['points'].shape != pipe['points'].shape or
            not np.allclose(counterpart['points'], pipe['points'], rtol=0, atol=1e-10) or
            abs(counterpart['outer']-pipe['outer']) > 1e-12):
            contract_failures.append('Hot metadata differs from actual pipe(): '+pipe['name'])
    recorded = {p['name']:p for p in line_records}
    for path in audit_metadata['coldPaths']:
        actual = recorded.get(path['name'])
        if (actual is None or actual['points'].shape != np.asarray(path['points']).shape or
            not np.allclose(actual['points'], path['points'], rtol=0, atol=1e-10) or
            abs(actual['radius']-path['radius']) > 1e-12):
            contract_failures.append('Cold metadata differs from actual primitive: '+path['name'])
    interfaces = {item['header']:item for item in audit_metadata.get('enginePortInterfaces', [])}
    for pipe in pipe_records:
        match = re.fullmatch(r'rear\.exhaust\.bank_header\.(-?1)\.(\d)', pipe['name'])
        if match:
            side = int(match.group(1))
            item = interfaces.get(pipe['name'])
            if (item is None or item['cylinderBank'] != f'rear.engine.cylinder_bank.{side}' or
                not np.allclose(item['center'], pipe['points'][0], atol=1e-10, rtol=0) or
                abs(item['rootEndX']-(pipe['points'][0, 0]+side*.050)) > 1e-10):
                contract_failures.append('Engine root exemption must match exact named 50mm source interface: '+pipe['name'])
elif not args.quick_tubes:
    contract_failures.append('Full revised-package acceptance requires actual hot/cold/collector/interface metadata.')

def add_check(name, other, result, hot_radius=0, cold_radius=0, method='exact authored surfaces', required=.020):
    check = emit(name, other, result, hot_radius, cold_radius, method)
    check['requiredGap'] = required
    checks.append(check)

cold_line_names = {line['name'] for line in structures}
solid_parts = [p for p in model.parts if p['name'].startswith(
    ('rear.frame.', 'rear.bumper.', 'rear.engine.', 'rear.heat_shield.',
     'rear.bash_plate.', 'rear.exhaust.rubber_')) and p['name'] not in cold_line_names]
query_cache = {}
def query(parts):
    key = tuple(p['name'] for p in parts)
    if key not in query_cache:
        query_cache[key] = MeshQuery(parts)
    return query_cache[key]

for pipe in hot_paths:
    points = pipe['points']
    for structure in structures:
        add_check(pipe['name'], structure['name'], closest_polylines(points, structure['points']),
                  pipe['outer'], structure['radius'], 'exact authored polyline capsule pair')
    if args.quick_tubes:
        continue
    body_result = query(bulkhead_parts).polyline(points)
    add_check(pipe['name'], 'interior.rear_bulkhead', body_result, pipe['outer'],
              method='actual hot path capsule/actual fixed generator bulkhead triangles')
    for part in solid_parts:
        p = part['p'].astype(float)
        if box_distance(points.min(0), points.max(0), p.min(0), p.max(0)) >= pipe['outer']+.035:
            continue
        pieces = [points]
        region = narrow_port_region(pipe, part['name'])
        if region is not None:
            pieces = outside_box_segments(points, *region)
            interface_regions.append(dict(hotPart=pipe['name'], otherPart=part['name'],
                                          low=region[0].tolist(), high=region[1].tolist(),
                                          remainingPieces=len(pieces),
                                          reason='Named engine port/head attachment only; all outside path portions remain checked.'))
            if part['name'].startswith(('rear.engine.cylinder_bank.', 'rear.engine.cooling_fin.')):
                # A local thermal-gap exception never permits an actual
                # intersecting header/head surface, even inside the root.
                outer = [p for p in model.parts if p['name'] == pipe['name']+'.outer_wall']
                if not outer:
                    contract_failures.append('Named port has no actual header wall: '+pipe['name'])
                else:
                    wall_points = np.concatenate([p['p'] for p in outer]).astype(float)
                    lower = box_distance(wall_points.min(0), wall_points.max(0), p.min(0), p.max(0))
                    actual = ((lower, None, None) if lower > 1e-6 else query([part]).mesh(query(outer)))
                    add_check(pipe['name'], part['name'], actual,
                              method='unclipped actual header/head surface nonintersection; positive AABB gap is conservative',
                              required=1e-6)
        if not pieces:
            continue
        mesh = query([part])
        result = min((mesh.polyline(piece) for piece in pieces), key=lambda value:value[0])
        if region is not None and result[0]-pipe['outer'] < .020:
            outer = [p for p in model.parts if p['name'] == pipe['name']+'.outer_wall']
            clipped = outside_box_surface(outer, *region)
            if clipped:
                precise = mesh.mesh(MeshQuery(clipped))
                add_check(pipe['name'], part['name'], precise,
                          method='actual header triangles exactly clipped outside same 50mm named root/solid triangles')
        else:
            add_check(pipe['name'], part['name'], result, pipe['outer'], 0,
                      'exact authored polyline capsule/solid triangles; narrow named port root clipped' if region else
                      'exact authored polyline capsule/solid triangles')

case = [p for p in model.parts if p['name'].startswith(
    ('rear.exhaust.transverse_oval_silencer_case', 'rear.exhaust.silencer_axial_neck_and_endcap.'))]
collectors = []
if audit_metadata:
    for collector in audit_metadata.get('collectors', []):
        parts = [p for p in model.parts if p['name'].startswith(collector['name']+'.')]
        if not parts:
            contract_failures.append('Collector has no actual surface: '+collector['name'])
        else:
            collectors.append((collector, parts))

if not args.quick_tubes:
    hot_mesh_groups = ([('rear.exhaust.silencer_case', case)] if case else [])
    hot_mesh_groups.extend((meta['name'], parts) for meta, parts in collectors)
    for name, hot_parts in hot_mesh_groups:
        hot_mesh = query(hot_parts)
        add_check(name, 'interior.rear_bulkhead', query(bulkhead_parts).mesh(hot_mesh),
                  method='actual hot mesh/actual fixed generator bulkhead triangles')
        for structure in structures:
            result = hot_mesh.polyline(structure['points'])
            add_check(name, structure['name'], (result[0], result[2], result[1]),
                      0, structure['radius'], 'actual hot mesh triangles/structural capsule')
        for part in solid_parts:
            p = part['p'].astype(float)
            if box_distance(hot_mesh.lo, hot_mesh.hi, p.min(0), p.max(0)) >= .035:
                continue
            result = query([part]).mesh(hot_mesh)
            add_check(name, part['name'], result, method='actual hot mesh triangles/solid triangles')

    for part in [p for p in model.parts if p['name'].startswith('rear.engine.')]:
        result = query(bulkhead_parts).mesh(query([part]))
        add_check(part['name'], 'interior.rear_bulkhead', result,
                  method='actual engine mesh/fixed generator bulkhead fit', required=.005)

    for structure in structures:
        if structure['name'].startswith(('rear.frame.', 'rear.bumper.')):
            result = query(bulkhead_parts).polyline(structure['points'])
            add_check(structure['name'], 'interior.rear_bulkhead', result, structure['radius'],
                      method='cold fixed frame capsule/actual generator bulkhead static fit', required=.005)
    for part in [p for p in solid_parts if p['name'].startswith(('rear.frame.', 'rear.bumper.'))]:
        add_check(part['name'], 'interior.rear_bulkhead', query(bulkhead_parts).mesh(query([part])),
                  method='cold fixed frame solid triangles/actual generator bulkhead fit', required=.005)

    # Shield bulk may attach through named standoffs; it may not pass through
    # structural frame/guard tubes. 2 mm is a fit gap, not the hot-part rule.
    shield = [p for p in model.parts if p['name'].startswith('rear.heat_shield.') and
              p['name'] not in {line['name'] for line in line_records}]
    if shield:
        shield_query = query(shield)
        for structure in structures:
            if not structure['name'].startswith(('rear.frame.', 'rear.bumper.')):
                continue
            value = shield_query.polyline(structure['points'])
            add_check('rear.heat_shield.bulk', structure['name'],
                      (value[0], value[2], value[1]), 0, structure['radius'],
                      'actual shield sheet triangles/structural capsule', required=.002)

    # Convex case pressure-volume containment catches wholly embedded rubber,
    # even when two disconnected surfaces themselves do not cross.
    if case:
        case_points = np.concatenate([p['p'] for p in case]).astype(float)
        hull = ConvexHull(case_points)
        for part in [p for p in solid_parts if p['name'].startswith('rear.exhaust.rubber_')]:
            distances = part['p']@hull.equations[:, :3].T+hull.equations[:, 3]
            contained = (distances < -1e-7).all(1)
            if contained.any():
                point = part['p'][np.flatnonzero(contained)[0]].astype(float)
                add_check('rear.exhaust.case_pressure_volume', part['name'], (0., point, point),
                          method='authored case convex pressure-volume containment', required=.020)

    # Independent bore rays inspect the actual surfaces, never metadata alone.
    for meta, parts in collectors:
        centers = np.asarray(meta['inletCenters'], float)
        if len(centers) != 3 or min(np.linalg.norm(a-b) for i,a in enumerate(centers) for b in centers[i+1:]) < 2*meta['inletRadius']+.002:
            contract_failures.append('Collector requires three distinct separated entry bores: '+meta['name'])
        for index, center in enumerate(centers):
            hits = ray_hits(center+[0, 0, .004], center-[0, 0, .020], parts)
            flow_proofs.append(dict(kind='collector inlet', part=meta['name'], index=index,
                                    hits=hits, passed=hits == 0))
        outlet = np.asarray(meta['center'], float)
        outlet[2] = meta['stations'][-1]['z']
        hits = ray_hits(outlet-[0, 0, .004], outlet+[0, 0, .015], parts)
        flow_proofs.append(dict(kind='collector exit', part=meta['name'], hits=hits, passed=hits == 0))
    if audit_metadata:
        exhaust_parts = [p for p in model.parts if p['name'].startswith('rear.exhaust.')]
        case_center = np.asarray(metadata['muffler']['center'], float)
        tip_centers = np.asarray(metadata['tip']['centers'], float)
        for side in [-1, 1]:
            tip = tip_centers[0 if side < 0 else 1]
            for offset in [(0, 0), (.020, 0), (-.020, 0), (0, .020), (0, -.020)]:
                origin = tip+np.array([offset[0], offset[1], -.015])
                end = origin.copy()
                end[2] = case_center[2]-.020
                hits = ray_hits(origin, end, exhaust_parts)
                flow_proofs.append(dict(kind='tailpipe through case opening', side=side,
                                        offset=offset, hits=hits, passed=hits == 0))
            origin = case_center+np.array([side*(metadata['muffler']['length']/2+.020), 0, 0])
            hits = ray_hits(origin, origin+[-side*.18, 0, 0], exhaust_parts)
            flow_proofs.append(dict(kind='axial case inlet', side=side, hits=hits, passed=hits == 0))

checks.sort(key=lambda value: value['surfaceGap']-value['requiredGap'])
failures = [v for v in checks if v['surfaceGap'] < v['requiredGap']-1e-7]
changed = []
for path, original in [(rear, rear_bytes), (generator, generator_bytes), (Path(__file__), audit_bytes)]:
    if path.read_bytes() != original:
        changed.append(str(path))
status = ('inconclusive_source_changed' if changed else 'fail' if failures or contract_failures or
          any(not v['passed'] for v in flow_proofs) else 'diagnostic_subset' if args.quick_tubes else 'pass')
report = dict(status=status, sourceSha256=hashlib.sha256(rear_bytes).hexdigest(),
              generatorSha256=hashlib.sha256(generator_bytes).hexdigest(),
              auditorSha256=hashlib.sha256(audit_bytes).hexdigest(), changedSources=changed,
              seconds=time.monotonic()-started, analyticFixtures=fixtures,
              scope='tube-only diagnostic subset' if args.quick_tubes else 'rear source package static geometry',
              curveStations='actual generated stations at authored spacing', pipeCount=len(pipe_records),
              hotEnvelopeCount=len(hot_paths), collectorMeshGroups=len(collectors),
              structuralTubeCount=len(structures), minimumHotStructureGap=.020,
              minimumShieldFrameFitGap=.002, contractFailures=contract_failures,
              namedLocalInterfaces=interface_regions, openBoreRays=flow_proofs,
              limits='Conservative exact capsule bounds and actual authored triangle distances. Narrow named engine port/head roots only; all outside portions remain checked. Case containment is a conservative convex pressure-volume keepout. No stress, thermal, internal-flow or dynamic certification.',
              failures=failures, nearby=[v for v in checks if v['requiredGap'] <= v['surfaceGap'] < .035],
              allChecks=checks)
if args.out:
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({key:value for key,value in report.items() if key != 'allChecks'}, indent=2))
sys.exit(3 if changed else 2 if status == 'fail' else 4 if args.quick_tubes else 0)
