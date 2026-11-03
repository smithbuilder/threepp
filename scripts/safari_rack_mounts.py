"""Four small, conformal roof feet for the original Safari basket.

Call before the generator's legacy rack translation. Every authored Y includes
``legacy_lift``; the existing rack.* translation seats the feet on the same
roof callback used by the body. The four existing 22 mm legs and basket are
untouched. This is plausible visible game hardware, not a load certification.
"""
import math

import numpy as np


PAD_OFFSET = .00055  # covers chord error between samples on the curved roof
PAD_THICKNESS = .0035
SHOE_THICKNESS = .005
PAD_HALF = (.035, .060)
SHOE_HALF = (.032, .054)
LEG_RADIUS = .022
SOCKET_BORE = .02235


def _unit(value):
    value = np.asarray(value, float)
    length = np.linalg.norm(value)
    if not np.isfinite(length) or length < 1e-12:
        raise ValueError('Invalid rack-foot direction')
    return value / length


def _roof_normal(height, x, z):
    h = .0001
    dx = (height(x+h, z)-height(x-h, z))/(2*h)
    dz = (height(x, z+h)-height(x, z-h))/(2*h)
    return _unit([-dx, 1., -dz])


def _mesh(model, name, points, faces, material, normals):
    p = np.asarray(points, float)
    f = np.asarray(faces, np.int64).reshape(-1, 3)
    n = np.asarray(normals, float)
    fn = np.cross(p[f[:, 1]]-p[f[:, 0]], p[f[:, 2]]-p[f[:, 0]])
    if not np.isfinite(p).all() or not np.isfinite(n).all():
        raise ValueError('Non-finite rack-foot geometry: '+name)
    if np.min(np.linalg.norm(fn, axis=1)) <= 1e-12:
        raise ValueError('Degenerate rack-foot face: '+name)
    reverse = np.einsum('ij,ij->i', fn, n[f].sum(axis=1)) < 0
    f[reverse] = f[reverse][:, ::-1]
    model.mesh(name, p, f, material, normals=n)


def _flat_mesh(model, name, points, faces, material):
    source = np.asarray(points, float)
    triangles = source[np.asarray(faces, np.int64)].copy()
    direction = np.cross(triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0])
    reverse = np.einsum('ij,ij->i', direction, triangles.mean(axis=1)-source.mean(axis=0)) < 0
    triangles[reverse] = triangles[reverse][:, ::-1]
    p = triangles.reshape(-1, 3)
    f = np.arange(len(p)).reshape(-1, 3)
    n = np.cross(p[f[:, 1]]-p[f[:, 0]], p[f[:, 2]]-p[f[:, 0]])
    n /= np.linalg.norm(n, axis=1)[:, None]
    _mesh(model, name, p, f, material, np.repeat(n, 3, axis=0))


def _conformal_slab(model, name, center, half, lower, upper, material, height):
    """Two sampled roof graphs and closed physical edges; no flat footplate."""
    x, z = center
    xs = np.linspace(x-half[0], x+half[0], 5)
    zs = np.linspace(z-half[1], z+half[1], 5)
    faces = []
    for i in range(4):
        for j in range(4):
            a = i*5+j
            faces.extend(((a, a+5, a+1), (a+1, a+5, a+6)))
    surfaces = []
    for label, offset, sign in [('roof_contact', lower, -1), ('top', upper, 1)]:
        p = np.asarray([(xx, height(xx, zz)+offset, zz) for zz in zs for xx in xs])
        n = [_roof_normal(height, xx, zz)*sign for zz in zs for xx in xs]
        _mesh(model, name+'.'+label, p, faces, material, n)
        surfaces.append(p)
    perimeter = list(range(5))+list(range(9, 25, 5))+list(range(23, 19, -1))+list(range(15, 0, -5))
    p = np.concatenate(surfaces)
    f = []
    for j, a in enumerate(perimeter):
        b = perimeter[(j+1) % len(perimeter)]
        f.extend(((a, b, a+25), (b, b+25, a+25)))
    _flat_mesh(model, name+'.physical_edges', p, f, material)


def _socket(model, name, x, z, bottom_offset, top_y, material, height):
    """A real annular sleeve: 0.35 mm radial room around the unchanged leg."""
    angles = np.arange(12)*math.tau/12
    p = []
    n = []
    for radius, top, inner in [(.0295, False, False), (.0275, True, False),
                               (SOCKET_BORE, False, True), (SOCKET_BORE, True, True)]:
        for angle in angles:
            dx, dz = radius*math.cos(angle), radius*math.sin(angle)
            p.append([x+dx, top_y if top else height(x+dx, z+dz)+bottom_offset, z+dz])
            n.append(_unit([math.cos(angle), .002/.05 if not inner else 0., math.sin(angle)])
                     *(-1 if inner else 1))
    faces = []
    for a in range(12):
        b = (a+1) % 12
        faces.extend(((a, a+12, b), (b, a+12, b+12),
                      (a+24, b+24, a+36), (b+24, b+36, a+36)))
    _mesh(model, name+'.walls', p, faces, material, n)
    # Separate hard normals at the annular top and curved shoe contact.
    for label, rings, sign in [('top_rim', [1, 3], 1), ('shoe_contact', [0, 2], -1)]:
        q = np.asarray([p[i*12+j] for i in rings for j in range(12)])
        ns = [np.array([0., 1., 0.])*sign if sign > 0 else
              -_roof_normal(height, point[0], point[2]) for point in q]
        fs = []
        for a in range(12):
            b = (a+1) % 12
            fs.extend(((a, b, a+12), (b, b+12, a+12)))
        _mesh(model, name+'.'+label, q, fs, material, ns)


def _hex_head(model, name, base, axis, radius, thickness, material):
    axis = _unit(axis)
    u = _unit(np.cross(axis, [0, 0, 1] if abs(axis[2]) < .9 else [0, 1, 0]))
    v = np.cross(axis, u)
    base = np.asarray(base, float)
    ring = [u*math.cos(a)*radius+v*math.sin(a)*radius for a in np.arange(6)*math.tau/6]
    p = [base+q+axis*d for d in [0, thickness] for q in ring]
    f = []
    for j in range(1, 5):
        f.extend(((0, j+1, j), (6, 6+j, 6+j+1)))
    for j in range(6):
        k = (j+1) % 6
        f.extend(((j, k, j+6), (k, k+6, j+6)))
    _flat_mesh(model, name, p, f, material)


def _gusset(model, name, x, z, direction, shoe_offset, material, height):
    # Two alternating webs leave both central roof bolts serviceable.
    xx = x+direction*.019
    points = np.asarray([[xx, height(xx, z+direction*.019)+shoe_offset-.0001, z+direction*.019],
                         [xx, height(xx, z+direction*.052)+shoe_offset-.0001, z+direction*.052],
                         [xx, height(x, z)+.045, z+direction*.019]])
    p = np.concatenate((points+[-.0015, 0, 0], points+[.0015, 0, 0]))
    faces = [(0, 2, 1), (3, 4, 5)]
    for j in range(3):
        k = (j+1) % 3
        faces.extend(((j, k, j+3), (k, k+3, j+3)))
    _flat_mesh(model, name, p, faces, material)


def build_rack_mounts(model, primitives, materials, roof_height_fn, legacy_lift=.17):
    """Add feet only, returning CPU construction proof in final coordinates.

    Required primitive: cylinder. Required material keys: black, rubber, metal.
    No materials, maps, passes, basket members, or replacement legs are created.
    """
    first = len(model.parts)
    cylinder = primitives['cylinder']
    black, rubber, metal = (materials[key] for key in ('black', 'rubber', 'metal'))
    def height(x, z):
        return float(roof_height_fn(float(x), float(z)))+legacy_lift
    shoe_bottom = PAD_OFFSET+PAD_THICKNESS
    shoe_top = shoe_bottom+SHOE_THICKNESS
    feet = []
    for side in [-1, 1]:
        for z in [-.58, -.04]:
            x = side*.67
            prefix = f'rack.foot.{side}.{z}'
            _conformal_slab(model, prefix+'.rubber_pad', (x, z), PAD_HALF,
                            PAD_OFFSET, shoe_bottom, rubber, height)
            _conformal_slab(model, prefix+'.steel_shoe', (x, z), SHOE_HALF,
                            shoe_bottom, shoe_top, black, height)
            _socket(model, prefix+'.leg_socket', x, z, shoe_top-.0001,
                    height(x, z)+.060, black, height)
            for direction in [-1, 1]:
                _gusset(model, prefix+f'.welded_web.{direction}', x, z, direction,
                        shoe_top, black, height)
            bolts = []
            for direction in [-1, 1]:
                zz = z+direction*.041
                normal = _roof_normal(height, x, zz)
                seat = np.array([x, height(x, zz)+shoe_top, zz])
                tag = prefix+f'.roof_bolt.{direction}'
                cylinder(tag+'.shank', seat-normal*(shoe_top-.0001),
                         seat+normal*.0015, .0033, metal, 6, caps=(False, False))
                cylinder(tag+'.washer', seat-normal*.0001, seat+normal*.0015,
                         .0085, metal, 8)
                _hex_head(model, tag+'.hex_head', seat+normal*.0015, normal,
                          .0065, .0048, metal)
                actual = seat.copy(); actual[1] -= legacy_lift
                bolts.append(dict(seat=actual.tolist(), axis=normal.tolist(),
                                  shank_radius=.0033, washer_radius=.0085))
            # A cross pin visibly fixes the existing leg inside the sleeve.
            pin = np.array([x, height(x, z)+.039, z])
            cylinder(prefix+'.leg_cross_pin.shank', pin+[-.032, 0, 0],
                     pin+[.032, 0, 0], .003, metal, 6, caps=(False, False))
            for direction in [-1, 1]:
                _hex_head(model, prefix+f'.leg_cross_pin.hex.{direction}',
                          pin+[direction*.029, 0, 0], [direction, 0, 0],
                          .0055, .004, metal)
            feet.append(dict(center=[x, float(roof_height_fn(x, z)), z],
                             roof_normal=_roof_normal(height, x, z).tolist(),
                             pad_half_xz=list(PAD_HALF), shoe_half_xz=list(SHOE_HALF),
                             pad_bottom_offset=PAD_OFFSET, pad_thickness_y=PAD_THICKNESS,
                             shoe_bottom_offset=shoe_bottom, shoe_top_offset=shoe_top,
                             socket_top_above_roof=.060, roof_bolts=bolts,
                             sleeve_bore_radius=SOCKET_BORE, legacy_leg_radius=LEG_RADIUS,
                             reinforced_webs=2, transverse_leg_pin=True))
    parts = model.parts[first:]
    points = np.concatenate([part['p'] for part in parts]).astype(float)
    final_points = points-[0, legacy_lift, 0]
    normals = np.concatenate([part['n'] for part in parts]).astype(float)
    twice_areas = np.concatenate([np.linalg.norm(np.cross(
        part['p'][part['f'][:, 1]]-part['p'][part['f'][:, 0]],
        part['p'][part['f'][:, 2]]-part['p'][part['f'][:, 0]]), axis=1) for part in parts])
    # Check the rendered triangles between roof samples, not only their
    # vertices: a chord of this convex roof can otherwise cut the paint.
    clearances = []
    for part in parts:
        if not part['name'].endswith('rubber_pad.roof_contact'):
            continue
        for triangle in part['p'][part['f']].astype(float):
            for i in range(17):
                for j in range(17-i):
                    a, b = i/16, j/16
                    xx, yy, zz = triangle[0]*(1-a-b)+triangle[1]*a+triangle[2]*b
                    clearances.append(yy-legacy_lift-float(roof_height_fn(xx, zz)))
    proof = dict(finite=bool(np.isfinite(points).all() and np.isfinite(normals).all()),
                 max_unit_normal_error=float(np.max(abs(np.linalg.norm(normals, axis=1)-1))),
                 min_triangle_area=float(twice_areas.min()/2),
                 triangles=sum(len(part['f']) for part in parts),
                 all_names_receive_rack_translation=all(part['name'].startswith('rack.') for part in parts),
                 contact_surface='roof_height_fn(x,z) at every pad and shoe vertex',
                 pad_roof_dense_samples=len(clearances),
                 pad_roof_min_y_clearance=float(min(clearances)),
                 pad_roof_max_y_clearance=float(max(clearances)),
                 nominal_pad_to_shoe_gap=0., socket_to_shoe_overlap=.0001,
                 unchanged_leg_bore_radial_clearance=SOCKET_BORE-LEG_RADIUS,
                 bolt_count=8, transverse_pin_count=4)
    if not proof['finite'] or proof['max_unit_normal_error'] > 1e-5 or proof['min_triangle_area'] <= 1e-12:
        raise ValueError('Rack-foot CPU geometry proof failed')
    if proof['triangles'] > 2000:
        raise ValueError('Rack-foot triangle budget exceeded')
    if proof['pad_roof_min_y_clearance'] < -1e-7:
        raise ValueError('Rack-foot rubber pad intersects the roof callback')
    return dict(coordinate_frame='authored before legacy rack Y translation',
                legacy_lift=legacy_lift, parts=len(parts), feet=feet, proof=proof,
                actual_bounds=dict(min=final_points.min(0).tolist(), max=final_points.max(0).tolist()),
                construction='conformal rubber pad, curved steel shoe, two webs, hollow leg sleeve, two roof bolts and one transverse leg pin per foot',
                limits='Visible game geometry only; no stress certification or roof load rating.')
