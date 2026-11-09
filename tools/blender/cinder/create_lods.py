"""Preserve named rigid pivots and author three density tiers for lowriders."""
import bpy,sys,json,hashlib,gc
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'build/unity-assets';rows=[]
for key,source in [('catrina','la-catrina/la-catrina.glb'),('media-luna','media-luna/media-luna.glb'),('nocturne','nocturne/nocturne.glb')]:
    src=ROOT/'asset-library/models'/source
    frozen=ROOT/'assets/unity/sources'/(key+'.glb')
    if frozen.exists():src=frozen
    for suffix,ratio in [('',.38 if key=='catrina' else 1),('-mid',.13),('-far',.035)]:
        bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
        for block in list(bpy.data.meshes):
            if block.users==0:bpy.data.meshes.remove(block)
        gc.collect();bpy.ops.import_scene.gltf(filepath=str(src))
        if ratio<1:
            for obj in list(bpy.context.scene.objects):
                if obj.type!='MESH' or len(obj.data.polygons)<500:continue
                chain=[];part=obj
                while part:chain.append(part.name);part=part.parent
                if any(n.startswith(('bag_','coil_','leaf_','roof_cloth_')) or n.startswith('air.nocturne.rubber') for n in chain):continue
                bpy.context.view_layer.objects.active=obj
                mod=obj.modifiers.new('Authored density tier','DECIMATE');mod.ratio=ratio;mod.use_collapse_triangulate=True
                bpy.ops.object.modifier_apply(modifier=mod.name)
        dst=OUT/(key+suffix);dst.mkdir(parents=True,exist_ok=True)
        bpy.ops.export_scene.gltf(filepath=str(dst/'model.glb'),export_format='GLB',export_yup=True,export_apply=True,export_animations=False)
        count=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in bpy.context.scene.objects if o.type=='MESH')
        rows.append(dict(id=key+suffix,source=str(src.relative_to(ROOT)).replace('\\','/'),sourceSha256=hashlib.sha256(src.read_bytes()).hexdigest(),sha256=hashlib.sha256((dst/'model.glb').read_bytes()).hexdigest(),triangles=count,ratio=ratio,pivots='Preserved named glTF nodes',author='SmithBuilder offline density adaptation',date='2026-11-08'))
(ROOT/'assets/unity/lod-manifest.json').write_text(json.dumps(dict(assets=rows),indent=2)+'\n');print(json.dumps(rows,indent=2))
