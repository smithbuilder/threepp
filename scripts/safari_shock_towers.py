"""Sheet-metal cabin floor and rear shock enclosures around the live rig.

The checked-in envelope is the original live Safari coilover sweep over full
travel, expanded by 20mm. Fixed clevis load tubes are included separately.
The floor has two open-to-wheelwell notches with exact contour topology; the
towers are hollow closed-top cups, open underneath, rather than solid boxes.
"""
from pathlib import Path
import json
import math
import numpy as np


def _ring(bounds,radius):
    xmin,xmax,zmin,zmax=bounds;points=[]
    for x,z,start in [(xmin,zmin,math.pi),(xmax,zmin,1.5*math.pi),
                       (xmax,zmax,0.),(xmin,zmax,.5*math.pi)]:
        for a in np.linspace(start,start+math.pi/2,7):
            points.append((x+radius*math.cos(a),z+radius*math.sin(a)))
    return np.asarray(points)


def _ear_clip(points):
    """Triangulate one simple concave floor contour, retaining its real cuts."""
    p=np.asarray(points,float);order=list(range(len(p)))
    area=sum(p[i,0]*p[(i+1)%len(p),1]-p[(i+1)%len(p),0]*p[i,1] for i in range(len(p)))
    if area<0:order.reverse()
    faces=[]
    def cross(a,b):return a[0]*b[1]-a[1]*b[0]
    while len(order)>3:
        found=False
        for k,b in enumerate(order):
            a=order[k-1];c=order[(k+1)%len(order)]
            if cross(p[b]-p[a],p[c]-p[b])<=1e-12:continue
            inside=False
            for q in order:
                if q in (a,b,c):continue
                if min(cross(p[b]-p[a],p[q]-p[a]),cross(p[c]-p[b],p[q]-p[b]),
                       cross(p[a]-p[c],p[q]-p[c]))>=-1e-12:
                    inside=True;break
            if inside:continue
            faces.append((a,b,c));order.pop(k);found=True;break
        if not found:raise ValueError('Floor contour cannot be triangulated')
    faces.append(tuple(order));return faces


def build_shock_towers(model,material):
    source=Path(__file__).with_name('safari_rear_shock_envelope.json')
    cfg=json.loads(source.read_text());stations=cfg['stations']
    ys=np.array([v['y'] for v in stations]);keys=('xmin','xmax','zmin','zmax')
    values=np.array([[v[key] for key in keys] for v in stations])
    thick=.0025;rounding=.002;floor_bottom=.4925;floor_top=.5475
    floor_half_width=.81;floor_rear=-1.50;floor_front=.60;cap_y=1.225

    def section(y):
        b=np.array([np.interp(y,ys,values[:,i]) for i in range(4)])
        bounds=[b]
        for leg in cfg['frameLegs']:
            a=np.asarray(leg['start']);end=np.asarray(leg['end']);d=end-a
            radius=leg['radius']+leg['clearance']+.004
            if a[1]-radius<=y<=end[1]+radius:
                # Horizontal slice of the inclined padded cylinder. A small
                # service allowance also covers the clevis-to-tube weld toe.
                t=float(np.clip((y-a[1])/d[1],0,1));c=a+d*t
                rx=radius*math.sqrt(1+(d[0]/d[1])**2)
                rz=radius*math.sqrt(1+(d[2]/d[1])**2)
                bounds.append(np.array([c[0]-rx,c[0]+rx,c[2]-rz,c[2]+rz]))
        bb=np.asarray(bounds)
        return np.array([bb[:,0].min()-.0005,bb[:,1].max()+.0005,
                         bb[:,2].min()-.0005,bb[:,3].max()+.0005])

    bb=np.array([section(y) for y in np.linspace(.465,.57,43)])
    base=np.array([bb[:,0].min(),bb[:,1].max(),bb[:,2].min(),bb[:,3].max()])
    def profile(y):
        b=base.copy() if y<=.57 else section(y)
        if .57<y<.64:
            t=(y-.57)/.07;t=t*t*(3-2*t)
            union=np.array([min(base[0],b[0]),max(base[1],b[1]),min(base[2],b[2]),max(base[3],b[3])])
            b=(1-t)*union+t*b
        # A stamped service flat on the lower outboard collar keeps its
        # OUTER sheet clear of the original padded tyre plane. The envelope
        # itself already has 20mm room plus .5mm service, so consuming the
        # otherwise additional 2mm corner-radius bulge retains >=20.5mm inner
        # axial room here. Both skins move together; sheet thickness stays2.5mm.
        t=float(np.clip((y-.57)/.07,0,1));t=t*t*(3-2*t)
        b[1]-=.002*(1-t)
        return b

    # Exact open notches: circular-corner walls meet this same floor loop.
    r=rounding+thick;xmin,xmax,zmin,zmax=base
    right=[(floor_half_width,zmax+r),(xmin,zmax+r)]
    right += [(xmin+r*math.cos(a),zmax+r*math.sin(a)) for a in np.linspace(math.pi/2,math.pi,7)[1:]]
    right += [(xmin-r,zmin)]
    right += [(xmin+r*math.cos(a),zmin+r*math.sin(a)) for a in np.linspace(math.pi,1.5*math.pi,7)[1:]]
    right += [(floor_half_width,zmin-r)]
    contour=[(-floor_half_width,floor_front),(floor_half_width,floor_front)]+right
    contour += [(floor_half_width,floor_rear),(-floor_half_width,floor_rear)]
    contour += [(-x,z) for x,z in right[::-1]]
    polygon=np.asarray(contour,float);top_faces=_ear_clip(polygon);n=len(polygon)
    points=[(x,floor_top,z) for x,z in polygon]+[(x,floor_bottom,z) for x,z in polygon]
    faces=[]
    for tri in top_faces:
        if np.cross(np.asarray(points[tri[1]])-points[tri[0]],np.asarray(points[tri[2]])-points[tri[0]])[1]<0:tri=tuple(reversed(tri))
        faces.append(tri);faces.append(tuple(i+n for i in reversed(tri)))
    for i in range(n):
        j=(i+1)%n;a,b=polygon[i],polygon[j]
        outer=(abs(abs(a[0])-floor_half_width)<1e-9 and abs(a[0]-b[0])<1e-9)
        outer|=(abs(a[1]-b[1])<1e-9 and (abs(a[1]-floor_rear)<1e-9 or abs(a[1]-floor_front)<1e-9))
        if outer:faces.extend(((i+n,j,i),(i+n,j+n,j)))
    model.mesh('interior.stamped_floor_with_real_shock_well_notches',points,faces,material)

    heights=np.unique(np.r_[.465,floor_bottom,floor_top,.57,np.arange(.58,1.22,.01),cap_y])
    for side in (-1,1):
        rings_inner=[];rings_outer=[]
        for y in heights:
            rings_inner.append([(side*x,y,z) for x,z in _ring(profile(y),rounding)])
            yo=y+thick if y==cap_y else y
            rings_outer.append([(side*x,yo,z) for x,z in _ring(profile(y),rounding+thick)])
        count=len(rings_inner[0])
        for label,rings,direction in [('wheelwell_inner_skin',rings_inner,-1),('cabin_outer_skin',rings_outer,1)]:
            p=np.asarray(rings).reshape(-1,3);f=[]
            for i in range(len(rings)-1):
                center=np.mean(np.asarray(rings)[i:i+2],axis=(0,1))
                for j in range(count):
                    a=i*count+j;b=i*count+(j+1)%count;c=a+count;d=b+count
                    for tri in ((a,b,c),(b,d,c)):
                        radial=p[list(tri)].mean(0)-center;radial[1]=0
                        if np.cross(p[tri[1]]-p[tri[0]],p[tri[2]]-p[tri[0]])@radial*direction<0:tri=tuple(reversed(tri))
                        f.append(tri)
            model.mesh(f'interior.rear_shock_tower.{side}.{label}',p,f,material)
        # Closed sheet roof, with the real shock cavity still open underneath.
        for label,ring,direction in [('cabin_cap',rings_outer[-1],1),('cavity_cap',rings_inner[-1],-1)]:
            p=[np.mean(ring,axis=0)]+list(ring);f=[]
            for j in range(count):
                tri=(0,j+1,(j+1)%count+1)
                if np.cross(np.asarray(p[tri[1]])-p[0],np.asarray(p[tri[2]])-p[0])[1]*direction<0:tri=tuple(reversed(tri))
                f.append(tri)
            model.mesh(f'interior.rear_shock_tower.{side}.{label}',p,f,material)
        p=rings_inner[0]+rings_outer[0];f=[]
        for j in range(count):
            k=(j+1)%count
            for tri in ((j,k,j+count),(k,k+count,j+count)):
                if np.cross(np.asarray(p[tri[1]])-p[tri[0]],np.asarray(p[tri[2]])-p[tri[0]])[1]>0:tri=tuple(reversed(tri))
                f.append(tri)
        model.mesh(f'interior.rear_shock_tower.{side}.lower_sheet_return',p,f,material)

    return dict(interface=cfg['interface'],envelope_source=source.name,
                clearance_m=cfg['clearance'],sheet_thickness_m=thick,
                lower_outboard_collar_inset_m=.002,
                floor=dict(y_top=floor_top,y_bottom=floor_bottom,half_width=floor_half_width,
                           rear_z=floor_rear,front_z=floor_front,right_notch_inner_x=xmin-r,
                           notch_rear_z=zmin-r,notch_front_z=zmax+r),
                tower_cap_y=cap_y+thick,real_open_underbody=True)
