"""Blender 4.5 authored export for Cinder's Unity adaptation, metres/Y-up/+Z."""
import bpy, math, sys, random
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'build/unity-assets'
def clear():
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def mat(name,c,metal=0,rough=.5):
    m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;return m
def xyz(p):return (p[0],-p[2],p[1])
def finish(o,name,m,parent=None):
    o.name=name;o.data.materials.append(m)
    if parent:o.parent=parent
    return o
def box(name,p,s,m,parent=None,bevel=0):
    if bevel:
        bpy.ops.mesh.primitive_cube_add(size=1,location=xyz(p));o=bpy.context.object;o.scale=(s[0],s[2],s[1]);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    else:
        # Direct mesh construction avoids thousands of global dependency updates.
        sx,sy,sz=s[0]*.5,s[2]*.5,s[1]*.5
        vertices=[(-sx,-sy,-sz),(sx,-sy,-sz),(sx,sy,-sz),(-sx,sy,-sz),(-sx,-sy,sz),(sx,-sy,sz),(sx,sy,sz),(-sx,sy,sz)]
        mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);mesh.update()
        o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o);o.location=xyz(p)
    if bevel:
        mod=o.modifiers.new('Authored edge radius','BEVEL');mod.width=bevel;mod.segments=2;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
    # Architectural maps use metres, not the cube's default net unwrap.
    uv=o.data.uv_layers.active or o.data.uv_layers.new(name='Metres')
    for face in o.data.polygons:
        axis=max(range(3),key=lambda i:abs(face.normal[i]))
        for li in face.loop_indices:
            v=o.data.vertices[o.data.loops[li].vertex_index].co
            uv.data[li].uv=((v.y if axis==0 else v.x)*.35,(v.y if axis==2 else v.z)*.35)
    return finish(o,name,m,parent)
def link(name,a,b,r,m,parent=None,verts=12):
    a,b=Vector(xyz(a)),Vector(xyz(b));d=b-a;bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d.length,location=(a+b)*.5);o=bpy.context.object;o.rotation_quaternion=d.to_track_quat('Z','Y');o.rotation_mode='QUATERNION';o.rotation_quaternion=d.to_track_quat('Z','Y');return finish(o,name,m,parent)
def empty(name,p=(0,0,0),parent=None):
    o=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(o);o.location=xyz(p)
    if parent:o.parent=parent
    return o
def wheel(i,r,width,track,wb,rubber,alloy):
    p=((1 if i%2 else -1)*track,.41,wb if i<2 else -wb);root=empty('wheel_'+str(i),p);spin=empty('wheel_'+str(i)+'_spin',parent=root)
    # Child coordinates are already local because the root carries the hub.
    bpy.ops.mesh.primitive_torus_add(major_segments=48,minor_segments=12,location=(0,0,0),major_radius=r-width*.72,minor_radius=width*.72);o=bpy.context.object;o.rotation_euler[1]=math.pi/2;o.scale.z=1.0;finish(o,'all-terrain carcass',rubber,spin)
    link('alloy barrel',(-width*.65,0,0),(width*.65,0,0),r*.57,alloy,spin,32)
    for side in (-1,1):
        for k in range(8):
            a=k*math.tau/8;link('split spoke',(side*width*.72,0,0),(side*width*.72,math.sin(a)*r*.52,math.cos(a)*r*.52),.024,alloy,spin,8)
    for k in range(40):
        a=k*math.tau/40
        for side in (-1,1):
            o=box('directional tread',(side*width*.48,math.sin(a)*(r-.008),math.cos(a)*(r-.008)),(width*.82,.052,.10),rubber,spin);o.rotation_euler[0]=a
    return root
def export(key):
    out=OUT/key;out.mkdir(parents=True,exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(out/'model.glb'),export_format='GLB',export_yup=True,export_apply=True,export_animations=False)
    print('AUTHORED',key)
def combine_static():
    # Batch static pieces by material without destroying named moving pivots.
    groups={}
    for o in list(bpy.context.scene.objects):
        if o.type=='MESH':groups.setdefault(o.data.materials[0].name,[]).append(o)
    for name,items in groups.items():
        bpy.ops.object.select_all(action='DESELECT')
        for o in items:o.select_set(True)
        bpy.context.view_layer.objects.active=items[0];bpy.ops.object.join();items[0].name=name+' authored batch'
clear();rubber=mat('warm charcoal tyre',(.025,.028,.029));alloy=mat('brushed alloy',(.45,.48,.5),.85,.24);paint=mat('Cinder ochre enamel',(.62,.19,.035),.45,.27);steel=mat('satin chassis',(.055,.064,.07),.65,.4);seat=mat('woven seat',(.045,.05,.048),0,.9)
for i in range(4):wheel(i,.49,.17,1.08,1.35,rubber,alloy)
export('safari-running-gear')
clear()
for i in range(4):wheel(i,.54,.20,1.50,1.35,rubber,alloy)
box('undercarriage',(0,.62,0),(1.45,.18,2.8),steel,bevel=.04);box('front cowl',(0,1.0,1.02),(1.4,.34,.55),paint,bevel=.08);box('rear power cover',(0,.95,-.97),(1.45,.42,.8),paint,bevel=.06)
for side in (-1,1):
    x=side*.67
    pts=[(x,.69,-1.3),(x,1.77,-.65),(x,1.78,.4),(x,.75,1.15)]
    for j in range(3):link('roll cage rail',pts[j],pts[j+1],.045,steel)
    link('door bar',(x,.76,-.75),(x,1.25,.6),.036,steel)
    box('side sill',(x,.76,0),(.1,.32,1.2),paint,bevel=.025)
    for end in (-1,1):link('wishbone',(side*.55,.62,end*1.25),(side*1.5,.41,end*1.35),.026,steel)
for z in (-.65,.4):link('cage crossmember',(-.67,1.78,z),(.67,1.78,z),.045,steel)
for side in (-1,1):
    box('bucket seat cushion',(side*.37,.88,-.18),(.54,.15,.6),seat,bevel=.04);box('bucket seat back',(side*.37,1.17,-.49),(.54,.7,.13),seat,bevel=.05)
    box('four point harness',(side*.37,1.22,-.405),(.08,.56,.022),paint)
box('dashboard',(0,1.2,.5),(1.22,.2,.18),steel,bevel=.035);link('steering column',(-.37,1.1,.4),(-.37,1.27,.13),.025,steel)
export('buggy')
clear();brick=[mat('warm brick',(.24,.11,.065)),mat('sandstone',(.37,.30,.21)),mat('warehouse painted',(.16,.21,.22))];trim=mat('cream facade trim',(.60,.57,.48));glass=mat('blue black windows',(.035,.07,.09),.45,.18);asphalt=mat('road markings',(.63,.60,.44));wood=mat('planter wood',(.11,.075,.042));leaf=mat('street tree leaves',(.065,.15,.045),rough=.96);bark=mat('tree bark',(.11,.07,.04));metal=mat('street furniture',(.045,.055,.06),.6)
buildings=[(-13,49,18,18,14.4),(-13,71,18,22,20.8),(-13,94,18,16,11.2),(14,52,16,24,10.8),(14,84,16,36,17.6),(-55,49,17,24,18),(-55,85,17,38,25),(55,52,17,30,21),(55,93,17,28,14),(-16,142,38,24,23),(32,145,28,30,31)]
for j,(x,z,w,d,h) in enumerate(buildings):
    box('building '+str(j),(x,.16+h/2,z),(w,h,d),brick[j%3],bevel=.08)
    for y in [3.4+k*3.5 for k in range(int(h/3.5))]:
        for s in (-1,1):
            for zz in range(int(-d/2)+2,int(d/2),3):box('recessed glazing',(x+s*(w/2+.012),y,z+zz),(.04,1.9,1.6),glass)
            box('stone string course',(x,y-1.2,z+s*(d/2+.025)),(w+.12,.18,.12),trim)
            for zz in range(int(-d/2)+2,int(d/2),3):
                for offset in (-.94,.94):box('window sill lintel',(x+s*(w/2+.05),y+offset,z+zz),(.16,.09,1.8),trim)
    box('roof coping',(x,h+.22,z),(w+.28,.22,d+.28),trim)
    for s in (-1,1):
        box('street awning',(x+s*(w/2+.35),2.9,z),(.9,.14,d*.7),brick[(j+1)%3])
        for zz in range(int(-d/2)+2,int(d/2)-1,4):
            box('shopfront glazing',(x+s*(w/2+.03),1.45,z+zz),(.06,2.35,3.1),glass)
            box('shopfront frame',(x+s*(w/2+.09),1.45,z+zz-1.62),(.12,2.5,.12),trim)
        box('storefront signboard',(x+s*(w/2+.10),3.6,z),(.18,.80,min(d-2,11)),metal)
        bpy.ops.object.text_add(location=xyz((x+s*(w/2+.205),3.48,z-4)))
        text=bpy.context.object;text.data.body=['MERCER / COFFEE','MERCER / LOFTS','NORTH / SUPPLY','CINDER / MOTOR WORKS','BAY / WAREHOUSE','WEST / STUDIOS','MERCER / HOUSE','EAST / HOUSE','DOCK / STORAGE','NORTH / MILL','THE / EXCHANGE'][j]
        text.data.size=.42;text.data.extrude=.002;text.rotation_euler=(math.pi/2,0,-s*math.pi/2);text.data.materials.append(trim);text.name='storefront lettering';bpy.context.view_layer.objects.active=text;bpy.ops.object.convert(target='MESH')
for x in (-33,33):
    for z in range(20,123,8):box('lane dash',(x,.018,z),(.13,.018,3.5),asphalt)
for z in (22,116):
    for x in range(-37,38,2):box('crosswalk',(x,.022,z),(1.1,.02,5),asphalt)
for x in (-23.7,23.7,-44.7,44.7):
    for z in (42,60,78,96):
        box('tree planter',(x,.44,z),(2,.55,2),wood,bevel=.06);link('street trunk',(x,.4,z),(x,3.1,z),.14,bark)
        rng=random.Random(int(x*100+z*7));vertices=[];faces=[];shades=[]
        for k in range(14):
            a=k*2.39996;radius=.65+1.05*rng.random();cx=x+math.sin(a)*radius;cz=z+math.cos(a)*radius;cy=3.5+1.7*rng.random();link('street branch',(x,2.5,z),(cx,cy,cz),.045,bark,verts=8)
            for j in range(24):
                centre=Vector((cx+rng.uniform(-.65,.65),cy+rng.uniform(-.55,.55),cz+rng.uniform(-.65,.65)));angle=rng.random()*math.tau;along=Vector((rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(-1,1))).normalized()*.28;across=along.cross(Vector((rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(-1,1)))).normalized()*.12;n=len(vertices)
                for point in (centre+Vector((0,.018,0)),centre+along,centre+across,centre-along*.8,centre-across):vertices.append(xyz(point));shades.append(.68+.32*rng.random())
                faces.extend([(n,n+1,n+2),(n,n+2,n+3),(n,n+3,n+4),(n,n+4,n+1)])
        mesh=bpy.data.meshes.new('authored lobed foliage');mesh.from_pydata(vertices,[],faces);mesh.update();col=mesh.color_attributes.new(name='COLOR_0',type='FLOAT_COLOR',domain='POINT')
        for j,value in enumerate(shades):col.data[j].color=(value,value,value,1)
        o=bpy.data.objects.new('street foliage',mesh);bpy.context.collection.objects.link(o);o.data.materials.append(leaf)
for x in (-40,40):
    for z in (29,61,93,121):link('street lamp',(x,0,z),(x,6,z),.065,metal);box('lamp head',(x,6,z),(.6,.15,.8),trim)
combine_static();export('city-kit')
clear();orange=mat('painted safety amber',(.78,.29,.025));black=mat('gantry graphite',(.07,.085,.09),.65)
for z in (131,143):
    for x in (17,33):link('wind post',(x,0,z),(x,3.8,z),.10,black)
    link('wind crossbeam',(17,3.8,z),(33,3.8,z),.10,orange)
for x in (17,33):link('wind roof rail',(x,3.8,131),(x,3.8,143),.10,black)
combine_static();export('playground-kit')
