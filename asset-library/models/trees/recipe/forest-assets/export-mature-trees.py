import os
import bpy,bmesh,math,json,struct,hashlib,runpy
from pathlib import Path
from mathutils import Vector,Matrix
recipeDir=Path(__file__).resolve().parent; root=Path(os.environ['THREEPP_FOREST_SOURCE_DIR']);globals().update(runpy.run_path(str(recipeDir/'mature-common.py')))
out=Path(os.environ['THREEPP_FOREST_OUTPUT_DIR']);reports=[]
def material(leaves,variant,far):
    m=bpy.data.materials.new('fir_tree_01.'+('foliage' if leaves else 'bark'));m.use_nodes=True;n=m.node_tree.nodes;n.clear();l=m.node_tree.links
    output=n.new('ShaderNodeOutputMaterial');shader=n.new('ShaderNodeBsdfPrincipled');l.new(shader.outputs[0],output.inputs[0]);shader.inputs['Metallic'].default_value=0;shader.inputs['Roughness'].default_value=.96
    if leaves and far:
        base=out/'textures'/f'fir_tree_01-{variant}-canopy-albedo-1k.png';normal=out/'textures'/f'fir_tree_01-{variant}-canopy-normal-1k.png';rough=None
    elif leaves:
        base=root/'fir_tree_01'/'twig_basecolor_8bit.png';normal=root/'fir_tree_01'/'twig_nor_gl_8bit.png';rough=root/'fir_tree_01'/'twig_rough_8bit.png'
    else:
        base=root/'fir_tree_01'/'bark_diff_8bit.png';normal=root/'fir_tree_01'/'bark_nor_gl_8bit.png';rough=root/'fir_tree_01'/'bark_rough_8bit.png'
    tex=n.new('ShaderNodeTexImage');tex.image=image(base,True);l.new(tex.outputs['Color'],shader.inputs['Base Color'])
    if leaves:l.new(tex.outputs['Alpha'],shader.inputs['Alpha']);m.surface_render_method='DITHERED';m.alpha_threshold=.3;m.use_backface_culling=False
    else:m.use_backface_culling=True
    tex=n.new('ShaderNodeTexImage');tex.image=image(normal,False);normalnode=n.new('ShaderNodeNormalMap');normalnode.inputs[0].default_value=.72 if far else .65;l.new(tex.outputs['Color'],normalnode.inputs[1]);l.new(normalnode.outputs[0],shader.inputs['Normal'])
    if rough:
        tex=n.new('ShaderNodeTexImage');tex.image=image(rough,False);l.new(tex.outputs['Color'],shader.inputs['Roughness'])
    return m
for variant,mirror in [('c',False),('b',False),('c',True)]:
    label='c-mirrored' if mirror else variant
    for lod in [1,2]:
        parts,metadata=load_variant(variant,mirror);wood=[o for o in parts if 'twig' not in o.data.materials[0].name];leaves=next(o for o in parts if 'twig' in o.data.materials[0].name);foliage_before=triangles(leaves)
        # Far branches are already represented by the complete silhouette.
        # Keep only the connected main trunk as3Dwood, avoiding thousands of
        # disconnected twig stubs that a collapse ratio cannot remove safely.
        if lod==2:wood=[o for o in wood if '_trunk_' in o.data.materials[0].name]
        for part in wood:
            part.data.materials.clear();part.data.materials.append(material(False,label,False))
            for polygon in part.data.polygons:polygon.material_index=0
        bpy.ops.object.select_all(action='DESELECT')
        for part in wood:part.select_set(True)
        bpy.context.view_layer.objects.active=wood[0];bpy.ops.object.join();bark=bpy.context.view_layer.objects.active
        wood_before=triangles(bark);goal=2000 if lod==1 else 900
        decimate=bark.modifiers.new('Wood-only bounded LOD','DECIMATE');decimate.ratio=min(1,goal/wood_before);decimate.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=decimate.name)
        bark.data.materials.clear();bark.data.materials.append(material(False,label,False))
        for polygon in bark.data.polygons:polygon.material_index=0
        bark.name=f'fir_tree_01.{label}.lod{lod}.bark'
        if lod==2:
            leaves.select_set(False);metadata=json.loads((root/'mature-bakes'/f'fir_tree_01-{label}-grids.json').read_text());height=metadata['heightMetres'];span=metadata['cardSpanMetres'];vertices=[];faces=[];uvs=[];normals=[]
            for view in [0,2]:
                grid=metadata['views'][view]['farGrid'];cols=grid['columns'];rows=grid['rows'];angle=view*math.pi/4;u=Vector((math.cos(angle),math.sin(angle),0));front=Vector((math.sin(angle),-math.cos(angle),0));base=len(vertices)
                for row in range(rows+1):
                    v=.05/1.1+(row/rows)/1.1
                    for col in range(cols+1):
                        point=u*((col/cols-.5)*span)+front*grid['depthMetres'][row*(cols+1)+col]+Vector((0,0,row/rows*height));vertices.append(tuple(point));normals.append(tuple(front));uvs.append((view%2*.5+col/cols*.5,(1-view//2)*.5+v*.5))
                for row in range(rows):
                    for col in range(cols):
                        i=base+row*(cols+1)+col;faces.append((i,i+1,i+cols+2,i+cols+1))
            mesh=bpy.data.meshes.new('Full mature-fir silhouette depth sheets');mesh.from_pydata(vertices,[],faces);mesh.update();layer=mesh.uv_layers.new(name='UVMap')
            for loop in mesh.loops:layer.data[loop.index].uv=uvs[loop.vertex_index]
            for polygon in mesh.polygons:polygon.use_smooth=True
            mesh.normals_split_custom_set_from_vertices(normals);leaves=bpy.data.objects.new(f'fir_tree_01.{label}.lod{lod}.foliage',mesh);bpy.context.scene.collection.objects.link(leaves)
        leaves.name=f'fir_tree_01.{label}.lod{lod}.foliage';leaves.data.materials.clear();leaves.data.materials.append(material(True,label,lod==2))
        for polygon in leaves.data.polygons:polygon.material_index=0
        assert lod!=1 or triangles(leaves)==foliage_before,'Near authored foliage coverage was changed'
        bpy.ops.object.select_all(action='DESELECT');bark.select_set(True);leaves.select_set(True);bpy.context.view_layer.objects.active=leaves
        path=out/f'fir_tree_01-{label}-lod{lod}.glb'
        bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_texcoords=True,export_normals=True,export_tangents=True,export_materials='EXPORT',export_image_format='AUTO',export_yup=True,export_apply=True,export_cameras=False,export_lights=False)
        raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n]);binary=raw[20+n:]
        for m in g['materials']:
            if m.get('name','').endswith('.foliage'):m['alphaMode']='MASK';m['alphaCutoff']=.3;m['doubleSided']=True
            else:m['alphaMode']='OPAQUE';m['doubleSided']=False
        payload=json.dumps(g,separators=(',',':')).encode();payload+=b' '*((-len(payload))%4);raw=struct.pack('<III',0x46546c67,2,20+len(payload)+len(binary))+struct.pack('<II',len(payload),0x4e4f534a)+payload+binary;path.write_bytes(raw)
        report=dict(metadata,file=path.name,lod=lod,sourceAsset='fir_tree_01',sourceLOD='authoredLOD2',parts=[{'role':'bark','sourceTriangles':wood_before,'triangles':triangles(bark),'vertices':len(bark.data.vertices)},{'role':'foliage','sourceTriangles':foliage_before,'triangles':triangles(leaves),'vertices':len(leaves.data.vertices)}],totalTriangles=triangles(bark)+triangles(leaves),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),nearFoliageUnchanged=lod==1,mirrorAppliedToVerticesAndWinding=mirror)
        reports.append(report)
(root/'mature-export.json').write_text(json.dumps(reports,indent=2));print(json.dumps([{k:r[k] for k in ['file','totalTriangles','heightMetres','bytes']} for r in reports],indent=2))
