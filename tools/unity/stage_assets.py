"""Freeze donor bytes for the Unity importer; no donor files are modified."""
from pathlib import Path
import hashlib,json,shutil,struct
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'build/unity-assets'
OUT.mkdir(parents=True,exist_ok=True)
sources={
 'safari':ROOT/'showcase/assets/safari-body.glb',
 'baja':ROOT/'asset-library/models/baja-427/baja-427.glb',
 'switchback':ROOT/'asset-library/models/switchback/switchback.glb',
 'catrina':ROOT/'asset-library/models/la-catrina/la-catrina.glb',
 'media-luna':ROOT/'asset-library/models/media-luna/media-luna.glb',
 'nocturne':ROOT/'asset-library/models/nocturne/nocturne.glb',
}
rows=[]
for key,src in sources.items():
    frozen=ROOT/'assets/unity/sources'/(key+'.glb')
    if frozen.exists():src=frozen
    if not src.exists():
        if key in ('catrina','media-luna','nocturne'):raise FileNotFoundError(src)
        continue
    donor=src.read_bytes();data=(OUT/key/'model.glb').read_bytes() if key in ('catrina','media-luna','nocturne') and (ROOT/'assets/unity/lod-manifest.json').exists() and (OUT/key/'model.glb').exists() else donor;n=struct.unpack_from('<I',data,12)[0]
    doc=json.loads(data[20:20+n]); dst=OUT/key;dst.mkdir(exist_ok=True)
    # Materialize glTF defaults so Unity JsonUtility cannot confuse absent mesh 0.
    for node in doc.get('nodes',[]):node.setdefault('mesh',-1)
    for mesh in doc.get('meshes',[]):
        for prim in mesh['primitives']:
            prim.setdefault('indices',-1);prim.setdefault('material',-1);prim.setdefault('mode',4)
            for attr in ('NORMAL','TEXCOORD_0','COLOR_0','TANGENT'):prim['attributes'].setdefault(attr,-1)
    for im in doc.get('images',[]):im.setdefault('bufferView',-1)
    for m in doc.get('materials',[]):
        m.setdefault('alphaCutoff',.5);p=m.setdefault('pbrMetallicRoughness',{});p.setdefault('metallicFactor',1);p.setdefault('roughnessFactor',1)
    jb=json.dumps(doc,separators=(',',':')).encode();jb+=b' '*((-len(jb))%4);tail=data[20+n:]
    staged=struct.pack('<III',0x46546c67,2,20+len(jb)+len(tail))+struct.pack('<II',len(jb),0x4e4f534a)+jb+tail
    (dst/'model.glb').write_bytes(staged)
    for im in doc.get('images',[]):
        uri=im.get('uri','')
        if uri and not uri.startswith('data:'):
            target=dst/uri;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src.parent/uri,target)
    triangles=sum(doc['accessors'][p['indices']]['count']//3 for m in doc.get('meshes',[]) for p in m['primitives'] if 'indices' in p)
    rows.append(dict(id=key,source=str(src.relative_to(ROOT)).replace('\\','/'),sha256=hashlib.sha256(donor).hexdigest(),triangles=triangles,nodes=len(doc.get('nodes',[])),materials=len(doc.get('materials',[])),author='SmithBuilder donor kit; original provenance remains beside source',date='2026-11-08',parts='Named glTF nodes preserved',placement='Metres, Y up, +Z forward. No runtime embedded engine.'))
for key in ('buggy','safari-running-gear','city-kit','forest-kit'):
    src=OUT/key/'model.glb'
    if src.exists():rows.append(dict(id=key,source='tools/blender/cinder/create_kit.py',sha256=hashlib.sha256(src.read_bytes()).hexdigest(),author='SmithBuilder',date='2026-11-08',placement='Metres, Y up, +Z forward',parts='Named authored nodes'))
tree=ROOT/'asset-library/models/trees/exports/fir_tree_01-b-lod2.glb'
if not tree.exists():tree=next((ROOT/'asset-library/models/trees').rglob('fir_tree_01-b-lod2.glb'))
treeout=OUT/'conifer';treeout.mkdir(exist_ok=True);shutil.copy2(tree,treeout/'model.glb')
# Tree exports use external atlas files. Preserve their relative references.
td=tree.read_bytes();tn=struct.unpack_from('<I',td,12)[0];tj=json.loads(td[20:20+tn])
for im in tj.get('images',[]):
    uri=im.get('uri','')
    if uri and not uri.startswith('data:'):
        source=tree.parent/uri
        if not source.exists():source=next((ROOT/'asset-library/models/trees').rglob(Path(uri).name))
        target=treeout/uri;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
art=ROOT/'Unity/Assets/Cinder/Art/Generated';art.mkdir(parents=True,exist_ok=True)
shutil.copy2(ROOT/'asset-library/environments/kloofendal-partly-cloudy/sky_1k.hdr',art/'sky.hdr')
shutil.copy2(ROOT/'asset-library/materials/gravel-road/basecolor_1k.jpg',art/'gravel.jpg')
shutil.copy2(ROOT/'asset-library/materials/forest-floor/basecolor_1k.jpg',art/'forest-floor.jpg')
cityart=ROOT/'Unity/Assets/Resources/Cinder/City';cityart.mkdir(parents=True,exist_ok=True)
for name in ('ph-asphalt-color.jpg','ph-asphalt-normal.jpg','ph-red-brick-color.jpg','ph-red-brick-normal.jpg','ph-buff-brick-color.jpg','ph-buff-brick-normal.jpg','ph-plaster-color.jpg','ph-plaster-normal.jpg'):
    shutil.copy2(ROOT/'showcase/assets/city'/name,cityart/name)
for path in OUT.glob('*/model.glb'):
    raw=path.read_bytes();size=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+size]);tail=raw[20+size:]
    for n in doc.get('nodes',[]):n.setdefault('mesh',-1)
    for m in doc.get('meshes',[]):
        for p in m['primitives']:
            p.setdefault('indices',-1);p.setdefault('material',-1);p.setdefault('mode',4)
            for a in ('NORMAL','TEXCOORD_0','COLOR_0','TANGENT'):p['attributes'].setdefault(a,-1)
    for im in doc.get('images',[]):im.setdefault('bufferView',-1)
    for m in doc.get('materials',[]):
        m.setdefault('normalTexture',{'index':-1});m['normalTexture'].setdefault('scale',1);m.setdefault('alphaCutoff',.5)
        p=m.setdefault('pbrMetallicRoughness',{});p.setdefault('metallicFactor',1);p.setdefault('roughnessFactor',1)
        p.setdefault('baseColorTexture',{'index':-1});p.setdefault('metallicRoughnessTexture',{'index':-1})
    jb=json.dumps(doc,separators=(',',':')).encode();jb+=b' '*((-len(jb))%4)
    path.write_bytes(struct.pack('<III',0x46546c67,2,20+len(jb)+len(tail))+struct.pack('<II',len(jb),0x4e4f534a)+jb+tail)
for row in rows:
    staged=OUT/row['id']/'model.glb'
    if staged.exists():row['stagedSha256']=hashlib.sha256(staged.read_bytes()).hexdigest()
lodfile=ROOT/'assets/unity/lod-manifest.json'
if lodfile.exists():
    lods=json.loads(lodfile.read_text())
    for row in lods['assets']:
        row.setdefault('exportSha256',row['sha256']);row['sha256']=hashlib.sha256((OUT/row['id']/'model.glb').read_bytes()).hexdigest()
    lodfile.write_text(json.dumps(lods,indent=2)+'\n')
target=ROOT/'assets/unity/manifest.json';target.write_text(json.dumps(dict(revision='cinder-unity',assets=rows,notes=['Named pivots and materials preserved; lowrider hero/mid/far adaptations recorded separately','Generated kit is an original Unity adaptation of donor dimensions, not identical procedural donor art']),indent=2)+'\n')
print(json.dumps(rows,indent=2))
