"""Build the original Cinder Safari coupe body. CPU-only, no third-party model.

Units are metres, +Z forward, matching safariDimensions. NumPy/SciPy/Pillow
author smooth mesh patches, real open arches and small PBR maps. GLB is written
directly so the generation is reproducible without Blender or paid services.
The user-provided safari.jpg guides proportions and the expedition outfit;
no source pixels, manufacturer logos or imported geometry enter this model.
"""
from pathlib import Path
import json, math, struct, io, copy
import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.spatial import Delaunay
from PIL import Image, ImageDraw
from safari_surface_maps import maps, weather_colors, side_maps, side_uv

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'showcase/assets/safari-body.glb'
TAU=math.tau
SPEC=dict(halfTrack=1.08,halfWheelbase=1.35,tyreRadius=.49,tyreHalfWidth=.17,droop=.28,bump=.50,nominal=.41)
RARCH=SPEC['tyreRadius']+SPEC['bump']-SPEC['nominal']+.035

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
    def mesh(self,name,p,faces,mat,uv=None,colors=None):
        p=np.asarray(p,dtype=np.float32);f=np.asarray(faces,dtype=np.uint32).reshape(-1,3)
        if name.startswith(('body.continuous_','body.side_with_','body.rounded_front','livery.bonnet_band')):
            # The central nose rolls down/forward between raised lamp wings;
            # pull its upper edge behind its lower lip without a vertical slab.
            t=np.clip((p[:,2]-1.90)/.40,0,1);t=t*t*(3-2*t)
            mask=np.exp(-((p[:,0]/.70)**6));height=np.clip((p[:,1]-.69)/.24,0,1)
            p[:,2]-=.16*t*mask*height
        n=np.zeros_like(p);fn=np.cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]])
        for k in range(3):np.add.at(n,f[:,k],fn)
        length=np.linalg.norm(n,axis=1);n/=np.maximum(length[:,None],1e-12)
        if uv is None:uv=np.c_[p[:,0],p[:,2]]*.4
        self.parts.append(dict(name=name,p=p,f=f,n=n,uv=np.asarray(uv,dtype=np.float32),mat=mat,colors=None if colors is None else np.asarray(colors,dtype=np.float32)))
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
glass=M.mat('safari.smoky_glazing',0x43565b,.11,.06,.58)
lens=M.mat('safari.clear_lamp_glass',0xd8c793,.11,.08,.48,0x8d703d)
reflector=M.mat('safari.polished_reflector',0xb7beb7,.19,.94)
filament=M.mat('safari.lamp_filament',0xffdf9b,.23,.15,1,0xffd17c)
roundel=M.mat('safari.911_roundel',0xffffff,.62)
M.materials[roundel].update(alphaMode='MASK',alphaCutoff=.35)
red=M.mat('safari.oxide_red',0xb53c2e,.54,.04)
yellow=M.mat('safari.ochre_yellow',0xd5a22b,.56,.03)
orange=M.mat('safari.recovery_orange',0xcc6d27,.79,.01)
olive=M.mat('safari.olive_case',0x646550,.82,.03)
canvas=M.mat('safari.canvas',0x444a42,.96)
tail=M.mat('safari.tail_lens',0x9b2e26,.23,.06,1,0x290908)
amber=M.mat('safari.amber_lens',0xc8832a,.26,.04,1,0x38220a)
paint_side=len(M.materials);M.materials.append(copy.deepcopy(M.materials[paint]));M.materials[paint_side]['name']='safari.side_enamel_local_dust'


def basis(axis):
    y=np.asarray(axis,float);y/=np.linalg.norm(y)
    x=np.cross(y,[0,0,1] if abs(y[2])<.9 else [0,1,0]);x/=np.linalg.norm(x)
    z=np.cross(x,y);return np.c_[x,y,z]

def cylinder(name,a,b,r,mat,n=12,r2=None):
    a=np.array(a,float);b=np.array(b,float);B=basis(b-a);p=[];uv=[]
    for k,(c,rad) in enumerate([(a,r),(b,r if r2 is None else r2)]):
        for j in range(n+1):
            t=j*TAU/n;p.append(c+B[:,0]*math.cos(t)*rad+B[:,2]*math.sin(t)*rad);uv.append((j/n,k))
    f=[]
    for j in range(n):f.extend([(j,j+n+1,j+1),(j+1,j+n+1,j+n+2)])
    p.extend([a,b]);uv.extend([(.5,0),(.5,1)])
    for j in range(n):f.extend([(len(p)-2,j+1,j),(len(p)-1,n+1+j,n+2+j)])
    M.mesh(name,p,f,mat,uv)

def ellipsoid(name,center,size,mat,around=24,vertical=12,B=None):
    center=np.array(center);B=np.eye(3) if B is None else B;p=[];uv=[]
    for i in range(vertical+1):
        t=i*math.pi/vertical
        for j in range(around+1):
            a=j*TAU/around;v=np.array([math.sin(t)*math.cos(a),math.cos(t),math.sin(t)*math.sin(a)])*size
            p.append(center+B@v);uv.append((j/around,i/vertical))
    f=[]
    for i in range(vertical):
        for j in range(around):
            a=i*(around+1)+j;c=a+around+1;f.extend([(a,a+1,c),(a+1,c+1,c)])
    M.mesh(name,p,f,mat,uv)

def box(name,c,size,mat,bevel=.025,steps=3):
    c=np.array(c);half=np.array(size)*.5;bevel=min(bevel,float(min(half))*.8);p=[];f=[];uv=[]
    for axis in range(3):
        for sign in [-1,1]:
            other=[a for a in range(3) if a!=axis];offset=len(p)
            for i in range(steps+1):
                for j in range(steps+1):
                    q=np.zeros(3);q[axis]=sign*half[axis];q[other[0]]=(i*2/steps-1)*half[other[0]];q[other[1]]=(j*2/steps-1)*half[other[1]]
                    core=np.clip(q,-half+bevel,half-bevel);delta=q-core;q=core+delta/max(np.linalg.norm(delta),1e-12)*bevel
                    p.append(c+q);uv.append((i/steps,j/steps))
            for i in range(steps):
                for j in range(steps):
                    a=offset+i*(steps+1)+j;b=a+1;cc=a+steps+1;d=cc+1;tri=[(a,cc,b),(b,cc,d)]
                    normal=np.cross(np.array(p[cc])-p[a],np.array(p[b])-p[a])
                    if normal[axis]*sign<0:tri=[tuple(reversed(t)) for t in tri]
                    f.extend(tri)
    M.mesh(name,p,f,mat,uv)

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

def polyline(name,points,r,mat,n=8):
    for i in range(len(points)-1):cylinder(f'{name}.{i}',points[i],points[i+1],r,mat,n)

def plate(name,points,mat):
    # A small convex patch, with explicit vertex order and no fake back face.
    p=np.asarray(points);M.mesh(name,p,[(0,i,i+1) for i in range(1,len(p)-1)],mat)

def spline(points):return PchipInterpolator([p[0] for p in points],[p[1] for p in points])
width=spline([(-2.32,.83),(-2.12,1.00),(-1.35,1.145),(-.70,1.07),(0,1.00),(.65,1.02),(1.35,1.12),(2.04,1.03),(2.30,.83)])
base=spline([(-2.32,.91),(-1.90,1.00),(-1.35,1.06),(-.7,1.15),(.55,1.15),(1.35,1.03),(2.04,.94),(2.30,.88)])

def upper(x,z):
    w=float(width(z));t=abs(x)/w
    lobes=math.exp(-((z-1.35)/.72)**2)+math.exp(-((z+1.35)/.70)**2)
    lamp_lobe=.22*math.exp(-((abs(x)-.83)/.27)**2-((z-2.04)/.47)**2)
    rear_lift=.18*np.clip((-z-1.94)/.34,0,1)**2*(3-2*np.clip((-z-1.94)/.34,0,1))*(1-.10*t*t)
    shoulder=(.06+lobes*.10)*math.sin(t*math.pi/2)**2-.05*t**8
    return float(base(z))+.040*(1-t*t)+shoulder+lamp_lobe+rear_lift

def opening(z):
    front=np.clip((z-1.94)/.36,0,1);rear=np.clip((-z-1.94)/.38,0,1)
    result=.35+.34*(front*front*(3-2*front))+.25*(rear*rear*(3-2*rear))
    for wheelz in [-1.35,1.35]:
        dz=z-wheelz
        if abs(dz)<RARCH:result=max(result,.41+math.sqrt(max(0,RARCH**2-dz*dz)))
    return result

def body_x(z,y):
    top=upper(float(width(z)),z);t=np.clip((y-.32)/max(.15,top-.32),0,1)
    # Rounded sill/door shoulder rather than a vertical rectangular slab.
    return float(width(z))-.22*(1-t)**2

# Continuous upper shell: rolling front fenders and rear haunches are the same
# curved skin as bonnet and rear deck, not separate flat wings.
zs=np.linspace(-2.32,2.30,151);ts=np.linspace(-1,1,41);p=[];uv=[]
for z in zs:
    row=[];rowuv=[]
    for t in ts:
        x=float(width(z))*t;row.append((x,upper(x,z),z));rowuv.append((t*.5+.5,(z+2.32)/4.62))
    p.append(row);uv.append(rowuv)
M.grid('body.continuous_bonnet_shoulders_rear_deck',p,paint,uv,weather=True)

# Deep side body skins terminate on the actual round wheel opening boundary.
for side in [-1,1]:
    p=[];uv=[]
    for z in zs:
        low=opening(z);high=upper(float(width(z)),z);row=[];rowuv=[]
        for t in np.linspace(0,1,9):
            y=low+(high-low)*t;row.append((side*body_x(z,y),y,z));rowuv.append(((z+2.32)/4.62,y))
        p.append(row);uv.append(rowuv)
    M.grid(f'body.side_with_open_arches.{side}',p,paint,uv,flip=side>0,weather=True)
    # Lower sill has a return into the floor only between the open arches.
    for z0,z1 in [(-2.32,-1.35-RARCH),(-1.35+RARCH,1.35-RARCH),(1.35+RARCH,2.30)]:
        p=[]
        for z in np.linspace(z0,z1,8):p.append([(side*.56,.31,z),(side*body_x(z,.32),.32,z)])
        M.grid(f'body.sill_return.{side}.{z0:.2f}',p,dark)
    # Charcoal bolted flares wrap an opening with thickness and a curved return.
    for axle in [-1.35,1.35]:
        p=[];uv=[]
        angles=np.linspace(-.13,math.pi+.13,65)
        for a in angles:
            row=[];rowuv=[]
            for t in np.linspace(0,1,6):
                r=RARCH+.105*t;z=axle+r*math.cos(a);y=.41+r*math.sin(a)
                x=float(width(np.clip(z,-2.32,2.30)))+.035+.115*math.sin(t*math.pi/2)
                row.append((side*x,y,z));rowuv.append((a/math.pi,t))
            p.append(row);uv.append(rowuv)
        M.grid(f'arch.flare_shell.{side}.{axle}',p,dark,uv)
        p=[]
        for a in angles:
            z=axle+RARCH*math.cos(a);y=.41+RARCH*math.sin(a);x=float(width(np.clip(z,-2.32,2.30)))+.035
            # Fold the lip back into the body while following a larger inner
            # radius. Dropping this return below the opening clipped the
            # 20mm-padded steered tyre near maximum compression.
            inner_r=RARCH+.020;inner_z=axle+inner_r*math.cos(a);inner_y=.41+inner_r*math.sin(a)
            inner_x=float(width(np.clip(inner_z,-2.32,2.30)))+.035-.055
            p.append([(side*x,y,z),(side*inner_x,inner_y,inner_z)])
        M.grid(f'arch.thick_inner_return.{side}.{axle}',p,dark)
        for j,a in enumerate(np.linspace(.10,math.pi-.10,11)):
            r=RARCH+.073;z=axle+r*math.cos(a);y=.41+r*math.sin(a);x=float(width(np.clip(z,-2.32,2.30)))+.15
            cylinder(f'arch.bolt.{side}.{axle}.{j}',(side*(x-.006),y,z),(side*(x+.010),y,z),.014,metal,6)

# Nose/tail closures share the shell boundary and roll under to the sump line.
for z,front in [(2.30,True),(-2.32,False)]:
    p=[]
    for yfrac in np.linspace(0,1,12):
        row=[]
        for t in np.linspace(-1,1,41):
            x=float(width(z))*t;top=upper(x,z);bottom=.69 if front else .60;y=bottom+(top-bottom)*yfrac
            zz=z+(1 if front else -1)*.075*math.sin(yfrac*math.pi)
            row.append((x,y,zz))
        p.append(row)
    M.grid('body.rounded_front_valance' if front else 'body.rounded_rear_valance',p,paint,flip=not front,weather=True)

# Compact curved greenhouse. Roof edge, glass boundary and painted quarters
# share the same sampled curves; no triangular flat glass tent or loose bars.
roof_z=np.linspace(-.85,.10,49)
roof_w=spline([(-.85,.70),(-.62,.735),(-.40,.745),(-.15,.735),(.10,.685)])
roof_y=spline([(-1.65,1.17),(-1.35,1.325),(-1.05,1.485),(-.75,1.66),(-.40,1.77),(-.15,1.745),(.10,1.68)])
p=[]
for z in roof_z:
    p.append([(float(roof_w(z))*t,float(roof_y(z))-.055*t*t,z) for t in np.linspace(-1,1,41)])
M.grid('cabin.rounded_roof_crown',p,paint)

def glazing(name,z0,z1,w0,w1,y0,y1,mat,curve=0):
    p=[]
    for t in np.linspace(0,1,25):
        z=z0+(z1-z0)*t;w=w0+(w1-w0)*t;y=y0+(y1-y0)*t+curve*math.sin(t*math.pi)
        p.append([(w*x,y-.035*x*x,z+.032*(1-x*x)) for x in np.linspace(-1,1,37)])
    M.grid(name,p,mat)
glazing('cabin.front_windscreen',.105,.55,.68,.84,1.67,1.20,glass,.025)
rear_glass_w=spline([(-1.65,.86),(-1.35,.83),(-1.05,.76),(-.85,.70)])
p=[]
for z in np.linspace(-1.65,-.85,49):
    p.append([(float(rear_glass_w(z))*x,float(roof_y(z))-.009-.055*x*x,z) for x in np.linspace(-1,1,37)])
M.grid('cabin.rear_glass_same_continuous_roof_arc',p,glass)
glazing('cabin.front_cowl',.55,.75,.84,.93,1.20,1.20,paint)
glazing('cabin.rear_deck_join',-1.65,-1.76,.86,.99,1.17,1.15,paint)
window_top=spline([(-1.57,1.17)]+[(z,float(roof_y(z))-.065) for z in [-1.35,-1.05,-.85,-.62,-.40,-.15,.10]]+[(.55,1.17)])
def side_glass_point(side,z,t):
    top=float(window_top(z));y=1.17+(top-1.17)*t
    opening_fraction=np.clip((top-1.17)/.15,0,1)
    topx=.91+(float(roof_w(np.clip(z,-.85,.10)))-.012-.91)*opening_fraction
    x=.91+(topx-.91)*t+.012*math.sin(t*math.pi)
    return (side*x,y,z)
for side in [-1,1]:
    zs_window=np.linspace(-1.57,.55,85);p=[]
    for z in zs_window:p.append([side_glass_point(side,z,t) for t in np.linspace(0,1,13)])
    M.grid(f'cabin.curved_side_glazing.{side}',p,glass,flip=side>0)
    for edge in [0,1]:
        pts=[side_glass_point(side,z,edge) for z in zs_window]
        polyline(f'cabin.side_window_seal.{side}.{edge}',pts,.011,black,6)
    polyline(f'cabin.A_pillar.{side}',[(side*.84,1.20,.55),(side*.70,1.605,.15),(side*.685,1.625,.10)],.035,paint,12)
    polyline(f'cabin.front_seal.{side}',[(side*.815,1.205,.545),(side*.666,1.625,.115)],.010,black)
    polyline(f'cabin.C_pillar.{side}',[(side*float(rear_glass_w(z)),float(roof_y(z))-.055,z) for z in np.linspace(-1.65,-.85,33)],.035,paint,10)
    cylinder(f'cabin.B_pillar.{side}',side_glass_point(side,-.36,0),side_glass_point(side,-.36,1),.022,black,10)
    p=[]
    for z in np.linspace(-.85,.10,49):
        q=side_glass_point(side,z,1);p.append([q,(side*float(roof_w(z)),float(roof_y(z))-.055,z)])
    M.grid(f'cabin.closed_roof_edge.{side}',p,paint)
    p=[]
    for z in np.linspace(-1.65,-.85,33):
        t=(z+1.65)/.80;innerx=float(rear_glass_w(z));innery=float(roof_y(z))-.055
        outerx=body_x(z,upper(float(width(z)),z));outery=upper(float(width(z)),z)
        p.append([(side*(innerx+(outerx-innerx)*v),innery+(outery-innery)*v+.035*math.sin(v*math.pi),z) for v in np.linspace(0,1,9)])
    M.grid(f'cabin.sculpted_closed_rear_quarter.{side}',p,paint)
    polyline(f'cabin.beltline.{side}',[(side*.91,1.17,.55),(side*.93,1.17,-.48),(side*.91,1.17,-1.57)],.022,paint,10)
    cylinder(f'door.handle.{side}',(side*1.013,1.08,-.34),(side*1.013,1.08,-.51),.017,metal,10)
    cylinder(f'mirror.stalk.{side}',(side*.88,1.31,.48),(side*1.02,1.37,.45),.018,black)
    ellipsoid(f'mirror.housing.{side}',(side*1.035,1.40,.44),(.13,.075,.08),paint,24,12)
    door=[(.53,1.165),(.55,.94),(.50,.49),(-.50,.49),(-.63,.77),(-.64,1.165)]
    polyline(f'door.shutline.{side}',[(side*(body_x(z,y)+.003),y,z) for z,y in door],.005,dark,6)

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
    for z in np.linspace(1.00,2.28,65):
        p.append([(offset,upper(offset,z)+.004,z),(offset+w,upper(offset+w,z)+.004,z)])
    M.grid(f'livery.bonnet_band.{mat}',p,mat)

# Lamp assemblies: physical reflector rim, convex lens, fluting and guard wire.
def spotlight(name,x,y,z,r,guard=False,tilt=0):
    first_part=len(M.parts)
    cylinder(name+'.bucket',(x,y,z-.065),(x,y,z),r*1.04,black,32)
    torus(name+'.rubber_gasket',(x,y,z+.006),r*1.015,.013,black,(0,0,1),48,8)
    torus(name+'.reflector_rim',(x,y,z+.010),r*.94,.006,metal,(0,0,1),48,6)
    p=[]
    for t in np.linspace(.02,1,13):
        row=[]
        for a in np.linspace(0,TAU,49):
            rr=t*r*.91;row.append((x+rr*math.cos(a),y+rr*math.sin(a),z-.050*(1-t*t)))
        p.append(row)
    M.grid(name+'.recessed_metal_reflector',p,reflector)
    ellipsoid(name+'.bulb',(x,y,z-.012),(r*.13,r*.16,r*.14),lens,16,10)
    cylinder(name+'.filament',(x-r*.05,y,z-.003),(x+r*.05,y,z-.003),r*.012,filament,6)
    p=[]
    for t in np.linspace(.001,1,13):
        row=[]
        for a in np.linspace(0,TAU,49):
            rr=t*r*.93;row.append((x+rr*math.cos(a),y+rr*math.sin(a),z+.012+.022*(1-t*t)))
        p.append(row)
    M.grid(name+'.curved_translucent_lens',p,lens)
    for ring in [.30,.58,.82]:
        torus(name+f'.optic_prism_ring.{ring}',(x,y,z+.012+.022*(1-ring*ring)),r*.93*ring,.0015,lens,(0,0,1),40,4)
    for j,dx in enumerate(np.linspace(-r*.65,r*.65,5)):
        dy=math.sqrt(max(0,(r*.87)**2-dx*dx));cylinder(name+f'.lens_flute.{j}',(x+dx,y-dy,z+.028),(x+dx,y+dy,z+.028),.0013,lens,5)
    if guard:
        for j,t in enumerate([-.50,0,.50]):
            extent=math.sqrt(1-t*t)*r*.92
            cylinder(name+f'.guard_vertical.{j}',(x+t*r,y-extent,z+.060),(x+t*r,y+extent,z+.060),.005,black,6)
            cylinder(name+f'.guard_horizontal.{j}',(x-extent,y+t*r,z+.061),(x+extent,y+t*r,z+.061),.005,black,6)

    if tilt:
        c=math.cos(tilt);ss=math.sin(tilt);rotation=np.array([[1,0,0],[0,c,ss],[0,-ss,c]])
        origin=np.array([x,y,z])
        for part in M.parts[first_part:]:
            part['p']=(part['p']-origin)@rotation.T+origin;part['n']=part['n']@rotation.T
for side in [-1,1]:
    p=[]
    for t in np.linspace(0,1,29):
        z=2.35-.85*t;cx=side*.83;cy=1.00-.12*t;rx=.187+.075*t;ry=.187+.013*t
        row=[]
        for a in np.linspace(0,TAU,65):
            angle=.34*(1-t)**1.5;dy=ry*math.sin(a)
            x=cx+rx*math.cos(a);y=cy+dy*math.cos(angle);zz=z-dy*math.sin(angle)
            y=max(y,opening(zz)+.040)
            row.append((x,y,zz))
        p.append(row)
    M.grid(f'body.lamp_nacelle_flowing_into_wing.{side}',p,paint,weather=True)
for side in [-1,1]:
    spotlight(f'lamps.main.{side}',side*.83,1.00,2.36,.165,tilt=.34)
    box(f'lamps.front_indicator.{side}',(side*.83,.82,2.337),(.30,.075,.045),amber,.015)
    box(f'lamps.rear_tail.{side}',(side*.64,.93,-2.365),(.54,.09,.045),tail,.012)
    for j in range(5):box(f'lamps.tail_flute.{side}.{j}',(side*.64+(j-2)*.085,.93,-2.391),(.004,.072,.003),dark,.001,1)
    spotlight(f'lamps.bumper_aux.{side}',side*.36,.85,2.44,.126,True)
box('rear.black_tail_panel',(0,.94,-2.362),(1.63,.19,.035),black,.02)
for side in [-1,1]:box(f'lamps.rear_tail_overlay.{side}',(side*.64,.93,-2.392),(.54,.085,.024),tail,.01)

# Ducktail rise is now authored into upper(), the same continuous body/deck
# skin. A small curved trailing return gives it thickness without an upright wall.
p=[]
z=-2.32;w=float(width(z))
for offset in [0,.025]:p.append([(x,upper(x,z)-offset,z+offset*.55) for x in np.linspace(-w,w,41)])
M.grid('rear.thin_integrated_ducktail_edge',p,paint)
for j,z in enumerate(np.linspace(-1.94,-1.76,9)):
    y=upper(0,z)+.008;box(f'rear.engine_grille_slot.{j}',(0,y,z),(.85,.012,.013),black,.004)

# Tubular bumpers and bash plate. Delaunay triangulation removes the real holes
# from the metal sheet; these are not black circular decals.
polyline('front.wrap_bumper',[(-1.09,.68,2.30),(-.99,.68,2.41),(.99,.68,2.41),(1.09,.68,2.30)],.035,black,12)
polyline('front.lamp_bullbar',[(-.61,.68,2.41),(-.61,.99,2.46),(-.48,1.03,2.46),(.48,1.03,2.46),(.61,.99,2.46),(.61,.68,2.41)],.025,black,12)
polyline('rear.wrap_cage',[(-1.05,.61,-2.28),(-.94,.52,-2.46),(.94,.52,-2.46),(1.05,.61,-2.28)],.034,black,12)
for side in [-1,1]:
    cylinder(f'rear.diagonal_brace.{side}',(side*.94,.52,-2.46),(side*.65,.91,-2.36),.024,metal,10)
    torus(f'front.red_recovery_shackle.{side}',(side*.66,.51,2.42),.059,.015,red,(0,0,1),24,6,(1,1,1.35))
    box(f'front.shackle_mount.{side}',(side*.66,.61,2.39),(.075,.065,.09),metal,.008)
    cylinder(f'rear.exhaust_tip.{side}',(side*.14,.42,-2.24),(side*.14,.40,-2.55),.043,metal,16)
    cylinder(f'rear.exhaust_dark_bore.{side}',(side*.14,.40,-2.553),(side*.14,.40,-2.556),.031,black,16)

def skid():
    holes=[(x,y,.043) for y in [-.105,0,.105] for x in np.linspace(-.55,.55,8)]
    pts=[(-.73,-.21),(.73,-.21),(.73,.21),(-.73,.21)]
    for x,y,r in holes:
        for a in np.linspace(0,TAU,13)[:-1]:pts.append((x+r*math.cos(a),y+r*math.sin(a)))
    pts=np.asarray(pts);tri=Delaunay(pts).simplices;keep=[]
    for f in tri:
        c=pts[f].mean(axis=0)
        if not any((c[0]-x)**2+(c[1]-y)**2<r*r*.98 for x,y,r in holes):keep.append(f)
    p=[(x,.45+y*.84,2.35+y*.54) for x,y in pts];M.mesh('front.actual_perforated_skid_plate',p,keep,metal,pts)
skid()

# Expedition roof basket and its restrained, coherent loadout.
for side in [-1,1]:
    polyline(f'rack.lower_rail.{side}',[(side*.73,2.04,-.81),(side*.77,2.04,-.70),(side*.77,2.04,.58),(side*.68,2.04,.70)],.018,black)
    polyline(f'rack.upper_rail.{side}',[(side*.73,2.19,-.81),(side*.77,2.19,-.70),(side*.77,2.19,.58),(side*.68,2.19,.70)],.018,black)
    for z in [-.65,-.25,.25,.60]:cylinder(f'rack.side_upright.{side}.{z}',(side*.77,2.04,z),(side*.77,2.19,z),.012,black)
    for z in [-.58,-.04]:
        roof_height=float(roof_y(z))-.055*(.67/float(roof_w(z)))**2
        cylinder(f'rack.gutter_mount.{side}.{z}',(side*.67,roof_height+.17,z),(side*.67,2.05,z),.022,black)
for y in [2.04,2.19]:
    for z in [-.81,.70]:cylinder(f'rack.end_rail.{y}.{z}',(-.71,y,z),(.71,y,z),.018,black)
for j,z in enumerate(np.linspace(-.71,.60,7)):cylinder(f'rack.crossbar.{j}',(-.73,2.04,z),(.73,2.04,z),.012,black)
for j,x in enumerate([-.54,-.18,.18,.54]):spotlight(f'lamps.roof_aux.{j}',x,2.18,.76,.123,True)

# Full-size horizontal spare, with a real hollow centre and visible tread.
spare=np.array([-.25,2.25,.04]);torus('cargo.spare_tyre',spare,.37,.12,rubber,(0,1,0),56,12,stretch=(1,1.42,1))
torus('cargo.spare_bead',spare+[0,.165,0],.244,.018,bronze,(0,1,0),40,6)
cylinder('cargo.spare_wheel_barrel',spare-[0,.145,0],spare+[0,.145,0],.244,bronze,32)
for j in range(8):
    a=j*TAU/8;cylinder(f'cargo.spare_spoke.{j}',spare+[.07*math.cos(a),.165,.07*math.sin(a)],spare+[.23*math.cos(a),.165,.23*math.sin(a)],.018,bronze)
for j in range(44):
    a=j*TAU/44
    for side in [-1,1]:
        c=spare+[.478*math.cos(a),side*.085,.478*math.sin(a)];box(f'cargo.spare_tread.{j}.{side}',c,(.055,.060,.048),rubber,.007,1)
box('cargo.spare_strap_long',(-.25,2.44,.04),(.045,.025,.88),orange,.006)
box('cargo.spare_strap_cross',(-.25,2.45,.04),(.89,.025,.045),orange,.006)

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

# Orange traction boards carry real raised teeth and drain slots.
for layer in range(2):
    x=.83;y=2.12+layer*.055
    box(f'cargo.traction_board.{layer}',(x,y,-.03),(.21,.035,1.12),orange,.018,3)
    for j,z in enumerate(np.linspace(-.50,.44,15)):
        for dx in [-.065,0,.065]:box(f'cargo.board_tooth.{layer}.{j}.{dx}',(x+dx,y+.026,z),(.027,.026,.035),orange,.004,1)
    for z in [-.39,.31]:box(f'cargo.board_strap.{layer}.{z}',(x,y+.034,z),(.25,.018,.035),black,.005)

# Canvas duffel and red Hi-Lift style recovery jack complete the load.
cylinder('cargo.canvas_duffel',(-.65,2.22,-.64),(-.07,2.22,-.64),.13,canvas,20)
for x in [-.55,-.17]:torus(f'cargo.duffel_strap.{x}',(x,2.22,-.64),.132,.012,black,(1,0,0),24,5)
box('cargo.recovery_jack_beam',(-.82,2.15,-.01),(.038,.050,1.33),red,.006)
box('cargo.recovery_jack_foot',(-.82,2.15,-.70),(.15,.11,.06),red,.010)
box('cargo.recovery_jack_runner',(-.82,2.15,-.35),(.11,.15,.13),red,.012)
for j,z in enumerate(np.linspace(-.60,.60,16)):
    cylinder(f'cargo.jack_hole.{j}',(-.842,2.15,z),(-.845,2.15,z),.010,black,8)

# Smooth the true shared-position loft seams, preserving hard hardware edges.
seam_parts=[part for part in M.parts if part['name'].startswith(('body.continuous_','body.side_with_','body.rounded_'))]
seams={}
for part in seam_parts:
    for i,point in enumerate(part['p']):seams.setdefault(tuple(np.round(point,5)),[]).append((part,i))
for entries in seams.values():
    if len(entries)<2:continue
    normal=sum((part['n'][i] for part,i in entries),np.zeros(3));normal/=max(np.linalg.norm(normal),1e-9)
    for part,i in entries:part['n'][i]=normal

# Seat every load onto the basket floor and mount the basket feet to the true
# curved roof. Translation preserves baked normals and avoids floating props.
for part in M.parts:
    name=part['name'];delta=0
    if name.startswith(('rack.','lamps.roof_aux.')):delta=-.17
    elif name.startswith('cargo.spare'):delta=-.2096
    elif name.startswith(('cargo.red_fuel','cargo.can_')):delta=-.21
    elif name.startswith(('cargo.olive','cargo.case_')):delta=-.21
    elif name.startswith(('cargo.canvas','cargo.duffel')):delta=-.22
    elif name.startswith(('cargo.traction','cargo.board','cargo.recovery','cargo.jack')):delta=-.17
    part['p'][:,1]+=delta

def strap(name,points,width,mat=black):
    p=[]
    for i,c in enumerate(points):
        c=np.array(c);d=np.array(points[min(i+1,len(points)-1)])-np.array(points[max(i-1,0)])
        across=np.cross(d,[0,1,0]);across/=max(np.linalg.norm(across),1e-8)
        p.append([c-across*width*.5,c+across*width*.5])
    M.grid(name,p,mat)
strap('cargo.spare_wrap_webbing',[(-.73,1.885,.04),(-.68,2.15,.04),(-.52,2.23,.04),(.02,2.23,.04),(.19,2.15,.04),(.24,1.885,.04)],.045,orange)
strap('cargo.case_wrap_webbing',[(.10,1.885,-.46),(.10,2.21,-.46),(.68,2.21,-.46),(.68,1.885,-.46)],.035)
strap('cargo.can_anchor_webbing',[(.36,1.885,.38),(.36,2.36,.38),(.64,2.36,.38),(.64,1.885,.38)],.027)
for j,(a,b) in enumerate([((.415,1.97,.489),(.585,2.29,.489)),((.585,1.97,.489),(.415,2.29,.489))]):cylinder(f'cargo.can_front_emboss.{j}',a,b,.009,red,8)

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
    image_names=['cream_enamel','enamel_roughness','enamel_normal','911_roundel','cargo_micrograin','side_local_dust','side_roughness_clearcoat_mask']
    for i,data in enumerate(maps()+[roundel_png(),grain_normal_png()]+side_maps()[:2]):
        document['images'].append(dict(name=image_names[i],bufferView=view(data),mimeType='image/png'))
        document['textures'].append(dict(sampler=0,source=i))
    document['materials'][paint]['pbrMetallicRoughness'].update(baseColorFactor=[1,1,1,1],baseColorTexture=dict(index=0),metallicRoughnessTexture=dict(index=1))
    document['materials'][paint]['normalTexture']=dict(index=2,scale=.12)
    document['materials'][roundel]['pbrMetallicRoughness']['baseColorTexture']=dict(index=3)
    document['materials'][paint_side]['pbrMetallicRoughness'].update(baseColorFactor=[1,1,1,1],baseColorTexture=dict(index=5),metallicRoughnessTexture=dict(index=6))
    document['materials'][paint_side]['normalTexture']=dict(index=2,scale=.12)
    document['materials'][paint_side]['extensions']['KHR_materials_clearcoat']['clearcoatTexture']=dict(index=6)
    for part in M.parts:
        if part['name'].startswith('body.side_with_open_arches.'):
            part['mat']=paint_side;part['uv']=side_uv(part['p']);part['colors']=None
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
    report=dict(spec=SPEC,sourceParts=len(M.parts),drawMeshes=len(batches),vertices=sum(len(p['p']) for p in M.parts),triangles=sum(len(p['f']) for p in M.parts),bytes=len(glb),generator='scripts/generate-safari-body.py',source='Original geometry; user safari.jpg silhouette/outfit reference only',limits='Body-only model; parent supplies wheels, live suspension and cockpit. Original Safari-inspired vehicle, not Porsche replica or fitment certification.')
    OUT.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))

if __name__=='__main__':save()
