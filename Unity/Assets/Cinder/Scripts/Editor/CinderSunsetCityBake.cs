using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace Cinder.Editor
{
    // View-only adaptation of the frozen native city. Original assets are read,
    // never modified. Existing geometry/materials stay unchanged; cloned meshes
    // carry the replacement static sunset shade and finite lamp visibility data.
    public static class CinderSunsetCityBake
    {
        const string SourcePrefab="Assets/Resources/Cinder/Generated/mercer-city/mercer-city.prefab";
        const string DirectoryPath="Assets/Resources/Cinder/Generated/mercer-city-sunset";
        const string Destination=DirectoryPath+"/mercer-city-sunset.prefab";
        const string ReceiptPath=DirectoryPath+"/sunset-city-bake.json";
        const float BuildingFloor=.62f,SunDiskRadius=.0047f;
        static readonly Vector3 NativeSun=new Vector3(-.6331052f,.7430080f,-.2170646f);
        static readonly Vector3 SunsetSun=new Vector3(.70f,.20f,-.685f).normalized;
        static readonly float[] StreetTreeXs={-23.7f,23.7f,-44.7f,44.7f};
        static readonly float[] PocketTreeXs={-20f,20f};
        static readonly float[,] Buildings={
            {-13,49,18,18,14.4f},{-13,71,18,22,20.8f},{-13,94,18,16,11.2f},
            {14,52,16,24,10.8f},{14,84,16,36,17.6f},{-55,49,17,24,18},
            {-55,85,17,38,25},{55,52,17,30,21},{55,93,17,28,14},
            {-16,142,38,24,23},{32,145,28,30,31}
        };
        static readonly Vector3[] LampHeads=MakeLampHeads();
        [Serializable] sealed class SourceRow {public string path,sha256;}
        [Serializable] sealed class MeshRow
        {
            public string name,sourceMesh;public int vertices,triangles,changedColors;
            public float meanOldShade,meanNewShade,maximumRatio;
            public float[] sourceBounds;public int[] lampVisibleVertices,lampOccludedVertices;
            public bool geometryNormalsExistingUvsUnchanged;
        }
        [Serializable] sealed class Receipt
        {
            public string version,inputFingerprint,prefab,limitations,oldShadeQueries;
            public SourceRow[] sources;public MeshRow[] meshes;
            public int meshCount,vertices,triangles,changedColors,buildingCount,sunRaySamples;
            public float[] nativeSun,sunsetSun,lampHeadsXyz,sunSampleWeights;
            public float buildingShadowFloor,sunDiskRadiusRadians,lampNormalOffset;
            public int[] lampUvChannels;
            public bool originalPrefabUntouched,sharedMaterialsReused;
        }
        static Vector3[] MakeLampHeads()
        {
            var points=new List<Vector3>();
            foreach(float x in new[]{-23.7f,23.7f,-44.7f,44.7f})foreach(float z in new[]{49f,85f})
                points.Add(new Vector3(x+(x<0?-1.35f:1.35f),5.24f,z));
            return points.ToArray();
        }
        static void Slab(float p,float direction,float lo,float hi,ref float near,ref float far)
        {
            if(Mathf.Abs(direction)<1e-12f){if(p<lo||p>hi){near=1;far=0;}return;}
            float a=(lo-p)/direction,b=(hi-p)/direction;if(a>b){float swap=a;a=b;b=swap;}
            near=Mathf.Max(near,a);far=Mathf.Min(far,b);
        }
        static bool BuildingHit(Vector3 point,Vector3 direction,float initialNear,float initialFar)
        {
            for(int i=0;i<11;i++)
            {
                float near=initialNear,far=initialFar,x=Buildings[i,0],z=Buildings[i,1],w=Buildings[i,2],d=Buildings[i,3],h=Buildings[i,4];
                Slab(point.x,direction.x,x-w*.5f,x+w*.5f,ref near,ref far);
                Slab(point.y,direction.y,.16f,h+.16f,ref near,ref far);
                Slab(point.z,direction.z,z-d*.5f,z+d*.5f,ref near,ref far);
                if(far>=near)return true;
            }
            return false;
        }
        static float CanopyContact(Vector3 point,Vector3 direction)
        {
            float result=1;if(point.y>=.3f)return result;
            foreach(float x in StreetTreeXs)for(int i=0;i<4;i++)TreeShade(point,direction,x,42+i*18,ref result);
            foreach(float x in PocketTreeXs){TreeShade(point,direction,x,36.8f,ref result);TreeShade(point,direction,x,103.2f,ref result);}
            return result;
        }
        static void TreeShade(Vector3 point,Vector3 direction,float tx,float tz,ref float result)
        {
            float xx=(point.x-tx+4.7f*direction.x/direction.y)/1.15f,zz=point.z-tz+4.7f*direction.z/direction.y;
            float radius=Mathf.Sqrt(xx*xx+zz*zz);
            result=Mathf.Min(result,.72f+.28f*Mathf.Clamp01((radius-1.2f)/1.8f));
            float dx=point.x-tx,dz=point.z-tz,contact=Mathf.Sqrt(dx*dx+dz*dz);
            result=Mathf.Min(result,.78f+.22f*Mathf.Clamp01(contact/1.2f));
        }
        // Float operation order and ray parameterization match frozen
        // CityLayout.hpp::shade; source ground queries use a different bias from
        // CityBlock.hpp::add's normal-offset static parts.
        public static float NativeShade(Vector3 point)
        {
            var ray=new Vector3(NativeSun.x/NativeSun.y,1,NativeSun.z/NativeSun.y);
            return BuildingHit(point,ray,.03f,100)? .52f:CanopyContact(point,NativeSun);
        }
        static Vector3[] SunRays()
        {
            Vector3 right=Vector3.Cross(Vector3.up,SunsetSun).normalized,up=Vector3.Cross(SunsetSun,right).normalized;
            return new[]{SunsetSun,(SunsetSun+right*SunDiskRadius).normalized,(SunsetSun-right*SunDiskRadius).normalized,(SunsetSun+up*SunDiskRadius).normalized,(SunsetSun-up*SunDiskRadius).normalized};
        }
        static float SunsetShade(Vector3 point,Vector3[] rays)
        {
            float blocked=0;
            for(int i=0;i<rays.Length;i++)
            {
                Vector3 d=rays[i];var ray=new Vector3(d.x/d.y,1,d.z/d.y);
                if(BuildingHit(point,ray,.03f,100))blocked+=i==0?.5f:.125f;
            }
            return Mathf.Min(1-(1-BuildingFloor)*blocked,CanopyContact(point,SunsetSun));
        }
        static float LampVisible(Vector3 point,Vector3 normal,int lamp)
        {
            Vector3 start=point+normal*.02f,segment=LampHeads[lamp]-start;
            return segment.sqrMagnitude<.0025f||!BuildingHit(start,segment,.00001f,.99999f)?1:0;
        }
        static string Hash(byte[] bytes)
        {
            using(var hash=SHA256.Create())return BitConverter.ToString(hash.ComputeHash(bytes)).Replace("-","").ToLowerInvariant();
        }
        static SourceRow Source(string root,string relative)
        {
            string absolute=Path.GetFullPath(Path.Combine(root,relative));
            if(!absolute.StartsWith(Path.GetFullPath(root)+Path.DirectorySeparatorChar,StringComparison.OrdinalIgnoreCase)||!File.Exists(absolute))throw new Exception("Missing sunset-city source: "+relative);
            return new SourceRow{path=relative.Replace('\\','/'),sha256=Hash(File.ReadAllBytes(absolute))};
        }
        static float[] Values(Vector3 value)=>new[]{value.x,value.y,value.z};
        static bool GeometryEqual(Mesh original,Mesh clone)
        {
            if(!original.vertices.SequenceEqual(clone.vertices)||!original.normals.SequenceEqual(clone.normals)||!original.tangents.SequenceEqual(clone.tangents)||original.subMeshCount!=clone.subMeshCount||!original.bounds.Equals(clone.bounds))return false;
            for(int i=0;i<original.subMeshCount;i++)if(!original.GetIndices(i).SequenceEqual(clone.GetIndices(i)))return false;
            for(int channel=0;channel<8;channel++)
            {
                if(channel==2||channel==3)continue;var a=new List<Vector4>();var b=new List<Vector4>();original.GetUVs(channel,a);clone.GetUVs(channel,b);if(!a.SequenceEqual(b))return false;
            }
            return true;
        }
        public static void Run(string repositoryRoot)
        {
            var source=AssetDatabase.LoadAssetAtPath<GameObject>(SourcePrefab);if(!source)throw new Exception("Import native Mercer before sunset-city bake");
            var sources=new List<SourceRow>();
            foreach(string path in new[]{"assets/unity/city/mercer-city.glb","assets/unity/city/source/CityLayout.hpp","assets/unity/city/source/CityBlock.hpp","Unity/Assets/Cinder/Scripts/Editor/CinderSunsetCityBake.cs","Unity/"+SourcePrefab})sources.Add(Source(repositoryRoot,path));
            var sourceFilters=source.GetComponentsInChildren<MeshFilter>(true).OrderBy(f=>f.name,StringComparer.Ordinal).ToArray();
            if(sourceFilters.Length!=26)throw new Exception("Sunset-city bake requires all 26 original city meshes");
            foreach(var filter in sourceFilters)sources.Add(Source(repositoryRoot,"Unity/"+AssetDatabase.GetAssetPath(filter.sharedMesh)));
            sources=sources.OrderBy(s=>s.path,StringComparer.Ordinal).ToList();
            const string version="sunset-city-v1;sun=.70,.20,-.685;buildingFloor=.62;disk=.0047;lampUv=2,3;lampNormalBias=.02";
            string fingerprint=Hash(Encoding.UTF8.GetBytes(version+"\n"+string.Join("\n",sources.Select(s=>s.path+"\0"+s.sha256))));
            if(File.Exists(ReceiptPath))
            {
                var prior=JsonUtility.FromJson<Receipt>(File.ReadAllText(ReceiptPath));
                if(prior.inputFingerprint!=fingerprint||!File.Exists(Destination))throw new Exception("Preserve existing sunset-city bake before changing its source/parameters");
                var cached=AssetDatabase.LoadAssetAtPath<GameObject>(Destination);var cachedFilters=cached?cached.GetComponentsInChildren<MeshFilter>(true).OrderBy(f=>f.name,StringComparer.Ordinal).ToArray():null;
                if(cachedFilters==null||cachedFilters.Length!=26||prior.meshes==null||prior.meshes.Length!=26)throw new Exception("Cached sunset-city prefab is incomplete");
                for(int i=0;i<26;i++)if(!cachedFilters[i].sharedMesh||cachedFilters[i].name!=sourceFilters[i].name||cachedFilters[i].sharedMesh.vertexCount!=prior.meshes[i].vertices||cachedFilters[i].sharedMesh.triangles.Length/3!=prior.meshes[i].triangles||!GeometryEqual(sourceFilters[i].sharedMesh,cachedFilters[i].sharedMesh)||cachedFilters[i].sharedMesh.GetVertexAttributeDimension(VertexAttribute.TexCoord2)!=4||cachedFilters[i].sharedMesh.GetVertexAttributeDimension(VertexAttribute.TexCoord3)!=4)throw new Exception("Cached sunset-city mesh data changed: "+sourceFilters[i].name);
                Debug.Log("SUNSET CITY cached source fingerprint "+fingerprint);return;
            }
            if(Directory.Exists(DirectoryPath)&&Directory.GetFiles(DirectoryPath,"*",SearchOption.AllDirectories).Length>0)throw new Exception("Preserve partial sunset-city output before rebuilding");
            Directory.CreateDirectory(DirectoryPath);AssetDatabase.Refresh();GameObject instance=null;var records=new List<MeshRow>();int totalVertices=0,totalTriangles=0,totalChanged=0;
            try
            {
                instance=UnityEngine.Object.Instantiate(source);instance.name="mercer-city-sunset";
                if(PrefabUtility.IsPartOfPrefabInstance(instance))PrefabUtility.UnpackPrefabInstance(instance,PrefabUnpackMode.Completely,InteractionMode.AutomatedAction);
                var filters=instance.GetComponentsInChildren<MeshFilter>(true).OrderBy(f=>f.name,StringComparer.Ordinal).ToArray();Vector3[] rays=SunRays();
                for(int index=0;index<filters.Length;index++)
                {
                    var filter=filters[index];Mesh original=filter.sharedMesh;var vertices=original.vertices;var normals=original.normals;var colors=original.colors;
                    if(vertices.Length!=normals.Length||vertices.Length!=colors.Length||original.HasVertexAttribute(VertexAttribute.TexCoord2)||original.HasVertexAttribute(VertexAttribute.TexCoord3))throw new Exception("Missing native shade/normals or occupied lamp UV2/UV3: "+filter.name);
                    Matrix4x4 matrix=filter.transform.localToWorldMatrix;for(int k=0;k<16;k++)if(Mathf.Abs(matrix[k]-Matrix4x4.identity[k])>1e-6f)throw new Exception("Sunset-city mesh must retain baked native coordinates: "+filter.name);
                    var clone=UnityEngine.Object.Instantiate(original);clone.name=original.name+" sunset shade";var rebaked=new Color[colors.Length];var mask0=new List<Vector4>(vertices.Length);var mask1=new List<Vector4>(vertices.Length);
                    var visible=new int[8];var occluded=new int[8];double oldSum=0,newSum=0;float maxRatio=0;int changed=0;
                    for(int vertex=0;vertex<vertices.Length;vertex++)
                    {
                        Vector3 point=vertices[vertex],normal=normals[vertex],query=filter.name.StartsWith("ground.",StringComparison.Ordinal)?point+new Vector3(0,.025f,0):point+normal*.04f;
                        float oldShade=NativeShade(query),newShade=SunsetShade(query,rays),ratio=newShade/oldShade;Color c=colors[vertex];var next=new Color(c.r*ratio,c.g*ratio,c.b*ratio,c.a);
                        if(float.IsNaN(next.r)||float.IsNaN(next.g)||float.IsNaN(next.b)||float.IsInfinity(next.r)||float.IsInfinity(next.g)||float.IsInfinity(next.b)||Mathf.Min(next.r,Mathf.Min(next.g,next.b))<0)throw new Exception("Invalid sunset-city colour: "+filter.name);
                        rebaked[vertex]=next;if(!next.Equals(c))changed++;oldSum+=oldShade;newSum+=newShade;maxRatio=Mathf.Max(maxRatio,ratio);
                        Vector4 first=Vector4.zero,second=Vector4.zero;for(int lamp=0;lamp<8;lamp++){float weight=LampVisible(point,normal,lamp);if(lamp<4)first[lamp]=weight;else second[lamp-4]=weight;if(weight>.5f)visible[lamp]++;else occluded[lamp]++;}
                        mask0.Add(first);mask1.Add(second);
                    }
                    clone.colors=rebaked;clone.SetUVs(2,mask0);clone.SetUVs(3,mask1);
                    if(!GeometryEqual(original,clone))throw new Exception("Sunset-city bake changed geometry/normals/original UVs: "+filter.name);
                    string asset=DirectoryPath+"/mesh-"+index.ToString("D2",CultureInfo.InvariantCulture)+".asset";AssetDatabase.CreateAsset(clone,asset);filter.sharedMesh=clone;
                    int triangles=original.triangles.Length/3;totalVertices+=vertices.Length;totalTriangles+=triangles;totalChanged+=changed;
                    records.Add(new MeshRow{name=filter.name,sourceMesh=AssetDatabase.GetAssetPath(original),vertices=vertices.Length,triangles=triangles,changedColors=changed,meanOldShade=(float)(oldSum/vertices.Length),meanNewShade=(float)(newSum/vertices.Length),maximumRatio=maxRatio,sourceBounds=Values(original.bounds.center).Concat(Values(original.bounds.extents)).ToArray(),lampVisibleVertices=visible,lampOccludedVertices=occluded,geometryNormalsExistingUvsUnchanged=true});
                    var sourceRenderer=sourceFilters[index].GetComponent<MeshRenderer>();var targetRenderer=filter.GetComponent<MeshRenderer>();
                    if(!sourceRenderer.sharedMaterials.SequenceEqual(targetRenderer.sharedMaterials))throw new Exception("Sunset-city bake changed a shared material: "+filter.name);
                }
                if(totalTriangles!=383961)throw new Exception("Sunset-city triangle count differs from native-restored source");
                var prefab=PrefabUtility.SaveAsPrefabAsset(instance,Destination);if(!prefab)throw new Exception("Sunset-city prefab write failed");
                var receipt=new Receipt{version=version,inputFingerprint=fingerprint,prefab=Destination,sources=sources.ToArray(),meshes=records.ToArray(),meshCount=records.Count,vertices=totalVertices,triangles=totalTriangles,changedColors=totalChanged,buildingCount=11,sunRaySamples=5,nativeSun=Values(NativeSun),sunsetSun=Values(SunsetSun),lampHeadsXyz=LampHeads.SelectMany(Values).ToArray(),sunSampleWeights=new[]{.5f,.125f,.125f,.125f,.125f},buildingShadowFloor=BuildingFloor,sunDiskRadiusRadians=SunDiskRadius,lampNormalOffset=.02f,lampUvChannels=new[]{2,3},originalPrefabUntouched=true,sharedMaterialsReused=true,oldShadeQueries="ground.*: position+(0,.025,0); static.*: position+normal*.04, matching frozen CityBlock.hpp",limitations="Static vertex-sampled analytic building/canopy shade, interpolated over unchanged triangles. Adaptive ground was reduced against daylight colours; no per-pixel sunset-shadow or exact leaf-silhouette guarantee. Lamp UV2/UV3 masks test only 11 building volumes at vertices, not dynamic car/bench/foliage occlusion. Native source colours retain their finite original ground-colour approximation."};
                File.WriteAllText(ReceiptPath,JsonUtility.ToJson(receipt,true));AssetDatabase.ImportAsset(ReceiptPath);AssetDatabase.SaveAssets();
                Debug.Log("SUNSET CITY meshes="+records.Count+" triangles="+totalTriangles+" vertices="+totalVertices+" source="+fingerprint);
            }
            finally {if(instance)UnityEngine.Object.DestroyImmediate(instance);}
        }
    }
}
