"""Sample fixed enclosure triangles against actual native solved wheel poses.

This is a targeted regression check for the cabin/bay skins and wheel arches, not an
exhaustive continuous collision proof. Metal mechanisms are checked separately.
"""
from pathlib import Path
import argparse,csv,hashlib,json,struct
from functools import lru_cache
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.spatial import cKDTree

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--poses',required=True);args=parser.parse_args()
raw=(ROOT/'showcase/assets/la-catrina.glb').read_bytes();length=struct.unpack_from('<I',raw,12)[0]
doc=json.loads(raw[20:20+length]);blob=raw[28+length:]
nodes=doc['nodes'];parents={c:i for i,n in enumerate(nodes) for c in n.get('children',[])}
@lru_cache(None)
def world_matrix(i):
    node=nodes[i]
    if 'matrix' in node:
        matrix=np.asarray(node['matrix'],float).reshape(4,4,order='F')
    else:
        matrix=np.eye(4)
        matrix[:3,:3]=Rotation.from_quat(node.get('rotation',[0,0,0,1])).as_matrix()*np.asarray(node.get('scale',[1,1,1]))
        matrix[:3,3]=node.get('translation',[0,0,0])
    return world_matrix(parents[i])@matrix if i in parents else matrix
def arr(i):
    a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];w={'SCALAR':1,'VEC3':3}[a['type']]
    return np.frombuffer(blob,dtype={5126:'<f4',5125:'<u4'}[a['componentType']],count=a['count']*w,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,w)
parts={'body.trunk_step','body.trunk_lining_insert','body.engine_wheelhouse','body.engine_ram_cover','body.engine_inner_fender','body.engine_lower_pan','body.radiator_support','hydraulic.rack_sill','hydraulic.rack_crossrail','interior.carpeted_sill','interior.front_kick_panel','interior.rear_quarter_liner','interior.floor_carpet','body.cabin_floor','body.rear_cabin_tunnel','body.rear_bulkhead','body.trunk_center_floor','body.trunk_aft_floor','body.trunk_inner_quarter','body.trunk_front_bulkhead','body.trunk_rear_liner','body.trunk_wheelhouse','body.trunk_ram_cover','hydraulic.equipment_rack','hydraulic.battery','hydraulic.battery_lid'}
parts.update({'body.quarter','body.door','body.fender','body.arch_return','body.deck_shoulder','trim.arch_lip'})
parts.update({'interior.upper_quarter_card','interior.forward_quarter_card','interior.upper_door_rail','interior.parcel_shelf','interior.upper_quarter_return'})
parts.update({'hydraulic.ram_fixed_pin','hydraulic.ram_pin_head','hydraulic.ram_spherical_inner_ball','hydraulic.ram_pin_spacer'})
parts.add('chassis.boxed_X_rail')
spacing=.025;allowance=.006;sampled={}
for i,node in enumerate(nodes):
    if 'mesh' not in node:continue
    mesh=doc['meshes'][node['mesh']];p=mesh['primitives'][0]
    matrix=world_matrix(i)
    vertices=arr(p['attributes']['POSITION'])@matrix[:3,:3].T+matrix[:3,3];faces=arr(p['indices']).reshape(-1,3)
    for part in mesh['extras']['sourcePartRanges']:
        if part['name'] not in parts and not part['name'].startswith(('body.arch_','body.wheel_well_','body.engine_ram_','body.trunk_ram_','body.trunk_frame_channel_','chassis.ram_','chassis.spring_pocket_')):continue
        start=part['start'];end=start+part['count'];tri=faces[((faces>=start)&(faces<end)).all(1)]
        for face in tri:
            a,b,c=vertices[face];steps=max(1,int(np.ceil(max(np.linalg.norm(b-a),np.linalg.norm(c-a),np.linalg.norm(c-b))/spacing)))
            u,v=np.meshgrid(np.arange(steps+1)/steps,np.arange(steps+1)/steps);mask=u+v<=1.000001
            sampled.setdefault(part['name'],[]).append(a+u[mask,None]*(b-a)+v[mask,None]*(c-a))
sampled={k:np.concatenate(v) for k,v in sampled.items()};assert sampled
rows=list(csv.DictReader(Path(args.poses).open(newline='')));assert len(rows)>=243*4
pose_count=len(rows)
unique={tuple(r[k] for k in ('wheel','x','y','z','qx','qy','qz','qw')):r for r in rows}
rows=list(unique.values())
trees={name:cKDTree(points) for name,points in sampled.items()}
hits={};minimum=10
for row in rows:
    center=np.array([float(row[k]) for k in ('x','y','z')]);rot=Rotation.from_quat([float(row[k]) for k in ('qx','qy','qz','qw')]).as_matrix()
    for name,points in sampled.items():
        near=points[trees[name].query_ball_point(center,.45)]
        if not len(near):continue
        local=(near-center)@rot
        axial=np.abs(local[:,0])-(.0775+allowance);radial=np.linalg.norm(local[:,1:],axis=1)-(.2891+allowance)
        inside=(axial<0)&(radial<0)
        minimum=min(minimum,float(np.max(np.c_[axial,radial],axis=1).min()))
        if inside.any():hits.setdefault(name,[]).append({'pose':int(row['pose']),'wheel':int(row['wheel']),'samples':int(inside.sum())})
result={'status':'FAIL' if hits else 'PASS','modelSha256':hashlib.sha256(raw).hexdigest(),'poseSource':str(Path(args.poses).resolve()),'wheelPoses':pose_count,'uniqueWheelTransforms':len(rows),'sampleSpacingMetres':spacing,'tyreAllowanceMetres':allowance,'sampledParts':{k:len(v) for k,v in sampled.items()},'minimumSignedCylinderMetric':minimum,'hits':hits,'scope':'Fixed body skins, arches, enclosures and rack surfaces versus243native articulation/steering poses; sampled triangles,6mm tyre allowance. Not exhaustive moving mechanism collision or continuous clearance.'}
output=ROOT/'build/la-catrina/enclosure-audit.json';output.parent.mkdir(parents=True,exist_ok=True)
output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('hits','sampledParts')},indent=2));print('Intersecting parts:',list(hits))
raise SystemExit(1 if hits else 0)
