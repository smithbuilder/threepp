"""Seated OE-style mirrors inside the original Safari housing ellipsoids.

CPU geometry only. The existing generator retains its unchanged mirror.stalk
cylinders; this module replaces only its closed ivory housing ellipsoids.
The insert uses ordinary opaque metallic PBR and the existing scene probe.
There are no maps, render targets, scene cameras or renderer modifications.
"""
from __future__ import annotations

import copy
import hashlib
import math
from pathlib import Path

import numpy as np


RADII = np.array([.13, .075, .08])
DRIVER_EYE = np.array([-.4, 1.43, -.3])
SEGMENTS = 28
SHELL_RINGS = 6
SHELL_WALL = .002
CUT_FRACTION = .64
INSERT_SCALE = .97
INSERT_RECESS = .0015
INSERT_BOW = .001
INSERT_THICKNESS = .002


def _unit(value):
    value = np.asarray(value, float)
    return value / np.linalg.norm(value)


def _section(radii, normal, offset):
    """Exact ellipsoid/plane intersection, parameterized by a unit circle."""
    support = np.linalg.norm(radii * normal)
    axis = radii * normal / support
    tangent = _unit(np.cross([0., 1., 0.], axis))
    other = np.cross(axis, tangent)
    centre = radii**2 * normal * offset / support**2
    extent = math.sqrt(1 - (offset / support)**2)
    transform = radii[:, None] * np.c_[tangent, other] * extent
    return centre, transform, axis, tangent, other


def _mesh(model, name, positions, normals, faces, material):
    """Preserve analytic normals; orient every triangle toward its solid side."""
    positions = np.asarray(positions, float)
    normals = np.asarray(normals, float)
    oriented = []
    for face in faces:
        a, b, c = face
        cross = np.cross(positions[b] - positions[a], positions[c] - positions[a])
        if cross @ normals[list(face)].sum(0) < 0:
            face = tuple(reversed(face))
        oriented.append(face)
    model.mesh(name, positions, oriented, material, normals=normals)


def _housing(model, name, centre, normal, offset, material):
    """Closed 2 mm shell: outer ellipsoid, inner cavity and actual cut rim."""
    positions = []; normals = []; faces = []; boundaries = []
    for inner, radii in ((False, RADII), (True, RADII - SHELL_WALL)):
        _, _, axis, tangent, other = _section(radii, normal, offset)
        start = len(positions)
        positions.append(centre - radii * axis)
        normals.append(_unit((-axis / radii) * (-1 if inner else 1)))
        cut_angle = math.acos(offset / np.linalg.norm(radii * normal))
        for phi in np.linspace(math.pi, cut_angle, SHELL_RINGS + 1)[1:]:
            for j in range(SEGMENTS):
                theta = math.tau * j / SEGMENTS
                unit = axis * math.cos(phi) + math.sin(phi) * (
                    tangent * math.cos(theta) + other * math.sin(theta))
                positions.append(centre + radii * unit)
                normals.append(_unit((unit / radii) * (-1 if inner else 1)))
        for j in range(SEGMENTS):
            faces.append((start, start + 1 + j, start + 1 + (j + 1) % SEGMENTS))
        for ring in range(SHELL_RINGS - 1):
            a = start + 1 + ring * SEGMENTS
            b = a + SEGMENTS
            for j in range(SEGMENTS):
                k = (j + 1) % SEGMENTS
                faces.extend(((a + j, b + j, a + k), (a + k, b + j, b + k)))
        boundaries.append(np.asarray(positions[-SEGMENTS:]))
    # Separate rim vertices retain the real hard edge at the cut aperture.
    start = len(positions)
    for boundary in boundaries:
        positions.extend(boundary)
        normals.extend([normal] * SEGMENTS)
    for j in range(SEGMENTS):
        k = (j + 1) % SEGMENTS
        faces.extend(((start + j, start + SEGMENTS + j, start + k),
                      (start + k, start + SEGMENTS + j, start + SEGMENTS + k)))
    _mesh(model, name, positions, normals, faces, material)


def _gasket(model, name, centre, transform, normal, material):
    """Closed moulded lip, intentionally wrapping the insert and shell seat."""
    positions = []; normals = []; faces = []; cross_segments = 8
    for j in range(SEGMENTS):
        theta = math.tau * j / SEGMENTS
        radial = np.array([math.cos(theta), math.sin(theta)])
        tangent = np.array([-math.sin(theta), math.cos(theta)])
        for k in range(cross_segments):
            phi = math.tau * k / cross_segments
            scale = .98 + .022 * math.cos(phi)
            depth = -.0014 + .0014 * math.sin(phi)
            positions.append(centre + transform @ (scale * radial) + normal * depth)
            dt = transform @ (scale * tangent)
            dp = transform @ (-.022 * math.sin(phi) * radial) + normal * .0014 * math.cos(phi)
            normals.append(_unit(np.cross(dt, dp)))
            a = j * cross_segments + k
            b = ((j + 1) % SEGMENTS) * cross_segments + k
            c = j * cross_segments + (k + 1) % cross_segments
            d = ((j + 1) % SEGMENTS) * cross_segments + (k + 1) % cross_segments
            faces.extend(((a, b, c), (b, d, c)))
    _mesh(model, name, positions, normals, faces, material)


def _insert(model, name, centre, transform, normal, material):
    """Closed silvered insert with a 1 mm convex face and a 2 mm edge."""
    transform = transform * INSERT_SCALE
    centre = centre - normal * INSERT_RECESS
    positions = [centre + normal * INSERT_BOW]; normals = [normal]; faces = []
    for radius in np.linspace(.25, 1., 4):
        for j in range(SEGMENTS):
            theta = math.tau * j / SEGMENTS
            u, v = radius * math.cos(theta), radius * math.sin(theta)
            positions.append(centre + transform @ [u, v] + normal * INSERT_BOW * (1 - radius**2))
            du = transform[:, 0] - normal * 2 * INSERT_BOW * u
            dv = transform[:, 1] - normal * 2 * INSERT_BOW * v
            normals.append(_unit(np.cross(du, dv)))
    for j in range(SEGMENTS):
        faces.append((0, 1 + j, 1 + (j + 1) % SEGMENTS))
    for ring in range(3):
        a = 1 + ring * SEGMENTS; b = a + SEGMENTS
        for j in range(SEGMENTS):
            k = (j + 1) % SEGMENTS
            faces.extend(((a + j, b + j, a + k), (a + k, b + j, b + k)))
    # Side and back are real geometry, with hard edge normals, hidden in the
    # rubber seat rather than a floating reflective disc over a closed sphere.
    start = len(positions)
    for depth in (0., -INSERT_THICKNESS):
        for j in range(SEGMENTS):
            theta = math.tau * j / SEGMENTS
            radial = np.array([math.cos(theta), math.sin(theta)])
            tangent = transform @ [-math.sin(theta), math.cos(theta)]
            positions.append(centre + transform @ radial + normal * depth)
            normals.append(_unit(np.cross(tangent, normal)))
    for j in range(SEGMENTS):
        k = (j + 1) % SEGMENTS
        faces.extend(((start + j, start + SEGMENTS + j, start + k),
                      (start + k, start + SEGMENTS + j, start + SEGMENTS + k)))
    back = len(positions)
    positions.append(centre - normal * INSERT_THICKNESS); normals.append(-normal)
    for j in range(SEGMENTS):
        theta = math.tau * j / SEGMENTS
        positions.append(centre + transform @ [math.cos(theta), math.sin(theta)] - normal * INSERT_THICKNESS)
        normals.append(-normal)
    for j in range(SEGMENTS):
        faces.append((back, back + 1 + j, back + 1 + (j + 1) % SEGMENTS))
    _mesh(model, name, positions, normals, faces, material)


def build_mirrors(model, materials, source_primitives=None):
    """Append both mirror heads; retain the generator's original stalk loop.

    Required material keys are paint/rubber/metal. source_primitives is accepted
    for the shared authoring API but no primitive or renderer is required.
    Each silvered insert reflects the existing environment probe only.
    """
    for key in ('paint', 'rubber', 'metal'):
        if key not in materials:
            raise ValueError('Safari mirrors require material ' + key)
    mirror = copy.deepcopy(model.materials[materials['metal']])
    mirror.update(name='safari.mirror_silvered_insert', doubleSided=False, alphaMode='OPAQUE')
    mirror['pbrMetallicRoughness'] = dict(baseColorFactor=[.88, .90, .88, 1.],
                                       roughnessFactor=.06, metallicFactor=1.)
    for key in ('normalTexture', 'occlusionTexture', 'emissiveTexture', 'emissiveFactor', 'extensions'):
        mirror.pop(key, None)
    insert_material = len(model.materials); model.materials.append(mirror)
    first = len(model.parts); records = []
    for side in (-1, 1):
        centre = np.array([side * 1.035, 1.40, .44])
        # The normal bisects the driver ray and the rearward scene direction.
        # Looking directly at the eye would reflect the driver at themselves.
        normal = _unit(_unit(DRIVER_EYE - centre) + [0., 0., -1.])
        for _ in range(5):
            offset = CUT_FRACTION * np.linalg.norm(RADII * normal)
            aperture, _, _, _, _ = _section(RADII - SHELL_WALL, normal, offset)
            face_centre = centre + aperture + normal * (INSERT_BOW - INSERT_RECESS)
            normal = _unit(_unit(DRIVER_EYE - face_centre) + [0., 0., -1.])
        offset = CUT_FRACTION * np.linalg.norm(RADII * normal)
        aperture, transform, _, _, _ = _section(RADII - SHELL_WALL, normal, offset)
        aperture_centre = centre + aperture
        _housing(model, f'mirror.housing.{side}', centre, normal, offset, materials['paint'])
        _gasket(model, f'mirror.gasket.{side}', aperture_centre, transform, normal, materials['rubber'])
        _insert(model, f'mirror.insert.{side}', aperture_centre, transform, normal, insert_material)
        face_centre = aperture_centre + normal * (INSERT_BOW - INSERT_RECESS)
        view = _unit(DRIVER_EYE - face_centre)
        reflected = -view + 2 * (normal @ view) * normal
        records.append(dict(side=side, legacyCentre=centre.tolist(), legacyRadii=RADII.tolist(),
                            cutPlaneNormal=normal.tolist(), cutPlaneOffset=float(offset),
                            apertureCentre=aperture_centre.tolist(), apertureTransform=transform.tolist(),
                            insertFaceCentre=face_centre.tolist(), driverFacingCosine=float(normal @ view),
                            reflectedCentreDirection=reflected.tolist(), shellWall=SHELL_WALL,
                            insertBow=INSERT_BOW, insertThickness=INSERT_THICKNESS,
                            insertRecess=INSERT_RECESS, insertApertureScale=INSERT_SCALE,
                            stalkStart=[side*.88, 1.31, .48], stalkEnd=[side*1.02, 1.37, .45],
                            stalkRadius=.018))
    return dict(parts=len(model.parts)-first, mirrors=records, stalksOwned=False,
                replaces='only the two legacy mirror.housing ellipsoids',
                source='scripts/safari_mirrors.py',
                sourceSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                reflection='existing scene environment; no scene-camera reflection',
                limits='Finite shell/insert fit and view direction; no physical mirror visibility certification.')
