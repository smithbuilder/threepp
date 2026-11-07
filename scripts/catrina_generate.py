"""La Catrina: original, reproducible lowrider mesh and paintwork.

The supplied atlas guides visual matching and documented paint extraction.
Metres, +Y up, +Z front. No external mesh is included. Roof, hood, deck paint
and side-scroll masks derive from the atlas; transformations and hash are recorded.
"""
from pathlib import Path
from contextlib import contextmanager
import copy, hashlib, io, json, math, struct
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import baja427_generate as g

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'showcase/assets/la-catrina.glb'
TAU=math.tau
HUB=.2891
ZAXLE=1.5113

class Model(g.Model):
    def __init__(self):super().__init__();self.origins=[];self.joints={}
    def node(self,name,parent=None,translation=None,rotation=None,extras=None):
        world=np.array([0,0,0] if translation is None else translation,float)
        local=world if parent is None else world-self.origins[parent]
        n=super().node(name,parent,local.tolist(),rotation,extras);self.origins.append(world);return n
    def mesh(self,name,p,f,mat,uv=None,normals=None):
        p=np.asarray(p,float);f=np.asarray(f,np.uint32).reshape(-1,3)
        area=np.cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]])
        keep=np.linalg.norm(area,axis=1)>1e-10;f=f[keep];area=area[keep]
        if not len(f):return
        if normals is not None:
            normals=np.asarray(normals,float);flip=(area*normals[f].mean(1)).sum(1)<0;f[flip]=f[flip,::-1]
        used=np.unique(f)
        if len(used)<len(p):
            remap=np.zeros(len(p),np.uint32);remap[used]=np.arange(len(used));f=remap[f];p=p[used]
            if uv is not None:uv=np.asarray(uv)[used]
            if normals is not None:normals=normals[used]
        if uv is None:
            axis=int(np.argmax(np.abs(area).sum(0)))
            uv=np.c_[(p[:,0]+1.01)/2.02,(2.665-p[:,2])/5.33] if axis==1 else np.c_[(p[:,0]+1.01)/2.02,1-p[:,1]/1.32] if axis==2 else np.c_[(2.665-p[:,2])/5.33,1-p[:,1]/.94]
        super().mesh(name,p-self.origins[self.parent],f,mat,uv,normals)
    def mat(self,name,*args,**kwargs):
        i=super().mat(name,*args,**kwargs);self.materials[i]['name']='catrina.'+name;return i

M=Model();g.M=M
box,cylinder,tube,torus,quad,basis=g.box,g.cylinder,g.tube,g.torus,g.quad,g.basis
root=M.node('VEH_LaCatrina',extras={'units':'metres','up':'+Y','forward':'+Z','groundOffset':0})
body=M.node('body',root);M.parent=body
paint=M.mat('candy_rose',0xd20a58,.20,.55)
rose=M.mat('rose_shadow',0x7c123b,.26,.4)
chrome=M.mat('polished_chrome',0xe7e5db,.16,.97)
silver=M.mat('satin_aluminum',0x9dabae,.28,.8)
black=M.mat('black_recess',0x111118,.85)
rubber=M.mat('rubber',0x1b1a20,.9)
white=M.mat('ivory_whitewall',0xf4ead5,.78)
plum=M.mat('plum_vinyl',0x4f1432,.57)
pipe=M.mat('pink_seat_piping',0xc65680,.42)
gold=M.mat('champagne_gold',0xe4bd74,.27,.65)
steel=M.mat('chassis_graphite',0x29282d,.5,.6)
red=M.mat('coil_candy_red',0xb60d39,.33,.5)
glass=M.mat('clear_tinted_glass',0xb2c7ca,.08,.15,alpha=.18)
lamp=M.mat('headlight_glass',0xf5e6c4,.16,.15,0xb8ab8f)
tail=M.mat('ruby_tail_lens',0xa90827,.20,.20,0x72131b)
amber=M.mat('amber_lens',0xffae31,.24,.10)
for m in (paint,rose):M.materials[m]['extensions']={'KHR_materials_clearcoat':{'clearcoatFactor':1,'clearcoatRoughnessFactor':.12}}

@contextmanager
def parent(n):
    prev=M.parent;M.parent=n
    try:yield
    finally:M.parent=prev

def poly(name,p,mat):M.mesh(name,p,[(0,i,i+1) for i in range(1,len(p)-1)],mat)

def apply_candy_finish():
    """Representative undercoat facets beneath a smooth lacquer clearcoat.

    Texture texels represent groups of flakes at game-view resolution, not
    measured individual particles. Pigment artwork and geometry stay unchanged.
    """
    from scipy.ndimage import gaussian_filter
    rng=np.random.default_rng(196411)
    shape=(512,1024)
    facets=rng.random(shape)<.10
    tilt=gaussian_filter(rng.normal(0,.12,(*shape,2)),sigma=(.45,.45,0))
    tilt+=facets[:,:,None]*rng.uniform(-.36,.36,(*shape,2))
    normals=np.concatenate([tilt,np.ones((*shape,1))],axis=2)
    normals/=np.linalg.norm(normals,axis=2)[:,:,None]
    normal=np.uint8(np.clip((normals*.5+.5)*255,0,255))
    packed=np.full((*shape,3),255,np.uint8)
    packed[:,:,1]=np.uint8(np.where(facets,.48,.92)*255)
    indices={}
    for name,values in [('undercoat_flake_normal',normal),('undercoat_flake_roughness',packed)]:
        buf=io.BytesIO();Image.fromarray(values).save(buf,format='PNG')
        indices[name]=len(M.images);M.images.append((name,buf.getvalue()))
    names={'catrina.candy_rose','catrina.rose_shadow','catrina.candy_scroll_side',
           'catrina.reference_roof_lace','catrina.reference_hood_lace','catrina.reference_deck_lace'}
    for material in M.materials:
        if material['name'] not in names:continue
        material['normalTexture']={'index':indices['undercoat_flake_normal'],'scale':.32}
        material['pbrMetallicRoughness']['metallicRoughnessTexture']={'index':indices['undercoat_flake_roughness']}
    globals()['candy_finish_scope']={'type':'Undercoat facet normal and packed linear roughness maps beneath smooth clear lacquer',
        'size':[1024,512],'seed':196411,'normalScale':.32,
        'limits':'Representative groups of flakes at game resolution; not measured particle size, pigment reflectance or lacquer thickness. Original reference-derived color artwork is unchanged.'}

def image_mat(name,im,metal=.42,rough=.24):
    buf=io.BytesIO();im.save(buf,format='PNG');idx=len(M.images);M.images.append((name,buf.getvalue()))
    mat=M.mat(name,0xffffff,rough,metal);M.materials[mat]['pbrMetallicRoughness']['baseColorTexture']={'index':idx}
    M.materials[mat]['extensions']={'KHR_materials_clearcoat':{'clearcoatFactor':1,'clearcoatRoughnessFactor':.14}}
    return mat

def scroll(d,cx,cy,scale,col,width=1):
    # Paired acanthus-like scrolls, all original vector curves.
    for s in (-1,1):
        pts=[]
        for t in np.linspace(0,math.pi*3.7,64):
            r=scale*(.06+.075*t);pts.append((cx+s*(r*math.cos(t)+scale*.35),cy+r*math.sin(t)*.53))
        d.line(pts,fill=col,width=width)
        for a in np.linspace(-1.05,1.05,7):
            x=cx+s*scale*(.45+.48*math.cos(a));y=cy+scale*.48*math.sin(a)
            d.ellipse((x-scale*.025,y-scale*.018,x+scale*.025,y+scale*.018),fill=col)

def textures():
    rng=np.random.default_rng(1964)
    h,w=512,2048;yy=np.linspace(0,1,h)[:,None]
    base=np.zeros((h,w,3),np.float32)
    for k,(c,a) in enumerate(((198,28),(12,28),(78,28))):base[:,:,k]=c+a*np.sin(yy*math.pi*5+.2)
    flakes=rng.random((h,w));base+=(flakes[:,:,None]-.5)*6;base[flakes>.997]+=35
    im=Image.fromarray(np.clip(base,0,255).astype(np.uint8),'RGB');d=ImageDraw.Draw(im)
    # Texture v=1-y/.94: panel at .70 m, retaining geometry-driven body creases.
    band=int((1-.705/.94)*h)
    d.rectangle((0,band-14,w,band+14),fill='#922246')
    for dy in (-17,-14,14,17):d.line((0,band+dy,w,band+dy),fill='#e5bc80',width=2)
    for x in range(-20,w+40,70):scroll(d,x,band,30,'#d7a66e',1)
    for py in (.36,.40):d.line((0,int((1-py/.94)*h),w,int((1-py/.94)*h)),fill='#f0a7bd',width=1)
    # Door cameo and tiny rear calavera, deliberately restrained.
    for z,y,r in ((-.20,.68,14),(-2.03,.66,10)):
        x=int((2.665-z)/5.33*w);py=int((1-y/.94)*h)
        d.ellipse((x-r,py-r*1.4,x+r,py+r*1.4),outline='#efc88d',width=2)
        d.ellipse((x-r*.47,py-r*.60,x+r*.47,py+r*.35),fill='#e4bc80')
        for dx in (-.19,.19):d.ellipse((x+r*(dx-.12),py-r*.21,x+r*(dx+.12),py+r*.03),fill='#70213d')
        d.line((x-r*.26,py+r*.34,x+r*.26,py+r*.34),fill='#70213d',width=1)
    side=image_mat('candy_scroll_side',im.resize((1024,256),Image.Resampling.LANCZOS))
    top=Image.new('RGB',(1024,1024),'#bd1859');d=ImageDraw.Draw(top)
    # Gold paisley lattice and champagne double-keyline around each panel.
    for row,y in enumerate(range(-50,1100,110)):
        for x in range(-80,1100,140):
            cx=x+(70 if row%2 else 0)
            d.line([(cx,y-43),(cx+68,y),(cx,y+43),(cx-68,y),(cx,y-43)],fill='#852446',width=4)
            scroll(d,cx,y,37,'#e7ba7a',3)
    for inset in (18,29,45):d.rounded_rectangle((inset,inset,1023-inset,1023-inset),radius=11,outline='#edc68e',width=4 if inset!=29 else 7)
    topmat=image_mat('engraved_panel_lace',top,metal=.22,rough=.34)
    # A broad glossy sky reflection must not erase the lace pigment at the
    # low street camera. Keep the clear lacquer highlight, with a wider lobe.
    M.materials[topmat]['extensions']['KHR_materials_clearcoat']={'clearcoatFactor':.40,'clearcoatRoughnessFactor':.30}
    return side,topmat

sidepaint,toppaint=textures()

def side_x(y,z=0):
    shape=np.interp(y,[.16,.20,.30,.43,.52,.62,.68,.705,.73,.78,.84,.88,.91],[.925,.945,.969,.984,.993,1.001,1.008,1.010,1.000,.991,.981,.960,.935])
    taper=.055*max(0,(abs(z)-2.15)/.45)
    return float(shape-taper)

def arch_bottom(z):
    result=.18
    for c,r in ((ZAXLE,.351),(-ZAXLE,.335)):
        dz=z-c
        if abs(dz)<r:result=max(result,HUB+math.sqrt(r*r-dz*dz))
    return result

def outline(name,p,r,mat):tube(name,p+[p[0]],r,mat,8)

def shell():
    # Long, folded side sheets with actual open arches and shoulder/rocker creases.
    for s in (-1,1):
        for za,zb,name in ((-2.55,-.78,'quarter'),(-.776,.88,'door'),(.884,2.55,'fender')):
            rows=[];uv=[]
            zs=np.linspace(za,zb,max(20,int((zb-za)*115)))
            for z in zs:
                lower=arch_bottom(z)
                ys=np.clip([.18,.20,.25,.30,.36,.40,.43,.52,.62,.68,.705,.73,.78,.84,.88,.90],lower,.90)
                rows.append([(s*side_x(y,z),y,z) for y in ys]);uv.append([((2.665-z)/5.33,1-y/.94) for y in ys])
            M.grid('body.'+name,rows,sidepaint,uv,flip=s>0)
        for z0,r in ((ZAXLE,.351),(-ZAXLE,.335)):
            rows=[]
            for a in np.linspace(0,math.pi,65):
                y=HUB+r*math.sin(a);z=z0+r*math.cos(a)
                rows.append([(s*side_x(y,z),y,z),(s*(side_x(y,z)-.06),y-.006,z)])
            M.grid('body.arch_return',rows,paint,flip=s>0)
            # A deep stamped inner fender returns all the way to the tyre
            # housing, so the exterior arch never opens into an empty shell.
            rows=[]
            for a in np.linspace(0,math.pi,65):
                y=HUB+(r+.012)*math.sin(a);z=z0+(r+.012)*math.cos(a)
                rows.append([(s*(side_x(y,z)-.05),y+.007,z),(s*.65,y+.007,z)])
            M.grid('body.wheel_well_liner',rows,black,flip=s>0)
            tube('trim.arch_lip',[(s*(side_x(HUB+r*math.sin(a),z0+r*math.cos(a))+.003),HUB+r*math.sin(a),z0+r*math.cos(a)) for a in np.linspace(0,math.pi,65)],.007,chrome,6)
        # Side mouldings follow the actual body sheet contour.
        for y,rad in ((.651,.008),(.608,.007),(.245,.006)):
            span=[]
            for z in np.linspace(-2.52,2.52,101):
                if y-rad>=arch_bottom(z):span.append((s*(side_x(y,z)+.004),y,z))
                else:
                    if len(span)>1:tube('trim.side_spear',span,rad,chrome,8)
                    span=[]
            if len(span)>1:tube('trim.side_spear',span,rad,chrome,8)
        for z in (-.78,.88):
            tube('body.door_gap',[(s*(side_x(y,z)+.001),y,z) for y in np.linspace(.23,.875,24)],.0021,black,6)
        box('trim.door_handle',(s*1.014,.79,-.48),(.025,.025,.17),chrome,.01)
        cylinder('trim.door_lock',(s*1.01,.747,-.53),(s*1.025,.747,-.53),.012,chrome,12)
        # Fine shoulder rail under the pillarless glass opening.
        tube('trim.belt_rail',[(s*.954,.902,z) for z in np.linspace(-1.28,1.08,45)],.009,chrome,8)
    # Front and rear decks are crowned surfaces, separate opening panels.
    for front,z0,z1 in ((True,.95,2.55),(False,-2.55,-1.28)):
        name='hood' if front else 'trunk'
        hinge_z=z0 if front else z1
        node=M.node(name+'_hinge',body,[0,.901,hinge_z],extras={'axis':[1,0,0],'openRadians':-1.10 if front else 1.08})
        with parent(node):
            rows=[];uv=[]
            for v,z in zip(np.linspace(0,1,38),np.linspace(z0,z1,38)):
                hw=min(.94,side_x(.88,z)-.015)
                rows.append([(x,.901+.027*(1-(x/hw)**2),z) for x in np.linspace(-hw,hw,31)])
                uv.append([(u,v) for u in np.linspace(0,1,31)])
            M.grid('body.'+name,rows,toppaint,uv)
            for s in (-1,1):tube('trim.'+name+'_edge',[(s*(min(.94,side_x(.88,z)-.015)+.002),.901,z) for z in np.linspace(z0,z1,40)],.0045,chrome,6)
            M.grid('body.'+name+'_inner',np.array(rows)-[0,.012,0],rose,uv,flip=True)
        for s in (-1,1):
            rows=[]
            for z in np.linspace(min(z0,z1),max(z0,z1),42):
                hw=min(.94,side_x(.88,z)-.015)
                rows.append([(s*x,.901-.015*t,z) for t,x in zip(np.linspace(0,1,6),np.linspace(hw,side_x(.88,z),6))])
            M.grid('body.deck_shoulder',rows,paint,flip=s<0)
    # Underbody floor stops at the wheel openings; deck interiors stay accessible.
    box('body.cabin_floor',(0,.225,.11),(1.77,.065,2.06),rose,.025)
    box('body.rear_cabin_tunnel',(0,.225,-1.11),(1.02,.065,.38),rose,.018)
    box('body.firewall',(0,.57,.84),(1.74,.58,.045),rose,.025)
    box('body.rear_bulkhead',(0,.55,-1.13),(1.74,.58,.045),rose,.025)
    # Leave real tyre pockets: the closed-link axle shifts sideways as it
    # drops. The narrow central floor clears that motion; full-width floor
    # resumes behind the rear tyre envelope, supporting the hydraulic rack.
    box('body.trunk_center_floor',(0,.29,-1.575),(1.02,.045,.75),plum,.015)
    box('body.trunk_aft_floor',(0,.29,-2.2625),(1.77,.045,.625),plum,.015)

def roof_and_glass():
    # Pillarless two-door hardtop: raked front/rear glass and broad C pillars.
    rows=[];uv=[]
    for v,z in zip(np.linspace(0,1,38),np.linspace(-.91,.53,38)):
        edge=1.277-.012*abs((z+.19)/.72)
        rows.append([(x,edge+.035*(1-(x/.789)**2),z) for x in np.linspace(-.789,.789,35)])
        uv.append([(u,v) for u in np.linspace(0,1,35)])
    M.grid('cab.lace_roof',rows,toppaint,uv)
    M.grid('cab.roof_headliner',np.array(rows)-[0,.018,0],plum,uv,flip=True)
    for s in (-1,1):
        edge=[]
        for z in np.linspace(-.91,.53,38):
            y=1.277-.012*abs((z+.19)/.72)
            edge.append([(s*.789,y,z),(s*.789,y-.018,z)])
        M.grid('cab.folded_roof_edge',edge,paint,flip=s<0)
    for z in (-.91,.53):
        y=1.277-.012*abs((z+.19)/.72)
        edge=[]
        for x in np.linspace(-.789,.789,35):
            yy=y+.035*(1-(x/.789)**2);edge.append([(x,yy,z),(x,yy-.018,z)])
        M.grid('cab.roof_end_return',edge,paint,flip=z<0)
    for s in (-1,1):
        # Thin A posts and thicker folded rear sail panels.
        tube('cab.A_post',[(s*.925,.907,1.02),(s*.790,1.274,.53)],.023,paint,12)
        tube('trim.A_post',[(s*.934,.914,1.025),(s*.804,1.279,.531)],.009,chrome,8)
        p=[(s*.79,1.275,-.91),(s*.948,.906,-1.30),(s*.943,.904,-.99),(s*.789,1.268,-.69)]
        poly('cab.C_pillar',p if s<0 else p[::-1],toppaint)
        tube('trim.rear_post',[(s*.79,1.278,-.91),(s*.953,.907,-1.30)],.010,chrome,8)
        tube('trim.roof_drip',[(s*.80,1.278,z) for z in np.linspace(-.92,.54,36)],.008,chrome,8)
        tube('trim.window_top',[(s*.795,1.263,z) for z in np.linspace(-.69,.52,35)],.008,chrome,8)
        # Open front window; small fixed rear quarter glass preserves hardtop silhouette.
        poly('cab.quarter_glass',[(s*.923,.915,-.97),(s*.79,1.257,-.68),(s*.79,1.257,-.35),(s*.923,.915,-.35)],glass)
        tube('trim.quarter_divider',[(s*.924,.914,-.35),(s*.792,1.259,-.35)],.007,chrome,8)
    for front in (True,False):
        lowz,highz=(1.02,.53) if front else (-1.30,-.91)
        p=[(-.917,.919,lowz),(.917,.919,lowz),(.781,1.268,highz),(-.781,1.268,highz)]
        poly('cab.windshield' if front else 'cab.backlight',p if front else p[::-1],glass)
        outline('trim.glass_surround',p,.010,chrome)
    for s in (-1,1):
        # Door mirror and slender pedestal.
        a=(s*.958,.90,.73);b=(s*1.052,1.00,.69)
        cylinder('trim.mirror_stalk',a,b,.012,chrome,10)
        box('trim.mirror_back',(s*1.066,1.02,.68),(.055,.071,.13),chrome,.025)
        box('trim.mirror_glass',(s*1.067,1.022,.609),(.043,.054,.004),silver,.009)
    for x in (-.35,.32):tube('trim.wiper',[(x-.12,.935,1.015),(x+.11,.976,.967)],.005,steel,8)

def front_rear():
    # Recessed grille and quadruple round headlamps across a squared-off nose.
    rows=[]
    for x in np.linspace(-.938,.938,43):
        top=.901+.027*(1-(x/.938)**2)
        rows.append([(x,.827,2.559),(x,top,2.553)])
    M.grid('front.painted_header',rows,paint)
    tube('trim.nose_brow',[(x,.834,2.596) for x in np.linspace(-.93,.93,35)],.009,chrome,8)
    box('front.lower_valance',(0,.267,2.524),(1.84,.18,.06),paint,.025)
    for s in (-1,1):
        box('front.fender_corner',(s*.936,.574,2.535),(.054,.63,.056),paint,.02)
        box('front.lower_apron',(s*.735,.457,2.546),(.40,.068,.05),paint,.012)
    box('front.grille_recess',(0,.657,2.564),(1.84,.36,.035),black,.025)
    for y in np.linspace(.505,.819,10):box('front.horizontal_grille',(0,y,2.588),(1.13,.009,.012),chrome,.003)
    for x in np.linspace(-.55,.55,24):box('front.vertical_grille',(x,.658,2.59),(.008,.32,.015),silver,.002)
    for s in (-1,1):
        box('front.headlamp_pod',(s*.735,.662,2.579),(.427,.365,.048),chrome,.055)
        for x in (s*.637,s*.827):
            cylinder('front.headlamp_dark',(x,.675,2.606),(x,.675,2.614),.091,black,40)
            cylinder('front.headlamp_reflector',(x,.675,2.614),(x,.675,2.625),.079,lamp,40)
            torus('front.headlamp_rim',(x,.675,2.621),.086,.006,chrome,axis=(0,0,1),segments=40,sides=7)
            # Lens fluting resolves as real bright fine structure in close view.
            for dx in np.linspace(-.061,.061,9):
                h=math.sqrt(.072**2-dx**2);cylinder('front.lens_flute',(x+dx,.675-h,2.63),(x+dx,.675+h,2.63),.0019,silver,5)
        box('front.signal_housing',(s*.77,.405,2.627),(.24,.077,.042),chrome,.018)
        box('front.amber_lens',(s*.77,.406,2.650),(.205,.043,.007),amber,.012)
    # Bumpers include real wraparound ends, highlights and guards.
    for front in (True,False):
        z=2.605 if front else -2.605
        p=[(-.965,.420,z*.975),(-.90,.392,z),(0,.375,z+( .015 if front else -.015)),(.90,.392,z),(.965,.420,z*.975)]
        tube('trim.bumper_beam',p,.045,chrome,10)
        tube('trim.bumper_highlight',[(x,y+.033,zz) for x,y,zz in p],.012,chrome,8)
        for s in (-1,1):
            box('trim.bumper_guard',(s*.56,.386,z),(.053,.20,.074),chrome,.018)
            box('trim.bumper_mount',(s*.56,.35,z*.94),(.07,.07,.15),steel,.01)
        plate=M.node('front_plate' if front else 'rear_plate',body,[0,.37,z])
        with parent(plate):
            box('trim.plate_backing',(0,.36,z),(.31,.15,.016),chrome,.01)
            box('trim.plate',(0,.36,z+(.010 if front else -.010)),(.275,.117,.008),black,.003)
    box('rear.tail_panel',(0,.655,-2.557),(1.88,.39,.028),paint,.035)
    rows=[]
    for x in np.linspace(-.938,.938,43):
        top=.901+.027*(1-(x/.938)**2)
        rows.append([(x,.837,-2.559),(x,top,-2.553)])
    M.grid('rear.painted_header',rows,paint,flip=True)
    tube('trim.tail_brow',[(x,.846,-2.581) for x in np.linspace(-.93,.93,35)],.007,chrome,8)
    box('rear.lower_valance',(0,.267,-2.524),(1.84,.18,.06),paint,.025)
    for s in (-1,1):box('rear.quarter_corner',(s*.936,.574,-2.535),(.054,.63,.056),paint,.02)
    box('rear.inset_trim',(0,.658,-2.577),(1.82,.258,.023),chrome,.035)
    box('rear.dark_inset',(0,.658,-2.593),(1.75,.213,.012),black,.02)
    for s in (-1,1):
        for ax in (.45,.635,.82):
            x=s*ax;torus('rear.tail_bezel',(x,.664,-2.614),.078,.008,chrome,axis=(0,0,1),segments=36,sides=8)
            cylinder('rear.tail_lens',(x,.664,-2.605),(x,.664,-2.622),.067,tail,36)
            for radius in (.037,.054):torus('rear.tail_lens_ring',(x,.664,-2.625),radius,.003,tail,axis=(0,0,1),segments=32,sides=5)
    tube('rear.center_badge',[(-.08,.67,-2.62),(0,.63,-2.625),(.08,.67,-2.62)],.007,chrome,8)
    tube('front.hood_ornament',[(0,.932,2.38),(0,.964,2.42),(0,.95,2.49)],.005,chrome,8)

def interior():
    for z,w in ((.24,1.48),(-.78,1.50)):
        box('interior.bench_cushion',(0,.43,z),(w,.20,.51),plum,.075)
        box('interior.bench_back',(0,.68,z-.21),(w,.50,.14),plum,.055,B=g.rotX(-.12))
        for x in np.linspace(-w*.46,w*.46,22):
            tube('interior.seat_pleat',[(x,.531,z+.18),(x,.535,z-.17),(x,.49,z-.23)],.0045,pipe,6)
            tube('interior.back_pleat',[(x,.52,z-.124),(x,.85,z-.167),(x,.90,z-.19)],.004,pipe,6)
        for s in (-1,1):tube('interior.bench_piping',[(s*w*.48,.46,z+.22),(s*w*.48,.53,z+.17),(s*w*.48,.53,z-.17)],.005,pipe,7)
    box('interior.dashboard',(0,.79,.79),(1.68,.16,.23),plum,.045)
    box('interior.dash_chrome',(0,.775,.656),(1.55,.055,.016),chrome,.007)
    # Driver is left (-X). Gauges face into the cabin.
    for x,r in ((-.53,.062),(-.38,.036),(-.68,.036)):
        cylinder('interior.gauge_face',(x,.802,.660),(x,.802,.648),r,black,24)
        torus('interior.gauge_bezel',(x,.802,.645),r,.004,chrome,axis=(0,0,1),segments=24,sides=6)
        tube('interior.gauge_needle',[(x,.802,.642),(x+r*.45,.802+r*.45,.642)],.0015,white,5)
    cylinder('interior.steering_column',(-.53,.68,.68),(-.53,.77,.43),.025,steel,16)
    torus('interior.steering_ring',(-.53,.795,.41),.175,.011,plum,axis=(0,.30,1),segments=48,sides=8)
    for a in (0,2.1,4.2):cylinder('interior.steering_spoke',(-.53,.795,.41),(-.53+.162*math.cos(a),.795+.155*math.sin(a),.41-.047*math.sin(a)),.007,chrome,8)
    cylinder('interior.steering_hub',(-.53,.795,.40),(-.53,.795,.425),.034,chrome,20)
    for s in (-1,1):
        box('interior.door_card',(s*.893,.61,-.03),(.045,.43,1.57),plum,.02)
        box('interior.arm_rest',(s*.858,.59,-.12),(.10,.07,.47),plum,.025)
        tube('interior.door_trim',[(s*.865,.76,-.70),(s*.865,.76,.69)],.006,chrome,8)
        cylinder('interior.door_pull',(s*.845,.687,-.15),(s*.845,.687,.07),.009,chrome,8)
    # Palm-sized wired switch pendant resting on the bench. A dark inset face
    # and four panel-mounted toggles distinguish it from a solid chrome block.
    box('interior.hydraulic_switchbox',(.06,.554,.27),(.15,.035,.09),silver,.012)
    box('interior.switch_face',(.06,.572,.27),(.126,.003,.068),black,.009)
    for x in (.025,.095):
        for z in (.25,.29):
            cylinder('interior.switch_nut',(x,.574,z),(x,.577,z),.006,chrome,12)
            cylinder('interior.switch_stalk',(x,.577,z),(x,.592,z-.005),.0022,chrome,10)
            cylinder('interior.switch_knob',(x,.589,z-.004),(x,.597,z-.007),.0035,black,10)
    for x in (.012,.108):
        for z in (.245,.295):
            cylinder('interior.switch_face_screw',(x,.573,z),(x,.575,z),.0018,chrome,8)
    cylinder('interior.switch_strain_relief',(.135,.550,.27),(.153,.550,.27),.006,black,12)
    tube('interior.switch_cable',[(.153,.550,.27),(.20,.545,.29),(.26,.540,.40),(.48,.533,.45),(.68,.518,.46),(.77,.45,.48),(.79,.31,.58)],.003,black,10)
    box('interior.rear_shelf',(0,.83,-1.05),(1.67,.055,.35),plum,.015)
    for x in (-.50,.50):
        cylinder('interior.speaker',(x,.857,-1.05),(x,.864,-1.05),.115,black,28)
        for d in np.linspace(-.09,.09,9):
            h=math.sqrt(.102**2-d*d);cylinder('interior.speaker_grille',(x-h,.867,-1.05+d),(x+h,.867,-1.05+d),.0015,silver,5)

def wheel(i):
    front=i<2;s=-1 if i%2==0 else 1;x=s*(.765 if front else .755);z=ZAXLE if front else -ZAXLE
    c=np.array([x,HUB,z]);node=M.node('wheel_'+str(i),body,c,extras={'corner':['FL','FR','RL','RR'][i],'tyreDiameter':.5782,'tyreWidth':.155})
    steer=M.node('wheel_'+str(i)+'_steer',node,c);spin=M.node('wheel_'+str(i)+'_spin',steer,c,extras={'spinAxis':[1,0,0]})
    with parent(spin):
        # Rounded 155/80 R13 profile with a true .5782 m outer diameter.
        profile=[(-.0775,.178),(-.0775,.215),(-.073,.255),(-.059,.282),(-.044,.2891),(.044,.2891),(.059,.282),(.073,.255),(.0775,.215),(.0775,.178)]
        rows=[]
        for a in np.linspace(0,TAU,81):rows.append([c+[xx,r*math.sin(a),r*math.cos(a)] for xx,r in profile])
        M.grid('wheel.tyre',rows,rubber,flip=True)
        for side in (-1,1):
            # Narrow concentric ivory band; tyre stays black at the rim and shoulder.
            rows=[]
            for a in np.linspace(0,TAU,81):rows.append([c+[side*.0778,r*math.sin(a),r*math.cos(a)] for r in (.219,.233)])
            M.grid('wheel.whitewall',rows,white,flip=side<0)
            torus('wheel.rim_lip',c+[side*.070,0,0],.172,.009,chrome,segments=64,sides=7)
            torus('wheel.inner_barrel',c+[side*.047,0,0],.155,.006,chrome,segments=48,sides=7)
        cylinder('wheel.rim_barrel',c+[-.060,0,0],c+[.060,0,0],.165,silver,64,caps=False)
        cylinder('wheel.hub',c+[-.065,0,0],c+[.065,0,0],.041,chrome,24)
        # 72 fine cross-laced steel spokes, prominent wire wheel face.
        for side in (-1,1):
            for j in range(36):
                a=TAU*j/36
                for offset,rad,depth in ((.15,.041,.057),(-.13,.051,.018)):
                    a2=a+offset
                    cylinder('wheel.wire_spoke',c+[side*depth,rad*math.sin(a2),rad*math.cos(a2)],c+[side*.061,.161*math.sin(a),.161*math.cos(a)],.0017,chrome,5)
            cylinder('wheel.knockoff_hub',c+[side*.065,0,0],c+[side*.084,0,0],.036,gold,20)
            for a in (0,TAU/3,TAU*2/3):
                cylinder('wheel.knockoff_ear',c+[side*.08,.018*math.sin(a),.018*math.cos(a)],c+[side*.087,.057*math.sin(a+.2),.057*math.cos(a+.2)],.008,chrome,8,r2=.004)
        for a in np.linspace(0,TAU,64,endpoint=False):
            for dx in (-.028,.028):
                p1=c+[dx-.013,.2878*math.sin(a-.025),.2878*math.cos(a-.025)]
                p2=c+[dx+.013,.2878*math.sin(a+.025),.2878*math.cos(a+.025)]
                cylinder('wheel.tread_sipe',p1,p2,.0011,black,5)
    # Stationary brake drum / backing plate, intentionally outside spin node.
    with parent(steer):cylinder('wheel.brake_drum',c+[-.05,0,0],c+[.05,0,0],.128,steel,40)
    return c

def gear():
    with parent(body):
        # Central narrowed boxed X frame, linked at both axles and body mounts.
        for s in (-1,1):
            tube('chassis.boxed_X_rail',[(s*.57,.27,2.39),(s*.57,.27,1.53),(s*.22,.25,.40),(s*.12,.25,-.20),(s*.52,.29,-1.46),(s*.58,.32,-2.30)],.051,steel,4)
            for z in (-2.17,-.90,.80,2.18):cylinder('chassis.body_outrigger',(s*.49,.26,z),(s*.89,.26,z),.025,steel,8)
        for z in (1.98,-.75,-2.23):box('chassis.crossmember',(0,.27,z),(1.14,.075,.08),steel,.008)
        box('driveline.V8_block',(0,.48,1.54),(.44,.37,.59),steel,.04)
        for s in (-1,1):box('driveline.valve_cover',(s*.17,.65,1.55),(.18,.12,.52),chrome,.04,B=g.rotZ(s*.4))
        cylinder('driveline.aircleaner',(0,.697,1.54),(0,.751,1.54),.19,chrome,32)
        cylinder('driveline.transmission',(0,.40,1.22),(0,.30,.58),.15,silver,20,r2=.075)
        for s in (-1,1):tube('driveline.exhaust',[(s*.22,.38,1.40),(s*.32,.22,.50),(s*.34,.22,-1.21),(s*.46,.23,-2.47)],.022,silver,12)
    axle=M.node('rear_axle',body,[0,HUB,-ZAXLE],extras={'rollAxis':[0,0,1]})
    with parent(axle):
        cylinder('axle.tube',(-.755,HUB,-ZAXLE),(.755,HUB,-ZAXLE),.041,steel,20)
        box('axle.differential',(0,HUB,-ZAXLE),(.25,.23,.25),steel,.075)
        cylinder('axle.diff_cover',(0,HUB,-ZAXLE-.12),(0,HUB,-ZAXLE-.145),.106,chrome,16)
        cylinder('axle.pinion',(0,HUB,-ZAXLE+.10),(0,HUB,-ZAXLE+.22),.046,steel,16)
        for s in (-1,1):box('axle.spring_saddle',(s*.56,HUB+.045,-ZAXLE),(.16,.055,.16),steel,.01)
    for i in range(4):
        c=wheel(i);s=-1 if i%2==0 else 1;front=i<2;z=c[2]
        if front:
            for upper in (False,True):
                a=np.array([s*.18,.43 if upper else .25,z]);b=np.array([s*.715,.43 if upper else .25,z])
                nm='front_'+str(i)+('_upper' if upper else '_lower');n=M.node(nm,body,a,extras={'end':b.tolist(),'axis':[0,0,1]})
                with parent(n):
                    for dz in (-.16,.16) if upper else (-.22,.22):cylinder('front.control_arm',a+[0,0,dz],b,.019 if upper else .024,chrome,12)
                    cylinder('front.pivot_shaft',a+[0,0,-.18 if upper else -.24],a+[0,0,.18 if upper else .24],.019,steel,12)
                    torus('front.balljoint',b,.024,.009,steel,axis=(0,1,0),segments=18,sides=8)
                M.joints[nm]={'a':a.tolist(),'b':b.tolist()}
            upright=M.node('upright_'+str(i),body,c)
            with parent(upright):cylinder('front.upright',(s*.715,.25,z),(s*.715,.43,z),.027,steel,14)
        else:
            a=np.array([s*.56,.33,-.45]);b=np.array([s*.56,.33,-ZAXLE]);nm='rear_'+str(i)+'_lower'
            n=M.node(nm,body,a,extras={'end':b.tolist()})
            with parent(n):cylinder('rear.trailing_link',a,b,.021,chrome,12)
            M.joints[nm]={'a':a.tolist(),'b':b.tolist()}
        a=np.array([s*(.55 if front else .56),.90,z]);b=np.array([a[0],.27 if front else .33,z])
        n=M.node('hydraulic_'+str(i),body,a,extras={'end':b.tolist(),'axis':[0,-1,0]})
        barrel=M.node('hydraulic_'+str(i)+'_barrel',n,a)
        with parent(barrel):
            cylinder('hydraulic.barrel',a,a+[0,-.36,0],.032,chrome,20)
            for dy in (-.015,-.345):cylinder('hydraulic.seal_collar',a+[0,dy+.008,0],a+[0,dy-.008,0],.040,silver,20)
            cylinder('hydraulic.top_pin',a+[-.05,0,0],a+[.05,0,0],.010,steel,12)
        cup=np.array([a[0],.55,z]);rod=M.node('hydraulic_'+str(i)+'_rod',n,cup)
        with parent(rod):
            cylinder('hydraulic.piston_rod',cup,cup+[0,.34,0],.014,chrome,16)
            cylinder('hydraulic.spring_cup',cup+[0,-.010,0],cup+[0,.010,0],.072,chrome,24)
        springlen=.28 if front else .22
        coil=M.node('coil_'+str(i),body,b,extras={'length':springlen})
        with parent(coil):
            g.coil('hydraulic.coil',b,b+[0,springlen,0],.049,.0085,red,6)
            cylinder('hydraulic.bottom_seat',b+[0,-.012,0],b+[0,.008,0],.067,steel,24)
        with parent(body):
            cylinder('chassis.ram_tower',a+[0,-.035,0],a+[0,.002,0],.055,steel,20)
            cylinder('chassis.ram_mount',a+[0,-.01,0],(s*.48,.89,z),.025,steel,12)
            tube('hydraulic.pressure_hose',[a+[0,-.04,.032],(s*.46,.65,z+.07),(s*.39,.36,z+.13),(s*.39,.35,-1.90)],.0055,black,8)
        M.joints['hydraulic_'+str(i)]={'a':a.tolist(),'b':b.tolist(),'barrelLength':.36,'rodCupY':.55,'coilLength':springlen}
    a=np.array([-.60,.62,-1.30]);b=np.array([.56,.35,-1.30]);n=M.node('rear_panhard',body,a)
    with parent(n):cylinder('rear.panhard',a,b,.017,chrome,12)
    M.joints['rear_panhard']={'a':a.tolist(),'b':b.tolist()}
    for nm,a,b,r in (('rear_upper',[0,.46,-.45],[0,.42,-ZAXLE],.023),('driveshaft',[0,.30,.59],[0,HUB,-ZAXLE+.22],.034)):
        a=np.array(a);b=np.array(b);n=M.node(nm,body,a)
        with parent(n):cylinder('driveline.'+nm,a,b,r,steel,16)
        M.joints[nm]={'a':a.tolist(),'b':b.tolist()}

def trunk():
    n=M.node('trunk_equipment',body)
    with parent(n):
        box('hydraulic.equipment_rack',(0,.35,-2.195),(1.55,.055,.65),chrome,.01)
        # Four batteries and two isolated pump/reservoir circuits.
        for x in (-.60,-.20,.20,.60):
            box('hydraulic.battery',(x,.51,-2.02),(.30,.27,.24),black,.025)
            box('hydraulic.battery_lid',(x,.66,-2.02),(.30,.035,.24),plum,.01)
            for s in (-1,1):
                cylinder('hydraulic.battery_terminal',(x+s*.09,.673,-2.02),(x+s*.09,.695,-2.02),.013,red if s<0 else steel,12)
                tube('hydraulic.heavy_battery_cable',[(x+s*.09,.697,-2.02),(x+s*.10,.72,-2.16),(x+s*.10,.49,-2.22)],.008,red if s<0 else black,8)
            box('hydraulic.battery_clamp',(x,.68,-2.02),(.028,.025,.26),chrome,.003)
        for z in (-2.25,-2.43):
            cylinder('hydraulic.chrome_motor',(-.55,.48,z),(-.13,.48,z),.075,chrome,28)
            cylinder('hydraulic.gold_pump',(-.13,.48,z),(.06,.48,z),.064,gold,24)
            cylinder('hydraulic.reservoir',(.08,.48,z),(.50,.48,z),.080,chrome,28)
            box('hydraulic.valve_bank',(.59,.47,z),(.15,.14,.15),gold,.02)
            for x in (-.45,.35):box('hydraulic.pump_mount',(x,.385,z),(.09,.10,.15),steel,.015)
            for dz in (-.035,.035):tube('hydraulic.pressure_line',[(.59,.55,z+dz),(.71,.57,z+dz),(.73,.38,-1.92)],.005,red if dz<0 else black,8)
        box('hydraulic.rear_trunk_liner',(0,.54,-2.54),(1.73,.40,.035),plum,.01)

def export():
    doc={'asset':{'version':'2.0','generator':'La Catrina original CPU author'},'extensionsUsed':['KHR_materials_clearcoat'],'scene':0,'scenes':[{'name':'La Catrina hydraulic coupe','nodes':[0]}],'nodes':copy.deepcopy(M.nodes),'meshes':[],'materials':M.materials,'bufferViews':[],'accessors':[],'buffers':[{'byteLength':0}],'images':[],'textures':[],'samplers':[{'magFilter':9729,'minFilter':9987,'wrapS':33071,'wrapT':33071}],'animations':[]};binary=bytearray()
    def view(data,target=None):
        binary.extend(b'\0'*(-len(binary)%4));v={'buffer':0,'byteOffset':len(binary),'byteLength':len(data)};binary.extend(data)
        if target:v['target']=target
        doc['bufferViews'].append(v);return len(doc['bufferViews'])-1
    def acc(data,typ,integer=False,bounds=False):
        a=np.asarray(data,np.uint32 if integer else np.float32);v={'bufferView':view(a.tobytes(),34963 if integer else None),'componentType':5125 if integer else 5126,'count':len(a),'type':typ}
        if bounds:v.update(min=a.min(0).tolist(),max=a.max(0).tolist())
        doc['accessors'].append(v);return len(doc['accessors'])-1
    for name,data in M.images:
        doc['images'].append({'name':name,'bufferView':view(data),'mimeType':'image/png'});doc['textures'].append({'sampler':0,'source':len(doc['images'])-1})
    batches={}
    for p in M.parts:
        key=(p['parent'],p['mat'],p['name'].split('.')[0]);b=batches.setdefault(key,{'p':[],'n':[],'uv':[],'f':[],'count':0,'names':set(),'ranges':[]})
        b['ranges'].append({'name':p['name'],'start':b['count'],'count':len(p['p'])})
        b['p'].append(p['p']);b['n'].append(p['n']);b['uv'].append(p['uv']);b['f'].append(p['f']+b['count']);b['count']+=len(p['p']);b['names'].add(p['name'])
    for (node,mat,semantic),b in batches.items():
        p,n,uv,f=[np.concatenate(b[k]) for k in ('p','n','uv','f')]
        mesh={'name':semantic+'.'+M.materials[mat]['name'],'primitives':[{'attributes':{'POSITION':acc(p,'VEC3',bounds=True),'NORMAL':acc(n,'VEC3'),'TEXCOORD_0':acc(uv,'VEC2')},'indices':acc(f.reshape(-1,1),'SCALAR',True),'material':mat}],'extras':{'sourceParts':sorted(b['names']),'sourcePartRanges':b['ranges']}}
        doc['meshes'].append(mesh);doc['nodes'][node]['children'].append(len(doc['nodes']));doc['nodes'].append({'name':mesh['name'],'mesh':len(doc['meshes'])-1})
    for name,angle in (('hood_hinge',-1.10),('trunk_hinge',1.08)):
        index=next(i for i,n in enumerate(M.nodes) if n['name']==name)
        times=acc(np.array([0,1,2]).reshape(-1,1),'SCALAR',bounds=True)
        values=acc([[0,0,0,1],[math.sin(angle/2),0,0,math.cos(angle/2)],[0,0,0,1]],'VEC4')
        doc['animations'].append({'name':name.replace('_hinge','')+'_open','channels':[{'sampler':0,'target':{'node':index,'path':'rotation'}}],'samplers':[{'input':times,'output':values,'interpolation':'LINEAR'}]})
    for n in doc['nodes']:
        if not n.get('children'):n.pop('children',None)
    from catrina_ao import apply_cache
    cavity_info=apply_cache(doc,binary,ROOT)
    binary.extend(b'\0'*(-len(binary)%4));doc['buffers'][0]['byteLength']=len(binary)
    js=json.dumps(doc,separators=(',',':')).encode();js+=b' '*(-len(js)%4)
    glb=struct.pack('<III',0x46546c67,2,28+len(js)+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_bytes(glb)
    parents={child:i for i,node in enumerate(M.nodes) for child in node.get('children',[])}
    transforms={}
    def world_transform(i):
        if i in transforms:return transforms[i]
        node=M.nodes[i]
        if 'matrix' in node:matrix=np.asarray(node['matrix'],float).reshape(4,4,order='F')
        else:
            x,y,z,w=node.get('rotation',[0,0,0,1]);length=math.sqrt(x*x+y*y+z*z+w*w)
            x,y,z,w=[a/length for a in (x,y,z,w)]
            rotation=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
            matrix=np.eye(4);matrix[:3,:3]=rotation@np.diag(node.get('scale',[1,1,1]));matrix[:3,3]=node.get('translation',[0,0,0])
        if i in parents:matrix=world_transform(parents[i])@matrix
        transforms[i]=matrix;return matrix
    p=np.concatenate([(np.c_[part['p'],np.ones(len(part['p']))]@world_transform(part['parent']).T)[:,:3] for part in M.parts]);lo=p.min(0);hi=p.max(0)
    manifest={'asset':'La Catrina','version':3,'units':'metres','up':'+Y','forward':'+Z','groundOffset':0,'bounds':{'min':lo.tolist(),'max':hi.tolist(),'size':(hi-lo).tolist()},'bodyWidth':2.02,'wheelbase':3.0226,'frontTrack':1.53,'rearTrack':1.51,'tyreDiameter':.5782,'tyreWidth':.155,'wheelCenters':{str(i):[(-1 if i%2==0 else 1)*(.765 if i<2 else .755),HUB,ZAXLE if i<2 else -ZAXLE] for i in range(4)},'joints':M.joints,'meshDraws':len(doc['meshes']),'nodes':len(doc['nodes']),'triangles':sum(len(p['f']) for p in M.parts),'vertices':sum(len(p['p']) for p in M.parts),'sourceParts':len(M.parts),'animations':[a['name'] for a in doc['animations']],'embeddedImages':len(M.images),'bytes':len(glb),'sha256':hashlib.sha256(glb).hexdigest(),'sourceSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'sourceFiles':{name:hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest() for name in ('catrina_generate.py','catrina_art.py','catrina_hardware.py','catrina_reference_paint.py','baja427_generate.py')},'provenance':'Original authored geometry and small vector cameos. Roof, hood and deck paint use rectified source ornament masks plus bounded source grain, remapped to the supplied Candy and Champagne palette pigments; the side-spear scroll uses a paint-only source mask in a separate narrow UV field. All derive from the user-supplied La-Catrina-Master.jpg. Source hash, sampled regions and transforms are recorded in referencePaint. No external meshes copied.','limitations':['Fictional game model inspired by a 1964 hardtop; not licensed vehicle CAD or manufacturing geometry.','Hydraulics and suspension are a reduced game approximation, not multibody linkage or certified mesh clearance.','Hydraulic hopping is implemented by the shared physical playground; portable service clips open the hood and trunk only.']}
    manifest.update(cavity_info)
    manifest['sourceFiles']['catrina_ao.py']=hashlib.sha256((Path(__file__).parent/'catrina_ao.py').read_bytes()).hexdigest()
    manifest['sourceFiles']['catrina_frame_pockets.py']=hashlib.sha256((Path(__file__).parent/'catrina_frame_pockets.py').read_bytes()).hexdigest()
    manifest.update(bodyOffsetZ=-.19,cabinOffsetZ=-.23,interiorOffsetZ=-.15)
    manifest['referencePaint']=globals().get('reference_paint_provenance',{})
    manifest['framePocket']=globals().get('frame_pocket_scope',{})
    manifest['candyFinish']=globals().get('candy_finish_scope',{})
    OUT.with_suffix('.json').write_text(json.dumps(manifest,indent=2)+'\n')
    lib=ROOT/'asset-library/models/la-catrina';lib.mkdir(parents=True,exist_ok=True)
    for file in (OUT,OUT.with_suffix('.json')):(lib/file.name).write_bytes(file.read_bytes())
    for name,data in M.images:(lib/(name+'.png')).write_bytes(data)
    library={'schemaVersion':1,'revision':3,'id':'vehicle.la-catrina','type':'gltf-model','file':'la-catrina.glb','sha256':manifest['sha256'],'units':'metres','up':'+Y','forward':'+Z','groundOffset':0,'runtimeDependencies':[],'source':manifest['provenance'],'license':'Original geometry and small vector cameos: project license. Top paint and side-spear scroll derive from user-supplied artwork; no independent public redistribution license is asserted for that artwork.','worldBounds':manifest['bounds'],'rig':{'wheelCenters':manifest['wheelCenters'],'joints':M.joints,'clips':manifest['animations']},'files':['la-catrina.glb','la-catrina.json','asset.json','README.md']+[name+'.png' for name,data in M.images],'limitations':manifest['limitations']}
    (lib/'asset.json').write_text(json.dumps(library,indent=2)+'\n')
    (lib/'README.md').write_text('# La Catrina\n\nOriginal candy-rose hydraulic coupe authored from the supplied visual atlas. The standard GLB contains all textures, 13-inch chrome wire wheels with narrow whitewalls, four headlamps, six rear lamps, plum pleated benches, an X frame, two hydraulic pump circuits and four batteries.\n\nMetres, +Y up, +Z forward. Root origin is ground level in the rest pose. Wheel nodes and separate steering/spin groups are named in `la-catrina.json`; the rear axle is one rigid node. Hood and trunk have portable service animations. Hydraulic road motion is supplied by the engine adapter and the shared physical solver.\n\nRequires Python with NumPy, Pillow and SciPy. Regenerate with `python scripts/catrina_generate.py`; validate with `python scripts/catrina_audit.py`. Geometry and small vector cameos are original. Roof, hood and deck use rectified source ornament masks plus bounded source grain remapped to palette pigments. The side-spear scroll uses a source mask in a dedicated narrow UV field; its larger La Catrina and calavera cameos are original vectors. See `referencePaint` in the JSON for exact source SHA, sample coordinates and processing. Coachwork is authored in `scripts/catrina_art.py`; researched fittings in `scripts/catrina_hardware.py`; spring-pocket frame routing in `scripts/catrina_frame_pockets.py`; reference-paint rectification in `scripts/catrina_reference_paint.py`. These sources, `catrina_generate.py`, `baja427_generate.py`, `catrina_ao.py`, any matching geometry-bound cavity cache and the exact atlas under `docs/la-catrina/references/La-Catrina-Master.jpg` are required for regeneration. Original geometry follows the project license; no public redistribution license is asserted for the user-supplied artwork.\n')
    print(json.dumps({k:manifest[k] for k in ('asset','bounds','triangles','meshDraws','bytes','sha256')},indent=2))

if __name__=='__main__':
    import catrina_art
    catrina_art.install(globals())
    shell();roof_and_glass();front_rear();interior();gear();trunk()
    import catrina_hardware
    catrina_hardware.add_hardware(globals())
    apply_candy_finish()
    export()
