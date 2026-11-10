using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;
using Debug=UnityEngine.Debug;

namespace Cinder.Editor
{
    // Fixed, CPU-only single-bounce city radiance. This does not render a scene,
    // create a GPU target, change simulation physics or run during normal play.
    public static class CityReflectionBake
    {
        const int Width=512,Height=256,CubeSize=128,MaxLayers=64,BakeLayer=30;
        const float Far=500,RayEpsilon=.001f,NativeRotation=3.4095478f;
        const string Output="Assets/Resources/Cinder/city-reflection-filtered.exr";
        const string ReceiptPath="Assets/Resources/Cinder/city-reflection-bake.json";
        static readonly Vector3 Origin=new Vector3(-31,.85f,65);
        static readonly Vector3 Sun=new Vector3(-.6331052f,.7430080f,-.2170646f).normalized;
        static readonly Color SunColor=new Color(1,.9411765f,.8509804f).linear;
        static readonly Color AmbientSky=new Color(.26f,.31f,.38f).linear;
        static readonly Color AmbientEquator=new Color(.19f,.20f,.20f).linear;
        static readonly Color AmbientGround=new Color(.10f,.09f,.075f).linear;

        [Serializable] sealed class MaterialSet {public NativeMaterial[] materials=null;}
        [Serializable] sealed class NativeMaterial
        {
            public string id=null,name=null;public float[] color=null,emissive=null;public float metalness=0,alphaCutoff=0;
            public Maps maps=null;
        }
        [Serializable] sealed class Maps {public string color=null;}
        [Serializable] sealed class Source {public string path,sha256;}
        [Serializable] sealed class Receipt
        {
            public string algorithm,limitations,outputSha256;
            public int width,height,cubemapSize,rays,opaqueHits,skyMisses,alphaSkipped,alphaLayerLimit;
            public float[] origin,sunDirection,ambientSkyLinear,ambientEquatorLinear,ambientGroundLinear;
            public float normalizedSunIntensity,nativeSkyRotationRadians,maximumLinearChannel,cylindricalImportLongitudeCorrectionU;
            public long elapsedMilliseconds;public bool gpuRendering,simulationChanged;
            public Source[] sources;public CubemapCardinals.Sample[] faces;
        }
        sealed class Surface
        {
            public MeshCollider Collider;public int[] Triangles;public Vector3[] Normals;public Color[] Colors;
            public Vector2[] UV;public Transform Transform;public NativeMaterial Material;public Texture2D Albedo;
            public Color Factor,Emission;
        }
        sealed class Counters {public int Opaque,Sky,Alpha,Limit;}
        static string Hash(byte[] bytes)
        {
            using(var hash=SHA256.Create())return BitConverter.ToString(hash.ComputeHash(bytes)).Replace("-","").ToLowerInvariant();
        }
        static Color Channels(float[] values,string label)
        {
            if(values==null||values.Length<3||values.Any(v=>float.IsNaN(v)||float.IsInfinity(v)||v<0))throw new Exception("Invalid city reflection "+label);
            return new Color(values[0],values[1],values[2],values.Length>3?values[3]:1);
        }
        static string SafePath(string repositoryRoot,string relative)
        {
            string root=Path.GetFullPath(repositoryRoot)+Path.DirectorySeparatorChar;
            string absolute=Path.GetFullPath(Path.Combine(root,relative));
            if(!absolute.StartsWith(root,StringComparison.OrdinalIgnoreCase)||!File.Exists(absolute))throw new Exception("Missing city reflection source: "+relative);
            return absolute;
        }
        static Texture2D Albedo(string repositoryRoot,NativeMaterial material,Dictionary<string,Texture2D> images,List<Source> sources)
        {
            string path=material.maps?.color;if(string.IsNullOrEmpty(path))return null;
            if(!path.StartsWith("Assets/Resources/Cinder/CityRestored/",StringComparison.Ordinal))throw new Exception("Unexpected city reflection image path: "+path);
            if(images.TryGetValue(path,out var existing))return existing;
            string relative="Unity/"+path;byte[] bytes=File.ReadAllBytes(SafePath(repositoryRoot,relative));
            string frozen="assets/unity/city/textures/"+Path.GetFileName(path);byte[] frozenBytes=File.ReadAllBytes(SafePath(repositoryRoot,frozen));
            if(!bytes.SequenceEqual(frozenBytes))throw new Exception("Staged city reflection image differs from its frozen source: "+path);
            var texture=new Texture2D(2,2,TextureFormat.RGBA32,false,true);
            if(!texture.LoadImage(bytes))throw new Exception("Cannot decode city reflection albedo: "+path);
            // GetPixel returns stored file RGB. Conversion to linear happens below,
            // exactly once, separately from scalar alpha and vertex shade data.
            texture.wrapMode=material.id=="leaf"?TextureWrapMode.Clamp:TextureWrapMode.Repeat;
            texture.filterMode=FilterMode.Bilinear;images.Add(path,texture);sources.Add(new Source{path=relative,sha256=Hash(bytes)});sources.Add(new Source{path=frozen,sha256=Hash(frozenBytes)});return texture;
        }
        static Color Sky(Texture2D panorama,Vector3 direction)
        {
            float c=Mathf.Cos(NativeRotation),s=Mathf.Sin(NativeRotation);
            float x=c*direction.x-s*direction.z,z=s*direction.x+c*direction.z;
            float u=Mathf.Repeat(.5f+Mathf.Atan2(z,x)/(2*Mathf.PI),1);
            float v=.5f+Mathf.Asin(Mathf.Clamp(direction.y,-1,1))/Mathf.PI;
            return panorama.GetPixelBilinear(u,v);
        }
        static Color Trace(PhysicsScene physics,Dictionary<int,Surface> surfaces,Texture2D sky,Vector3 direction,Counters counters)
        {
            Vector3 start=Origin;float remaining=Far;
            for(int layer=0;layer<MaxLayers;layer++)
            {
                if(!physics.Raycast(start,direction,out var hit,remaining,1<<BakeLayer,QueryTriggerInteraction.Ignore)){counters.Sky++;return Sky(sky,direction);}
                if(!surfaces.TryGetValue(hit.collider.GetInstanceID(),out var surface))throw new Exception("City reflection hit an unbound collider");
                int offset=hit.triangleIndex*3;
                if(offset<0||offset+2>=surface.Triangles.Length)throw new Exception("City reflection triangle index is invalid");
                int a=surface.Triangles[offset],b=surface.Triangles[offset+1],c=surface.Triangles[offset+2];
                Vector3 weights=hit.barycentricCoordinate;
                Vector2 uv=surface.UV[a]*weights.x+surface.UV[b]*weights.y+surface.UV[c]*weights.z;
                // Same localized retained-coordinate lettering adaptation as the
                // runtime city.sign material. Other source UVs remain untouched.
                if(surface.Material.id=="sign")uv.x=1-uv.x;
                Color texel=surface.Albedo?surface.Albedo.GetPixelBilinear(uv.x,uv.y):Color.white;
                float alpha=texel.a*surface.Factor.a;
                if(surface.Material.alphaCutoff>0&&alpha<surface.Material.alphaCutoff)
                {
                    counters.Alpha++;float step=hit.distance+RayEpsilon;remaining-=step;
                    if(remaining<=RayEpsilon){counters.Sky++;return Sky(sky,direction);}
                    start+=direction*step;continue;
                }
                Vector3 normal=surface.Transform.TransformDirection(surface.Normals[a]*weights.x+surface.Normals[b]*weights.y+surface.Normals[c]*weights.z).normalized;
                if(Vector3.Dot(normal,direction)>0)normal=-normal;
                Color shade=surface.Colors[a]*weights.x+surface.Colors[b]*weights.y+surface.Colors[c]*weights.z;
                Color ambient=normal.y>=0?Color.Lerp(AmbientEquator,AmbientSky,normal.y):Color.Lerp(AmbientEquator,AmbientGround,-normal.y);
                Color direct=SunColor*((2.9f/Mathf.PI)*Mathf.Max(0,Vector3.Dot(normal,Sun)));
                Color albedo=texel.linear*surface.Factor*shade;
                Color radiance=albedo*(1-surface.Material.metalness)*(direct+ambient)+surface.Emission;
                counters.Opaque++;return radiance;
            }
            counters.Limit++;counters.Sky++;return Sky(sky,direction);
        }
        public static void Run(string repositoryRoot)
        {
            var timer=Stopwatch.StartNew();var sources=new List<Source>();var images=new Dictionary<string,Texture2D>(StringComparer.Ordinal);
            string metadata="assets/unity/city/materials.json",model="assets/unity/city/mercer-city.glb",skyFile="Unity/Assets/Resources/Cinder/sky.hdr";
            foreach(string relative in new[]{metadata,model,skyFile,"Unity/Assets/Cinder/Scripts/Editor/CityReflectionBake.cs","Unity/Assets/Cinder/Scripts/Editor/CubemapCardinals.cs"})sources.Add(new Source{path=relative,sha256=Hash(File.ReadAllBytes(SafePath(repositoryRoot,relative)))});
            var set=JsonUtility.FromJson<MaterialSet>(File.ReadAllText(SafePath(repositoryRoot,metadata)));
            if(set?.materials==null||set.materials.Length!=25)throw new Exception("City reflection needs all 25 native material definitions");
            var materials=set.materials.ToDictionary(m=>m.name,StringComparer.Ordinal);
            var sky=AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Resources/Cinder/sky.hdr");
            if(!sky||!sky.isReadable)throw new Exception("City reflection requires the readable linear source HDR from CinderSkyBake");
            sky.wrapModeU=TextureWrapMode.Repeat;sky.wrapModeV=TextureWrapMode.Clamp;
            var prefab=AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Resources/Cinder/Generated/mercer-city/mercer-city.prefab");
            if(!prefab)throw new Exception("City reflection needs the faithful imported Mercer prefab");
            foreach(var existing in Resources.FindObjectsOfTypeAll<Collider>())
                if(existing.gameObject.scene.IsValid()&&existing.gameObject.scene.isLoaded&&existing.enabled&&existing.gameObject.activeInHierarchy&&existing.gameObject.layer==BakeLayer)throw new Exception("CPU city reflection layer 30 already contains an active collider");
            var priorScene=SceneManager.GetActiveScene();
            var scene=EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Additive);scene.name="Cinder fixed city reflection CPU bake";
            var physics=Physics.defaultPhysicsScene;bool priorBackfaces=Physics.queriesHitBackfaces;Texture2D output=null,importPanorama=null;
            try
            {
                if(!physics.IsValid())throw new Exception("Editor CPU reflection physics scene is invalid");
                var instance=(GameObject)PrefabUtility.InstantiatePrefab(prefab,scene);
                var surfaces=new Dictionary<int,Surface>();
                foreach(var filter in instance.GetComponentsInChildren<MeshFilter>())
                {
                    var mesh=filter.sharedMesh;var renderer=filter.GetComponent<MeshRenderer>();
                    if(!mesh||!renderer||!renderer.sharedMaterial||!materials.TryGetValue(renderer.sharedMaterial.name,out var material))throw new Exception("Unmapped city reflection mesh/material");
                    var normals=mesh.normals;var colors=mesh.colors;var uv=mesh.uv;
                    if(mesh.subMeshCount!=1||normals.Length!=mesh.vertexCount||colors.Length!=mesh.vertexCount||uv.Length!=mesh.vertexCount)throw new Exception("Incomplete city reflection mesh attributes: "+mesh.name);
                    filter.gameObject.layer=BakeLayer;
                    var collider=filter.gameObject.AddComponent<MeshCollider>();collider.cookingOptions=MeshColliderCookingOptions.CookForFasterSimulation|MeshColliderCookingOptions.UseFastMidphase;collider.sharedMesh=mesh;
                    surfaces.Add(collider.GetInstanceID(),new Surface{Collider=collider,Triangles=mesh.triangles,Normals=normals,Colors=colors,UV=uv,Transform=filter.transform,Material=material,Albedo=Albedo(repositoryRoot,material,images,sources),Factor=Channels(material.color,material.name+" colour"),Emission=Channels(material.emissive,material.name+" emission")});
                }
                if(surfaces.Count!=26)throw new Exception("City reflection needs all 26 faithful city meshes");
                Physics.queriesHitBackfaces=true;Physics.SyncTransforms();
                var pixels=new Color[Width*Height];var counters=new Counters();float maximum=0;
                for(int y=0;y<Height;y++)
                {
                    if(timer.Elapsed.TotalSeconds>140)throw new Exception("CPU city reflection exceeded its 140-second work budget");
                    float latitude=(1-(y+.5f)/Height)*Mathf.PI,sin=Mathf.Sin(latitude),cos=Mathf.Cos(latitude);
                    for(int x=0;x<Width;x++)
                    {
                        float longitude=(.5f-(x+.5f)/Width)*(2*Mathf.PI);
                        Vector3 direction=new Vector3(sin*Mathf.Cos(longitude),cos,sin*Mathf.Sin(longitude));
                        Color value=Trace(physics,surfaces,sky,direction,counters);value.a=1;
                        if(float.IsNaN(value.r)||float.IsNaN(value.g)||float.IsNaN(value.b)||float.IsInfinity(value.r)||float.IsInfinity(value.g)||float.IsInfinity(value.b)||Mathf.Min(value.r,Mathf.Min(value.g,value.b))<0)throw new Exception("Nonfinite or negative city reflection radiance");
                        maximum=Mathf.Max(maximum,Mathf.Max(value.r,Mathf.Max(value.g,value.b)));pixels[y*Width+x]=value;
                    }
                }
                output=new Texture2D(Width,Height,TextureFormat.RGBAFloat,false,true);output.wrapModeU=TextureWrapMode.Repeat;output.wrapModeV=TextureWrapMode.Clamp;output.SetPixels(pixels);output.Apply();
                // Cubemap import has a measured quarter-turn offset from the
                // Skybox/Panoramic shader. Keep the canonical panorama unchanged
                // for diagnostics and shift only the importer-facing pixels.
                importPanorama=CubemapCardinals.PrepareForCylindricalImport(output);
                byte[] bytes=importPanorama.EncodeToEXR(Texture2D.EXRFlags.CompressZIP);File.WriteAllBytes(Output,bytes);AssetDatabase.ImportAsset(Output);
                var importer=(TextureImporter)AssetImporter.GetAtPath(Output);importer.textureType=TextureImporterType.Default;importer.textureShape=TextureImporterShape.TextureCube;importer.generateCubemap=TextureImporterGenerateCubemap.Cylindrical;importer.maxTextureSize=CubeSize;importer.sRGBTexture=false;importer.isReadable=true;importer.mipmapEnabled=true;importer.filterMode=FilterMode.Trilinear;importer.textureCompression=TextureImporterCompression.Uncompressed;
                var settings=new TextureImporterSettings();importer.ReadTextureSettings(settings);settings.cubemapConvolution=TextureImporterCubemapConvolution.Specular;importer.SetTextureSettings(settings);importer.SaveAndReimport();
                var importedCube=AssetDatabase.LoadAssetAtPath<Cubemap>(Output);if(!importedCube)throw new Exception("City reflection cube is missing after import");
                var receipt=new Receipt{algorithm="CPU static-city raycast, albedo/vertex-shade/mesh-normal single-bounce Lambert radiance; native HDR misses; specular-convolved import",limitations="Approximate diffuse environment, not a GPU renderer match or recursive GI. No normal-map, reflected-specular or transmission evaluation. Fixed origin; use a bounded box-projected custom probe and sky fallback outside its volume.",outputSha256=Hash(bytes),width=Width,height=Height,cubemapSize=CubeSize,rays=Width*Height,opaqueHits=counters.Opaque,skyMisses=counters.Sky,alphaSkipped=counters.Alpha,alphaLayerLimit=counters.Limit,origin=new[]{Origin.x,Origin.y,Origin.z},sunDirection=new[]{Sun.x,Sun.y,Sun.z},ambientSkyLinear=new[]{AmbientSky.r,AmbientSky.g,AmbientSky.b},ambientEquatorLinear=new[]{AmbientEquator.r,AmbientEquator.g,AmbientEquator.b},ambientGroundLinear=new[]{AmbientGround.r,AmbientGround.g,AmbientGround.b},normalizedSunIntensity=2.9f/Mathf.PI,nativeSkyRotationRadians=NativeRotation,maximumLinearChannel=maximum,elapsedMilliseconds=timer.ElapsedMilliseconds,gpuRendering=false,simulationChanged=false,sources=sources.OrderBy(s=>s.path,StringComparer.Ordinal).ToArray()};
                receipt.cylindricalImportLongitudeCorrectionU=-.25f;
                receipt.faces=CubemapCardinals.Read(output,importedCube);
                File.WriteAllText(ReceiptPath,JsonUtility.ToJson(receipt,true));AssetDatabase.ImportAsset(ReceiptPath);
                Debug.Log("CITY REFLECTION CPU BAKE rays="+(Width*Height)+" opaque="+counters.Opaque+" sky="+counters.Sky+" alphaSkips="+counters.Alpha+" maxLinear="+maximum+" elapsedMs="+timer.ElapsedMilliseconds);
            }
            finally
            {
                Physics.queriesHitBackfaces=priorBackfaces;
                foreach(var image in images.Values)UnityEngine.Object.DestroyImmediate(image);
                if(importPanorama)UnityEngine.Object.DestroyImmediate(importPanorama);
                if(output)UnityEngine.Object.DestroyImmediate(output);
                if(scene.IsValid())EditorSceneManager.CloseScene(scene,true);
                if(priorScene.IsValid()&&priorScene.isLoaded)SceneManager.SetActiveScene(priorScene);
            }
        }
    }
}
