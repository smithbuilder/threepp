using System;
using System.Linq;
using System.Collections.Generic;
using Cinder.Sim;
using Cinder.Host;
using UnityEngine;
using UnityEngine.Rendering;
namespace Cinder.View {
 public sealed class CinderView:IDisposable {
  public Transform Root {get;private set;}public Transform Car {get;private set;}public long Triangles;public int Renderers;
  readonly VehicleSim sim;readonly int world;readonly Dictionary<string,Transform> nodes=new Dictionary<string,Transform>();
  readonly Dictionary<Transform,Vector3> rest=new Dictionary<Transform,Vector3>();readonly Dictionary<Transform,Quaternion> restQ=new Dictionary<Transform,Quaternion>();
  readonly List<UnityEngine.Object> owned=new List<UnityEngine.Object>();
  readonly RigMechanisms mechanisms;
  readonly HashSet<string> viewPoseNames=new HashSet<string>(StringComparer.Ordinal);
  readonly List<(Transform,RigMechanisms)> lods=new List<(Transform,RigMechanisms)>();
  readonly List<(SkinnedMeshRenderer Renderer,MeshFilter[] Sources)> rigidBatches=new List<(SkinnedMeshRenderer,MeshFilter[])>();
  float panelPhase,roofPhase;
  Transform[] wheels=new Transform[4],spins=new Transform[4],steers=new Transform[4];
  readonly List<MeshRenderer> contactGround=new List<MeshRenderer>();
  readonly MaterialPropertyBlock contactProperties=new MaterialPropertyBlock();
  readonly Vector4[] contacts=new Vector4[4],contactAxes=new Vector4[4];
  public Vector4[] ContactFootprints=>(Vector4[])contacts.Clone();
  public static Vector3 V(DVec3 v)=>new Vector3((float)v.X,(float)v.Y,(float)v.Z);public static Quaternion Q(DQuat q)=>new Quaternion((float)q.X,(float)q.Y,(float)q.Z,(float)q.W);
  public CinderView(ModuleContext ctx,VehicleSim simulation,int selectedWorld){
   sim=simulation;world=selectedWorld;Root=new GameObject("Cinder module view").transform;if(ctx.World!=null)Root.SetParent(ctx.World.Root,false);Root.localPosition=ctx.Frame.Origin;Root.localRotation=ctx.Frame.Rotation;Root.localScale=Vector3.one*ctx.Frame.Scale;
   if(world!=1)BuildGround();var environment=SpawnKit(world==1?(CityEveningLighting.SunsetCity(world)?"mercer-city-sunset":"mercer-city"):"playground-kit",Root);if(world==1)foreach(var renderer in environment.GetComponentsInChildren<MeshRenderer>()){renderer.shadowCastingMode=ShadowCastingMode.Off;renderer.receiveShadows=renderer.transform.name.StartsWith("ground.",StringComparison.Ordinal);}
   if(world==1)foreach(var r in environment.GetComponentsInChildren<MeshRenderer>())if(r.transform.name.StartsWith("ground.",StringComparison.Ordinal))contactGround.Add(r);
   if(CityEveningLighting.SunsetCity(world))foreach(var renderer in environment.GetComponentsInChildren<MeshRenderer>()){
    var materials=renderer.sharedMaterials;bool changed=false;
    for(int i=0;i<materials.Length;i++)if(materials[i]&&materials[i].name=="city.lamp"){
     var lamp=new Material(materials[i]);owned.Add(lamp);bool emission=StandaloneHost.Arg("-city-lighting")!="emission-off";
     lamp.SetColor("_EmissionColor",emission?new Color(5,3.1f,1.35f,1).gamma:Color.black);materials[i]=lamp;changed=true;
    }
    if(changed)renderer.sharedMaterials=materials;
   }

   if(world==1&&StandaloneHost.Has("-local-reflection-diagnostic")){var cube=Resources.Load<Cubemap>("Cinder/city-reflection-filtered");if(!cube)throw new Exception("Missing offline city reflection bake");var local=new GameObject("Mercer fixed reflection");local.transform.SetParent(Root,false);local.transform.localPosition=new Vector3(-31,.85f,65);var probe=local.AddComponent<ReflectionProbe>();probe.mode=ReflectionProbeMode.Custom;probe.customBakedTexture=cube;probe.boxProjection=true;probe.size=new Vector3(35,16,50);probe.center=Vector3.zero;probe.blendDistance=2;probe.importance=10;probe.intensity=1;}
   if(world==2)BuildForest();
   Car=SpawnKit(sim.Tune.Id,Root).transform;
   if(sim.Tune.Id=="safari")SpawnKit("safari-running-gear",Car);
   foreach(var t in Car.GetComponentsInChildren<Transform>(true)){if(!nodes.ContainsKey(t.name))nodes[t.name]=t;rest[t]=t.localPosition;restQ[t]=t.localRotation;}
   string[] labels={"FL","FR","RL","RR"};for(int i=0;i<4;i++){
    wheels[i]=Find(sim.Tune.Id=="baja"?"wheel."+labels[i]+".steer":sim.Tune.Id=="switchback"?"corner."+labels[i]:"wheel_"+i);
    spins[i]=Find(sim.Tune.Id=="baja"?"wheel."+labels[i]+".roll":sim.Tune.Id=="switchback"?"hub."+labels[i]+".spin":"wheel_"+i+"_spin");steers[i]=Find("wheel_"+i+"_steer");
    if(wheels[i]==null||spins[i]==null)throw new Exception("Missing moving wheel pivot "+sim.Tune.Id+" corner "+i);
   }
   foreach(var mf in Root.GetComponentsInChildren<MeshFilter>()){Triangles+=mf.sharedMesh.triangles.Length/3;}Renderers=Root.GetComponentsInChildren<MeshRenderer>().Length;
   mechanisms=new RigMechanisms(Car,sim.Tune.Id);Pose(sim.State);Panels(1,1);Panels(0,0);if(sim.State.Vehicle>=4){BatchFixedBody(Car,mechanisms);foreach(string suffix in new[]{"-mid","-far"}){string key=sim.Tune.Id+suffix;var prefab=Resources.Load<GameObject>("Cinder/Generated/"+key+"/"+key);if(prefab){var t=UnityEngine.Object.Instantiate(prefab,Root,false).transform;var rig=new RigMechanisms(t,sim.Tune.Id);t.localPosition=Car.localPosition;t.localRotation=Car.localRotation;rig.Pose(sim.State,sim.Tune);rig.PosePanels(1,1);rig.PosePanels(0,0);BatchFixedBody(t,rig);lods.Add((t,rig));t.gameObject.SetActive(false);}}}Pose(sim.State);
  }
  GameObject SpawnKit(string id,Transform parent){var prefab=Resources.Load<GameObject>("Cinder/Generated/"+id+"/"+id);if(!prefab)throw new Exception("Missing authored kit "+id+". Run guarded builder.");return UnityEngine.Object.Instantiate(prefab,parent,false);}
  Material GroundMaterial(){var m=new Material(Shader.Find("Cinder/Body")){color=world==1?Color.white:new Color(.6f,.53f,.40f)};m.mainTexture=Resources.Load<Texture2D>(world==1?"Cinder/City/ph-asphalt-color":"Cinder/gravel");m.SetFloat("_Glossiness",.13f);owned.Add(m);return m;}
  void BatchFixedBody(Transform car,RigMechanisms rig){
   // Each rigid attachment is a single-weight bone. This merges matching
   // materials across moving parts while retaining their actual rig transforms.
   // Flexible meshes and scaled spring owners keep their live mesh renderers.
   var groups=new Dictionary<(Material Material,ShadowCastingMode Shadow,int Attributes),List<(MeshRenderer Renderer,Transform Owner)>>();
   foreach(var r in car.GetComponentsInChildren<MeshRenderer>()){
    if(r.sharedMaterial.renderQueue>=3000){r.shadowCastingMode=ShadowCastingMode.Off;continue;}
    var source=r.GetComponent<MeshFilter>();if(!source||rig.IsDeformedMesh(source.sharedMesh))continue;
    if(r.bounds.size.magnitude<.18f)r.shadowCastingMode=ShadowCastingMode.Off;
    bool visibilitySwitched=false;for(var t=r.transform;t&&t!=car;t=t.parent)visibilitySwitched|=rig.IsVisibilityBinding(t);if(visibilitySwitched)continue;
    Transform owner=car;for(var t=r.transform;t&&t!=car;t=t.parent)if(rig.IsPoseBinding(t)||viewPoseNames.Contains(t.name)){owner=t;break;}
    Vector3 scale=owner.localScale;if(Mathf.Abs(scale.x-scale.y)>1e-5f||Mathf.Abs(scale.y-scale.z)>1e-5f)continue;
    int mask=0;foreach(VertexAttribute attribute in new[]{VertexAttribute.Normal,VertexAttribute.Tangent,VertexAttribute.Color,VertexAttribute.TexCoord0})if(source.sharedMesh.HasVertexAttribute(attribute))mask|=1<<(int)attribute;
    var key=(r.sharedMaterial,r.shadowCastingMode,mask);if(!groups.TryGetValue(key,out var group))groups[key]=group=new List<(MeshRenderer,Transform)>();group.Add((r,owner));
   }
   foreach(var pair in groups){if(pair.Value.Count<2)continue;
    var items=pair.Value.Select(item=>new CombineInstance{mesh=item.Renderer.GetComponent<MeshFilter>().sharedMesh,transform=car.worldToLocalMatrix*item.Renderer.transform.localToWorldMatrix}).ToArray();
    var mesh=new Mesh{name="Rigid bone batch / "+pair.Key.Material.name,indexFormat=IndexFormat.UInt32};mesh.CombineMeshes(items,true,true);
    var bones=pair.Value.Select(item=>item.Owner).Distinct().ToArray();var indices=new Dictionary<Transform,int>();for(int i=0;i<bones.Length;i++)indices[bones[i]]=i;
    var weights=new BoneWeight[mesh.vertexCount];int offset=0;foreach(var item in pair.Value){int bone=indices[item.Owner],count=item.Renderer.GetComponent<MeshFilter>().sharedMesh.vertexCount;for(int i=0;i<count;i++)weights[offset++]=new BoneWeight{boneIndex0=bone,weight0=1};}
    if(offset!=weights.Length)throw new InvalidOperationException("Rigid bone batch changed source vertex count");
    mesh.boneWeights=weights;mesh.bindposes=bones.Select(bone=>bone.worldToLocalMatrix*car.localToWorldMatrix).ToArray();mesh.RecalculateBounds();owned.Add(mesh);
    var g=new GameObject("Rigid material batch / "+pair.Key.Material.name);g.transform.SetParent(car,false);var renderer=g.AddComponent<SkinnedMeshRenderer>();renderer.sharedMesh=mesh;renderer.sharedMaterial=pair.Key.Material;renderer.shadowCastingMode=pair.Key.Shadow;
    renderer.bones=bones;renderer.rootBone=car;renderer.quality=SkinQuality.Bone1;renderer.updateWhenOffscreen=true;renderer.localBounds=new Bounds(new Vector3(0,.8f,0),new Vector3(7,7,9));
    rigidBatches.Add((renderer,pair.Value.Select(item=>item.Renderer.GetComponent<MeshFilter>()).ToArray()));foreach(var item in pair.Value)item.Renderer.enabled=false;
   }
  }
  // Functional geometry invariant used by the headless runtime-batch probe.
  // Sources remain in the rig hierarchy and receive the authoritative poses;
  // their disabled renderers are compared with the visible combined geometry.
  public double ValidateRigidBatches(out int batches){
   batches=0;double maximum=0;
   foreach(var binding in rigidBatches){if(!binding.Renderer.enabled||!binding.Renderer.gameObject.activeInHierarchy)continue;batches++;
    var snapshot=new Mesh();binding.Renderer.BakeMesh(snapshot,true);var combined=snapshot.vertices;UnityEngine.Object.DestroyImmediate(snapshot);int offset=0;
    foreach(var source in binding.Sources){if(!source.gameObject.activeInHierarchy)return double.PositiveInfinity;foreach(var point in source.sharedMesh.vertices){if(offset>=combined.Length)return double.PositiveInfinity;var expected=source.transform.TransformPoint(point);var actual=binding.Renderer.transform.TransformPoint(combined[offset++]);double error=Vector3.Distance(expected,actual);if(double.IsNaN(error)||double.IsInfinity(error))return double.PositiveInfinity;maximum=Math.Max(maximum,error);}}
    if(offset!=combined.Length)return double.PositiveInfinity;
   }
   return maximum;
  }
  void BuildGround(){
   var t=sim.Terrain;var mesh=new Mesh{name="Shared sampled contact surface",indexFormat=IndexFormat.UInt32};int nx=TerrainModel.Nx,nz=TerrainModel.Nz;var v=new Vector3[(nx+1)*(nz+1)];var uv=new Vector2[v.Length];var colors=new Color[v.Length];var ix=new int[nx*nz*6];
   for(int z=0;z<=nz;z++)for(int x=0;x<=nx;x++){int i=z*(nx+1)+x;float px=(float)(TerrainModel.MinX+x*TerrainModel.Step),pz=(float)(TerrainModel.MinZ+z*TerrainModel.Step);v[i]=new Vector3(px,(float)t.VertexHeight(x,z),pz);uv[i]=new Vector2(px*.24f,pz*.24f);float lane=world==1?1:Mathf.Lerp(.68f,1,Mathf.Clamp01(Mathf.Abs(Mathf.Sin(px*.05f))));colors[i]=new Color(lane,lane,lane);}
   int k=0;for(int z=0;z<nz;z++)for(int x=0;x<nx;x++){int a=z*(nx+1)+x,b=a+1,c=a+nx+1,d=c+1;ix[k++]=a;ix[k++]=c;ix[k++]=b;ix[k++]=b;ix[k++]=c;ix[k++]=d;}mesh.vertices=v;mesh.uv=uv;mesh.colors=colors;mesh.triangles=ix;mesh.RecalculateNormals();mesh.RecalculateBounds();owned.Add(mesh);var g=new GameObject("Authoritative terrain");g.transform.SetParent(Root,false);g.AddComponent<MeshFilter>().sharedMesh=mesh;var groundRenderer=g.AddComponent<MeshRenderer>();var asphalt=GroundMaterial();groundRenderer.sharedMaterial=asphalt;if(world==1){var roadIndices=new List<int>();var paveIndices=new List<int>();for(int j=0;j<ix.Length;j+=3){var list=Mathf.Min(v[ix[j]].y,Mathf.Min(v[ix[j+1]].y,v[ix[j+2]].y))>.12f?paveIndices:roadIndices;list.Add(ix[j]);list.Add(ix[j+1]);list.Add(ix[j+2]);}mesh.subMeshCount=2;mesh.SetTriangles(roadIndices,0);mesh.SetTriangles(paveIndices,1);var paving=new Material(Shader.Find("Cinder/Body")){color=new Color(.55f,.55f,.55f),mainTexture=Resources.Load<Texture2D>("Cinder/City/paving")};paving.SetFloat("_Glossiness",.1f);owned.Add(paving);groundRenderer.sharedMaterials=new[]{asphalt,paving};}
  }
  void BuildForest(){var tree=Resources.Load<GameObject>("Cinder/Generated/conifer/conifer");if(!tree)return;var rng=new System.Random(619);for(int i=0;i<70;i++){float x=(float)(rng.NextDouble()*122-61),z=(float)(rng.NextDouble()*190);if(Mathf.Abs(x+50)<6||Mathf.Abs(x+25)<5||Mathf.Abs(x)<9||Mathf.Abs(x-25)<7||Mathf.Abs(x-50)<7)continue;var t=UnityEngine.Object.Instantiate(tree,Root).transform;t.localPosition=new Vector3(x,(float)sim.Terrain.Height(x,z),z);t.localRotation=Quaternion.Euler(0,rng.Next(360),0);t.localScale=Vector3.one*(.6f+(float)rng.NextDouble()*.35f);}}
  Transform Find(string n){if(!nodes.TryGetValue(n,out var t))return null;viewPoseNames.Add(n);return t;}
  void Point(Transform t,Vector3 p){if(t)t.position=Car.TransformPoint(p);}
  void Rotate(Transform t,Quaternion q){if(t)t.rotation=Car.rotation*q;}
  void Link(string name,Vector3 a,Vector3 b,Vector3 oldEnd){var t=Find(name);if(!t)return;Vector3 original=rest[t];Point(t,a);Rotate(t,Quaternion.FromToRotation(oldEnd-original,b-a));}
  void LinkMarker(string name,string marker,Vector3 endpoint){var t=Find(name);var m=Find(marker);if(!t||!m)return;var a=rest[t];Vector3 dir=rest[m];Point(t,a);Rotate(t,Quaternion.FromToRotation(dir,endpoint-a));}
  public void Pose(SimState s){
   Car.localPosition=V(s.Position);Car.localRotation=Q(s.Rotation);string id=sim.Tune.Id;
   if(id=="media-luna"||id=="nocturne"){
    var axle=id=="nocturne"?WheelKinematics.NocturneRear(s.Travel[2],s.Travel[3]):WheelKinematics.LunaRear(s.Travel[2],s.Travel[3]);Point(Find("rear_axle"),V(axle.Center));Rotate(Find("rear_axle"),Q(axle.Rotation));if(id=="media-luna")Rotate(Find("torque_tube"),Q(axle.Tube));
   }else if(id=="baja"||id=="catrina"){var axle=id=="baja"?WheelKinematics.BajaRear(s.Travel[2],s.Travel[3]):WheelKinematics.CatrinaRear(s.Travel[2],s.Travel[3]);Point(Find("rear_axle"),V(axle.Center));Rotate(Find("rear_axle"),Q(axle.Rotation));}
   for(int i=0;i<4;i++){
    var pose=WheelKinematics.Pose(sim.Tune,i,s.Travel,s.Steer);var hub=V(s.WheelLocal[i]);Point(wheels[i],hub);Rotate(wheels[i],steers[i]&&i<2?Quaternion.identity:Q(pose.Rotation));if(steers[i])steers[i].localRotation=i<2?Q(pose.Rotation):Quaternion.identity;spins[i].localRotation=restQ[spins[i]]*Quaternion.AngleAxis((float)s.Spin[i]*Mathf.Rad2Deg,Vector3.right);
    var brake=Find("brake_"+i+"_spin")??Find("brake."+new[]{"FL","FR","RL","RR"}[i]+".rotor");if(brake)brake.localRotation=Quaternion.AngleAxis((float)s.Spin[i]*Mathf.Rad2Deg,Vector3.right);
    if(i<2&&(id=="media-luna"||id=="nocturne")){
     LinkMarker("front_lower_"+i,"lower_ball_"+i,V(pose.Low));LinkMarker("front_upper_"+i,"upper_ball_"+i,V(pose.High));Point(Find("knuckle_"+i),V(pose.Center));Rotate(Find("knuckle_"+i),Q(pose.Rotation));
     var lower=Find("front_lower_"+i);var tension=Find("tension_"+i);if(tension&&lower)Link("tension_"+i,rest[tension],V(pose.Low),rest[lower]+rest[Find("lower_ball_"+i)]);
    }
    if(i<2&&id=="catrina"){
     float sign=i==0?-1:1;var low=V(pose.Low);var high=V(pose.High);Link("front_"+i+"_lower",new Vector3(sign*.18f,.25f,1.5113f),low,new Vector3(sign*.715f,.25f,1.5113f));Link("front_"+i+"_upper",new Vector3(sign*.18f,.43f,1.5113f),high,new Vector3(sign*.715f,.43f,1.5113f));Point(Find("upright_"+i),hub);Rotate(Find("upright_"+i),Q(pose.Rotation));
    }
    // Translation belongs to the inner rod; casing length is always preserved.
    var casing=Find("damper_"+i);var rod=Find("damper_"+i+"_rod");var marker=Find("damper_mount_"+i);if(casing&&rod&&marker){Vector3 a=rest[casing],b=Car.InverseTransformPoint(marker.position),old=rest[rod];Point(casing,a);Rotate(casing,Quaternion.FromToRotation(old,b-a));rod.localPosition=old.normalized*Vector3.Distance(a,b);}
   }
   mechanisms.Pose(s,sim.Tune);
   PoseContactLighting(s);
   foreach(var lod in lods){lod.Item1.localPosition=Car.localPosition;lod.Item1.localRotation=Car.localRotation;if(lod.Item1.gameObject.activeSelf){lod.Item2.Pose(s,sim.Tune);lod.Item2.PosePanels(panelPhase,roofPhase);}}
  }
  void PoseContactLighting(SimState s){
   if(contactGround.Count==0)return;
   // View-only approximation of indirect occlusion at the actual tread support.
   // Re-sample the posed tread, rather than sticking a shadow under an airborne
   // hub. The sim remains authoritative; this never writes its state or forces.
   for(int i=0;i<4;i++){
    var pose=WheelKinematics.Pose(sim.Tune,i,s.Travel,s.Steer);var hub=s.Position+s.Rotation.Rotate(s.WheelLocal[i]);
    double gap=double.PositiveInfinity;DVec3 point=DVec3.Zero;
    for(int row=-1;row<=1;row++)for(int arc=-3;arc<=3;arc++){
     double a=arc*.24;var tread=hub+s.Rotation.Rotate(pose.Rotation.Rotate(new DVec3(row*sim.Tune.TyreHalfWidth*.70,-sim.Tune.TyreRadius*Math.Cos(a),sim.Tune.TyreRadius*Math.Sin(a))));
     double h=sim.Terrain.Height(tread.X,tread.Z),distance=tread.Y-h;
     if(distance<gap){gap=distance;point=new DVec3(tread.X,h,tread.Z);}
    }
    float weight=s.Grounded[i]?1-Mathf.SmoothStep(0,1,Mathf.InverseLerp(.015f,.12f,(float)Math.Max(0,gap))):0;
    contacts[i]=new Vector4((float)point.X,(float)point.Y,(float)point.Z,weight);
    var direction=s.Rotation.Rotate(pose.Rotation.Rotate(new DVec3(0,0,1)));var axis=new Vector2((float)direction.X,(float)direction.Z).normalized;
    contactAxes[i]=new Vector4(axis.x,axis.y,(float)sim.Tune.TyreHalfWidth+.12f,.32f);
   }
   string control=StandaloneHost.Arg("-lighting-control","none");
   contactProperties.SetFloat("_CinderContactEnabled",control=="legacy"||control=="contact-off"?0:1);
   contactProperties.SetMatrix("_CinderWorldToModule",Root.worldToLocalMatrix);
   contactProperties.SetVectorArray("_CinderContacts",contacts);contactProperties.SetVectorArray("_CinderContactAxes",contactAxes);
   foreach(var r in contactGround)r.SetPropertyBlock(contactProperties);
  }
  public void Panels(float openness,float roofT){panelPhase=openness;roofPhase=roofT;mechanisms.PosePanels(openness,roofT);foreach(var lod in lods)if(lod.Item1.gameObject.activeSelf)lod.Item2.PosePanels(openness,roofT);}
  Vector3 ExteriorCameraPosition(Vector3 desired){
   // Clamp in the module's terrain frame after every camera convention override.
   // Keep at least .35 module metres and .35 world metres along module up.
   Vector3 point=Root.InverseTransformPoint(desired);float scale=Mathf.Max(.0001f,Root.TransformVector(Vector3.up).magnitude);
   float clearance=.35f/Mathf.Min(1,scale);point.y=Mathf.Max(point.y,(float)sim.Terrain.Height(point.x,point.z)+clearance);return Root.TransformPoint(point);
  }
  public void GarageCamera(Camera camera,float orbit){Vector3 aim=Car.TransformPoint(new Vector3(0,.65f,0));Vector3 local=Quaternion.Euler(0,(orbit-24)*.35f,0)*(CityEveningLighting.SunsetCity(world)?new Vector3(-6.8f,2.8f,5.4f):new Vector3(-5.4f,1.9f,6.2f));camera.transform.position=ExteriorCameraPosition(Car.TransformPoint(local));camera.transform.LookAt(aim,Root.up);camera.transform.LookAt(aim-camera.transform.right*2.65f+Root.up*.25f,Root.up);camera.fieldOfView=48;camera.nearClipPlane=.06f;camera.farClipPlane=450;Car.gameObject.SetActive(true);foreach(var lod in lods)lod.Item1.gameObject.SetActive(false);}
  public void Camera(Camera camera,int mode,float yaw,float pitch){
   Vector3 aim=Car.TransformPoint(new Vector3(0,.8f,0));Vector3 local;
   switch(mode){case 7:local=new Vector3(-9,2.6f,12);aim=Car.TransformPoint(new Vector3(0,2.6f,-12));break;case 1:local=new Vector3(5,1.0f,1.4f);break;case 2:local=new Vector3(-4,1.6f,5);break;case 3:local=new Vector3(0,12,-7);break;case 4:local=new Vector3(2.4f,.68f,(float)sim.Tune.HalfWheelbase);aim=Car.TransformPoint(new Vector3(0,.42f,(float)sim.Tune.HalfWheelbase));break;case 5:local=new Vector3(2.5f,.7f,-(float)sim.Tune.HalfWheelbase);aim=Car.TransformPoint(new Vector3(0,.45f,-(float)sim.Tune.HalfWheelbase));break;case 6:local=new Vector3(-.36f,1.18f,-.38f);aim=Car.TransformPoint(new Vector3(-.36f,1.05f,15));break;default:local=Quaternion.Euler(pitch,yaw,0)*new Vector3(0,1.5f,-7);break;}
   Vector3 desired=Car.TransformPoint(local);camera.fieldOfView=mode==6?73:mode==7?58:48;camera.nearClipPlane=.06f;camera.farClipPlane=450;
   // Native lowrider review camera convention, retained for direct art comparisons.
   if(sim.State.Vehicle>=4&&mode<=2){string id=sim.Tune.Id;float fov=48;Vector3 eye=local;Vector3 target=new Vector3(0,id=="catrina"?.65f:id=="media-luna"?.78f:.45f,0);
    if(id=="catrina"){eye=mode==0?new Vector3(-3.8f,3.1f,-6.3f):mode==1?new Vector3(-5.6f,1.25f,3.2f):new Vector3(-3.9f,3.1f,5.8f);fov=mode==1?39:42;}
    if(id=="media-luna"){eye=mode==0?new Vector3(-3.4f,2.4f,-8.2f):mode==1?new Vector3(-5.65f,1.18f,3.25f):new Vector3(-2.6f,1.8f,7.4f);fov=mode==1?35:42;}
    if(id=="nocturne"){eye=mode==0?new Vector3(-4,2.6f,-8.5f):mode==1?new Vector3(-7.4f,1.5f,4.2f):new Vector3(-3.5f,2,8.2f);fov=mode==0?39:mode==1?36:38;}
    desired=Car.TransformPoint(eye);aim=Car.TransformPoint(target);camera.fieldOfView=fov;
   }
   if(world==1&&mode==3){desired=Root.TransformPoint(new Vector3(-69,64,1));aim=Root.TransformPoint(new Vector3(0,3,70));camera.fieldOfView=48;}
   camera.transform.position=mode==6?desired:ExteriorCameraPosition(desired);camera.transform.LookAt(aim,Root.up);
   int tier=Vector3.Distance(camera.transform.position,Car.position)>28?2:Vector3.Distance(camera.transform.position,Car.position)>12?1:0;Car.gameObject.SetActive(tier==0||lods.Count<2);for(int i=0;i<lods.Count;i++){bool active=tier==i+1;if(active&&!lods[i].Item1.gameObject.activeSelf){lods[i].Item2.Pose(sim.State,sim.Tune);lods[i].Item2.PosePanels(panelPhase,roofPhase);}lods[i].Item1.gameObject.SetActive(active);}
  }
  public void MeasureBudget(out long triangles,out int renderers){triangles=0;renderers=0;foreach(var mf in Root.GetComponentsInChildren<MeshFilter>()){var r=mf.GetComponent<MeshRenderer>();if(!r||!r.enabled)continue;if(r.isPartOfStaticBatch){for(int k=0;k<r.sharedMaterials.Length;k++){int sub=r.subMeshStartIndex+k;if(sub<mf.sharedMesh.subMeshCount)triangles+=(long)mf.sharedMesh.GetIndexCount(sub)/3;}}else{for(int sub=0;sub<mf.sharedMesh.subMeshCount;sub++)triangles+=(long)mf.sharedMesh.GetIndexCount(sub)/3;}renderers++;}foreach(var r in Root.GetComponentsInChildren<SkinnedMeshRenderer>()){if(!r.enabled||!r.sharedMesh)continue;for(int sub=0;sub<r.sharedMesh.subMeshCount;sub++)triangles+=(long)r.sharedMesh.GetIndexCount(sub)/3;renderers++;}}
  public void Dispose(){mechanisms?.Dispose();foreach(var lod in lods)lod.Item2.Dispose();if(Root)UnityEngine.Object.Destroy(Root.gameObject);foreach(var x in owned)UnityEngine.Object.Destroy(x);Root=null;Car=null;}
 }
}
