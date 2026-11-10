using System;
using System.Collections.Generic;
using System.Globalization;
using Cinder.Host;
using Cinder.Sim;
using UnityEngine;

namespace Cinder.View
{
    [Serializable] public sealed class RuntimeBatchReport
    {
        public bool Success=true;
        public int Checks;
        public List<string> Lines=new List<string>();
        public void Check(string name,bool pass,string detail="")
        {
            Checks++;Success&=pass;
            Lines.Add((pass?"PASS ":"FAIL ")+name+(string.IsNullOrEmpty(detail)?"":" "+detail));
        }
    }

    // Optimization regression, separate from LoadedRigProbe's mechanical checks.
    // Compare each visible merged batch with its disabled source geometry in the
    // current pose, so an animated member accidentally frozen into a batch fails.
    public static class RuntimeBatchProbe
    {
        const double Tolerance=.0002;
        static string N(double value)=>value.ToString("F8",CultureInfo.InvariantCulture);
        static bool Finite(double value)=>!double.IsNaN(value)&&!double.IsInfinity(value);
        static Transform TierRoot(CinderView view,string key)
        {
            foreach(Transform child in view.Root)
                if(child.name==key||child.name==key+"(Clone)")return child;
            return null;
        }
        static int VisibleRenderers(Transform tier)
        {
            int count=0;foreach(var renderer in tier.GetComponentsInChildren<Renderer>())
                if(renderer.enabled&&renderer.gameObject.activeInHierarchy)count++;
            return count;
        }
        static bool DetectsDisplacedSource(CinderView view,Transform tier,out double displaced,out double restored)
        {
            displaced=0;restored=0;
            foreach(var source in tier.GetComponentsInChildren<MeshRenderer>())
            {
                if(source.enabled||!source.gameObject.activeInHierarchy)continue;
                var filter=source.GetComponent<MeshFilter>();if(!filter||!filter.sharedMesh||filter.sharedMesh.vertexCount==0)continue;
                var prior=source.transform.localPosition;
                try
                {
                    source.transform.localPosition=prior+new Vector3(.01f,0,0);
                    displaced=view.ValidateRigidBatches(out _);
                }
                finally {source.transform.localPosition=prior;}
                restored=view.ValidateRigidBatches(out _);
                if(Finite(displaced)&&displaced>Tolerance)return Finite(restored)&&restored<=Tolerance;
            }
            return false;
        }
        static bool DetectsHiddenSource(CinderView view,Transform tier,out double hidden,out double restored)
        {
            hidden=0;restored=0;
            foreach(var source in tier.GetComponentsInChildren<MeshRenderer>())
            {
                if(source.enabled||!source.gameObject.activeInHierarchy||source.gameObject==tier.gameObject)continue;
                var filter=source.GetComponent<MeshFilter>();if(!filter||!filter.sharedMesh||filter.sharedMesh.vertexCount==0)continue;
                bool prior=source.gameObject.activeSelf;
                try
                {
                    source.gameObject.SetActive(false);
                    hidden=view.ValidateRigidBatches(out _);
                }
                finally {source.gameObject.SetActive(prior);}
                restored=view.ValidateRigidBatches(out _);
                if(!Finite(hidden)||hidden>Tolerance)return Finite(restored)&&restored<=Tolerance;
            }
            return false;
        }
        static bool RoofCovers(Transform tier,float phase,out string detail)
        {
            bool expectedVisible=phase<.02f,pass=true;int found=0,renderers=0;
            long visibleTriangles=0;var parts=new List<string>();
            for(int i=0;i<2;i++)
            {
                string name="roof_slot_cover_"+i;Transform cover=null;
                foreach(var node in tier.GetComponentsInChildren<Transform>(true))if(node.name==name){cover=node;break;}
                if(!cover){pass=false;parts.Add(name+"=missing");continue;}
                found++;int original=0;long triangles=0;bool enabled=true;
                foreach(var renderer in cover.GetComponentsInChildren<MeshRenderer>(true))
                {
                    var filter=renderer.GetComponent<MeshFilter>();if(!filter||!filter.sharedMesh)continue;
                    original++;enabled&=renderer.enabled;
                    if(renderer.enabled&&renderer.gameObject.activeInHierarchy)
                        for(int sub=0;sub<filter.sharedMesh.subMeshCount;sub++)triangles+=(long)filter.sharedMesh.GetIndexCount(sub)/3;
                }
                renderers+=original;visibleTriangles+=triangles;
                pass&=original>0&&enabled&&(expectedVisible?triangles>0:triangles==0);
                parts.Add(name+" originalRenderers="+original+" enabled="+enabled+" visibleTriangles="+triangles);
            }
            detail="phase="+N(phase)+" expectedVisible="+expectedVisible+" covers="+found+" originalRenderers="+renderers+" visibleTriangles="+visibleTriangles+" "+string.Join("; ",parts);
            return pass&&found==2;
        }
        static SimState Fixture(SimState bind,VehicleTune tune,int sample)
        {
            var state=bind.Clone();string id=tune.Id;
            // Same bounded travel envelope already accepted by LoadedRigProbe,
            // including hydraulic extension beyond the passive spring droop.
            double frontMin=id=="catrina"?-.12:id=="media-luna"?-.035:.278;
            double frontMax=id=="catrina"?.42:id=="media-luna"?.52:.418;
            double rearMin=id=="catrina"?-.28:id=="media-luna"?.24:.278;
            double rearMax=id=="catrina"?.42:id=="media-luna"?.50:.418;
            if(sample>=1&&sample<=4)
            {
                for(int i=0;i<4;i++)
                {
                    bool high=sample==2||sample==3&&i%2==1||sample==4&&i%2==0;
                    state.Travel[i]=i<2?(high?frontMax:frontMin):(high?rearMax:rearMin);
                    state.Actuator[i]=id=="catrina"?.58:id=="media-luna"&&i<2?.304:0;
                }
                state.Steer=sample==3?-.32:sample==4?.32:0;
            }
            for(int i=0;i<4;i++)
            {
                state.Spin[i]=sample==0?0:.4+i*.1;
                state.WheelLocal[i]=WheelKinematics.Hub(tune,i,state.Travel,state.Steer);
            }
            return state;
        }
        public static RuntimeBatchReport Run()
        {
            var report=new RuntimeBatchReport();int completedTiers=0,mergedTiers=0,unmergedTiers=0;
            string[] samples={"neutral","hydraulic droop","bump","left split and steer","right split and steer","half panels and roof","open panels and roof"};
            foreach(string id in new[]{"catrina","media-luna","nocturne"})
            {
                CinderView view=null;GameObject instance=null;
                try
                {
                    var sim=new VehicleSim(VehicleCatalog.Index(id));
                    for(int i=0;i<240;i++)sim.Step(new SimInput{Brake=1});
                    var bind=sim.State.Clone();
                    view=new CinderView(new ModuleContext{Frame=new Frame{Origin=new Vector3(12,3,-8),Rotation=Quaternion.Euler(7,31,-3),Scale=1.15f},Seed=619},sim,0);
                    instance=view.Root.gameObject;instance.hideFlags=HideFlags.HideAndDontSave;
                    report.Check(id+" runtime optimized view loaded",true);
                    foreach(string suffix in new[]{"","-mid","-far"})
                    {
                        string key=id+suffix;Transform selected=TierRoot(view,key);
                        report.Check(key+" runtime tier present",selected);
                        if(!selected)continue;
                        foreach(string other in new[]{id,id+"-mid",id+"-far"})
                        {
                            var root=TierRoot(view,other);if(root)root.gameObject.SetActive(root==selected);
                        }
                        view.Pose(bind);view.Panels(0,0);
                        double initialError=view.ValidateRigidBatches(out int initialBatches);
                        bool merged=initialBatches>0;
                        if(merged)
                        {
                            mergedTiers++;
                            bool detects=DetectsDisplacedSource(view,selected,out double displaced,out double restored);
                            report.Check(key+" runtime batch displaced-source tripwire",detects,"displacedM="+N(displaced)+" restoredM="+N(restored));
                            bool hides=DetectsHiddenSource(view,selected,out double hidden,out double returned);
                            report.Check(key+" runtime batch hidden-source tripwire",hides,"hiddenM="+N(hidden)+" restoredM="+N(returned));
                        }
                        else unmergedTiers++;
                        bool allSamples=true;double worst=0;
                        for(int sample=0;sample<samples.Length;sample++)
                        {
                            var state=Fixture(bind,sim.Tune,sample);
                            view.Pose(state);
                            float phase=sample==5?.5f:sample==6?1:0;
                            view.Panels(phase,phase);
                            double error=view.ValidateRigidBatches(out int batches);
                            int visible=VisibleRenderers(selected);
                            bool finite=Finite(error);bool participates=batches>0||(id=="nocturne"&&visible>0);
                            bool pass=finite&&error<=Tolerance&&participates;
                            report.Check(key+" runtime batch policy "+samples[sample],pass,"batches="+batches+" visibleRenderers="+visible+" mergedGeometryCoverage="+(batches>0?"compared":"none")+" maxWorldVertexErrorM="+N(error));
                            allSamples&=pass;if(finite)worst=Math.Max(worst,error);else worst=double.PositiveInfinity;
                        }
                        report.Check(key+" runtime batch sampled policy",allSamples,"poses="+samples.Length+" mergedGeometryCoverage="+(merged?"compared":"none")+" worstM="+N(worst));
                        if(id=="nocturne")foreach(float roofPhase in new[]{0f,.01f,.02f,.25f,.5f,.75f,1f})
                        {
                            view.Pose(bind);view.Panels(roofPhase,roofPhase);
                            bool covers=RoofCovers(selected,roofPhase,out string detail);
                            report.Check(key+" runtime roof-slot cover participation",covers,detail);
                        }
                        completedTiers++;
                    }
                    // The right-three-wheel pose exposed a camera override that
                    // bypassed the terrain clearance check. Exercise both rolls
                    // in the same translated/rotated/scaled host frame as the rig.
                    var cameraObject=new GameObject("Cinder camera clearance probe");
                    cameraObject.hideFlags=HideFlags.HideAndDontSave;
                    try {
                        var camera=cameraObject.AddComponent<Camera>();camera.enabled=false;
                        foreach(float roll in new[]{-22f,22f}) {
                            view.Pose(bind);view.Car.localRotation=Quaternion.Euler(0,0,roll);
                            for(int cameraMode=0;cameraMode<=2;cameraMode++) {
                                view.Camera(camera,cameraMode,0,0);
                                var local=view.Root.InverseTransformPoint(camera.transform.position);
                                double clearance=local.y-sim.Terrain.Height(local.x,local.z);
                                report.Check(id+" exterior camera terrain clearance",Finite(clearance)&&clearance>=.3499,"mode="+cameraMode+" rollDegrees="+roll+" clearanceM="+N(clearance));
                            }
                            view.GarageCamera(camera,24);
                            var garage=view.Root.InverseTransformPoint(camera.transform.position);
                            double gap=garage.y-sim.Terrain.Height(garage.x,garage.z);
                            report.Check(id+" garage camera terrain clearance",Finite(gap)&&gap>=.3499,"rollDegrees="+roll+" clearanceM="+N(gap));
                        }
                    } finally {UnityEngine.Object.DestroyImmediate(cameraObject);}
                }
                catch(Exception exception)
                {
                    report.Check(id+" runtime batch exception",false,exception.GetType().Name+": "+exception.Message);
                }
                finally
                {
                    view?.Dispose();
                    // Run is synchronous in the headless probe; do not retain the
                    // preceding car hierarchy while loading the next vehicle.
                    if(instance)UnityEngine.Object.DestroyImmediate(instance);
                }
            }
            report.Check("runtime batch all lowrider detail-tier policies covered",completedTiers==9,"tiers="+completedTiers+" mergedTiers="+mergedTiers+" unmergedTiers="+unmergedTiers);
            return report;
        }
    }
}
