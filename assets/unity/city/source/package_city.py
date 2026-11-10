"""Freeze exact native Mercer city data into a Unity-ready GLB and material ledger.

The native runtime never ships with Unity. This is an offline asset conversion.
The full CPU export is retained, and only redundant coplanar ground tessellation
may be reduced; original collision data and all city detail remain untouched.
"""
from pathlib import Path
import argparse, hashlib, json, math, shutil, struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def require(ok,message):
    if not ok:raise ValueError(message)
def readmesh(folder,row):
    attrs={k:np.fromfile(folder/v['file'],dtype='<f4').reshape(v['count'],v['itemSize']) for k,v in row['attributes'].items()}
    indices=np.fromfile(folder/row['indices']['file'],dtype='<u4').reshape(-1,3)
    return attrs,indices

def reduced_ground(folder,doc,tolerance=.012):
    nx,nz=264,440
    height=np.full((nz+1,nx+1),np.nan,dtype=np.float64);rgb=np.full((nz+1,nx+1,3),np.nan,dtype=np.float64)
    material=np.full((nz,nx),-1,dtype=int);native_count=0
    for mi,row in enumerate(doc['meshes']):
        if not row['groundIndexCount']:continue
        a,ix=readmesh(folder,row);ix=ix[:row['groundIndexCount']//3];p=a['position'];c=a['color'];native_count+=len(ix)
        for tri in ix:
            pp=p[tri];xx=np.rint((pp[:,0]+66)*2).astype(int);zz=np.rint((pp[:,2]+24)*2).astype(int)
            height[zz,xx]=pp[:,1];rgb[zz,xx]=c[tri]
            material[zz.min(),xx.min()]=mi
    require(native_count==232320 and np.isfinite(height).all() and np.isfinite(rgb).all() and (material>=0).all(),'Native ground grid was incomplete')
    leaves=[];worst_estimate=0
    def split(x,z,w,d):
        nonlocal worst_estimate
        hs=height[z:z+d+1,x:x+w+1];cols=rgb[z:z+d+1,x:x+w+1];m=material[z:z+d,x:x+w]
        flat=np.max(hs)-np.min(hs)<1e-7;same=np.all(m==m[0,0])
        u=np.arange(w+1)[None,:,None]/w;v=np.arange(d+1)[:,None,None]/d
        model=cols[0,0]*(1-u)*(1-v)+cols[0,-1]*u*(1-v)+cols[-1,0]*(1-u)*v+cols[-1,-1]*u*v
        error=float(np.max(np.abs(cols-model)))
        if (flat and same and error<=tolerance*.65) or (w==1 and d==1):
            leaves.append((x,z,w,d,int(m[0,0]),flat,error));worst_estimate=max(worst_estimate,error);return
        if w>=d and w>1:
            half=w//2;split(x,z,half,d);split(x+half,z,w-half,d)
        else:
            half=d//2;split(x,z,w,half);split(x,z+half,w,d-half)
    # Restrained four-metre cells keep the baked shade interpolation local.
    for z in range(0,nz,8):
        for x in range(0,nx,8):split(x,z,min(8,nx-x),min(8,nz-z))
    horizontal={};vertical={}
    for x,z,w,d,_,_,_ in leaves:
        for zz in (z,z+d):horizontal.setdefault(zz,set()).update((x,x+w))
        for xx in (x,x+w):vertical.setdefault(xx,set()).update((z,z+d))
    parts={};height_error=0;colour_error=0
    def sample(x,z):
        ix=min(int(x),nx-1);iz=min(int(z),nz-1);u=x-ix;v=z-iz
        # Same authoritative triangle interpolation as native terrain.
        def blend(data):
            a,b,c,d=data[iz,ix],data[iz,ix+1],data[iz+1,ix],data[iz+1,ix+1]
            return a+(b-a)*u+(c-a)*v if u+v<=1 else d+(c-d)*(1-u)+(b-d)*(1-v)
        return np.array((x*.5-66,float(blend(height)),z*.5-24)),blend(rgb)
    for x,z,w,d,mi,flat,estimated in leaves:
        out=parts.setdefault(mi,{'position':[],'color':[],'uv':[],'normal':[],'indices':[]})
        if not flat and w==1 and d==1:
            # Exact original diagonal through each non-planar/curb half-metre cell.
            points=[(x,z),(x+1,z),(x,z+1),(x+1,z+1)];local=[(0,2,1),(1,2,3)]
        else:
            boundary=[(xx,z) for xx in sorted(t for t in horizontal[z] if x<=t<=x+w)]
            boundary +=[(x+w,zz) for zz in sorted(t for t in vertical[x+w] if z<t<=z+d)]
            boundary +=[(xx,z+d) for xx in sorted((t for t in horizontal[z+d] if x<=t<x+w),reverse=True)]
            boundary +=[(x,zz) for zz in sorted((t for t in vertical[x] if z<t<z+d),reverse=True)]
            points=[(x+w*.5,z+d*.5)]+boundary;local=[(0,((k+1)%len(boundary))+1,k+1) for k in range(len(boundary))]
        pos=[];color=[]
        for xx,zz in points:
            pp,cc=sample(xx,zz);pos.append(pp);color.append(cc)
        pos=np.asarray(pos);color=np.asarray(color)
        # Validate every original lattice vertex against the actual new triangles.
        for zz in range(z,z+d+1):
            for xx in range(x,x+w+1):
                pp,cc=sample(xx,zz);found=False
                for aa,bb,dd in local:
                    a,b,c=pos[aa][[0,2]],pos[bb][[0,2]],pos[dd][[0,2]];q=pp[[0,2]]
                    det=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
                    if abs(det)<1e-12:continue
                    wa=((b[1]-c[1])*(q[0]-c[0])+(c[0]-b[0])*(q[1]-c[1]))/det;wb=((c[1]-a[1])*(q[0]-c[0])+(a[0]-c[0])*(q[1]-c[1]))/det;wc=1-wa-wb
                    if min(wa,wb,wc)>=-1e-7:
                        height_error=max(height_error,abs(wa*pos[aa,1]+wb*pos[bb,1]+wc*pos[dd,1]-pp[1]))
                        colour_error=max(colour_error,float(np.max(np.abs(wa*color[aa]+wb*color[bb]+wc*color[dd]-cc))));found=True;break
                require(found,'Reduced ground left an uncovered source vertex')
        # Keep vertices per face so exact curb normals and unmodified winding survive.
        tile=4 if doc['meshes'][mi]['id']=='paving' else 4.5
        for tri in local:
            a,b,c=pos[list(tri)];n=np.cross(b-a,c-a);n/=np.linalg.norm(n);base=len(out['position'])
            for ii in tri:
                pp=pos[ii];out['position'].append(pp);out['normal'].append(n);out['color'].append(color[ii]);out['uv'].append((pp[0]/tile,pp[2]/tile))
            out['indices'].append((base,base+1,base+2))
    require(height_error<1e-7,f'Ground geometry error {height_error}')
    require(colour_error<=tolerance,f'Ground colour error {colour_error} > {tolerance}')
    for part in parts.values():
        for key in part:part[key]=np.asarray(part[key],dtype='<u4' if key=='indices' else '<f4')
    return parts,{'nativeTriangles':native_count,'reducedTriangles':sum(len(p['indices']) for p in parts.values()),'leaves':len(leaves),'heightErrorAtAllOriginalVerticesMetres':height_error,'maximumLinearColourErrorAtAllOriginalVertices':colour_error,'linearColourTolerance':tolerance,'preserved':'Every nonflat half-metre curb cell, original diagonal, sampled heights, exact material boundaries; topology stitching prevents T-junction geometry cracks. Sim unchanged.'}

def build(folder,assets,full=False):
    native=json.loads((folder/'native-city.json').read_text());assets.mkdir(parents=True,exist_ok=True);textures=assets/'textures';textures.mkdir(exist_ok=True)
    images={};texture_rows=[]
    for row in native['textures']:
        if row['source']:
            original=Path(row['source']);name=original.name;frozen=ROOT/'assets/unity/city/textures'/name;source=frozen if frozen.is_file() else original;require(source.is_file(),'Native texture missing');target=textures/name
            if target.exists():require(digest(target)==digest(source),'Texture collision')
            else:shutil.copy2(source,target)
            source_label='showcase/assets/city/'+name
        else:
            name='native-leaf-cluster.png';target=textures/name;raw=(folder/row['raw']).read_bytes();mode={3:'RGB',4:'RGBA'}[row['channels']]
            require(len(raw)==row['width']*row['height']*row['channels'],'Bad native generated pixels')
            image=Image.frombytes(mode,(row['width'],row['height']),raw).transpose(Image.Transpose.FLIP_TOP_BOTTOM);image.save(target)
            source_label='Native vegetation::makeLeafClusterTexture(256,427,{.40,.50,.22},Lobed,12,2), exported CPU pixels'
        images[row['id']]=target;texture_rows.append({'file':name,'source':source_label,'sha256':digest(target),'nativeRepeat':row['repeat'],'nativeOffset':row['offset']})
    # All source image samplers use identity transforms; preserve errors loudly.
    for row in native['textures']:require(row['repeat']==[1.,1.] and row['offset']==[0.,0.],'Unexpected authored texture transform')
    gltf={'asset':{'version':'2.0','generator':'SmithBuilder exact native Mercer offline exporter'},'scene':0,'scenes':[{'nodes':[]}],'nodes':[],'meshes':[],'materials':[],'accessors':[],'bufferViews':[],'buffers':[],'images':[],'textures':[],'samplers':[{'wrapS':10497,'wrapT':10497,'magFilter':9729,'minFilter':9987},{'wrapS':33071,'wrapT':33071,'magFilter':9729,'minFilter':9987}]};blob=bytearray();tex_map={}
    def binary(data):
        while len(blob)%4:blob.append(0)
        off=len(blob);blob.extend(data);idx=len(gltf['bufferViews']);gltf['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':len(data)});return idx
    def accessor(a,kind):
        a=np.ascontiguousarray(a,dtype='<u4' if kind=='SCALAR' else '<f4');idx=len(gltf['accessors']);row={'bufferView':binary(a.tobytes()),'componentType':5125 if kind=='SCALAR' else 5126,'count':a.size if kind=='SCALAR' else len(a),'type':kind}
        if kind=='VEC3':row['min']=a.min(axis=0).tolist();row['max']=a.max(axis=0).tolist()
        gltf['accessors'].append(row);return idx
    def texture(path):
        key=str(path)
        if key in tex_map:return tex_map[key]
        data=path.read_bytes();image=len(gltf['images']);gltf['images'].append({'bufferView':binary(data),'mimeType':'image/png' if path.suffix.lower()=='.png' else 'image/jpeg','name':path.name});idx=len(gltf['textures']);gltf['textures'].append({'source':image,'sampler':1 if path.name=='native-leaf-cluster.png' else 0});tex_map[key]=idx;return idx
    materials=[]
    for row in native['meshes']:
        m=row['material'];maps={key:('Assets/Resources/Cinder/CityRestored/'+images[value].name if value else '') for key,value in m['maps'].items()};materials.append({**m,'maps':maps})
        pbr={'baseColorFactor':m['color']+[1.],'metallicFactor':m['metalness'],'roughnessFactor':m['roughness']};gm={'name':m['name'],'pbrMetallicRoughness':pbr,'doubleSided':m['doubleSided'],'emissiveFactor':m['emissive']}
        if m['alphaCutoff']>0:gm.update(alphaMode='MASK',alphaCutoff=m['alphaCutoff'])
        if m['maps']['color']:pbr['baseColorTexture']={'index':texture(images[m['maps']['color']])}
        if m['maps']['normal']:gm['normalTexture']={'index':texture(images[m['maps']['normal']]),'scale':m['normalScale'][0]}
        if m['maps']['roughness']:
            rough=Image.open(images[m['maps']['roughness']]).convert('RGB');r=np.asarray(rough);packed=np.zeros((r.shape[0],r.shape[1],4),dtype=np.uint8);packed[:,:,1]=r[:,:,1];packed[:,:,2]=255;packed[:,:,3]=255;dest=assets/('packed-'+m['id']+'.png');Image.fromarray(packed).save(dest);pbr['metallicRoughnessTexture']={'index':texture(dest)}
        gltf['materials'].append(gm)
    reduced,ground_report=reduced_ground(folder,native) if not full else ({},{'nativeTriangles':232320,'reducedTriangles':232320,'mode':'full original control'})
    total=0;counts=[]
    for mi,row in enumerate(native['meshes']):
        a,ix=readmesh(folder,row);ground=row['groundIndexCount']//3
        parts=[]
        if ground:
            if full:parts.append(('ground.'+row['id'],a,ix[:ground]))
            else:
                part=reduced[mi];parts.append(('ground.'+row['id'],{k:v for k,v in part.items() if k!='indices'},part['indices']))
        if len(ix)>ground:parts.append(('static.'+row['id'],a,ix[ground:]))
        for name,attrs,indices in parts:
            used,inverse=np.unique(indices,return_inverse=True);attrs={k:v[used].copy() for k,v in attrs.items()};indices=inverse.astype('<u4').reshape(-1,3)
            # glTF V is top-origin; native and the Unity sampler are bottom-origin.
            attrs['uv'][:,1]=1-attrs['uv'][:,1]
            attributes={semantic:accessor(attrs[key],kind) for key,semantic,kind in [('position','POSITION','VEC3'),('normal','NORMAL','VEC3'),('uv','TEXCOORD_0','VEC2'),('color','COLOR_0','VEC3')]}
            mesh=len(gltf['meshes']);gltf['meshes'].append({'name':name,'primitives':[{'attributes':attributes,'indices':accessor(indices.reshape(-1),'SCALAR'),'material':mi,'mode':4}]});node=len(gltf['nodes']);gltf['nodes'].append({'name':name,'mesh':mesh});gltf['scenes'][0]['nodes'].append(node);total+=len(indices);counts.append({'name':name,'vertices':len(used),'triangles':len(indices),'material':row['name'],'receiveCarShadow':name.startswith('ground.')})
    gltf['buffers']=[{'byteLength':len(blob)}];jb=json.dumps(gltf,separators=(',',':'),allow_nan=False).encode();jb+=b' '*((-len(jb))%4);blob+=b'\0'*((-len(blob))%4)
    data=struct.pack('<III',0x46546c67,2,28+len(jb)+len(blob))+struct.pack('<II',len(jb),0x4e4f534a)+jb+struct.pack('<II',len(blob),0x004e4942)+blob
    target=assets/('mercer-city-full.glb' if full else 'mercer-city.glb');require(not target.exists(),'Preserve existing GLB; choose a new output folder');target.write_bytes(data)
    (assets/'materials.json').write_text(json.dumps({'version':1,'materials':materials,'uvConvention':'glTF TEXCOORD_0=(nativeU,1-nativeV); Unity importer restores(nativeU,nativeV). Original source image bytes preserved; generated native texture rows converted to top-down PNG.','sunDirection':native['sunDirection'],'skyRotationRadians':native['skyRotationRadians']},indent=2)+'\n')
    sources=[]
    snapshot=assets/'source';snapshot.mkdir(exist_ok=True)
    for src in ['showcase/CityBlock.hpp','showcase/CityLayout.hpp','showcase/PlaygroundTerrain.hpp','showcase/RallyForest.hpp','tools/cinder-city-export/export_city.cpp','tools/cinder-city-export/package_city.py','include/threepp/extras/vegetation/TreeGenerator.hpp','include/threepp/extras/vegetation/TreeTextures.hpp','include/threepp/extras/core/NoiseUtils.hpp','include/threepp/extras/core/TextureBake.hpp']:
        relative=Path(src) if src.startswith('include/') else Path(src).name
        canonical=ROOT/'assets/unity/city/source'/relative
        source=canonical if canonical.is_file() else ROOT/src;dest=snapshot/relative;dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists():require(digest(dest)==digest(source),'Owning source changed during city export')
        else:shutil.copy2(source,dest)
        sources.append({'source':src,'frozen':dest.relative_to(ROOT).as_posix(),'sha256':digest(source)})
    for name in ['photo-surfaces.json','source.json']:
        src=ROOT/'showcase/assets/city'/name
        if src.exists():shutil.copy2(src,assets/name)
    manifest={'version':1,'id':'mercer-city','datePacific':'2026-11-09','author':'SmithBuilder native city; exact offline conversion for Unity','nativeTriangles':native['triangles'],'triangles':total,'materialBatches':25,'meshCount':len(counts),'meshes':counts,'groundReduction':ground_report,'sourceFiles':sources,'conversionTool':{'source':'tools/cinder-city-export/package_city.py','sha256':digest(Path(__file__))},'linkedNativeLibrary':{'source':'build/windows-gl/src/Release/threepp.lib','sha256':digest(ROOT/'build/windows-gl/src/Release/threepp.lib'),'bytes':(ROOT/'build/windows-gl/src/Release/threepp.lib').stat().st_size},'textures':texture_rows,'glb':target.name,'sha256':digest(target),'coverage':{'nativeBuildings':11,'nativeContextShells':15,'scope':'All native facade, window treatment, roof/service, street furniture, roadwear, signs, boundary, context and trees exported. Only ground tessellation reduced in accepted asset; full original CPU control retained.'},'runtime':'Geometry/material data only; no native runtime, scene/controller or physics embedded. Authoritative Unity Sim terrain unchanged.'}
    (assets/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'success':True,'glb':str(target),'triangles':total,'ground':ground_report,'meshes':len(counts),'textures':len(texture_rows)},indent=2))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,default=ROOT/'build/cinder-city-export/native-v1');ap.add_argument('--output',type=Path,default=ROOT/'assets/unity/city');ap.add_argument('--full-control',action='store_true');a=ap.parse_args();build(a.input.resolve(),a.output.resolve(),a.full_control)
