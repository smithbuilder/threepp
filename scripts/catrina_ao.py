"""Geometry-bound local cavity shading using the existing CPU visibility baker.

Static body, wheel assemblies and opening lids are baked separately. This avoids
painting the closed body/lid shadow onto moving suspension, wheels or open bays.
"""
from pathlib import Path
import copy,hashlib,json,struct,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/la-catrina/ao'
CACHE=ROOT/'docs/la-catrina/bakes/vertex-ao.npz'
PARTITION_VERSION=2

def accessor(doc,blob,index):
    a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
    width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
    return np.frombuffer(blob,dtype={5126:'<f4',5125:'<u4'}[a['componentType']],count=a['count']*width,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,width)

def geometry_signature(doc,blob):
    h=hashlib.sha256()
    h.update(json.dumps(doc['nodes'],sort_keys=True,separators=(',',':')).encode())
    for mesh in doc['meshes']:
        h.update(mesh['name'].encode())
        for p in mesh['primitives']:
            for k in ('POSITION','NORMAL'):h.update(accessor(doc,blob,p['attributes'][k]).tobytes())
            h.update(accessor(doc,blob,p['indices']).tobytes())
            m=doc['materials'][p['material']]
            h.update(json.dumps([m.get('alphaMode','OPAQUE'),m.get('emissiveFactor',[])],separators=(',',':')).encode())
    return h.hexdigest()

def add_accessor(doc,blob,values):
    values=np.asarray(values,dtype='<f4');blob.extend(b'\0'*(-len(blob)%4))
    doc['bufferViews'].append({'buffer':0,'byteOffset':len(blob),'byteLength':values.nbytes})
    blob.extend(values.tobytes())
    doc['accessors'].append({'bufferView':len(doc['bufferViews'])-1,'componentType':5126,'type':'VEC3','count':len(values),'min':values.min(0).tolist(),'max':values.max(0).tolist()})
    return len(doc['accessors'])-1

def apply_cache(doc,blob,root=ROOT):
    digest=geometry_signature(doc,blob);path=Path(root)/'docs/la-catrina/bakes/vertex-ao.npz'
    info={'geometrySha256':digest,'bakedCavityShading':False}
    if not path.exists():return info
    with np.load(path,allow_pickle=False) as cache:
        if 'partitionVersion' not in cache or int(cache['partitionVersion'])!=PARTITION_VERSION:return info
        if str(cache['geometrySha256'].item())!=digest:return info
        count=0
        for i,mesh in enumerate(doc['meshes']):
            if 'mesh_'+str(i) not in cache:continue
            values=cache['mesh_'+str(i)];p=mesh['primitives'][0]
            assert len(values)==doc['accessors'][p['attributes']['POSITION']]['count']
            assert np.isfinite(values).all() and values.min()>=0 and values.max()<=1
            colors=np.repeat((.45+.55*values)[:,None],3,axis=1)
            p['attributes']['COLOR_0']=add_accessor(doc,blob,colors);count+=1
    info.update(bakedCavityShading=True,cavityReceiverMeshes=count,bakeCacheSha256=hashlib.sha256(path.read_bytes()).hexdigest())
    return info

def read_glb(path):
    raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0]
    return json.loads(raw[20:20+n]),bytearray(raw[28+n:])

def write_glb(path,doc,blob):
    blob.extend(b'\0'*(-len(blob)%4));doc['buffers'][0]['byteLength']=len(blob)
    js=json.dumps(doc,separators=(',',':')).encode();js+=b' '*(-len(js)%4)
    path.write_bytes(struct.pack('<III',0x46546c67,2,28+len(js)+len(blob))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(blob),0x004e4942)+blob)

def prepare():
    OUT.mkdir(parents=True,exist_ok=True)
    model=ROOT/'showcase/assets/la-catrina.glb';doc,blob=read_glb(model)
    parents={c:i for i,n in enumerate(doc['nodes']) for c in n.get('children',[])}
    def origin(i):
        node=doc['nodes'][i];assert not node.get('rotation') and not node.get('scale')
        return np.array(node.get('translation',[0,0,0]))+(origin(parents[i]) if i in parents else 0)
    def group(i):
        n=doc['nodes'][i]['name']
        # Brake faces stay live-lit in wheel-off service views. Their removed
        # tyres/spokes must not leave a permanent baked shadow on the drums.
        if n.startswith('brake_'):return 'moving'
        if 'mesh' in doc['nodes'][i]:
            parts=doc['meshes'][doc['nodes'][i]['mesh']]['extras']['sourceParts']
            if parts and all(p.startswith(('wheel.brake_backplate','wheel.backplate_fastener')) for p in parts):return 'moving'
        if n in ('hood_hinge','trunk_hinge'):return 'lids'
        if n in ('wheel_0','wheel_1','wheel_2','wheel_3'):return 'wheels'
        if i in parents and doc['nodes'][parents[i]]['name']=='body':
            return 'body' if 'mesh' in doc['nodes'][i] else 'moving'
        return group(parents[i]) if i in parents else 'body'
    groups={name:[] for name in ('body','wheels','lids')};mesh_nodes={}
    for i,node in enumerate(doc['nodes']):
        if 'mesh' not in node:continue
        g=group(i)
        if g in groups:groups[g].append(node['mesh']);mesh_nodes[node['mesh']]=i
    meta={'geometrySha256':geometry_signature(doc,blob),'partitionVersion':PARTITION_VERSION,'sourceSha256':hashlib.sha256(model.read_bytes()).hexdigest(),'groups':groups,'partitionScope':'Static body, four wheel assemblies and opening lids are isolated occlusion sets; suspension and brake assemblies receive no baked shading, preserving wheel-off service views.'}
    for name,indices in groups.items():
        flat=copy.deepcopy(doc);data=bytearray(blob);flat['meshes']=[];flat['nodes']=[];flat.pop('animations',None)
        for old in indices:
            mesh=copy.deepcopy(doc['meshes'][old]);p=mesh['primitives'][0]
            points=accessor(doc,blob,p['attributes']['POSITION'])+origin(mesh_nodes[old])
            p['attributes']['POSITION']=add_accessor(flat,data,points);p['attributes'].pop('COLOR_0',None)
            flat['nodes'].append({'name':mesh['name'],'mesh':len(flat['meshes'])});flat['meshes'].append(mesh)
        flat['scene']=0;flat['scenes']=[{'nodes':list(range(len(flat['nodes'])))}]
        write_glb(OUT/(name+'.glb'),flat,data)
    (OUT/'source.json').write_text(json.dumps(meta,indent=2)+'\n')
    print('Prepared three independent CPU-only cavity groups:',meta['geometrySha256'])

def finish():
    meta=json.loads((OUT/'source.json').read_text());doc,blob=read_glb(ROOT/'showcase/assets/la-catrina.glb')
    assert geometry_signature(doc,blob)==meta['geometrySha256'],'Geometry changed during bake'
    cache={'geometrySha256':np.array(meta['geometrySha256']),'partitionVersion':np.array(PARTITION_VERSION)};reports={}
    for name,indices in meta['groups'].items():
        report=json.loads((OUT/(name+'.json')).read_text())
        assert report['sourceSha256']==hashlib.sha256((OUT/(name+'.glb')).read_bytes()).hexdigest()
        assert report['graphicsContext'] is False
        values=np.fromfile(OUT/report['valuesFile'],dtype='<f4')
        for mesh in report['meshes']:
            if not mesh['receiver']:continue
            start=mesh['floatOffset'];cache['mesh_'+str(indices[mesh['mesh']])]=values[start:start+mesh['vertexCount']]
        reports[name]={k:report[k] for k in ('samples','maxDistanceMetres','originBiasMetres','hemisphere','occluderTriangles','receiverVertices','rayQueries','bakeSeconds','peakWorkingSetBytes','graphicsContext')}
    CACHE.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(CACHE,**cache)
    meta.update(cacheSha256=hashlib.sha256(CACHE.read_bytes()).hexdigest(),reports=reports,colorFormula='0.45 + 0.55 * hemisphereVisibility',helperSource='showcase/safari_ao_bake.cpp')
    CACHE.with_suffix('.json').write_text(json.dumps(meta,indent=2)+'\n')
    print('Retained geometry-bound cavity cache:',meta['geometrySha256'])

if __name__=='__main__':
    {'prepare':prepare,'finish':finish}[sys.argv[1]]()
