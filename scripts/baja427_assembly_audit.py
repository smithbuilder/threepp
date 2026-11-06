"""CPU assembly checks against exact vertex ranges in the serialized truck GLB.

The deterministic source rebuild identifies parts inside material batches; every
source vertex range is matched to the actual GLB before any fit checks. This is
a visual assembly/clearance audit, not a towing rating or manufacturing review.
"""
from pathlib import Path
import hashlib,json,struct
import numpy as np
import baja427_generate as g

ROOT=Path(__file__).resolve().parents[1]

def main():
    path=ROOT/'showcase/assets/baja-427.glb';raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0];d=json.loads(raw[20:20+n]);binary=raw[28+n:]
    def attr(i):
        a=d['accessors'][i];v=d['bufferViews'][a['bufferView']]
        return np.frombuffer(binary,'<f4',count=a['count']*3,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,3)
    parent={c:i for i,v in enumerate(d['nodes']) for c in v.get('children',[])}
    def transform(i):
        v=d['nodes'][i];x,y,z,w=v.get('rotation',[0,0,0,1]);r=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
        m=np.eye(4);m[:3,:3]=r@np.diag(v.get('scale',[1,1,1]));m[:3,3]=v.get('translation',[0,0,0]);return transform(parent[i])@m if i in parent else m
    g.make_textures();g.build_body();g.front_hardware();g.build_running_gear();g.cargo()
    batches={}
    for p in g.M.parts:batches.setdefault((p['parent'],p['mat'],p['name'].split('.')[0]),[]).append(p)
    assert len(batches)==len(d['meshes']);parts=[]
    for mi,((node,material,semantic),items) in enumerate(batches.items()):
        prim=d['meshes'][mi]['primitives'][0];assert prim['material']==material
        values=attr(prim['attributes']['POSITION']);offset=0;T=transform(node)
        for p in items:
            actual=values[offset:offset+len(p['p'])];assert np.array_equal(actual,p['p']),p['name'];offset+=len(actual)
            world=actual@T[:3,:3].T+T[:3,3];parts.append({'name':p['name'],'points':world,'lo':world.min(0),'hi':world.max(0),'parent':node})
        assert offset==len(values)
    def named(prefix):
        exact=[p for p in parts if p['name']==prefix]
        return exact or [p for p in parts if p['name'].startswith(prefix)]
    checks=[]
    def distance(a,b):return float(np.linalg.norm(np.maximum(0,np.maximum(a['lo']-b['hi'],b['lo']-a['hi']))))
    def supported(a,b,tolerance=.003):
        aa=named(a);bb=named(b);assert aa and bb,(a,b)
        worst=max(min(distance(p,q) for q in bb) for p in aa)
        assert worst<=tolerance,(a,b,worst)
        checks.append({'component':a,'support':b,'maximumBoundingGapMetres':worst,'toleranceMetres':tolerance})
    supported('rear.frame_bracket','chassis.rail')
    supported('rear.frame_bracket','rear.bumper')
    supported('rear.receiver_crossmember','rear.frame_bracket')
    supported('rear.receiver_side_rear','rear.receiver_crossmember')
    supported('rear.receiver_collar','rear.receiver_side_front')
    supported('rear.recovery_lug_web','rear.bumper')
    supported('rear.recovery_lug_eye','rear.recovery_lug_web')
    supported('front.recovery_lug_web','front.recovery_gusset')
    supported('front.recovery_gusset','front.bumper')
    supported('front.recovery_lug_eye','front.recovery_lug_web')
    supported('chassis.wishbone_mount','chassis.rail')
    supported('chassis.wishbone_fork','chassis.wishbone_mount')
    supported('chassis.shock_tower','chassis.rail')
    supported('chassis.shock_tower_cap','chassis.shock_tower')
    supported('chassis.shock_top_fork','chassis.shock_tower_cap')
    supported('chassis.rear_tower','chassis.rail')
    supported('chassis.rear_tower_cap','chassis.rear_tower')
    supported('chassis.rear_shock_fork','chassis.rear_tower_cap')
    supported('chassis.rear_link_bracket','chassis.rail')
    supported('chassis.rear_link_crossmember','chassis.rail')
    supported('chassis.bed_standoff','chassis.rail')
    supported('chassis.bed_cross_support','bed.floor')
    supported('cargo.carrier_foot','bed.floor',.002)
    # A real open socket and through-pin bores replace the floating black decal.
    walls=named('rear.receiver_pin_wall');pin=named('rear.receiver_pin')
    bore=min(float(np.sqrt((p['points'][:,1]-.43)**2+(p['points'][:,2]+2.41)**2).min()) for p in walls)
    assert bore>.0129 and .0105<bore
    assert not named('rear.receiver_bore')
    # Cargo is above the actual new wheel-house surfaces, rather than in them.
    spare=[p for p in parts if p['name'].startswith('spare.') and any(s in p['name'] for s in ('carcass','sidewall','tread'))]
    v=np.concatenate([p['points'] for p in spare]);mask=(abs(v[:,0])>.755)&(abs(v[:,2]+1.59)<.585)
    roof=.4+np.sqrt(np.maximum(0,.655**2-(v[mask,2]+1.59)**2));cargoClearance=float(np.min(v[mask,1]-roof))
    assert cargoClearance>.014,cargoClearance
    assert v[:,1].max()<1.875
    # Actual damper vertices remain inboard of the rear wheel barrel/tread.
    def ancestry(i):
        names=[]
        while True:
            names.append(d['nodes'][i]['name'])
            if i not in parent:return names
            i=parent[i]
    rearDamper=[p for p in parts if p['name'].startswith('damper.') and any(v.startswith('rear.') and '.damper' in v for v in ancestry(p['parent']))]
    maxShockX=max(float(abs(p['points'][:,0]).max()) for p in rearDamper)
    minWheelX=min(float(abs(p['points'][:,0]).min()) for p in named('wheel.RL')+named('wheel.RR'))
    shockClearance=minWheelX-maxShockX;assert shockClearance>.020,shockClearance
    report={'status':'PASS','sha256':hashlib.sha256(raw).hexdigest(),'matchedSerializedParts':len(parts),'connectionChecks':checks,'receiverPinRadialClearanceMetres':bore-.0105,'spareToWheelHouseClearanceMetres':cargoClearance,'highestSpareY':float(v[:,1].max()),'rearDamperToWheelAxialClearanceMetres':shockClearance,'scope':['Every measured source part is verified against its actual serialized GLB vertex range.','Connectivity checks use component bounds plus explicit pin/bore and cargo surface clearances.','Moving fixed-length links, hubs, axle width, damper overlap and natural-motion tests run separately in the native CPU audit.'],'limits':['Does not certify weld strength, towing capacity or manufacturing tolerances.']}
    out=ROOT/'build/baja-427-v3/assembly-audit.json';out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='connectionChecks'},indent=2))

if __name__=='__main__':main()
