import os
import bpy,math,json,runpy
from pathlib import Path
from mathutils import Vector
recipeDir=Path(__file__).resolve().parent; root=Path(os.environ['THREEPP_FOREST_SOURCE_DIR']);globals().update(runpy.run_path(str(recipeDir/'mature-common.py')))
bakes=root/'mature-bakes';bakes.mkdir(exist_ok=True)
def bake_material(leaves,kind,view,height):
    m=bpy.data.materials.new('CPU mature-fir coverage bake');m.use_nodes=True;n=m.node_tree.nodes;n.clear();l=m.node_tree.links
    output=n.new('ShaderNodeOutputMaterial');mix=n.new('ShaderNodeMixShader');transparent=n.new('ShaderNodeBsdfTransparent');emission=n.new('ShaderNodeEmission')
    l.new(transparent.outputs[0],mix.inputs[1]);l.new(emission.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],output.inputs[0])
    prefix='twig' if leaves else 'bark'
    if leaves:
        alpha=n.new('ShaderNodeTexImage');alpha.image=image(root/'fir_tree_01'/'twig_alpha_8bit.png',False)
        threshold=n.new('ShaderNodeMath');threshold.operation='GREATER_THAN';threshold.inputs[1].default_value=.3;l.new(alpha.outputs['Color'],threshold.inputs[0]);l.new(threshold.outputs[0],mix.inputs[0])
    else:mix.inputs[0].default_value=1
    if kind=='albedo':
        tex=n.new('ShaderNodeTexImage');tex.image=image(root/'fir_tree_01'/f'{prefix}_diff_8bit.png',True);l.new(tex.outputs['Color'],emission.inputs[0])
    else:
        angle=view*math.pi/4;u=(math.cos(angle),math.sin(angle),0);v=(0,0,1);front=(math.sin(angle),-math.cos(angle),0)
        geometry=n.new('ShaderNodeNewGeometry')
        if kind=='depth':
            dot=n.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT';dot.inputs[1].default_value=front;l.new(geometry.outputs['Position'],dot.inputs[0])
            scale=n.new('ShaderNodeMath');scale.operation='MULTIPLY_ADD';scale.inputs[1].default_value=1/(height*1.1);scale.inputs[2].default_value=.5;l.new(dot.outputs['Value'],scale.inputs[0]);l.new(scale.outputs[0],emission.inputs[0])
        else:
            tex=n.new('ShaderNodeTexImage');tex.image=image(root/'fir_tree_01'/f'{prefix}_nor_gl_8bit.png',False)
            mapped=n.new('ShaderNodeNormalMap');mapped.inputs[0].default_value=.65;l.new(tex.outputs['Color'],mapped.inputs[1]);normal=mapped.outputs[0]
            dot=n.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT';dot.inputs[1].default_value=front;l.new(normal,dot.inputs[0])
            sign=n.new('ShaderNodeMath');sign.operation='SIGN';l.new(dot.outputs['Value'],sign.inputs[0])
            flipped=n.new('ShaderNodeVectorMath');flipped.operation='SCALE';l.new(normal,flipped.inputs[0]);l.new(sign.outputs[0],flipped.inputs['Scale'])
            combined=n.new('ShaderNodeCombineXYZ')
            for j,axis in enumerate([u,v,front]):
                dot=n.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT';dot.inputs[1].default_value=axis;l.new(flipped.outputs[0],dot.inputs[0])
                scale=n.new('ShaderNodeMath');scale.operation='MULTIPLY_ADD';scale.inputs[1].default_value=.5;scale.inputs[2].default_value=.5;l.new(dot.outputs['Value'],scale.inputs[0]);l.new(scale.outputs[0],combined.inputs[j])
            l.new(combined.outputs[0],emission.inputs[0])
    return m
for variant,mirrored in [('c',False),('b',False),('c',True)]:
    label='c-mirrored' if mirrored else variant;parts,metadata=load_variant(variant,mirrored)
    for p in parts:p['foliage']='twig' in p.data.materials[0].name
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16;scene.cycles.use_denoising=False;scene.cycles.transparent_max_bounces=32
    scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.resolution_x=512;scene.render.resolution_y=512;scene.render.resolution_percentage=100
    scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8';scene.world=None
    scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
    camera_data=bpy.data.cameras.new('CPU mature-fir camera');camera=bpy.data.objects.new('CPU mature-fir camera',camera_data);scene.collection.objects.link(camera);scene.camera=camera
    height=metadata['heightMetres'];camera_data.type='ORTHO';camera_data.ortho_scale=height*1.1;camera_data.clip_start=.01;camera_data.clip_end=height*20
    for view in range(4):
        angle=view*math.pi/4;target=Vector((0,0,height*.5));camera.location=target+Vector((math.sin(angle),-math.cos(angle),0))*height*4;camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
        for kind in ['albedo','normal','depth']:
            path=bakes/f'fir_tree_01-{label}-{view}-{kind}.png'
            if path.exists():continue
            for p in parts:p.data.materials.clear();p.data.materials.append(bake_material(bool(p['foliage']),kind,view,height))
            scene.view_settings.view_transform='Standard' if kind=='albedo' else 'Raw';scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
            print('BAKED',path.name,flush=True)
    metadata.update(asset='fir_tree_01',variant=label,bakePixelsPerView=[512,512],viewAnglesDegrees=[0,45,90,135],method='Complete authored adultLOD2 baked onCPU without foliage deletion')
    (bakes/f'fir_tree_01-{label}.json').write_text(json.dumps(metadata,indent=2))
