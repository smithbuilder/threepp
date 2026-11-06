"""Original Baja 427 first-candidate truck, CPU-only reproducible GLB authoring.

No imported geometry or copied reference pixels. NumPy/Pillow author shaped
panels, true open wheel arches, separate wheel/suspension pivots and PBR maps.
Coordinates: metres, Y up, Z forward. Body origin ground offset: +0.07m.
"""
from pathlib import Path
import io, json, math, struct, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'showcase/assets/baja-427.glb'
TAU=math.tau
def linear(c):
    a=np.array([(c>>16)&255,(c>>8)&255,c&255])/255
    return np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4).tolist()

class Model:
    def __init__(self):self.nodes=[];self.parts=[];self.materials=[];self.images=[];self.parent=0
    def node(self,name,parent=None,translation=None,rotation=None,extras=None):
        n={'name':name,'children':[]}
        if translation is not None:n['translation']=list(translation)
        if rotation is not None:n['rotation']=list(rotation)
        if extras:n['extras']=extras
        i=len(self.nodes);self.nodes.append(n)
        if parent is not None:self.nodes[parent]['children'].append(i)
        return i
    def mat(self,name,color,rough=.65,metal=0,emissive=None,alpha=1):
        m=dict(name='baja427.'+name,pbrMetallicRoughness=dict(baseColorFactor=linear(color)+[alpha],roughnessFactor=rough,metallicFactor=metal),doubleSided=False)
        if alpha<1:m.update(alphaMode='BLEND',doubleSided=True)
        if emissive is not None:m['emissiveFactor']=linear(emissive)
        self.materials.append(m);return len(self.materials)-1
    def mesh(self,name,p,f,mat,uv=None,normals=None):
        p=np.asarray(p,np.float32);f=np.asarray(f,np.uint32).reshape(-1,3)
        fn=np.cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]])
        f=f[np.linalg.norm(fn,axis=1)>1e-10]
        if len(f)==0:raise ValueError(name)
        n=np.zeros_like(p) if normals is None else np.asarray(normals,np.float32)
        if normals is None:
            fn=np.cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]])
            for k in range(3):np.add.at(n,f[:,k],fn)
        n/=np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-10)
        if uv is None:
            axis=int(np.argmax(np.abs(n).mean(0)))
            if axis==1:uv=np.c_[(p[:,0]+1.3)/2.6,(2.7-p[:,2])/5.4]
            elif axis==2:uv=np.c_[(p[:,0]+1.3)/2.6,1-p[:,1]/2]
            else:uv=np.c_[(2.45-p[:,2])/4.9,1-p[:,1]/2]
        else:uv=np.asarray(uv,np.float32)
        self.parts.append(dict(name=name,p=p,f=f,n=n,uv=uv,mat=mat,parent=self.parent))
    def grid(self,name,p,mat,uv=None,flip=False):
        p=np.asarray(p);r,c,_=p.shape;f=[]
        for i in range(r-1):
            for j in range(c-1):
                a=i*c+j;b=a+1;cc=a+c;d=cc+1
                f.extend([(a,b,cc),(b,d,cc)] if flip else [(a,cc,b),(b,cc,d)])
        self.mesh(name,p.reshape(-1,3),f,mat,None if uv is None else np.asarray(uv).reshape(-1,2))
M=Model();root=M.node('baja427',extras={'units':'metres','forward':'+Z','up':'+Y','groundOffset':.07});body=M.node('body',root);M.parent=body
paint=M.mat('ivory_enamel',0xdecdb2,.38,.12)
sidepaint=M.mat('ivory_side_livery_and_dust',0xffffff,.53,.08)
steel=M.mat('tube_coating',0x303734,.65,.12)
rubber=M.mat('tyre_rubber',0x242522,.94)
bronze=M.mat('bronze_rim',0x8a704c,.46,.72)
alloy=M.mat('skid_aluminium',0x9c9f96,.48,.85)
black=M.mat('recess_black',0x0e1414,.88)
flare=M.mat('flare_charcoal',0x353a36,.86)
glass=M.mat('smoked_glazing',0x263b43,.13,.22,alpha=.88)
red=M.mat('vermilion_shackle',0xbd3e2c,.44,.25)
orange=M.mat('orange_webbing',0xef8128,.84)
olive=M.mat('olive_toolcase',0x626149,.81,.05)
chrome=M.mat('machined_hardware',0xb8bdb8,.32,.88)
spring=M.mat('red_coil',0xbe3f27,.4,.45)
head=M.mat('headlamp_emission',0xffead0,.24,.05,0xffdc9a)
amber=M.mat('amber_emission',0xf4a12b,.24,.05,0xf28a15)
tail=M.mat('taillamp_emission',0xb52d22,.23,.05,0xff2210)
lampglass=M.mat('rally_lens',0xe5dab7,.25,.2,0xffd37e)
roundel=M.mat('427_roundel',0xffffff,.66)
M.materials[roundel].update(alphaMode='MASK',alphaCutoff=.4,doubleSided=True)
for p in (paint,sidepaint):M.materials[p]['extensions']={'KHR_materials_clearcoat':{'clearcoatFactor':.45,'clearcoatRoughnessFactor':.28}}

def basis(axis):
    # Copy: normalising a caller-owned segment vector would silently change
    # the length used by subsequent geometry (notably the spare tie-downs).
    y=np.array(axis,dtype=float,copy=True);y/=np.linalg.norm(y);x=np.cross(y,[0,0,1] if abs(y[2])<.9 else [0,1,0]);x/=np.linalg.norm(x);return np.c_[x,y,np.cross(x,y)]
def box(name,c,size,mat,bevel=.015,B=None):
    c=np.array(c);half=np.array(size)/2;bev=min(bevel,min(half)*.6);B=np.eye(3) if B is None else np.asarray(B);p=[];n=[];f=[];uv=[]
    for axis in range(3):
        for sign in (-1,1):
            o=[a for a in range(3) if a!=axis];start=len(p);steps=3 if bev else 1
            for i in range(steps+1):
                for j in range(steps+1):
                    q=np.zeros(3);q[axis]=sign*half[axis];q[o[0]]=(2*i/steps-1)*half[o[0]];q[o[1]]=(2*j/steps-1)*half[o[1]]
                    core=np.clip(q,-half+bev,half-bev);d=q-core;nn=d/max(np.linalg.norm(d),1e-10) if bev else np.eye(3)[axis]*sign
                    v=c+B@(core+nn*bev if bev else q);p.append(v);n.append(B@nn)
                    proj=int(np.argmax(abs(B[:,axis])))
                    uv.append(((v[0]+1.3)/2.6,(2.7-v[2])/5.4) if proj==1 else ((v[0]+1.3)/2.6,1-v[1]/2) if proj==2 else ((2.45-v[2])/4.9,1-v[1]/2))
            for i in range(steps):
                for j in range(steps):
                    a=start+i*(steps+1)+j;b=a+1;cc=a+steps+1;d=cc+1;tris=[(a,cc,b),(b,cc,d)]
                    if np.dot(np.cross(np.array(p[cc])-p[a],np.array(p[b])-p[a]),B[:,axis])*sign<0:tris=[t[::-1] for t in tris]
                    f.extend(tris)
    M.mesh(name,p,f,mat,uv,n)
def cylinder(name,a,b,r,mat,n=12,r2=None,caps=True):
    a=np.asarray(a,float);b=np.asarray(b,float);B=basis(b-a);p=[];f=[];norm=[]
    for c,rad in ((a,r),(b,r if r2 is None else r2)):
        for j in range(n+1):
            q=B[:,0]*math.cos(TAU*j/n)+B[:,2]*math.sin(TAU*j/n);p.append(c+q*rad);norm.append(q)
    for j in range(n):f.extend([(j,j+n+1,j+1),(j+1,j+n+1,j+n+2)])
    if caps:
        for c,off,sgn in ((a,0,-1),(b,n+1,1)):
            k=len(p);p.extend([c]+p[off:off+n+1]);norm.extend([B[:,1]*sgn]*(n+2))
            for j in range(n):f.append((k,k+j+1,k+j+2) if sgn<0 else (k,k+j+2,k+j+1))
    M.mesh(name,p,f,mat,normals=norm)
def tube(name,points,r,mat,n=10):
    for i in range(len(points)-1):cylinder(name+str(i),points[i],points[i+1],r,mat,n,caps=False)
def torus(name,c,major,minor,mat,axis=(1,0,0),segments=48,sides=8,stretch=1):
    c=np.asarray(c);B=basis(axis);p=[];n=[];f=[]
    for i in range(segments+1):
        a=TAU*i/segments;rad=B[:,0]*math.cos(a)+B[:,2]*math.sin(a)
        for j in range(sides+1):
            t=TAU*j/sides;q=rad*math.cos(t)+B[:,1]*math.sin(t);p.append(c+rad*(major+minor*math.cos(t))+B[:,1]*minor*math.sin(t)*stretch);n.append(rad*math.cos(t)+B[:,1]*math.sin(t)/stretch)
    for i in range(segments):
        for j in range(sides):
            a=i*(sides+1)+j;b=a+1;cc=a+sides+1;d=cc+1;f.extend([(a,b,cc),(b,d,cc)])
    M.mesh(name,p,f,mat,normals=n)
def quad(name,p,mat,uv=None):M.mesh(name,p,[(0,1,2),(0,2,3)],mat,uv)

def outline_panel(name,outline,z,depth,mat):
    """Convex stamped front panel with a real edge return, in XY."""
    p=[];f=[];N=len(outline)
    for dz in (-depth/2,depth/2):p.extend([(x,y,z+dz) for x,y in outline])
    p.extend([(np.mean([v[0] for v in outline]),np.mean([v[1] for v in outline]),z-depth/2),
              (np.mean([v[0] for v in outline]),np.mean([v[1] for v in outline]),z+depth/2)])
    for j in range(N):
        k=(j+1)%N;f.extend([(2*N,j,k),(2*N+1,N+k,N+j),(j,N+j,N+k),(j,N+k,k)])
    # Supply consistent outward face winding and flat-to-soft weighted normals.
    p=np.asarray(p);f=np.asarray(f)
    center=p.mean(0);fn=np.cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]])
    flip=(fn*(p[f].mean(1)-center)).sum(1)<0;f[flip]=f[flip,::-1]
    M.mesh(name,p,f,mat)

def bonnet_y(u,z):
    t=(z-1.04)/1.35
    crown=.095*math.exp(-(abs(u)/.61)**6)*math.sin(math.pi*(.12+.78*t))
    return 1.178+.065*(1-t)+.045*(1-u*u)+crown
def rotX(a):return np.array([[1,0,0],[0,math.cos(a),-math.sin(a)],[0,math.sin(a),math.cos(a)]])
def rotY(a):return np.array([[math.cos(a),0,math.sin(a)],[0,1,0],[-math.sin(a),0,math.cos(a)]])
def rotZ(a):return np.array([[math.cos(a),-math.sin(a),0],[math.sin(a),math.cos(a),0],[0,0,1]])

def plate_hole(name,c,halfsize,depth,hole,mat,B=None):
    """Closed steel plate with an actual through bore; local normal +Z."""
    c=np.asarray(c);B=np.eye(3) if B is None else B;hx,hy=halfsize;corner=math.atan2(hy,hx)
    angles=sorted(set([round(a,10) for a in np.linspace(0,TAU,25)[:-1]]+[corner,math.pi-corner,math.pi+corner,TAU-corner]))
    p=[];f=[];norm=[];N=len(angles)
    for zz,sgn in ((depth/2,1),(-depth/2,-1)):
        start=len(p)
        for a in angles:
            co,si=math.cos(a),math.sin(a);outer=1/max(abs(co)/hx,abs(si)/hy)
            for r in (hole,outer):p.append(c+B@np.array([co*r,si*r,zz]));norm.append(B@np.array([0,0,sgn]))
        for i in range(N):
            a=start+2*i;b=a+1;cc=start+2*((i+1)%N);d=cc+1;tris=[(a,b,cc),(b,d,cc)];f.extend(tris if sgn>0 else [t[::-1] for t in tris])
    for inside in (True,False):
        for i,a in enumerate(angles):
            an=angles[(i+1)%N];start=len(p)
            for angle,zz in ((a,depth/2),(a,-depth/2),(an,-depth/2),(an,depth/2)):
                co,si=math.cos(angle),math.sin(angle);r=hole if inside else 1/max(abs(co)/hx,abs(si)/hy)
                p.append(c+B@np.array([co*r,si*r,zz]));nn=np.array([-co,-si,0]) if inside else np.array([co,si,0]);norm.append(B@nn)
            tri=[(start,start+2,start+1),(start,start+3,start+2)];f.extend(tri if inside else [t[::-1] for t in tri])
    M.mesh(name,p,f,mat,normals=norm)

def brake_disc(name,parent,center,side):
    """Rotating annular disc; the caliper belongs to the stationary knuckle."""
    n=M.node(name,parent,center);M.parent=n;B=rotY(math.pi/2)
    for z,front in ((-.009,False),(.009,True)):
        p=[[B@np.array([r*math.cos(a),r*math.sin(a),z]) for r in (.055,.195)] for a in np.linspace(0,TAU,41)]
        M.grid('rotor.annulus',p,alloy,flip=front)
    for radius,inside in ((.055,True),(.195,False)):
        p=[[B@np.array([radius*math.cos(a),radius*math.sin(a),z]) for z in (-.009,.009)] for a in np.linspace(0,TAU,41)]
        M.grid('rotor.edge',p,alloy,flip=inside)
    # Hat/flange meets the bearing/axle concentric with the wheel hub.
    cylinder('rotor.hat',[-.018,0,0],[.018,0,0],.079,alloy,32)
    return n

def brake_caliper(name,center,side):
    x,y,z=center
    for dx in (-.024,.024):box(name+'.pad_housing',(x+dx,y+.14,z-.08),(.018,.11,.10),red,.008)
    box(name+'.outer_bridge',(x,y+.212,z-.08),(.067,.025,.10),red,.008)
def coil(name,a,b,r,wire,mat,turns=8):
    a=np.array(a);b=np.array(b);B=basis(b-a);v=[]
    for t in np.linspace(0,1,turns*16+1):v.append(a+(b-a)*t+B[:,0]*math.cos(t*TAU*turns)*r+B[:,2]*math.sin(t*TAU*turns)*r)
    tube(name,v,wire,mat,6)

def make_textures():
    rng=np.random.default_rng(427)
    w,h=1024,512;arr=np.zeros((h,w,3),np.float32);arr[:]=[222,205,178]
    arr+=rng.normal(0,1.2,(h,w,1));im=Image.fromarray(np.uint8(np.clip(arr,0,255)));d=ImageDraw.Draw(im)
    def px(z,y):return ((2.45-z)/4.9*w,(1-y/2)*h)
    zz=np.linspace(2.45,-2.45,240)
    # Swoosh rises over the rear wheel and then runs along the cargo bed.
    yc=.49+.48/(1+np.exp((zz+.66)*8))
    for offset,width,color in ((.12,.11,(230,159,34)),(.025,.095,(230,113,32)),(-.065,.085,(180,58,40))):
        poly=[px(z,y+offset+width/2) for z,y in zip(zz,yc)]+[px(z,y+offset-width/2) for z,y in zip(zz[::-1],yc[::-1])];d.polygon(poly,fill=color)
    overlay=Image.new('RGBA',im.size);dust=ImageDraw.Draw(overlay)
    for _ in range(14500):
        x=int(rng.integers(w));y=int(rng.integers(h));v=y/h;chance=np.clip((v-.35)*1.5,.04,.9)
        if rng.random()>chance:continue
        r=float(rng.uniform(.3,1.6));dust.ellipse((x-r,y-r,x+r,y+r),fill=(98,69,39,int(rng.integers(15,95))))
    im=Image.alpha_composite(im.convert('RGBA'),overlay).convert('RGB');buf=io.BytesIO();im.save(buf,format='PNG');M.images.append(('ivory_stripes_dust',buf.getvalue()))
    im.save(OUT.with_name('baja-427-livery.png'))
    im=Image.new('RGBA',(512,512));d=ImageDraw.Draw(im);d.ellipse((5,5,507,507),fill=(229,215,187,255),outline=(45,44,36,255),width=4)
    font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',257);bb=d.textbbox((0,0),'427',font=font);d.text(((512-bb[2])/2,223-(bb[3]-bb[1])/2-bb[1]),'427',font=font,fill=(20,24,22,255))
    buf=io.BytesIO();im.save(buf,format='PNG');M.images.append(('427_roundel',buf.getvalue()));im.save(OUT.with_name('baja-427-roundel.png'))
    M.materials[sidepaint]['pbrMetallicRoughness']['baseColorTexture']={'index':0}
    M.materials[roundel]['pbrMetallicRoughness']['baseColorTexture']={'index':1}
    # Original packed PBR maps: linear roughness in G, metalness in B.
    # Low amplitude normal relief sells dried deposits without moving panels.
    from scipy.ndimage import gaussian_filter
    noise=gaussian_filter(rng.random((512,1024)).astype(np.float32),1.0)
    yy=np.linspace(0,1,512)[:,None];grime=np.clip((yy-.42)*1.1,0,.58)
    rough=np.clip(.88+grime*.2+(noise-.5)*.14,.82,1)
    packed=np.zeros((512,1024,3),np.uint8);packed[:,:,0]=255;packed[:,:,1]=rough*255;packed[:,:,2]=255
    norm=np.zeros_like(packed);dy,dx=np.gradient(noise)
    norm[:,:,0]=np.clip(127.5-dx*34,0,255);norm[:,:,1]=np.clip(127.5-dy*34,0,255);norm[:,:,2]=255
    for name,arr in (('surface_roughness',packed),('surface_normal',norm)):
        im=Image.fromarray(arr);buf=io.BytesIO();im.save(buf,format='PNG');M.images.append((name,buf.getvalue()));im.save(OUT.with_name('baja-427-'+name+'.png'))
    for mi in (paint,sidepaint,flare,rubber,steel,bronze,alloy):
        M.materials[mi]['pbrMetallicRoughness']['metallicRoughnessTexture']={'index':2}
        M.materials[mi]['normalTexture']={'index':3,'scale':.32 if mi in (paint,sidepaint) else .7}
    # Ivory panels share the same authored dirt vocabulary as the livery.
    im=Image.new('RGB',(1024,512),(222,205,178));layer=Image.new('RGBA',im.size);d=ImageDraw.Draw(layer)
    for _ in range(13000):
        x=int(rng.integers(1024));y=int(rng.integers(512));r=float(rng.uniform(.25,1.55))
        d.ellipse((x-r,y-r,x+r,y+r),fill=(93,66,39,int(rng.integers(9,80))))
    im=Image.alpha_composite(im.convert('RGBA'),layer).convert('RGB');buf=io.BytesIO();im.save(buf,format='PNG');M.images.append(('ivory_panel_dust',buf.getvalue()));im.save(OUT.with_name('baja-427-panel-dust.png'))
    M.materials[paint]['pbrMetallicRoughness'].update(baseColorFactor=[1,1,1,1],baseColorTexture={'index':4})

def side_width(y,z):
    # Tucked rocker and broad upper fender shoulder.
    shoulder=np.interp(y,[.40,.58,.75,.96,1.07,1.18],[1.025,1.075,1.135,1.173,1.16,1.10])
    return shoulder*(1-.075*max(0,(abs(z)-1.9)/.55))
def arch_lower(z):
    y=.43
    for wz in (-1.59,1.59):
        dz=abs(z-wz)
        if dz<.61:y=max(y,.40+math.sqrt(.61**2-dz**2))
    return y
def build_body():
    # Continuous body sides have real open wheel arches, not dark circles.
    for side in (-1,1):
        zvals=np.linspace(-2.41,2.39,257);p=[]
        for z in zvals:
            lo=arch_lower(z);p.append([[side*side_width(y,z),y,z] for y in np.linspace(lo,1.16,9)])
        M.grid('body.side_open_arches',p,sidepaint,flip=side>0)
        # Wheel flares follow the same real opening, with solid inner returns.
        for wz in (-1.59,1.59):
            p=[]
            for a in np.linspace(-.15,math.pi+.15,61):
                rr=[.613,.635,.697,.710];xx=[1.126,1.217,1.206,1.15]
                p.append([[side*x,.40+r*math.sin(a),wz+r*math.cos(a)] for x,r in zip(xx,rr)])
            M.grid('body.fender_flare',p,flare,flip=side<0)
            for a in np.linspace(.08,math.pi-.08,10):
                yy=.4+.685*math.sin(a);zz=wz+.685*math.cos(a);cylinder('flare.bolt',[side*1.21,yy,zz],[side*1.222,yy,zz],.012,chrome,6)
        # Real panel seams and side steps.
        seamx=side*1.181
        for z in (-.43,.38,1.04):
            top=1.16 if z!=.38 else 1.31;tube('door.shutline',[(seamx,.53,z),(seamx,top,z)],.005,black,6)
        box('door.handle_recess',(side*1.17,1.13,.67),(.022,.055,.21),black,.01)
        box('door.handle',(side*1.187,1.13,.67),(.025,.035,.17),paint,.01)
        tube('rockslider',[(side*1.19,.40,-.64),(side*1.24,.40,-.35),(side*1.24,.40,.75),(side*1.17,.4,1.02)],.038,steel,10)
        for z in (-.35,.5):cylinder('rockslider.mount',[side*.66,.4,z],[side*1.22,.4,z],.026,steel,8)
        # Side roundel plane is deliberately separate so both digits read normally.
        x=side*1.187;z=.31;y=.895;r=.285
        points=[(x,y-r,z+side*r),(x,y-r,z-side*r),(x,y+r,z-side*r),(x,y+r,z+side*r)]
        quad('livery.427',points,roundel,[(0,1),(1,1),(1,0),(0,0)])
        # Hood-side cooling vent, with slot ribs.
        box('hood.side_vent',(side*1.12,1.14,1.2),(.025,.12,.20),black,.015)
        for dz in (-.06,0,.06):box('hood.vent_rib',(side*1.135,1.14,1.2+dz),(.012,.085,.009),steel,.002)
    # Shaped hood: subtle center bulge, rolled shoulders and a separate scoop.
    p=[]
    for z in np.linspace(1.04,2.39,32):
        row=[]
        for u in np.linspace(-1,1,35):
            x=u*(1.085-.05*(z-1.04)/1.35);row.append((x,bonnet_y(u,z),z))
        p.append(row)
    M.grid('body.sculpted_bonnet',p,paint)
    # Painted fender shoulders bridge the upper side skin to the bonnet's
    # rolled outer edges. Keep a 4mm removable-panel seam, not an open air slot.
    for side in (-1,1):
        p=[]
        for z in np.linspace(1.04,2.39,32):
            hx=1.085-.05*(z-1.04)/1.35;hy=bonnet_y(1,z)
            outer=np.array([side*side_width(1.16,z),1.16,z]);inner=np.array([side*(hx+.004),hy-.002,z])
            p.append([outer*(1-t)+inner*t for t in np.linspace(0,1,5)])
        M.grid('body.bonnet_fender_shoulder',p,paint,flip=side>0)
    p=[]
    for u in np.linspace(-1,1,35):
        hood_y=bonnet_y(u,2.39)
        p.append([(u*1.035,1.145,2.437),(u*1.035,hood_y-.002,2.393)])
    M.grid('body.front_bonnet_brow',p,paint)
    # Recessed hood vent follows the sculpted centre, rather than a raised slab.
    for z in np.linspace(1.43,1.83,12):
        y=bonnet_y(0,z)+.003
        box('hood.recessed_louver',(0,y,z),(.53,.011,.026),black,.004)
    for side in (-1,1):
        p=[]
        for z in np.linspace(1.14,2.28,24):
            u=side*.67;x=u*(1.085-.05*(z-1.04)/1.35)
            p.append((x,bonnet_y(u,z)+.001,z))
        tube('hood.pressed_character_line',p,.005,paint,6)
    # Cabin pillars, roof and opaque interior keep the large glass bounded.
    roofp=[]
    for z in np.linspace(-.43,.48,12):
        roofp.append([(u*(.965+.018*math.sin((z+.43)/.91*math.pi)),1.84+.045*(1-u*u),z) for u in np.linspace(-1,1,25)])
    M.grid('body.crown_roof',roofp,paint)
    # Crowned painted windscreen header closes the upper glass-to-roof edge.
    # Its top samples exactly match the leading roof row at Z=.48.
    header=[]
    for u in np.linspace(-1,1,25):
        top_y=1.84+.045*(1-u*u)
        header.append([((.927+t*.038)*u,1.805+t*(top_y-1.805),.468+t*.012) for t in np.linspace(0,1,5)])
    M.grid('cab.upper_windscreen_header',header,paint)
    # Four rails surround a genuine rear-window opening. A solid painted wall
    # behind blended glass would make the pane read as a metal rectangle.
    box('cab.rear_wall_lower',(0,1.15,-.45),(2.02,.29,.08),paint,.025)
    box('cab.rear_wall_upper',(0,1.803,-.45),(2.02,.074,.08),paint,.018)
    for side in (-1,1):box('cab.rear_wall_side',(side*.94,1.53,-.45),(.14,.48,.08),paint,.018)
    box('cab.interior_floor',(0,.76,.25),(1.94,.12,1.3),black,.02)
    for side in (-1,1):
        # Four-sided side glazing with painted A, B and C pillars.
        def cabpoint(y,z,offset=0):
            return (side*(1.086-.127*(y-1.22)/.60+offset),y,z)
        outer=[(1.20,1.075),(1.838,.48),(1.838,-.43),(1.20,-.43)]
        inner=[(1.275,.965),(1.775,.422),(1.775,-.338),(1.275,-.345)]
        for k in range(4):
            j=(k+1)%4
            points=[cabpoint(*outer[k]),cabpoint(*outer[j]),cabpoint(*inner[j]),cabpoint(*inner[k])]
            quad('cab.stamped_window_frame',points if side<0 else points[::-1],paint)
        # Split side glass sits behind thick painted perimeter and black B trim.
        panes=[[(1.282,.95),(1.768,.415),(1.768,-.055),(1.282,-.055)],
               [(1.282,-.145),(1.768,-.145),(1.768,-.33),(1.282,-.337)]]
        for pane in panes:
            points=[cabpoint(y,z,-.008) for y,z in pane]
            quad('cab.side_window',points if side<0 else points[::-1],glass)
            tube('cab.window_seal',points+[points[0]],.012,black,8)
        points=[cabpoint(1.27,-.055),cabpoint(1.78,-.055),cabpoint(1.78,-.145),cabpoint(1.27,-.145)]
        quad('cab.B_pillar',points if side<0 else points[::-1],black)
        tube('cab.A_pillar',[(side*1.09,1.20,1.08),(side*.967,1.83,.46)],.031,paint,12)
        tube('cab.C_pillar',[(side*1.09,1.18,-.43),(side*.973,1.84,-.42)],.035,paint,12)
        tube('cab.roof_side_return',[(side*.973,1.838,-.43),(side*.976,1.845,.10),(side*.967,1.838,.48)],.024,paint,12)
        tube('cab.lower_window_rail',[(side*1.086,1.20,1.04),(side*1.086,1.20,-.42)],.026,paint,12)
        # Mirror stem, fairing and actual reflective inset.
        tube('mirror.arm',[(side*1.08,1.26,.94),(side*1.29,1.27,.91)],.024,steel)
        box('mirror.housing',(side*1.31,1.29,.88),(.20,.16,.24),steel,.07)
        box('mirror.glass',(side*1.313,1.29,.752),(.157,.117,.008),chrome,.012)
    windshield=[(-1.035,1.235,1.053),(1.035,1.235,1.053),(.927,1.805,.468),(-.927,1.805,.468)]
    quad('cab.windscreen',windshield,glass);tube('cab.windscreen_seal',windshield+[windshield[0]],.019,black)
    for side in (-1,1):tube('cab.wiper',[(side*.8,1.24,1.065),(side*.25,1.30,1.005)],.009,black,6)
    rear_glass=[(-.86,1.30,-.498),(-.86,1.765,-.498),(.86,1.765,-.498),(.86,1.30,-.498)]
    quad('cab.rear_glass',rear_glass,glass);tube('cab.rear_glass_seal',rear_glass+[rear_glass[0]],.015,black,8)
    for x in (-.47,.47):
        box('interior.seat_base',(x,.98,.15),(.52,.18,.52),flare,.06)
        box('interior.seat_back',(x,1.23,-.08),(.52,.57,.17),flare,.055,B=rotX(-.10))
        box('interior.headrest',(x,1.57,-.13),(.30,.17,.12),black,.035)
    box('interior.dashboard',(0,1.20,.84),(1.93,.24,.31),black,.045)
    torus('interior.steering_wheel',(-.47,1.26,.57),.17,.018,steel,axis=(0,.2,1),segments=24,sides=6)
    # Open cargo bed: walls have depth, floor ribs, wheel tubs and stake pockets.
    box('bed.floor',(0,.64,-1.43),(2.00,.09,1.85),flare,.012)
    for x in np.linspace(-.93,.93,17):box('bed.floor_rib',(x,.696,-1.43),(.026,.025,1.77),steel,.005)
    for side in (-1,1):
        box('bed.inner_wall',(side*1.05,.92,-1.43),(.10,.44,1.83),flare,.012)
        box('bed.rail_cap',(side*1.103,1.172,-1.43),(.145,.055,1.88),steel,.018)
        for z in (-.62,-2.18):box('bed.stake_pocket',(side*1.105,1.202,z),(.065,.012,.10),black,.005)
        # Inner tubs lie inward of the exterior tyre's sweep.
        # Hollow wheel house: the tyre volume is empty, with a real inner wall.
        aa=np.linspace(math.asin((.695-.40)/.635),math.pi-math.asin((.695-.40)/.635),35)
        for radius,inner in ((.635,True),(.655,False)):
            p=[[(side*x,.4+radius*math.sin(a),-1.59+radius*math.cos(a)) for x in np.linspace(.755,1.10,5)] for a in aa]
            M.grid('bed.wheel_well_shell',p,flare,flip=(side>0)!=inner)
        p=[]
        for a in aa:
            z=-1.59+.655*math.cos(a);p.append([(side*.755,.695,z),(side*.755,.4+.655*math.sin(a),z)])
        M.grid('bed.wheel_well_inner_wall',p,flare,flip=side<0)
        for a in (aa[0],aa[-1]):
            p=[[(side*x,.4+r*math.sin(a),-1.59+r*math.cos(a)) for r in (.635,.655)] for x in np.linspace(.755,1.10,5)]
            M.grid('bed.wheel_well_return',p,flare,flip=(side>0)==(a==aa[0]))
    box('bed.front_bulkhead',(0,.94,-.53),(2.0,.44,.06),flare,.012)
    # Tailgate pivots about X at its actual lower hinge.
    gate=M.node('tailgate.hinge',body,[0,.71,-2.407],extras={'axis':'+X','openAngleRadians':-1.45});M.parent=gate
    box('tailgate.outer',(0,.22,0),(2.16,.44,.065),paint,.025)
    box('tailgate.top_cap',(0,.459,0),(2.18,.04,.085),steel,.015)
    for x in np.linspace(-.91,.91,9):box('tailgate.inner_rib',(x,.22,.042),(.036,.34,.023),flare,.008)
    box('tailgate.handle',(0,.37,-.04),(.31,.06,.027),black,.01)
    for x in (-.75,.75):cylinder('tailgate.hinge_barrel',[x-.065,0,0],[x+.065,0,0],.031,chrome,10)
    M.parent=body
    # Ladder frame remains visible below the body.
    for x in (-.58,.58):box('chassis.rail',(x,.35,0),(.13,.17,4.58),steel,.02)
    for z in (-2.1,-1.15,0,1.05,2.05):box('chassis.crossmember',(0,.36,z),(1.22,.105,.10),steel,.012)
    box('chassis.fuel_tank',(0,.37,-.7),(.82,.22,.62),alloy,.035)
    cylinder('exhaust.pipe',[.71,.29,-2.26],[.71,.29,.31],.042,chrome,12)
    cylinder('exhaust.tip',[.71,.29,-2.46],[.71,.29,-2.22],.052,black,16)

def front_hardware():
    # Tapered grille, black fin rows, robust tubular bumper and perforated skid.
    outline=[(-.97,.702),(-1.055,.78),(-1.055,1.12),(-.98,1.183),(-.65,1.183),(-.55,1.215),(.55,1.215),(.65,1.183),(.98,1.183),(1.055,1.12),(1.055,.78),(.97,.702)]
    outline_panel('front.stamped_fascia',outline,2.395,.085,paint)
    grille=[(-.57,.75),(-.715,.82),(-.715,1.085),(-.58,1.175),(.58,1.175),(.715,1.085),(.715,.82),(.57,.75)]
    outline_panel('front.grille_cavity',grille,2.446,.025,black)
    # Tapered grille with a thick bevel surround and deeper regular honeycomb.
    tube('front.grille_surround',[(x,y,2.476) for x,y in grille+[grille[0]]],.021,steel,10)
    for iy,y in enumerate(np.arange(.793,1.14,.045)):
        for x in np.arange(-.66,.67,.05196):
            x+=.02598*(iy%2)
            if abs(x)>.64-(.06 if y<.83 or y>1.09 else 0):continue
            a=.030;pts=[(x+a*math.cos(t),y+a*math.sin(t),2.464) for t in np.linspace(math.pi/6,TAU+math.pi/6,7)]
            tube('front.grille_mesh',pts,.003,steel,5)
    for x in (-.22,0,.22):box('front.marker',(x,1.163,2.498),(.075,.027,.025),amber,.008)
    for side in (-1,1):
        x=side*.87
        box('front.headlight_housing',(x,.973,2.451),(.34,.37,.05),black,.045)
        # Rounded C-shaped DRL, with machined projector barrels behind it.
        points=[(side*.735,.803,2.493),(side*.958,.803,2.493),(side*.993,.833,2.493),(side*.993,1.10,2.493),(side*.962,1.132,2.493),(side*.735,1.132,2.493)]
        tube('front.C_headlight',points,.017,head,12)
        for y in (.88,1.05):
            cylinder('front.projector_barrel',[x,y,2.471],[x,y,2.489],.054,chrome,24)
            cylinder('front.projector_lens',[x,y,2.490],[x,y,2.494],.039,glass,24)
            torus('front.projector_ring',(x,y,2.496),.043,.005,chrome,axis=(0,0,1),segments=24,sides=6)
        box('front.turn_signal',(side*.89,.967,2.499),(.18,.015,.014),amber,.004)
    tube('front.bumper',[(-1.19,.60,2.33),(-1.16,.65,2.54),(-.89,.67,2.60),(.89,.67,2.60),(1.16,.65,2.54),(1.19,.60,2.33)],.043,steel,12)
    tube('front.upper_hoop',[(-.63,.69,2.58),(-.56,.91,2.59),(.56,.91,2.59),(.63,.69,2.58)],.03,steel,10)
    for side in (-1,1):cylinder('front.bumper_chassis',[side*.58,.36,2.08],[side*.58,.65,2.57],.038,steel,10)
    # Solid aluminium sheet with eight real circular bores. Each cell is an
    # annular rectangle; exact corner rays prevent cracks along cell borders.
    center=np.array([0,.485,2.48]);B=rotX(-.32)
    hx,hy=.125,.0675
    corner=math.atan2(hy,hx)
    angles=sorted(set([round(a,10) for a in np.linspace(0,TAU,33)[:-1]]+[corner,math.pi-corner,math.pi+corner,TAU-corner]))
    for cx in (-.375,-.125,.125,.375):
        for cy in (-.0675,.0675):
            p=[];f=[];norm=[]
            for depth,sgn in ((.011,1),(-.011,-1)):
                start=len(p)
                for a in angles:
                    co,si=math.cos(a),math.sin(a);t=1/max(abs(co)/hx,abs(si)/hy)
                    for r in (.031,t):p.append(center+B@np.array([cx+co*r,cy+si*r,depth]));norm.append(B@np.array([0,0,sgn]))
                for i in range(len(angles)):
                    a=start+2*i;b=a+1;c=start+2*((i+1)%len(angles));dd=c+1;tri=[(a,b,c),(b,dd,c)];f.extend(tri if sgn>0 else [t[::-1] for t in tri])
            for i,a in enumerate(angles):
                an=angles[(i+1)%len(angles)];start=len(p)
                for angle,depth in ((a,.011),(a,-.011),(an,-.011),(an,.011)):
                    co,si=math.cos(angle),math.sin(angle);p.append(center+B@np.array([cx+.031*co,cy+.031*si,depth]));norm.append(B@np.array([-co,-si,0]))
                f.extend([(start,start+2,start+1),(start,start+3,start+2)])
            M.mesh('front.perforated_skid_plate',p,f,alloy,normals=norm)
    for y in (-.135,.135):box('front.skid_fold',center+B@np.array([0,y,0]),(1.0,.014,.026),alloy,.004,B=B)
    for side in (-1,1):
        x=side*.70;torus('front.red_shackle',(x,.49,2.585),.061,.015,red,axis=(0,0,1),segments=20,sides=7,stretch=1)
        cylinder('front.shackle_pin',[x-.075,.535,2.585],[x+.075,.535,2.585],.014,chrome,10)
        box('front.recovery_lug_web',(x,.57,2.40),(.026,.14,.30),steel,.004)
        box('front.recovery_gusset',(x,.64,2.56),(.035,.065,.08),steel,.004)
        plate_hole('front.recovery_lug_eye',(x,.535,2.585),(.04,.04),.026,.016,steel,B=rotY(math.pi/2))
    for x in (-.39,.39):
        cylinder('rallylamp.housing',[x,.85,2.52],[x,.85,2.65],.118,steel,32)
        cylinder('rallylamp.lens',[x,.85,2.652],[x,.85,2.658],.102,lampglass,32)
        torus('rallylamp.bezel',(x,.85,2.659),.108,.010,chrome,axis=(0,0,1),segments=32,sides=6)
        for delta in (-.06,-.02,.02,.06):
            span=math.sqrt(.10**2-delta**2)
            cylinder('rallylamp.guard',[x-span,.85+delta,2.672],[x+span,.85+delta,2.672],.0045,steel,6)
            cylinder('rallylamp.guard',[x+delta,.85-span,2.673],[x+delta,.85+span,2.673],.0045,steel,6)
        box('rallylamp.mount',(x,.705,2.56),(.075,.065,.12),steel,.006)
    # Rear receiver bumper and inset C lamps.
    tube('rear.bumper',[(-1.14,.58,-2.38),(-1.14,.54,-2.49),(1.14,.54,-2.49),(1.14,.58,-2.38)],.047,steel,10)
    # Bolted frame extensions carry the bumper and split towing crossmember.
    # The former bumper/receiver had no connection back to the ladder rails.
    for side in (-1,1):
        box('rear.frame_bracket',(side*.58,.42,-2.34),(.11,.24,.52),steel,.01)
        box('rear.receiver_crossmember',(side*.365,.43,-2.32),(.63,.16,.20),steel,.008)
        for z in (-2.17,-2.27):
            cylinder('rear.frame_mount_bolt',[side*.505,.37,z],[side*.655,.37,z],.013,chrome,8)
        # Recovery lug has a real eye and a web welded into the crossmember.
        x=side*.72
        box('rear.recovery_lug_web',(x,.49,-2.38),(.026,.075,.24),steel,.004)
        plate_hole('rear.recovery_lug_eye',(x,.49,-2.54),(.042,.045),.026,.016,steel,B=rotY(math.pi/2))
        path=[(x-.048,.49,-2.54),(x-.060,.435,-2.54),(x-.038,.395,-2.54),(x+.038,.395,-2.54),(x+.060,.435,-2.54),(x+.048,.49,-2.54)]
        tube('rear.recovery_bow',path,.013,red,10)
        cylinder('rear.recovery_pin',[x-.077,.49,-2.54],[x+.077,.49,-2.54],.0125,chrome,12)
    # Hollow receiver with pin bores, collar and recessed interior back wall.
    for side in (-1,1):
        x=side*.0415
        plate_hole('rear.receiver_pin_wall',(x,.43,-2.41),(.052,.052),.021,.013,steel,B=rotY(math.pi/2))
        box('rear.receiver_side_front',(x,.43,-2.531),(.021,.104,.138),steel,.002)
        box('rear.receiver_side_rear',(x,.43,-2.279),(.021,.104,.158),steel,.002)
        box('rear.receiver_horizontal',(0,.43+side*.0415,-2.40),(.104,.021,.40),steel,.002)
        box('rear.receiver_collar_vertical',(side*.049,.43,-2.607),(.036,.134,.025),steel,.002)
        box('rear.receiver_collar_horizontal',(0,.43+side*.049,-2.607),(.134,.036,.025),steel,.002)
    box('rear.receiver_inner_stop',(0,.43,-2.201),(.062,.062,.003),black,0)
    cylinder('rear.receiver_pin',[-.095,.43,-2.41],[.103,.43,-2.41],.0105,chrome,12)
    cylinder('rear.receiver_pin_head',[-.104,.43,-2.41],[-.091,.43,-2.41],.019,chrome,12)
    for side in (-1,1):
        x=side*1.026;box('rear.taillight_housing',(x,.943,-2.423),(.17,.395,.043),black,.02)
        box('rear.taillight_lens',(x,.943,-2.448),(.128,.352,.018),red,.014)
        points=[(x-side*.044,.789,-2.461),(x+side*.045,.789,-2.461),(x+side*.045,1.10,-2.461),(x-side*.044,1.10,-2.461)]
        tube('rear.C_taillight',points,.011,tail,8)

def wheel(name,parent,translation=(0,0,0),rotation=None,steer=True):
    pivot=M.node(name+'.steer',parent,translation,rotation,{'steerAxis':'+Y','spinAxis':'+X','tyreRadius':.47})
    roll=M.node(name+'.roll',pivot);M.parent=roll
    # Wide rounded carcass, sculpted tread, recessed bronze wheel barrels.
    torus(name+'.carcass',(0,0,0),.348,.111,rubber,segments=64,sides=12,stretch=1.56)
    for x in (-.155,.155):
        torus(name+'.sidewall',(x,0,0),.348,.065,rubber,segments=64,sides=8,stretch=.26)
        torus(name+'.bead',(x*1.08,0,0),.244,.011,rubber,segments=48,sides=6)
    # Three staggered actual tread-block bands, batched into one tyre draw.
    for i in range(44):
        for j,x in enumerate((-.135,0,.135)):
            a=TAU*(i+(j%2)*.5)/44;B=rotX(a);c=np.array([x,.455*math.cos(a),.455*math.sin(a)])
            B=B@rotY((-.22 if j==0 else .22 if j==2 else (-1)**i*.12))
            box(name+'.tread',c,(.105,.033,.052),rubber,.005,B=B)
    cylinder(name+'.barrel',[-.155,0,0],[.155,0,0],.244,bronze,48,caps=False)
    for s in (-1,1):
        x=s*.176
        torus(name+'.beadlock',(x,0,0),.238,.017,bronze,axis=(1,0,0),segments=48,sides=7)
        # Spoked ring, with real gaps instead of painted wheel holes.
        torus(name+'.inner_ring',(x-s*.012,0,0),.172,.029,bronze,segments=40,sides=6)
        cylinder(name+'.hub',[x-s*.028,0,0],[x+s*.007,0,0],.078,bronze,24)
        for k in range(10):
            a=TAU*k/10;B=rotX(a);box(name+'.spoke',[x-s*.017,.122*math.cos(a),.122*math.sin(a)],(.03,.105,.039),bronze,.008,B=B)
        for k in range(20):
            a=TAU*k/20;cylinder(name+'.beadlock_bolt',[x,.238*math.cos(a),.238*math.sin(a)],[x+s*.009,.238*math.cos(a),.238*math.sin(a)],.0085,bronze if name.startswith('spare.') else chrome,6)
        for k in range(6):
            a=TAU*k/6;cylinder(name+'.lug',[x,.056*math.cos(a),.056*math.sin(a)],[x+s*.016,.056*math.cos(a),.056*math.sin(a)],.010,bronze if name.startswith('spare.') else chrome,6)
    return pivot,roll

def damper(name,a,b,front=False):
    """Separate fixed shell/rod, sliding seats and a spring with its own node."""
    a=np.array(a,float);b=np.array(b,float);v=b-a;u=v/np.linalg.norm(v);rod_fraction=.60 if front else .68
    root=M.node(name,body,a.tolist(),extras={'end':b.tolist(),'telescopic':True})
    shell=M.node(name+'.body',root);M.parent=shell
    cylinder('damper.fixed_shell',v*.10,v*.63,.038 if front else .034,alloy,16)
    torus('damper.upper_eye',[0,0,0],.024,.011,steel,axis=(0,0,1),segments=16,sides=7)
    shaft=M.node(name+'.shaft',root,v.tolist());M.parent=shaft
    cylinder('damper.fixed_rod',-v*rod_fraction,[0,0,0],.018 if front else .015,chrome,12)
    torus('damper.lower_eye',[0,0,0],.024,.011,steel,axis=(0,0,1),segments=16,sides=7)
    if front:
        n=M.node(name+'.spring',root,(v*.18).tolist());M.parent=n;coil('damper.coil',[0,0,0],v*.70,.069,.009,spring,8)
        for label,t in (('upper_seat',.18),('lower_seat',.88)):
            n=M.node(name+'.'+label,root,(v*t).tolist());M.parent=n;cylinder('damper.spring_seat',-u*.008,u*.008,.088,steel,24)
    M.parent=body
    return {'node':name,'a':a.tolist(),'b':b.tolist(),'bodyLength':float(np.linalg.norm(v)*.53),'rodLength':float(np.linalg.norm(v)*rod_fraction),'spring':front}

def eye(name,c,mat=steel,axis=(1,0,0),outer=.032,inner=.014,depth=.035):
    # An annular plate makes the actual bore visible around its hinge pin.
    B=rotY(math.pi/2) if axis==(1,0,0) else np.eye(3)
    plate_hole(name,c,(outer,outer),depth,inner,mat,B)

def build_running_gear():
    pivots={};mounts=[];dampers=[]
    for side,label in ((-1,'L'),(1,'R')):pivots['F'+label]=wheel('wheel.F'+label,body,[side*1.025,.40,1.59])
    axle=M.node('rear_axle',body,[0,.40,-1.59],extras={'rollAxis':'+Z','wheelCentres':[-1.025,1.025]});M.parent=axle
    cylinder('rear_axle.tube',[-1.025,0,0],[1.025,0,0],.063,steel,20)
    box('rear_axle.diff',(0,-.015,0),(.35,.28,.27),steel,.08)
    cylinder('rear_axle.cover',[0,-.015,-.15],[0,-.015,-.18],.145,steel,12)
    cylinder('rear_axle.pinion',[0,0,.12],[0,0,.31],.064,steel,16)
    for a in np.linspace(0,TAU,10,endpoint=False):cylinder('rear_axle.diff_bolt',[.123*math.cos(a),-.015+.123*math.sin(a),-.181],[.123*math.cos(a),-.015+.123*math.sin(a),-.194],.01,chrome,6)
    for side,label in ((-1,'L'),(1,'R')):
        pivots['R'+label]=wheel('wheel.R'+label,axle,[side*1.025,0,0]);M.parent=axle
        # Link, spring and damper tabs have a continuous path into the axle tube.
        for yy in (-.09,.09):
            for dx in (-.032,.032):
                plate_hole('rear_axle.link_eye',(side*.77+dx,yy,0),(.040,.040),.016,.014,steel,B=rotY(math.pi/2))
                box('rear_axle.link_tab',(side*.77+dx,(.057 if yy>0 else -.057)/2,0),(.016,.077,.075),steel,.004)
            cylinder('rear_axle.link_pin',[side*.70,yy,0],[side*.84,yy,0],.013,chrome,12)
        box('rear_axle.spring_perch',(side*.76,.032,0),(.20,.045,.19),steel,.008)
        box('rear_axle.damper_bracket_web',(side*.76,.005,-.075),(.10,.09,.12),steel,.006)
        for dx in (-.045,.045):box('rear_axle.damper_fork_stay',(side*.76+dx,.005,-.14),(.014,.09,.14),steel,.004)
        for z in (-.202,-.138):plate_hole('rear_axle.damper_fork',(side*.76,.01,z),(.040,.040),.016,.013,steel)
        cylinder('rear_axle.damper_pin',[side*.76,.01,-.22],[side*.76,.01,-.12],.012,chrome,12)
        # Non-rotating rear discs/calipers stay with the housing, not wheel roll.
        brake_disc('brake.R'+label+'.rotor',axle,[side*.90,0,0],side);M.parent=axle
        brake_caliper('rear_axle.caliper',(side*.90,0,0),side)
        cylinder('rear_axle.caliper_carrier',[side*.86,.03,-.03],[side*.876,.14,-.08],.012,steel,12)
    box('rear_axle.panhard_tab',(.76,.015,.12),(.07,.10,.25),steel,.006)
    cylinder('rear_axle.panhard_pin',[.76,.03,.18],[.76,.03,.28],.013,chrome,12)
    M.parent=body
    # Engine/transfer case and drive shafts now meet the actual pinion nose.
    box('chassis.engine',(0,.58,.91),(.58,.42,.67),steel,.05)
    box('chassis.transfer_case',(0,.40,.44),(.34,.25,.38),alloy,.035)
    cylinder('chassis.front_prop',[0,.40,.54],[0,.37,1.43],.036,steel,16)
    box('chassis.front_differential',(0,.37,1.59),(.34,.24,.32),steel,.05)
    for x in (-.58,.58):box('chassis.engine_mount',(x*.75,.43,.91),(.24,.12,.18),steel,.012)
    a=np.array([0,.4,.54]);b=np.array([0,.4,-1.28]);v=b-a
    n=M.node('driveline.shaft',body,a.tolist(),extras={'end':b.tolist()});M.parent=n
    cylinder('driveline.prop_tube',[0,0,0],v*.72,.042,steel,16)
    tail=M.node('driveline.slip',n,v.tolist());M.parent=tail;cylinder('driveline.slip_tube',-v*.40,[0,0,0],.032,chrome,12)
    for parent in (n,tail):
        M.parent=parent;torus('driveline.universal_joint',[0,0,0],.042,.012,steel,axis=(1,0,0),segments=16,sides=7)
    M.parent=body
    links=[]
    for side,label in ((-1,'L'),(1,'R')):
        for high in (False,True):
            inner=np.array([side*(.70 if high else .68),.40 if high else .27,1.59]);outer=np.array([side*.97,.46 if high else .31,1.59])
            name='front.'+label+('.upper_arm' if high else '.lower_arm');n=M.node(name,body,inner.tolist(),extras={'rotationAxis':'+Z','end':outer.tolist(),'rigid':True});M.parent=n
            span=.30 if high else .22
            for dz in (-span,span):cylinder(name,[0,0,dz],outer-inner,.024,steel,12)
            cylinder(name+'.inner_pin',[0,0,-span-.04],[0,0,span+.04],.013,chrome,12)
            for dz in (-span,span):eye(name+'.bushing',[0,0,dz],axis=(0,0,1),outer=.030)
            cylinder(name+'.ball_joint',outer-inner+[0,-.018,0],outer-inner+[0,.018,0],.027,chrome,16)
            if not high:
                foot=(outer-inner)*.81
                for z in (-.035,.035):box('front.shock_lower_tab',foot+[0,.012,z],(.055,.05,.014),steel,.004)
                cylinder('front.shock_lower_pin',foot+[0,0,-.055],foot+[0,0,.055],.012,chrome,12)
            links.append({'node':name,'mount':inner.tolist(),'end':outer.tolist(),'axis':[0,0,1]})
            M.parent=body
            for dz in (-span,span):
                box('chassis.wishbone_mount',(side*.665,.34 if high else .33,1.59+dz),(.09,.08,.16),steel,.006)
                for zz in (-.028,.028):plate_hole('chassis.wishbone_fork',inner+[0,0,dz+zz],(.047,.040),.014,.014,steel)
        # Steering upright is the missing physical connection between arms/hub.
        origin=np.array([side*.97,.31,1.59]);n=M.node('front.'+label+'.upright',body,origin.tolist());M.parent=n
        box('upright.knuckle',(0,.075,0),(.055,.15,.055),steel,.018)
        cylinder('upright.hub_bearing',[side*-.075,.09,0],[side*.075,.09,0],.049,chrome,20)
        upright=n;brake_disc('brake.F'+label+'.rotor',upright,[side*.055,.09,0],side);M.parent=upright
        brake_caliper('upright.caliper',(side*.055,.09,0),side)
        cylinder('upright.caliper_brace',[0,.15,0],[side*.029,.23,-.08],.014,steel,12)
        tube('upright.steering_arm',[(0,.03,0),(side*.018,.03,-.11)],.021,steel,12)
        M.parent=body
        # CV shaft and rack tie rod have ball-jointed end hardware.
        for name,a,b,r in [('front.'+label+'.halfshaft',[side*.17,.37,1.59],[side*.90,.40,1.59],.018),('front.'+label+'.tie_rod',[side*.58,.32,1.34],[side*.988,.34,1.48],.014)]:
            n=M.node(name,body,a,extras={'end':b});M.parent=n;v=np.array(b)-a
            if 'halfshaft' in name:
                cylinder('front.cv_tube',[0,0,0],v*.72,r,steel,12)
                torus('front.inner_cv_boot',[0,0,0],.025,.009,rubber,axis=(1,0,0),segments=12,sides=6)
                slip=M.node(name+'.slip',n,v.tolist());M.parent=slip
                cylinder('front.cv_slip',-v*.45,[0,0,0],r*.78,steel,12)
                torus('front.outer_cv_boot',[0,0,0],.025,.009,rubber,axis=(1,0,0),segments=12,sides=6)
            else:
                cylinder('front.driven_link',[0,0,0],v,r,steel,12)
                for c in (np.zeros(3),v):torus('front.link_boot',c,.025,.009,rubber,axis=(1,0,0),segments=12,sides=6)
                M.parent=body;slide=M.node('front.'+label+'.rack_slide',body,[side*.50,.32,1.34]);M.parent=slide
                cylinder('front.rack_slider',[0,0,0],[side*.08,0,0],.018,chrome,12)
            M.parent=body;mounts.append({'node':name,'a':a,'b':b})
        a=[side*.67,.94,1.59];b=[side*.9149,.3024,1.59];dampers.append(damper('front.'+label+'.coilover',a,b,True))
        # Welded tower legs clear the coil and terminate at an actual top clevis.
        for z in (-.14,.14):
            cylinder('chassis.shock_tower',[side*.58,.40,1.59+z],[side*.67,.94,1.59+z],.025,steel,12)
            cylinder('chassis.shock_tower_cap',[side*.67,.94,1.59+z],[side*.67,.94,1.59+math.copysign(.04,z)],.022,steel,12)
        cylinder('chassis.shock_top_pin',[side*.67,.94,1.51],[side*.67,.94,1.67],.012,chrome,12)
        for z in (-.032,.032):plate_hole('chassis.shock_top_fork',(side*.67,.94,1.59+z),(.038,.040),.018,.013,steel)
        for z in (-.016,.016):plate_hole('chassis.shock_top_washer',(side*.67,.94,1.59+z),(.022,.022),.009,.013,chrome)
        # Rear spring towers and damper towers connect to the frame rails.
        for z,top in ((-1.59,.89),(-1.92,.96)):
            box('chassis.rear_tower',(side*.58,(.35+top)/2,z),(.11,top-.35,.12),steel,.012)
            if z<-1.8:
                for dz in (-.032,.032):cylinder('chassis.rear_tower_cap',[side*.58,top,z+dz],[side*.67,top,z+dz],.016,steel,12)
            else:cylinder('chassis.rear_tower_cap',[side*.58,top,z],[side*.70,top,z],.025,steel,12)
        a=np.array([side*.69,.89,-1.59]);b=np.array([side*.76,.44,-1.59]);v=b-a
        root=M.node('rear.'+label+'.spring',body,a.tolist());co=M.node('rear.'+label+'.spring.coil',root);M.parent=co;coil('rear.coil',[0,0,0],v,.078,.011,spring,7)
        for name,c in (('upper_seat',np.zeros(3)),('lower_seat',v)):
            n=M.node('rear.'+label+'.spring.'+name,root,c.tolist());M.parent=n;u=v/np.linalg.norm(v);cylinder('rear.spring_seat',-u*.009,u*.009,.095,steel,24)
        M.parent=body;mounts.append({'node':'rear.'+label+'.spring','a':a.tolist(),'b':b.tolist()})
        dampers.append(damper('rear.'+label+'.damper',[side*.70,.96,-1.92],[side*.76,.41,-1.76]))
        for z in (-1.952,-1.888):plate_hole('chassis.rear_shock_fork',(side*.70,.96,z),(.038,.040),.018,.013,steel)
        cylinder('chassis.rear_shock_pin',[side*.70,.96,-2.0],[side*.70,.96,-1.84],.012,chrome,12)
        for high in (False,True):
            a=np.array([side*.64,.48 if high else .30,-.72]);b=np.array([side*.77,.49 if high else .31,-1.59]);name='rear.'+label+('.upper_link' if high else '.lower_link')
            n=M.node(name,body,a.tolist(),extras={'end':b.tolist(),'rigid':True});M.parent=n;v=b-a;cylinder('rear.locating_link',[0,0,0],v,.026,steel,12)
            for c in (np.zeros(3),v):
                eye('rear.link_eye',c,outer=.036,inner=.024)
                torus('rear.elastic_bushing',c,.017,.007,rubber,axis=(1,0,0),segments=16,sides=7)
            M.parent=body;box('chassis.rear_link_bracket',(side*.64,.40,-.72),(.11,.27,.13),steel,.008)
            cylinder('chassis.rear_link_pin',a-[.065,0,0],a+[.065,0,0],.013,chrome,12)
            mounts.append({'node':name,'a':a.tolist(),'b':b.tolist(),'rigid':True})
    cylinder('chassis.steering_rack',[-.60,.32,1.34],[.60,.32,1.34],.035,steel,16)
    box('chassis.rear_link_crossmember',(0,.40,-.72),(1.28,.12,.13),steel,.012)
    a=np.array([-.72,.58,-1.36]);b=np.array([.76,.43,-1.36]);name='rear.panhard'
    n=M.node(name,body,a.tolist(),extras={'end':b.tolist(),'rigid':True});M.parent=n;cylinder('rear.panhard',[0,0,0],b-a,.022,steel,12)
    for c in (np.zeros(3),b-a):eye('rear.panhard_eye',c,axis=(0,0,1),outer=.032)
    M.parent=body;cylinder('chassis.panhard_mount',[-.58,.40,-1.36],a,.035,steel,12);mounts.append({'node':name,'a':a.tolist(),'b':b.tolist(),'rigid':True})
    return {'wheelNodes':{k:{'steer':M.nodes[v[0]]['name'],'roll':M.nodes[v[1]]['name']} for k,v in pivots.items()},'rearAxle':{'node':'rear_axle','origin':[0,.40,-1.59],'rotationAxis':[0,0,1]},'frontArms':links,'mounts':mounts,'dampers':dampers,'visualTravel':{'droop':.268,'bump':.52,'rest':.40},'assemblyVersion':3}


def cargo():
    M.parent=body;tiedowns=M.node('cargo.spare_tiedowns',body)
    # Support the bed floor over the rails, rather than floating above them.
    for z in (-2.10,-.78):
        box('chassis.bed_cross_support',(0,.585,z),(2.04,.075,.12),steel,.01)
        for side in (-1,1):box('chassis.bed_standoff',(side*.58,.47,z),(.11,.24,.12),steel,.008)
    for side in (-1,1):
        x=side*.49;a=-.54;R=rotX(a)@rotZ(math.pi/2)
        q=[math.sin(a/2)*math.cos(math.pi/4),-math.sin(a/2)*math.sin(math.pi/4),math.cos(a/2)*math.sin(math.pi/4),math.cos(a/2)*math.cos(math.pi/4)]
        label='spare.L' if side<0 else 'spare.R';pivot,roll=wheel(label,body,[x,1.09,-1.38],q,False)
        points=np.concatenate([p['p'] for p in M.parts if p['parent']==roll and p['mat']==rubber])@R.T+[x,1.09,-1.38]
        # Exact authored tyre samples determine clearance over the new wheel tubs.
        mask=(abs(points[:,0])>.735)&(abs(points[:,2]+1.59)<.585)
        roof=.4+np.sqrt(np.maximum(0,.655**2-(points[mask,2]+1.59)**2))
        raise_y=max(.18,float(np.max(roof+.025-points[mask,1])) if mask.any() else .18)
        # Leave room above the spring towers and their upper seats.
        for tower_z,tower_y in ((-1.59,.92),(-1.92,.99)):
            hit=(abs(points[:,0]-side*.58)<.10)&(abs(points[:,2]-tower_z)<.09)
            if hit.any():raise_y=max(raise_y,float(np.max(tower_y+.02-points[hit,1])))
        if float(points[:,1].max())+raise_y>1.875:raise ValueError('Spare carrier cannot fit below the cab roof: '+str(raise_y))
        M.nodes[pivot]['translation'][1]+=raise_y;points[:,1]+=raise_y;cy=1.09+raise_y
        M.parent=body
        # Two steel rails sit tangent beneath the tyre; inner feet clear wheel wells.
        plane_offset=.220/math.cos(.54)
        def rail_y(z):return cy-plane_offset+math.tan(.54)*(z+1.38)
        for dx in (-.20,.20):
            railx=x+dx
            tube('cargo.carrier_cradle',[(railx,rail_y(-1.93),-1.93),(railx,rail_y(-.83),-.83)],.027,steel,12)
            for z in (-1.93,-.83):
                top=rail_y(z);cylinder('cargo.carrier_leg',[railx,.704,z],[railx,top,z],.024,steel,12)
                box('cargo.carrier_foot',(railx,.7025,z),(.11,.035,.14),steel,.006)
                for dz in (-.04,.04):cylinder('cargo.carrier_bolt',[railx,.69,z+dz],[railx,.729,z+dz],.008,chrome,8)
        for z in (-1.93,-.83):cylinder('cargo.carrier_cross',[x-.20,rail_y(z),z],[x+.20,rail_y(z),z],.027,steel,12)
        # A taut strap follows the actual top tyre silhouette, including anchors.
        near=points[abs(points[:,0]-x)<.045];pairs=[(float(z),float(y)+.006) for y,z in near[:,[1,2]]]
        anchors=[(-2.02,.77),(-.73,.80)];pairs+=anchors;pairs=sorted(set(pairs));hull=[]
        for pt in pairs:
            while len(hull)>1:
                av=np.array(hull[-1])-hull[-2];bv=np.array(pt)-hull[-1]
                if av[0]*bv[1]-av[1]*bv[0]<0:break
                hull.pop()
            hull.append(pt)
        M.parent=tiedowns
        for (z0,y0),(z1,y1) in zip(hull,hull[1:]):
            a=np.array([x,y0,z0]);b=np.array([x,y1,z1]);d=b-a;box('cargo.orange_tiedown',(a+b)/2,(.075,np.linalg.norm(d),.007),orange,.002,B=basis(d))
        for z,y in anchors:
            box('cargo.strap_anchor',(x,y,z),(.11,.05,.10),steel,.006)
            cylinder('cargo.strap_anchor_stay',[x,.71,z],[x,y,z],.017,steel,10)
        M.parent=body
    # Cases/boards occupy the clear centre channel, outside the tyre carrier legs.
    box('cargo.tool_case',(0,.86,-2.23),(.52,.25,.30),olive,.035)
    box('cargo.tool_case_lid',(0,.998,-2.23),(.54,.04,.32),olive,.01)
    for x in (-.20,.20):box('cargo.case_latch',(x,.91,-2.068),(.035,.08,.02),steel,.004)
    tube('cargo.case_handle',[(-.10,1.02,-2.23),(-.10,1.06,-2.23),(.10,1.06,-2.23),(.10,1.02,-2.23)],.013,black,8)
    for y in (.735,.775):
        box('cargo.traction_board',(0,y,-1.40),(.25,.025,.98),orange,.015)
        for z in np.linspace(-1.83,-.97,12):box('cargo.traction_lug',(0,y+.02,z),(.21,.027,.025),orange,.004)


def save(rig):
    OUT.parent.mkdir(parents=True,exist_ok=True)
    document={'asset':{'version':'2.0','generator':'Original Baja427 CPU mesh author'},'extensionsUsed':['KHR_materials_clearcoat'],'scene':0,'scenes':[{'name':'Baja 427 candidate','nodes':[0]}],'nodes':M.nodes,'meshes':[],'materials':M.materials,'bufferViews':[],'accessors':[],'buffers':[{'byteLength':0}],'images':[],'textures':[],'samplers':[{'magFilter':9729,'minFilter':9987,'wrapS':33071,'wrapT':33071}]};binary=bytearray()
    def view(b,target=None):
        binary.extend(b'\0'*(-len(binary)%4));v={'buffer':0,'byteOffset':len(binary),'byteLength':len(b)};binary.extend(b)
        if target:v['target']=target
        document['bufferViews'].append(v);return len(document['bufferViews'])-1
    def accessor(a,t,index=False,bounds=False):
        a=np.asarray(a,dtype=np.uint32 if index else np.float32);v={'bufferView':view(a.tobytes(),34963 if index else 34962),'componentType':5125 if index else 5126,'count':len(a),'type':t}
        if bounds:v.update(min=a.min(0).tolist(),max=a.max(0).tolist())
        document['accessors'].append(v);return len(document['accessors'])-1
    for name,data in M.images:
        document['images'].append({'name':name,'bufferView':view(data),'mimeType':'image/png'});document['textures'].append({'sampler':0,'source':len(document['images'])-1})
    batches={}
    for part in M.parts:
        # Semantic subdivision preserves the useful removable components while
        # batching tread blocks, grille cells, bolts and coil turns by material.
        semantic=part['name'].split('.')[0]
        key=(part['parent'],part['mat'],semantic)
        b=batches.setdefault(key,{'p':[],'f':[],'n':[],'uv':[],'names':[],'count':0})
        b['p'].append(part['p']);b['f'].append(part['f']+b['count']);b['n'].append(part['n']);b['uv'].append(part['uv']);b['names'].append(part['name']);b['count']+=len(part['p'])
    for (parent,mat,semantic),b in batches.items():
        p,f,n,uv=(np.concatenate(b[k]) for k in ('p','f','n','uv'));attrs={'POSITION':accessor(p,'VEC3',bounds=True),'NORMAL':accessor(n,'VEC3'),'TEXCOORD_0':accessor(uv,'VEC2')}
        name=semantic+'.'+M.materials[mat]['name'];document['meshes'].append({'name':name,'primitives':[{'attributes':attrs,'indices':accessor(f.reshape(-1,1),'SCALAR',True),'material':mat}],'extras':{'sourceParts':sorted(set(b['names']))}})
        node={'name':name,'mesh':len(document['meshes'])-1};document['nodes'][parent]['children'].append(len(document['nodes']));document['nodes'].append(node)
    binary.extend(b'\0'*(-len(binary)%4));document['buffers'][0]['byteLength']=len(binary)
    for node in document['nodes']:
        if not node.get('children'):node.pop('children',None)
    js=json.dumps(document,separators=(',',':')).encode();js+=b' '*(-len(js)%4)
    glb=struct.pack('<III',0x46546c67,2,28+len(js)+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary;OUT.write_bytes(glb)
    report={'name':'Baja 427 mechanical refinement v3','units':'metres','up':'+Y','forward':'+Z','groundOffset':.07,'dimensions':{'bodyLength':4.86,'overallLength':5.26,'bodyWidth':2.35,'roofHeightFromGround':1.955,'wheelbase':3.18,'track':2.05,'tyreRadius':.47,'tyreHalfWidth':.187,'wheelHubY':.40},'rig':rig,'tailgate':{'node':'tailgate.hinge','pivot':[0,.71,-2.407],'axis':[1,0,0],'openAngleRadians':-1.45},'lampMaterials':['baja427.headlamp_emission','baja427.amber_emission','baja427.taillamp_emission','baja427.rally_lens'],'wheelLayout':['FL','FR','RL','RR'],'spareNodes':['spare.L.steer','spare.R.steer'],'sourceParts':len(M.parts),'meshDraws':len(document['meshes']),'nodes':len(document['nodes']),'vertices':sum(len(p['p']) for p in M.parts),'triangles':sum(len(p['f']) for p in M.parts),'bytes':len(glb),'sha256':hashlib.sha256(glb).hexdigest(),'sourceSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'embeddedImages':len(M.images),'textureDecodedBytesRGBA':4*1024*512*4+512*512*4,'source':'Original authored geometry and textures; user Baja-427-Master-Reference.jpg is visual guidance only. No source pixels or external mesh copied.','limits':['First game candidate; not photoreal match or manufacturing geometry.','Visual suspension groups have reference endpoints; no full kinematic closure or certified travel/steering clearance.','Spare tyres are complete wheel instances with static strap fit.','Cabin has simple seats/dashboard; no operating interior controls.','Native appearance is validated separately at the bounded 960x600 preview profile.']}
    OUT.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':
    make_textures();build_body();front_hardware();rig=build_running_gear();cargo();save(rig)
