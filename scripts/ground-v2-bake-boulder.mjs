// Offline, renderer-independent authoring source. Output is a normal OBJ asset;
// no engine executes this generator at runtime. node scripts/ground-v2-bake-boulder.mjs
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const folder=path.join(root,'asset-library/models/fieldstone');
fs.mkdirSync(folder,{recursive:true});
const latCount=5,lonCount=7,vertices=[],uv=[],faces=[];
const sub=(a,b)=>a.map((v,i)=>v-b[i]);
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0);
for(let lat=0;lat<=latCount;lat++){
  const theta=lat*Math.PI/latCount,st=Math.sin(theta),ct=Math.cos(theta);
  for(let lon=0;lon<=lonCount;lon++){
    const phi=lon*Math.PI*2/lonCount;
    const r=.96+.08*Math.sin(2*phi+.6)*st*st+.055*Math.cos(3*phi-.4)*st*st+.035*Math.sin(3*theta);
    vertices.push([st*Math.cos(phi)*r,ct*r*.83,st*Math.sin(phi)*r]);
    uv.push([lon/lonCount,1-lat/latCount]);
  }
}
for(let lat=0;lat<latCount;lat++)for(let lon=0;lon<lonCount;lon++){
  const a=lat*(lonCount+1)+lon,b=a+lonCount+1;
  for(const ids of [[a,a+1,b],[a+1,b+1,b]]){
    let n=cross(sub(vertices[ids[1]],vertices[ids[0]]),sub(vertices[ids[2]],vertices[ids[0]]));
    if(dot(n,n)<1e-12)continue;
    if(dot(n,vertices[ids[0]])<0){[ids[1],ids[2]]=[ids[2],ids[1]];n=n.map(x=>-x);}
    faces.push({ids,n});
  }
}
// Weld normals at the UV seam and poles, retaining duplicate UV vertices.
const key=p=>p.map(v=>Math.abs(v)<1e-6?'0.000000':v.toFixed(6)).join(',');
const sums=new Map(vertices.map(p=>[key(p),[0,0,0]]));
for(const {ids,n} of faces)for(const i of ids){const s=sums.get(key(vertices[i]));n.forEach((v,k)=>s[k]+=v);}
const normals=vertices.map(p=>{const n=sums.get(key(p)),length=Math.hypot(...n);return n.map(v=>v/length);});
const fmt=a=>a.map(v=>v.toFixed(8)).join(' ');
const out=['# Original fieldstone; metres, Y up; MIT (repository LICENSE).','o Fieldstone','s 1',
  ...vertices.map(p=>'v '+fmt(p)),...uv.map(p=>'vt '+fmt(p)),...normals.map(n=>'vn '+fmt(n)),
  ...faces.map(({ids})=>'f '+ids.map(i=>`${i+1}/${i+1}/${i+1}`).join(' '))].join('\n')+'\n';
fs.writeFileSync(path.join(folder,'boulder.obj'),out);
const metadata={schemaVersion:1,id:'model.fieldstone',type:'obj-model',format:'OBJ',file:'boulder.obj',
  units:'metres',upAxis:'Y',triangles:faces.length,vertices:vertices.length,smoothVertexNormals:true,
  material:'material.forest-floor',materialBinding:{materialId:'material.forest-floor',
    materialManifest:'../../materials/forest-floor/material.json',uvSet:0,
    uvScale:[2,.52],uvOffset:[0,0],wrapS:'repeat',wrapT:'repeat',
    uvConvention:'OBJ vt coordinates with bottom-left origin; V increases from the negative-Y pole to the positive-Y pole',
    sampling:"Multiply the OBJ UVs by uvScale, then add uvOffset for every bound texture. The threepp adapter's compensation for shared terrain texture transforms is not part of this portable binding.",
    normalConvention:'OpenGL +Y tangent space',
    overrides:{baseColorFactorLinear:[1.10,1.13,1.10],roughnessFactor:.97,normalScale:[.65,.65]}},
  source:'Original procedural fieldstone authored for this project; offline source scripts/ground-v2-bake-boulder.mjs',
  license:'MIT',licenseFile:'../../LICENSE',
  sha256:crypto.createHash('sha256').update(out).digest('hex'),
  bounds:{min:[0,1,2].map(i=>Math.min(...vertices.map(p=>p[i]))),max:[0,1,2].map(i=>Math.max(...vertices.map(p=>p[i])))},
  notes:'Static portable OBJ with UVs and explicit welded smooth normals; no runtime procedural dependency. Reuses material.forest-floor textures. 56 nondegenerate triangles versus the previous70-slot boulder.'};
fs.writeFileSync(path.join(folder,'asset.json'),JSON.stringify(metadata,null,2)+'\n');
console.log(JSON.stringify({triangles:faces.length,bytes:Buffer.byteLength(out),sha256:metadata.sha256}));
