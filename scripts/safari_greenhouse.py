"""Curved stamped window surrounds, real rounded apertures and seated glass.

Each surround spans the supplied common body/roof boundary. The aperture is
an actual rounded contour: painted crown, 10mm reveal, physical rubber seat, then
the curved pane. Glass never fills a sharp full-cabin quad under a thin pipe.
"""
import math
import numpy as np


def _rounded_rectangle(bounds,radii):
    u0,u1,v0,v1=bounds;ru,rv=radii;points=[]
    for cu,cv,start in [(u1-ru,v0+rv,-math.pi/2),(u1-ru,v1-rv,0),
                         (u0+ru,v1-rv,math.pi/2),(u0+ru,v0+rv,math.pi)]:
        for a in np.linspace(start,start+math.pi/2,10):
            points.append((cu+ru*math.cos(a),cv+rv*math.sin(a)))
    return np.asarray(points)


def _inset(poly,distance,metric):
    p=np.asarray(poly)*metric;edge=np.roll(p,-1,axis=0)-p
    edge/=np.linalg.norm(edge,axis=1)[:,None];normal=np.c_[-edge[:,1],edge[:,0]]
    previous=np.roll(normal,1,axis=0)
    return (p+distance*(previous+normal)/np.maximum(1+np.sum(previous*normal,axis=1)[:,None],1e-9))/metric


def _ray(poly,center,direction):
    edge=np.roll(poly,-1,axis=0)-poly;normal=np.c_[-edge[:,1],edge[:,0]]
    denominator=normal@direction;numerator=np.sum((center-poly)*normal,axis=1)
    valid=denominator < -1e-12
    return center+direction*np.min(numerator[valid]/(-denominator[valid]))


def _surface_frame(point,uv):
    u,v=map(float,uv);epsilon=1e-5
    du=(np.asarray(point(u+epsilon,v))-point(u-epsilon,v))/(2*epsilon)
    dv=(np.asarray(point(u,v+epsilon))-point(u,v-epsilon))/(2*epsilon)
    jacobian=np.column_stack((du,dv));normal=np.cross(du,dv)
    normal/=np.linalg.norm(normal)
    return jacobian,normal


def _physical_inset(point,uv,center,width):
    """Offset a closed aperture by metres on its actual mapped surface.

    A fixed UV metric made the compressed quarter-window corners much thinner
    than the nominal seal. Use each local surface metric for the inward
    bracket, then solve the physical distance to the emitted outer edge.
    """
    outer=np.asarray([point(*q) for q in uv],float)
    edge=np.roll(outer,-1,axis=0)-outer
    length2=np.sum(edge*edge,axis=1)
    def distance(p):
        t=np.clip(np.sum((p-outer)*edge,axis=1)/np.maximum(length2,1e-24),0,1)
        return float(np.linalg.norm(p-outer-t[:,None]*edge,axis=1).min())
    inner=[]
    for a in uv:
        # The distance level set is sampled on the same ordered rays as the
        # glass rings. Moving vertices in separately estimated normals can
        # reverse tiny corner cells; radial root finding cannot reorder them.
        direction=center-a;jacobian,_=_surface_frame(point,a)
        metres_per_parameter=np.linalg.norm(jacobian@direction)
        lower=0.;upper=min(.95,width*1.5/metres_per_parameter)
        for _ in range(12):
            if distance(np.asarray(point(*(a+direction*upper))))>=width:break
            upper=min(.999,upper*1.5)
        else:raise ValueError('Requested physical seal does not fit aperture')
        for _ in range(26):
            middle=(lower+upper)*.5
            if distance(np.asarray(point(*(a+direction*middle))))<width:lower=middle
            else:upper=middle
        inner.append(a+direction*((lower+upper)*.5))
    inner=np.asarray(inner)
    return inner,inner-uv



def build_framed_pane(model,name,point,paint,glass,rubber,outward,
                      aperture=(.06,.94,.06,.94),corner=(.08,.08),
                      metric=(1.,1.),reveal=.010,boundary_knots=None,
                      boundary_out=None,rubber_seat_m=.006):
    if not 0<rubber_seat_m<.025:raise ValueError('Invalid physical rubber seat width')
    outward=np.asarray(outward,float);metric=np.asarray(metric,float)
    aperture_loop=_rounded_rectangle(aperture,corner)
    outer=np.array([[0.,0.],[1.,0.],[1.,1.],[0.,1.]])
    center=np.array([(aperture[0]+aperture[1])*.5,(aperture[2]+aperture[3])*.5])
    boundary=[]
    for edge in range(4):
        for t in np.linspace(0,1,17):
            boundary.append(((t,0),(1,t),(1-t,1),(0,1-t))[edge])
    angles=list(np.linspace(0,2*math.pi,49)[:-1])
    angles.extend(math.atan2(v[1]-center[1],v[0]-center[0])%(2*math.pi)
                  for v in np.r_[aperture_loop,np.asarray(boundary)])
    angles=np.unique(np.round(angles,11));directions=np.c_[np.cos(angles),np.sin(angles)]
    aperture_uv=np.array([_ray(aperture_loop,center,d) for d in directions])
    glass_uv,inset_directions=_physical_inset(point,aperture_uv,center,rubber_seat_m)
    outer_uv=np.array([_ray(outer,center,d) for d in directions]);count=len(angles)

    cache={}
    def sample(uv):
        u,v=map(float,uv);key=(round(u,11),round(v,11))
        if key not in cache:
            p=np.asarray(point(u,v),float)
            du=np.asarray(point(min(1,u+1e-4),v))-point(max(0,u-1e-4),v)
            dv=np.asarray(point(u,min(1,v+1e-4)))-point(u,max(0,v-1e-4))
            n=np.cross(du,dv);n/=max(np.linalg.norm(n),1e-12)
            if n@outward<0:n=-n
            cache[key]=(p,n)
        return cache[key]

    # A stamped surround is drawn in one panel direction. Offsetting every
    # point by a separately estimated surface normal made the small polar
    # corner cells cusp where shared cabin boundary samples change tangent.
    # Keep the real pane fixed and form its crown/reveal/seat in this common
    # draw direction, with an exactly zero offset at the exterior boundary.
    draw_direction=sample(center)[1]

    field_orientations={}
    def field_normal(field,t,angle,kind='surface'):
        # Differentiate the actual raised/rolled field, rather than allowing
        # the uneven polar triangles to weight one side of a highlight. The
        # milliradian/milliparameter stencil also spans the tiny piecewise-
        # linear boundary samples supplied by the cabin's shared mesh edges.
        epsilon=.0025
        if t<epsilon:
            dt=-3*field(t,angle)+4*field(t+epsilon,angle)-field(t+2*epsilon,angle)
        elif t>1-epsilon:
            dt=3*field(t,angle)-4*field(t-epsilon,angle)+field(t-2*epsilon,angle)
        else:
            dt=field(t+epsilon,angle)-field(t-epsilon,angle)
        da=field(t,angle+epsilon)-field(t,angle-epsilon)
        n=np.cross(dt,da);length=np.linalg.norm(n)
        if length<1e-12:raise ValueError('Degenerate window field normal: '+name)
        n/=length
        # A connected rolled crown can legitimately turn past the nominal
        # window-facing direction. Orient its parameter field once; forcing
        # every sample toward global X/Z made those valid turns jump 180 deg.
        key=(field,kind)
        if key not in field_orientations:
            t0=.5;a0=0.
            dt0=field(t0+epsilon,a0)-field(t0-epsilon,a0)
            da0=field(t0,a0+epsilon)-field(t0,a0-epsilon)
            reference=np.cross(dt0,da0)
            hint=outward if kind=='surface' else np.asarray(point(*center))-field(t0,a0)
            if kind=='glass_edge':hint=-hint
            field_orientations[key]=1. if reference@hint>=0 else -1.
        return n*field_orientations[key]

    def emit_mesh(suffix,p,f,material,kind='surface',normals=None,closed=False):
        p=np.asarray(p,float)
        # The grid already has a continuous winding. A local facing test
        # split valid rolled corners into alternately reversed triangles.
        face=p[np.asarray(f)];face_normal=np.cross(face[:,1]-face[:,0],face[:,2]-face[:,0])
        desired=(np.asarray(normals).reshape(-1,3)[np.asarray(f)].sum(1) if closed else
                 outward if kind=='surface' else np.asarray(point(*center))-face.mean(1))
        if kind=='glass_edge':desired=-desired
        if np.sum(face_normal*desired)<0:f=[tuple(reversed(tri)) for tri in f]
        model.mesh(name+'.'+suffix,p,f,material,
                   normals=None if normals is None else np.asarray(normals).reshape(-1,3))
        part=model.parts[-1]
        if normals is not None:return
        # A closed UV seam carries one physical normal, including the rounded
        # paint crown. Avoid a specular hairline at the polar tessellation seam.
        sums={}
        for i,v in enumerate(part['p']):sums.setdefault(tuple(np.round(v,6)),[]).append(i)
        for group in sums.values():
            n=part['n'][group].sum(0);n/=max(np.linalg.norm(n),1e-12);part['n'][group]=n

    def emit(suffix,rows,material,kind='surface',normals=None,closed=False):
        points=np.asarray(rows,float);p=points.reshape(-1,3);f=[];nrows,ncols,_=points.shape
        for i in range(nrows-1):
            for j in range(ncols-1):
                a=i*ncols+j;b=a+1;c=a+ncols;d=c+1
                f.extend(((a,b,c),(b,d,c)))
        emit_mesh(suffix,p,f,material,kind,normals,closed)

    def direction_at(angle):return np.array([math.cos(angle),math.sin(angle)])
    def frame_field(t,angle):
        direction=direction_at(angle)
        inner=_ray(aperture_loop,center,direction);edge=_ray(outer,center,direction)
        p,n=sample(inner*(1-t)+edge*t)
        return p+draw_direction*reveal*(1-t)**2

    frame=[];frame_normals=[]
    for t in ((0.,.22,.52,.78,1.) if boundary_knots is None else (0.,.22,.52,.78)):
        row=[];nr=[]
        for inner,edge,angle in zip(aperture_uv,outer_uv,angles):
            uv=inner*(1-t)+edge*t;p,n=sample(uv)
            row.append(p+draw_direction*reveal*(1-t)**2)
            nr.append(field_normal(frame_field,t,angle))
        frame.append(row+[row[0]])
        frame_normals.append(nr+[nr[0]])
    if boundary_knots is None:
        emitted_uv=outer_uv
        emit('stamped_painted_surround',frame,paint,normals=frame_normals)
    else:
        # The outer perimeter is a real shared mesh edge. Sampling the right
        # curve at unrelated polar rays still cut different chords through it
        # (almost 10 mm at the rear glass foot). Retain the existing inner
        # rings/glass and stitch only the final band to the neighbour's knots.
        emitted_uv=np.r_[np.asarray(boundary_knots,float),outer,[[1.,center[1]]]]
        if not np.isfinite(emitted_uv).all() or np.any(emitted_uv< -1e-8) or np.any(emitted_uv>1+1e-8):
            raise ValueError('Invalid shared window boundary: '+name)
        emitted_uv=np.clip(emitted_uv,0,1)
        if not np.all(np.min(np.c_[emitted_uv,1-emitted_uv],axis=1)<1e-8):
            raise ValueError('Window boundary knot is not on an edge: '+name)
        ba=np.arctan2(emitted_uv[:,1]-center[1],emitted_uv[:,0]-center[0])%(2*math.pi)
        ba,indices=np.unique(np.round(ba,11),return_index=True)
        emitted_uv=emitted_uv[indices]
        outer_points=[sample(uv)[0] for uv in emitted_uv]
        outer_normals=[field_normal(frame_field,1.,a) for a in ba]
        points=np.asarray(frame).reshape(-1,3).tolist();normals=np.asarray(frame_normals).reshape(-1,3).tolist()
        f=[];ncols=count+1
        for i in range(len(frame)-1):
            for j in range(count):
                a=i*ncols+j;b=a+1;c=a+ncols;d=c+1
                f.extend(((a,b,c),(b,d,c)))
        inner_start=(len(frame)-1)*ncols;outer_start=len(points)
        points.extend(outer_points+[outer_points[0]])
        normals.extend(outer_normals+[outer_normals[0]])
        aa=np.r_[angles,2*math.pi];bb=np.r_[ba,2*math.pi];i=j=0
        while i<count or j<len(ba):
            next_inner=aa[i+1] if i<count else math.inf
            next_outer=bb[j+1] if j<len(ba) else math.inf
            a=inner_start+i;b=outer_start+j
            if abs(next_inner-next_outer)<1e-10:
                f.extend(((a,a+1,b),(a+1,b+1,b)));i+=1;j+=1
            elif next_inner<next_outer:
                f.append((a,a+1,b));i+=1
            else:
                f.append((a,b+1,b));j+=1
        emit_mesh('stamped_painted_surround',points,f,paint,normals=normals)
    if boundary_out is not None:
        # These float32 coordinates are the actual Model.mesh positions, not
        # a second approximate curve for a neighbouring stamping to follow.
        boundary_out.update(uv=emitted_uv.copy(),points=np.asarray([sample(uv)[0] for uv in emitted_uv],np.float32))
    def lip_field(t,angle):
        uv=_ray(aperture_loop,center,direction_at(angle));p,n=sample(uv)
        return p+draw_direction*(reveal+(.0015-reveal)*t)
    lip=[];lip_normals=[]
    for height in (reveal,reveal*.65,.0015):
        row=[sample(uv)[0]+draw_direction*height for uv in aperture_uv]
        lip.append(row+[row[0]])
        t=(height-reveal)/(.0015-reveal)
        nr=[field_normal(lip_field,t,angle,'reveal') for angle in angles]
        lip_normals.append(nr+[nr[0]])
    emit('painted_aperture_reveal',lip,paint,'reveal',normals=lip_normals)
    gasket=[]
    for t in (0.,.5,1.):
        row=[]
        for a,b in zip(aperture_uv,glass_uv):
            p,n=sample(a*(1-t)+b*t)
            row.append(p+((1-t)*draw_direction+t*n)*(.0015+.001*math.sin(t*math.pi)))
        gasket.append(row)
    # The EPDM extrusion actually seats the pane. Its top contact ring shares
    # the glass edge exactly; a 0.10 mm buried clearance avoids coincident
    # rubber/glass cut faces. The lower seat and outer return close the solid.
    gasket.append([sample(b)[0] for b in glass_uv])
    lower=[]
    for b,direction in zip(glass_uv,inset_directions):
        jacobian,_=_surface_frame(point,b)
        outside=b-direction*(.00010/np.linalg.norm(jacobian@direction))
        p,n=sample(outside);lower.append(p-n*.0032)
    gasket.append(lower)
    gasket.append([sample(a)[0]-sample(a)[1]*.0032 for a in aperture_uv])
    section=np.asarray(gasket);gasket_normals=[]
    for i,row in enumerate(section):
        before=row-section[(i-1)%len(section)];after=section[(i+1)%len(section)]-row
        before/=np.maximum(np.linalg.norm(before,axis=1)[:,None],1e-15)
        after/=np.maximum(np.linalg.norm(after,axis=1)[:,None],1e-15)
        along=np.roll(row,-1,axis=0)-np.roll(row,1,axis=0)
        n=-np.cross(before+after,along);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-15)
        gasket_normals.append(n)
    gasket=[np.r_[row,row[:1]] for row in section]
    gasket_normals=[np.r_[row,row[:1]] for row in gasket_normals]
    gasket.append(gasket[0]);gasket_normals.append(gasket_normals[0])
    emit('continuous_rubber_seat',gasket,rubber,normals=gasket_normals,closed=True)
    pane=[];pane_normals=[]
    for r in np.linspace(1/11,1,11):
        samples=[sample(center+(uv-center)*r) for uv in glass_uv]
        row=[pair[0] for pair in samples];nr=[pair[1] for pair in samples]
        pane.append(row+[row[0]])
        pane_normals.append(nr+[nr[0]])
    emit('curved_glass',pane,glass,normals=pane_normals)
    first=np.array(pane[0]);p=np.r_[np.asarray(point(*center))[None,:],first[:-1]];f=[]
    for j in range(count):
        tri=(0,j+1,(j+1)%count+1)
        if np.cross(p[tri[1]]-p[tri[0]],p[tri[2]]-p[tri[0]])@outward<0:tri=tuple(reversed(tri))
        f.append(tri)
    model.mesh(name+'.glass_center',p,f,glass,
               normals=np.r_[sample(center)[1][None,:],np.asarray(pane_normals[0][:-1])])
    edge=[]
    for inset in (0.,-.0032):
        row=[sample(uv)[0]+sample(uv)[1]*inset for uv in glass_uv]
        edge.append(row+[row[0]])
    emit('real_glass_cut_edge',edge,glass,'glass_edge')
    return dict(name=name,rounded_aperture=True,reveal_m=reveal,rubber_seat_m=rubber_seat_m,
                rubber_seat_construction='closed EPDM extrusion; physical surface inset; glass-edge contact',
                glass_thickness_m=.0032,boundary_samples=count,
                shared_outer_boundary_samples=len(emitted_uv))
