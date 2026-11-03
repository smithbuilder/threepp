"""Serviceable front recovery hardware for the original Cinder Safari.

Coordinates are actual chassis metres, +Z forward. Call AFTER the generator's
legacy front-hardware translation. The two .38/.34/1.65 pickups meet the fixed
Safari rails; the cream body carries no recovery or skid load. This is a
visually plausible game assembly, not a load rating or certified fitment.
"""
import copy
import math

import numpy as np

TAU = math.tau
SHEET = .006


def _unit(value):
    value = np.asarray(value, float)
    return value / np.linalg.norm(value)


def _oriented_mesh(model, name, points, faces, material, normals):
    """Keep winding and the deliberately hard/smooth normals in agreement."""
    p = np.asarray(points, float)
    f = np.asarray(faces, np.int64).reshape(-1, 3)
    n = np.asarray(normals, float)
    fn = np.cross(p[f[:, 1]]-p[f[:, 0]], p[f[:, 2]]-p[f[:, 0]])
    reverse = np.einsum('ij,ij->i', fn, n[f].sum(1)) < 0
    f[reverse] = f[reverse][:, ::-1]
    model.mesh(name, p, f, material, normals=n)


def _quads(model, name, rows, normals, material):
    rows = np.asarray(rows, float)
    normals = np.asarray(normals, float)
    faces = []
    for i in range(len(rows)-1):
        for j in range(len(rows[0])-1):
            a = i*len(rows[0])+j
            b = a+len(rows[0])
            faces.extend(((a, a+1, b), (a+1, b+1, b)))
    _oriented_mesh(model, name, rows.reshape(-1, 3), faces, material,
                   normals.reshape(-1, 3))


def _solid_polygon(model, name, points, thickness, material):
    """A convex, welded gusset with physical edge faces and flat normals."""
    q = np.asarray(points, float)
    normal = _unit(np.cross(q[1]-q[0], q[2]-q[0]))
    p = []
    n = []
    f = []

    def face(vertices, direction):
        start = len(p)
        p.extend(vertices)
        n.extend([direction]*len(vertices))
        f.extend((start, start+i, start+i+1) for i in range(1, len(vertices)-1))

    face(q+normal*thickness/2, normal)
    face(q-normal*thickness/2, -normal)
    for i in range(len(q)):
        a, b = q[i], q[(i+1) % len(q)]
        edge_n = _unit(np.cross(b-a, normal))
        face([a+normal*thickness/2, b+normal*thickness/2,
              b-normal*thickness/2, a-normal*thickness/2], edge_n)
    _oriented_mesh(model, name, p, f, material, n)


def _perimeter_rectangle(half_width, half_length, samples=6):
    corners = np.array([[-half_width, -half_length], [half_width, -half_length],
                        [half_width, half_length], [-half_width, half_length]])
    return np.asarray([a+(corners[(i+1) % 4]-a)*t
                       for i, a in enumerate(corners)
                       for t in np.linspace(0, 1, samples, endpoint=False)])


def _annular_sheet(model, name, center, u, v, outer, hole_radius, thickness,
                   material, bevel=.00065, outer_edges=()):
    """Exact ring topology: two skins, chamfered bore, selected outer walls.

    Every outer cell boundary is authored explicitly. No triangulation or
    centroid rejection can accidentally bridge a hole or create a saw edge.
    Adjacent rectangular cells share matching perimeter positions.
    """
    center = np.asarray(center, float)
    u, v = _unit(u), _unit(v)
    normal = _unit(np.cross(u, v))
    outer = np.asarray(outer, float)
    radial = outer/np.linalg.norm(outer, axis=1)[:, None]
    inner = radial*(hole_radius+bevel)
    count = len(outer)
    faces = []
    for j in range(count):
        k = (j+1) % count
        faces.extend(((j, k, count+j), (k, count+k, count+j)))
    for side in [-1, 1]:
        points = [center+u*q[0]+v*q[1]+normal*(side*thickness/2)
                  for loop in [outer, inner] for q in loop]
        _oriented_mesh(model, name+('.skin_a' if side > 0 else '.skin_b'),
                       points, faces, material, [normal*side]*(count*2))
    # The 0.65 mm chamfer catches light at the real opening; its narrowest
    # diameter is still open all the way through the six millimetre sheet.
    rows = []
    ns = []
    for depth, radius, axial in [(thickness/2, hole_radius+bevel, .65),
                                 (thickness/2-bevel, hole_radius, 0),
                                 (-thickness/2+bevel, hole_radius, 0),
                                 (-thickness/2, hole_radius+bevel, -.65)]:
        rows.append([center+u*d[0]*radius+v*d[1]*radius+normal*depth
                     for d in np.r_[radial, radial[:1]]])
        ns.append([_unit(-u*d[0]-v*d[1]+normal*axial)
                   for d in np.r_[radial, radial[:1]]])
    _quads(model, name+'.open_bore_wall', rows, ns, material)
    for j in outer_edges:
        a, b = outer[j], outer[(j+1) % count]
        aa, bb = center+u*a[0]+v*a[1], center+u*b[0]+v*b[1]
        edge_n = _unit(np.cross(bb-aa, normal))
        p = [aa+normal*thickness/2, bb+normal*thickness/2,
             aa-normal*thickness/2, bb-normal*thickness/2]
        _oriented_mesh(model, name+f'.outer_edge.{j}', p,
                       [(0, 1, 2), (1, 3, 2)], material, [edge_n]*4)


def _ray_polygon_perimeter(outline, segments=64):
    """Sample a convex plate around its pin bore, including exact corners."""
    outline = np.asarray(outline, float)
    angles = np.unique(np.round(np.r_[np.arange(segments)*TAU/segments,
                                      np.mod(np.arctan2(outline[:, 1], outline[:, 0]), TAU)], 11))
    points = []
    for angle in angles:
        direction = np.array([math.cos(angle), math.sin(angle)])
        distances = []
        for i, a in enumerate(outline):
            edge = outline[(i+1) % len(outline)]-a
            system = np.c_[direction, -edge]
            if abs(np.linalg.det(system)) < 1e-10:
                continue
            length, along = np.linalg.solve(system, a)
            if length > 0 and -1e-8 <= along <= 1+1e-8:
                distances.append(length)
        if not distances:
            raise ValueError('Pin bore must lie inside its convex lug')
        points.append(direction*min(distances))
    points = np.asarray(points)
    keep = np.r_[True, np.linalg.norm(np.diff(points, axis=0), axis=1) > 1e-8]
    points = points[keep]
    if np.linalg.norm(points[-1]-points[0]) < 1e-8:
        points = points[:-1]
    return points


def _forged_eye(model, name, center, axis, radius, bore, thickness, material):
    """A thick forged eye, with eased shoulders and an actual axial bore."""
    axis = _unit(axis)
    u = _unit(np.cross(axis, [0, 0, 1]))
    v = np.cross(axis, u)
    center = np.asarray(center, float)
    angles = np.linspace(0, TAU, 33)
    radial = np.asarray([u*math.cos(a)+v*math.sin(a) for a in angles])
    # Continuous outer profile, unlike a flat cylinder or a torus.
    bevel = min(.003, thickness*.24, radius*.08)
    bore_bevel = min(.0006, thickness*.20)
    profile = [(-thickness/2, radius-bevel), (-thickness/2+bevel, radius),
               (thickness/2-bevel, radius), (thickness/2, radius-bevel)]
    points = [[center+axis*x+d*r for d in radial] for x, r in profile]
    normals = [[_unit(d+axis*ax) for d in radial] for ax in [-.5, 0, 0, .5]]
    _quads(model, name+'.forged_outer_shoulder', points, normals, material)
    for side in [-1, 1]:
        rows = [[center+axis*(side*thickness/2)+d*r for d in radial]
                for r in [bore+bore_bevel, radius-bevel]]
        _quads(model, name+f'.annular_face.{side}', rows,
               [[axis*side]*len(angles)]*2, material)
    rows = [[center+axis*x+d*r for d in radial] for x, r in
            [(-thickness/2, bore+bore_bevel), (-thickness/2+bore_bevel, bore),
             (thickness/2-bore_bevel, bore), (thickness/2, bore+bore_bevel)]]
    _quads(model, name+'.open_pin_bore', rows,
           [[-d for d in radial]]*4, material)


def _forged_bow(model, name, center, material):
    """Open U forging: its two legs terminate in separate pin eyes."""
    center = np.asarray(center, float)
    # Separate straight necks blend tangentially into a broad bow crown.
    # The pin closes this U; there is deliberately no red crossbar/torus.
    points = []
    for t in np.linspace(0, 1, 10, endpoint=False):
        points.append([-.049-.013*t, -.024-.069*t, 0])
    for angle in np.linspace(math.pi, TAU, 33, endpoint=False):
        points.append([.062*math.cos(angle), -.093+.058*math.sin(angle), 0])
    for t in np.linspace(0, 1, 11):
        points.append([.062-.013*t, -.093+.069*t, 0])
    points = np.asarray(points)+center
    tangent = np.gradient(points, axis=0)
    tangent /= np.linalg.norm(tangent, axis=1)[:, None]
    # In-plane radial and fore/aft radial retain a slightly flattened forged
    # section, with a heavier crown rather than a perfect bent wire circle.
    sections = []
    normals = []
    for point, direction in zip(points, tangent):
        across = _unit(np.cross(direction, [0, 0, 1]))
        crown = np.clip((center[1]-point[1]-.03)/.12, 0, 1)
        radius = .0148+.0035*crown
        sections.append([point+across*(radius*math.cos(a))+
                         np.array([0, 0, radius*.91*math.sin(a)])
                         for a in np.linspace(0, TAU, 13)])
        normals.append([_unit(across*math.cos(a)+np.array([0, 0, math.sin(a)/.91]))
                        for a in np.linspace(0, TAU, 13)])
    _quads(model, name+'.open_U_forging', sections, normals, material)
    # The end faces are inside the eye forgings, but close the forging itself.
    for end in [0, len(sections)-1]:
        loop = sections[end][:-1]
        _oriented_mesh(model, name+f'.neck_end.{end}', loop,
                       [(0, i, i+1) for i in range(1, len(loop)-1)],
                       material, [tangent[end]*(1 if end else -1)]*len(loop))


def _bent_strip(model, name, points, normals, width, material, end_caps=True):
    """A bend with separate six millimetre skins and real end/side walls."""
    points = np.asarray(points, float)
    normals = np.asarray(normals, float)
    rows = []
    ns = []
    for side in [-1, 1]:
        rows.append([[point+np.array([x, 0, 0])+normal*side*SHEET/2
                      for x in [-width, width]]
                     for point, normal in zip(points, normals)])
        ns.append([[normal*side]*2 for normal in normals])
        _quads(model, name+f'.skin.{side}', rows[-1], ns[-1], material)
    # Side walls are omitted here: the continuous side returns close them.
    if end_caps:
        for end in [0, len(points)-1]:
            p = [rows[0][end][0], rows[0][end][1],
                 rows[1][end][0], rows[1][end][1]]
            direction = _unit(points[1]-points[0]) if end == 0 else _unit(points[-1]-points[-2])
            _oriented_mesh(model, name+f'.end_wall.{end}', p,
                           [(0, 1, 2), (1, 3, 2)], material,
                           [direction*(-1 if end == 0 else 1)]*4)


def build_front_recovery(model, primitives, materials):
    """Build the assembly and return dimensions plus CPU topology evidence."""
    first = len(model.parts)
    box = primitives['box']
    cylinder = primitives['cylinder']
    polyline = primitives['polyline']
    torus = primitives['torus']
    frame = materials['black']
    alloy = materials['metal']
    # Powder coat is a dielectric finish over steel. The pin remains exposed
    # satin metal; adding metallicFactor=1 to red paint would be implausible.
    powder = len(model.materials)
    model.materials.append(copy.deepcopy(model.materials[materials['red']]))
    model.materials[powder]['name'] = 'safari.front_recovery_red_powdercoat'
    model.materials[powder]['pbrMetallicRoughness'].update(roughnessFactor=.36,
                                                       metallicFactor=.035)
    model.materials[powder]['extensions'] = {
        'KHR_materials_clearcoat': {'clearcoatFactor': .23,
                                  'clearcoatRoughnessFactor': .25}}
    pin_finish = len(model.materials)
    model.materials.append(copy.deepcopy(model.materials[alloy]))
    model.materials[pin_finish]['name'] = 'safari.front_recovery_satin_pin_steel'
    model.materials[pin_finish]['pbrMetallicRoughness'].update(roughnessFactor=.31,
                                                           metallicFactor=.88)
    anchors = []
    pins = []
    load_paths = []
    # A separate recovery crossmember is behind the bumper. Both carriers
    # terminate at actual fixed chassis rail/crossmember geometry, not paint.
    box('front.recovery.chassis_crossmember', (0, .58, 2.08),
        (1.44, .075, .08), frame, .009, 3)
    for side in [-1, 1]:
        a = np.array([side*.38, .34, 1.65])
        b = np.array([side*.69, .58, 2.08])
        anchors.append(a.tolist())
        cylinder(f'front.recovery.chassis_load_strut.{side}', a, b, .029, frame, 16)
        cylinder(f'front.recovery.inboard_crossmember_diagonal.{side}',
                 (side*.25, .34, 1.59), b, .024, frame, 12)
        box(f'front.recovery.rail_end_splice.{side}', a+[0, 0, .006],
            (.087, .080, .046), frame, .005, 2)
        cylinder(f'front.recovery.splice_bolt.{side}',
                 a+[-.058, 0, 0], a+[.058, 0, 0], .012, alloy, 6)
        # This triangle shares the carrier and beam endpoints. Its thickness
        # and edge faces are modelled; it is not a floating single triangle.
        _solid_polygon(model, f'front.recovery.beam_carrier_gusset.{side}',
                       [b, b+[-side*.13, 0, 0], a+(b-a)*.73], .006, frame)
        # Short bolt-on risers independently attach the existing tubular
        # guard. The recovery crossmember, rather than its thin guard tube,
        # carries the forged lug.
        cylinder(f'front.recovery.bumper_riser.{side}', b,
                 (side*.69, .68, 2.19), .024, frame, 12)
        pin = np.array([side*.69, .585, 2.225])
        pins.append(pin.tolist())
        # One 20 mm vertical YZ lug between the shackle eyes. Its neck is
        # welded through the carrier face; the bore is genuinely annular.
        arc = [[.040*math.cos(a), .040*math.sin(a)]
               for a in np.linspace(-math.pi/2, math.pi/2, 25)]
        outline = np.asarray([[-.17, -.055]]+arc+[[-.17, .055]])
        outer = _ray_polygon_perimeter(outline)
        _annular_sheet(model, f'front.recovery.welded_pin_lug.{side}', pin,
                       [0, 0, 1], [0, 1, 0], outer, .0126, .020, frame,
                       outer_edges=range(len(outer)))
        for cheek in [-1, 1]:
            x = pin[0]+cheek*.018
            _solid_polygon(model, f'front.recovery.lug_neck_gusset.{side}.{cheek}',
                           [(x, .548, 2.055), (x, .622, 2.055),
                            (x, .585, 2.164)], .006, frame)
            polyline(f'front.recovery.lug_neck_weld.{side}.{cheek}',
                     [(x, .55, 2.055), (x, .62, 2.055)], .0028, alloy, 8)
        _forged_bow(model, f'front.recovery.shackle.{side}', pin, powder)
        for eye in [-1, 1]:
            _forged_eye(model, f'front.recovery.shackle_eye.{side}.{eye}',
                        pin+[eye*.0345, 0, 0], [1, 0, 0], .0295,
                        .0123, .027, powder)
            _forged_eye(model, f'front.recovery.lug_pin_spacer.{side}.{eye}',
                        pin+[eye*.0155, 0, 0], [1, 0, 0], .020,
                        .0119, .009, pin_finish)
        cylinder(f'front.recovery.shackle_pin.{side}', pin+[-.065, 0, 0],
                 pin+[.077, 0, 0], .0115, pin_finish, 24)
        cylinder(f'front.recovery.pin_hex_head.{side}', pin+[-.064, 0, 0],
                 pin+[-.049, 0, 0], .021, pin_finish, 6)
        # A real annular washer sits under the retaining nut. Narrow thread
        # ridges belong only to the exposed pin, never to the red bow form.
        _forged_eye(model, f'front.recovery.pin_washer.{side}',
                    pin+[.050, 0, 0], [1, 0, 0], .019, .0118, .003,
                    pin_finish)
        cylinder(f'front.recovery.pin_retaining_hex_nut.{side}',
                 pin+[.052, 0, 0], pin+[.067, 0, 0], .021, pin_finish, 6)
        for thread in range(3):
            torus(f'front.recovery.exposed_pin_thread.{side}.{thread}',
                  pin+[.069+thread*.002, 0, 0], .0116, .00075,
                  pin_finish, (1, 0, 0), 24, 4)
        for segment, (clip_a, clip_b) in enumerate([([.075, -.014, -.004], [.075, .015, 0]),
                                                    ([.075, .015, 0], [.075, .007, .008])]):
            cylinder(f'front.recovery.pin_split_retainer.{side}.{segment}',
                     pin+clip_a, pin+clip_b, .0018, pin_finish, 8)
        load_paths.append(dict(rail=a.tolist(), carrier=b.tolist(),
                               welded_lug_neck=[side*.69, .585, 2.055],
                               pin=pin.tolist(), attachment='fixed chassis, not body'))

    # Continuous centreline: flat rear pan, a physical 35 mm bend, inclined
    # perforated kick and a 12 mm leading return. The leading edge rises to
    # preserve approach room rather than hanging as a flat vertical plough.
    radius = .035
    lo, hi = .1, 1.0
    for _ in range(45):
        theta = (lo+hi)/2
        rise = radius*(1-math.cos(theta))+(2.255-1.97-radius*math.sin(theta))*math.tan(theta)
        if rise < .19:
            lo = theta
        else:
            hi = theta
    theta = (lo+hi)/2
    flat_end = np.array([0, .36, 1.97])
    bend_angles = np.linspace(0, theta, 10)
    bend = np.asarray([flat_end+[0, radius*(1-math.cos(a)), radius*math.sin(a)]
                       for a in bend_angles])
    bend_normals = np.asarray([[0, math.cos(a), -math.sin(a)] for a in bend_angles])
    ramp_start = bend[-1]
    ramp_end = np.array([0, .55, 2.255])
    ramp_tangent = _unit(ramp_end-ramp_start)
    ramp_normal = np.array([0, ramp_tangent[2], -ramp_tangent[1]])
    holes = []
    half_width = .55

    def perforated_panel(name, start, end, rows, columns):
        start, end = np.asarray(start), np.asarray(end)
        tangent = _unit(end-start)
        normal = np.cross([1, 0, 0], tangent)
        length = float(np.linalg.norm(end-start))
        for row in range(rows):
            for col in range(columns):
                center = start+tangent*((row+.5)*length/rows)
                center = center+[(col+.5)*half_width*2/columns-half_width, 0, 0]
                outer = _perimeter_rectangle(half_width/columns, length/rows/2)
                # Shared rectangular boundaries are not walls. Only the two
                # physical fore/aft panel ends get a six millimetre edge.
                edges = []
                if row == 0 and name == 'rear_pan':
                    edges.extend(range(0, 6))
                _annular_sheet(model, f'front.skid.{name}.cell.{row}.{col}',
                               center, [1, 0, 0], tangent, outer, .0305,
                               SHEET, alloy, outer_edges=edges)
                holes.append(dict(center=center.tolist(), normal=normal.tolist(),
                                  radius=.0305, panel=name))

    perforated_panel('rear_pan', [0, .36, 1.73], flat_end, 1, 6)
    _bent_strip(model, 'front.skid.rear_to_kick_bend', bend, bend_normals,
                half_width, alloy, end_caps=False)
    perforated_panel('kick_panel', ramp_start, ramp_end, 2, 6)
    nose_angles = np.linspace(theta, 1.39, 10)
    nose_radius = .012
    nose = np.asarray([ramp_end+[0, nose_radius*(math.cos(theta)-math.cos(a)),
                                      nose_radius*(math.sin(a)-math.sin(theta))]
                       for a in nose_angles])
    nose_normals = np.asarray([[0, math.cos(a), -math.sin(a)] for a in nose_angles])
    nose_end = nose[-1]+[0, .026*math.sin(1.39), .026*math.cos(1.39)]
    nose = np.r_[nose, [nose_end]]
    nose_normals = np.r_[nose_normals, [nose_normals[-1]]]
    _bent_strip(model, 'front.skid.leading_folded_return', nose, nose_normals,
                half_width, alloy, end_caps=False)
    # The front lip has its own real six millimetre terminal edge.
    end_n = nose_normals[-1]
    _oriented_mesh(model, 'front.skid.leading_terminal_edge',
                   [nose_end+[-half_width, 0, 0]+end_n*SHEET/2,
                    nose_end+[half_width, 0, 0]+end_n*SHEET/2,
                    nose_end+[half_width, 0, 0]-end_n*SHEET/2,
                    nose_end+[-half_width, 0, 0]-end_n*SHEET/2],
                   [(0, 1, 2), (0, 2, 3)], alloy,
                   [[0, math.sin(1.39), math.cos(1.39)]]*4)
    # Side returns follow every real fold. Their rolled root is tangent to
    # the main sheet and their 65 degree upstand stiffens the complete pan.
    path = np.r_[[[0, .36, 1.73]], bend, [ramp_end], nose[1:]]
    path_n = np.r_[[[0, 1, 0]], bend_normals, [ramp_normal], nose_normals[1:]]
    side_angle = math.radians(65)
    cross_angles = np.linspace(0, side_angle, 7)
    cross_profile = [( .009*math.sin(a), .009*(1-math.cos(a)), a)
                     for a in cross_angles]
    cross_profile.append((cross_profile[-1][0]+.025*math.cos(side_angle),
                          cross_profile[-1][1]+.025*math.sin(side_angle), side_angle))
    for side in [-1, 1]:
        out = np.array([side, 0, 0])
        shells = []
        for skin_side in [-1, 1]:
            points = []
            normals = []
            for point, normal in zip(path, path_n):
                row = []
                row_n = []
                for distance, height, a in cross_profile:
                    fold_n = normal*math.cos(a)-out*math.sin(a)
                    row.append(point+out*(half_width+distance)+normal*height+
                               fold_n*skin_side*SHEET/2)
                    row_n.append(fold_n*skin_side)
                points.append(row)
                normals.append(row_n)
            _quads(model, f'front.skid.side_fold.{side}.skin.{skin_side}',
                   points, normals, alloy)
            shells.append(points)
        edge_points = [[shells[0][i][-1], shells[1][i][-1]] for i in range(len(path))]
        edge_normals = [[_unit(out*math.cos(side_angle)+normal*math.sin(side_angle))]*2
                        for normal in path_n]
        _quads(model, f'front.skid.side_fold.{side}.six_mm_rim',
               edge_points, edge_normals, alloy)
        for end in [0, len(path)-1]:
            points = [shells[0][end], shells[1][end]]
            tangent = _unit(path[1]-path[0]) if end == 0 else _unit(path[-1]-path[-2])
            _quads(model, f'front.skid.side_fold.{side}.end.{end}', points,
                   [[tangent*(-1 if end == 0 else 1)]*len(cross_profile)]*2, alloy)

    # Four service bolts and independent folded brackets connect to the
    # chassis carriers/crossmember. No skid bolt terminates in the white nose.
    mounts = []
    for side in [-1, 1]:
        for front in [False, True]:
            z = 2.128 if front else 1.762
            if front:
                center = ramp_start+ramp_tangent*((z-ramp_start[2])/ramp_tangent[2])
                n = ramp_normal
                anchor = [side*(half_width*2/3), .58, 2.08]
            else:
                center = np.array([0, .36, z])
                n = np.array([0, 1, 0])
                t = (z-1.65)/(2.08-1.65)
                anchor = np.array([side*.38, .34, 1.65])+(np.array([side*.69, .58, 2.08])-
                                                                       [side*.38, .34, 1.65])*t
            center[0] = side*(half_width*2/3)
            foot = center+n*.006
            # These brackets lie alongside two columns, between bores. A
            # broad folded foot can be unbolted without removing the beam.
            tangent = np.cross([1, 0, 0], n)
            _solid_polygon(model, f'front.skid.mount_foot.{side}.{front}',
                           [foot+[-.0325, 0, 0]-tangent*.030,
                            foot+[.0325, 0, 0]-tangent*.030,
                            foot+[.0325, 0, 0]+tangent*.030,
                            foot+[-.0325, 0, 0]+tangent*.030], SHEET, frame)
            anchor = np.asarray(anchor)
            _solid_polygon(model, f'front.skid.folded_chassis_mount_bracket.{side}.{front}',
                           [anchor+[-.028, 0, 0], anchor+[.028, 0, 0],
                            foot+[.028, 0, 0], foot+[-.028, 0, 0]], SHEET, frame)
            cylinder(f'front.skid.service_bolt.{side}.{front}',
                     center-n*.013, center+n*.024, .010, pin_finish, 6)
            _forged_eye(model, f'front.skid.service_washer.{side}.{front}',
                        center-n*.005, n, .017, .0103, .002, alloy)
            mounts.append(dict(sheet=center.tolist(), chassis=np.asarray(anchor).tolist(),
                               removable_bolt=True))

    parts = model.parts[first:]
    all_points = np.concatenate([part['p'] for part in parts])
    skid_points = np.concatenate([part['p'] for part in parts
                                  if part['name'].startswith('front.skid.')])
    # Metadata is descriptive proof of construction, not a dynamic acceptance
    # result. The parent still runs the unchanged actual-tyre/coilover sweep.
    return dict(parts=len(parts), triangles=sum(len(p['f']) for p in parts),
                coordinateFrame='actual chassis metres; call after legacy front translation',
                bounds=dict(min=all_points.min(0).tolist(), max=all_points.max(0).tolist()),
                railAnchors=anchors, recoveryLoadPaths=load_paths,
                shackle=dict(pinCenters=pins, pinAxis=[1, 0, 0], pinRadius=.0115,
                             eyeBoreRadius=.0123, centralLugBoreRadius=.0126,
                             centralLugThickness=.020, eyeThickness=.027,
                             form='open forged U plus two annular eyes, transverse pin, washer and retaining nut',
                             stowedBowPlane='XY; rotates around X pin for a pull',
                             coating='dielectric red powder coat over steel; exposed satin metal pin'),
                skid=dict(sheetThickness=SHEET, perforations=holes, openHoleCount=len(holes),
                          holeWalls=True, centroidFaceMask=False,
                          rearCenter=[0, .36, 1.73], leadingKick=ramp_end.tolist(),
                          leadingReturn=nose_end.tolist(), rearBendRadius=radius,
                          sideFoldDegrees=65, foldedSideHeight=cross_profile[-1][1],
                          mounts=mounts,
                          bounds=dict(min=skid_points.min(0).tolist(), max=skid_points.max(0).tolist())),
                unchanged='headlamps, auxiliary lamps, cabin, rear assembly, vehicle/tyre specification',
                limits='Original game geometry; no load rating, stress certification or full moving-suspension acceptance claimed.')
