using System;
using System.Collections.Generic;
using Cinder.Sim;
using UnityEngine;

namespace Cinder.View {
    // The mesh adapter consumes the authoritative sim pose. Linkages and flexible
    // parts follow donor bind pivots; no view calculation feeds vehicle physics.
    public sealed class RigMechanisms : IDisposable {
        readonly Transform car;readonly string id;
        readonly Transform[] hierarchy;
        readonly Dictionary<string,Transform> nodes=new Dictionary<string,Transform>();
        readonly Dictionary<Transform,Vector3> local=new Dictionary<Transform,Vector3>(),bind=new Dictionary<Transform,Vector3>();
        readonly Dictionary<Transform,Quaternion> rotations=new Dictionary<Transform,Quaternion>();
        readonly List<Mesh> owned=new List<Mesh>();
        readonly Dictionary<Transform,List<Deform>> axial=new Dictionary<Transform,List<Deform>>();
        readonly List<Deform>[] coils={new List<Deform>(),new List<Deform>()},leaves={new List<Deform>(),new List<Deform>()};
        readonly List<Deform>[] bags={new List<Deform>(),new List<Deform>(),new List<Deform>(),new List<Deform>()};
        readonly List<Deform>[] cloth={new List<Deform>(),new List<Deform>(),new List<Deform>()};
        // Donor full droop demanded 6.655 mm more leaf chord than its fixed
        // shackle circle permits. A 10 mm forward installation correction makes
        // the complete legal travel feasible while retaining both steel lengths.
        static readonly Vector3 LunaLeafBracketCorrection=new Vector3(0,0,.010f);
        float panels,roof;
        sealed class Deform {
            public Mesh Mesh;public Transform Node;public Vector3[] Rest,Work;public Vector2[] UV;public Matrix4x4 ToMesh;public bool Rubber;
            public void Set(int i,Vector3 ownerPoint) {Work[i]=ToMesh.MultiplyPoint3x4(ownerPoint);}
            public void Apply(bool normals=false) {Mesh.vertices=Work;if(normals)Mesh.RecalculateNormals();Mesh.RecalculateBounds();}
        }
        static Vector3 V(DVec3 p) {return new Vector3((float)p.X,(float)p.Y,(float)p.Z);}
        static Quaternion Q(DQuat p) {return new Quaternion((float)p.X,(float)p.Y,(float)p.Z,(float)p.W);}
        static Quaternion Aim(Vector3 old,Vector3 next) {return old.sqrMagnitude<1e-12f||next.sqrMagnitude<1e-12f?Quaternion.identity:Quaternion.FromToRotation(old,next);}
        readonly HashSet<Transform> poseBindings=new HashSet<Transform>();
        readonly HashSet<Transform> visibilityBindings=new HashSet<Transform>();
        public bool IsVisibilityBinding(Transform node)=>visibilityBindings.Contains(node);
        void SetVisibility(Transform node,bool visible){visibilityBindings.Add(node);node.gameObject.SetActive(visible);}
        public bool IsPoseBinding(Transform node)=>poseBindings.Contains(node);
        public bool IsDeformedMesh(Mesh mesh)=>owned.Contains(mesh);
        Transform Find(string name) {nodes.TryGetValue(name,out var t);if(t)poseBindings.Add(t);return t;}
        Transform Need(string name) {var t=Find(name);if(!t)throw new InvalidOperationException("Missing "+id+" moving mechanism: "+name);return t;}
        Vector3 B(string name) {return bind[Need(name)];}
        Vector3 L(string name) {return local[Need(name)];}
        Vector3 P(string name) {return car.InverseTransformPoint(Need(name).position);}
        Quaternion R(string name) {return Quaternion.Inverse(car.rotation)*Need(name).rotation;}
        void Point(string name,Vector3 point) {var t=Find(name);if(t)t.position=car.TransformPoint(point);}
        void Rotate(string name,Quaternion rotation) {var t=Find(name);if(t)t.rotation=car.rotation*rotation;}
        void ResetLocal(string name) {var t=Find(name);if(t){t.localPosition=local[t];t.localRotation=rotations[t];t.localScale=Vector3.one;}}
        public RigMechanisms(Transform car,string id) {
            this.car=car?car:throw new ArgumentNullException("car");this.id=id;
            hierarchy=car.GetComponentsInChildren<Transform>(true);
            foreach(var t in hierarchy)if(!nodes.ContainsKey(t.name))nodes[t.name]=t;
            // The donor hides the assembled roof at rest with a .001 root scale.
            // Those are visibility switches, not authored dimensions. Restore the
            // full mechanical frame before measuring any bind points or vertices.
            if(id=="nocturne")foreach(string name in new[]{"roof_root","roof_lift_0","roof_lift_1"})Need(name).localScale=Vector3.one;
            foreach(var t in hierarchy){local[t]=t.localPosition;bind[t]=car.InverseTransformPoint(t.position);rotations[t]=t.localRotation;}
            if(id=="media-luna") {
                for(int i=0;i<2;i++){Capture("coil_"+i,coils[i]);Capture("leaf_"+i,leaves[i]);foreach(string n in new[]{"front_lower_","front_upper_","knuckle_","tierod_","hydraulic_","spring_perch_","shackle_","axle_seat_"})Need(n+i);}
                Need("rear_axle");Need("torque_tube");
            } else if(id=="nocturne") {
                for(int i=0;i<4;i++){Capture("bag_"+i,bags[i]);Need("bag_lower_"+i);Need("rear_link_"+i);Need("rear_link_end_"+i);Need("damper_"+i);Need("damper_mount_"+i);}
                for(int i=0;i<3;i++)if(Find("roof_cloth_"+i))Capture("roof_cloth_"+i,cloth[i]);
                Need("rear_axle");Need("driveshaft");Need("driveshaft_slip");Need("driveshaft_end");
                for(int i=0;i<3;i++){Need("roof_bow_"+i);Need("roof_cloth_"+i);}
                for(int i=0;i<2;i++){foreach(string name in new[]{"roof_lift_"+i,"roof_lift_"+i+"_rod","roof_lift_"+i+"_stage1","roof_lift_"+i+"_stage2","roof_lift_end_"+i,"deck_actuator_"+i,"deck_actuator_"+i+"_rod","deck_actuator_end_"+i})Need(name);for(int side=0;side<2;side++)for(int half=0;half<2;half++)Need("roof_rail_"+i+"_"+half+(side==0?"_L":"_R"));}
            } else if(id=="catrina") {
                foreach(string name in new[]{"rear_axle","rear_2_lower","rear_3_lower","rear_upper","rear_panhard","driveshaft","driveshaft_slip"})Need(name);
                for(int i=0;i<4;i++){Need("hydraulic_"+i);Need("hydraulic_"+i+"_rod");Need("coil_"+i);Need("coil_"+i+"_seat");}
            }
        }
        void Capture(string name,List<Deform> list) {
            Transform owner=Need(name);
            foreach(var filter in owner.GetComponentsInChildren<MeshFilter>(true)) {
                if(!filter.sharedMesh)continue;Mesh mesh=UnityEngine.Object.Instantiate(filter.sharedMesh);mesh.name=filter.sharedMesh.name+" live "+id;mesh.MarkDynamic();filter.sharedMesh=mesh;owned.Add(mesh);
                Matrix4x4 toOwner=owner.worldToLocalMatrix*filter.transform.localToWorldMatrix;Vector3[] vertices=mesh.vertices,rest=new Vector3[vertices.Length];for(int i=0;i<rest.Length;i++)rest[i]=toOwner.MultiplyPoint3x4(vertices[i]);
                var renderer=filter.GetComponent<MeshRenderer>();bool rubber=renderer&&renderer.sharedMaterial&&renderer.sharedMaterial.name.IndexOf("rubber",StringComparison.OrdinalIgnoreCase)>=0;
                // Unity may rename generated material assets after their file name.
                // The authored glTF part hierarchy preserves the semantic identity.
                for(Transform p=filter.transform;p&&p!=owner;p=p.parent)rubber|=p.name.IndexOf("rubber",StringComparison.OrdinalIgnoreCase)>=0;
                list.Add(new Deform{Mesh=mesh,Node=filter.transform,Rest=rest,Work=vertices,UV=mesh.uv,ToMesh=toOwner.inverse,Rubber=rubber});
            }
            if(list.Count==0)throw new InvalidOperationException("Missing deformable mesh "+id+" / "+name);
        }
        void Link(string name,Vector3 start,Vector3 end,Vector3 restEnd) {Point(name,start);Rotate(name,Aim(restEnd-B(name),end-start));Need(name).localScale=Vector3.one;}
        void Telescope(string casing,string rod,Vector3 endpoint) {
            if(!Find(casing)||!Find(rod))return;Vector3 start=B(casing),rest=L(rod),direction=endpoint-start;Point(casing,start);Rotate(casing,Aim(rest,direction));Need(casing).localScale=Vector3.one;Need(rod).localPosition=rest.normalized*direction.magnitude;Need(rod).localScale=Vector3.one;
        }
        public void Pose(SimState state,VehicleTune tune) {
            if(id=="media-luna"||id=="nocturne")PoseLinkedLowrider(state,tune);
            else if(id=="catrina")PoseCatrina(state,tune);
            else if(id=="baja")PoseBaja(state,tune);
            else if(id=="switchback")PoseSwitchback(state,tune);
            PosePanels(panels,roof);
        }
        void PoseLinkedLowrider(SimState s,VehicleTune tune) {
            bool nocturne=id=="nocturne";Point("steering_rack",new Vector3((nocturne?.12f:.16f)*(float)Math.Sin(s.Steer),B("steering_rack").y,B("steering_rack").z));
            for(int i=0;i<2;i++) {
                string n=i.ToString();WheelPose pose=WheelKinematics.Pose(tune,i,s.Travel,s.Steer);string lower="front_lower_"+n,upper="front_upper_"+n;
                ResetLocal(lower);ResetLocal(upper);Rotate(lower,Aim(L("lower_ball_"+n),V(pose.Low)-B(lower)));Rotate(upper,Aim(L("upper_ball_"+n),V(pose.High)-B(upper)));
                Point("knuckle_"+n,V(pose.Center));Rotate("knuckle_"+n,Q(pose.Rotation));
                string tie="tierod_"+n;Vector3 restTie=B("tierod_end_"+n)-B(tie);Point(tie,V(pose.Rack));Rotate(tie,Aim(restTie,P("tierod_end_"+n)-V(pose.Rack)));
                if(nocturne){string tension="tension_"+n;Rotate(tension,Aim(B("lower_ball_"+n)-B(tension),V(pose.Low)-B(tension)));}
                else PoseLunaCoil(i,(float)s.Actuator[i]*.5f);
            }
            AxlePose rear=nocturne?WheelKinematics.NocturneRear(s.Travel[2],s.Travel[3]):WheelKinematics.LunaRear(s.Travel[2],s.Travel[3]);Point("rear_axle",V(rear.Center));Rotate("rear_axle",Q(rear.Rotation));
            if(nocturne) {
                for(int i=0;i<4;i++){string link="rear_link_"+i;Rotate(link,Aim(V(WheelKinematics.NocturneRearEnd(i)-WheelKinematics.NocturneRearBody(i)),P("rear_link_end_"+i)-B(link)));}
                Vector3 direction=P("driveshaft_end")-B("driveshaft"),rest=new Vector3(0,.348f,-1.3602f)-B("driveshaft");Rotate("driveshaft",Aim(rest,direction)*Quaternion.AngleAxis((float)((s.Spin[2]+s.Spin[3])*.5*2.89)*Mathf.Rad2Deg,rest.normalized));Need("driveshaft_slip").localPosition=rest.normalized*direction.magnitude;
            } else {Rotate("torque_tube",Q(rear.Tube));for(int i=0;i<2;i++)PoseLunaLeaf(i);}
            for(int i=0;i<4;i++) {
                // Authored wheel offsets belong under knuckle / rigid rear axle.
                ResetLocal("wheel_"+i);ResetLocal("wheel_"+i+"_steer");var spin=Need("wheel_"+i+"_spin");spin.localRotation=Quaternion.AngleAxis((float)s.Spin[i]*Mathf.Rad2Deg,Vector3.right);
                Telescope("damper_"+i,"damper_"+i+"_rod",P("damper_mount_"+i));if(nocturne)PoseBag(i);
            }
        }
        void PoseLunaCoil(int i,float stroke) {
            string n=i.ToString();Vector3 seat=P("spring_seat_"+n),basePoint=B("coil_"+n);Point("spring_perch_"+n,seat);Rotate("spring_perch_"+n,Quaternion.identity);Point("coil_"+n,seat);Rotate("coil_"+n,Quaternion.identity);Need("coil_"+n).localScale=Vector3.one;
            Transform rod=Need("hydraulic_"+n+"_rod");Vector3 cup=local[rod];cup.y-=stroke;rod.localPosition=cup;rod.localRotation=rotations[rod];rod.localScale=Vector3.one;
            Vector3 delta=new Vector3(0,-stroke,0)-(seat-basePoint);
            foreach(var wire in coils[i]){if(wire.UV.Length!=wire.Rest.Length)throw new InvalidOperationException("Media Luna coil is missing axial UV stations");for(int j=0;j<wire.Rest.Length;j++)wire.Set(j,wire.Rest[j]+delta*wire.UV[j].x);wire.Apply();}
        }
        void PoseLunaLeaf(int i) {
            string n=i.ToString();Vector3 seat=P("axle_seat_"+n),restSeat=B("axle_seat_"+n),fixedPoint=B("leaf_"+n),bracket=B("shackle_"+n)+LunaLeafBracketCorrection,eyeLocal=L("leaf_eye_"+n),restEye=B("leaf_eye_"+n);
            Point("shackle_"+n,bracket);
            foreach(var t in hierarchy)if(t.name.StartsWith("frame.shackle_bracket",StringComparison.Ordinal))t.position=car.TransformPoint(bind[t]+LunaLeafBracketCorrection);
            float chords=Vector3.Distance(fixedPoint,restSeat)+Vector3.Distance(restSeat,restEye),target=chords-Vector3.Distance(fixedPoint,seat),dx=bracket.x-seat.x,yz2=Mathf.Max(0,target*target-dx*dx),sy=seat.y-bracket.y,sz=seat.z-bracket.z,d=Mathf.Max(1e-7f,Mathf.Sqrt(sy*sy+sz*sz)),radius=eyeLocal.magnitude;
            float along=Mathf.Clamp((radius*radius-yz2+d*d)/(2*d),-radius,radius),across=Mathf.Sqrt(Mathf.Max(0,radius*radius-along*along));Vector3 eyeOffset=new Vector3(0,(along*sy-across*sz)/d,(along*sz+across*sy)/d);Rotate("shackle_"+n,Aim(eyeLocal,eyeOffset));
            Vector3 seatDelta=seat-restSeat,eyeDelta=bracket+eyeOffset-restEye;
            foreach(var mesh in leaves[i]){for(int j=0;j<mesh.Rest.Length;j++){Vector3 p=mesh.Rest[j];float z=fixedPoint.z+p.z;bool behind=z<restSeat.z;float t=behind?(z-restSeat.z)/(restEye.z-restSeat.z):(z-fixedPoint.z)/(restSeat.z-fixedPoint.z),w=Mathf.Clamp01(t),blend=w*w*(3-2*w);mesh.Set(j,behind?p+seatDelta*(1-blend)+eyeDelta*blend:p+seatDelta*blend);}mesh.Apply(true);}
        }
        void PoseBag(int i) {
            string n=i.ToString();Vector3 bottom=P("bag_lower_"+n),oldBottom=B("bag_"+n),top=i<2?new Vector3((i==0?-1:1)*.48f,.525f,1.6002f):new Vector3((i%2==0?-1:1)*.58f,.65f,-1.75f),delta=bottom-oldBottom;float span=top.y-oldBottom.y;
            Quaternion owner=i<2?R("front_lower_"+n):R("rear_axle");Point("bag_"+n,bottom);Rotate("bag_"+n,Quaternion.identity);Need("bag_"+n).localScale=Vector3.one;
            foreach(var mesh in bags[i]){for(int j=0;j<mesh.Rest.Length;j++){Vector3 v=mesh.Rest[j];if(mesh.Rubber){float fraction=Mathf.Clamp01(v.y/span);Vector3 radial=new Vector3(v.x,0,v.z),low=owner*radial,high=radial+new Vector3(0,span,0)-delta;v=Vector3.Lerp(low,high,fraction);}else if(v.y>span*.5f)v-=delta;else v=owner*v;mesh.Set(j,v);}mesh.Apply(mesh.Rubber);}
            Point("lower_bag_plate_"+n,bottom);Rotate("lower_bag_plate_"+n,owner);Point("upper_bag_plate_"+n,top);Rotate("upper_bag_plate_"+n,Quaternion.identity);
        }
        void PoseCatrina(SimState s,VehicleTune tune) {
            Vector3[] springBottom=new Vector3[4];
            for(int i=0;i<2;i++){float sign=i==0?-1:1;WheelPose p=WheelKinematics.Pose(tune,i,s.Travel,s.Steer);Vector3 low=V(p.Low),high=V(p.High),a=new Vector3(sign*.18f,.25f,1.5113f),b=new Vector3(sign*.18f,.43f,1.5113f);Link("front_"+i+"_lower",a,low,new Vector3(sign*.715f,.25f,1.5113f));Link("front_"+i+"_upper",b,high,new Vector3(sign*.715f,.43f,1.5113f));Point("upright_"+i,V(p.Hub));Rotate("upright_"+i,Q(p.Rotation));springBottom[i]=Vector3.LerpUnclamped(a,low,(.55f-.18f)/.535f)+new Vector3(0,.02f,0);}
            AxlePose rear=WheelKinematics.CatrinaRear(s.Travel[2],s.Travel[3]);Vector3 rearCenter=V(rear.Center);Quaternion rearQ=Q(rear.Rotation);Point("rear_axle",rearCenter);Rotate("rear_axle",rearQ);Func<Vector3,Vector3> axlePoint=p=>rearQ*(p-new Vector3(0,.2891f,-1.5113f))+rearCenter;
            string[] links={"rear_2_lower","rear_3_lower","rear_upper","rear_panhard"};for(int i=0;i<4;i++){Vector3 end=V(WheelKinematics.CatrinaRearEnd(i));Link(links[i],V(WheelKinematics.CatrinaRearBody(i)),axlePoint(end),end);}
            for(int i=2;i<4;i++)springBottom[i]=axlePoint(new Vector3((i==2?-1:1)*.56f,.33f,-1.5113f));
            for(int i=0;i<4;i++) {
                float sign=i%2==0?-1:1;string n=i.ToString();WheelPose wheel=WheelKinematics.Pose(tune,i,s.Travel,s.Steer);Point("wheel_"+n,V(wheel.Hub));Rotate("wheel_"+n,i<2?Quaternion.identity:Q(wheel.Rotation));var steering=Find("wheel_"+n+"_steer");if(steering)steering.localRotation=i<2?Q(wheel.Rotation):Quaternion.identity;
                Need("wheel_"+n+"_spin").localRotation=Quaternion.AngleAxis((float)s.Spin[i]*Mathf.Rad2Deg,Vector3.right);var brake=Find("brake_"+n+"_spin");if(brake)brake.localRotation=Quaternion.AngleAxis((float)s.Spin[i]*Mathf.Rad2Deg,Vector3.right);
                string mount=i<2?"front_"+n+"_lower":links[i-2];Vector3 frame=i<2?new Vector3(sign*.48f,.78f,1.6313f):new Vector3(sign*.20f,.50f,-2),offset=i<2?new Vector3(sign*.535f*.38f,.03f,.12f):new Vector3(-sign*.10f,.02f,(-1.5113f+.45f)*.84f);
                Vector3 endpoint=R(mount)*offset+P(mount),axis=(endpoint-frame).normalized,pin=i<2?Vector3.forward:new Vector3(.9f,-.25f,-sign*.35f).normalized;Quaternion aim=AimDamper(axis,pin);Point("damper_"+n,frame);Rotate("damper_"+n,aim);Need("damper_"+n).localScale=Vector3.one;var rod=Need("damper_"+n+"_rod");rod.localPosition=new Vector3(0,-Vector3.Distance(frame,endpoint),0);rod.localRotation=Quaternion.Inverse(aim)*AimDamper(axis,R(mount)*pin);rod.localScale=Vector3.one;
                Vector3 top=new Vector3(sign*(i<2?.55f:.56f),.86f,i<2?1.5113f:-1.5113f),toSeat=springBottom[i]-top;float distance=toSeat.magnitude;Vector3 down=toSeat.normalized;
                Point("hydraulic_"+n,top);Rotate("hydraulic_"+n,Aim(Vector3.down,down));Need("hydraulic_"+n).localScale=Vector3.one;
                float request=.310f+Mathf.Clamp((float)s.Actuator[i]*.42f,0,.244f),upperStop=Mathf.Min(.430f,distance-.114f),cup=Mathf.Clamp(request,.280f,Mathf.Max(.280f,upperStop));var ram=Need("hydraulic_"+n+"_rod");ram.localPosition=new Vector3(0,-cup,0);ram.localRotation=rotations[ram];ram.localScale=Vector3.one;
                Point("coil_"+n,springBottom[i]);Rotate("coil_"+n,Aim(Vector3.up,-down));Need("coil_"+n).localScale=new Vector3(1,(distance-cup)/(i<2?.28f:.22f),1);Point("coil_"+n+"_seat",springBottom[i]);Rotate("coil_"+n+"_seat",Aim(Vector3.up,-down));Need("coil_"+n+"_seat").localScale=Vector3.one;
            }
            Vector3 shaftStart=new Vector3(0,.30f,.59f),shaftEnd=axlePoint(new Vector3(0,.2891f,-1.2913f)),next=shaftEnd-shaftStart;Point("driveshaft",shaftStart);Rotate("driveshaft",Aim(Vector3.up,next));Need("driveshaft").localScale=Vector3.one;Need("driveshaft_slip").localPosition=new Vector3(0,next.magnitude,0);Need("driveshaft_slip").localRotation=Quaternion.identity;Need("driveshaft_slip").localScale=Vector3.one;
        }
        static Quaternion AimDamper(Vector3 axis,Vector3 pin) {Quaternion aim=Aim(Vector3.down,axis);Vector3 current=aim*Vector3.forward,target=(pin-axis*Vector3.Dot(pin,axis)).normalized;float angle=Mathf.Atan2(Vector3.Dot(axis,Vector3.Cross(current,target)),Vector3.Dot(current,target))*Mathf.Rad2Deg;return Quaternion.AngleAxis(angle,axis)*aim;}
        void PoseBaja(SimState s,VehicleTune tune) {
            AxlePose axle=WheelKinematics.BajaRear(s.Travel[2],s.Travel[3]);Quaternion aq=Q(axle.Rotation);Vector3 ac=V(axle.Center);Point("rear_axle",ac);Rotate("rear_axle",aq);Func<Vector3,Vector3> ap=p=>aq*p+ac;
            for(int i=0;i<2;i++){float sign=i==0?-1:1;string side=i==0?"L":"R",front="front."+side,rear="rear."+side;WheelPose p=WheelKinematics.BajaFront(i,s.Travel[i],s.Steer);Quaternion q=Q(p.Rotation);Vector3 low=V(p.Low),high=V(p.High),hub=V(p.Hub);Link(front+".lower_arm",B(front+".lower_arm"),low,new Vector3(sign*.97f,.31f,1.59f));Link(front+".upper_arm",B(front+".upper_arm"),high,new Vector3(sign*.97f,.46f,1.59f));Point(front+".upright",low);Rotate(front+".upright",q);
                Vector3 tieEnd=q*new Vector3(sign*.018f,.03f,-.11f)+low,tieStart=B(front+".tie_rod"),restEnd=new Vector3(sign*.988f,.34f,1.48f);float length=Vector3.Distance(tieStart,restEnd),dy=tieEnd.y-tieStart.y,dz=tieEnd.z-tieStart.z;tieStart.x=tieEnd.x-sign*Mathf.Sqrt(Mathf.Max(.01f,length*length-dy*dy-dz*dz));Link(front+".tie_rod",tieStart,tieEnd,restEnd);Point(front+".rack_slide",new Vector3(tieStart.x-sign*.08f,tieStart.y,tieStart.z));
                BajaExtend(front+".halfshaft",q*new Vector3(sign*-.07f,.09f,0)+low);BajaExtend(front+".coilover",Vector3.LerpUnclamped(B(front+".lower_arm"),low,.81f));BajaExtend(rear+".damper",ap(new Vector3(sign*.76f,.01f,-.17f)));
                for(int j=0;j<2;j++){string name=rear+(j==0?".lower_link":".upper_link");Vector3 end=new Vector3(sign*.77f,j==0?.31f:.49f,-1.59f);Link(name,B(name),ap(new Vector3(sign*.77f,j==0?-.09f:.09f,0)),end);}
                string spring=rear+".spring";Vector3 start=B(spring),restEndSpring=new Vector3(sign*.76f,.44f,-1.59f),target=ap(new Vector3(sign*.76f,.04f,0)),rest=restEndSpring-start;Rotate(spring,Aim(rest,target-start));string lower=rear+".spring.lower_seat",coil=rear+".spring.coil";if(Find(lower))Need(lower).localPosition=rest.normalized*Vector3.Distance(start,target);if(Find(coil))ScaleAlong(Need(coil),rest.normalized,Vector3.Distance(start,target)/rest.magnitude);
                string label=i==0?"FL":"FR";Point("wheel."+label+".steer",hub);Rotate("wheel."+label+".steer",q);
                label=i==0?"RL":"RR";Point("wheel."+label+".steer",ap(new Vector3(sign*1.025f,0,0)));Rotate("wheel."+label+".steer",aq);
            }
            Link("rear.panhard",B("rear.panhard"),ap(new Vector3(.76f,.03f,.23f)),new Vector3(.76f,.43f,-1.36f));BajaExtend("driveline.shaft",ap(new Vector3(0,0,.31f)));
        }
        void BajaExtend(string name,Vector3 endpoint) {
            var node=Find(name);if(!node)return;Vector3 restEnd;if(name.Contains("halfshaft"))restEnd=new Vector3(name.Contains(".R")?.90f:-.90f,.40f,1.59f);else if(name.Contains("coilover"))restEnd=new Vector3(name.Contains(".R")?.9149f:-.9149f,.3024f,1.59f);else if(name.Contains("damper"))restEnd=new Vector3(name.Contains(".R")?.76f:-.76f,.41f,-1.76f);else restEnd=new Vector3(0,.4f,-1.28f);
            Vector3 rest=restEnd-B(name),next=endpoint-B(name);Point(name,B(name));Rotate(name,Aim(rest,next));
            string rodName=name=="driveline.shaft"?"driveline.slip":name.Contains("halfshaft")?name+".slip":name+".shaft";var rod=Find(rodName);if(rod){rod.localPosition=rest.normalized*next.magnitude;rod.localScale=Vector3.one;}
            if(name.Contains("coilover")){var lower=Find(name+".lower_seat");if(lower)lower.localPosition=rest.normalized*(next.magnitude-.12f*rest.magnitude);var spring=Find(name+".spring");if(spring)ScaleAlong(spring,rest.normalized,(next.magnitude-.30f*rest.magnitude)/(.70f*rest.magnitude));}
        }
        void ScaleAlong(Transform node,Vector3 axis,float ratio) {
            // Equivalent to donor R(axis) * S(1,ratio,1) * inverse(R(axis)),
            // performed on this instance's flexible mesh without stretching its
            // rigid seats or introducing a transform shear in Unity.
            node.localScale=Vector3.one;
            if(!axial.TryGetValue(node,out var list)){list=new List<Deform>();Capture(node.name,list);axial[node]=list;}
            axis.Normalize();ratio=Mathf.Max(.05f,ratio);foreach(var mesh in list){for(int j=0;j<mesh.Rest.Length;j++){Vector3 p=mesh.Rest[j];mesh.Set(j,p+axis*(Vector3.Dot(p,axis)*(ratio-1)));}mesh.Apply(true);}
        }
        void PoseSwitchback(SimState s,VehicleTune tune) {
            for(int i=0;i<2;i++){float sign=i==0?-1:1;string side=i==0?"L":"R",front="front."+side,rear="rear."+side;WheelPose p=WheelKinematics.Switchback(i,s.Travel[i],s.Steer);Vector3 ball=V(p.Low),hub=V(p.Hub);Quaternion q=Q(p.Rotation);Link(front+".lower_arm",B(front+".lower_arm"),ball,new Vector3(sign*.734f,.255f,1.24f));Link(front+".radius_rod",B(front+".radius_rod"),ball,new Vector3(sign*.734f,.255f,1.24f));
                Vector3 end=q*new Vector3(0,.065f,-.10f)+ball,start=B(front+".tie_rod"),restEnd=new Vector3(sign*.734f,.32f,1.14f);float len=Vector3.Distance(start,restEnd),yy=end.y-start.y,zz=end.z-start.z;start.x=end.x-sign*Mathf.Sqrt(Mathf.Max(.001f,len*len-yy*yy-zz*zz));Link(front+".tie_rod",start,end,restEnd);
                Plunge(front+".halfshaft",hub+q*new Vector3(-sign*.076f,0,0),new Vector3(sign*.734f,.31f,1.24f));
                SwitchTelescope(front+".strut",front+".strut_rod",q*new Vector3(-sign*.060f,.125f,0)+ball,new Vector3(sign*.674f,.38f,1.24f),front+".coil");WheelPose rp=WheelKinematics.Switchback(i+2,s.Travel[i+2],s.Steer);Quaternion rq=Q(rp.Rotation);Rotate(rear+".trailing_arm",rq);Vector3 pivot=new Vector3(sign*.68f,.33f,-.66f),rearEnd=new Vector3(sign*.70f,.32f,-1.27f);SwitchTelescope(rear+".damper",rear+".damper_rod",rq*(rearEnd-pivot)+pivot,rearEnd);
                Plunge(rear+".halfshaft",rq*(new Vector3(sign*.734f,.31f,-1.24f)-pivot)+pivot,new Vector3(sign*.734f,.31f,-1.24f));
            }
        }
        void Plunge(string name,Vector3 end,Vector3 restEnd) {Vector3 start=B(name),old=restEnd-start,next=end-start;Point(name,start);Rotate(name,Aim(old,next));ScaleAlong(Need(name),old.normalized,next.magnitude/old.magnitude);}
        void SwitchTelescope(string name,string rod,Vector3 end,Vector3 restEnd,string spring=null) {Vector3 start=B(name),old=restEnd-start,next=end-start;Point(name,start);Rotate(name,Aim(old,next));Need(rod).localPosition=old.normalized*next.magnitude;if(spring!=null&&Find(spring))ScaleAlong(Need(spring),old.normalized,(next.magnitude-.55f*old.magnitude)/(.45f*old.magnitude));}
        public void PosePanels(float openness,float roofT) {
            panels=Mathf.Clamp01(openness);roof=Mathf.Clamp01(roofT);
            if(id=="nocturne") {
                for(int i=0;i<4;i++){Rotate("door_"+i+"_hinge",Quaternion.AngleAxis((i%2!=0?1:-1)*(i<2?-1:1)*1.05f*Mathf.Rad2Deg*Mathf.Clamp01((panels-.25f)/.75f),Vector3.up));var glass=Find("door_glass_"+i);if(glass){float drop=Mathf.Clamp01(panels/.25f);Vector3 scale=Vector3.one;scale.y=roof>.9f?1-drop*(i<2?.999f:.5f):.001f;glass.localScale=scale;}}
                Rotate("hood_hinge",Quaternion.AngleAxis(-1.05f*Mathf.Rad2Deg*panels,Vector3.right));PoseRoof(roof);
            } else if(id=="catrina") {Rotate("hood_hinge",Quaternion.AngleAxis(-1.10f*Mathf.Rad2Deg*panels,Vector3.right));Rotate("trunk_hinge",Quaternion.AngleAxis(1.08f*Mathf.Rad2Deg*panels,Vector3.right));}
            else if(id=="media-luna"){Rotate("hood_hinge",Quaternion.AngleAxis(-.95f*Mathf.Rad2Deg*panels,Vector3.right));Rotate("trunk_hinge",Quaternion.AngleAxis(1.05f*Mathf.Rad2Deg*panels,Vector3.right));}
            else if(id=="switchback"){Rotate("door.L.hinge",Quaternion.Euler(0,58*panels,0));Rotate("door.R.hinge",Quaternion.Euler(0,-58*panels,0));Rotate("hood.hinge",Quaternion.Euler(-65*panels,0,0));Rotate("tailgate.hinge",Quaternion.Euler(-90*panels,0,0));for(int i=0;i<2;i++){float sign=i==0?-1:1;string name="tailgate.stay."+(i==0?"L":"R");if(!Find(name))continue;Vector3 start=new Vector3(sign*.68f,.81f,-1.92f),hinge=new Vector3(0,.407f,-2.125f),end=Quaternion.Euler(-90*panels,0,0)*(new Vector3(sign*.68f,.79f,-2.10f)-hinge)+hinge,old=new Vector3(0,-.02f,-.18f);Point(name,start);Rotate(name,Aim(old,end-start));ScaleAlong(Need(name),old.normalized,Vector3.Distance(start,end)/old.magnitude);}}
        }
        void PoseRoof(float t) {
            var root=Find("roof_root");if(!root)return;Vector3 roofRest=bind[root];float open=t<.12f?t/.12f:t>.86f?(1-t)/.14f:1;Rotate("deck_hinge",Quaternion.AngleAxis(-1.12f*Mathf.Rad2Deg*Mathf.Clamp01(open),Vector3.right));
            for(int i=0;i<2;i++){var cover=Find("roof_slot_cover_"+i);if(cover)SetVisibility(cover,t<.02f);}float finish=Mathf.Clamp01((t-.78f)/.08f);Rotate("finish_panel",Quaternion.AngleAxis(-3*Mathf.Rad2Deg*finish*finish*(3-2*finish),Vector3.right));
            float deploy=Mathf.Clamp01((t-.18f)/.60f);deploy=deploy*deploy*(3-2*deploy);Point("roof_root",roofRest);Rotate("roof_root",Quaternion.identity);root.localScale=Vector3.one;root.gameObject.SetActive(true);Vector3[] restBows=new Vector3[3],live=new Vector3[3];Quaternion[] bowQ=new Quaternion[3];
            for(int i=0;i<3;i++){string bow="roof_bow_"+i;if(!Find(bow))return;restBows[i]=B(bow);live[i]=Vector3.Lerp(new Vector3(0,.705f+i*.032f,-2.03f-i*.035f),restBows[i],deploy);live[i].y+=.52f*Mathf.Sin(deploy*Mathf.PI);bowQ[i]=Quaternion.AngleAxis((1-deploy)*90,Vector3.right);Point(bow,live[i]);Rotate(bow,bowQ[i]);Need(bow).localScale=Vector3.one;}
            for(int i=0;i<3;i++){var node=Find("roof_cloth_"+i);if(!node)continue;node.localPosition=Vector3.zero;node.localRotation=Quaternion.identity;node.localScale=Vector3.one;
                foreach(var cm in cloth[i]){for(int j=0;j<cm.Rest.Length;j++){Vector3 original=cm.Rest[j]+restBows[i],a=bowQ[i]*(original-restBows[i])+live[i],p=a;
                    if(i<2){float fraction=Mathf.Clamp01((original.z-restBows[i].z)/(restBows[i+1].z-restBows[i].z));Vector3 b=bowQ[i+1]*(original-restBows[i+1])+live[i+1];p=Vector3.Lerp(a,b,fraction);float restLength=Vector3.Distance(restBows[i],restBows[i+1]),liveLength=Vector3.Distance(live[i],live[i+1]),slack=Mathf.Max(0,restLength-liveLength),amplitude=Mathf.Min(.055f+.035f*Mathf.Sin(deploy*Mathf.PI),slack*.24f)*(i==0?.72f:1),phase=fraction*2*Mathf.PI,envelope=Mathf.Sin(fraction*Mathf.PI),fold=Mathf.Sin(phase+.35f*Mathf.Sin(phase))*envelope;p.y+=amplitude*fold+.004f*(1-deploy)*Mathf.Sin(fraction*21.9911486f+i*.6f)*envelope;}
                    if(i==2)p.y=deploy*p.y+(1-deploy)*(.770f+.012f*Mathf.Sin((original.z-restBows[i].z)*50));cm.Set(j,p-roofRest);
                }cm.Apply(true);}
            }
            for(int i=0;i<2;i++)for(int side=0;side<2;side++){float sign=side==0?-1:1,wa=i==0?.79f:.82f,wb=i==0?.82f:.79f;Vector3 a=bowQ[i]*new Vector3(sign*wa,-.04f,0)+live[i],b=bowQ[i+1]*new Vector3(sign*wb,-.04f,0)+live[i+1],ar=restBows[i]+new Vector3(sign*wa,-.04f,0),br=restBows[i+1]+new Vector3(sign*wb,-.04f,0),rest=br-ar,chord=b-a,across=new Vector3(-sign,0,0);if(chord.sqrMagnitude>.000001f)across-=chord*Vector3.Dot(across,chord)/chord.sqrMagnitude;if(across.magnitude<.00001f)across=Vector3.up;across.Normalize();float half=rest.magnitude*.5f;Vector3 mid=(a+b)*.5f+across*Mathf.Sqrt(Mathf.Max(0,half*half-chord.sqrMagnitude*.25f));for(int h=0;h<2;h++){string rail="roof_rail_"+i+"_"+h+(side==0?"_L":"_R");Point(rail,h==0?a:mid);Rotate(rail,Aim(rest,h==0?mid-a:b-mid));}}
            for(int i=0;i<2;i++){string lift="roof_lift_"+i;if(Find(lift)){Need(lift).localScale=Vector3.one;Vector3 end=P("roof_lift_end_"+i),next=end-B(lift),rest=L(lift+"_rod"),axis=rest.normalized;Point(lift,B(lift));Rotate(lift,Aim(axis,next));Need(lift+"_rod").localPosition=axis*next.magnitude;Need(lift+"_stage1").localPosition=axis*(.300f+(next.magnitude-.378659f)/3);Need(lift+"_stage2").localPosition=axis*(.339f+(next.magnitude-.378659f)*2/3);}string deck="deck_actuator_"+i;if(Find(deck))Telescope(deck,deck+"_rod",P("deck_actuator_end_"+i));}
        }
        public Dictionary<string,int> SampleCounts() {
            var counts=new Dictionary<string,int>();
            if(id=="nocturne") {
                for(int i=0;i<4;i++){int meshes=0,low=0,high=0;float span=(i<2?.525f:.65f)-B("bag_"+i).y;foreach(var mesh in bags[i])if(mesh.Rubber){meshes++;foreach(var p in mesh.Rest){if(Mathf.Abs(p.y)<.00001f)low++;if(Mathf.Abs(p.y-span)<.00001f)high++;}}counts["bag "+i+" rubber meshes"]=meshes;counts["bag "+i+" lower bearing ring vertices"]=low;counts["bag "+i+" upper bearing ring vertices"]=high;}
                for(int i=0;i<3;i++){int vertices=0;foreach(var mesh in cloth[i])vertices+=mesh.Rest.Length;counts["roof cloth "+i+" vertices"]=vertices;}
            } else if(id=="media-luna") {
                for(int i=0;i<2;i++){int low=0,high=0,vertices=0,frontEyes=0,rearEyes=0;foreach(var mesh in coils[i]){if(mesh.UV.Length!=mesh.Rest.Length)throw new InvalidOperationException("Missing coil station coordinates");foreach(var uv in mesh.UV){if(Mathf.Abs(uv.x)<.00001f)low++;if(Mathf.Abs(uv.x-1)<.00001f)high++;}}foreach(var mesh in leaves[i]){vertices+=mesh.Rest.Length;foreach(var p in mesh.Rest){if(Mathf.Abs(p.z)<.00001f)frontEyes++;if(Mathf.Abs(p.z+B("leaf_"+i).z-B("leaf_eye_"+i).z)<.00001f)rearEyes++;}}counts["coil "+i+" lower station vertices"]=low;counts["coil "+i+" upper station vertices"]=high;counts["leaf "+i+" vertices"]=vertices;counts["leaf "+i+" front eye vertices"]=frontEyes;counts["leaf "+i+" rear eye vertices"]=rearEyes;}
            }
            return counts;
        }
        // Runtime evidence comes from loaded transforms and deformed vertex data.
        // The reviewer can call this after Pose over a finite split-travel sweep.
        public Dictionary<string,double> Measure(SimState s,VehicleTune tune) {
            var result=new Dictionary<string,double>();double hubError=0,damperError=0,linkError=0,bagError=0,plateError=0;
            for(int i=0;i<4;i++){string pivot=id=="baja"?"wheel."+new[]{"FL","FR","RL","RR"}[i]+".roll":id=="switchback"?"hub."+new[]{"FL","FR","RL","RR"}[i]+".spin":"wheel_"+i+"_spin";if(Find(pivot))hubError=Math.Max(hubError,Vector3.Distance(P(pivot),V(WheelKinematics.Pose(tune,i,s.Travel,s.Steer).Hub)));}
            result["maximumHubAttachmentErrorM"]=hubError;
            if(id=="media-luna"||id=="nocturne") {
                for(int i=0;i<4;i++)damperError=Math.Max(damperError,Vector3.Distance(P("damper_"+i+"_rod"),P("damper_mount_"+i)));
                if(id=="nocturne") {
                    for(int i=0;i<4;i++) {
                        string link="rear_link_"+i;Vector3 endpoint=R(link)*V(WheelKinematics.NocturneRearEnd(i)-WheelKinematics.NocturneRearBody(i))+P(link);linkError=Math.Max(linkError,Vector3.Distance(endpoint,P("rear_link_end_"+i)));
                        Vector3 bottom=P("bag_lower_"+i),top=i<2?new Vector3((i==0?-1:1)*.48f,.525f,1.6002f):new Vector3((i%2==0?-1:1)*.58f,.65f,-1.75f);float span=top.y-B("bag_"+i).y;Quaternion owner=i<2?R("front_lower_"+i):R("rear_axle");
                        plateError=Math.Max(plateError,Math.Max(Vector3.Distance(P("lower_bag_plate_"+i),bottom),Vector3.Distance(P("upper_bag_plate_"+i),top)));
                        int rubberMeshes=0,lowerSamples=0,upperSamples=0;
                        foreach(var mesh in bags[i])if(mesh.Rubber){rubberMeshes++;for(int j=0;j<mesh.Rest.Length;j++){Vector3 original=mesh.Rest[j];bool low=Mathf.Abs(original.y)<.00001f,high=Mathf.Abs(original.y-span)<.00001f;if(!low&&!high)continue;if(low)lowerSamples++;if(high)upperSamples++;Vector3 radial=new Vector3(original.x,0,original.z),expected=low?owner*radial+bottom:radial+top,actual=car.InverseTransformPoint(mesh.Node.TransformPoint(mesh.Work[j]));bagError=Math.Max(bagError,Vector3.Distance(expected,actual));}}
                        if(rubberMeshes==0||lowerSamples==0||upperSamples==0)throw new InvalidOperationException("Bag "+i+" has no measurable rubber bearing rings");
                    }
                    result["maximumBellowsBearingRingErrorM"]=bagError;result["maximumBagPlateAttachmentErrorM"]=plateError;result["maximumRearLinkAttachmentErrorM"]=linkError;result["maximumDriveshaftEndpointErrorM"]=Vector3.Distance(P("driveshaft_slip"),P("driveshaft_end"));
                }
                result["maximumDamperEndpointErrorM"]=damperError;
                if(id=="media-luna") {
                    double coilError=0,perchError=0,leafChordError=0,shackleError=0,leafEyeError=0;
                    for(int i=0;i<2;i++){Vector3 seat=P("spring_seat_"+i);perchError=Math.Max(perchError,Math.Max(Vector3.Distance(P("spring_perch_"+i),seat),Vector3.Distance(P("coil_"+i),seat)));float stroke=(float)s.Actuator[i]*.5f;int lowerSamples=0,upperSamples=0;foreach(var mesh in coils[i])for(int j=0;j<mesh.Rest.Length;j++){bool low=Mathf.Abs(mesh.UV[j].x)<.00001f,high=Mathf.Abs(mesh.UV[j].x-1)<.00001f;if(!low&&!high)continue;if(low)lowerSamples++;if(high)upperSamples++;Vector3 expected=mesh.Rest[j]+(low?seat:B("coil_"+i)+new Vector3(0,-stroke,0)),actual=car.InverseTransformPoint(mesh.Node.TransformPoint(mesh.Work[j]));coilError=Math.Max(coilError,Vector3.Distance(expected,actual));}if(lowerSamples==0||upperSamples==0)throw new InvalidOperationException("Luna coil "+i+" has no measurable bearing stations");
                        Vector3 fixedPoint=B("leaf_"+i),restSeat=B("axle_seat_"+i),restEye=B("leaf_eye_"+i),liveSeat=P("axle_seat_"+i),eye=P("leaf_eye_"+i);double restChord=Vector3.Distance(fixedPoint,restSeat)+Vector3.Distance(restSeat,restEye),liveChord=Vector3.Distance(fixedPoint,liveSeat)+Vector3.Distance(liveSeat,eye);leafChordError=Math.Max(leafChordError,Math.Abs(restChord-liveChord));shackleError=Math.Max(shackleError,Math.Abs(Vector3.Distance(P("shackle_"+i),eye)-L("leaf_eye_"+i).magnitude));
                        int frontEyeSamples=0,rearEyeSamples=0;foreach(var mesh in leaves[i])for(int j=0;j<mesh.Rest.Length;j++){Vector3 p=mesh.Rest[j];bool frontEye=Mathf.Abs(p.z)<.00001f,rearEye=Mathf.Abs(p.z+fixedPoint.z-restEye.z)<.00001f;if(!frontEye&&!rearEye)continue;if(frontEye)frontEyeSamples++;if(rearEye)rearEyeSamples++;Vector3 expected=p+fixedPoint+(rearEye?eye-restEye:Vector3.zero),actual=car.InverseTransformPoint(mesh.Node.TransformPoint(mesh.Work[j]));leafEyeError=Math.Max(leafEyeError,Vector3.Distance(expected,actual));}if(frontEyeSamples==0||rearEyeSamples==0)throw new InvalidOperationException("Luna leaf "+i+" has no measurable eye vertices");}
                    result["maximumCoilBearingStationErrorM"]=coilError;result["maximumSpringPerchAttachmentErrorM"]=perchError;result["maximumLeafChordConservationErrorM"]=leafChordError;result["maximumShackleLengthErrorM"]=shackleError;result["maximumModeledLeafEyeAttachmentErrorM"]=leafEyeError;
                }
            }
            if(id=="catrina") {
                string[] links={"rear_2_lower","rear_3_lower","rear_upper","rear_panhard"};AxlePose axle=WheelKinematics.CatrinaRear(s.Travel[2],s.Travel[3]);Vector3 center=V(axle.Center);Quaternion q=Q(axle.Rotation);
                for(int i=0;i<4;i++){Vector3 body=V(WheelKinematics.CatrinaRearBody(i)),end=V(WheelKinematics.CatrinaRearEnd(i)),live=R(links[i])*(end-body)+P(links[i]),expected=q*(end-new Vector3(0,.2891f,-1.5113f))+center;linkError=Math.Max(linkError,Vector3.Distance(live,expected));}
                result["maximumRearLinkAttachmentErrorM"]=linkError;result["maximumDriveshaftEndpointErrorM"]=Vector3.Distance(P("driveshaft_slip"),q*(new Vector3(0,.2891f,-1.2913f)-new Vector3(0,.2891f,-1.5113f))+center);
                double springSeatError=0,springStopViolation=0,ramOverlapViolation=0;
                for(int i=0;i<4;i++){float sign=i%2==0?-1:1;Vector3 expectedSeat;if(i<2){Vector3 a=new Vector3(sign*.18f,.25f,1.5113f);expectedSeat=Vector3.LerpUnclamped(a,V(WheelKinematics.CatrinaFront(i,s.Travel[i],s.Steer).Low),(.55f-.18f)/.535f)+new Vector3(0,.02f,0);}else expectedSeat=q*(new Vector3(sign*.56f,.33f,-1.5113f)-new Vector3(0,.2891f,-1.5113f))+center;springSeatError=Math.Max(springSeatError,Vector3.Distance(P("coil_"+i+"_seat"),expectedSeat));
                    damperError=Math.Max(damperError,Vector3.Distance(P("damper_"+i+"_rod"),P("damper_"+i+"_lower_joint")));Vector3 top=P("hydraulic_"+i),cup=P("hydraulic_"+i+"_rod"),axis=(expectedSeat-top).normalized;double springLength=Vector3.Dot(expectedSeat-cup,axis);springStopViolation=Math.Max(springStopViolation,Math.Max(0,.114-springLength));double overlap=Vector3.Dot(P("hydraulic_"+i+"_barrel_end")-P("hydraulic_"+i+"_rod_tip"),axis);ramOverlapViolation=Math.Max(ramOverlapViolation,Math.Max(0,.05-overlap));}
                result["maximumDamperEndpointErrorM"]=damperError;result["maximumSpringSeatAttachmentErrorM"]=springSeatError;result["maximumSpringCompressionStopViolationM"]=springStopViolation;result["maximumHydraulicOverlapViolationM"]=ramOverlapViolation;
            }
            return result;
        }
        public Dictionary<string,double> MeasurePanels() {
            var result=new Dictionary<string,double>();if(id!="nocturne"||!Find("roof_root"))return result;double joint=0,actuator=0,rigidScale=0;
            for(int i=0;i<3;i++){var bow=Find("roof_bow_"+i);if(bow)rigidScale=Math.Max(rigidScale,Vector3.Distance(bow.localScale,Vector3.one));}
            for(int i=0;i<2;i++)for(int side=0;side<2;side++) {
                float sign=side==0?-1:1,wa=i==0?.79f:.82f,wb=i==0?.82f:.79f;string first="roof_rail_"+i+"_0"+(side==0?"_L":"_R"),second="roof_rail_"+i+"_1"+(side==0?"_L":"_R");if(!Find(first)||!Find(second))throw new InvalidOperationException("Incomplete folding roof rail pair");
                Vector3 ar=B("roof_bow_"+i)+new Vector3(sign*wa,-.04f,0),br=B("roof_bow_"+(i+1))+new Vector3(sign*wb,-.04f,0),half=(br-ar)*.5f,target=R("roof_bow_"+(i+1))*new Vector3(sign*wb,-.04f,0)+P("roof_bow_"+(i+1));joint=Math.Max(joint,Math.Max(Vector3.Distance(R(first)*half+P(first),P(second)),Vector3.Distance(R(second)*half+P(second),target)));
            }
            for(int i=0;i<2;i++){string lift="roof_lift_"+i;if(Find(lift))actuator=Math.Max(actuator,Vector3.Distance(P(lift+"_rod"),P("roof_lift_end_"+i)));string deck="deck_actuator_"+i;if(Find(deck))actuator=Math.Max(actuator,Vector3.Distance(P(deck+"_rod"),P("deck_actuator_end_"+i)));}
            result["maximumRoofRailJointErrorM"]=joint;result["maximumRoofActuatorEndpointErrorM"]=actuator;result["maximumRigidBowScaleError"]=rigidScale;return result;
        }
        public void Dispose() {foreach(var mesh in owned)if(mesh)UnityEngine.Object.Destroy(mesh);owned.Clear();}
    }
}
