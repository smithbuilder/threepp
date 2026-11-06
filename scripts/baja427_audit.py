"""CPU-only checks of the actual serialized Baja427 GLB; no renderer/context."""
from pathlib import Path
import io,json,struct,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'showcase/assets/baja-427.glb'
def audit():
    raw=P.read_bytes();assert struct.unpack_from('<III',raw)==(0x46546c67,2,len(raw))
    n,k=struct.unpack_from('<II',raw,12);assert k==0x4e4f534a;d=json.loads(raw[20:20+n]);bn,bk=struct.unpack_from('<II',raw,20+n);assert bk==0x004e4942
    binary=raw[28+n:];assert len(binary)==bn
    def acc(i):
        a=d['accessors'][i];v=d['bufferViews'][a['bufferView']];typ={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];size={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
        offset=v.get('byteOffset',0)+a.get('byteOffset',0);arr=np.frombuffer(binary,dtype=typ,count=a['count']*size,offset=offset).reshape(-1,size);assert np.isfinite(arr).all();return arr
    parents={}
    for i,node in enumerate(d['nodes']):
        for c in node.get('children',[]):assert c not in parents;parents[c]=i
    names={n['name']:i for i,n in enumerate(d['nodes']) if 'mesh' not in n}
    assert len(names)==sum('mesh' not in n for n in d['nodes']),'Duplicate rig group names'
    def transform(i):
        node=d['nodes'][i];q=node.get('rotation',[0,0,0,1]);x,y,z,w=q;R=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]]);a=np.eye(4);a[:3,:3]=R@np.diag(node.get('scale',[1,1,1]));a[:3,3]=node.get('translation',[0,0,0]);return transform(parents[i])@a if i in parents else a
    triangle_count=0;vertex_count=0;world=[];min_area=1e9;winding_bad=[];ranges=[];ground={}
    for i,node in enumerate(d['nodes']):
        if 'mesh' not in node:continue
        T=transform(i)
        for prim in d['meshes'][node['mesh']]['primitives']:
            p=acc(prim['attributes']['POSITION']);nn=acc(prim['attributes']['NORMAL']);uv=acc(prim['attributes']['TEXCOORD_0']);f=acc(prim['indices']).reshape(-1,3).astype(int)
            assert f.min()>=0 and f.max()<len(p);assert len(p)==len(nn)==len(uv);assert np.max(abs(np.linalg.norm(nn,axis=1)-1))<1e-4
            fn=np.cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]]);areas=np.linalg.norm(fn,axis=1)/2;assert areas.min()>1e-11;min_area=min(min_area,float(areas.min()))
            dot=(fn*nn[f].mean(1)).sum(1);bad=int((dot < -1e-9).sum())
            if bad:winding_bad.append({'mesh':node['name'],'backwardFaces':bad,'triangles':len(f)})
            points=p@T[:3,:3].T+T[:3,3];world.append(points);vertex_count+=len(p);triangle_count+=len(f)
            ranges.append((node['name'],points.min(0).tolist(),points.max(0).tolist()))
            if node['name'].startswith('wheel.'):
                par=i
                while par in parents and not d['nodes'][par]['name'].endswith('.steer'):par=parents[par]
                key=d['nodes'][par]['name'];old=ground.get(key,1e9);ground[key]=min(old,float(points[:,1].min()))
    for pos in ('FL','FR','RL','RR'):
        steer=names['wheel.'+pos+'.steer'];roll=names['wheel.'+pos+'.roll'];assert parents[roll]==steer
        assert d['nodes'][parents[steer]]['name']==('body' if pos.startswith('F') else 'rear_axle')
    assert d['nodes'][names['rear_axle']]['translation']==[0,.4,-1.59]
    assert d['nodes'][names['tailgate.hinge']]['translation']==[0,.71,-2.407]
    for name in ('spare.L.steer','spare.R.steer'):assert name in names
    assert d['nodes'][parents[names['cargo.spare_tiedowns']]]['name']=='body'
    # Regression for a real source bug: obtaining a basis must not normalise
    # the caller's segment in-place before its length is used to size a strap.
    from baja427_generate import basis
    segment=np.array([0,.53,.09]);before=segment.copy();B=basis(segment)
    assert np.array_equal(segment,before) and np.max(abs(B.T@B-np.eye(3)))<1e-10
    images=[]
    for image in d['images']:
        v=d['bufferViews'][image['bufferView']];data=binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
        with Image.open(io.BytesIO(data)) as im:im.load();images.append({'name':image['name'],'size':list(im.size)})
    points=np.concatenate(world);meta=json.loads(P.with_suffix('.json').read_text());digest=hashlib.sha256(raw).hexdigest()
    assert meta['sha256']==digest;assert meta['vertices']==vertex_count;assert meta['triangles']==triangle_count;assert meta['meshDraws']==len(d['meshes'])
    assert len(d['meshes'])<=150 and triangle_count<250000
    assert len(images)==meta['embeddedImages']==5 and all(abs(y+.07)<.004 for y in ground.values())
    report={'status':'pass' if not winding_bad else 'winding-warning','scope':'serialized GLB geometry, finite attributes, hierarchy, pivots, mesh budget, images and stationary tyre ground alignment','sha256':digest,'bytes':len(raw),'meshes':len(d['meshes']),'nodes':len(d['nodes']),'vertices':vertex_count,'triangles':triangle_count,'minimumTriangleArea':min_area,'worldBounds':{'min':points.min(0).tolist(),'max':points.max(0).tolist()},'wheelMinimumY':ground,'worldGroundOffset':.07,'images':images,'windingWarnings':winding_bad,'limits':['No renderer or audio device opened.','Does not validate dynamic suspension closure or steering/travel envelope.','No claim of user handling or visual acceptance.']}
    out=ROOT/'docs/baja-427/CPU-AUDIT.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':audit()
