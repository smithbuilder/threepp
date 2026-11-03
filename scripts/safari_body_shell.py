"""Original Safari coupe primary skin, authored in metres (+Z forward).

This module owns the primary sheet-metal loft only.  It deliberately has no
generator, GLB, renderer, texture, cabin, flare, lamp or accessory side effects.
``build_primary_shell`` accepts the existing generator's ``Model.mesh`` API.

The transverse profile is a low crowned bonnet, a C2 Hermite transition to
each continuous wing, then an elliptical shoulder turning vertical into the
door/quarter skin.  It is not a sum of pods or Gaussian displacement fields.
Top, side and end panels use common boundary samples, and exact loft derivative
normals are carried through the aperture cuts. No name-based position warp
or centroid-based triangle deletion is required (or compatible).
"""
from __future__ import annotations

from functools import lru_cache
import math

import numpy as np
from scipy.interpolate import PchipInterpolator, CubicSpline

Z_MIN, Z_MAX = -2.32, 2.08
RARCH = .615
AXLE_Y = .41
AXLES = (-1.35, 1.35)
REAR_RECESS = dict(x_min=-.76, x_max=.76, y_min=.84, y_max=1.045,
                   front_z=-2.32, back_z=-2.265)
rear_recess = REAR_RECESS
ENGINE_GRILLE_RECESS = dict(x_min=-.46,x_max=.46,z_min=-2.07,z_max=-1.73,
                            depth=.020)
FRONT_INTAKE = dict(half_width=.58,v_min=.18,v_max=.50,depth=.055,
                    type='open curved aperture with folded returns and recessed backing')
DUCKTAIL = dict(integrated=True,root_z=-1.88,crest_z=-2.275,tip_z=-2.32,
                half_width=.87,rise=.245,tip_y=1.2804,thickness=.027)
LAMP_SEATS = tuple(dict(x=side*.89, y=1.00, z=2.14, radius=.174,lens_radius=.165,
                        tilt=.34,axial_min=-.15,axial_max=.10) for side in (-1, 1))


def _spline(points):
    # Sheet metal needs continuous curvature through the longitudinal control
    # sections. PCHIP preserved values/slopes, but its second derivative jumped
    # at every knot and printed bands into reflections. Retain every measured
    # control value and the previous endpoint tangents with a clamped C2 cubic.
    x,y=np.asarray(points,dtype=float).T
    endpoint=PchipInterpolator(x,y).derivative()
    return CubicSpline(x,y,bc_type=((1,float(endpoint(x[0]))),
                                   (1,float(endpoint(x[-1])))))


# A rounded plan-view perimeter; neither end tapers into hanging sharp tips.
width = _spline([(-2.32,.90),(-2.12,1.025),(-1.75,1.145),(-1.35,1.185),
                 (-.90,1.11),(-.55,1.015),(0,.965),(.65,1.025),
                 (1.35,1.12),(1.70,1.115),(1.92,1.09),(2.08,1.07)])
_centre = _spline([(-2.32,1.055),(-2.12,1.045),(-1.94,1.07),
                   (-1.65,1.15),(-1.35,1.18),(-.70,1.185),(0,1.195),
                   (.56,1.205),(.95,1.13),(1.35,1.042),(1.68,.974),
                   (1.90,.920),(2.08,.875)])
_peak = _spline([(-2.32,1.13),(-2.12,1.20),(-1.75,1.31),
                 (-1.35,1.37),(-.90,1.31),(-.55,1.225),(0,1.205),
                 (.56,1.212),(.95,1.27),(1.35,1.325),(1.68,1.30),
                 (1.90,1.24),(2.08,1.17)])
_edge = _spline([(-2.32,1.06),(-2.10,1.085),(-1.75,1.12),(-1.35,1.145),
                 (-.70,1.16),(0,1.17),(.56,1.17),(.95,1.14),
                 (1.35,1.13),(1.68,1.08),(1.90,1.01),(2.08,.935)])
_crest_x = _spline([(-2.32,.72),(-2.12,.84),(-1.75,.905),(-1.35,.94),(-.70,.85),
                    (0,.79),(.56,.84),(.95,.845),(1.35,.86),
                    (1.68,.89),(2.08,.89)])

_curves=(width,_centre,_peak,_edge,_crest_x)
_slopes=tuple(fn.derivative() for fn in _curves)
_hermite_inverse=np.linalg.inv(np.array([[1,1,1],[3,4,5],[6,12,20]],float))


def _smooth(t):
    t = float(np.clip(t, 0, 1))
    return t*t*(3-2*t)


def _smoother(t):
    t=float(np.clip(t,0,1))
    return t*t*t*(t*(t*6-15)+10)


def _smooth_derivative(t):
    return 6*t*(1-t) if 0<t<1 else 0.


def _smoother_derivative(t):
    return 30*t*t*(1-t)*(1-t) if 0<t<1 else 0.


def _ducktail_weight(x,z):
    span=min(DUCKTAIL['half_width'],float(width(z)))
    return 1-_smoother(min(1.,(abs(float(x))/span)**2))


def _ducktail_rise(z):
    cfg=DUCKTAIL
    rise=_smoother((cfg['root_z']-z)/(cfg['root_z']-cfg['crest_z']))
    roll=.08*_smoother((cfg['crest_z']-z)/(cfg['crest_z']-cfg['tip_z']))
    return cfg['rise']*(rise-roll)


@lru_cache(maxsize=4096)
def _section(z):
    """Return the C2 inner-wing polynomial and exact outer ellipse."""
    values,_=_section_with_derivatives(z)
    return values


@lru_cache(maxsize=4096)
def _section_with_derivatives(z):
    """Value and longitudinal derivative of every transverse loft parameter.

    The Hermite constraints and their derivatives use the same linear solve;
    this is the exact derivative of the designed skin, not a mesh estimate.
    """
    z = float(np.clip(z, Z_MIN, Z_MAX))
    w, centre, peak, edge, crest = (float(fn(z)) for fn in _curves)
    wd,cd,pd,ed,rd=(float(fn(z)) for fn in _slopes)
    if z>.56:
        t=(z-.56)/.80
        valley=.49-.020*_smoother(t);vd=-.020/.80*_smoother_derivative(t)
    else:
        t=(z+.70)/1.26
        valley=.52-.030*_smoother(t);vd=-.030/1.26*_smoother_derivative(t)
    t=(z-.56)/.40
    crown=.010+.006*_smoother(t);kd=.006/.40*_smoother_derivative(t)
    span = crest-valley;sd=rd-vd
    y0 = centre-crown
    y0d=cd-kd
    d0 = -2*crown/valley*span
    d0d=-2*((kd/valley-crown*vd/valley**2)*span+crown/valley*sd)
    dd0 = -2*crown/(valley*valley)*span*span
    dd0d=-2*((kd/valley**2-2*crown*vd/valley**3)*span**2+2*crown/valley**2*span*sd)
    dd1 = -(peak-edge)/((w-crest)**2)*span*span
    dd1d=-(pd-ed)*span**2/(w-crest)**2-2*(peak-edge)*span*sd/(w-crest)**2+2*(peak-edge)*span**2*(wd-rd)/(w-crest)**3
    a0, a1, a2 = y0, d0, dd0*.5
    a0d,a1d,a2d=y0d,d0d,dd0d*.5
    rhs = np.array([peak-a0-a1-a2, -a1-2*a2, dd1-2*a2])
    rhsd=np.array([pd-a0d-a1d-a2d,-a1d-2*a2d,dd1d-2*a2d])
    a3, a4, a5 = _hermite_inverse@rhs
    a3d,a4d,a5d=_hermite_inverse@rhsd
    return ((w,centre,peak,edge,crest,valley,crown,(a0,a1,a2,a3,a4,a5)),
            (wd,cd,pd,ed,rd,vd,kd,(a0d,a1d,a2d,a3d,a4d,a5d)))


def _base_upper(x, z):
    w, centre, peak, edge, crest, valley, crown, a = _section(float(z))
    x = min(abs(float(x)), w)
    if x <= valley:
        return centre-crown*(x/valley)**2
    if x <= crest:
        t = (x-valley)/(crest-valley)
        return float(sum(coefficient*t**i for i,coefficient in enumerate(a)))
    t = (x-crest)/(w-crest)
    return edge+(peak-edge)*math.sqrt(max(0., 1-t*t))


def upper(x,z):
    """Continuous bonnet, wing and integral raised engine-lid skin."""
    raw=_base_upper(x,z)+_ducktail_rise(float(z))*_ducktail_weight(x,z)
    blend=_smoother((-2.04-float(z))/.20)
    if not blend:return raw
    w,centre,_,edge,_,_,_,_=_section(float(z))
    q=min(abs(float(x)),w)
    # The trailing lip must have one continuous transverse crown. Adding the
    # lid rise to the separate wing crown made a genuine 4 mm trough/crest
    # pair near X=.59/.65. Fair only the last 200 mm into a monotone ellipse,
    # preserving centre height and the side boundary exactly.
    target=edge+(centre+_ducktail_rise(float(z))-edge)*math.sqrt(max(0.,1-(q/w)**2))
    return raw+blend*(target-raw)


def upper_derivatives(x,z):
    """Exact (height, d/dx, d/dz, d2/dxdz) of the compound upper skin."""
    q=abs(float(x));sign=1. if x>=0 else -1.
    values,derivatives=_section_with_derivatives(float(z))
    w,c,p,e,r,v,k,a=values;wd,cd,pd,ed,rd,vd,kd,ad=derivatives
    q=min(q,w-1e-12)
    if q<=v:
        y=c-k*q*q/v**2
        dx=-2*k*q/v**2
        dz=cd-kd*q*q/v**2+2*k*q*q*vd/v**3
        dxz=-2*q*(kd/v**2-2*k*vd/v**3)
    elif q<=r:
        span=r-v;sd=rd-vd;t=(q-v)/span;tz=(-vd-t*sd)/span
        y=sum(co*t**i for i,co in enumerate(a))
        pt=sum(i*a[i]*t**(i-1) for i in range(1,6))
        ptt=sum(i*(i-1)*a[i]*t**(i-2) for i in range(2,6))
        pz=sum(co*t**i for i,co in enumerate(ad))
        ptz=sum(i*ad[i]*t**(i-1) for i in range(1,6))
        dx=pt/span;dz=pz+pt*tz
        dxz=(ptz+ptt*tz)/span-pt*sd/span**2
    else:
        span=w-r;sd=wd-rd;t=(q-r)/span;tz=(-rd-t*sd)/span
        f=math.sqrt(max(1e-15,1-t*t));height=p-e
        y=e+height*f;dx=-height*t/(span*f)
        dz=ed+(pd-ed)*f-height*t*tz/f
        dxz=-(pd-ed)*t/(span*f)+height*(t*sd/(span**2*f)-tz/(span*f**3))
    cfg=DUCKTAIL
    ta=(cfg['root_z']-z)/(cfg['root_z']-cfg['crest_z'])
    tb=(cfg['crest_z']-z)/(cfg['crest_z']-cfg['tip_z'])
    rise=cfg['rise']*(_smoother(ta)-.08*_smoother(tb))
    rise_z=cfg['rise']*(-_smoother_derivative(ta)/(cfg['root_z']-cfg['crest_z'])
                          +.08*_smoother_derivative(tb)/(cfg['crest_z']-cfg['tip_z']))
    span=min(cfg['half_width'],w);sd=wd if w<cfg['half_width'] else 0.
    t=(q/span)**2;tz=-2*q*q*sd/span**3
    weight=1-_smoother(t);weight_z=-_smoother_derivative(t)*tz
    weight_x=-_smoother_derivative(t)*2*q/span**2
    second=60*t*(1-t)*(1-2*t) if 0<t<1 else 0.
    weight_xz=-second*tz*2*q/span**2+_smoother_derivative(t)*4*q*sd/span**3
    y+=rise*weight;dx+=rise*weight_x
    dz+=rise_z*weight+rise*weight_z
    dxz+=rise_z*weight_x+rise*weight_xz
    blend_t=(-2.04-float(z))/.20
    blend=_smoother(blend_t);blend_z=-_smoother_derivative(blend_t)/.20
    if blend:
        t=q/w;f=math.sqrt(max(1e-15,1-t*t));height=c+rise-e
        height_z=cd+rise_z-ed;tz=-t*wd/w
        target=e+height*f
        target_x=-height*t/(w*f)
        target_z=ed+height_z*f-height*t*tz/f
        target_xz=-height_z*t/(w*f)+height*(t*wd/(w*w*f)-tz/(w*f**3))
        dxz+=blend*(target_xz-dxz)+blend_z*(target_x-dx)
        dz+=blend*(target_z-dz)+blend_z*(target-y)
        dx+=blend*(target_x-dx);y+=blend*(target-y)
    return y,sign*dx,dz,sign*dxz


def lower_baseline(z):
    """Uncut lower body line, also used to trim flare ends onto the shell."""
    z = float(z)
    result = .35 + .385*_smooth((z-1.45)/.50)
    result += .405*_smooth((-z-1.45)/.50)
    return result


def opening(z):
    """Exact .615m tyre opening, smoothly tucked lower corners outside it."""
    z = float(z)
    # Waiting until the arch's last station to raise the bumper-side body
    # makes a hanging triangular toe. The baseline already turns up here.
    result = lower_baseline(z)
    for axle in AXLES:
        dz = z-axle
        if abs(dz) < RARCH:
            result = max(result, AXLE_Y+math.sqrt(RARCH*RARCH-dz*dz))
    return result


def body_x(z, y):
    """Outer side profile; vertical tangent matches the elliptical shoulder."""
    z = float(np.clip(z, Z_MIN, Z_MAX))
    edge = float(_edge(z))
    t = float(np.clip((float(y)-.32)/(edge-.32), 0, 1))
    # The lower nose corners turn inward rather than ending in flat points.
    nose = .035*_smooth((z-1.94)/.36)
    inset = .155+nose
    return float(width(z))-inset*(1-t)**2


def body_x_derivatives(z,y):
    """Exact (outer X, dX/dY, dX/dZ) of the lower side stamping."""
    z=float(np.clip(z,Z_MIN,Z_MAX));edge=float(_edge(z));ed=float(_slopes[3](z))
    raw=(float(y)-.32)/(edge-.32);t=float(np.clip(raw,0,1))
    ty=1/(edge-.32) if 0<raw<1 else 0.
    tz=-(y-.32)*ed/(edge-.32)**2 if 0<raw<1 else 0.
    u=(z-1.94)/.36;inset=.155+.035*_smooth(u)
    inset_z=.035/.36*_smooth_derivative(u)
    return (float(width(z))-inset*(1-t)**2,
            2*inset*(1-t)*ty,
            float(_slopes[0](z))-inset_z*(1-t)**2+2*inset*(1-t)*tz)


def cabin_cut_width(z):
    return float(np.interp(z, [-1.65,-1.35,-.45,.30,.56],
                          [.86,.90,.91,.89,.84]))


def engine_grille_floor(x,z):
    return upper(x,z)-ENGINE_GRILLE_RECESS['depth']


def _across(z):
    """Arc-spaced top samples resolve the shoulder's vertical tangent."""
    w, _, _, _, crest, valley, _, _ = _section(float(z))
    half = np.r_[np.linspace(0,valley,9), .46,.58,
                 np.linspace(valley,crest,9)[1:],
                 crest+(w-crest)*np.sin(np.linspace(0,math.pi/2,9))[1:]]
    # The rear glass foot meets the cabin aperture at x=+/-.86. Keep that
    # actual shared boundary vertex instead of interpolating a different chord.
    if z<=-1.65+1e-9:half=np.r_[half,.86]
    half=np.sort(half)
    return np.r_[-half[:0:-1], half]


def _triangles(rows, cols, flip=False):
    faces = []
    for i in range(rows-1):
        for j in range(cols-1):
            a=i*cols+j; b=a+1; c=a+cols; d=c+1
            faces.extend(((a,b,c),(b,d,c)) if flip else
                         ((a,c,b),(b,c,d)))
    return np.asarray(faces, dtype=np.uint32)


def _lamp_value(point, seat):
    x, y, z = point-np.array([seat['x'],seat['y'],seat['z']])
    transverse = y*math.cos(seat['tilt'])-z*math.sin(seat['tilt'])
    return x*x+transverse*transverse-seat['radius']**2


def _lamp_axial(point, seat):
    offset=point-np.array([seat['x'],seat['y'],seat['z']])
    return float(offset@np.array([0.,math.sin(seat['tilt']),math.cos(seat['tilt'])]))


def _clip_plane(poly, value):
    """Clip a convex polygon against a linear signed half-space >= 0."""
    if not poly:
        return []
    result=[]
    for i,(a,au) in enumerate(poly):
        b,bu=poly[(i+1)%len(poly)]
        av,bv=value(a),value(b)
        if av>=-1e-12:
            result.append((a,au))
        if (av>=-1e-12)!=(bv>=-1e-12):
            t=float(np.clip(av/(av-bv),0,1))
            result.append((a+(b-a)*t,au+(bu-au)*t))
    return result


def _clip_outside_lamp_radius(poly, seat):
    if not poly:
        return []
    values=[_lamp_value(p,seat) for p,_ in poly]
    if all(v>=-1e-12 for v in values):
        return poly
    if all(v < -1e-12 for v in values):
        return []
    result=[]
    for i,(a,au) in enumerate(poly):
        b,bu=poly[(i+1)%len(poly)];av=values[i];bv=values[(i+1)%len(poly)]
        if av>=-1e-12:
            result.append((a,au))
        if (av>=-1e-12)!=(bv>=-1e-12):
            t=_lamp_intersection(a,b,seat)
            result.append((a+(b-a)*t,au+(bu-au)*t))
    return result


def _lamp_intersection(a, b, seat):
    # A finite exact quadratic intersection, independent of triangle size.
    centre=np.array([seat['x'],seat['y'],seat['z']])
    transverse=np.array([0.,math.cos(seat['tilt']),-math.sin(seat['tilt'])])
    pa=a-centre; delta=b-a
    aa=delta[0]**2+float(delta@transverse)**2
    bb=2*(pa[0]*delta[0]+float(pa@transverse)*float(delta@transverse))
    cc=_lamp_value(a,seat)
    if aa < 1e-16:
        return float(np.clip(-cc/bb,0,1)) if abs(bb)>1e-16 else .5
    disc=max(0.,bb*bb-4*aa*cc)
    roots=[t for t in ((-bb-math.sqrt(disc))/(2*aa),
                       (-bb+math.sqrt(disc))/(2*aa)) if -1e-7<=t<=1+1e-7]
    if not roots:
        return float(np.clip(cc/(cc-_lamp_value(b,seat)),0,1))
    # At most one crossing for an outside/inside edge.  A root precisely on
    # its endpoint is valid and is welded to its neighbouring triangle.
    return float(np.clip(min(roots,key=lambda t:abs(t-.5)),0,1))


def _cut_lamps(points, faces, uv):
    """Clip crossed triangles at exact FINITE lamp-cylinder intersections.

    This cuts real surface apertures, not black disks or centroid masks.
    New UVs interpolate on their original triangle and remain body-local.
    """
    points=np.asarray(points,float); uv=np.asarray(uv,float)
    for seat in LAMP_SEATS:
        axial=np.array([_lamp_axial(p,seat) for p in points])
        amin,amax=seat['axial_min'],seat['axial_max']
        output_p=[]; output_uv=[]; output_f=[]
        for face in faces:
            poly=[(points[i],uv[i]) for i in face]
            radial_values=[_lamp_value(points[i],seat) for i in face]
            if (max(axial[face])<=amin+1e-12 or min(axial[face])>=amax-1e-12
                    or all(value>=-1e-12 for value in radial_values)):
                pieces=[poly]
            else:
                # Preserve both exact outside half-spaces. Only their middle
                # slab intersects the finite physical headlamp-seat cutter.
                low=_clip_plane(poly,lambda p:amin-_lamp_axial(p,seat))
                rest=_clip_plane(poly,lambda p:_lamp_axial(p,seat)-amin)
                middle=_clip_plane(rest,lambda p:amax-_lamp_axial(p,seat))
                high=_clip_plane(rest,lambda p:_lamp_axial(p,seat)-amax)
                pieces=[low,_clip_outside_lamp_radius(middle,seat),high]
            for new in pieces:
                if len(new)<3:
                    continue
                base=len(output_p)
                output_p.extend(p for p,_ in new)
                output_uv.extend(t for _,t in new)
                output_f.extend((base,base+i,base+i+1) for i in range(1,len(new)-1))
        points=np.asarray(output_p,float); uv=np.asarray(output_uv,float)
        faces=np.asarray(output_f,np.uint32)
    # The triangle clip deliberately duplicates corners; weld exact position
    # AND UV here so generated meshes do not carry three vertices per face.
    keys=np.round(np.c_[points,uv],8)
    _, first, inverse=np.unique(keys,axis=0,return_index=True,return_inverse=True)
    return points[first], inverse[faces], uv[first]


def _emit(model, name, grid, material, uv=None, flip=False, weather=None,
          lamp_cuts=False, grille_cut=False,cut_cells=None):
    p=np.asarray(grid,float); rows,cols,_=p.shape
    faces=_triangles(rows,cols,flip)
    if cut_cells is not None:
        mask=np.asarray(cut_cells,bool)
        if mask.shape!=(rows-1,cols-1):raise ValueError('Aperture grid shape '+name)
        faces=faces[~np.repeat(mask.reshape(-1),2)]
    p=p.reshape(-1,3)
    if uv is None:
        uv=np.c_[p[:,0]/np.maximum(width(np.clip(p[:,2],Z_MIN,Z_MAX)),1e-8)*.5+.5,
                 (p[:,2]-Z_MIN)/(Z_MAX-Z_MIN)]
        # Rounded returns extend a few centimetres past the atlas endpoints.
        # Keep those samples inside the last texel instead of wrapping dust.
        uv=np.clip(uv,.5/512,1-.5/512)
    else:
        uv=np.asarray(uv,float).reshape(-1,2)
    if grille_cut:
        # These are exact grid-aligned aperture edges, not centroid masks.
        bounds=ENGINE_GRILLE_RECESS; corners=p[faces]
        inside=(corners[:,:,0]>=bounds['x_min']-1e-9)&(corners[:,:,0]<=bounds['x_max']+1e-9)
        inside&=(corners[:,:,2]>=bounds['z_min']-1e-9)&(corners[:,:,2]<=bounds['z_max']+1e-9)
        faces=faces[~np.all(inside,axis=1)]
    if lamp_cuts:
        p,faces,uv=_cut_lamps(p,faces,uv)
    # Remove only truly degenerate faces, never visible rows of a surface.
    area=np.linalg.norm(np.cross(p[faces[:,1]]-p[faces[:,0]],
                                 p[faces[:,2]]-p[faces[:,0]]),axis=1)
    faces=faces[area>1e-12]
    colors=weather(p) if weather is not None else None
    model.mesh(name,p,faces,material,uv,colors)


def _weld_outward_normals(parts):
    """Area-weight shared positions, including UV and aperture seams."""
    all_points=np.concatenate([part['p'] for part in parts])
    _,inverse=np.unique(np.round(all_points,6),axis=0,return_inverse=True)
    sums=np.zeros((int(inverse.max())+1,3),float)
    offset=0
    for part in parts:
        p=part['p']; f=part['f']; ids=inverse[offset:offset+len(p)]
        fn=np.cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]])
        for corner in range(3):
            np.add.at(sums,ids[f[:,corner]],fn)
        offset+=len(p)
    sums/=np.maximum(np.linalg.norm(sums,axis=1)[:,None],1e-12)
    offset=0
    for part in parts:
        part['n']=sums[inverse[offset:offset+len(part['p'])]].astype(np.float32)
        offset+=len(part['p'])


def _front_point(s,v):
    """Rounded nose point and its exact transverse/vertical derivatives.

    The lower edge is the shared lower-body contour. The upper edge is the
    actual descending bonnet/raised-wing section, with its true tangent.
    """
    z=Z_MAX;w=float(width(z));low=opening(z)
    high,hx,hz,hxz=upper_derivatives(s*w,z)
    bulge=.055*(1-s**8);bs=-.44*s**7
    tangent=-math.pi*bulge*hz
    tangent_s=-math.pi*(bs*hz+bulge*hxz*w)
    sv=math.sin(v*math.pi/2);cv=math.cos(v*math.pi/2)
    poly=v*v*(v-1);polyd=3*v*v-2*v
    y=low+(high-low)*sv+tangent*poly
    ys=hx*w*sv+tangent_s*poly
    yv=(high-low)*cv*math.pi/2+tangent*polyd
    bx,by,_=body_x_derivatives(z,y)
    top_x,top_y,_=body_x_derivatives(z,high)
    edge=float(_edge(z));inset=.155+.035*_smooth((z-1.94)/.36)
    top_yy=-2*inset/(edge-.32)**2 if .32<high<edge else 0.
    correction=top_y*tangent
    correction_s=top_yy*hx*w*tangent+top_y*tangent_s
    sm=_smooth(v);smd=_smooth_derivative(v)
    a=bx+(w-top_x)*sm-correction*poly
    a_s=by*ys-top_y*hx*w*sm-correction_s*poly
    a_v=by*yv+(w-top_x)*smd-correction*polyd
    point=np.array([s*a,y,z+bulge*math.sin(math.pi*v)])
    transverse=np.array([a+s*a_s,ys,bs*math.sin(math.pi*v)])
    vertical=np.array([s*a_v,yv,math.pi*bulge*math.cos(math.pi*v)])
    return point,transverse,vertical


def _front_normal(point):
    """Invert the nose parameterisation for exact normals on clipped cuts."""
    x,y,z=map(float,point);w=float(width(Z_MAX));low=opening(Z_MAX)
    s=float(np.clip(x/w,-1,1));high=upper(s*w,Z_MAX)
    v=2/math.pi*math.asin(float(np.clip((y-low)/max(high-low,1e-8),0,1)))
    for _ in range(7):
        p,ds,dv=_front_point(s,v);error=p[:2]-[x,y]
        jac=np.array([[ds[0],dv[0]],[ds[1],dv[1]]])
        if abs(np.linalg.det(jac))<1e-12:break
        step=np.linalg.solve(jac,error)
        s=float(np.clip(s-step[0],-1,1));v=float(np.clip(v-step[1],0,1))
        if np.linalg.norm(step)<1e-11:break
    _,ds,dv=_front_point(s,v);normal=np.cross(ds,dv)
    if np.linalg.norm(normal)<1e-10:normal=np.array([0.,0.,1.])
    return normal/max(np.linalg.norm(normal),1e-12)


def _front_intake(model,material):
    """Fold the real nose opening inward; paint is absent inside its loop."""
    cfg=FRONT_INTAKE;limit=cfg['half_width']/float(width(Z_MAX))
    ss=_across(Z_MAX)/float(width(Z_MAX));ss=ss[(ss>=-limit-1e-9)&(ss<=limit+1e-9)]
    vs=np.unique(np.r_[np.linspace(0,1,13),cfg['v_min'],cfg['v_max']])
    vs=vs[(vs>=cfg['v_min']-1e-9)&(vs<=cfg['v_max']+1e-9)]
    loop=[(s,cfg['v_min']) for s in ss]
    loop.extend((limit,v) for v in vs[1:])
    loop.extend((s,cfg['v_max']) for s in ss[-2::-1])
    loop.extend((-limit,v) for v in vs[-2::-1])
    grid=[]
    for s,v in loop:
        p,_,_=_front_point(s,v)
        grid.append([p,p-[0,0,cfg['depth']]])
    _emit(model,'body.front_cooling_intake.folded_return',grid,material)
    grid=[[_front_point(s,v)[0]-[0,0,cfg['depth']] for s in ss] for v in vs]
    _emit(model,'body.front_cooling_intake.recessed_backing',grid,material,flip=True)


def _rear_upper_point_normal(s,v):
    """Exact rear under-face field and its derivatives, including the lid roll."""
    z=Z_MIN;w=float(width(z));x=s*w;weight=_ducktail_weight(x,z)
    span=min(DUCKTAIL['half_width'],w);t=(abs(x)/span)**2
    weight_s=-_smoother_derivative(t)*2*x*w/(span*span)
    top=upper(x,z);_,top_x,_,_=upper_derivatives(x,z)
    high=top-DUCKTAIL['thickness']*weight
    high_s=top_x*w-DUCKTAIL['thickness']*weight_s
    y=REAR_RECESS['y_max']+(high-REAR_RECESS['y_max'])*v
    ys=high_s*v;yv=high-REAR_RECESS['y_max']
    bx,by,_=body_x_derivatives(z,y)
    inset=.012*v+.085*math.sin(v*math.pi)
    inset_v=.012+.085*math.pi*math.cos(v*math.pi)
    point=np.array([s*bx,y,z+weight*inset])
    ds=np.array([bx+s*by*ys,ys,weight_s*inset])
    dv=np.array([s*by*yv,yv,weight*inset_v])
    normal=-np.cross(ds,dv);normal/=max(np.linalg.norm(normal),1e-12)
    return point,normal


def _apply_analytic_loft_normals(parts):
    """Shade the actual smooth loft, independent of uneven sampling density.

    Uniform area averaging visibly biases normals where narrow shoulder arc
    cells meet long deck cells. The loft derivatives are authoritative; the
    same normal is then carried to every matching cap/return seam vertex.
    """
    shared={};width_slope=_slopes[0]
    for part in parts:
        top=part['name'].startswith('body.continuous_')
        side=part['name'].startswith('body.side_with_')
        front=part['name']=='body.rounded_front_valance'
        rear_upper=part['name']=='body.rounded_rear_valance.upper'
        rear_flat=part['name']=='body.rounded_rear_valance.lower' or part['name'].startswith('body.rounded_rear_valance.cheek_')
        if not top and not side and not front and not rear_upper and not rear_flat:continue
        normals=[]
        for x,y,z in part['p'].astype(float):
            if rear_flat:
                # These are actual constant-Z panels. Area welding only the
                # occasional coincident side vertex made diagonal normal fans
                # across the planar fascia instead of a consistent fold.
                normals.append(np.array([0.,0.,-1.]));continue
            if rear_upper:
                s=float(np.clip(x/body_x(Z_MIN,y),-1,1))
                xtop=s*float(width(Z_MIN));weight=_ducktail_weight(xtop,Z_MIN)
                high=upper(xtop,Z_MIN)-DUCKTAIL['thickness']*weight
                v=float(np.clip((y-REAR_RECESS['y_max'])/(high-REAR_RECESS['y_max']),0,1))
                normals.append(_rear_upper_point_normal(s,v)[1]);continue
            if front:
                normals.append(_front_normal((x,y,z)))
                continue
            z=float(np.clip(z,Z_MIN,Z_MAX));sign=1 if x>=0 else -1
            if top:
                w=float(width(z));margin=w-abs(x)
                if margin<1e-5:n=np.array([sign,0.,-float(width_slope(z))])
                else:
                    _,dx,dz,_=upper_derivatives(x,z)
                    n=np.array([-dx,1.,-dz])
            else:
                _,dy,dz=body_x_derivatives(z,y)
                n=np.array([sign,-dy,-dz])
            n/=max(np.linalg.norm(n),1e-12);normals.append(n)
            shared.setdefault(tuple(np.round([x,y,z],6)),[]).append(n)
        part['n']=np.asarray(normals,np.float32)
    for part in parts:
        for i,p in enumerate(part['p']):
            normals=shared.get(tuple(np.round(p,6)))
            if normals:
                n=np.sum(normals,axis=0);n/=max(np.linalg.norm(n),1e-12);part['n'][i]=n


def _lamp_returns(model, skins, material):
    """Fold the cut lamp perimeter into the body, behind the fitted gasket."""
    edges={}
    for part in skins:
        points=part['p']
        for face in part['f']:
            for i,j in ((0,1),(1,2),(2,0)):
                a=points[face[i]].astype(float);b=points[face[j]].astype(float)
                ka=tuple(np.round(a,6));kb=tuple(np.round(b,6))
                key=tuple(sorted((ka,kb)))
                if key not in edges:
                    edges[key]=[0,a,b]
                edges[key][0]+=1
    for index,seat in enumerate(LAMP_SEATS):
        centre=np.array([seat['x'],seat['y'],seat['z']])
        axis=np.array([0.,math.sin(seat['tilt']),math.cos(seat['tilt'])])
        points=[];faces=[]
        for count,a,b in edges.values():
            axial_a,axial_b=_lamp_axial(a,seat),_lamp_axial(b,seat)
            if count!=1 or min(axial_a,axial_b)<seat['axial_min']-2e-6 or max(axial_a,axial_b)>seat['axial_max']+2e-6:
                continue
            radial_edge=max(abs(_lamp_value(a,seat)),abs(_lamp_value(b,seat)))<=2e-7
            plane_edge=any(max(abs(axial_a-plane),abs(axial_b-plane))<=2e-6 for plane in (seat['axial_min'],seat['axial_max']))
            plane_edge &= max(_lamp_value(a,seat),_lamp_value(b,seat))<=2e-7
            if not radial_edge and not plane_edge:
                continue
            radial=[]
            for p in (a,b):
                r=p-centre-axis*float((p-centre)@axis)
                radial.append(r/max(np.linalg.norm(r),1e-9))
            qa=a-axis*.030+radial[0]*.008
            qb=b-axis*.030+radial[1]*.008
            base=len(points);points.extend((a,b,qa,qb))
            pair=[(base,base+1,base+2),(base+1,base+3,base+2)]
            n=np.cross(b-a,qa-a)
            if float(n@(-radial[0]))<0:
                pair=[tuple(reversed(face)) for face in pair]
            faces.extend(pair)
        if points:
            model.mesh('body.lamp_aperture_return.'+str(index),points,faces,material)


def _engine_grille_recess(model, zs, material):
    bounds=ENGINE_GRILLE_RECESS
    xmin,xmax,zmin,zmax=(bounds[key] for key in ('x_min','x_max','z_min','z_max'))
    longitudinal=zs[(zs>=zmin)&(zs<=zmax)]
    loop=[(xmin,z) for z in longitudinal]
    loop.extend((x,zmax) for x in _across(zmax) if xmin<x<=xmax)
    loop.extend((xmax,z) for z in longitudinal[-2::-1])
    loop.extend((x,zmin) for x in _across(zmin)[::-1] if xmin<=x<xmax)
    if loop[-1]!=loop[0]:loop.append(loop[0])
    grid=[[(x,upper(x,z),z),(x,engine_grille_floor(x,z),z)] for x,z in loop]
    _emit(model,'body.engine_grille_aperture_return',grid,material)
    grid=[]
    for z in longitudinal:
        grid.append([(x,engine_grille_floor(x,z),z) for x in np.linspace(xmin,xmax,17)])
    _emit(model,'body.engine_grille_recess_floor',grid,material)


def _ducktail_return(model,material,weather):
    """Rounded 27mm trailing lip of the ONE continuous engine-lid surface.

    The top is already present in the rear deck's authoritative upper() loft.
    This return rolls around its trailing edge into the curved under-face;
    there is no added wing, root wall, side plate or rectangular foil.
    """
    grid=[]
    for theta in np.linspace(0,math.pi,9):
        row=[]
        for x in _across(Z_MIN):
            weight=_ducktail_weight(x,Z_MIN)
            y=upper(x,Z_MIN)-DUCKTAIL['thickness']*.5*(1-math.cos(theta))*weight
            z=Z_MIN-.010*weight*math.sin(theta)+.012*weight*theta/math.pi
            row.append((x,y,z))
        grid.append(row)
    _emit(model,'body.rounded_ducktail_trailing_return',grid,material,
          flip=True,weather=weather)


def build_primary_shell(model, paint, dark, weather_colors=None,
                        paint_side=None, paint_top=None):
    """Append the primary body panels and return integration metadata.

    Keep the original builder's cabin, inner cabin panels, bolted flares and
    fitted hardware. Remove its old top/side/sill/end patches and duplicate
    trailing ducktail strip. Model.mesh/grid must not change coordinates or
    delete faces by name. ``paint_side``/``paint_top`` default to ``paint``.
    """
    first=len(model.parts)
    side_mat=paint if paint_side is None else paint_side
    top_mat=paint if paint_top is None else paint_top
    # The same longitudinal stations form both sides and all upper patches.
    stations=list(np.linspace(Z_MIN,Z_MAX,151))+[-2.275,-2.12,-2.025,-1.88,-1.75,-1.65,.56]
    stations += [ENGINE_GRILLE_RECESS['z_min'],ENGINE_GRILLE_RECESS['z_max']]
    for axle in AXLES:
        stations.extend(axle+RARCH*np.cos(np.linspace(0,math.pi,33)))
    zs=np.unique(np.round(stations,10))
    zs=zs[(zs>=Z_MIN)&(zs<=Z_MAX)]
    for label,zlo,zhi in [('front',.56,Z_MAX),('rear',Z_MIN,-1.65)]:
        p=[];uv=[]
        for z in zs[(zs>=zlo)&(zs<=zhi)]:
            xs=_across(float(z)); w=float(width(z))
            p.append([(x,upper(x,z),z) for x in xs])
            uv.append([(x/w*.5+.5,(z-Z_MIN)/(Z_MAX-Z_MIN)) for x in xs])
        _emit(model,'body.continuous_bonnet_shoulders_rear_deck.'+label,
              p,top_mat,uv,weather=weather_colors,lamp_cuts=label=='front',
              grille_cut=label=='rear')
    for side in (-1,1):
        p=[];uv=[]
        for z in zs[(zs>=-1.65)&(zs<=.56)]:
            w,_,_,_,crest,_,_,_=_section(float(z))
            cut=cabin_cut_width(z)
            theta=math.asin(float(np.clip((cut-crest)/(w-crest),0,1)))
            xs=crest+(w-crest)*np.sin(np.linspace(theta,math.pi/2,9))
            if cut<crest:
                xs=np.linspace(cut,w,9)
            xs=xs if side>0 else -xs[::-1]
            p.append([(x,upper(x,z),z) for x in xs])
            uv.append([(x/w*.5+.5,(z-Z_MIN)/(Z_MAX-Z_MIN)) for x in xs])
        _emit(model,'body.continuous_bonnet_shoulders_rear_deck.shoulder_'+str(side),
              p,top_mat,uv,weather=weather_colors)

    levels=np.sin(np.linspace(0,math.pi/2,13))
    for side in (-1,1):
        p=[];uv=[];returns=[]
        for z in zs:
            low=opening(z); high=float(_edge(z))
            if high<=low:
                raise ValueError(f'Body crosses arch at z={z}: {high} <= {low}')
            row=[];ruv=[]
            for t in levels:
                y=low+(high-low)*t
                row.append((side*body_x(z,y),y,z))
                ruv.append(((z-Z_MIN)/(Z_MAX-Z_MIN),y))
            p.append(row);uv.append(ruv)
            x=body_x(z,low)
            # Raised inner edge always remains outside the actual arch void.
            # At the very ends it meets the longitudinally folded under-lip,
            # closing the corner instead of leaving two disconnected returns.
            inner_z=z-.035*_smooth((z-(Z_MAX-.10))/.10)
            inner_z+=.035*_smooth((-z-2.22)/.10)
            returns.append([(side*x,low,z),(side*(x-.040),low+.022,inner_z)])
        _emit(model,'body.side_with_open_arches.'+str(side),p,side_mat,uv,
              flip=side>0,weather=weather_colors,lamp_cuts=True)
        _emit(model,'body.lower_perimeter_return.'+str(side),returns,dark,
              flip=side<0)

    # A rounded, closed nose follows the true side contour at BOTH corners.
    # Its top tangent turns into the bonnet instead of meeting a flat slab.
    z=Z_MAX;xs=_across(z);svals=xs/float(width(z));cfg=FRONT_INTAKE
    vvals=np.unique(np.r_[np.linspace(0,1,13),cfg['v_min'],cfg['v_max']])
    p=[[_front_point(s,v)[0] for s in svals] for v in vvals]
    cut=np.outer((vvals[:-1]>=cfg['v_min']-1e-9)&(vvals[1:]<=cfg['v_max']+1e-9),
                 (xs[:-1]>=-cfg['half_width']-1e-9)&(xs[1:]<=cfg['half_width']+1e-9))
    _emit(model,'body.rounded_front_valance',p,top_mat,flip=True,
          weather=weather_colors,lamp_cuts=True,cut_cells=cut)
    _front_intake(model,dark)

    # Rear fascia is made from four intact panels around an aligned opening.
    # The outer shape and true rectangular aperture are not triangle masks.
    z=Z_MIN; low=opening(z); ymin=REAR_RECESS['y_min']; ymax=REAR_RECESS['y_max']
    xmin=REAR_RECESS['x_min'];xmax=REAR_RECESS['x_max']
    p=[]
    for y in np.linspace(low,ymin,7):
        p.append([(s*body_x(z,y),y,z) for s in np.linspace(-1,1,49)])
    _emit(model,'body.rounded_rear_valance.lower',p,top_mat,
          weather=weather_colors)
    for side in (-1,1):
        p=[]
        for y in np.linspace(ymin,ymax,9):
            p.append([(side*(xmax+(body_x(z,y)-xmax)*t),y,z)
                      for t in np.linspace(0,1,7)])
        _emit(model,'body.rounded_rear_valance.cheek_'+str(side),p,top_mat,
              flip=side<0,weather=weather_colors)
    p=[];xs=_across(z);svals=xs/float(width(z))
    for v in np.linspace(0,1,17):
        p.append([_rear_upper_point_normal(s,v)[0] for s in svals])
    _emit(model,'body.rounded_rear_valance.upper',p,top_mat,
          weather=weather_colors)
    corners=[(xmin,ymin),(xmax,ymin),(xmax,ymax),(xmin,ymax),(xmin,ymin)]
    p=[]
    for x,y in corners:
        p.append([(x,y,z),(x,y,REAR_RECESS['back_z'])])
    _emit(model,'body.rear_band_aperture_return',p,dark)
    model.mesh('body.rear_band_cavity_backing',
               [(xmin,ymin,REAR_RECESS['back_z']),(xmax,ymin,REAR_RECESS['back_z']),
                (xmax,ymax,REAR_RECESS['back_z']),(xmin,ymax,REAR_RECESS['back_z'])],
               [(0,2,1),(0,3,2)],dark)

    # Closed under-returns at both ends meet the lower side returns exactly.
    for z,label,direction in [(Z_MAX,'front',-1),(Z_MIN,'rear',1)]:
        low=opening(z); w=body_x(z,low);p=[]
        for v in (0,1):
            p.append([(s*(w-.04*v),low+.022*v,z+direction*.035*v)
                      for s in np.linspace(-1,1,49)])
        _emit(model,'body.closed_'+label+'_under_return',p,dark,
              flip=direction>0)

    _ducktail_return(model,top_mat,weather_colors)
    # Weld only enamel primary surfaces: folded dark returns keep their edge.
    skins=[part for part in model.parts[first:] if part['name'].startswith(
        ('body.continuous_','body.side_with_','body.rounded_'))]
    _weld_outward_normals(skins)
    _apply_analytic_loft_normals(skins)
    _lamp_returns(model,skins,dark)
    _engine_grille_recess(model,zs,dark)
    return dict(rear_recess=dict(REAR_RECESS),lamp_seats=LAMP_SEATS,
                engine_grille_recess=dict(ENGINE_GRILLE_RECESS),ducktail=dict(DUCKTAIL),
                front_intake=dict(FRONT_INTAKE),
                primary_form='descending central bonnet between raised continuous lamp wings; full rear hips around inset engine deck',
                normals='analytic derivatives of section polynomial/ellipse, ducktail, side contour and rounded nose',
                bounds=dict(z_min=Z_MIN,z_max=Z_MAX),front_hardware_delta_z=-.22,
                shell_parts=len(model.parts)-first,
                shell_triangles=sum(len(p['f']) for p in model.parts[first:]))
