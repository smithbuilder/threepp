"""Physical, CPU-authored optics for the original Cinder Safari.

The helpers only append geometry/materials to the supplied authoring model.
There is no renderer, transmission extension, image processing or GLB write.
Lamp origins, radii and the existing rear aperture remain authoritative.
"""
from __future__ import annotations

import math
import numpy as np

TAU = math.tau


def configure_optics_materials(model, materials):
    """Set ordinary glTF PBR finishes once; return the augmented material map.

    The headlamp is real bare aluminium, not a diffuse luminous disc.  A
    modestly rough pressed surface broadens reflected light.  Black diffuse
    glass avoids adding an opaque grey veil in this alpha-only renderer.
    Rear colour comes from coated satin reflector chambers behind a separate
    smooth clear cover.  No optical layer is emissive.
    """
    result = dict(materials)
    reflector = model.materials[result['reflector']]['pbrMetallicRoughness']
    reflector.update(roughnessFactor=.29, metallicFactor=1.0)
    clear = model.materials[result['lens']]
    clear['pbrMetallicRoughness'].update(baseColorFactor=[0., 0., 0., .16],
                                      roughnessFactor=.065, metallicFactor=0.)
    clear.update(alphaMode='BLEND', doubleSided=True)
    for key in ('tail', 'amber'):
        model.materials[result[key]]['pbrMetallicRoughness']['roughnessFactor'] = .20
    result['lens_edge'] = model.mat('safari.lamp_glass_cut_edge', 0x677471, .20, 0, .34)
    # These are the BACK interfaces of the existing clear covers. Runtime
    # thin-glass opt-in uses bulk transmission 1.0 here: the outer cover owns
    # the .96 bulk factor, so absorption is not counted again. Each interface
    # contributes its own unattenuated PBR Fresnel reflection (F0=.04).
    result['inner_glass'] = model.mat('safari.headlamp_internal_prism_glass', 0x000000, .09, 0, .04)
    result['rear_cover'] = model.mat('safari.rear_optical_cover', 0x000000, .075, 0, .16)
    model.materials[result['rear_cover']]['doubleSided'] = False
    result['rear_inner_glass'] = model.mat('safari.rear_internal_prism_glass', 0x000000, .095, 0, .04)
    result['red_reflector'] = model.mat('safari.red_coated_satin_reflector', 0xa72b21, .28, .72)
    result['amber_reflector'] = model.mat('safari.amber_coated_satin_reflector', 0xc38324, .30, .60)
    # Etching scatters a small fraction of daylight from selected internal
    # prism flanks.  This is not a grey alpha veil covering the whole lens.
    result['etched_glass'] = model.mat('safari.etched_inner_prism_scatter', 0xb8c1bd, .34, 0, .30)
    result['red_scatter'] = model.mat('safari.red_inner_prism_scatter', 0x9b3b30, .32, 0, .30)
    result['amber_scatter'] = model.mat('safari.amber_inner_prism_scatter', 0xb78c46, .33, 0, .30)
    for key in ('etched_glass','red_scatter','amber_scatter'):
        model.materials[result[key]]['doubleSided'] = False
    result['socket'] = model.mat('safari.lamp_ceramic_socket', 0x878477, .66, 0)
    result['satin'] = model.mat('safari.lamp_satin_aluminium', 0xbfc3bf, .32, 1)
    result['garnish'] = model.mat('safari.rear_deep_red_garnish', 0x591613, .27, 0)
    result['red_edge'] = model.mat('safari.tail_lens_moulded_edge', 0x481410, .25, 0)
    result['amber_edge'] = model.mat('safari.amber_lens_moulded_edge', 0x593509, .25, 0)
    for key in ('garnish', 'red_edge', 'amber_edge'):
        model.materials[result[key]]['extensions'] = {
            'KHR_materials_clearcoat': {'clearcoatFactor': .65, 'clearcoatRoughnessFactor': .10}}
    return result


def _lathe(model, name, origin, profile, material, segments=64, flip=False):
    """Revolve (radius, axial offset) pairs, with shared smooth azimuth seams.

    Consecutive profile rows determine the normal direction.  Inward-to-outward
    gives the forward-facing bowl normal; a back-to-front exterior barrel uses
    ``flip=True``.  End faces are authored separately, never by
    a cylinder cap covering an optical opening.
    """
    origin = np.asarray(origin, float)
    angles = np.linspace(0, TAU, segments+1)
    points = [[origin + [radius*math.cos(a), radius*math.sin(a), depth]
               for a in angles] for radius, depth in profile]
    model.grid(name, points, material, flip=flip)


def _front_surface(model, name, center, radius, material, height, rings=18, segments=96):
    """A round front surface with analytic normals and one true centre vertex."""
    center = np.asarray(center, float)
    points = [center + [0., 0., height(0., 0.)]]
    normals = [np.array([0., 0., 1.])]
    uv = [(.5, .5)]
    for k in range(1, rings+1):
        rr = radius*k/rings
        for j in range(segments+1):
            a = 0. if j == segments else TAU*j/segments
            xx, yy = rr*math.cos(a), rr*math.sin(a)
            points.append(center + [xx, yy, height(xx, yy)])
            epsilon = radius*.0001
            dx = (height(xx+epsilon, yy)-height(xx-epsilon, yy))/(2*epsilon)
            dy = (height(xx, yy+epsilon)-height(xx, yy-epsilon))/(2*epsilon)
            n = np.array([-dx, -dy, 1.]); normals.append(n/np.linalg.norm(n))
            uv.append((.5+xx/(2*radius), .5+yy/(2*radius)))
    faces = [(0, 1+j, 2+j) for j in range(segments)]
    for k in range(rings-1):
        for j in range(segments):
            a = 1+k*(segments+1)+j; b = a+1; c = a+segments+1; d = c+1
            faces.extend([(a, c, b), (b, c, d)])
    model.mesh(name, points, faces, material, uv, normals=normals)


def _fluted_glass(model, name, origin, radius, material, inner_material, scatter):
    """Smooth 3 mm-bowed cover, with pressed flutes on its INSIDE face only.

    The 2.2 mm lens wall has one smooth external interface.  Broad directional
    prism slopes project backwards into the chamber and retain their real
    creases.  They never turn the exterior into a corrugated metal-like face.
    """
    origin = np.asarray(origin, float)
    lens_radius = radius*.923
    dome = .003
    edge = radius*.069
    thickness = .0022
    pitch = lens_radius*2/13
    # Actual pressed relief, independent of the housing radius. Three adjacent
    # optical zones spread progressively farther across the lower beam. The
    # upper clear-sector cutoff rises gently across the lens; this is an
    # asymmetric optical mould, not a repeated rectangular surface grid.
    zone_relief = (.0012, .0015, .0018)

    def sag(xx, yy):
        return edge+dome*(1-(xx*xx+yy*yy)/(lens_radius*lens_radius))

    _front_surface(model, name+'.smooth_outer_cover', origin, lens_radius, material,
                   sag, rings=18, segments=96)
    # Horizontal stations split the rounded edge, upper clear sector and lower
    # spread-beam sector.  They are surface samples, not a rectangular rib grid.
    for strip in range(13):
        xa = -lens_radius+strip*pitch
        xb = xa+pitch
        amplitude = zone_relief[0 if strip < 4 else 1 if strip < 8 else 2]
        for half, (left, right, rising) in enumerate(((xa, (xa+xb)*.5, True),
                                                     ((xa+xb)*.5, xb, False))):
            rows=[];normal_rows=[]
            for xx in np.linspace(left, right, 3):
                extent = math.sqrt(max(0., lens_radius*lens_radius-xx*xx))
                row=[];normal_row=[]
                phase = (xx-xa)/pitch
                prism = amplitude*(1-abs(phase*2-1))
                prism_dx = (2 if rising else -2)*amplitude/pitch
                for t in np.linspace(-1, 1, 25):
                    yy = t*extent
                    # Broad lower beam-spreading flutes fade before the upper
                    # clear sector and at the lens's pressed perimeter.
                    spread = (.52+.18*xx/lens_radius-yy/lens_radius)/.25
                    fade = np.clip(spread, 0, 1)
                    fade_dx = .18/(lens_radius*.25) if 0 < spread < 1 else 0.
                    fade_dy = -1/(lens_radius*.25) if 0 < spread < 1 else 0.
                    radial = 8*(1-(xx*xx+yy*yy)/(lens_radius*lens_radius))
                    edge_fade = np.clip(radial, 0, 1)
                    edge_dx = -16*xx/lens_radius**2 if 0 < radial < 1 else 0.
                    edge_dy = -16*yy/lens_radius**2 if 0 < radial < 1 else 0.
                    row.append(origin+[xx, yy, sag(xx, yy)-thickness-prism*fade*edge_fade])
                    dx = -2*dome*xx/lens_radius**2-(prism_dx*fade*edge_fade
                         +prism*fade_dx*edge_fade+prism*fade*edge_dx)
                    dy = -2*dome*yy/lens_radius**2-prism*(fade_dy*edge_fade+fade*edge_dy)
                    normal=np.array([-dx,-dy,1.]);normal_row.append(normal/np.linalg.norm(normal))
                rows.append(row);normal_rows.append(normal_row)
            # A sparse set of one-flank, lower-beam etched zones scatters
            # daylight.  The thin scattering sheet faces the observer (+Z)
            # once; clear inner interfaces retain their physical -Z normal.
            points=np.asarray(rows).reshape(-1,3);normals=np.asarray(normal_rows).reshape(-1,3)
            clear_faces=[];etched_faces=[]
            for i in range(2):
                for j in range(24):
                    a=i*25+j;b=a+1;c=a+25;d=c+1
                    for face in ((a,c,b),(b,c,d)):
                        yy=points[list(face),1].mean()-origin[1]
                        etched=(strip%3!=1 and half==0 and -.78<yy/lens_radius<.38)
                        (etched_faces if etched else clear_faces).append(face)
            if clear_faces:
                model.mesh(name+f'.internal_moulded_prism.{strip}.{half}',points,
                           [f[::-1] for f in clear_faces],inner_material,normals=-normals)
            if etched_faces:
                model.mesh(name+f'.etched_internal_flank.{strip}.{half}',points,
                           etched_faces,scatter,normals=normals)
    _lathe(model, name+'.perimeter_thickness', origin,
           [(lens_radius, edge-thickness), (lens_radius, edge)], material, 96, flip=True)
    # The narrow pressed perimeter is visibly ground, like a real sealed-beam
    # mould seam.  It remains behind the smooth cover and occupies only 5%.
    _lathe(model,name+'.ground_internal_perimeter',origin,
           [(radius*.894,sag(radius*.894,0)-thickness-.00015),
            (radius*.918,sag(radius*.918,0)-thickness-.00015)],scatter,96)
    return lens_radius, edge+dome


def build_spotlight(model, primitives, materials, name, x, y, z, radius,
                    guard=False, tilt=0):
    """Append one open reflector/bulb/pressed-glass assembly at an existing seat.

    ``primitives`` provides box/cylinder/ellipsoid/torus/polyline.  Its methods
    already target ``model``.  Maximum radial extent is 1.05*radius and the
    axial envelope [-.80r, +.45r] fits the pre-existing main lamp aperture.
    """
    cylinder = primitives['cylinder']; torus = primitives['torus']
    ellipsoid = primitives['ellipsoid']; polyline = primitives['polyline']
    black = materials['black']; rubber = materials.get('rubber', black)
    reflector = materials['reflector']; glass = materials['lens']
    satin = materials.get('satin', reflector)
    first = len(model.parts); origin = np.array([x, y, z], float); r = radius

    # The rolled black case is open at the front.  Its tapered rear dish and
    # the retaining flange are genuinely separate from the optical bowl.
    _lathe(model, name+'.pressed_housing', origin,
           [(r*.38, -r*.80), (r*.65, -r*.76), (r*.94, -r*.49),
            (r*1.015, -r*.19), (r*1.015, r*.012)], black, 48, flip=True)
    back_center=origin+[0,0,-r*.80]
    back_ring=[back_center+[r*.38*math.cos(a),r*.38*math.sin(a),0]
               for a in np.linspace(0,TAU,49)]
    model.mesh(name+'.flat_housing_rear_closure',[back_center]+back_ring,
               [(0,j+2,j+1) for j in range(48)],black,
               normals=np.tile([0.,0.,-1.],(50,1)))
    torus(name+'.sealing_gasket', origin+[0,0,r*.018], r*1.01, r*.039,
          rubber, (0,0,1), 48, 10)
    # A wide, shallow bevel catches the sky while the small rolled lip catches
    # direct highlights.  Neither is a disk across the opening.
    _lathe(model, name+'.stamped_retaining_bezel', origin,
           [(r*.924, r*.082), (r*.946, r*.067), (r*.990, r*.040),
            (r*1.007, r*.013)], satin, 64)
    torus(name+'.rolled_chrome_retaining_lip', origin+[0,0,r*.062], r*.948,
          r*.016, reflector, (0,0,1), 48, 8)
    _lathe(model, name+'.recessed_dark_inner_reveal', origin,
           [(r*.915, -r*.035), (r*.926, r*.063)], black, 48)

    # A 0.64r-deep paraboloid with 24 shallow pressed sectors. The geometric
    # envelope is unchanged, but exact derivatives of that continuous mould
    # replace independent triangle averages. Sector boundaries have one normal
    # rather than a spurious 3--7 degree radial shading crease.
    for sector in range(24):
        rows=[];normal_rows=[]
        for t in [.10,.18,.28,.40,.53,.67,.81,.92,1.]:
            row=[];normal_row=[]
            for phase in np.linspace(0,1,4):
                angle=((sector+phase)%24)*TAU/24
                rr=r*.911*t
                depth=-r*.64*(1-t*t)
                pressed=math.sin(phase*math.pi)**2 if 0 < phase < 1 else 0.
                pressed_slope=12*math.sin(phase*TAU) if 0 < phase < 1 else 0.
                stamp=-r*.009*pressed*t*(1-.55*t)
                row.append(origin+[rr*math.cos(angle),rr*math.sin(angle),depth+stamp])
                radial_slope=(1.28*t-.009*pressed*(1-1.10*t))/.911
                angular_slope=-.009*pressed_slope*(1-.55*t)/.911
                dx=radial_slope*math.cos(angle)-angular_slope*math.sin(angle)
                dy=radial_slope*math.sin(angle)+angular_slope*math.cos(angle)
                normal=np.array([-dx,-dy,1.]);normal_row.append(normal/np.linalg.norm(normal))
            rows.append(row);normal_rows.append(normal_row)
        faces=[]
        for i in range(len(rows)-1):
            for j in range(3):
                a=i*4+j;b=a+1;c=a+4;d=c+1
                faces.extend([(a,c,b),(b,c,d)])
        model.mesh(name+f'.parabolic_aluminium_sector.{sector}',np.asarray(rows).reshape(-1,3),
                   faces,reflector,normals=np.asarray(normal_rows).reshape(-1,3))
    # A dark opening and ceramic neck ground the bulb in the deepest area.
    cylinder(name+'.socket_bore', origin+[0,0,-r*.66], origin+[0,0,-r*.58],
             r*.105, black, 28)
    cylinder(name+'.ceramic_bulb_neck', origin+[0,0,-r*.58], origin+[0,0,-r*.31],
             r*.070, materials.get('socket', satin), 24)
    # Paraboloid z=-.64r+rho^2/(4f), f=(.911r)^2/(4*.64r).
    # The finite bulb and its real coil share that focus. Its front stays
    # behind the anti-dazzle shade, while the neck remains inserted inside.
    focus = r*(-.64+.911**2/(4*.64))
    ellipsoid(name+'.halogen_bulb_envelope', origin+[0,0,focus],
              (r*.087,r*.105,r*.16), glass, 24, 12)
    # A small real metal bulb shade blocks the direct halogen filament.  Its
    # 0.22r diameter leaves the rest of the deep reflector clearly exposed.
    _lathe(model, name+'.bulb_anti_dazzle_shade', origin,
           [(r*.070,-r*.13),(r*.105,-r*.10),(r*.112,-r*.047),
            (r*.095,-r*.015),(r*.055,r*.007),(r*.008,r*.012)], satin, 32, flip=True)
    ellipsoid(name+'.shade_closed_nose', origin+[0,0,r*.009],
              (r*.057,r*.057,r*.015), satin, 24, 10)
    for side in (-1,1):
        polyline(name+f'.bulb_shade_support.{side}',
                 [origin+[side*r*.082,-r*.023,-r*.065],
                  origin+[side*r*.22,-r*.12,-r*.18],
                  origin+[side*r*.54,-r*.44,-r*.32]], r*.0095, satin, 7)
    # Retain a physically small warm coil inside the bulb, shielded head-on.
    if 'filament' in materials:
        coil=[]
        for t in np.linspace(0,1,37):
            a=t*TAU*4
            coil.append(origin+[r*(t-.5)*.067,r*.007*math.cos(a),focus+r*.007*math.sin(a)])
        polyline(name+'.shielded_tungsten_coil', coil, r*.0024, materials['filament'], 5)

    _fluted_glass(model, name+'.convex_pressed_glass', origin, r, glass,
                  materials.get('inner_glass',glass),materials.get('etched_glass',glass))
    # The moulded perimeter has a separate cut edge; not another opaque disc.
    torus(name+'.thick_cut_glass_edge', origin+[0,0,r*.065], r*.922, r*.009,
          materials.get('lens_edge',glass), (0,0,1), 80, 6)
    for j, angle in enumerate((math.radians(-90),math.radians(30),math.radians(150))):
        xx,yy = r*.982*math.cos(angle),r*.982*math.sin(angle)
        cylinder(name+f'.bezel_retaining_screw.{j}', origin+[xx,yy,r*.037],
                 origin+[xx,yy,r*.055],r*.016,satin,10)
        # A narrow slot in each screw is actual geometry, not a decal.
        a=origin+[xx-r*.010,yy,r*.0553]; b=origin+[xx+r*.010,yy,r*.0553]
        cylinder(name+f'.bezel_screw_slot.{j}',a,b,r*.0024,black,5)
    if guard:
        torus(name+'.guard_outer_wire',origin+[0,0,r*.333],r*.961,r*.024,
              black,(0,0,1),64,8)
        for j,t in enumerate((-.47,0,.47)):
            extent=math.sqrt(.94**2-t*t)*r
            # A slight bow protects the glass rather than lying on its face.
            for vertical in (False,True):
                points=[]
                for s in np.linspace(-1,1,15):
                    v=s*extent; depth=r*(.335+.035*(1-s*s))
                    points.append(origin+([t*r,v,depth] if vertical else [v,t*r,depth]))
                polyline(name+f'.bowed_guard_{"vertical" if vertical else "horizontal"}.{j}',
                         points,r*.026,black,8)
    if tilt:
        c=math.cos(tilt);s=math.sin(tilt)
        rotation=np.array([[1,0,0],[0,c,s],[0,-s,c]])
        for part in model.parts[first:]:
            part['p']=(part['p']-origin)@rotation.T+origin
            part['n']=part['n']@rotation.T
    return dict(radius=r, radial_envelope=r*1.05, depth=r*.80,
                cover_bow=.003,cover_wall=.0022,prisms_inside=True,
                parts=len(model.parts)-first)


def _rear_lens(model, name, bounds, front_z, cover, inner_glass, reflector, pattern,
               scatter=None,cut_edge=None):
    """A smooth clear mould over internal prisms and a separate coloured bowl.

    Exterior bow is 3 mm, wall thickness is 2.5 mm, and prism relief projects
    into the chamber from the rear face.  The coloured satin-metal reflector
    is another 14.5--38.5 mm behind that rear interface.  Ordinary alpha does
    not simulate coloured transmission, so colour is authored in that coated
    reflector rather than painted onto the smooth transparent front cover.
    """
    x0,x1,y0,y1=bounds;cx=(x0+x1)*.5;cy=(y0+y1)*.5
    rx=(x1-x0)*.5;ry=(y1-y0)*.5
    def rounded(u,v):
        # Superellipse follows the radius of a moulded rectangular lens.
        a=math.atan2(v,u);r=max(abs(u),abs(v))
        exponent=7.
        divisor=(abs(math.cos(a))**exponent+abs(math.sin(a))**exponent)**(1/exponent)
        return r*math.cos(a)/divisor,r*math.sin(a)/divisor
    bow=.003;thickness=.0025
    def point_from_fraction(xx,yy,layer='cover',relief=0.):
        shape=(1-xx*xx)*(1-yy*yy)
        if layer=='reflector':
            # A deep concave chamber, facing rearwards (-Z), not a coloured
            # opaque plaque immediately under the transparent front surface.
            zz=front_z+.017+.021*shape+relief
        else:
            zz=front_z-bow*shape+(thickness+relief if layer=='inner' else 0.)
        return np.array([cx+rx*xx,cy+ry*yy,zz])
    def surface(u,v,layer='cover',relief=0.):
        return point_from_fraction(*rounded(u,v),layer,relief)
    def ring_point(rr,angle,layer='inner',relief=0.):
        ca,sa=math.cos(angle),math.sin(angle)
        exponent=7.
        divisor=(abs(ca)**exponent+abs(sa)**exponent)**(1/exponent)
        # True ellipse at the central optical zones, gently morphing into the
        # rectangular mould at its edge.  Every ring shares the outer seam.
        blend=np.clip((rr-.68)/.32,0,1)
        extent=rr*(1+blend*(1/divisor-1))
        return point_from_fraction(extent*ca,extent*sa,layer,relief)

    # One continuous smooth external surface, with analytic outward normals.
    points=[];normals=[];uv=[];faces=[];rows=19;cols=31
    for i,u in enumerate(np.linspace(-1,1,cols)):
        for j,v in enumerate(np.linspace(-1,1,rows)):
            xx,yy=rounded(u,v);points.append(point_from_fraction(xx,yy));uv.append(((u+1)*.5,(v+1)*.5))
            dx=2*bow*xx/rx*(1-yy*yy);dy=2*bow*yy/ry*(1-xx*xx)
            normal=np.array([dx,dy,-1.]);normals.append(normal/np.linalg.norm(normal))
            if i<cols-1 and j<rows-1:
                a=i*rows+j;b=a+1;c=a+rows;d=c+1
                faces.extend([(a,b,c),(b,d,c)])
    model.mesh(name+'.smooth_outer_cover',points,faces,cover,uv,normals=normals)

    # Recessed Fresnel bands belong to the INSIDE glass interface.  Their
    # crests point into the housing and never disturb the outside silhouette.
    if pattern=='fresnel':
        profile=[.00,.18,.34,.40,.45,.57,.63,.68,.79,.85,.90,1.]
        crest={.40:.00075,.63:.00075,.85:.00065}
        for k,(a,b) in enumerate(zip(profile,profile[1:])):
            points=[]
            for rr in (max(a,.0001),b):
                relief=crest.get(rr,0.)
                points.append([ring_point(rr,t,'inner',relief)
                               for t in np.linspace(0,TAU,65)])
            etched=scatter is not None and (a,b) in ((.34,.40),(.57,.63),(.79,.85))
            model.grid(name+f'.{"etched" if etched else "clear"}_internal_fresnel_band.{k}',
                       points,scatter if etched else inner_glass,flip=etched)
        center=point_from_fraction(0.,0.,'inner')
        ring=[ring_point(.0001,t,'inner') for t in np.linspace(0,TAU,65)]
        model.mesh(name+'.internal_centre_interface',[center]+ring,
                   [(0,1+j,2+j) for j in range(64)],inner_glass)
    else:
        # Five deliberately broad prisms have a centre rise with true creases.
        for j in range(5):
            ua=-1+j*.4;ub=ua+.4
            for half,(left,right) in enumerate(((ua,(ua+ub)*.5),((ua+ub)*.5,ub))):
                points=[]
                for u in np.linspace(left,right,3):
                    phase=(u-ua)/.4;relief=.0009*(1-abs(phase*2-1))
                    points.append([surface(u,v,'inner',relief*(1-v*v)) for v in np.linspace(-1,1,17)])
                etched=scatter is not None and half==0 and j in (0,2,4)
                model.grid(name+f'.{"etched" if etched else "clear"}_internal_vertical_prism.{j}.{half}',
                           points,scatter if etched else inner_glass,flip=etched)

    # A separate twelve-sector satin reflector catches broad coloured light
    # behind the cover.  It has real curvature/depth, not external red rings.
    for sector in range(12):
        points=[]
        for rr in (.0001,.20,.40,.62,.82,1.):
            row=[]
            for phase in np.linspace(0,1,4):
                angle=(sector+phase)*TAU/12
                stamp=.00045*math.sin(phase*math.pi)**2*rr
                row.append(ring_point(rr,angle,'reflector',stamp))
            points.append(row)
        model.grid(name+f'.recessed_coated_reflector_sector.{sector}',points,reflector,flip=True)
    center=point_from_fraction(0.,0.,'reflector')
    ring=[ring_point(.0001,t,'reflector') for t in np.linspace(0,TAU,65)]
    model.mesh(name+'.reflector_centre',[center]+ring,
               [(0,2+j,1+j) for j in range(64)],reflector)
    perimeter=[]
    for t in np.linspace(0,TAU,81):
        # Use a unit square's radial boundary with the same rounded mapping.
        u,v=math.cos(t),math.sin(t);divisor=max(abs(u),abs(v))
        perimeter.append(surface(u/divisor,v/divisor))
    points=[[q for q in perimeter], [q+[0,0,thickness] for q in perimeter]]
    model.grid(name+'.smooth_cover_two_point_five_mm_edge',points,cover,flip=True)
    if cut_edge is not None:
        # A strongly absorbed, moulded coloured edge is a narrow physical rim,
        # not a coloured plaque or opaque tint over the clear lens aperture.
        points=[]
        for rr in (.973,1.):
            points.append([ring_point(rr,t,'cover')+[0,0,-.00015]
                           for t in np.linspace(0,TAU,81)])
        model.grid(name+'.tinted_moulded_cut_edge',points,cut_edge,flip=True)


def build_rear_optics(model, primitives, materials, rear_recess):
    """Append a recessed connected rear lamp, entirely within the real opening.

    Returns ``rear_z``, ``rear_mid`` and ``rear_width`` for the existing identity
    decal and mounting screws.  It does not touch the bumper or engine frame.
    """
    r=rear_recess;box=primitives['box'];plate=primitives['plate']
    cylinder=primitives['cylinder'];polyline=primitives['polyline']
    black=materials['black'];satin=materials.get('satin',materials['reflector'])
    tail=materials['tail'];amber=materials['amber']
    garnish=materials.get('garnish',tail)
    z=r['front_z'];mid=(r['x_min']+r['x_max'])*.5
    cy=(r['y_min']+r['y_max'])*.5;w=r['x_max']-r['x_min']-.060
    first=len(model.parts)
    outer=[(r['x_min']+.001,r['y_min']+.001),(r['x_max']-.001,r['y_min']+.001),
           (r['x_max']-.001,r['y_max']-.001),(r['x_min']+.001,r['y_max']-.001)]
    inner=[(mid-w*.5,cy-.076),(mid+w*.5,cy-.076),
           (mid+w*.5,cy+.076),(mid-w*.5,cy+.076)]
    for i in range(4):
        j=(i+1)%4;a,b=outer[i],outer[j];c,d=inner[j],inner[i]
        plate(f'rear.optics.recessed_perimeter_frame.{i}',
              [(a[0],a[1],z-.006),(b[0],b[1],z-.006),
               (c[0],c[1],z-.006),(d[0],d[1],z-.006)],black)
        plate(f'rear.optics.deep_housing_return.{i}',
              [(d[0],d[1],z-.006),(c[0],c[1],z-.006),
               (c[0],c[1],z+.043),(d[0],d[1],z+.043)],black)
    # The tray is inside the authored 55 mm recess, with 6 mm rear clearance.
    box('rear.optics.shared_recessed_housing_tray',(mid,cy,z+.043),
        (w,.152,.007),black,.006,3)
    box('rear.optics.recessed_red_centre_garnish',(mid,cy,z+.0005),
        (w*.418,.141,.018),garnish,.008,5)
    # Two slender moulded channels catch grazing light around the identity;
    # they do not lay an exact repeated cell grid over the entire red band.
    for k,yy in enumerate((cy-.059,cy+.059)):
        polyline(f'rear.optics.centre_garnish_moulding.{k}',
                 [(mid-w*.196,yy,z-.009),(mid,yy,z-.0097),(mid+w*.196,yy,z-.009)],
                 .0011,tail,6)
    for side in (-1,1):
        lo=mid+side*w*.216;hi=mid+side*w*.391
        x0,x1=sorted((lo,hi));red_bounds=(x0+.003,x1-.003,cy-.068,cy+.068)
        alo=mid+side*w*.399;ahi=mid+side*w*.491
        ax0,ax1=sorted((alo,ahi));amber_bounds=(ax0+.002,ax1-.002,cy-.068,cy+.068)
        for label,bounds,mat in (('red',red_bounds,tail),('amber',amber_bounds,amber)):
            bx0,bx1,by0,by1=bounds;cx=(bx0+bx1)*.5
            # This is an OPEN chamber, with four returns and a back wall.
            # A closed box would put an opaque cap in front of the reflector.
            chamber=[(bx0-.0045,cy-.0725),(bx1+.0045,cy-.0725),
                     (bx1+.0045,cy+.0725),(bx0-.0045,cy+.0725)]
            for k in range(4):
                a=chamber[k];b=chamber[(k+1)%4]
                plate(f'rear.optics.{label}_open_chamber_wall.{side}.{k}',
                      [(a[0],a[1],z+.002),(b[0],b[1],z+.002),
                       (b[0],b[1],z+.0385),(a[0],a[1],z+.0385)],black)
            plate(f'rear.optics.{label}_chamber_back_wall.{side}',
                  [(xx,yy,z+.0385) for xx,yy in chamber[::-1]],black)
            for yy in (by0-.002,by1+.002):
                cylinder(f'rear.optics.{label}_reflector_return.{side}.{yy}',
                         (bx0+.006,yy,z+.003),(bx1-.006,yy,z+.003),.0017,satin,6)
            _rear_lens(model,f'rear.optics.{label}_lens.{side}',bounds,z-.009,
                       materials.get('rear_cover',materials['lens']),
                       materials.get('rear_inner_glass',materials['lens']),
                       materials.get('red_reflector' if label=='red' else 'amber_reflector',mat),
                       'fresnel' if label=='red' else 'vertical',
                       materials.get('red_scatter' if label=='red' else 'amber_scatter'),
                       materials.get('red_edge' if label=='red' else 'amber_edge'))
            gasket=[]
            for t in np.linspace(0,TAU,65):
                exponent=7.;ca=math.cos(t);sa=math.sin(t)
                divisor=(abs(ca)**exponent+abs(sa)**exponent)**(1/exponent)
                gasket.append((cx+(bx1-bx0)*.506*ca/divisor,
                               cy+(by1-by0)*.506*sa/divisor,z-.0078))
            polyline(f'rear.optics.{label}_lens_sealing_gasket.{side}',gasket,.0012,black,6)
            for k,yy in enumerate((cy-.077,cy+.077)):
                cylinder(f'rear.optics.{label}_retaining_screw.{side}.{k}',
                         (cx,yy,z-.006),(cx,yy,z-.0085),.0032,satin,10)
        # A protective divider is narrow enough to read as a real housing seam.
        xx=mid+side*w*.395
        box(f'rear.optics.lamp_chamber_divider.{side}',(xx,cy,z+.006),
            (.006,.145,.029),black,.002,2)
    garnish_front_z=z+.0005-.018*.5
    return dict(rear_z=z,rear_mid=mid,rear_width=w,parts=len(model.parts)-first,
                frontmost_z=z-.012,backmost_z=z+.0465,
                garnish_front_z=garnish_front_z,legend_front_z=garnish_front_z-.0005,
                cover_bow=.003,cover_wall=.0025,prisms_inside=True)


def build_front_indicator(model,primitives,materials,name,x,y,z,width=.30,height=.075,depth=.045):
    """A real small amber chamber in the previous bar's unchanged envelope.

    Coordinates and the lamp-name prefix keep the existing nose translation.
    The smooth cover, internal diffuser, coloured reflector and black four-
    sided frame are physical layers.  No opaque yellow bar closes the front.
    """
    if width<.12 or height<.05 or depth<.045:
        raise ValueError('Front indicator envelope is too small for its physical optical layers')
    plate=primitives['plate'];black=materials['black'];half=width*.5;hh=height*.5
    back=-depth*.5;front=depth*.5-.003
    inner=[(-half+.009,-hh+.009),(half-.009,-hh+.009),
           (half-.009,hh-.009),(-half+.009,hh-.009)]
    outer=[(-half,-hh),(half,-hh),(half,hh),(-half,hh)]
    origin=np.array([x,y,z]);first=len(model.parts)
    for k in range(4):
        a,b=outer[k],outer[(k+1)%4];c,d=inner[(k+1)%4],inner[k]
        plate(name+f'.open_frame.{k}',
              [origin+[a[0],a[1],front],origin+[b[0],b[1],front],
               origin+[c[0],c[1],front],origin+[d[0],d[1],front]],black)
        plate(name+f'.deep_chamber_wall.{k}',
              [origin+[d[0],d[1],front],origin+[c[0],c[1],front],
               origin+[c[0],c[1],back],origin+[d[0],d[1],back]],black)
    plate(name+'.chamber_back_wall',[origin+[xx,yy,back] for xx,yy in outer],black)
    lens_start=len(model.parts)
    _rear_lens(model,name+'.amber_optic',(-half+.009,half-.009,-hh+.009,hh-.009),
               -front,materials.get('rear_cover',materials['lens']),
               materials.get('rear_inner_glass',materials['lens']),
               materials.get('amber_reflector',materials['amber']),'vertical',
               materials.get('amber_scatter'),materials.get('amber_edge'))
    rotation=np.diag([-1.,1.,-1.])
    for part in model.parts[lens_start:]:
        part['p']=part['p']@rotation.T+origin;part['n']=part['n']@rotation.T
    return dict(parts=len(model.parts)-first,envelope=[width,height,depth],cover_bow=.003,
                cover_wall=.0025,prisms_inside=True)
