"""Serialized portable asset checks, including dimensions and moving hierarchy."""
from pathlib import Path
import hashlib,io,json,struct
import numpy as np
from PIL import Image
from scipy.spatial.transform import Rotation

ROOT=Path(__file__).resolve().parents[1];path=ROOT/'showcase/assets/la-catrina.glb'
raw=path.read_bytes();magic,version,size=struct.unpack_from('<III',raw)
assert magic==0x46546c67 and version==2 and size==len(raw)
jlen,jtyp=struct.unpack_from('<II',raw,12);doc=json.loads(raw[20:20+jlen]);offset=20+jlen
blen,btyp=struct.unpack_from('<II',raw,offset);blob=raw[offset+8:offset+8+blen]
nodes=doc['nodes'];parents={c:i for i,n in enumerate(nodes) for c in n.get('children',[])};names={n['name']:i for i,n in enumerate(nodes)}
checks=[]
def check(name,passed,detail=None):
    checks.append({'check':name,'passed':bool(passed),'detail':detail})
    if not passed:print('FAIL',name,detail)
def array(index):
    a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
    return np.frombuffer(blob,dtype={5126:'<f4',5125:'<u4'}[a['componentType']],count=a['count']*width,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,width)
world_matrices={}
def world_matrix(i):
    if i not in world_matrices:
        n=nodes[i]
        if 'matrix' in n:local=np.asarray(n['matrix'],float).reshape(4,4).T
        else:
            local=np.eye(4);local[:3,:3]=Rotation.from_quat(n.get('rotation',[0,0,0,1])).as_matrix()@np.diag(n.get('scale',[1,1,1]));local[:3,3]=n.get('translation',[0,0,0])
        world_matrices[i]=world_matrix(parents[i])@local if i in parents else local
    return world_matrices[i]

def origin(i):return world_matrix(i)[:3,3]
def world_points(i,v):
    m=world_matrix(i);return v@m[:3,:3].T+m[:3,3]
def ancestor(i,p):
    while i in parents:
        if i==p:return True
        i=parents[i]
    return i==p
def points(parent=0,mat=None,part=None):
    out=[]
    for i,n in enumerate(nodes):
        if 'mesh' not in n or not ancestor(i,parent):continue
        mesh=doc['meshes'][n['mesh']]
        for p in mesh['primitives']:
            if mat and doc['materials'][p['material']]['name']!=mat:continue
            v=array(p['attributes']['POSITION'])
            if part:
                for r in mesh['extras']['sourcePartRanges']:
                    if r['name']==part:out.append(world_points(i,v[r['start']:r['start']+r['count']]))
            else:out.append(world_points(i,v))
    return np.concatenate(out) if out else np.empty((0,3))
def surface_samples(part_names,spacing=.020):
    """Sample triangle interiors as well as corners, catching a broad panel
    through a tyre even when every original box vertex lies outside it."""
    samples=[]
    for i,node in enumerate(nodes):
        if 'mesh' not in node:continue
        mesh=doc['meshes'][node['mesh']];primitive=mesh['primitives'][0]
        vertices=world_points(i,array(primitive['attributes']['POSITION']));faces=array(primitive['indices']).reshape(-1,3)
        for part in mesh['extras']['sourcePartRanges']:
            if part['name'] not in part_names:continue
            start=part['start'];end=start+part['count'];tri=faces[((faces>=start)&(faces<end)).all(1)]
            for face in tri:
                a,b,c=vertices[face];n=max(1,int(np.ceil(max(np.linalg.norm(b-a),np.linalg.norm(c-a),np.linalg.norm(c-b))/spacing)))
                u,v=np.meshgrid(np.arange(n+1)/n,np.arange(n+1)/n);mask=u+v<=1.000001
                samples.append(a+u[mask,None]*(b-a)+v[mask,None]*(c-a))
    return np.concatenate(samples)
rig=[n['name'] for n in nodes if 'mesh' not in n]
check('rig names unique',len(rig)==len(set(rig)))
check('hierarchy connected exactly once',len(parents)==len(nodes)-1)
finite=indexok=normalok=winding=True;triangles=0;badwinding=[]
for mesh in doc['meshes']:
    for p in mesh['primitives']:
        v=array(p['attributes']['POSITION']);n=array(p['attributes']['NORMAL']);f=array(p['indices']).reshape(-1,3);triangles+=len(f)
        finite &= bool(np.isfinite(v).all() and np.isfinite(n).all())
        indexok &= bool(f.min()>=0 and f.max()<len(v))
        normalok &= bool(np.max(abs(np.linalg.norm(n,axis=1)-1))<.002)
        cross=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]])
        bad=int(np.sum((cross*n[f].mean(1)).sum(1)<-1e-8));winding &= bad==0
        if bad:badwinding.append({'mesh':mesh['name'],'count':bad})
check('all attributes finite',finite);check('indices in range',indexok);check('unit vertex normals',normalok);check('winding follows normals',winding,badwinding)
# Correct winding against a supplied normal cannot detect a whole surface whose
# intended exterior faces inward. Check these actual outward-facing parts too.
for part in ('cab.C_pillar','front.fender_roll','rear.fender_roll'):
    facing=[]
    for i,node in enumerate(nodes):
        if 'mesh' not in node:continue
        mesh=doc['meshes'][node['mesh']];primitive=mesh['primitives'][0]
        for r in mesh['extras']['sourcePartRanges']:
            if r['name']!=part:continue
            sl=slice(r['start'],r['start']+r['count'])
            v=world_points(i,array(primitive['attributes']['POSITION'])[sl])
            n=array(primitive['attributes']['NORMAL'])[sl]
            radial=n[:,0]*np.sign(v[:,0])
            if 'fender_roll' in part:radial+=n[:,2]*np.sign(v[:,2])
            facing.extend(radial.tolist())
    check(part+' actual exterior faces outward',bool(facing) and min(facing)>.1,min(facing) if facing else None)
reflector=points(part='front.headlamp_reflector');backing=points(part='front.headlamp_dark')
check('headlamp reflectors not occluded by opaque backing caps',len(reflector)>0 and len(backing)>0 and reflector[:,2].min()>backing[:,2].max()+.001,{'reflectorMinimumZ':float(reflector[:,2].min()),'backingMaximumZ':float(backing[:,2].max())})
for top_part in ('body.hood','body.trunk','cab.lace_roof'):
    top_normals=[];top_positions=[]
    for i,node in enumerate(nodes):
        if 'mesh' not in node:continue
        mesh=doc['meshes'][node['mesh']]
        for r in mesh['extras']['sourcePartRanges']:
            if r['name']==top_part:
                sl=slice(r['start'],r['start']+r['count'])
                top_normals.append(array(mesh['primitives'][0]['attributes']['NORMAL'])[sl])
                top_positions.append(world_points(i,array(mesh['primitives'][0]['attributes']['POSITION'])[sl]))
    ny=np.concatenate(top_normals)[:,1]
    v=np.concatenate(top_positions)
    # The reference-measured end face is about half a lamp diameter deep.
    # Its last200mm now rolls downward, up to about41 degrees. Only this end
    # band may have steep normals; the remaining painted field stays shallow.
    field=np.ones(len(v),dtype=bool)
    if top_part=='body.hood':field=v[:,2]<v[:,2].max()-.21
    elif top_part=='body.trunk':field=v[:,2]>v[:,2].min()+.21
    minimum=.90 if top_part=='cab.lace_roof' else .75
    check(top_part+' curved skin faces sky with outward normals',ny.min()>minimum and ny[field].min()>.90 and ny[field].mean()>.98,{'minimumY':float(ny.min()),'fieldMinimumY':float(ny[field].min()),'fieldMeanY':float(ny[field].mean()),'steepEndBandMetres':0 if top_part=='cab.lace_roof' else .21})
for top_part in ('body.hood','body.trunk','cab.lace_roof'):
    mapped=[]
    for mesh in doc['meshes']:
        for r in mesh['extras']['sourcePartRanges']:
            if r['name']==top_part:
                primitive=mesh['primitives'][0];uv=array(primitive['attributes']['TEXCOORD_0'])[r['start']:r['start']+r['count']]
                material=doc['materials'][primitive['material']]
                texture_index=material['pbrMetallicRoughness'].get('baseColorTexture',{}).get('index')
                expected={'cab.lace_roof':'reference_roof_lace','body.hood':'reference_hood_lace','body.trunk':'reference_deck_lace'}[top_part]
                mapped.append(np.ptp(uv,axis=0).min()>.99 and texture_index is not None and doc['images'][doc['textures'][texture_index]['source']]['name']==expected)
    check(top_part+' spans complete lace texture',bool(mapped) and all(mapped))
liner=points(part='body.trunk_rear_liner');rear_header=points(part='rear.painted_header')
liner_margin=float(liner[:,2].min()-rear_header[:,2].max()) if len(liner) and len(rear_header) else -1
check('trunk rear liner remains inside painted rear header',liner_margin>=.010,{'inboardMarginMetres':liner_margin})
for name,axis,sign in (('front.painted_header',2,1),('rear.painted_header',2,-1)):
    ns=[]
    for mesh in doc['meshes']:
        for r in mesh['extras']['sourcePartRanges']:
            if r['name']==name:ns.append(array(mesh['primitives'][0]['attributes']['NORMAL'])[r['start']:r['start']+r['count']])
    # Formed header returns now curve through the fender shoulder; they must
    # still face outward within26 degrees, rather than being perfectly planar.
    facing=float((np.concatenate(ns)[:,axis]*sign).min()) if ns else -1
    check(name+' closes curved deck edge facing outward',facing>.90,facing)
# Refined source retains the same native resolution, shadow and process caps.
check('bounded native mesh budget',triangles<750000 and len(doc['meshes'])<250,{'triangles':triangles,'draws':len(doc['meshes'])})
for name in ('rubber','ivory_whitewall','plum_vinyl','clear_tinted_glass','coil_candy_red','chassis_graphite','hardware_black_powdercoat'):
    values=[m['pbrMetallicRoughness'].get('metallicFactor',1) for m in doc['materials'] if m['name']=='catrina.'+name]
    check(name+' has dielectric coating/material response',bool(values) and max(values)<.001,values)
chrome_values=[m['pbrMetallicRoughness'].get('metallicFactor',0) for m in doc['materials'] if m['name']=='catrina.polished_chrome']
check('polished chrome remains metallic',bool(chrome_values) and min(chrome_values)>.9,chrome_values)
for i in range(4):
    name='wheel_'+str(i);expected=np.array([(-1 if i%2==0 else 1)*(.765 if i<2 else .755),.2891,1.5113 if i<2 else -1.5113])
    check(name+' metric hub',np.linalg.norm(origin(names[name])-expected)<1e-6)
    check(name+' steering and spin independent',parents[names[name+'_spin']]==names[name+'_steer'] and parents[names[name+'_steer']]==names[name])
    pp=points(names[name],mat='catrina.rubber')-expected
    check(name+' exact narrow tyre',abs(np.ptp(pp[:,0])-.155)<1e-5 and abs(np.ptp(pp[:,1])-.5782)<1e-5)
    check(name+' grounded tread',abs(pp[:,1].min()+.2891)<1e-6)
    rod=names['hydraulic_'+str(i)+'_rod'];hyd=names['hydraulic_'+str(i)]
    check(name+' separate piston with engaged rest rod',parents[rod]==hyd and abs(origin(rod)[1]-.55)<1e-6 and abs(origin(hyd)[1]-.86)<1e-6)
    coil=names['coil_'+str(i)];check(name+' separate spring',parents[coil]==names['body'])
for i in range(2):
    for upper in (False,True):
        nm='front_'+str(i)+('_upper' if upper else '_lower');n=nodes[names[nm]];a=origin(names[nm]);b=np.array(n['extras']['end'])
        check(nm+' fixed .535m span',abs(np.linalg.norm(b-a)-.535)<1e-6)
check('rear axle rigid independent group','rear_axle' in names and 'rear_upper' in names and 'rear_panhard' in names)
allp=points();lo=allp.min(0);hi=allp.max(0)
check('reference length within 10mm',abs(hi[2]-lo[2]-5.33)<.01,float(hi[2]-lo[2]))
check('asymmetric overhangs align with 190mm rearward hull offset',abs((hi[2]+lo[2])*.5+.19)<.01,{'envelopeCenterZ':float((hi[2]+lo[2])*.5),'physicsHullOffsetZ':-.19})
check('hardtop height in reference proportion',1.29<hi[1]<1.34,float(hi[1]))
check('no parts below contact plane',lo[1]>-.00001,float(lo[1]))
side=points(part='body.door');check('two metre side body',abs(np.ptp(side[:,0])-2.02)<.01,float(np.ptp(side[:,0])))
spears=points(part='trim.side_spear');intersections=0
for z,r,skirted in ((1.5113,.315,False),(-1.5113,.335,True)):
    dz=spears[:,2]-z
    # The rear opening is a low fender skirt, not a circular front arch.
    aperture=.2891+(.170*np.sqrt(np.maximum(0,1-(dz/r)**4)) if skirted else np.sqrt(np.maximum(0,r*r-dz**2)))
    inside=(abs(dz)<r)&(spears[:,1]<aperture-.003)
    intersections+=int(inside.sum())
check('side mouldings stop outside wheel apertures',intersections==0,intersections)
floor_parts={'body.cabin_floor','body.rear_cabin_tunnel','body.trunk_center_floor','body.trunk_aft_floor','body.rear_bulkhead'}
equipment_parts={'hydraulic.equipment_rack','hydraulic.battery','hydraulic.battery_lid'}
for group,part_names in (('floor and rear bulkhead',floor_parts),('trunk rack and battery cases',equipment_parts)):
    samples=surface_samples(part_names);hits=0
    for i in range(4):
        hub=np.array([(-1 if i%2==0 else 1)*(.765 if i<2 else .755),.2891,1.5113 if i<2 else -1.5113])
        delta=samples-hub
        inside=(abs(delta[:,0])<.0775+.012)&(np.linalg.norm(delta[:,1:],axis=1)<.2891+.012)
        hits+=int(inside.sum())
    check(group+' clears rest tyre cylinders with 12mm allowance',hits==0,{'surfaceSamples':len(samples),'maximumTriangleSampleSpacing':.020,'insideSamples':hits})
    # Conservative bounds derived from all720 recorded native-motion rear
    # poses, expanded30mm around the tyre footprint at floor height.
    envelope=(abs(samples[:,0])>.566515-.030)&(abs(samples[:,0])<1.06)&(samples[:,2]>-1.8210-.030)&(samples[:,2]<-1.2165+.030)&(samples[:,1]>.220)&(samples[:,1]<.360)
    check(group+' clears observed rear-motion floor footprint',not envelope.any(),{'insideSamples':int(envelope.sum()),'scope':'720 recorded native poses; y .25..33m with 30mm expansion, not exhaustive suspension sweep'})
def part_count(name):return sum(r['name']==name for m in doc['meshes'] for r in m['extras']['sourcePartRanges'])
check('four headlight reflector surfaces',part_count('front.headlamp_reflector')==4)
check('six tail lens surfaces',part_count('rear.tail_lens')==6)
check('two opening service clips',{a['name'] for a in doc['animations']}=={'hood_open','trunk_open'})
for im in doc['images']:
    v=doc['bufferViews'][im['bufferView']];img=Image.open(io.BytesIO(blob[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]))
    check(im['name']+' obeys 1K texture budget',max(img.size)<=1024,list(img.size))
manifest=json.loads(path.with_suffix('.json').read_text())
check('manifest exact content hash',hashlib.sha256(raw).hexdigest()==manifest['sha256'])
check('manifest bounds include complete parent transforms',np.allclose(manifest['bounds']['min'],lo,atol=1e-5,rtol=0) and np.allclose(manifest['bounds']['max'],hi,atol=1e-5,rtol=0),{'actualMinimum':lo.tolist(),'actualMaximum':hi.tolist()})
if manifest.get('bakedCavityShading'):
    from catrina_ao import geometry_signature
    cache_path=ROOT/'docs/la-catrina/bakes/vertex-ao.npz'
    check('cavity cache matches exact geometry and retained source',geometry_signature(doc,blob)==manifest['geometrySha256'] and hashlib.sha256(cache_path.read_bytes()).hexdigest()==manifest['bakeCacheSha256'])
    colors=[array(p['attributes']['COLOR_0']) for m in doc['meshes'] for p in m['primitives'] if 'COLOR_0' in p['attributes']]
    check('cavity shading stays finite and bounded',len(colors)==manifest['cavityReceiverMeshes'] and all(np.isfinite(c).all() and c.min()>=.44999 and c.max()<=1.00001 for c in colors),{'receiverMeshes':len(colors),'minimum':min(float(c.min()) for c in colors),'maximum':max(float(c.max()) for c in colors)})
lib=ROOT/'asset-library/models/la-catrina'
check('portable library exact mirror',(lib/'la-catrina.glb').read_bytes()==raw)
result={'status':'PASS' if all(c['passed'] for c in checks) else 'FAIL','passed':sum(c['passed'] for c in checks),'checks':checks,'assetSha256':manifest['sha256'],'bounds':{'min':lo.tolist(),'max':hi.tolist()}}
out=ROOT/'build/la-catrina';out.mkdir(parents=True,exist_ok=True);(out/'asset-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'passed':result['passed'],'total':len(checks),'triangles':triangles,'draws':len(doc['meshes'])},indent=2))
raise SystemExit(0 if result['status']=='PASS' else 1)
