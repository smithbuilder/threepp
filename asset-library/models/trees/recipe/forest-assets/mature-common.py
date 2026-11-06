import os
import bpy,bmesh,math
from pathlib import Path
from mathutils import Vector,Matrix
recipeDir=Path(__file__).resolve().parent; root=Path(os.environ['THREEPP_FOREST_SOURCE_DIR'])
def restore_uv(mesh):
    if mesh.uv_layers.active:return
    source=mesh.attributes.get('UVMap')
    if not source:raise RuntimeError('Authored adult tree lost its named UV attribute')
    coords=[(v.vector.x,v.vector.y) for v in source.data];mesh.attributes.remove(source)
    layer=mesh.uv_layers.new(name='UVMap')
    for i,uv in enumerate(coords):layer.data[i].uv=uv
def load_variant(variant,mirrored=False):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    name=f'fir_tree_01_{variant}_LOD2'
    with bpy.data.libraries.load(str(root/'fir_tree_01-1k.blend'),link=False) as (s,t):t.objects=[name]
    obj=t.objects[0];bpy.context.scene.collection.objects.link(obj);restore_uv(obj.data);bpy.context.view_layer.update()
    low=Vector((float('inf'),)*3);high=Vector((-float('inf'),)*3)
    for v in obj.data.vertices:
        q=obj.matrix_world@v.co
        for j in range(3):low[j]=min(low[j],q[j]);high[j]=max(high[j],q[j])
    centre=Vector(((low.x+high.x)*.5,(low.y+high.y)*.5,low.z));matrix=obj.matrix_world.copy()
    for v in obj.data.vertices:
        v.co=matrix@v.co-centre
        if mirrored:v.co.x=-v.co.x
    obj.matrix_world=Matrix.Identity(4)
    if mirrored:
        mesh=bmesh.new();mesh.from_mesh(obj.data);bmesh.ops.reverse_faces(mesh,faces=list(mesh.faces));mesh.to_mesh(obj.data);mesh.free();obj.data.update()
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.separate(type='MATERIAL');bpy.ops.object.mode_set(mode='OBJECT')
    parts=list(bpy.context.selected_objects)
    return parts,{'sourceVariant':variant,'mirrored':mirrored,'heightMetres':high.z-low.z,'sourceBoundsBlenderZUp':{'min':list(low),'max':list(high)},'sourceCentreBlenderZUp':list(centre),'cardSpanMetres':(high.z-low.z)*1.10}
def image(path,srgb):
    im=bpy.data.images.load(str(path),check_existing=True);im.colorspace_settings.name='sRGB' if srgb else 'Non-Color';return im
def triangles(obj):return sum(len(p.vertices)-2 for p in obj.data.polygons)
