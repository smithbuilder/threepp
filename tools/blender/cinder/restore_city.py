"""Blender 4.5 verification of the faithful native Mercer data asset.

Run headlessly through the shared guarded offline-tool runner. This script does
not alter the authoritative GLB. It validates imported meshes/colour/materials,
keeps an editable .blend beside its report, and fails closed on content drift.
"""
import bpy,json,sys,math,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3]
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
source=Path(args[0]) if args else ROOT/'assets/unity/city/mercer-city.glb'
output=Path(args[1]) if len(args)>1 else ROOT/'build/cinder-city-export/blender-verified-v1'
if bpy.app.version[:2]!=(4,5):raise RuntimeError('Blender4.5 required')
if output.exists():raise RuntimeError('Preserve existing verification output; choose a new folder')
output.mkdir(parents=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(source))
manifest=json.loads((ROOT/'assets/unity/city/manifest.json').read_text())
expected={m['name']:m for m in manifest['meshes']}
meshes={o.name:o for o in bpy.context.scene.objects if o.type=='MESH'}
if set(meshes)!=set(expected):raise RuntimeError('Native city mesh identities changed in Blender import')
rows=[]
for name,obj in meshes.items():
    mesh=obj.data;mesh.calc_loop_triangles();triangles=len(mesh.loop_triangles)
    if triangles!=expected[name]['triangles']:raise RuntimeError('Triangle count mismatch '+name)
    if len(mesh.vertices)!=expected[name]['vertices']:raise RuntimeError('Vertex count mismatch '+name)
    if len(mesh.color_attributes)==0:raise RuntimeError('Baked native colour data missing '+name)
    if len(mesh.uv_layers)!=1:raise RuntimeError('NativeUV layer count mismatch '+name)
    if len(mesh.materials)!=1 or mesh.materials[0].name!=expected[name]['material']:raise RuntimeError('Material identity missing '+name)
    low=[min((obj.matrix_world@v.co)[i] for v in mesh.vertices) for i in range(3)];high=[max((obj.matrix_world@v.co)[i] for v in mesh.vertices) for i in range(3)]
    if not all(math.isfinite(c) for c in low+high):raise RuntimeError('Nonfinite city bounds')
    rows.append({'name':name,'triangles':triangles,'vertices':len(mesh.vertices),'nativeMaterial':mesh.materials[0].name,'colourLayers':[c.name for c in mesh.color_attributes],'boundsBlenderZUp':[low,high]})
if sum(r['triangles'] for r in rows)!=manifest['triangles']:raise RuntimeError('Total triangles changed')
bpy.ops.wm.save_as_mainfile(filepath=str(output/'Mercer-City-Restored.blend'))
report={'success':True,'blender':bpy.app.version_string,'glb':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'triangles':manifest['triangles'],'meshCount':len(rows),'materialCount':len(bpy.data.materials),'checks':['Exact mesh identities','Exact per-mesh vertex and triangle counts','Native baked colour layers present','Native UV layer and material identities present','Finite imported bounds'],'meshes':rows,'scope':'Offline Blender import validation. No image rendered and no visual acceptance claim. Authoritative GLB unchanged.'}
(output/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS nativeMercer Blender verification',manifest['triangles'],'triangles',len(rows),'meshes')
