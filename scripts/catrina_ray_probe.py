"""CPU surface identification for the fixed rear three-quarter review camera.

Static body geometry only; rig rotations are intentionally outside this tool.
"""
from pathlib import Path
import json,struct,sys,numpy as np
raw=(Path(__file__).resolve().parents[1]/'showcase/assets/la-catrina.glb').read_bytes()
n=struct.unpack_from('<I',raw,12)[0];d=json.loads(raw[20:20+n]);b=raw[28+n:]
parents={c:i for i,v in enumerate(d['nodes']) for c in v.get('children',[])}
def arr(j):
    a=d['accessors'][j];v=d['bufferViews'][a['bufferView']];w={'SCALAR':1,'VEC3':3}[a['type']]
    return np.frombuffer(b,dtype={5126:'<f4',5125:'<u4'}[a['componentType']],offset=v.get('byteOffset',0)+a.get('byteOffset',0),count=a['count']*w).reshape(-1,w)
def pos(i):return np.array(d['nodes'][i].get('translation',[0,0,0]))+(pos(parents[i]) if i in parents else 0)
eye=np.array([4.5,2.1,-5.8]);forward=np.array([0,.67,0])-eye;forward/=np.linalg.norm(forward)
right=np.cross(forward,[0,1,0]);right/=np.linalg.norm(right);up=np.cross(right,forward)
for coord in sys.argv[1:]:
    px,py=map(float,coord.split(','))
    ray=forward+right*((px/960*2-1)*1.6*np.tan(np.deg2rad(31/2)))+up*((1-py/600*2)*np.tan(np.deg2rad(31/2)))
    ray/=np.linalg.norm(ray);hits=[]
    for ni,node in enumerate(d['nodes']):
        if 'mesh' not in node:continue
        mesh=d['meshes'][node['mesh']];p=mesh['primitives'][0]
        verts=arr(p['attributes']['POSITION'])+pos(ni);f=arr(p['indices']).reshape(-1,3)
        a=verts[f[:,0]];e1=verts[f[:,1]]-a;e2=verts[f[:,2]]-a;h=np.cross(ray,e2)
        det=np.einsum('ij,ij->i',e1,h);valid=abs(det)>1e-8
        inv=np.divide(1,det,out=np.zeros_like(det),where=valid);s=eye-a
        u=inv*np.einsum('ij,ij->i',s,h);q=np.cross(s,e1);v=inv*np.dot(q,ray);t=inv*np.einsum('ij,ij->i',e2,q)
        idx=np.where(valid&(u>=0)&(v>=0)&(u+v<=1)&(t>0))[0]
        for j in idx:
            part=next((r['name'] for r in mesh['extras']['sourcePartRanges'] if r['start']<=f[j,0]<r['start']+r['count']),'?')
            norm=arr(p['attributes']['NORMAL'])[f[j]].mean(0)
            hits.append((float(t[j]),part,d['materials'][p['material']]['name'],(eye+ray*t[j]).round(4).tolist(),norm.round(3).tolist()))
    print(coord,sorted(hits)[:3])
