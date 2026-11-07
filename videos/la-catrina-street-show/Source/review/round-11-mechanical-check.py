import sys,hashlib,json,pathlib
sys.dont_write_bytecode=True
source_paths=["scripts/catrina_art.py","scripts/catrina_hardware.py","scripts/catrina_frame_pockets.py","showcase/CatrinaRig.hpp","scripts/catrina_generate.py","scripts/baja427_generate.py","scripts/catrina_reference_paint.py"]
source_hashes={p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() for p in source_paths}
print('SOURCE_HASHES',json.dumps(source_hashes),flush=True)
import sys,math,csv,hashlib,numpy as np
sys.stdout.reconfigure(encoding='utf-8')
from scipy.spatial.transform import Rotation
sys.dont_write_bytecode=True;sys.path.insert(0,'scripts')
import catrina_generate as c,catrina_art,catrina_hardware
catrina_art.install(vars(c))
for f in[c.shell,c.roof_and_glass,c.front_rear,c.interior,c.gear,c.trunk]:f()
catrina_hardware.add_hardware(vars(c));M=c.M
parents={ch:i for i,n in enumerate(M.nodes)for ch in n.get('children',[])}
world={}
def wm(i):
 if i not in world:
  n=M.nodes[i];a=np.eye(4);a[:3,:3]=Rotation.from_quat(n.get('rotation',[0,0,0,1])).as_matrix()@np.diag(n.get('scale',[1,1,1]));a[:3,3]=n.get('translation',[0,0,0]);world[i]=wm(parents[i])@a if i in parents else a
 return world[i]
def vertices(p):
 a=wm(p['parent']);return p['p']@a[:3,:3].T+a[:3,3]
def triangles(p):return vertices(p)[p['f']]
def crossings(va,fa,vb,fb,stop=False):
 if np.any(va.max(0)<vb.min(0)-1e-7)or np.any(vb.max(0)<va.min(0)-1e-7):return 0
 edges=np.unique(np.sort(np.concatenate([fa[:,[0,1]],fa[:,[1,2]],fa[:,[2,0]]]),axis=1),axis=0);tri=vb[fb];aa=tri[:,0];e1=tri[:,1]-aa;e2=tri[:,2]-aa;count=0
 for edge in edges:
  o=va[edge[0]];d=va[edge[1]]-o;p=np.cross(d,e2);det=(e1*p).sum(1);ok=abs(det)>1e-11;inv=np.where(ok,1/np.where(ok,det,1),0);tv=o-aa;u=(tv*p).sum(1)*inv;q=np.cross(tv,e1);v=(d*q).sum(1)*inv;t=(e2*q).sum(1)*inv;count+=np.count_nonzero(ok&(u>=-1e-6)&(v>=-1e-6)&(u+v<=1.000001)&(t>=-1e-6)&(t<=1.000001))
  if stop and count:return count
 return count
def intersect(a,b):return crossings(vertices(a),a['f'],vertices(b),b['f'],True)or crossings(vertices(b),b['f'],vertices(a),a['f'],True)
def dists(points,tri):
 p=points[:,None,:];a,b,cc=[tri[None,:,i,:]for i in range(3)];u=b-a;v=cc-a;w=p-a;uu=(u*u).sum(2);uv=(u*v).sum(2);vv=(v*v).sum(2);wu=(w*u).sum(2);wv=(w*v).sum(2);den=uu*vv-uv*uv;alpha=(wu*vv-wv*uv)/den;beta=(wv*uu-wu*uv)/den;n=np.cross(u,v);plane=np.abs((w*n).sum(2))/np.sqrt((n*n).sum(2));best=np.where((alpha>=0)&(beta>=0)&(alpha+beta<=1),plane,np.inf)
 for x,y in[(a,b),(b,cc),(cc,a)]:
  edge=y-x;t=np.clip(((p-x)*edge).sum(2)/(edge*edge).sum(2),0,1);best=np.minimum(best,np.linalg.norm(p-x-t[:,:,None]*edge,axis=2))
 return best.min(1)
def rot_between(a,b):
 a=np.array(a,float);a/=np.linalg.norm(a);b=np.array(b,float);b/=np.linalg.norm(b);q=np.r_[np.cross(a,b),1+a.dot(b)];q/=np.linalg.norm(q);return Rotation.from_quat(q).as_matrix()
print('finalParts',len(M.parts),'helperHash',hashlib.sha256(open('scripts/catrina_hardware.py','rb').read()).hexdigest(),flush=True)


def crossings(va,fa,vb,fb,stop=False):
 lo=vb.min(0);hi=vb.max(0)
 if np.any(va.max(0)<lo-1e-7)or np.any(hi<va.min(0)-1e-7):return 0
 edges=np.unique(np.sort(np.concatenate([fa[:,[0,1]],fa[:,[1,2]],fa[:,[2,0]]]),axis=1),axis=0)
 ea=va[edges[:,0]];eb=va[edges[:,1]];elo=np.minimum(ea,eb);ehi=np.maximum(ea,eb);keep=np.all(ehi>=lo-1e-7,1)&np.all(elo<=hi+1e-7,1);ea=ea[keep];eb=eb[keep];elo=elo[keep];ehi=ehi[keep]
 tri=vb[fb];tlo=tri.min(1);thi=tri.max(1);count=0
 for start in range(0,len(ea),32):
  sl=slice(start,start+32);cand=np.any(np.all(thi[None]>=elo[sl,None]-1e-7,2)&np.all(tlo[None]<=ehi[sl,None]+1e-7,2),0)
  if not cand.any():continue
  ts=tri[cand];aa=ts[None,:,0];e1=ts[None,:,1]-aa;e2=ts[None,:,2]-aa;o=ea[sl,None,:];d=eb[sl,None,:]-o;p=np.cross(d,e2);det=(e1*p).sum(2);ok=abs(det)>1e-11;inv=np.where(ok,1/np.where(ok,det,1),0);tv=o-aa;u=(tv*p).sum(2)*inv;q=np.cross(tv,e1);v=(d*q).sum(2)*inv;t=(e2*q).sum(2)*inv;count+=np.count_nonzero(ok&(u>=-1e-6)&(v>=-1e-6)&(u+v<=1.000001)&(t>=-1e-6)&(t<=1.000001))
  if stop and count:return count
 return count


fixed=[p for p in M.parts if M.nodes[p['parent']]['name']=='body' and (p['name'].startswith(('chassis.','body.','interior.'))or p['name']in['hydraulic.ram_fixed_pin','hydraulic.ram_pin_spacer'])]
fv=[vertices(p)for p in fixed];flo=np.array([v.min(0)for v in fv]);fhi=np.array([v.max(0)for v in fv])
rows=list(csv.DictReader(open('build/sessions/20261106-101153-431/physics-audit/catrina-rig-poses.csv')));groups={};hits={};maxangle=0
for i in range(4):
 for nm in['barrel','rod','coil','seat']:
  name=f'hydraulic_{i}_{nm}'if nm in['barrel','rod']else f'coil_{i}'+('_seat'if nm=='seat'else'');node=next(j for j,n in enumerate(M.nodes)if n['name']==name);v=[];f=[];count=0
  for p in M.parts:
   if p['parent']==node:v.append(p['p']);f.append(p['f']+count);count+=len(p['p'])
  groups[i,nm]=np.concatenate(v),np.concatenate(f)
print('movingSweepFixedParts',len(fixed),flush=True)
for off in range(0,len(rows),12):
 pose=rows[off:off+4];pts=[np.array([float(row[k])for k in['x','y','z']])for row in pose];RR=Rotation.from_quat([float(pose[2][k])for k in['qx','qy','qz','qw']]).as_matrix()@Rotation.from_rotvec([-.6,0,0]).as_matrix();center=(pts[2]+pts[3])*.5
 for i in range(4):
  s=-1 if i%2==0 else 1
  if i<2:
   dy=pts[i][1]-.2891;span=math.sqrt(.535**2-dy*dy);seat=np.array([s*(.18+span*.37/.535),.27+dy*.37/.535,1.5113])
  else:seat=center+RR@np.array([s*.56,.0409,0])
  top=np.array(M.joints[f'hydraulic_{i}']['a']);dist=np.linalg.norm(seat-top);axis=(seat-top)/dist;rot=rot_between([0,-1,0],axis);maxangle=max(maxangle,math.degrees(math.acos(np.clip(rot[0,0],-1,1))))
  for ext in[0,.29,.58]:
   cup=np.clip(.310+ext*.42,.280,max(.280,min(.430,dist-.114)))
   for nm in['barrel','rod','coil','seat']:
    if nm in['barrel','seat']and ext!=0:continue
    vv,pf=groups[i,nm]
    if nm=='barrel':pv=vv@rot.T+top
    elif nm=='rod':pv=vv@rot.T+top+axis*cup
    else:pv=(vv*np.array([1,(dist-cup)/(.28 if i<2 else .22)if nm=='coil'else 1,1]))@rot.T+seat
    candidates=np.where(np.all(fhi>=pv.min(0)-1e-7,1)&np.all(flo<=pv.max(0)+1e-7,1))[0]
    for k in candidates:
     key=(i,nm,fixed[k]['name'])
     if key in hits:continue
     if crossings(pv,pf,fv[k],fixed[k]['f'],True)or crossings(fv[k],fixed[k]['f'],pv,pf,True):hits[key]=(off//4+1,ext);print('MOVING_INTERSECTION',key,hits[key],flush=True)
print('movingSweepComplete','uniquePosePairs',81,'commandLevels',[0,.29,.58],'collisionCategories',len(hits),'maxPinMisalignmentDegrees',maxangle,flush=True)


_casingParts=[p for p in M.parts if p['name'].startswith('body.trunk_frame_channel_')]
_casingVerts=[vertices(p)for p in _casingParts];_casingLo=np.array([v.min(0)for v in _casingVerts]);_casingHi=np.array([v.max(0)for v in _casingVerts]);_casingHits={}
_ids={n['name']:i for i,n in enumerate(M.nodes)}
_names=['rear_axle','rear_2_lower','rear_3_lower','rear_upper','rear_panhard']+[f'damper_{i}{tail}'for i in[2,3]for tail in['','_rod']]
_locals={}
for nm in _names:
 vv=[];ff=[];nn=0
 for pp in M.parts:
  if pp['parent']==_ids[nm]:vv.append(pp['p']);ff.append(pp['f']+nn);nn+=len(pp['p'])
 _locals[nm]=np.concatenate(vv),np.concatenate(ff)
def _shockAim(axis,pin):
 yy=-axis;zz=pin-np.dot(pin,yy)*yy;zz/=np.linalg.norm(zz);return np.c_[np.cross(yy,zz),yy,zz]
def _casingTest(name,pv,pf,pose):
 if not _casingParts:return
 ks=np.where(np.all(_casingHi>=pv.min(0)-1e-7,1)&np.all(_casingLo<=pv.max(0)+1e-7,1))[0]
 for kk in ks:
  key=(name,_casingParts[kk]['name'])
  if key in _casingHits:continue
  if crossings(pv,pf,_casingVerts[kk],_casingParts[kk]['f'],True)or crossings(_casingVerts[kk],_casingParts[kk]['f'],pv,pf,True):
   _casingHits[key]=pose;print('CASING_MOTION_INTERSECTION',key,pose,flush=True)
for offset in range(0,len(rows),12):
 rr=rows[offset:offset+4];center=np.mean([[float(rr[k][a])for a in['x','y','z']]for k in[2,3]],0);RR=Rotation.from_quat([float(rr[2][k])for k in['qx','qy','qz','qw']]).as_matrix()@Rotation.from_rotvec([-.6,0,0]).as_matrix();pose=int(rr[0]['pose']);vv,ff=_locals['rear_axle'];_casingTest('rear_axle',vv@RR.T+center,ff,pose);mounts={}
 for nm in _names[1:5]:
  aa,bb=[np.array(M.joints[nm][k])for k in['a','b']];end=center+RR@(bb-[0,.2891,-1.5113]);QQ=rot_between(bb-aa,end-aa);mounts[nm]=(aa,QQ);vv,ff=_locals[nm];_casingTest(nm,vv@QQ.T+aa,ff,pose)
 for corner in[2,3]:
  jj=M.joints[f'damper_{corner}'];aa,QQ=mounts[jj['mountNode']];end=aa+QQ@(np.array(jj['b'])-aa);top=np.array(jj['a']);axis=(end-top)/np.linalg.norm(end-top);pin=np.array(jj['fixedPinAxis'])
  for tail,origin,rotation in[('',top,_shockAim(axis,pin)),('_rod',end,_shockAim(axis,QQ@pin))]:
   nm=f'damper_{corner}{tail}';vv,ff=_locals[nm];_casingTest(nm,vv@rotation.T+origin,ff,pose)
print('casingMotionComplete','parts',len(_casingParts),'intersectionCategories',len(_casingHits),flush=True)


_moving_hits=dict(hits);_max_pin_angle=maxangle
loadparts=[p for p in M.parts if p['name'].startswith('chassis.ram_')or p['name']in['chassis.boxed_X_rail','hydraulic.ram_fixed_pin']]
graph=[set()for p in loadparts]
for i in range(len(loadparts)):
 for j in range(i):
  if intersect(loadparts[i],loadparts[j]):graph[i].add(j);graph[j].add(i)
seen={i for i,p in enumerate(loadparts)if p['name']=='chassis.boxed_X_rail'};queue=list(seen)
while queue:
 i=queue.pop()
 for j in graph[i]:
  if j not in seen:seen.add(j);queue.append(j)
unconnected=[{'part':p['name'],'center':vertices(p).mean(0).tolist()}for i,p in enumerate(loadparts)if i not in seen]
steel=[p for p in M.parts if p['name'].startswith(('chassis.ram_','chassis.spring_pocket_'))or p['name']=='chassis.boxed_X_rail']
enclosures=[p for p in M.parts if p['name'].startswith(('body.engine_ram_','body.trunk_ram_','body.trunk_frame_channel_'))]
static_hits=[]
for p in steel:
 for q in enclosures:
  if intersect(p,q):static_hits.append({'moving':p['name'],'fixed':q['name']})
lids={};lid_hits=[];shelf_hits=[]
from scipy.interpolate import LinearNDInterpolator
for front in[True,False]:
 nm='hood'if front else'trunk';inner=next(p for p in M.parts if p['name']=='body.'+nm+'_inner');v=vertices(inner);height=LinearNDInterpolator(v[:,[0,2]],v[:,1]);covers=[p for p in M.parts if p['name'].startswith('body.'+('engine'if front else'trunk')+'_ram_cover')or(not front and p['name'].startswith('body.trunk_frame_channel_'))];cv=[vertices(p)for p in covers];vv=np.concatenate(cv);gap=height(vv[:,[0,2]])-vv[:,1];lids[nm]={'minimumClosedInnerVerticalGapMetres':float(np.nanmin(gap)),'gapScope':'Only cover points inside the inner-lid X/Z domain; forward rear-pocket overlap is separately checked against parcel shelf.'}
 hinge=next(j for j,n in enumerate(M.nodes)if n['name']==nm+'_hinge');pivot=wm(hinge)[:3,3];lp=[p for p in M.parts if p['parent']==hinge]
 for step in range(9):
  angle=(-1.10 if front else 1.08)*step/8;rot=Rotation.from_rotvec([angle,0,0]).as_matrix()
  for p in lp:
   pv=(vertices(p)-pivot)@rot.T+pivot
   for k,q in enumerate(covers):
    if crossings(pv,p['f'],cv[k],q['f'],True)or crossings(cv[k],q['f'],pv,p['f'],True):lid_hits.append({'lid':nm,'part':p['name'],'cover':q['name'],'angle':angle})
 for p in covers:
  for q in[p for p in M.parts if p['name']=='interior.parcel_shelf']:
   if intersect(p,q):shelf_hits.append({'cover':p['name'],'shelf':q['name']})
print('staticResults','connected',len(seen),'of',len(loadparts),'unconnected',unconnected,'steelEnclosureHits',static_hits,'lidHits',lid_hits,'shelfHits',shelf_hits,'lidGaps',lids,flush=True)



def bracket_sat_intersect(va,fa,vb,fb):
 if np.any(va.max(0)<vb.min(0)-1e-8)or np.any(vb.max(0)<va.min(0)-1e-8):return False
 ta=va[fa];tb=vb[fb];alo=ta.min(1);ahi=ta.max(1);blo=tb.min(1);bhi=tb.max(1)
 for start in range(0,len(ta),128):
  ai,bi=np.where(np.all(ahi[start:start+128,None]>=blo[None]-1e-8,2)&np.all(alo[start:start+128,None]<=bhi[None]+1e-8,2))
  if not len(ai):continue
  for off in range(0,len(ai),1024):
   aa=ta[ai[off:off+1024]+start];bb=tb[bi[off:off+1024]]
   ea=np.roll(aa,-1,axis=1)-aa;eb=np.roll(bb,-1,axis=1)-bb
   na=np.cross(ea[:,0],ea[:,1]);nb=np.cross(eb[:,0],eb[:,1])
   axes=np.concatenate([na[:,None],nb[:,None],np.cross(ea[:,:,None],eb[:,None]).reshape(-1,9,3),np.cross(na[:,None],ea),np.cross(nb[:,None],eb)],1)
   lengths=np.linalg.norm(axes,axis=2);valid=lengths>1e-12;axes=axes/np.where(valid,lengths,1)[:,:,None]
   pa=np.einsum('nvc,nac->nav',aa,axes);pb=np.einsum('nvc,nac->nav',bb,axes)
   separated=((pa.max(2)<pb.min(2)-1e-8)|(pb.max(2)<pa.min(2)-1e-8))&valid
   if np.any(~separated.any(1)):return True
 return False

_bracketHits={};_exhaustArmHits={};_exhaustFixedHits=[]
_brackets=[p for p in M.parts if p['name']=='chassis.spring_pocket_arm_bracket']
_pipes=[p for p in M.parts if p['name'].startswith(('driveline.exhaust','engine.exhaust_collector'))]
_pipeV=[vertices(p)for p in _pipes];_pipeLo=np.array([v.min(0)for v in _pipeV]);_pipeHi=np.array([v.max(0)for v in _pipeV])
for side in[0,1]:
 sign=-1 if side==0 else 1
 heights=np.linspace(-.12,.42,65)
 for upper in[False,True]:
  nm=f'front_{side}_'+('upper'if upper else'lower');node=next(j for j,n in enumerate(M.nodes)if n['name']==nm);origin=np.array([sign*.18,.43 if upper else .25,1.5113]);parts=[p for p in M.parts if p['parent']==node]
  for height in heights:
   dy=height-.2891;span=math.sqrt(.535**2-dy*dy);rot=Rotation.from_rotvec([0,0,sign*math.atan2(dy,span)]).as_matrix()
   for p in parts:
    pv=p['p']@rot.T+origin
    if p['name']in['front.bush_sleeve','front.formed_channel_arm']:
     for q in _brackets:
      key=(nm,p['name'],tuple(np.round(vertices(q).mean(0),5)))
      if key not in _bracketHits and bracket_sat_intersect(pv,p['f'],vertices(q),q['f']):_bracketHits[key]=height
    ks=np.where(np.all(_pipeHi>=pv.min(0)-1e-7,1)&np.all(_pipeLo<=pv.max(0)+1e-7,1))[0]
    for kk in ks:
     key=(nm,p['name'],_pipes[kk]['name'])
     if key not in _exhaustArmHits and(crossings(pv,p['f'],_pipeV[kk],_pipes[kk]['f'],True)or crossings(_pipeV[kk],_pipes[kk]['f'],pv,p['f'],True)):_exhaustArmHits[key]=height
for p in _pipes:
 for q in M.parts:
  if not(q['name'].startswith(('body.trunk_frame_channel_','chassis.spring_pocket_'))or q['name']=='chassis.boxed_X_rail'):continue
  if intersect(p,q):_exhaustFixedHits.append({'pipe':p['name'],'fixed':q['name'],'pipeCenter':vertices(p).mean(0).tolist()})
print('attachmentExhaustResults','bracketSleeveArmHits',list(_bracketHits.items()),'exhaustArmHits',list(_exhaustArmHits.items()),'exhaustFixedHits',_exhaustFixedHits,flush=True)


pose_path='build/sessions/20261106-101153-431/physics-audit/catrina-rig-poses.csv'
end_hashes={p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()for p in source_paths}
result={
'sourceHashes':source_hashes,'hashesUnchanged':source_hashes==end_hashes,
'poseSource':pose_path,'poseSha256':hashlib.sha256(pathlib.Path(pose_path).read_bytes()).hexdigest(),
'poseRows':len(rows),'parts':len(M.parts),'triangles':sum(len(p['f'])for p in M.parts),'fixedBodyPartsTested':len(fixed),'newFrameCasingParts':len(_casingParts),'frontHeightSamples':65,
'movingFixedHitCategories':[{'pair':list(k),'poseAndCommand':list(v)}for k,v in _moving_hits.items()],
'casingMotionHitCategories':[{'pair':list(k),'pose':v}for k,v in _casingHits.items()],
'maxRamPinMisalignmentDegrees':_max_pin_angle,
'loadPathConnectedParts':len(seen),'loadPathTotalParts':len(loadparts),'loadPathUnconnectedParts':unconnected,
'steelEnclosureHits':static_hits,'lidHits':lid_hits,'parcelShelfHits':shelf_hits,'lidGaps':lids,
'bracketSleeveArmHits':[{ 'pair':str(k),'height':v}for k,v in _bracketHits.items()],
'exhaustArmHits':[{ 'pair':str(k),'height':v}for k,v in _exhaustArmHits.items()],
'exhaustFixedHits':_exhaustFixedHits}
print('FINAL_RESULT_JSON',json.dumps(result),flush=True)

"""Appended to the round-09 reproducer; all geometry is independently rerun.

CPU only. No model export, native viewer, browser or source modification.
"""
from collections import Counter
from datetime import datetime, timezone

_original_result = result
_base_hashes_after = dict(end_hashes)
_all_vertices = {id(p): vertices(p) for p in M.parts}
def vertices(p):
    return _all_vertices[id(p)]

# Restrict new sheet-versus-steel work to changed surfaces, leaving intentional
# fixed body/frame attachments elsewhere outside this incremental scope.
_changed_skin_parts = [p for p in M.parts if
    p['name'].startswith(('body.engine_ram_cover', 'body.trunk_ram_cover',
                         'body.wheel_well_', 'body.arch_',
                         'body.engine_wheelhouse', 'body.trunk_wheelhouse')) or
    p['name'] in ('body.trunk_rear_liner', 'trim.arch_lip')]
_revised_tower_parts = [p for p in M.parts if p['name'] in (
    'chassis.ram_tower_post', 'chassis.ram_rail_foot', 'chassis.ram_header_riser',
    'chassis.ram_header_crossbar', 'chassis.ram_header_side')]
_changed_parts = _changed_skin_parts + _revised_tower_parts
_changed_v = [vertices(p) for p in _changed_parts]
_changed_lo = np.array([v.min(0) for v in _changed_v])
_changed_hi = np.array([v.max(0) for v in _changed_v])
_new_hits = {}
_exact_pair_tests = Counter()
_transformed_groups = Counter()

def new_test(stage, name, pv, pf, pose):
    """Coplanar-aware exact triangle SAT after part/triangle AABB pruning."""
    _transformed_groups[stage] += 1
    candidates = np.where(np.all(_changed_hi >= pv.min(0)-1e-8, 1) &
                          np.all(_changed_lo <= pv.max(0)+1e-8, 1))[0]
    if stage == 'fixedSteel':
        # Tower-to-frame welded connections are intentional and remain in the
        # original load-path graph. Fixed steel is rejected against skins only.
        candidates = candidates[candidates < len(_changed_skin_parts)]
    for k in candidates:
        key = (stage, name, k)
        _exact_pair_tests[stage] += 1
        if key in _new_hits:
            continue
        if bracket_sat_intersect(pv, pf, _changed_v[k], _changed_parts[k]['f']):
            _new_hits[key] = {'stage': stage, 'moving': name,
                'fixed': _changed_parts[k]['name'], 'changedSurfaceIndex': k,
                'fixedCenter': _changed_v[k].mean(0).tolist(), 'sample': pose}
            print('NEW_EXACT_INTERSECTION', json.dumps(_new_hits[key]), flush=True)

_steel_parts = [p for p in M.parts if M.nodes[p['parent']]['name'] == 'body' and
    (p['name'].startswith(('chassis.', 'damper.support_', 'damper.tower_', 'damper.pin_clevis'))
     or p['name'] in ('hydraulic.ram_fixed_pin', 'hydraulic.ram_pin_spacer',
                     'hydraulic.ram_pin_head', 'hydraulic.ram_spherical_inner_ball'))]
for _j, _p in enumerate(_steel_parts):
    new_test('fixedSteel', _p['name'], vertices(_p), _p['f'], {'fixedSteelIndex': _j})
print('NEW_FIXED_STEEL_COMPLETE', len(_steel_parts), flush=True)

# Exact tyre surfaces, including the real profile and tread depressions, are
# transformed using the actual spin-node world quaternion in every CSV row.
# Repeated wheel transforms are computed once; all 972 rows are accounted for.
_tyres = {}
for _i in range(4):
    _node = next(j for j,n in enumerate(M.nodes) if n['name'] == f'wheel_{_i}_spin')
    _parts = [p for p in M.parts if p['parent'] == _node and p['name'] == 'wheel.tyre']
    assert len(_parts) == 1, (_i, len(_parts))
    _tyres[_i] = (_parts[0]['p'], _parts[0]['f'])
_wheel_transforms = {}
for _row in rows:
    _key = tuple(_row[k] for k in ('wheel','x','y','z','qx','qy','qz','qw'))
    _wheel_transforms.setdefault(_key, _row)
for _j, _row in enumerate(_wheel_transforms.values()):
    _i = int(_row['wheel'])
    _center = np.array([float(_row[k]) for k in ('x','y','z')])
    _rotation = Rotation.from_quat([float(_row[k]) for k in ('qx','qy','qz','qw')]).as_matrix()
    _vv, _ff = _tyres[_i]
    new_test('tyres', f'wheel_{_i}.tyre', _vv @ _rotation.T + _center, _ff,
             {'pose': int(_row['pose']), 'wheel': _i})
print('NEW_EXACT_TYRES_COMPLETE', len(rows), len(_wheel_transforms), flush=True)

# Re-run ram, rigid cup/seat and spring transforms through SAT specifically for
# the changed covers, arch liners, front end curtains and rail-notch edges.
for _offset in range(0, len(rows), 12):
    _pose = rows[_offset:_offset+4]
    _pts = [np.array([float(row[k]) for k in ('x','y','z')]) for row in _pose]
    _RR = Rotation.from_quat([float(_pose[2][k]) for k in ('qx','qy','qz','qw')]).as_matrix() @ Rotation.from_rotvec([-.6,0,0]).as_matrix()
    _center = (_pts[2]+_pts[3])*.5
    for _i in range(4):
        _sign = -1 if _i % 2 == 0 else 1
        if _i < 2:
            _dy = _pts[_i][1]-.2891
            _span = math.sqrt(.535**2-_dy**2)
            _seat = np.array([_sign*(.18+_span*.37/.535), .27+_dy*.37/.535, 1.5113])
        else:
            _seat = _center + _RR @ np.array([_sign*.56, .0409, 0])
        _top = np.array(M.joints[f'hydraulic_{_i}']['a'])
        _distance = np.linalg.norm(_seat-_top)
        _axis = (_seat-_top)/_distance
        _rotation = rot_between([0,-1,0], _axis)
        for _command in (0, .29, .58):
            _cup = np.clip(.310+_command*.42, .280, max(.280, min(.430, _distance-.114)))
            for _name in ('barrel','rod','coil','seat'):
                if _name in ('barrel','seat') and _command != 0:
                    continue
                _vv, _ff = groups[_i, _name]
                if _name == 'barrel':
                    _pv = _vv @ _rotation.T + _top
                elif _name == 'rod':
                    _pv = _vv @ _rotation.T + _top + _axis*_cup
                else:
                    _scale = np.array([1, (_distance-_cup)/(.28 if _i<2 else .22) if _name=='coil' else 1, 1])
                    _pv = (_vv*_scale) @ _rotation.T + _seat
                new_test('springRamSeat', f'{_i}.{_name}', _pv, _ff,
                         {'pose': int(_pose[0]['pose']), 'command': _command})
print('NEW_EXACT_SPRING_RAM_COMPLETE', flush=True)

# Front wishbones and separate shock barrel/rod against the changed tub sheets.
# No attachment-region exclusion is used here: the new curtains are not joints.
_front_groups = {}
for _name in [f'front_{i}_{level}' for i in (0,1) for level in ('lower','upper')] + [f'damper_{i}{tail}' for i in (0,1) for tail in ('','_rod')]:
    _node = next(j for j,n in enumerate(M.nodes) if n['name'] == _name)
    _vlist, _flist, _count = [], [], 0
    for _p in M.parts:
        if _p['parent'] == _node:
            _vlist.append(_p['p']); _flist.append(_p['f']+_count); _count += len(_p['p'])
    _front_groups[_name] = np.concatenate(_vlist), np.concatenate(_flist)
for _i in (0,1):
    _sign = -1 if _i == 0 else 1
    for _height in np.linspace(-.12, .42, 65):
        _dy = _height-.2891; _span = math.sqrt(.535**2-_dy**2)
        _rotation = Rotation.from_rotvec([0,0,_sign*math.atan2(_dy,_span)]).as_matrix()
        for _level in ('lower','upper'):
            _name = f'front_{_i}_{_level}'
            _origin = np.array([_sign*.18, .25 if _level=='lower' else .43, 1.5113])
            _vv,_ff = _front_groups[_name]
            new_test('frontArms', _name, _vv @ _rotation.T + _origin, _ff, {'height': float(_height)})
        _joint = M.joints[f'damper_{_i}']; _origin = np.array([_sign*.18,.25,1.5113])
        _end = _origin + _rotation @ (np.array(_joint['b'])-_origin)
        _top = np.array(_joint['a']); _axis = (_end-_top)/np.linalg.norm(_end-_top)
        _pin = np.array(_joint['fixedPinAxis'])
        for _tail,_pivot,_rot in (('',_top,_shockAim(_axis,_pin)),('_rod',_end,_shockAim(_axis,_rotation@_pin))):
            _name = f'damper_{_i}{_tail}'; _vv,_ff = _front_groups[_name]
            new_test('frontDampers', _name, _vv @ _rot.T + _pivot, _ff, {'height': float(_height)})
print('NEW_EXACT_FRONT_MOTION_COMPLETE', flush=True)

# All actual hinge-owned lid meshes, at the original nine opening angles,
# tested against every changed liner/cover rather than cover names alone.
_lid_mesh_counts = {}
for _front in (True,False):
    _name = 'hood' if _front else 'trunk'
    _hinge = next(j for j,n in enumerate(M.nodes) if n['name'] == _name+'_hinge')
    _pivot = wm(_hinge)[:3,3]
    _parts = [p for p in M.parts if p['parent'] == _hinge]
    _lid_mesh_counts[_name] = len(_parts)
    for _step in range(9):
        _angle = (-1.10 if _front else 1.08)*_step/8
        _rotation = Rotation.from_rotvec([_angle,0,0]).as_matrix()
        for _p in _parts:
            new_test('lids', _name+'.'+_p['name'], (vertices(_p)-_pivot) @ _rotation.T + _pivot, _p['f'],
                     {'lid':_name,'angleRadians':_angle})
print('NEW_EXACT_LIDS_COMPLETE', flush=True)

_end_hashes = {p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() for p in source_paths}
_pose_end_hash = hashlib.sha256(pathlib.Path(pose_path).read_bytes()).hexdigest()
_original_result.update(sourceHashesAfter=_end_hashes,
    hashesUnchanged=source_hashes==_base_hashes_after==_end_hashes,
    poseHashUnchanged=_pose_end_hash==_original_result['poseSha256'],
    changedSurfaceParts=len(_changed_parts),
    changedSkinParts=len(_changed_skin_parts),
    revisedTowerParts=len(_revised_tower_parts),
    changedSurfaceNames=dict(Counter(p['name'] for p in _changed_parts)),
    addedFixedSteelParts=len(_steel_parts),
    exactTyrePoseRows=len(rows), exactTyreNativePoses=len({r['pose'] for r in rows}),
    exactTyreUniqueWheelTransforms=len(_wheel_transforms),
    exactTyreTrianglesPerWheel={str(i):len(v[1]) for i,v in _tyres.items()},
    addedTransformedGroups=dict(_transformed_groups),
    addedExactTrianglePairTests=dict(_exact_pair_tests),
    addedExactTriangleHits=list(_new_hits.values()),
    lidMeshCounts=_lid_mesh_counts)
_failure_keys = ('movingFixedHitCategories','casingMotionHitCategories','loadPathUnconnectedParts',
    'steelEnclosureHits','lidHits','parcelShelfHits','bracketSleeveArmHits','exhaustArmHits',
    'exhaustFixedHits','addedExactTriangleHits')
_pass = (not any(_original_result[k] for k in _failure_keys) and
    _original_result['hashesUnchanged'] and _original_result['poseHashUnchanged'] and
    all(g['minimumClosedInnerVerticalGapMetres']>0 for g in _original_result['lidGaps'].values()))
_prior = json.loads(pathlib.Path('build/la-catrina/independent/round-09-mechanical.json').read_text(encoding='utf-8-sig'))
_script = pathlib.Path(__file__)
_report = {k:_prior[k] for k in ('method','intentionalContactExclusions','limitations','units','sampling')}
_report.update(review='Round 11 independent mechanical source geometry review',
    scope='Previous scoped mechanical checks independently rerun, plus exact coplanar-aware checks of revised ram-cover/wheelhouse blisters, arch/inner-apron skins, front end curtains, rail notches and tapered tower posts against actual fixed steel, ram/spring/seat motion, tyres, front wishbones/dampers and lid sweeps. Fixed tower-to-frame joints remain intentional load-path connections.',
    status=('PASS' if _pass else 'FAIL')+' — scoped sampled source-geometry review',
    createdUtc=datetime.now(timezone.utc).isoformat(),reviewer='/root/round10_mechanical_check',
    results=_original_result,
    reproducer={'workingDirectory':'C:/Users/oliver/Projects/engine-threepp',
        'requirements':['Python','numpy','scipy','Pillow'],
        'script':str(_script.relative_to(pathlib.Path.cwd())).replace('\\','/'),
        'scriptSha256':hashlib.sha256(_script.read_bytes()).hexdigest(),
        'execution':'python -B build/la-catrina/independent/round-11-mechanical-check.py',
        'sideEffects':'Writes only this mechanical review JSON/Markdown; in-memory geometry only, no asset export, native process, browser, source edits or bytecode.'})
_report['method'] += [
    'Repeat the original checks from their runnable reproducer against freshly constructed current geometry; previous PASS values are not inherited.',
    'For changed cover/liner/arch/curtain/notch surfaces, apply the coplanar-aware triangle SAT to actual fixed steel, all sampled ram/coil/seat poses, actual tyre meshes transformed by the native spin-node quaternions, front arms/dampers at 65 heights, and both lids at nine angles. Part AABBs only prune candidates; every reported contact is an actual triangle pair.',
    'All 972 wheel rows from 243 native commands are represented; exactly repeated wheel transforms are deduplicated without dropping unique steering/articulation combinations. No tyre cylinder or inflated marker substitutes for the actual tyre mesh in these additional checks.'
]
_report['method'] += [
    'Round 11 expands the coplanar-aware target list to the actual engine/trunk wheelhouse skins, curved front apron edge skins and every tapered ram member (posts, rail feet, risers, header crossbars and header sides). All are checked against actual tyres, spring/ram/seat transforms, front arms/dampers and hinge-owned lid meshes. Fixed steel is checked against the skins; member-to-member welded joints remain in the independent rail-connectivity graph.'
]
_report['limitations'] = [line for line in _report['limitations'] if not line.startswith('Tire sweep')]
_report['limitations'] += [
    'Actual-tyre triangle tests in this report cover the listed changed surfaces. Broader serialized-model enclosure sampling and exported/baked asset/native-executable identity remain separate root-agent gates.',
    'Exact triangle SAT includes coplanar surface contact; it does not establish a general watertight solid-containment proof or a positive minimum separation for every pair.',
    'Nine lid angles and finite suspension/steering samples are diagnostic samples, not continuously swept collision detection.'
]
_report['sampling'].update(actualTyreNativePoses=len({r['pose'] for r in rows}),
    actualTyrePoseRows=len(rows),actualTyreUniqueTransforms=len(_wheel_transforms),
    addedTransformedGroups=dict(_transformed_groups))
_out = pathlib.Path('build/la-catrina/independent/round-11-mechanical')
_out.with_suffix('.json').write_text(json.dumps(_report,indent=2)+'\n',encoding='utf-8')
_summary = [f"# {_report['review']}", '', _report['status'], '', _report['scope'], '',
    f"Source hashes unchanged: {_original_result['hashesUnchanged']}. Pose hash unchanged: {_original_result['poseHashUnchanged']}.",
    f"Actual geometry: {_original_result['parts']} parts, {_original_result['triangles']} triangles.",
    f"Updated surfaces: {len(_changed_parts)} parts; fixed steel: {len(_steel_parts)} parts.",
    f"Tyres: {len(rows)} rows / {len({r['pose'] for r in rows})} native poses / {len(_wheel_transforms)} unique wheel transforms.",
    f"Original collision categories: {sum(len(_original_result[k]) for k in _failure_keys if k!='addedExactTriangleHits')}; new exact triangle collision categories: {len(_new_hits)}.",
    f"Frame connectivity: {_original_result['loadPathConnectedParts']}/{_original_result['loadPathTotalParts']} ram load-path parts reach modeled boxed rails.",
    f"Closed inner-lid vertical gaps: hood {_original_result['lidGaps']['hood']['minimumClosedInnerVerticalGapMetres']*1000:.3f} mm; trunk {_original_result['lidGaps']['trunk']['minimumClosedInnerVerticalGapMetres']*1000:.3f} mm (within each lid's X/Z interpolation domain).",'',
    '## Exact inputs', '', *[f'- `{p}`: `{h}`' for p,h in source_hashes.items()],
    f'- `{pose_path}`: `{_original_result["poseSha256"]}`', '', '## Method', '',
    *['- '+line for line in _report['method']], '', '## Intentional contacts excluded', '',
    *['- '+line for line in _report['intentionalContactExclusions']], '', '## Limits', '',
    *['- '+line for line in _report['limitations']], '', '## Reproduce', '',
    '```powershell', _report['reproducer']['execution'], '```', '',
    f"Script SHA256: `{_report['reproducer']['scriptSha256']}`", '',
    'Full pair counts, sample counts, source hashes before/after, collision findings and scope are in the companion JSON.', '']
if _new_hits:
    _summary += ['## Findings', '', *['- '+json.dumps(h) for h in _new_hits.values()], '']
_out.with_suffix('.md').write_text('\n'.join(_summary),encoding='utf-8')
print('ROUND11_FINAL', json.dumps({'status':_report['status'],'hashesUnchanged':_original_result['hashesUnchanged'],
    'addedExactTriangleHits':len(_new_hits),'resultsPath':str(_out.with_suffix('.json'))}),flush=True)
raise SystemExit(0 if _pass else 1)
