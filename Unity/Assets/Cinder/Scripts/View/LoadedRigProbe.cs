using System;
using System.Collections.Generic;
using System.Globalization;
using Cinder.Sim;
using UnityEngine;

namespace Cinder.View {
    [Serializable] public sealed class LoadedRigReport {
        public bool Success=true;public int Checks;public List<string> Lines=new List<string>();
        public void Check(string name,bool pass,string detail="") {Checks++;Success&=pass;Lines.Add((pass?"PASS ":"FAIL ")+name+(detail.Length==0?"":" "+detail));}
    }
    public static class LoadedRigProbe {
        static string N(double x) {return x.ToString("F8",CultureInfo.InvariantCulture);}
        static bool Finite(float x) {return !float.IsNaN(x)&&!float.IsInfinity(x);}
        static bool Finite(Vector3 v) {return Finite(v.x)&&Finite(v.y)&&Finite(v.z);}
        static bool Finite(Quaternion v) {return Finite(v.x)&&Finite(v.y)&&Finite(v.z)&&Finite(v.w);}
        static bool FiniteGeometry(GameObject instance,bool all) {
            foreach(var t in instance.GetComponentsInChildren<Transform>(true))if(!Finite(t.localPosition)||!Finite(t.localRotation)||!Finite(t.localScale))return false;
            int samples=0;foreach(var f in instance.GetComponentsInChildren<MeshFilter>(true)){Mesh mesh=f.sharedMesh;if(!mesh)continue;if(!all&&mesh.name.IndexOf(" live ",StringComparison.Ordinal)<0)continue;foreach(var p in mesh.vertices){samples++;if(!Finite(p))return false;}}
            return samples>0;
        }
        public static LoadedRigReport Run() {
            var report=new LoadedRigReport();
            foreach(string id in new[]{"catrina","media-luna","nocturne"})foreach(string suffix in new[]{"","-mid","-far"}) {
                string key=id+suffix;
                GameObject instance=null;RigMechanisms mechanisms=null;
                try {
                    var prefab=Resources.Load<GameObject>("Cinder/Generated/"+key+"/"+key);if(!prefab)throw new InvalidOperationException("Missing authored prefab "+key);
                    instance=UnityEngine.Object.Instantiate(prefab);instance.name="Loaded rig probe "+key;instance.hideFlags=HideFlags.HideAndDontSave;
                    mechanisms=new RigMechanisms(instance.transform,id);report.Check(key+" loaded named mechanisms",true);report.Check(key+" bind geometry finite",FiniteGeometry(instance,true));
                    foreach(var count in mechanisms.SampleCounts())report.Check(key+" measured "+count.Key,count.Value>0,"samples="+count.Value);
                    VehicleTune tune=VehicleCatalog.All[VehicleCatalog.Index(id)];var sim=new VehicleSim(VehicleCatalog.Index(id));for(int i=0;i<240;i++)sim.Step(new SimInput{Brake=1});SimState bind=sim.State.Clone();int poses=0;
                    double fmin=id=="catrina"?-.12:id=="media-luna"?-.035:.278,fmax=id=="catrina"?.42:id=="media-luna"?.52:.418,rmin=id=="catrina"?-.28:id=="media-luna"?.24:.278,rmax=id=="catrina"?.42:id=="media-luna"?.50:.418;
                    var worst=new Dictionary<string,double>();
                    for(int left=0;left<3;left++)for(int right=0;right<3;right++)foreach(double steer in new[]{-.32,0,.32}) {
                        SimState state=bind.Clone();state.Travel[0]=fmin+(fmax-fmin)*left*.5;state.Travel[1]=fmin+(fmax-fmin)*right*.5;state.Travel[2]=rmin+(rmax-rmin)*left*.5;state.Travel[3]=rmin+(rmax-rmin)*right*.5;state.Steer=steer;
                        for(int i=0;i<4;i++){state.Spin[i]=.4+i*.1;state.Actuator[i]=id=="catrina"?.58:id=="media-luna"&&i<2?.304:0;}
                        instance.transform.localPosition=new Vector3((float)state.Position.X,(float)state.Position.Y,(float)state.Position.Z);instance.transform.localRotation=new Quaternion((float)state.Rotation.X,(float)state.Rotation.Y,(float)state.Rotation.Z,(float)state.Rotation.W);mechanisms.Pose(state,tune);
                        var measures=mechanisms.Measure(state,tune);int required=id=="nocturne"?6:7;if(measures.Count<required)throw new InvalidOperationException("Incomplete loaded mechanical measurements");foreach(var pair in measures){if(!worst.ContainsKey(pair.Key)||pair.Value>worst[pair.Key])worst[pair.Key]=pair.Value;}
                        report.Check(key+" split pose "+poses+" flexible geometry finite",FiniteGeometry(instance,id=="catrina"));poses++;
                    }
                    report.Check(key+" bounded split-travel sweep",poses==27,"poses="+poses);foreach(var pair in worst)report.Check(key+" "+pair.Key,!double.IsNaN(pair.Value)&&!double.IsInfinity(pair.Value)&&pair.Value<=.0002,"m="+N(pair.Value));
                    mechanisms.Pose(bind,tune);
                    foreach(float phase in new[]{0f,.25f,.5f,.75f,1f}) {
                        mechanisms.PosePanels(phase,phase);report.Check(key+" panels "+N(phase)+" geometry finite",FiniteGeometry(instance,id=="catrina"));var panelMeasures=mechanisms.MeasurePanels();if(id=="nocturne"&&panelMeasures.Count!=3)throw new InvalidOperationException("Incomplete roof mechanical measurements");foreach(var pair in panelMeasures)report.Check(key+" panels "+N(phase)+" "+pair.Key,pair.Value<=.0002&&!double.IsNaN(pair.Value)&&!double.IsInfinity(pair.Value),"value="+N(pair.Value));
                    }
                } catch(Exception exception) {report.Check(key+" loaded rig exception",false,exception.GetType().Name+": "+exception.Message);}
                finally {mechanisms?.Dispose();if(instance)UnityEngine.Object.DestroyImmediate(instance);}
            }
            return report;
        }
    }
}
