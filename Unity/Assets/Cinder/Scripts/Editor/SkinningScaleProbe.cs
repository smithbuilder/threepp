using System;
using System.IO;
using System.Collections.Generic;
using System.Reflection;
using Cinder.Host;
using Cinder.Sim;
using Cinder.View;
using UnityEditor;
using UnityEngine;

namespace Cinder.Editor
{
    // CPU diagnostic for BakeMesh's scale convention. A finite row is not a
    // fidelity PASS: inspect every error column and the analytic control.
    public static class SkinningScaleProbe
    {
        [Serializable] sealed class Report
        {
            public string unity,createdUtc,scope;
            public bool finite=true;
            public List<Row> fixtureRows=new List<Row>();
            public List<Row> actualCarRows=new List<Row>();
            public List<string> errors=new List<string>();
        }
        [Serializable] sealed class Row
        {
            public string kind,phase;
            public float parentScale;
            public bool useScale,finite=true;
            public int batches,vertices,inactiveSources;
            public double transformPointMaxErrorM,rotationTranslationMaxErrorM,analyticSkinMaxErrorM;
            public float[] expectedFirstWorld,bakedFirstLocal,transformedFirstWorld,rendererLossyScale;
        }
        static bool Finite(double value)=>!double.IsNaN(value)&&!double.IsInfinity(value);
        static float[] V(Vector3 point)=>new[]{point.x,point.y,point.z};
        static Transform Child(Transform parent,string name,Vector3 position,Quaternion rotation)
        {
            var child=new GameObject(name).transform;child.SetParent(parent,false);
            child.localPosition=position;child.localRotation=rotation;return child;
        }
        static void AddPoint(Row row,SkinnedMeshRenderer renderer,Vector3 baked,Vector3 analytic,Vector3 expected)
        {
            Vector3 world=renderer.transform.TransformPoint(baked);
            Vector3 rigid=renderer.transform.position+renderer.transform.rotation*baked;
            double directError=Vector3.Distance(world,expected),rigidError=Vector3.Distance(rigid,expected),analyticError=Vector3.Distance(analytic,expected);
            row.finite&=Finite(directError)&&Finite(rigidError)&&Finite(analyticError);
            row.transformPointMaxErrorM=Math.Max(row.transformPointMaxErrorM,directError);
            row.rotationTranslationMaxErrorM=Math.Max(row.rotationTranslationMaxErrorM,rigidError);
            row.analyticSkinMaxErrorM=Math.Max(row.analyticSkinMaxErrorM,analyticError);
            if(row.vertices==0){row.expectedFirstWorld=V(expected);row.bakedFirstLocal=V(baked);row.transformedFirstWorld=V(world);row.rendererLossyScale=V(renderer.transform.lossyScale);}
            row.vertices++;
        }
        static void Fixture(Report report,float scale)
        {
            GameObject root=null;Mesh sourceMesh=null,skinMesh=null;
            try
            {
                root=new GameObject("Skinning scale analytic fixture");root.hideFlags=HideFlags.HideAndDontSave;
                root.transform.position=new Vector3(12,3,-8);root.transform.rotation=Quaternion.Euler(7,31,-3);root.transform.localScale=Vector3.one*scale;
                var bone=Child(root.transform,"One rigid bone",new Vector3(-.2f,.4f,.7f),Quaternion.Euler(-9,18,5));
                var original=Child(bone,"Source",new Vector3(.25f,-.1f,.6f),Quaternion.Euler(10,-5,7));
                var output=Child(root.transform,"Skin output",Vector3.zero,Quaternion.identity);
                sourceMesh=new Mesh{name="Known triangle"};sourceMesh.vertices=new[]{new Vector3(-1,-.3f,-.5f),new Vector3(1,.1f,-.2f),new Vector3(.1f,1.2f,.7f)};sourceMesh.triangles=new[]{0,1,2};sourceMesh.RecalculateNormals();
                original.gameObject.AddComponent<MeshFilter>().sharedMesh=sourceMesh;
                var input=sourceMesh.vertices;var vertices=new Vector3[input.Length];
                for(int i=0;i<input.Length;i++)vertices[i]=output.InverseTransformPoint(original.TransformPoint(input[i]));
                var bind=bone.worldToLocalMatrix*output.localToWorldMatrix;
                skinMesh=new Mesh{name="Known single-weight skin"};skinMesh.vertices=vertices;skinMesh.triangles=new[]{0,1,2};skinMesh.RecalculateNormals();
                skinMesh.boneWeights=new[]{new BoneWeight{boneIndex0=0,weight0=1},new BoneWeight{boneIndex0=0,weight0=1},new BoneWeight{boneIndex0=0,weight0=1}};skinMesh.bindposes=new[]{bind};skinMesh.RecalculateBounds();
                var renderer=output.gameObject.AddComponent<SkinnedMeshRenderer>();renderer.sharedMesh=skinMesh;renderer.bones=new[]{bone};renderer.rootBone=root.transform;renderer.quality=SkinQuality.Bone1;renderer.updateWhenOffscreen=true;
                var bonePosition=bone.localPosition;var boneRotation=bone.localRotation;
                for(int phase=0;phase<2;phase++)
                {
                    bone.localPosition=bonePosition+(phase==0?Vector3.zero:new Vector3(.22f,.35f,-.18f));
                    bone.localRotation=phase==0?boneRotation:Quaternion.Euler(22,37,-11)*boneRotation;
                    foreach(bool useScale in new[]{false,true})
                    {
                        var row=new Row{kind="known-single-weight",phase=phase==0?"neutral":"bone moved",parentScale=scale,useScale=useScale,batches=1};
                        var baked=new Mesh();
                        try
                        {
                            renderer.BakeMesh(baked,useScale);var points=baked.vertices;
                            if(points.Length!=input.Length)throw new InvalidOperationException("Known fixture changed baked vertex count");
                            for(int i=0;i<input.Length;i++)AddPoint(row,renderer,points[i],bone.localToWorldMatrix.MultiplyPoint3x4(bind.MultiplyPoint3x4(vertices[i])),original.TransformPoint(input[i]));
                        }
                        finally {UnityEngine.Object.DestroyImmediate(baked);}
                        report.fixtureRows.Add(row);report.finite&=row.finite&&row.vertices==3;
                    }
                }
            }
            finally
            {
                if(root)UnityEngine.Object.DestroyImmediate(root);
                if(sourceMesh)UnityEngine.Object.DestroyImmediate(sourceMesh);
                if(skinMesh)UnityEngine.Object.DestroyImmediate(skinMesh);
            }
        }
        static IEnumerable<(SkinnedMeshRenderer Renderer,MeshFilter[] Sources)> Bindings(CinderView view)
        {
            var field=typeof(CinderView).GetField("rigidBatches",BindingFlags.Instance|BindingFlags.NonPublic);
            if(field==null)throw new MissingFieldException("CinderView.rigidBatches");
            return (IEnumerable<(SkinnedMeshRenderer Renderer,MeshFilter[] Sources)>)field.GetValue(view);
        }
        static void ActualCar(Report report,string id,float scale)
        {
            CinderView view=null;GameObject root=null;
            try
            {
                var sim=new VehicleSim(VehicleCatalog.Index(id));for(int i=0;i<240;i++)sim.Step(new SimInput{Brake=1});
                var bindState=sim.State.Clone();
                view=new CinderView(new ModuleContext{Frame=new Frame{Origin=new Vector3(12,3,-8),Rotation=Quaternion.Euler(7,31,-3),Scale=scale},Seed=619},sim,0);root=view.Root.gameObject;
                for(int phase=0;phase<2;phase++)
                {
                    var state=bindState.Clone();
                    if(phase==1)
                    {
                        for(int i=0;i<4;i++)
                        {
                            bool high=i%2==1;
                            double low=id=="catrina"?(i<2?-.12:-.28):id=="media-luna"?(i<2?-.035:.24):.278;
                            double raised=id=="catrina"?.42:id=="media-luna"?(i<2?.52:.50):.418;
                            state.Travel[i]=high?raised:low;state.Spin[i]=.4+i*.1;
                            state.Actuator[i]=id=="catrina"?.58:id=="media-luna"&&i<2?.304:0;
                        }
                        state.Steer=.32;
                        for(int i=0;i<4;i++)state.WheelLocal[i]=WheelKinematics.Hub(sim.Tune,i,state.Travel,state.Steer);
                    }
                    view.Pose(state);view.Panels(phase==0?0:.5f,phase==0?0:.5f);
                    foreach(bool useScale in new[]{false,true})
                    {
                        var row=new Row{kind=id+"-hero",phase=phase==0?"neutral":"split-steer panels-half",parentScale=scale,useScale=useScale};
                        foreach(var binding in Bindings(view))
                        {
                            var renderer=binding.Renderer;if(!renderer.enabled||!renderer.gameObject.activeInHierarchy)continue;
                            row.batches++;var mesh=renderer.sharedMesh;var weights=mesh.boneWeights;var binds=mesh.bindposes;var original=mesh.vertices;var bones=renderer.bones;
                            var baked=new Mesh();
                            try
                            {
                                renderer.BakeMesh(baked,useScale);var points=baked.vertices;int offset=0;
                                foreach(var source in binding.Sources)
                                {
                                    if(!source.gameObject.activeInHierarchy)row.inactiveSources++;
                                    foreach(var point in source.sharedMesh.vertices)
                                    {
                                        if(offset>=points.Length||offset>=weights.Length)throw new InvalidOperationException("Actual batch vertex count changed");
                                        var weight=weights[offset];if(weight.weight0!=1||weight.weight1!=0||weight.weight2!=0||weight.weight3!=0)throw new InvalidOperationException("Diagnostic expected one-weight rigid vertices");
                                        Vector3 analytic=bones[weight.boneIndex0].localToWorldMatrix.MultiplyPoint3x4(binds[weight.boneIndex0].MultiplyPoint3x4(original[offset]));
                                        AddPoint(row,renderer,points[offset],analytic,source.transform.TransformPoint(point));offset++;
                                    }
                                }
                                if(offset!=points.Length)throw new InvalidOperationException("Actual source comparison incomplete");
                            }
                            finally {UnityEngine.Object.DestroyImmediate(baked);}
                        }
                        report.actualCarRows.Add(row);report.finite&=row.finite&&row.vertices>0&&row.batches>0;
                    }
                }
            }
            finally {view?.Dispose();if(root)UnityEngine.Object.DestroyImmediate(root);}
        }
        public static void Run()
        {
            var report=new Report{unity=Application.unityVersion,createdUtc=DateTime.UtcNow.ToString("o"),scope="CPU-only BakeMesh scale-convention diagnostic. Exit 0 means finite populated measurements; errors are not accepted as geometry fidelity."};
            string root=Path.GetFullPath(Path.Combine(Application.dataPath,"../.."));
            string directory=Path.Combine(root,"build/SkinningScaleProbe",DateTime.UtcNow.ToString("yyyyMMdd-HHmmss-fff"));Directory.CreateDirectory(directory);
            foreach(float scale in new[]{1f,.8f,1.15f,2f})try{Fixture(report,scale);}catch(Exception exception){report.finite=false;report.errors.Add("known fixture scale "+scale+": "+exception);}
            foreach(string id in new[]{"catrina","media-luna","nocturne"})foreach(float scale in new[]{1f,1.15f})try{ActualCar(report,id,scale);}catch(Exception exception){report.finite=false;report.errors.Add(id+" scale "+scale+": "+exception);}
            report.finite&=report.fixtureRows.Count==16&&report.actualCarRows.Count==24;
            string path=Path.Combine(directory,"measurements.json");File.WriteAllText(path,JsonUtility.ToJson(report,true));
            Debug.Log("SKINNING SCALE DIAGNOSTIC finite="+report.finite+" knownRows="+report.fixtureRows.Count+" actualRows="+report.actualCarRows.Count+" output="+path);
            EditorApplication.Exit(report.finite?0:1);
        }
    }
}
