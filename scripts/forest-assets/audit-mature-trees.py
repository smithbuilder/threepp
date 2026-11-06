import os
from pathlib import Path
from PIL import Image
import json,struct,hashlib,io
import numpy as np
recipeDir=Path(__file__).resolve().parent; root=Path(os.environ['THREEPP_FOREST_SOURCE_DIR']);out=Path(os.environ['THREEPP_FOREST_OUTPUT_DIR'])
exports=json.loads((root/'mature-export.json').read_text());models=[]
def sha(data):return hashlib.sha256(data).hexdigest()
def accessor(g,b,index):
    a=g['accessors'][index];v=g['bufferViews'][a['bufferView']];dtype={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']];components={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];size=np.dtype(dtype).itemsize
    return np.ndarray((a['count'],components),dtype=dtype,buffer=b,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',components*size),size))
for exported in exports:
    path=out/exported['file'];raw=path.read_bytes();assert struct.unpack_from('<III',raw)==(0x46546c67,2,len(raw));n=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n]);binary=raw[28+n:]
    assert all('uri' not in x for x in g['buffers']) and len(g['meshes'])==2 and len(g['materials'])==2
    for node in g['nodes']:
        assert np.prod(node.get('scale',[1,1,1]))>0,'Negative node determinant loses winding in the runtime adapter'
        if 'matrix' in node:assert np.linalg.det(np.array(node['matrix']).reshape((4,4),order='F'))>0
    semantics={}
    for mat in g['materials']:
        p=mat.get('pbrMetallicRoughness',{})
        for obj,semantic,space in [(p.get('baseColorTexture'),'baseColorRGBA','sRGB'),(p.get('metallicRoughnessTexture'),'metallicRoughnessGB','linear'),(mat.get('normalTexture'),'normalGL','linear')]:
            if obj:semantics[g['textures'][obj['index']]['source']]=(semantic,space)
    images=[]
    for i,im in enumerate(g['images']):
        view=g['bufferViews'][im['bufferView']];data=binary[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']];image=Image.open(io.BytesIO(data));image.load();assert max(image.size)<=1024
        if data.startswith(b'\x89PNG'):assert data[24]==8
        semantic,space=semantics[i];entry={'name':im.get('name'),'semantic':semantic,'colorSpace':space,'width':image.width,'height':image.height,'bitsPerChannel':8,'mode':image.mode,'bytes':len(data),'sha256':sha(data)}
        if semantic=='baseColorRGBA' and image.mode=='RGBA':
            alpha=np.array(image.getchannel('A'));entry['alphaCoverageAt0_3']=float(np.mean(alpha>=77));assert alpha.min()==0 and alpha.max()==255
        images.append(entry)
    parts=[]
    for mesh in g['meshes']:
        for p in mesh['primitives']:
            pos=accessor(g,binary,p['attributes']['POSITION']);idx=accessor(g,binary,p['indices']);norm=accessor(g,binary,p['attributes']['NORMAL']);uv=accessor(g,binary,p['attributes']['TEXCOORD_0']);assert np.isfinite(pos).all() and np.isfinite(norm).all() and np.isfinite(uv).all() and idx.max()<len(pos)
            mat=g['materials'][p['material']];role='foliage' if mat['name'].endswith('.foliage') else 'bark';parts.append({'role':role,'vertices':len(pos),'triangles':len(idx)//3,'material':mat['name'],'alphaMode':mat.get('alphaMode','OPAQUE'),'alphaCutoff':mat.get('alphaCutoff'),'doubleSided':mat.get('doubleSided',False)})
    triangles=sum(p['triangles'] for p in parts);assert triangles==exported['totalTriangles'];assert exported['lod']==1 or triangles<=1920
    if exported['lod']==1:assert next(p['triangles'] for p in parts if p['role']=='foliage')==next(p['sourceTriangles'] for p in exported['parts'] if p['role']=='foliage')
    models.append({'file':path.name,'sourceVariant':exported['sourceVariant'],'mirrored':exported['mirrored'],'lod':exported['lod'],'heightMetres':exported['heightMetres'],'vertices':sum(p['vertices'] for p in parts),'triangles':triangles,'parts':parts,'embeddedTextures':images,'bytes':len(raw),'sha256':sha(raw)})
near=sum(m['triangles'] for m in models if m['lod']==1);assert near<=41744
manifest=json.loads((root/'fir_tree_01-files.json').read_text());blend=root/'fir_tree_01-1k.blend';assert hashlib.md5(blend.read_bytes()).hexdigest()==manifest['blend']['1k']['blend']['md5']
sources=[]
for path in sorted((root/'fir_tree_01').glob('*.png')):
    if path.stem.endswith('_8bit'):continue
    entry=manifest[path.stem]['1k']['png'];data=path.read_bytes();assert hashlib.md5(data).hexdigest()==entry['md5'];sources.append({'semantic':path.stem,'url':entry['url'],'sha256':sha(data),'officialMd5Verified':True,'width':1024,'height':1024})
receipt={'schemaVersion':1,'id':'model.mature-conifers','title':'Mature fir B, C and mirrored C','kind':'models','license':'CC0-1.0','licenseUrl':'https://polyhaven.com/license','authors':'Rico Cilliers(modeling), Rob Tuytel(photography)','sourceUrl':'https://polyhaven.com/a/fir_tree_01','sourceBlend':{'url':manifest['blend']['1k']['blend']['url'],'bytes':blend.stat().st_size,'sha256':sha(blend.read_bytes()),'officialMd5Verified':True},'sourceTextureMaps':sources,'format':'Self-contained standard glTF2.0 GLB; no Draco, external images, runtime shader or backend dependency','coordinateSystem':{'up':'+Y','units':'metres','pivot':'ground at y=0, centered X/Z','heights':'Original adult14.08–14.55m retained in portable files'},'derivation':{'near':'Authored sourceLOD2. All27,952combined foliage triangles retained exactly; onlywoodgeometry collapse-simplified. SourceCORNER/FLOAT_VECTOR UVMap restored to ordinary glTF2D UVs. Original sprig diffuse/alpha/GLnormal/roughness retained at1K. Sourcewoodmaterialnetworks consolidated using the common original bark PBR maps to retain two material draws per prototype.','far':'Complete authored adult silhouettes CPU-baked at512px/view using unlit diffuse, view-relative normal and first-hit depth; packed into1024 four-view atlases. Two depth-shaped sheets and a900triangle connected3Dtrunk. No needle-geometry deletion is used to obtain opacity coverage.','mirror':'C mirror applied directly to X vertex positions; polygon winding reversed before normal/tangent export; all exported node transforms have positive determinant.','processing':'Blender4.5.9 LTS CPU only, two threads; no GPU rendering. Runtime images converted to8bits/channel. No directional illumination baked into baseColor.','history':'Needle-collapse candidate rejected as empty stems. Sapling coverage candidate restored opacity but was rejected as immature/cactus-like. Both exact model/capture/header snapshots remain underbuild/fidelity-v1/rejected-needle-lod andcoverage-sapling-candidate.'},'lodAdvisory':{'lod1':'Full authored3Dbough foliage for roadside/medium distance; original14m adult proportions.','lod2':'Distant fixed-view impostor, advisory>50m. It is not a close-up hero mesh or dynamically view-blended LOD.'},'runtimeAdapter':{'nearInstances':180,'nearDrawBatches':6,'nearVariants':['fir_tree_01-c-lod1.glb','fir_tree_01-b-lod1.glb','fir_tree_01-c-mirrored-lod1.glb'],'nearHeightMetres':[7,14],'nearRoadsideOffsetMetres':'80%8–14m,20%14–22m; minimum7.5m road-center clearance','farInstances':240,'farDrawBatches':2,'farVariant':'fir_tree_01-c-lod2.glb','farHeightMetres':[10,18],'aspect':'Authoredcrown/trunkaspect retained with small near width variation','materials':'All near prototypes share original sprig PBR maps and consolidated bark PBR maps. Far shares bark only and uses its own full-silhouette atlas/normal.','leafShadows':False},'verification':{'scope':'CPU structural/source/image validation only; native appearance pending fresh root review','combinedNearPrototypeTriangles':near,'exactPreviousNearLimit':41744,'farCLimit':1920,'fullAuthoredNearFoliageRetained':True,'finitePositionsNormalsUVs':True,'validIndices':True,'allImagesDecodedMax1K8bit':True,'positiveExportedNodeDeterminants':True,'officialSourceMd5Verified':True},'qualityLimitations':['Wood uses a consolidated common bark material to keep the original two-draw prototype budget; variant-specific original multi-layer trunk shader networks are not reproduced.','Far trees use two fixed-view depth sheets, with limited close-range parallax and no view blending.','The stage has finite repeated prototypes and no added foliage wind, transmission shader or antialiasing.','Technical validation does not establish AAA quality, final native appearance, frame rate or user acceptance.'],'models':models,'standaloneAtlases':[{'file':str(p.relative_to(out)).replace('\\','/'),'width':1024,'height':1024,'colorSpace':'sRGB' if 'albedo' in p.name else 'linear','sha256':sha(p.read_bytes()),'bytes':p.stat().st_size,'layout':'2x2views0/45/90/135degrees, row-major fromupper-left'} for p in sorted((out/'textures').glob('fir_tree_01-*-canopy-*.png'))]}
(out/'asset.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'nearTriangles':near,'farCTriangles':next(m['triangles'] for m in models if m['file']=='fir_tree_01-c-lod2.glb'),'models':[{k:m[k] for k in ['file','vertices','triangles']} for m in models],'imagesValidated':sum(len(m['embeddedTextures']) for m in models)},indent=2))
