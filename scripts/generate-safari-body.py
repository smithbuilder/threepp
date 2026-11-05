"""Build the original Cinder Safari coupe body. CPU-only, no third-party model.

Units are metres, +Z forward, matching safariDimensions. NumPy/SciPy/Pillow
author smooth mesh patches, real open arches and small PBR maps. GLB is written
directly so the generation is reproducible without Blender or paid services.
The user-provided safari.jpg guides proportions and the expedition outfit;
no source pixels, manufacturer logos or imported geometry enter this model.
"""
from pathlib import Path
import json, math, struct, io, copy, hashlib
import numpy as np
from scipy.interpolate import PchipInterpolator, BPoly
from scipy.spatial import ConvexHull
from functools import lru_cache
from PIL import Image, ImageDraw
from safari_surface_maps import maps, weather_colors, side_maps, side_uv, top_maps, flare_maps, hardware_weather_colors, hardware_finish, hardware_uv, front_maps, rear_maps, front_uv, rear_uv, webbing_base_color
from safari_body_shell import width, upper, body_x, opening, lower_baseline, cabin_cut_width, build_primary_shell, REAR_RECESS
import safari_body_shell as shell
from safari_rear_assembly import build_rear_assembly
from safari_front_recovery import build_front_recovery
from safari_spare_wheel import build_spare_wheel
from safari_rack_mounts import build_rack_mounts
from safari_mirrors import build_mirrors
from safari_shock_towers import build_shock_towers
from safari_greenhouse import build_framed_pane
from safari_panel_gaps import build_panel_gap
from safari_optics import configure_optics_materials, build_spotlight, build_rear_optics, build_front_indicator

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'showcase/assets/safari-body.glb'
TAU=math.tau
SPEC=dict(halfTrack=1.08,halfWheelbase=1.35,tyreRadius=.49,tyreHalfWidth=.17,droop=.28,bump=.50,nominal=.41)
RARCH=SPEC['tyreRadius']+SPEC['bump']-SPEC['nominal']+.035
# The outboard flare lip needs additional real clearance when the steered
# sidewall swings beneath it. The painted body aperture remains unchanged.
FLARE_RADIUS=RARCH+.008

def linear(hex):
    rgb=np.array([(hex>>16)&255,(hex>>8)&255,hex&255],float)/255
    return np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4).tolist()

class Model:
    def __init__(self): self.parts=[];self.materials=[];self.images=[]
    def mat(self,name,color,rough=.6,metal=0,alpha=1,emissive=None):
        m=dict(name=name,pbrMetallicRoughness=dict(baseColorFactor=linear(color)+[alpha],roughnessFactor=rough,metallicFactor=metal),doubleSided=True)
        if alpha<1:m.update(alphaMode='BLEND')
        if emissive is not None:m['emissiveFactor']=linear(emissive)
        self.materials.append(m);return len(self.materials)-1
    def mesh(self,name,p,faces,mat,uv=None,colors=None,normals=None):
        p=np.asarray(p,dtype=np.float32);f=np.asarray(faces,dtype=np.uint32).reshape(-1,3)
        if uv is None:uv=np.c_[p[:,0],p[:,2]]*.4
        uv=np.asarray(uv,np.float32);colors=None if colors is None else np.asarray(colors,np.float32)
        fn=np.cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]])
        f=f[np.linalg.norm(fn,axis=1)>1e-12]
        if not len(f):raise ValueError('Empty/degenerate mesh '+name)
        # Removed aperture faces and open caps must not leave unused zero-
        # normal vertices in the asset. This removes no visible surface.
        used,inverse=np.unique(f,return_inverse=True);p=p[used];uv=uv[used];f=inverse.reshape(-1,3).astype(np.uint32)
        if colors is not None:colors=colors[used]
        if normals is None:
            n=np.zeros_like(p);fn=np.cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]])
            for k in range(3):np.add.at(n,f[:,k],fn)
        else:n=np.asarray(normals,np.float32)[used]
        length=np.linalg.norm(n,axis=1);n/=np.maximum(length[:,None],1e-12)
        self.parts.append(dict(name=name,p=p,f=f,n=n,uv=uv,mat=mat,colors=colors))
    def grid(self,name,p,mat,uv=None,flip=False,weather=False):
        p=np.asarray(p,float);rows,cols,_=p.shape;f=[]
        for i in range(rows-1):
            for j in range(cols-1):
                a=i*cols+j;b=a+1;c=a+cols;d=c+1
                f.extend([(a,b,c),(b,d,c)] if flip else [(a,c,b),(b,c,d)])
        flat=p.reshape(-1,3)
        if uv is not None:uv=np.asarray(uv).reshape(-1,2)
        colors=weather_colors(flat) if weather else None
        self.mesh(name,flat,f,mat,uv,colors)

M=Model()
paint=M.mat('safari.cream_enamel',0xd7cfb4,1.0,0)
M.materials[paint]['extensions']={'KHR_materials_clearcoat':{'clearcoatFactor':.6,'clearcoatRoughnessFactor':.18}}
dark=M.mat('safari.charcoal_flare',0x343b39,.83,0)
rubber=M.mat('safari.rubber',0x272c29,.96)
metal=M.mat('safari.brushed_alloy',0x91958d,.43,.85)
bronze=M.mat('safari.bronze',0x887042,.42,.82)
black=M.mat('safari.coated_steel',0x202a28,.58,0)
window_epdm=M.mat('safari.window_epdm_seal',0x141916,.76,0)
M.materials[window_epdm]['doubleSided']=False
cabin_abs=M.mat('safari.cabin_charcoal_abs_trim',0x252b29,.76,0)
cabin_cloth=M.mat('safari.charcoal_cloth_headliner',0x292b29,.94,0)
M.materials[cabin_abs]['doubleSided']=False
M.materials[cabin_cloth]['doubleSided']=False
glass=M.mat('safari.smoky_glazing',0x263337,.18,0,.60)
lens=M.mat('safari.clear_lamp_glass',0x000000,.06,0,.16)
reflector=M.mat('safari.polished_reflector',0xe3e5df,.12,1)
filament=M.mat('safari.lamp_filament',0xffdf9b,.23,.15,1,0xffd17c)
roundel=M.mat('safari.911_roundel',0xffffff,.62)
M.materials[roundel].update(alphaMode='MASK',alphaCutoff=.35)
red=M.mat('safari.oxide_red',0xb53c2e,.54,.04)
yellow=M.mat('safari.ochre_yellow',0xd5a22b,.56,.03)
orange=M.mat('safari.recovery_orange',0xcc6d27,.79,.01)
olive=M.mat('safari.olive_case',0x646550,.82,.03)
canvas=M.mat('safari.canvas',0x444a42,.96)
tail=M.mat('safari.tail_lens',0x9b2e26,.23,0)
amber=M.mat('safari.amber_lens',0xc8832a,.26,0)
for lamp_material in (tail,amber):
    M.materials[lamp_material]['extensions']={'KHR_materials_clearcoat':{'clearcoatFactor':.8,'clearcoatRoughnessFactor':.08}}
paint_side=len(M.materials);M.materials.append(copy.deepcopy(M.materials[paint]));M.materials[paint_side]['name']='safari.side_enamel_local_dust'
paint_top=len(M.materials);M.materials.append(copy.deepcopy(M.materials[paint]));M.materials[paint_top]['name']='safari.top_enamel_local_dust'
paint_front=len(M.materials);M.materials.append(copy.deepcopy(M.materials[paint]));M.materials[paint_front]['name']='safari.front_fascia_enamel_xy'
paint_rear=len(M.materials);M.materials.append(copy.deepcopy(M.materials[paint]));M.materials[paint_rear]['name']='safari.rear_fascia_enamel_xy'
rear_legend=M.mat('safari.rear_cinder_legend',0xffffff,.62);M.materials[rear_legend].update(alphaMode='MASK',alphaCutoff=.35)
flare_finish=M.mat('safari.flare_coating_local_dust',0xffffff,1,0)
rear_frame=M.mat('safari.rear_coated_steel_weathered',0xffffff,.58,0)
rear_steel=M.mat('safari.satin_exhaust_steel_weathered',0xffffff,.42,.90)
rear_cast=M.mat('safari.engine_cast_alloy_weathered',0xffffff,.72,.65)
rear_soot=M.mat('safari.exhaust_sooted_bore',0x151816,.94,.10)
rear_weld=M.mat('safari.exhaust_weld_heat_band',0x777262,.50,.90)


def basis(axis):
    y=np.asarray(axis,float);y/=np.linalg.norm(y)
    x=np.cross(y,[0,0,1] if abs(y[2])<.9 else [0,1,0]);x/=np.linalg.norm(x)
    z=np.cross(x,y);return np.c_[x,y,z]

def cylinder(name,a,b,r,mat,n=12,r2=None,caps=(True,True)):
    a=np.array(a,float);b=np.array(b,float);B=basis(b-a);p=[];uv=[]
    for k,(c,rad) in enumerate([(a,r),(b,r if r2 is None else r2)]):
        for j in range(n+1):
            t=j*TAU/n;p.append(c+B[:,0]*math.cos(t)*rad+B[:,2]*math.sin(t)*rad);uv.append((j/n,k))
    f=[]
    for j in range(n):f.extend([(j,j+n+1,j+1),(j+1,j+n+1,j+n+2)])
    p.extend([a,b]);uv.extend([(.5,0),(.5,1)])
    for j in range(n):
        if caps[0]:f.append((len(p)-2,j+1,j))
        if caps[1]:f.append((len(p)-1,n+1+j,n+2+j))
    M.mesh(name,p,f,mat,uv)

def ellipsoid(name,center,size,mat,around=24,vertical=12,B=None):
    center=np.array(center);size=np.asarray(size,float);B=np.eye(3) if B is None else np.asarray(B,float)
    p=[];uv=[];normals=[];normal_transform=np.linalg.inv(B).T
    for i in range(vertical+1):
        t=i*math.pi/vertical
        for j in range(around+1):
            a=0. if j==around else j*TAU/around
            unit=np.array([math.sin(t)*math.cos(a),math.cos(t),math.sin(t)*math.sin(a)])
            if i in (0,vertical):unit=np.array([0.,1. if i==0 else -1.,0.])
            p.append(center+B@(unit*size));uv.append((j/around,i/vertical))
            normal=normal_transform@(unit/size);normal/=np.linalg.norm(normal);normals.append(normal)
    f=[]
    for i in range(vertical):
        for j in range(around):
            a=i*(around+1)+j;c=a+around+1
            if i>0:f.append((a,a+1,c))
            if i<vertical-1:f.append((a+1,c+1,c))
    # The UV seam/poles duplicate positions, not the underlying smooth normal.
    M.mesh(name,p,f,mat,uv,normals=normals)

def box(name,c,size,mat,bevel=.025,steps=3):
    c=np.array(c);half=np.array(size)*.5;bevel=min(bevel,float(min(half))*.8);p=[];f=[];uv=[];normals=[]
    for axis in range(3):
        for sign in [-1,1]:
            other=[a for a in range(3) if a!=axis];offset=len(p)
            for i in range(steps+1):
                for j in range(steps+1):
                    q=np.zeros(3);q[axis]=sign*half[axis];q[other[0]]=(i*2/steps-1)*half[other[0]];q[other[1]]=(j*2/steps-1)*half[other[1]]
                    core=np.clip(q,-half+bevel,half-bevel);delta=q-core;q=core+delta/max(np.linalg.norm(delta),1e-12)*bevel
                    p.append(c+q);uv.append((i/steps,j/steps))
                    normals.append(delta/max(np.linalg.norm(delta),1e-12) if bevel>0 else np.eye(3)[axis]*sign)
            for i in range(steps):
                for j in range(steps):
                    a=offset+i*(steps+1)+j;b=a+1;cc=a+steps+1;d=cc+1;tri=[(a,cc,b),(b,cc,d)]
                    normal=np.cross(np.array(p[cc])-p[a],np.array(p[b])-p[a])
                    if normal[axis]*sign<0:tri=[tuple(reversed(t)) for t in tri]
                    f.extend(tri)
    # Exact rounded-box normals keep planar faces flat under structured IBL.
    # Positions, sampling, triangles and UVs retain their original values.
    M.mesh(name,p,f,mat,uv,normals=normals)

def torus(name,c,major,tube,mat,axis=(0,1,0),segments=48,sides=8,stretch=(1,1,1)):
    c=np.array(c);B=basis(axis);p=[];uv=[]
    for i in range(segments+1):
        a=i*TAU/segments
        for j in range(sides+1):
            b=j*TAU/sides;v=np.array([(major+tube*math.cos(b))*math.cos(a),tube*math.sin(b),(major+tube*math.cos(b))*math.sin(a)])*stretch
            p.append(c+B@v);uv.append((i/segments,j/sides))
    f=[]
    for i in range(segments):
        for j in range(sides):
            a=i*(sides+1)+j;cc=a+sides+1;f.extend([(a,a+1,cc),(a+1,cc+1,cc)])
    M.mesh(name,p,f,mat,uv)

def polyline(name,points,r,mat,n=10):
    # One welded sweep: no internal cylinder caps/corrugated bead joints.
    points=np.asarray(points,float)
    keep=np.r_[True,np.linalg.norm(np.diff(points,axis=0),axis=1)>1e-8];points=points[keep]
    if len(points)<2:return
    tangent=np.empty_like(points);tangent[0]=points[1]-points[0];tangent[-1]=points[-1]-points[-2]
    if len(points)>2:tangent[1:-1]=points[2:]-points[:-2]
    tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-9)
    normal=basis(tangent[0])[:,0];rows=[]
    for i,c in enumerate(points):
        if i:
            axis=np.cross(tangent[i-1],tangent[i]);length=np.linalg.norm(axis)
            if length>1e-8:
                axis/=length;angle=math.atan2(length,float(np.dot(tangent[i-1],tangent[i])))
                normal=normal*math.cos(angle)+np.cross(axis,normal)*math.sin(angle)+axis*np.dot(axis,normal)*(1-math.cos(angle))
            normal-=tangent[i]*np.dot(normal,tangent[i]);normal/=max(np.linalg.norm(normal),1e-9)
        binormal=np.cross(tangent[i],normal)
        rows.append([c+r*(normal*math.cos(a)+binormal*math.sin(a)) for a in np.linspace(0,TAU,n+1)])
    p=np.asarray(rows).reshape(-1,3).tolist();faces=[]
    for i in range(len(rows)-1):
        for j in range(n):
            a=i*(n+1)+j;b=a+1;c=a+n+1;d=c+1;faces.extend([(a,b,c),(b,d,c)])
    if np.linalg.norm(points[0]-points[-1])>1e-6:
        # Duplicate only terminal rings for flat end normals; the path has no
        # internal caps or coincident faces at its intermediate samples.
        for end in [0,len(rows)-1]:
            center=len(p);p.append(points[end].tolist());ring=len(p);p.extend(np.asarray(rows[end]).tolist())
            for j in range(n):faces.append((center,ring+j+1,ring+j) if end==0 else (center,ring+j,ring+j+1))
    M.mesh(name,p,faces,mat)

def plate(name,points,mat):
    # A small convex patch, with explicit vertex order and no fake back face.
    p=np.asarray(points);M.mesh(name,p,[(0,i,i+1) for i in range(1,len(p)-1)],mat)


def cabin_lining(part,material,thickness=.002):
    """A physical interior facing bonded behind unchanged exterior paint.

    The cabin face sits 2mm inboard. The existing painted skin is the shared
    backing, so no near-coplanar dark back layer can flicker through cream.
    Boundary returns close the composite sheet at its real apertures. No
    pane, painted reveal or visible exterior position is covered or moved.
    """
    source=part['p'].astype(float);normal=part['n'].astype(float);faces=part['f']
    front=source-normal*thickness;back=source
    points=front.tolist();normals=(-normal).tolist()
    indices=[tuple(reversed(f)) for f in faces]
    # Weld position-only UV seams before finding the real sheet perimeter.
    _,welded=np.unique(np.round(source,6),axis=0,return_inverse=True)
    edges=np.r_[faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]
    keys=np.sort(welded[edges],axis=1)
    _,first,counts=np.unique(keys,axis=0,return_index=True,return_counts=True)
    boundary=edges[first[counts==1]]
    for a,b in boundary:
        q=np.array([front[a],front[b],back[a],back[b]])
        n=np.cross(q[1]-q[0],q[2]-q[0]);length=np.linalg.norm(n)
        if length<1e-12:continue
        n/=length;base=len(points);points.extend(q.tolist());normals.extend([n.tolist()]*4)
        indices.extend(((base,base+1,base+2),(base+1,base+3,base+2)))
    M.mesh('interior.cabin_lining.'+part['name'],points,indices,material,normals=normals)
    assert np.array_equal(part['p'],source.astype(np.float32))
    return dict(source=part['name'],material=M.materials[material]['name'],
                thickness_m=thickness,backing='existing unchanged exterior painted skin',
                retained_apertures=True,closed_boundary_edges=len(boundary))

def rounded_closed_loop(points,rounding=.20,samples=7):
    """Fillet a closed panel loop within its control polygon's bounds."""
    points=np.asarray(points,float)
    if np.linalg.norm(points[0]-points[-1])<1e-9:points=points[:-1]
    result=[]
    for i,c in enumerate(points):
        previous=points[(i-1)%len(points)];following=points[(i+1)%len(points)]
        start=c+(previous-c)*rounding;end=c+(following-c)*rounding
        for t in np.linspace(0,1,samples):
            result.append((1-t)**2*start+2*t*(1-t)*c+t*t*end)
        next_start=following+(c-following)*rounding
        sections=max(2,int(math.ceil(np.linalg.norm(next_start-end)/.010)))
        result.extend(end+(next_start-end)*t for t in np.linspace(0,1,sections+1)[1:-1])
    return np.asarray(result+[result[0]])

def spline(points):return PchipInterpolator([p[0] for p in points],[p[1] for p in points])
# One authoritative primary shell owns bonnet, shoulders, open arches and fascia.
body_metadata=build_primary_shell(M,paint,dark,weather_colors,paint_side=paint_side,paint_top=paint_top)
panel_metadata=[]

class TriangleSurface:
    """Project fine fitted trim onto the emitted render triangles themselves."""
    def __init__(self,prefix,axes,out_axis,sign=1):
        parts=[part for part in M.parts if part['name'].startswith(prefix)]
        if not parts:raise ValueError('No body surface '+prefix)
        self.tri=np.concatenate([part['p'][part['f']] for part in parts]).astype(float)
        self.vertex_normals=np.concatenate([part['n'][part['f']] for part in parts]).astype(float)
        self.axes=list(axes);self.out_axis=out_axis;self.sign=sign
        flat=self.tri[:,:,self.axes];self.a=flat[:,0];self.ab=flat[:,1]-self.a;self.ac=flat[:,2]-self.a
        self.det=self.ab[:,0]*self.ac[:,1]-self.ab[:,1]*self.ac[:,0]
        self.valid=np.abs(self.det)>1e-12
        self.safe_det=np.where(self.valid,self.det,1.)
        normals=np.cross(self.tri[:,1]-self.tri[:,0],self.tri[:,2]-self.tri[:,0])
        self.normals=normals/np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-12)
    def sample(self,q):
        delta=np.asarray(q)-self.a
        u=(delta[:,0]*self.ac[:,1]-delta[:,1]*self.ac[:,0])/self.safe_det
        v=(self.ab[:,0]*delta[:,1]-self.ab[:,1]*delta[:,0])/self.safe_det
        hits=np.flatnonzero(self.valid&(u>=-1e-6)&(v>=-1e-6)&(u+v<=1+1e-6))
        if not len(hits):raise ValueError(f'Fitted trim misses body triangles at {q}')
        points=self.tri[hits,0]+u[hits,None]*(self.tri[hits,1]-self.tri[hits,0])+v[hits,None]*(self.tri[hits,2]-self.tri[hits,0])
        selected=int(np.argmax(points[:,self.out_axis]*self.sign));face=hits[selected]
        normal=self.vertex_normals[face,0]+u[face]*(self.vertex_normals[face,1]-self.vertex_normals[face,0])+v[face]*(self.vertex_normals[face,2]-self.vertex_normals[face,0])
        normal/=max(np.linalg.norm(normal),1e-12)
        return points[selected],normal
    def point(self,q,stand_off=.0026):
        p,n=self.sample(q);return p+n*stand_off

top_surface=TriangleSurface('body.continuous_bonnet_shoulders_rear_deck.',(0,2),1)
side_surfaces={side:TriangleSurface('body.side_with_open_arches.'+str(side),(2,1),0,side) for side in (-1,1)}
# A real stamped floor and sealed hollow wells clear the full live rear rig.
# Their source envelope includes the clevis support tubes, not just springs.
interior_metadata=build_shock_towers(M,black)
box('interior.front_bulkhead',(0,.88,.58),(1.63,.65,.05),black,.015)
box('interior.rear_bulkhead',(0,.86,-1.53),(1.62,.58,.05),black,.015)
for side in [-1,1]:
    # The door trim ends at the actual door; the rear well has its own skin.
    plate('interior.inner_door.'+str(side),[(side*.88,.57,-.75),(side*.88,.57,.48),(side*.88,1.16,.48),(side*.88,1.16,-.75)],black)

# Fitted charcoal flares share the primary shell's actual lower boundary.
flare_limits={}
def flare_angles(axle,radius):
    key=(axle,radius)
    if key not in flare_limits:
        def above(a):
            return .41+radius*math.sin(a)-lower_baseline(axle+radius*math.cos(a))
        low,high=-.40,math.pi/2
        for _ in range(48):
            mid=(low+high)*.5
            if above(mid)<0:low=mid
            else:high=mid
        start=(low+high)*.5
        low,high=math.pi/2,math.pi+.40
        for _ in range(48):
            mid=(low+high)*.5
            if above(mid)>=0:low=mid
            else:high=mid
        flare_limits[key]=(start,(low+high)*.5)
    return flare_limits[key]

for side in [-1,1]:
    # Charcoal bolted flares wrap an opening with thickness and a curved return.
    for axle in [-1.35,1.35]:
        p=[];uv=[]
        fractions=np.linspace(0,1,65)
        for u in fractions:
            row=[];rowuv=[]
            for t in np.linspace(0,1,6):
                r=FLARE_RADIUS+.105*t;start,end=flare_angles(axle,r);a=start+(end-start)*u
                z=axle+r*math.cos(a);y=.41+r*math.sin(a)
                x=float(width(np.clip(z,-2.32,2.30)))+.035+.115*math.sin(t*math.pi/2)
                row.append((side*x,y,z));rowuv.append((a/math.pi,t))
            p.append(row);uv.append(rowuv)
        M.grid(f'arch.flare_shell.{side}.{axle}',p,dark,uv,flip=side<0)
        p=[];uv=[]
        for u in fractions:
            start,end=flare_angles(axle,FLARE_RADIUS);a=start+(end-start)*u
            z=axle+FLARE_RADIUS*math.cos(a);y=.41+FLARE_RADIUS*math.sin(a);x=float(width(np.clip(z,-2.32,2.30)))+.035
            # Fold the lip back into the body while following a larger inner
            # radius. Dropping this return below the opening clipped the
            # 20mm-padded steered tyre near maximum compression.
            inner_r=FLARE_RADIUS+.020;start,end=flare_angles(axle,inner_r);inner_a=start+(end-start)*u
            inner_z=axle+inner_r*math.cos(inner_a);inner_y=.41+inner_r*math.sin(inner_a)
            inner_x=float(width(np.clip(inner_z,-2.32,2.30)))+.035-.055
            p.append([(side*x,y,z),(side*inner_x,inner_y,inner_z)])
            uv.append([(a/math.pi,0),(inner_a/math.pi,.08)])
        M.grid(f'arch.thick_inner_return.{side}.{axle}',p,dark,uv,flip=side>0)
        start,end=flare_angles(axle,FLARE_RADIUS+.073)
        for j,a in enumerate(np.linspace(start+.08,end-.08,11)):
            r=FLARE_RADIUS+.073;z=axle+r*math.cos(a);y=.41+r*math.sin(a);x=float(width(np.clip(z,-2.32,2.30)))+.15
            cylinder(f'arch.bolt.{side}.{axle}.{j}',(side*(x-.006),y,z),(side*(x+.010),y,z),.014,metal,6)

# One greenhouse boundary network owns panes, frame members and gaskets.
# Glass feet meet the actual rendered cabin aperture, not independent nearby
# coordinates; the primary bonnet/deck already provide both painted cowls.
roof_z=np.linspace(-.85,.10,49)
roof_w=spline([(-.85,.70),(-.62,.735),(-.40,.745),(-.15,.735),(.10,.685)])
roof_y=spline([(-1.65,1.17),(-1.35,1.325),(-1.05,1.485),(-.75,1.66),(-.40,1.77),(-.15,1.745),(.10,1.68)])
# The former rear roof corner sat too low for its steep forward tangent. That
# reflex corner rolled the side-window Coons chart back over itself. Raise
# this shared corner 40 mm and fair its slope/curvature into the unchanged
# apex. The same callback seats glass, roof skin and rack feet.
roof_corner_fairing=BPoly.from_derivatives([-.85,-.40],
    [[.040,.20-float(roof_y.derivative()(-.85)),-float(roof_y.derivative(2)(-.85))],
     [0.,0.,0.]])
def roof_centre_height(z):
    # The actual roof spans -.85..+.10. Small rearward extrapolation is also
    # useful when taking its endpoint derivative for the shared rear screen.
    return float(roof_y(z))+(float(roof_corner_fairing(z)) if z<-.40 else 0.)
def roof_crown_height(x,z):
    s=float(x)/float(roof_w(z))
    return roof_centre_height(z)-.13*(1-math.sqrt(max(.10,1-.90*s*s)))
def roof_crown_gradient(x,z):
    w=float(roof_w(z));wd=float(roof_w.derivative()(z));s=float(x)/w
    curve=math.sqrt(max(.10,1-.90*s*s))
    centre_z=float(roof_y.derivative()(z))
    if z<-.40:centre_z+=float(roof_corner_fairing.derivative()(z))
    return -.117*s/(w*curve),centre_z+.117*s*s*wd/(w*curve)
p=[]
for z in roof_z:
    p.append([(float(roof_w(z))*t,roof_crown_height(float(roof_w(z))*t,z),z) for t in np.linspace(-1,1,41)])
M.grid('cabin.rounded_roof_crown',p,paint)
roof_grid=np.asarray(M.parts[-1]['p']).reshape(len(roof_z),41,3).astype(float)
aperture_edges={}
for side in (-1,1):
    part=next(part for part in M.parts if part['name']=='body.continuous_bonnet_shoulders_rear_deck.shoulder_'+str(side))
    grid=part['p'].reshape(-1,9,3)
    aperture_edges[side]=grid[:,0 if side>0 else -1].astype(float)

def interpolate_curve(samples,t,axis):
    return np.array([np.interp(t,samples[:,axis],samples[:,i]) for i in range(3)])

def roof_front_edge(s):return interpolate_curve(roof_grid[-1],s*.685,0)
def roof_rear_edge(s):return interpolate_curve(roof_grid[0],s*.70,0)
def roof_side_edge(side,z):return interpolate_curve(roof_grid[:,-1 if side>0 else 0],z,2)
def body_aperture_edge(side,z):return interpolate_curve(aperture_edges[side],z,2)
foot_sections={}
for label,z in [('front',.56),('rear',-1.65)]:
    part=next(part for part in M.parts if part['name']=='body.continuous_bonnet_shoulders_rear_deck.'+label)
    row=part['p'][np.abs(part['p'][:,2]-z)<1e-6].astype(float)
    foot_sections[label]=row[np.argsort(row[:,0])]
@lru_cache(maxsize=8192)
def screen_front_foot(s):return interpolate_curve(foot_sections['front'],s*.84,0)
@lru_cache(maxsize=8192)
def screen_rear_foot(s):return interpolate_curve(foot_sections['rear'],s*.86,0)

def front_screen_point(t,s):
    p=(1-t)*roof_front_edge(s)+t*screen_front_foot(s)
    bow=math.sin(math.pi*t)
    return p+np.array([0.,(.010+.025*(1-s*s))*bow,.048*(1-s*s)*bow])

rear_glass_w=spline([(-1.65,.86),(-1.35,.83),(-1.05,.76),(-.85,.70)])
@lru_cache(maxsize=8192)
def rear_screen_controls(s):
    low=screen_rear_foot(s);high=roof_rear_edge(s)
    low_dx=float(rear_glass_w.derivative()(-1.65))*.80*s
    high_dx=float(rear_glass_w.derivative()(-.85))*.80*s
    _,body_dx,body_dz,_=shell.upper_derivatives(low[0],-1.65)
    roof_dx,roof_dz=roof_crown_gradient(high[0],-.85)
    return low[1],high[1],body_dx*low_dx+body_dz*.80,roof_dx*high_dx+roof_dz*.80
def rear_screen_point(t,s):
    z=-1.65+.80*t
    low,high,low_tangent,high_tangent=rear_screen_controls(s)
    y=(2*t**3-3*t*t+1)*low+(t**3-2*t*t+t)*low_tangent
    y+=(-2*t**3+3*t*t)*high+(t**3-t*t)*high_tangent
    # A gentle convex bow has zero endpoint slope, retaining the actual body
    # and roof tangent planes rather than adding a kink at the rubber seat.
    crown=(1-s*s)*16*t*t*(1-t)*(1-t)
    return np.array([float(rear_glass_w(z))*s,y+.025*crown,z-.015*crown])

def a_pillar_curve(side,v):return front_screen_point(1-v,side)
@lru_cache(maxsize=2)
def c_pillar_roof_tangent(side):
    low=body_aperture_edge(side,-1.57);high=roof_side_edge(side,-.85)
    roof_dx,roof_dz=roof_crown_gradient(high[0],high[2])
    dx=high[0]-low[0]-side*.004*math.pi
    desired_y=roof_dx*dx+roof_dz*(high[2]-low[2])
    return desired_y-(high[1]-low[1]-.012*math.pi)
def c_pillar_curve(side,v):
    low=body_aperture_edge(side,-1.57);high=roof_side_edge(side,-.85)
    # A small C2 end-tangent correction joins the same actual roof plane.
    tangent_basis=-4*v**3+7*v**4-3*v**5
    return (1-v)*low+v*high+np.array([side*.004*math.sin(math.pi*v),
        .012*math.sin(math.pi*v)+c_pillar_roof_tangent(side)*tangent_basis,0.])

def side_screen_point(side,u,v):
    bottom=body_aperture_edge(side,-1.57+2.13*u)
    top=roof_side_edge(side,-.85+.95*u)
    left=c_pillar_curve(side,v);right=a_pillar_curve(side,v)
    p00=body_aperture_edge(side,-1.57);p10=screen_front_foot(side)
    p01=roof_side_edge(side,-.85);p11=roof_front_edge(side)
    corner=(1-u)*(1-v)*p00+u*(1-v)*p10+(1-u)*v*p01+u*v*p11
    p=(1-v)*bottom+v*top+(1-u)*left+u*right-corner
    return p+np.array([side*.006*math.sin(math.pi*u)*math.sin(math.pi*v),0.,0.])

greenhouse_metadata=[];greenhouse_boundaries={}
SIDE_B_U=(-.36+1.57)/2.13
# Shared physical edges own their tessellation. More points on an unrelated
# polar grid did not make the old surround's chord meet the roof/body chord.
shared_post_t=np.unique(np.r_[np.linspace(0,1,65),.49,.50,.51])
def window_boundary_knots(u0,u1,v0,v1):
    knots=[]
    for axis,value,samples in [(0,0,u0),(0,1,u1),(1,0,v0),(1,1,v1)]:
        for t in samples:
            if -1e-7<=t<=1+1e-7:
                t=float(np.clip(t,0,1))
                if t<1e-7:t=0.
                elif t>1-1e-7:t=1.
                knots.append((value,t) if axis==0 else (t,value))
    return np.unique(np.round(knots,12),axis=0)
def screen_boundary_knots(label):
    roof=roof_grid[-1 if label=='front' else 0]
    rw=.685 if label=='front' else .70;fw=.84 if label=='front' else .86
    rt=(roof[:,0]/rw+1)*.5;ft=(foot_sections[label][:,0]/fw+1)*.5
    return window_boundary_knots(rt if label=='front' else ft,ft if label=='front' else rt,shared_post_t,shared_post_t)
for label,fn,outward,aperture,corner,metric in [
    ('front',lambda u,v:front_screen_point(u,2*v-1),(0,.2,1),(.065,.95,.045,.955),(.085,.055),(.67,1.60)),
    ('rear',lambda u,v:rear_screen_point(u,2*v-1),(0,.2,-1),(.10,.93,.08,.92),(.10,.085),(.85,1.60))]:
    boundary=greenhouse_boundaries[label]={}
    greenhouse_metadata.append(build_framed_pane(M,'cabin.'+label+'_screen',fn,paint,glass,window_epdm,outward,
        aperture=aperture,corner=corner,metric=metric,boundary_knots=screen_boundary_knots(label),boundary_out=boundary,rubber_seat_m=.014))
def actual_pane_edge(boundary,axis,value):
    uv=boundary['uv'];ids=np.flatnonzero(abs(uv[:,axis]-value)<1e-8)
    t=uv[ids,1-axis];order=np.argsort(t)
    return t[order],boundary['points'][ids][order].astype(float)
def edge_point(edge,t):return np.array([np.interp(t,edge[0],edge[1][:,i]) for i in range(3)])
for side in (-1,1):
    for label,lo,hi in [('quarter',0,SIDE_B_U),('door',SIDE_B_U,1)]:
        fn=lambda u,v,side=side,lo=lo,hi=hi:side_screen_point(side,lo+(hi-lo)*u,v)
        aperture=(.10,.93,.13,.89) if label=='quarter' else (.06,.94,.10,.92)
        corner=(.10,.15) if label=='quarter' else (.075,.115)
        hip_u=((aperture_edges[side][:,2]+1.57)/2.13-lo)/(hi-lo)
        roof_u=((roof_grid[:,-1 if side>0 else 0,2]+.85)/.95-lo)/(hi-lo)
        boundary=greenhouse_boundaries[(label,side)]={}
        greenhouse_metadata.append(build_framed_pane(M,f'cabin.{label}_window.{side}',fn,paint,glass,window_epdm,(side,0,0),
            aperture=aperture,corner=corner,metric=(.95,.48),
            boundary_knots=window_boundary_knots(shared_post_t,shared_post_t,hip_u,roof_u),boundary_out=boundary,rubber_seat_m=.010))
    # Narrow C-quarter stamping joins its actual two glazing boundaries.
    rear_edge=actual_pane_edge(greenhouse_boundaries['rear'],1,0 if side<0 else 1)
    quarter_edge=actual_pane_edge(greenhouse_boundaries[('quarter',side)],0,0)
    v_knots=np.unique(np.r_[rear_edge[0],quarter_edge[0]])
    hip_u=(aperture_edges[side][:,2]+1.65)/.08
    u_knots=np.unique(np.r_[np.linspace(0,1,9),hip_u[(hip_u>1e-7)&(hip_u<1-1e-7)]])
    u_knots=u_knots[np.r_[True,np.diff(u_knots)>1e-6]]
    p=[];rows=len(v_knots);cols=len(u_knots)
    low0=screen_rear_foot(side);low1=body_aperture_edge(side,-1.57);tip=roof_rear_edge(side)
    for v in v_knots[:-1]:
        rear=edge_point(rear_edge,v);front=edge_point(quarter_edge,v)
        for u in u_knots:
            lower=body_aperture_edge(side,-1.65+.08*u)
            corner=(1-u)*(1-v)*low0+u*(1-v)*low1+v*tip
            q=(1-u)*rear+u*front+(1-v)*lower+v*tip-corner
            p.append(q)
    tip_index=len(p);p.append(tip);f=[]
    for i in range(rows-2):
        for j in range(cols-1):
            a=i*cols+j;b=a+cols;f.extend(((a,b,a+1),(a+1,b,b+1)))
    for j in range(cols-1):f.append(((rows-2)*cols+j,tip_index,(rows-2)*cols+j+1))
    # This one connected stamping turns from the rear screen into the side.
    # Orient its parameter grid as a whole. Flipping individual faces against
    # a fixed direction reversed a valid lower corner and broke its normals.
    normal_sum=sum((np.cross(p[b]-p[a],p[c]-p[a]) for a,b,c in f),np.zeros(3))
    if normal_sum@np.array([side*.8,.3,-.3])<0:f=[tuple(reversed(tri)) for tri in f]
    M.mesh(f'cabin.shared_boundary_C_quarter.{side}',p,f,paint)

# Real cabin-facing finish on structural frames/roof and the shoulder inner
# sheets. Their opaque cream backfaces caused the apparent windshield cross;
# these closed trim panels retain the exterior and all six glazing openings.
lining_metadata=[]
for part in tuple(M.parts):
    if part['name']=='cabin.rounded_roof_crown':
        lining_metadata.append(cabin_lining(part,cabin_cloth))
    elif (part['name'].startswith('cabin.') and part['name'].endswith('.stamped_painted_surround')) or part['name'].startswith('cabin.shared_boundary_C_quarter.'):
        lining_metadata.append(cabin_lining(part,cabin_abs))
    elif part['name'].startswith('body.continuous_bonnet_shoulders_rear_deck.shoulder_'):
        lining_metadata.append(cabin_lining(part,cabin_abs))

for side in [-1,1]:
    handle_center=side_surfaces[side].point((-.425,1.08),.006)
    box(f'door.handle_recessed_backplate.{side}',handle_center,(.010,.055,.225),black,.004,4)
    lever_x=handle_center[0]+side*.032
    for j,z in enumerate([-.495,-.355]):
        contact=side_surfaces[side].point((z,1.08),.006)
        cylinder(f'door.handle_standoff.{side}.{j}',contact,(lever_x,1.08,z),.009,metal,10)
    polyline(f'door.rounded_pull_lever.{side}',[(lever_x-side*.009,1.08,-.51),(lever_x,1.095,-.495),(lever_x,1.095,-.355),(lever_x-side*.009,1.08,-.34)],.010,metal,10)
    cylinder(f'mirror.stalk.{side}',(side*.88,1.31,.48),(side*1.02,1.37,.45),.018,black)
    door=[(.52,1.158),(.565,1.10),(.575,.95),(.55,.69),(.48,.49),(.32,.47),(-.40,.47),(-.54,.50),(-.64,.75),(-.65,1.10),(-.60,1.145),(-.30,1.162),(.20,1.164)]
    door_loop=rounded_closed_loop(door)
    panel_metadata.append(build_panel_gap(M,f'door.real_panel_gap.{side}','body.side_with_open_arches.'+str(side),
                                          side_surfaces[side],door_loop,dark,(2,1)))

mirror_metadata=build_mirrors(M,dict(paint=paint,rubber=rubber,metal=metal))

# Continuous original stripes: lower sill bands curl up into the rear shoulder.
for side in [-1,1]:
    stripe_z=np.linspace(-.90,.66,65)
    stripe_y=spline([(-.90,1.02),(-.65,.76),(-.44,.50),(.26,.48),(.66,.55)])
    for mat,offset,height in [(red,0,.085),(yellow,.095,.10),(dark,-.035,.025)]:
        p=[]
        for z in stripe_z:
            y=float(stripe_y(z))+offset;x=body_x(z,y)+.005
            p.append([(side*x,y,z),(side*(body_x(z,y+height)+.005),y+height,z)])
        M.grid(f'livery.flowing_side_band.{side}.{mat}',p,mat,weather=True)
    # Conformed atlas follows the door curvature, including every digit.
    centerz=-.02;centery=.91;rad=.245;p=[];uv=[]
    for z in np.linspace(centerz-rad,centerz+rad,37):
        row=[];rowuv=[]
        for y in np.linspace(centery-rad,centery+rad,37):
            row.append((side*(body_x(z,y)+.007),y,z));rowuv.append((.5-side*(z-centerz)/(2*rad),.5-(y-centery)/(2*rad)))
        p.append(row);uv.append(rowuv)
    M.grid(f'livery.conformed_911_roundel.{side}',p,roundel,uv,flip=side>0,weather=True)

# Two unobtrusive bonnet stripes trace its curved centre toward the screen.
for mat,offset,w in [(red,-.12,.065),(yellow,-.04,.065)]:
    p=[]
    for z in np.linspace(1.00,shell.Z_MAX-.02,65):
        p.append([top_surface.point((offset,z),.0013),top_surface.point((offset+w,z),.0013)])
    M.grid(f'livery.bonnet_band.{mat}',p,mat)

bonnet_outline=[(-.56,.78),(.56,.78),(.62,1.05),(.60,1.89),(.52,2.18),(-.52,2.18),(-.60,1.89),(-.62,1.05)]
bonnet_outline=[(x,.78+(z-.78)*(shell.Z_MAX-.12-.78)/(2.18-.78)) for x,z in bonnet_outline]
panel_metadata.append(build_panel_gap(M,'body.real_bonnet_gap','body.continuous_bonnet_shoulders_rear_deck.front',
                                      top_surface,rounded_closed_loop(bonnet_outline),dark,(0,2)))

# Lamp assemblies: physical reflector rim, convex lens, fluting and guard wire.
optics_primitives={key:globals()[key] for key in ('box','cylinder','ellipsoid','torus','polyline','plate')}
optics_materials=configure_optics_materials(M,{key:globals()[key] for key in ('black','rubber','metal','reflector','lens','filament','tail','amber')})
def spotlight(name,x,y,z,r,guard=False,tilt=0):
    return build_spotlight(M,optics_primitives,optics_materials,name,x,y,z,r,guard,tilt)
for seat in body_metadata['lamp_seats']:
    side=-1 if seat['x']<0 else 1
    spotlight(f'lamps.main.{side}',seat['x'],seat['y'],seat['z'],.165,tilt=seat['tilt'])
    build_front_indicator(M,optics_primitives,optics_materials,f'lamps.front_indicator.{side}',seat['x'],.82,2.337)
    spotlight(f'lamps.bumper_aux.{side}',side*.36,.85,2.44,.126,True)
# Separate chambers and moulded lenses fit the existing real rear aperture.
r=body_metadata['rear_recess']
rear_optics=build_rear_optics(M,optics_primitives,optics_materials,r)
rear_z=rear_optics['rear_z'];rear_mid=rear_optics['rear_mid'];rear_width=rear_optics['rear_width']
legend_z=rear_optics['legend_front_z']
# Small original identity, fitted inside the connected lens assembly.
M.mesh('rear.masked_cinder_legend',[(-.27,.901,legend_z),(.27,.901,legend_z),(-.27,.979,legend_z),(.27,.979,legend_z)],[(0,2,1),(1,2,3)],rear_legend,[(1,1),(0,1),(1,0),(0,0)])
for side in [-1,1]:
    for j in range(5):
        slot_y=(r['y_min']+lower_baseline(shell.Z_MIN))*.5
        slot_h=min(.052,(r['y_min']-lower_baseline(shell.Z_MIN))*.65)
        box(f'rear.lower_cooling_slot.{side}.{j}',(side*(.40+j*.040),slot_y,rear_z-.006),(.020,slot_h,.008),black,.003,2)
    for j,y in enumerate([r['y_min']+.009,r['y_max']-.008]):
        screw_x=rear_mid+side*(rear_width*.5+.018)
        cylinder(f'rear.band_screw.{side}.{j}',(screw_x,y,rear_z-.009),(screw_x,y,rear_z-.012),.005,metal,6)

# Fitted louvers sit inside the module's real 20 mm-deep engine opening.
# The module supplies its floor and aperture walls; no black overlay hides paint.
grille=body_metadata['engine_grille_recess']
gx0,gx1,gz0,gz1=(grille[key] for key in ('x_min','x_max','z_min','z_max'))
frame_outline=[(gx0-.003,gz0-.003),(gx1+.003,gz0-.003),(gx1+.003,gz1+.003),(gx0-.003,gz1+.003)]
polyline('rear.engine_grille_perimeter_gasket',[top_surface.point(q,.0024) for q in rounded_closed_loop(frame_outline,0)],.0030,black,6)
for j,z in enumerate(np.linspace(gz0+.025,gz1-.025,8)):
    p=[]
    for dz,drop in [(-.011,.012),(.011,.005),(.011,.0075),(-.011,.0145),(-.011,.012)]:
        p.append([(x,upper(x,z+dz)-drop,z+dz) for x in np.linspace(gx0+.009,gx1-.009,17)])
    M.grid(f'rear.engine_grille_recessed_louver.{j}',p,black)
    for side,x in [(-1,gx0+.009),(1,gx1-.009)]:
        profile=[(x,upper(x,z+dz)-drop,z+dz) for dz,drop in [(-.011,.012),(.011,.005),(.011,.0075),(-.011,.0145)]]
        plate(f'rear.engine_grille_louver_end.{j}.{side}',profile if side<0 else profile[::-1],black)
for side in [-1,1]:
    for z in [gz0+.012,gz1-.012]:
        x=gx0+.012 if side<0 else gx1-.012;y=upper(x,z)-.007
        cylinder(f'rear.engine_grille_retainer.{side}.{z}',(x,y-.002,z),(x,y+.002,z),.005,metal,8)

# A fine, closed engine-cover seam follows the actual deck triangles.
lid_outline=[(gx0-.070,gz1+.060),(gx1+.070,gz1+.060),(gx1+.070,gz0-.060),(gx0-.070,gz0-.060)]
panel_metadata.append(build_panel_gap(M,'rear.real_engine_lid_gap','body.continuous_bonnet_shoulders_rear_deck.rear',
                                      top_surface,rounded_closed_loop(lid_outline),dark,(0,2)))

# The existing nose-following bumper/bullbar keeps its authored position.
# Recovery hardware below is built later in actual chassis coordinates.
polyline('front.wrap_bumper',[(-1.09,.68,2.30),(-.99,.68,2.41),(.99,.68,2.41),(1.09,.68,2.30)],.035,black,12)
polyline('front.lamp_bullbar',[(-.61,.68,2.41),(-.61,.99,2.46),(-.48,1.03,2.46),(.48,1.03,2.46),(.61,.99,2.46),(.61,.68,2.41)],.025,black,12)
rear_metadata=build_rear_assembly(M,dict(box=box,cylinder=cylinder,torus=torus,ellipsoid=ellipsoid,polyline=polyline,plate=plate,basis=basis),dict(frame=rear_frame,alloy=metal,steel=rear_steel,cast=rear_cast,rubber=rubber,soot=rear_soot,weld=rear_weld))

# Expedition roof basket and its restrained, coherent loadout.
for side in [-1,1]:
    polyline(f'rack.lower_rail.{side}',[(side*.73,2.04,-.81),(side*.77,2.04,-.70),(side*.77,2.04,.58),(side*.68,2.04,.70)],.018,black)
    polyline(f'rack.upper_rail.{side}',[(side*.73,2.19,-.81),(side*.77,2.19,-.70),(side*.77,2.19,.58),(side*.68,2.19,.70)],.018,black)
    for z in [-.65,-.25,.25,.60]:cylinder(f'rack.side_upright.{side}.{z}',(side*.77,2.04,z),(side*.77,2.19,z),.012,black)
    for z in [-.58,-.04]:
        roof_height=roof_crown_height(.67,z)
        cylinder(f'rack.gutter_mount.{side}.{z}',(side*.67,roof_height+.17,z),(side*.67,2.05,z),.022,black)
for y in [2.04,2.19]:
    for z in [-.81,.70]:cylinder(f'rack.end_rail.{y}.{z}',(-.71,y,z),(.71,y,z),.018,black)
for j,z in enumerate(np.linspace(-.71,.60,7)):cylinder(f'rack.crossbar.{j}',(-.73,2.04,z),(.73,2.04,z),.012,black)
for j,x in enumerate([-.54,-.18,.18,.54]):spotlight(f'lamps.roof_aux.{j}',x,2.18,.76,.123,True)

# Detached spare: the same carcass/barrel profile as the fitted wheels, with
# open spoke spaces, centre and lug holes. No brake or installed axle hardware.
spare_metadata=build_spare_wheel(M,dict(cylinder=cylinder),
    dict(rubber=rubber,bronze=bronze,black=black,metal=metal),[-.25,2.25,.04])

# Fuel can: bevelled tank, inset X emboss, open handle bridge, filler cap.
box('cargo.red_fuel_can',(.50,2.32,.38),(.25,.48,.21),red,.035,4)
for side in [-1,1]:
    cylinder(f'cargo.can_X_a.{side}',(.50+side*.128,2.15,.30),(.50+side*.128,2.48,.46),.012,red)
    cylinder(f'cargo.can_X_b.{side}',(.50+side*.128,2.15,.46),(.50+side*.128,2.48,.30),.012,red)
polyline('cargo.can_handle',[(.43,2.56,.34),(.43,2.62,.34),(.57,2.62,.34),(.57,2.56,.34)],.022,red)
cylinder('cargo.can_filler',(.50,2.56,.44),(.50,2.59,.44),.038,black,14)

# Gear case has separate lid, corner guards, ribs, latches and carrying handle.
box('cargo.olive_gear_case',(.39,2.23,-.46),(.61,.30,.48),olive,.045,4)
box('cargo.case_lid',(.39,2.395,-.46),(.63,.05,.50),olive,.025,3)
for x in [.13,.65]:
    box(f'cargo.case_latch.{x}',(x,2.29,-.713),(.045,.10,.024),black,.008)
    for z in [-.67,-.25]:box(f'cargo.case_corner.{x}.{z}',(x,2.22,z),(.035,.24,.035),black,.006)
for j,x in enumerate([.22,.39,.56]):box(f'cargo.case_rib.{j}',(x,2.23,-.708),(.020,.22,.018),olive,.004)
polyline('cargo.case_handle',[(.27,2.25,-.728),(.27,2.32,-.728),(.51,2.32,-.728),(.51,2.25,-.728)],.012,black)

# Orange recovery boards have open drainage holes, thickness and raised teeth.
def traction_board(name,c):
    c=np.asarray(c);p=[];f=[];half=np.array([.125,.56]);rounding=.035
    def outer_point(x,z):
        q=np.array([x,z]);core=np.clip(q,-half+rounding,half-rounding);d=q-core
        if np.linalg.norm(d)>rounding:q=core+d/np.linalg.norm(d)*rounding
        return q
    for row in range(10):
        for col in range(3):
            xc=(col+.5)*.25/3-.125;zc=(row+.5)*1.12/10-.56;base=len(p)
            outer=[];inner=[]
            for a in np.arange(8)*TAU/8:
                ca,sa=math.cos(a),math.sin(a);scale=max(abs(ca),abs(sa))
                outer.append(outer_point(xc+(.25/6)*ca/scale,zc+(.112/2)*sa/scale))
                inner.append((xc+.016*ca,zc+.028*sa))
            for y in [.0175,-.0175]:
                p.extend(c+[x,y,z] for x,z in outer);p.extend(c+[x,y,z] for x,z in inner)
            for i in range(8):
                j=(i+1)%8;oi=base+i;oj=base+j;ii=base+8+i;ij=base+8+j
                f.extend([(oi,ii,oj),(oj,ii,ij),(oi+16,oj+16,ii+16),(oj+16,ij+16,ii+16)])
                f.extend([(ii,ii+16,ij),(ij,ii+16,ij+16)])
                a,b=outer[i],outer[j]
                boundary=(col==0 and i in [3,4]) or (col==2 and i in [7,0]) or (row==0 and i in [5,6]) or (row==9 and i in [1,2])
                if boundary:f.extend([(oi,oj,oi+16),(oj,oj+16,oi+16)])
    for z in np.linspace(-.448,.448,9):
        for x in [-.105,-.035,.035,.105]:
            b=len(p);p.extend(c+q for q in [np.array([x-.013,.0175,z-.016]),np.array([x+.013,.0175,z-.016]),np.array([x+.013,.0175,z+.016]),np.array([x-.013,.0175,z+.016]),np.array([x,.0425,z])])
            f.extend([(b,b+1,b+4),(b+1,b+2,b+4),(b+2,b+3,b+4),(b+3,b,b+4)])
    M.mesh(name,p,f,orange)

for layer in range(2):
    x=.83;y=2.12+layer*.055
    traction_board(f'cargo.traction_board_perforated.{layer}',(x,y,-.03))
    for z in [-.39,.31]:box(f'cargo.board_strap.{layer}.{z}',(x,y+.049,z),(.27,.018,.035),black,.005)
for z in [-.39,.31]:
    polyline(f'cargo.board_rack_bracket.{z}',[(.72,2.04,z),(.72,2.10,z),(.96,2.10,z)],.009,black,8)

# Canvas duffel and red Hi-Lift style recovery jack complete the load.
p=[]
for theta in np.linspace(0,math.pi,25):
    u=math.cos(theta);x=-.36+.29*math.copysign(abs(u)**.28,u);row=[]
    for a in np.linspace(0,TAU,33):
        radius=.13*math.sin(theta)*(1+.035*math.sin(7*a+2*theta)+.018*math.sin(11*a-3*theta))
        row.append((x,2.22+radius*math.cos(a),-.64+radius*math.sin(a)))
    p.append(row)
M.grid('cargo.canvas_duffel_soft_folded_shell',p,canvas)
for x in [-.55,-.17]:torus(f'cargo.duffel_strap.{x}',(x,2.22,-.64),.132,.012,black,(1,0,0),24,5)
box('cargo.recovery_jack_beam',(-.82,2.15,-.01),(.038,.050,1.33),red,.006)
box('cargo.recovery_jack_foot',(-.82,2.15,-.70),(.15,.11,.06),red,.010)
box('cargo.recovery_jack_runner',(-.82,2.15,-.35),(.11,.15,.13),red,.012)
for j,z in enumerate(np.linspace(-.60,.60,16)):
    cylinder(f'cargo.jack_hole.{j}',(-.842,2.15,z),(-.845,2.15,z),.010,black,8)

rack_mount_metadata=build_rack_mounts(M,dict(cylinder=cylinder),
    dict(black=black,rubber=rubber,metal=metal),roof_crown_height)

# Seat every load onto the basket floor and mount the basket feet to the true
# curved roof. Translation preserves baked normals and avoids floating props.
for part in M.parts:
    name=part['name'];delta=0
    if name.startswith(('front.','lamps.front_indicator.','lamps.bumper_aux.')):
        # The fitted assembly follows the authored nose length; the axles and
        # suspension specification do not move with the overhang refinement.
        part['p'][:,2]+=shell.Z_MAX-2.30
    if name.startswith(('rack.','lamps.roof_aux.')):delta=-.17
    elif name.startswith('cargo.spare'):delta=-.2096
    elif name.startswith(('cargo.red_fuel','cargo.can_')):delta=-.21
    elif name.startswith(('cargo.olive','cargo.case_')):delta=-.21
    elif name.startswith(('cargo.canvas','cargo.duffel')):delta=-.22
    elif name.startswith(('cargo.traction','cargo.board','cargo.recovery','cargo.jack')):delta=-.17
    part['p'][:,1]+=delta

# Chassis pickups, folded perforated skid and open forged recovery shackles.
# This module authors final chassis coordinates and must follow the legacy
# bumper/lamp translation above so its rail anchors remain authoritative.
front_recovery_metadata=build_front_recovery(M,
    {key:globals()[key] for key in ('box','cylinder','torus','ellipsoid','polyline','plate','basis')},
    {key:globals()[key] for key in ('black','metal','red','rubber')})

def strap(name,points,width,mat=black):
    points=np.asarray(points,float);tangents=np.empty_like(points)
    tangents[0]=points[1]-points[0];tangents[-1]=points[-1]-points[-2]
    tangents[1:-1]=points[2:]-points[:-2]
    tangents/=np.maximum(np.linalg.norm(tangents,axis=1)[:,None],1e-12)
    # Wrap width follows the plane of the cargo loop, including vertical legs.
    # Cross(path,world-up) collapses precisely on those vertical sections.
    _,_,vectors=np.linalg.svd(points-points.mean(axis=0),full_matrices=True)
    across=vectors[-1];across*=1 if across[np.argmax(np.abs(across))]>=0 else -1
    across-=tangents[0]*float(across@tangents[0])
    if np.linalg.norm(across)<1e-8:across=basis(tangents[0])[:,0]
    across/=np.linalg.norm(across);p=[]
    for i,c in enumerate(points):
        if i:
            axis=np.cross(tangents[i-1],tangents[i]);sine=np.linalg.norm(axis)
            if sine>1e-9:
                axis/=sine;angle=math.atan2(sine,float(tangents[i-1]@tangents[i]))
                across=across*math.cos(angle)+np.cross(axis,across)*math.sin(angle)+axis*float(axis@across)*(1-math.cos(angle))
            across-=tangents[i]*float(across@tangents[i]);across/=max(np.linalg.norm(across),1e-12)
        p.append([c-across*width*.5,c+across*width*.5])
    p=np.asarray(p);assert np.allclose(np.linalg.norm(p[:,1]-p[:,0],axis=1),width,atol=1e-8)
    distance=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
    M.grid(name,p,mat,[[[0,d],[1,d]] for d in distance])
# The tensioned strap follows a 3 mm offset of the actual wheel's projected
# convex envelope. Its width runs along Z, so the complete strip stays clear
# of the carcass/tread/valve instead of cutting a corner or floating above it.
spare_points=np.concatenate([part['p'] for part in M.parts if part['name'].startswith('cargo.spare.')])
spare_hull=ConvexHull(spare_points[:,:2]);loop=spare_points[spare_hull.vertices,:2]
edges=np.roll(loop,-1,axis=0)-loop
outward=np.c_[edges[:,1],-edges[:,0]]/np.linalg.norm(edges,axis=1)[:,None]
offset=[]
for i,point in enumerate(loop):
    normals=np.array([outward[i-1],outward[i]])
    offset.append(np.linalg.solve(normals,np.einsum('ij,ij->i',normals,np.array([point,point]))+.003))
offset=np.asarray(offset);left=int(np.argmin(offset[:,0]));right=int(np.argmax(offset[:,0]))
routes=[]
for step in [-1,1]:
    route=[left];at=left
    while at!=right:
        at=(at+step)%len(offset);route.append(at)
    routes.append(offset[route])
upper_route=max(routes,key=lambda route:route[:,1].max())
spare_anchor_y=1.9124
spare_anchor_x=[-.775,.265]
spare_strap_points=[[spare_anchor_x[0],spare_anchor_y,.04]]+[[float(x),float(y),.04] for x,y in upper_route]+[[spare_anchor_x[1],spare_anchor_y,.04]]
strap('cargo.spare_wrap_webbing',spare_strap_points,.045,orange)

# Independent tie-down loops have 53 mm clear width for 45 mm webbing. The
# left loop is welded onto the actual basket side rail; the right stands on
# a short bridge sharing the existing Z=-.055 basket crossbar, not on the tyre.
for side,x in enumerate(spare_anchor_x):
    points=[]
    for yc,zc,start in [(1.9005,.0645,0),(1.8795,.0645,math.pi/2),
                        (1.8795,.0155,math.pi),(1.9005,.0155,3*math.pi/2)]:
        for angle in np.linspace(start,start+math.pi/2,6):
            points.append((x,yc+.0065*math.cos(angle),zc+.0065*math.sin(angle)))
    points.append(points[0])
    polyline(f'cargo.spare_restraint.anchor_loop.{side}',points,.0045,metal,8)
    # A folded webbing end surrounds the upper crossbar, with a short sewn
    # return beside the loaded strap. Its 5.4 mm bend clears the 4.5 mm bar.
    loop_points=[(x+.0054*math.sin(a),1.907+.0054*math.cos(a),.04)
                 for a in np.linspace(0,TAU,13)]
    loop_points.extend([(x+(.003 if side==0 else -.003),1.939,.04),
                        (x+(.005 if side==0 else -.005),1.956,.04)])
    strap(f'cargo.spare_restraint.anchor_webbing_return.{side}',loop_points,.045,orange)
cylinder('cargo.spare_restraint.right_crossbar_bridge',(.265,1.87,-.055),(.265,1.87,.04),.012,black,10)
cylinder('cargo.spare_restraint.left_loop_weld_mount',(-.775,1.873,.04),(-.77,1.873,.04),.009,metal,8)

# The open friction buckle follows the actual left strap direction. Its two
# rollers touch the fabric; it has no opaque plate hiding the webbing slot.
spare_buckle_axis=np.asarray(spare_strap_points[1])-spare_strap_points[0]
spare_buckle_axis/=np.linalg.norm(spare_buckle_axis)
spare_buckle_normal=np.array([-spare_buckle_axis[1],spare_buckle_axis[0],0.])
spare_buckle_center=np.asarray(spare_strap_points[0])+(np.asarray(spare_strap_points[1])-spare_strap_points[0])*.42
spare_buckle_frame=spare_buckle_center+spare_buckle_normal*.004
for z in [-.029,.029]:
    cylinder(f'cargo.spare_restraint.buckle_side.{z}',spare_buckle_frame-spare_buckle_axis*.032+[0,0,z],spare_buckle_frame+spare_buckle_axis*.032+[0,0,z],.0035,metal,8)
for t in [-.032,.032]:
    cylinder(f'cargo.spare_restraint.buckle_end.{t}',spare_buckle_frame+spare_buckle_axis*t-[0,0,.029],spare_buckle_frame+spare_buckle_axis*t+[0,0,.029],.0035,metal,8)
for t in [-.010,.010]:
    cylinder(f'cargo.spare_restraint.buckle_roller.{t}',spare_buckle_frame+spare_buckle_axis*t-[0,0,.024],spare_buckle_frame+spare_buckle_axis*t+[0,0,.024],.004,metal,12)
spare_metadata['fittedBounds']=dict(min=spare_points.min(0).tolist(),max=spare_points.max(0).tolist())
spare_metadata['restraint']=dict(path=spare_strap_points,width=.045,projectedHullOffset=.003,
    fittedAfterCargoSeating=True,anchorLoopClearWidth=.053,anchorX=spare_anchor_x,
    anchorSupports=['left basket rail X=-.77 Y=1.87','bridge to crossbar Z=-.055 Y=1.87'],
    buckleCenter=spare_buckle_center.tolist(),buckleType='open two-roller friction buckle')
strap('cargo.case_wrap_webbing',[(.10,1.885,-.46),(.10,2.21,-.46),(.68,2.21,-.46),(.68,1.885,-.46)],.035)
strap('cargo.can_anchor_webbing',[(.36,1.885,.38),(.36,2.36,.38),(.64,2.36,.38),(.64,1.885,.38)],.027)
for j,(a,b) in enumerate([((.415,1.97,.489),(.585,2.29,.489)),((.585,1.97,.489),(.415,2.29,.489))]):cylinder(f'cargo.can_front_emboss.{j}',a,b,.009,red,8)

# Ratchets, anchor loops and buckles are separate from the webbing itself.
box('cargo.case_ratchet_frame',(.709,2.10,-.46),(.025,.085,.065),metal,.006,3)
box('cargo.case_ratchet_handle',(.728,2.11,-.46),(.018,.048,.085),black,.004,3)
box('cargo.fuel_can_webbing_buckle',(.348,2.15,.38),(.023,.065,.050),metal,.005,3)
for x in [.74]:
    torus(f'cargo.basket_anchor_loop.{x}',(x,1.89,.04),.025,.006,metal,(1,0,0),16,6)
for j,angle in enumerate([.65,2.5]):
    y=2.00+.131*math.cos(angle);z=-.64+.131*math.sin(angle)
    for k,x in enumerate(np.linspace(-.63,-.10,22)):
        cylinder(f'cargo.duffel_panel_stitch.{j}.{k}',(x,y,z),(x+.011,y,z),.0017,paint,5)

def rear_legend_png():
    from PIL import ImageFont
    image=Image.new('RGBA',(512,128),(0,0,0,0));d=ImageDraw.Draw(image)
    font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',78)
    text='CINDER';bounds=d.textbbox((0,0),text,font=font);w=bounds[2]-bounds[0];h=bounds[3]-bounds[1]
    d.text(((512-w)/2-bounds[0],(128-h)/2-bounds[1]),text,font=font,fill=(230,222,201,255))
    out=io.BytesIO();image.save(out,format='PNG',optimize=True);return out.getvalue()

def roundel_png():
    from PIL import ImageFont
    image=Image.new('RGBA',(512,512),(0,0,0,0));d=ImageDraw.Draw(image)
    d.ellipse((9,9,503,503),fill=(227,220,199,255),outline=(37,43,39,255),width=5)
    font_path=Path('C:/Windows/Fonts/arialbd.ttf')
    font=ImageFont.truetype(str(font_path),236) if font_path.exists() else ImageFont.truetype('DejaVuSans-Bold.ttf',225)
    bounds=d.textbbox((0,0),'911',font=font);w,h=bounds[2]-bounds[0],bounds[3]-bounds[1]
    d.text(((512-w)/2-bounds[0],(512-h)/2-bounds[1]),'911',fill=(34,40,36,255),font=font)
    out=io.BytesIO();image.save(out,format='PNG',optimize=True);return out.getvalue()

def grain_normal_png():
    n=256;y,x=np.mgrid[:n,:n];h=.20*np.sin(x*TAU/5)*np.sin(y*TAU/5)+np.random.default_rng(31).random((n,n))*.10
    dy,dx=np.gradient(h);norm=np.dstack([-dx,-dy,np.ones((n,n))]);norm/=np.linalg.norm(norm,axis=2)[...,None]
    rgba=np.dstack([(norm*.5+.5)*255,np.full((n,n),255)])
    return png(rgba)

# Subtle original paint maps: no image/reference pixels are sampled.
def png(array):
    out=io.BytesIO();Image.fromarray(array.astype(np.uint8),'RGBA').save(out,format='PNG',optimize=True);return out.getvalue()

def save():
    document=dict(extensionsUsed=['KHR_materials_clearcoat'],asset=dict(version='2.0',generator='Cinder original CPU parametric body generator'),scene=0,scenes=[dict(nodes=[])],nodes=[],meshes=[],materials=M.materials,buffers=[dict(byteLength=0)],bufferViews=[],accessors=[],images=[],textures=[],samplers=[dict(magFilter=9729,minFilter=9987,wrapS=10497,wrapT=10497)])
    binary=bytearray()
    def view(data,target=None):
        while len(binary)%4:binary.append(0)
        offset=len(binary);binary.extend(data);v=dict(buffer=0,byteOffset=offset,byteLength=len(data))
        if target is not None:v['target']=target
        document['bufferViews'].append(v);return len(document['bufferViews'])-1
    def accessor(a,type,component=5126,target=34962,bounds=False):
        a=np.ascontiguousarray(a,dtype=np.uint32 if component==5125 else np.float32);v=view(a.tobytes(),target)
        x=dict(bufferView=v,componentType=component,count=len(a),type=type)
        if bounds:x.update(min=a.min(axis=0).tolist(),max=a.max(axis=0).tolist())
        document['accessors'].append(x);return len(document['accessors'])-1
    image_names=['cream_enamel','enamel_roughness','enamel_normal','911_roundel','cargo_micrograin','side_local_dust','side_roughness_clearcoat_mask','top_local_dust','top_roughness_clearcoat_mask','rear_cinder_legend','flare_coating_dust','flare_roughness','flare_micro_normal','front_fascia_xy_albedo','front_fascia_xy_roughness_coat','rear_fascia_xy_albedo','rear_fascia_xy_roughness_coat'];image_metadata=[]
    for i,data in enumerate(maps()+[roundel_png(),grain_normal_png()]+side_maps()[:2]+top_maps()+[rear_legend_png()]+flare_maps()+front_maps()[:2]+rear_maps()[:2]):
        with Image.open(io.BytesIO(data)) as img:
            image_metadata.append(dict(index=i,name=image_names[i],width=img.width,height=img.height))
        document['images'].append(dict(name=image_names[i],bufferView=view(data),mimeType='image/png'))
        document['textures'].append(dict(sampler=0,source=i))
    document['materials'][paint]['pbrMetallicRoughness'].update(baseColorFactor=[1,1,1,1],baseColorTexture=dict(index=0),metallicRoughnessTexture=dict(index=1))
    document['materials'][paint]['normalTexture']=dict(index=2,scale=.12)
    document['materials'][paint]['extensions']['KHR_materials_clearcoat']['clearcoatTexture']=dict(index=1)
    document['materials'][roundel]['pbrMetallicRoughness']['baseColorTexture']=dict(index=3)
    document['materials'][paint_side]['pbrMetallicRoughness'].update(baseColorFactor=[1,1,1,1],baseColorTexture=dict(index=5),metallicRoughnessTexture=dict(index=6))
    document['materials'][paint_side]['normalTexture']=dict(index=2,scale=.12)
    document['materials'][paint_side]['extensions']['KHR_materials_clearcoat']['clearcoatTexture']=dict(index=6)
    document['materials'][paint_top]['pbrMetallicRoughness'].update(baseColorFactor=[1,1,1,1],baseColorTexture=dict(index=7),metallicRoughnessTexture=dict(index=8))
    document['materials'][paint_top]['normalTexture']=dict(index=2,scale=.12)
    document['materials'][paint_top]['extensions']['KHR_materials_clearcoat']['clearcoatTexture']=dict(index=8)
    for material,base_image,orm_image in ((paint_front,13,14),(paint_rear,15,16)):
        document['materials'][material]['pbrMetallicRoughness'].update(baseColorFactor=[1,1,1,1],roughnessFactor=1,metallicFactor=0,baseColorTexture=dict(index=base_image),metallicRoughnessTexture=dict(index=orm_image))
        document['materials'][material]['normalTexture']=dict(index=2,scale=.12)
        document['materials'][material]['extensions']['KHR_materials_clearcoat'].update(clearcoatFactor=.6,clearcoatRoughnessFactor=.18,clearcoatTexture=dict(index=orm_image))
    document['materials'][rear_legend]['pbrMetallicRoughness']['baseColorTexture']=dict(index=9)
    document['materials'][flare_finish]['pbrMetallicRoughness'].update(baseColorTexture=dict(index=10),metallicRoughnessTexture=dict(index=11))
    document['materials'][flare_finish]['normalTexture']=dict(index=12,scale=.65)
    def apply_hardware_finish(material,kind,preserve_roughness=False):
        finish=hardware_finish(kind)
        pbr=M.materials[material]['pbrMetallicRoughness']
        pbr.update(metallicFactor=finish['metalness'])
        if not preserve_roughness:pbr['roughnessFactor']=finish['roughness']
        M.materials[material]['normalTexture']=dict(index=4,scale=finish['normal_scale'])
    for material,kind in [(rear_frame,'coated_steel'),(rear_steel,'exhaust'),(rear_cast,'cast_alloy'),(cabin_abs,'trim')]:
        apply_hardware_finish(material,kind)
    apply_hardware_finish(cabin_cloth,'canvas',preserve_roughness=True)
    M.materials[cabin_cloth]['normalTexture']['scale']=.12
    def component_key(name):
        for prefix,key in [(('cargo.case','cargo.olive'),'case'),(('cargo.canvas','cargo.duffel'),'canvas'),
                           (('cargo.red_fuel','cargo.can_'),'fuel_can'),(('cargo.recovery_jack','cargo.jack_'),'jack'),
                           (('cargo.traction','cargo.board_'),'boards'),(('cargo.spare',),'spare')]:
            if name.startswith(prefix):return key
        return None
    component_points={}
    for part in M.parts:
        key=component_key(part['name'])
        if key:component_points.setdefault(key,[]).append(part['p'])
    wear_bounds={key:dict(min=np.concatenate(points).min(0).tolist(),max=np.concatenate(points).max(0).tolist())
                 for key,points in component_points.items()}
    white_copies={}
    def finish_copy(original,kind,absolute_colour=True):
        key=(original,kind,absolute_colour)
        if key not in white_copies:
            material=copy.deepcopy(M.materials[original]);material['name']+='.'+kind+'_local_wear'
            if absolute_colour:material['pbrMetallicRoughness']['baseColorFactor']=[1,1,1,1]
            white_copies[key]=len(M.materials);M.materials.append(material)
            apply_hardware_finish(white_copies[key],kind)
        return white_copies[key]
    for part in M.parts:
        kind=None
        if part['mat'] in (rear_frame,rear_steel,rear_cast):
            kind={rear_frame:'coated_steel',rear_steel:'exhaust',rear_cast:'cast_alloy'}[part['mat']]
        elif part['mat']==black and part['name'].startswith(('rack.','front.wrap_bumper','front.lamp_bullbar','cargo.board_rack_bracket')):
            kind='coated_steel';part['mat']=finish_copy(black,kind)
        elif part['mat']==olive and part['name'].startswith(('cargo.olive','cargo.case')):
            kind='case';part['mat']=finish_copy(olive,kind)
        elif part['mat']==canvas and part['name'].startswith('cargo.canvas'):
            kind='canvas';part['mat']=finish_copy(canvas,kind)
        elif part['mat']==red and part['name'].startswith(('cargo.red_fuel','cargo.can_','cargo.recovery_jack','cargo.jack_')):
            kind='painted_steel';part['mat']=finish_copy(red,kind)
        elif part['mat']==orange and part['name'].startswith('cargo.traction'):
            kind='recovery_board';part['mat']=finish_copy(orange,kind)
        elif part['mat']==rubber and part['name'].startswith('cargo.spare'):
            kind='rubber';part['mat']=finish_copy(rubber,kind)
        if kind is not None:
            part['colors']=hardware_weather_colors(part['p'],kind,part['n'],part_name=part['name'],component_bounds=wear_bounds.get(component_key(part['name'])))
            part['uv']=hardware_uv(part['p'],part['n'],kind)
        if part['name'].startswith('cargo.') and any(token in part['name'] for token in ('webbing','strap')) and part['mat'] in (black,orange):
            source_mat=part['mat']
            part['mat']=finish_copy(source_mat,'canvas',absolute_colour=False)
            M.materials[part['mat']]['pbrMetallicRoughness']['baseColorFactor']=webbing_base_color(0xcc6d27 if source_mat==orange else 0x202a28)
            part['uv']=hardware_uv(part['p'],part['n'],'canvas');part['colors']=None
        if part['mat'] in (cabin_abs,cabin_cloth):
            part['uv']=hardware_uv(part['p'],part['n'],'trim');part['colors']=None
        if part['name'].startswith(('arch.flare_shell.','arch.thick_inner_return.')):
            part['mat']=flare_finish;part['colors']=None
        if part['name'].startswith('body.continuous_bonnet_shoulders_rear_deck.'):
            part['mat']=paint_top
        if part['name'].startswith('body.side_with_open_arches.'):
            part['mat']=paint_side;part['uv']=side_uv(part['p'])
        if part['name']=='body.rounded_front_valance':
            part['mat']=paint_front;part['uv']=front_uv(part['p'])
        if part['name'].startswith('body.rounded_rear_valance.'):
            part['mat']=paint_rear;part['uv']=rear_uv(part['p'])
        if part['mat'] in (paint_side,paint_top,paint_front,paint_rear):
            # All atlas surfaces, including the module's nose and rear fascia,
            # already contain local dirt. Do not apply it a second time.
            part['colors']=None
        if part['mat']==paint_top:
            part['uv']=np.clip(part['uv'],.5/512,1-.5/512)
    for material in [dark,rubber,olive,canvas]:document['materials'][material]['normalTexture']=dict(index=4,scale=.16 if material!=canvas else .28)
    # Preserve descriptive source parts in extras, batch static draw groups by
    # role/material. Hundreds of bolts/straps do not become hundreds of draws.
    batches={}
    def category(name):
        a=name.split('.')
        if a[0]=='body':return name
        if a[0]=='cargo':
            item=a[1]
            if item.startswith('spare'):return 'cargo.full_size_spare'
            if item.startswith(('can','red_fuel')):return 'cargo.red_fuel_can'
            if item.startswith(('case','olive')):return 'cargo.olive_gear_case'
            if item.startswith(('board','traction')):return 'cargo.stacked_traction_boards'
            if item.startswith(('duffel','canvas')):return 'cargo.canvas_duffel'
            return 'cargo.recovery_jack'
        if a[0]=='lamps':return '.'.join(a[:2])
        if a[0]=='arch':return '.'.join(a[:2])
        if a[0]=='livery':return '.'.join(a[:2])
        if a[0]=='cabin':return '.'.join(a[:2])
        if a[0]=='rear' and a[1] in ('frame','engine','exhaust','heat_shield','bash_plate','bumper'):return '.'.join(a[:2])
        return a[0]
    for part in M.parts:
        key=(category(part['name']),part['mat'])
        if key not in batches:batches[key]=dict(name=key[0]+'.'+M.materials[part['mat']]['name'],p=[],f=[],n=[],uv=[],colors=[],mat=part['mat'],names=[],count=0)
        group=batches[key];group['p'].append(part['p']);group['f'].append(part['f']+group['count']);group['n'].append(part['n']);group['uv'].append(part['uv']);group['colors'].append(np.ones((len(part['p']),4),np.float32) if part['colors'] is None else part['colors']);group['names'].append(part['name']);group['count']+=len(part['p'])
    for part in batches.values():
        for attribute in ['p','f','n','uv','colors']:part[attribute]=np.concatenate(part[attribute])
        attrs=dict(POSITION=accessor(part['p'],'VEC3',bounds=True),NORMAL=accessor(part['n'],'VEC3'),TEXCOORD_0=accessor(part['uv'],'VEC2'))
        if part['colors'] is not None:attrs['COLOR_0']=accessor(part['colors'],'VEC4')
        primitive=dict(attributes=attrs,indices=accessor(part['f'].reshape(-1,1),'SCALAR',5125,34963),material=part['mat'])
        document['meshes'].append(dict(name=part['name'],primitives=[primitive],extras=dict(originalParts=part['names'])));document['nodes'].append(dict(name=part['name'],mesh=len(document['meshes'])-1));document['scenes'][0]['nodes'].append(len(document['nodes'])-1)
    while len(binary)%4:binary.append(0)
    document['buffers'][0]['byteLength']=len(binary);js=json.dumps(document,separators=(',',':')).encode();js+=b' '*((-len(js))%4)
    glb=struct.pack('<III',0x46546c67,2,12+8+len(js)+8+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary
    OUT.write_bytes(glb)
    source_paths=[Path(__file__),ROOT/'scripts/safari_body_shell.py',ROOT/'scripts/safari_surface_maps.py',ROOT/'scripts/safari_rear_assembly.py',ROOT/'scripts/safari_front_recovery.py',ROOT/'scripts/safari_spare_wheel.py',ROOT/'scripts/safari_rack_mounts.py',ROOT/'scripts/safari_mirrors.py',ROOT/'scripts/safari_shock_towers.py',ROOT/'scripts/safari_rear_shock_envelope.json',ROOT/'scripts/safari_greenhouse.py',ROOT/'scripts/safari_panel_gaps.py',ROOT/'scripts/safari_optics.py',ROOT/'showcase/assets/safari-enamel-wear-v1.png',ROOT/'showcase/assets/safari-enamel-wear-v1-SOURCE.json']
    source_hashes={path.relative_to(ROOT).as_posix():hashlib.sha256(path.read_bytes()).hexdigest() for path in source_paths}
    atlas_bindings={M.materials[index]['name']:[part['name'] for part in M.parts if part['mat']==index] for index in (paint_side,paint_top,paint_front,paint_rear,flare_finish)}
    component_bounds={}
    for component in ('frame','engine','exhaust','heat_shield','bash_plate','bumper'):
        points=np.concatenate([part['p'] for part in M.parts if part['name'].startswith('rear.'+component+'.')])
        component_bounds[component]=dict(min=points.min(axis=0).tolist(),max=points.max(axis=0).tolist())
    report=dict(spec=SPEC,flareOpeningRadius=FLARE_RADIUS,sourceParts=len(M.parts),drawMeshes=len(batches),vertices=sum(len(p['p']) for p in M.parts),triangles=sum(len(p['f']) for p in M.parts),bytes=len(glb),embeddedImages=len(document['images']),imageMetadata=image_metadata,decodedTextureBytesRgba8=sum(i['width']*i['height']*4 for i in image_metadata),bodyMetadata=body_metadata,greenhouse=greenhouse_metadata,cabinInteriorLining=lining_metadata,panelGaps=panel_metadata,rearOptics=rear_optics,frontRecovery=front_recovery_metadata,spareWheel=spare_metadata,rackMounts=rack_mount_metadata,mirrors=mirror_metadata,interiorEnclosures=interior_metadata,rearAssembly=rear_metadata,rearComponentBounds=component_bounds,atlasBindings=atlas_bindings,sourceHashes=source_hashes,generator='scripts/generate-safari-body.py',source='Original geometry; user safari.jpg silhouette/outfit reference only',limits='Body-only model; parent supplies wheels, live suspension and cockpit. Original Safari-inspired vehicle, not Porsche replica or fitment certification.')
    OUT.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))

if __name__=='__main__':save()
