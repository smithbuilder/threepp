"""Detached full-size Cinder Safari spare, authored without a renderer.

The carcass, barrel and six-row tread follow the original road wheel in
RallyWheels.hpp, scaled to the Safari's .49 m radius / .17 m half width.
This is an unmounted wheel: there is no brake, axle cap, stud or lug nut.
The centre bore, five lug holes and spaces between the eight spokes are open.
All names start cargo.spare so the generator's existing cargo seating applies.
"""
import math

import numpy as np

TAU = math.tau
RADIUS_SCALE = .49 / .54
WIDTH_SCALE = .17 / .20

# (radius, axial position), in the road wheel's original coordinate system.
CARCASS_PROFILE = [
    (.230, -.145), (.251, -.174), (.290, -.189), (.330, -.195),
    (.400, -.193), (.460, -.183), (.500, -.158), (.515, -.120),
    (.521, -.070), (.523, 0), (.521, .070), (.515, .120),
    (.500, .158), (.460, .183), (.400, .193), (.330, .195),
    (.290, .189), (.251, .174), (.230, .145), (.242, .132),
    (.330, .163), (.450, .151), (.491, .108), (.498, 0),
    (.491, -.108), (.450, -.151), (.330, -.163), (.242, -.132),
    (.230, -.145),
]
BARREL_PROFILE = [
    (.235, -.170), (.238, -.158), (.228, -.146), (.228, .146),
    (.240, .166), (.235, .174), (.216, .148), (.216, -.146),
    (.225, -.170), (.235, -.170),
]


def _flat_mesh(model, name, points, faces, material):
    """Flat bevel faces with independent normals, not inflated smooth edges."""
    p = np.asarray(points, float)[np.asarray(faces, np.int64)].reshape(-1, 3)
    f = np.arange(len(p)).reshape(-1, 3)
    n = np.cross(p[f[:, 1]]-p[f[:, 0]], p[f[:, 2]]-p[f[:, 0]])
    n /= np.linalg.norm(n, axis=1)[:, None]
    model.mesh(name, p, f, material, normals=np.repeat(n, 3, axis=0))


def _lathe(model, name, center, profile, material, segments=40):
    """Physical annular cross-section, including its internal bead/barrel wall."""
    center = np.asarray(center, float)
    p = []
    for radius, axial in profile:
        p.append([center+[radius*RADIUS_SCALE*math.cos(a),
                         axial*WIDTH_SCALE,
                         radius*RADIUS_SCALE*math.sin(a)]
                  for a in np.linspace(0, TAU, segments+1)])
    model.grid(name, p, material)


def _tile_points():
    x, z, chamfer = .066/2, .063/2, .063*.18
    outline = [(-x+chamfer, -z), (x-chamfer, -z), (x, -z+chamfer),
               (x, z-chamfer), (x-chamfer, z), (-x+chamfer, z),
               (-x, z-chamfer), (-x, -z+chamfer)]
    # One physical bevel; 28 triangles instead of three over-sampled rings.
    points = [[a*s, h, b*s] for s, h in [(1, -.017/2), (.88, .017/2)]
              for a, b in outline]
    faces = []
    for j in range(8):
        k = (j+1) % 8
        faces.extend(((j, 8+j, k), (k, 8+j, 8+k)))
    for j in range(1, 7):
        faces.extend(((8, 8+j+1, 8+j), (0, j, j+1)))
    return np.asarray(points), faces


def _tread_radius(x):
    x = abs(x)
    if x < .07:
        return .523-x*.025
    if x < .14:
        return .52125-(x-.07)*.13
    return .51215-(x-.14)*.65


def _spoke(model, center, angle, material, number):
    """Dished eight-spoke face; roots join the hub outside the lug circle."""
    p = []
    for radius, axial, half_width in [(.113, .075, .024), (.130, .090, .023),
                                     (.185, .130, .019), (.218, .150, .017)]:
        # Eased rectangle in the axial/tangential section.
        depth, bevel = .010, .003
        cross = [(-depth+bevel, -half_width), (depth-bevel, -half_width),
                 (depth, -half_width+bevel), (depth, half_width-bevel),
                 (depth-bevel, half_width), (-depth+bevel, half_width),
                 (-depth, half_width-bevel), (-depth, -half_width+bevel)]
        for da, dt in cross:
            r, t = radius*RADIUS_SCALE, dt*RADIUS_SCALE
            p.append(np.asarray(center)+[r*math.cos(angle)-t*math.sin(angle),
                                          (axial+da)*WIDTH_SCALE,
                                          r*math.sin(angle)+t*math.cos(angle)])
    faces = []
    for station in range(3):
        for j in range(8):
            a, b = station*8+j, station*8+(j+1) % 8
            faces.extend(((a, b, a+8), (b, b+8, a+8)))
    for j in range(1, 7):
        faces.extend(((0, j+1, j), (24, 24+j, 24+j+1)))
    _flat_mesh(model, f'cargo.spare.spoke.{number}', p, faces, material)


def _hub(model, center, material):
    """Five perforated annular sectors with actual lug bores and centre bore."""
    inner, outer = .055*RADIUS_SCALE, .122*RADIUS_SCALE
    lug_radius, hole_radius = .094*RADIUS_SCALE, .0102*RADIUS_SCALE
    bottom, top = .069*WIDTH_SCALE, .089*WIDTH_SCALE
    half = math.pi/5
    # Identical rotational sectors make their radial seams match exactly.
    outline = np.r_[
        [[outer*math.cos(a), outer*math.sin(a)] for a in np.linspace(-half, half, 7)],
        [[inner*math.cos(a), inner*math.sin(a)] for a in np.linspace(half, -half, 7)],
    ]
    hole = np.array([lug_radius, 0.])
    polygon = outline-hole
    angles = np.unique(np.round(np.r_[np.arange(16)*TAU/16,
                     np.mod(np.arctan2(polygon[:, 1], polygon[:, 0]), TAU)], 12))
    perimeter = []
    for a in angles:
        ray = np.array([math.cos(a), math.sin(a)])
        hits = []
        for q, r in zip(polygon, np.roll(polygon, -1, axis=0)):
            edge = r-q
            matrix = np.c_[ray, -edge]
            if abs(np.linalg.det(matrix)) < 1e-13:
                continue
            distance, t = np.linalg.solve(matrix, q)
            if distance > 0 and -1e-9 <= t <= 1+1e-9:
                hits.append(distance)
        if not hits:
            raise ValueError('Lug bore left its supporting annular hub sector')
        perimeter.append(hole+ray*min(hits))
    perimeter = np.asarray(perimeter)
    bore = hole+hole_radius*np.c_[np.cos(angles), np.sin(angles)]
    for sector in range(5):
        angle = sector*TAU/5+.09
        rotation = np.array([[math.cos(angle), -math.sin(angle)],
                             [math.sin(angle), math.cos(angle)]])
        loops = [bore@rotation.T, perimeter@rotation.T]
        n = len(bore)
        p = [np.asarray(center)+[x, y, z]
             for y in [bottom, top] for loop in loops for x, z in loop]
        faces = []
        for j in range(n):
            k = (j+1) % n
            # Top/bottom annular skins, then the open lug bore wall.
            faces.extend(((j, k, n+j), (k, n+k, n+j),
                          (2*n+j, 3*n+j, 2*n+k), (2*n+k, 3*n+j, 3*n+k),
                          (j, 2*n+j, k), (k, 2*n+j, 2*n+k)))
            # Only real inner/outer circumference walls; adjacent radial
            # sector boundaries have no hidden coincident internal walls.
            a, b = perimeter[j], perimeter[k]
            same_seam = any(abs(np.cross([math.cos(s), math.sin(s)], a)) < 1e-9
                            and abs(np.cross([math.cos(s), math.sin(s)], b)) < 1e-9
                            for s in [-half, half])
            if not same_seam:
                faces.extend(((n+j, n+k, 3*n+j), (n+k, 3*n+k, 3*n+j)))
        _flat_mesh(model, f'cargo.spare.hub.open_lug_sector.{sector}', p,
                   [tuple(reversed(f)) for f in faces], material)
    return [[float(lug_radius*math.cos(i*TAU/5+.09)),
             float(lug_radius*math.sin(i*TAU/5+.09))] for i in range(5)], hole_radius


def _verify_open_passages(parts, center, lug_centers):
    """Trace the actual authored triangles, including spokes and barrel.

    These small generation-time witnesses catch a reinstated barrel cap or
    a spoke covering a lug hole. They do not stand in for whole-vehicle fit.
    """
    triangles = np.concatenate([part['p'][part['f']] for part in parts]).astype(float)
    e1 = triangles[:, 1]-triangles[:, 0]
    e2 = triangles[:, 2]-triangles[:, 0]
    direction = np.array([0., -1., 0.])
    h = np.cross(np.broadcast_to(direction, e2.shape), e2)
    determinant = np.einsum('ij,ij->i', e1, h)
    valid = abs(determinant) > 1e-12
    inverse = np.divide(1., determinant, out=np.zeros_like(determinant), where=valid)
    queries = [('center', [0., 0.])]
    queries += [(f'center_margin.{j}', [.035*math.cos(j*TAU/4), .035*math.sin(j*TAU/4)])
                for j in range(4)]
    for i, point in enumerate(lug_centers):
        queries.append((f'lug.{i}', point))
        queries += [(f'lug_margin.{i}.{j}', np.asarray(point)+
                     [.006*math.cos(j*TAU/4), .006*math.sin(j*TAU/4)])
                    for j in range(4)]
    queries += [(f'spoke_gap.{j}', [.15*math.cos((j+.5)*TAU/8),
                                   .15*math.sin((j+.5)*TAU/8)]) for j in range(8)]
    proof = []
    for name, (x, z) in queries:
        origin = center+[x, .4, z]
        v = origin-triangles[:, 0]
        u = np.einsum('ij,ij->i', v, h)*inverse
        q = np.cross(v, e1)
        w = (q@direction)*inverse
        distance = np.einsum('ij,ij->i', e2, q)*inverse
        hits = int(np.count_nonzero(valid & (u >= -1e-9) & (w >= -1e-9) &
                                   (u+w <= 1+1e-9) & (distance >= 0)))
        if hits:
            raise ValueError(f'Detached spare opening is blocked: {name}, {hits} triangles')
        proof.append(dict(name=name, localXZ=[float(x), float(z)], hits=hits))
    return proof


def build_spare_wheel(model, primitives, materials, center):
    """Append a horizontal unmounted spare before legacy cargo translation."""
    center = np.asarray(center, float)
    first = len(model.parts)
    rubber, bronze = materials['rubber'], materials['bronze']
    black, metal = materials['black'], materials['metal']
    _lathe(model, 'cargo.spare.tyre_road_profile', center, CARCASS_PROFILE, rubber)
    _lathe(model, 'cargo.spare.open_barrel_road_profile', center, BARREL_PROFILE, bronze)
    _lathe(model, 'cargo.spare.beadlock_annulus', center,
           [(.250, .163), (.250, .181), (.208, .181), (.208, .163), (.250, .163)], bronze)
    hole_centers, hole_radius = _hub(model, center, bronze)
    for j in range(8):
        _spoke(model, center, j*TAU/8, bronze, j)
    tile, faces = _tile_points()
    for row, axial in enumerate([-.173, -.126, -.044, .044, .126, .173]):
        for j in range(40):
            angle = (j+(row % 2)*.46)*TAU/40
            slope = (_tread_radius(axial+.001)-_tread_radius(axial-.001))/.002
            tilt = math.atan(slope)
            c, s = math.cos(tilt), math.sin(tilt)
            q = tile*np.array([.46 if row in (0, 5) else 1, 1,
                               1+(j % 3-1)*.055])
            q = q@np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]]).T
            q += [axial, _tread_radius(axial), 0]
            q += np.array([-s, c, 0])*.0065
            # Map the road wheel's axle X onto the horizontal spare's Y.
            x = (q[:, 1]*math.cos(angle)-q[:, 2]*math.sin(angle))*RADIUS_SCALE
            y = q[:, 0]*WIDTH_SCALE
            z = (q[:, 1]*math.sin(angle)+q[:, 2]*math.cos(angle))*RADIUS_SCALE
            p = np.c_[x, y, z]+center
            _flat_mesh(model, f'cargo.spare.tread.{row}.{j}', p,
                       [tuple(reversed(f)) for f in faces], rubber)
    # These are rim assembly bolts, not wheel-to-car lug nuts. Their axis is
    # the wheel axis, with the same 24-position ring as the road wheel.
    cylinder = primitives['cylinder']
    for j in range(24):
        angle = j*TAU/24
        radius = .232*RADIUS_SCALE
        p = center+[radius*math.cos(angle), .188*WIDTH_SCALE,
                    radius*math.sin(angle)]
        # Six flat faces, without redundant centre vertices in the two caps.
        corners = np.array([[radius*math.cos(a), y, radius*math.sin(a)]
                            for y in [-.0051, .0051]
                            for a in np.arange(6)*TAU/6])
        corners[:, [0, 2]] *= .009*RADIUS_SCALE/radius
        bolt_faces = []
        for k in range(6):
            n = (k+1) % 6
            bolt_faces.extend(((k, n, k+6), (n, n+6, k+6)))
        for k in range(1, 5):
            bolt_faces.extend(((0, k+1, k), (6, 6+k, 6+k+1)))
        # XZ angular order gives -Y on the top; reverse the complete solid.
        _flat_mesh(model, f'cargo.spare.beadlock_bolt.{j}', corners+p,
                   [tuple(reversed(f)) for f in bolt_faces], metal)
    angle = .72
    radius = .200*RADIUS_SCALE
    p = center+[radius*math.cos(angle), .177*WIDTH_SCALE,
                radius*math.sin(angle)]
    cylinder('cargo.spare.valve_stem', p, p+[0, .018, 0], .0045, black, 8)
    parts = model.parts[first:]
    points = np.concatenate([p['p'] for p in parts])
    local = points-center
    maximum_radius = float(np.linalg.norm(local[:, [0, 2]], axis=1).max())
    half_width = float(abs(local[:, 1]).max())
    if maximum_radius > .49+1e-7 or half_width > .17+1e-7:
        raise ValueError('Full-size spare exceeds the Safari tyre envelope')
    for part in parts:
        if not np.isfinite(part['p']).all() or not np.isfinite(part['n']).all() or \
                np.max(abs(np.linalg.norm(part['n'], axis=1)-1)) > 1e-5:
            raise ValueError('Invalid spare geometry/normals: '+part['name'])
    passages = _verify_open_passages(parts, center, hole_centers)
    return dict(parts=len(parts), triangles=sum(len(p['f']) for p in parts),
                centerBeforeCargoSeating=center.tolist(), axle=[0, 1, 0],
                roadProfileSource='showcase/RallyWheels.hpp original Cinder wheel',
                scales=dict(radius=RADIUS_SCALE, width=WIDTH_SCALE),
                actualMaximumRadius=maximum_radius, actualHalfWidth=half_width,
                bounds=dict(min=points.min(0).tolist(), max=points.max(0).tolist()),
                openCenterRadius=.055*RADIUS_SCALE,
                lugBores=dict(count=5, centersXZ=hole_centers, radius=hole_radius),
                treadRows=6, treadStations=40, spokeCount=8,
                openPassageChecks=passages,
                detached=True, hasBrakeRotor=False, hasAxleCap=False,
                hasInstalledLugNuts=False,
                limits='Original game wheel; not certified automotive fitment.')
