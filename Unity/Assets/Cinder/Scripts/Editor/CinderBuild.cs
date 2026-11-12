using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using Cinder.Host;
namespace Cinder.Editor {
 public static class CinderBuild {
  [Serializable] class SourceRow {public string path,sha256;}
  [Serializable] class Sources {public string revision,fingerprint;public SourceRow[] files;}
  public static void Run(){try{
   if(Application.unityVersion!="6000.3.6f1")throw new Exception("Pinned Unity 6000.3.6f1 required");
   string root=Path.GetFullPath(Path.Combine(Application.dataPath,"../..")),id=StandaloneHost.Arg("-cinder-build","");
   if(!System.Text.RegularExpressions.Regex.IsMatch(id,"^cinder-unity-r[0-9]+$"))throw new Exception("Unique revision required");string output=Path.Combine(root,"builds",id,"Cinder.exe");if(File.Exists(output)||File.Exists(Path.Combine(root,"evidence",id,"build-receipt.json")))throw new Exception("Candidate revision already used; choose a new revision");
   PlayerSettings.companyName="SmithBuilder";PlayerSettings.productName="Cinder";PlayerSettings.bundleVersion="0.1.0";PlayerSettings.defaultScreenWidth=1920;PlayerSettings.defaultScreenHeight=1080;PlayerSettings.fullScreenMode=FullScreenMode.FullScreenWindow;PlayerSettings.resizableWindow=true;PlayerSettings.runInBackground=false;PlayerSettings.colorSpace=ColorSpace.Linear;
   PlayerSettings.SetScriptingBackend(NamedBuildTarget.Standalone,ScriptingImplementation.Mono2x);PlayerSettings.SetApiCompatibilityLevel(NamedBuildTarget.Standalone,ApiCompatibilityLevel.NET_Standard);PlayerSettings.SetUseDefaultGraphicsAPIs(BuildTarget.StandaloneWindows64,false);PlayerSettings.SetGraphicsAPIs(BuildTarget.StandaloneWindows64,new[]{UnityEngine.Rendering.GraphicsDeviceType.Direct3D11});GraphicsSettings.defaultRenderPipeline=null;GraphicsSettings.lightsUseLinearIntensity=true;
   // A saved, owned base scene lets offline additive bake scenes be opened in
   // batch mode without attempting to save or reuse an untitled editor scene.
   var bakeBase=EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);Directory.CreateDirectory("Assets/Scenes");EditorSceneManager.SaveScene(bakeBase,"Assets/Scenes/OfflineBakeBase.unity");
   var shippedKits=new System.Collections.Generic.HashSet<string>(new[]{"catrina","catrina-mid","catrina-far","media-luna","media-luna-mid","media-luna-far","nocturne","nocturne-mid","nocturne-far","mercer-city","playground-kit","conifer"},StringComparer.Ordinal);
   foreach(var dir in Directory.GetDirectories(Path.Combine(root,"build/unity-assets"))){if(!shippedKits.Contains(Path.GetFileName(dir)))continue;string source=Path.Combine(dir,"model.glb");if(!File.Exists(source))continue;string kit=Path.GetFileName(dir);string hash=Hash(File.ReadAllBytes(source))+":import-v4";string receipt="Assets/Resources/Cinder/Generated/"+kit+"/source.sha256";if(File.Exists(receipt)&&File.ReadAllText(receipt)==hash){GlbImport.RefreshCoat(source,kit);continue;}if(Directory.Exists(Path.GetDirectoryName(receipt))&&Directory.GetFiles(Path.GetDirectoryName(receipt)).Length>0)throw new Exception("Preserve imported kit before changing source: "+kit);GlbImport.Import(source,kit);GlbImport.RefreshCoat(source,kit);File.WriteAllText(receipt,hash);}
   Directory.CreateDirectory("Assets/Resources/Cinder");foreach(string name in new[]{"sky.hdr","gravel.jpg","forest-floor.jpg"}){string src="Assets/Cinder/Art/Generated/"+name,dst="Assets/Resources/Cinder/"+name;if(File.Exists(src))File.Copy(src,dst,true);}File.WriteAllText("Assets/Resources/Cinder/build.txt",id);AssetDatabase.Refresh();
   CinderSkyBake.Run();CinderSunsetBake.Run();NativeCityMaterials.Configure(root);CinderSunsetCityBake.Run(root);if(StandaloneHost.Has("-bake-local-reflection-diagnostic"))CityReflectionBake.Run(root);
   foreach(var hardwareTier in new[]{GraphicsTier.Tier1,GraphicsTier.Tier2,GraphicsTier.Tier3}){var settings=UnityEditor.Rendering.EditorGraphicsSettings.GetTierSettings(NamedBuildTarget.Standalone,hardwareTier);settings.reflectionProbeBoxProjection=true;settings.reflectionProbeBlending=true;UnityEditor.Rendering.EditorGraphicsSettings.SetTierSettings(NamedBuildTarget.Standalone,hardwareTier,settings);}
   QualitySettings.vSyncCount=0;QualitySettings.antiAliasing=0;QualitySettings.shadowDistance=18;QualitySettings.shadowResolution=ShadowResolution.Low;
   var scene=EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);new GameObject("StandaloneHost").AddComponent<StandaloneHost>();RenderSettings.fog=true;RenderSettings.fogMode=FogMode.ExponentialSquared;Directory.CreateDirectory("Assets/Scenes");EditorSceneManager.SaveScene(scene,"Assets/Scenes/StandaloneHost.unity");EditorBuildSettings.scenes=new[]{new EditorBuildSettingsScene("Assets/Scenes/StandaloneHost.unity",true)};
   var graphics=new SerializedObject(AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/GraphicsSettings.asset")[0]);var shaders=graphics.FindProperty("m_AlwaysIncludedShaders");foreach(string name in new[]{"Standard","Cinder/Body","Cinder/Glass","Cinder/ShopGlass","Cinder/Foliage","Cinder/Grade","Cinder/City","Cinder/CityFoliage","Cinder/Canvas","Hidden/Cinder/CanvasDiagnostic","Skybox/Panoramic","Unlit/Color"}){var shader=Shader.Find(name);if(!shader)throw new Exception("Missing shader "+name);bool found=false;for(int i=0;i<shaders.arraySize;i++)found|=shaders.GetArrayElementAtIndex(i).objectReferenceValue==shader;if(!found){int n=shaders.arraySize;shaders.InsertArrayElementAtIndex(n);shaders.GetArrayElementAtIndex(n).objectReferenceValue=shader;}}graphics.ApplyModifiedPropertiesWithoutUndo();AssetDatabase.SaveAssets();
   string ev=Path.Combine(root,"evidence",id);Directory.CreateDirectory(ev);var sourceFiles=new System.Collections.Generic.List<SourceRow>();foreach(string sub in new[]{"Unity/Assets","Unity/Packages","Unity/ProjectSettings","tools/unity","tools/blender/cinder","tools/cinder-city-export","assets/unity"})foreach(string file in Directory.GetFiles(Path.Combine(root,sub),"*",SearchOption.AllDirectories)){string p=Path.GetRelativePath(root,file).Replace('\\','/');if(p.Contains("/__pycache__/",StringComparison.Ordinal)||p.EndsWith(".pyc",StringComparison.Ordinal))continue;sourceFiles.Add(new SourceRow{path=p,sha256=Hash(File.ReadAllBytes(file))});}var ordered=sourceFiles.OrderBy(r=>r.path,StringComparer.Ordinal).ToArray();string fingerprint=Hash(System.Text.Encoding.UTF8.GetBytes(string.Join("\n",ordered.Select(r=>r.path+"\0"+r.sha256))));File.WriteAllText(Path.Combine(ev,"source-manifest.json"),JsonUtility.ToJson(new Sources{revision=id,fingerprint=fingerprint,files=ordered},true));
   EditorUtility.UnloadUnusedAssetsImmediate();GC.Collect();GC.WaitForPendingFinalizers();
   var report=BuildPipeline.BuildPlayer(new BuildPlayerOptions{scenes=new[]{"Assets/Scenes/StandaloneHost.unity"},locationPathName=output,target=BuildTarget.StandaloneWindows64,options=BuildOptions.None});File.WriteAllText(Path.Combine(ev,"build-receipt.json"),"{\"revision\":\""+id+"\",\"sourceFingerprint\":\""+fingerprint+"\",\"unity\":\""+Application.unityVersion+"\",\"result\":\""+report.summary.result+"\",\"errors\":"+report.summary.totalErrors+",\"warnings\":"+report.summary.totalWarnings+"}");
   if(!SurfaceShaderDiagnostics.Write(Path.Combine(ev,"shader-diagnostics")))throw new Exception("Generated shader diagnostic failed; inspect manifest");
   EditorApplication.Exit(report.summary.result==BuildResult.Succeeded?0:1);
  }catch(Exception e){Debug.LogException(e);EditorApplication.Exit(1);}}
  static string Hash(byte[] b){using(var h=SHA256.Create())return BitConverter.ToString(h.ComputeHash(b)).Replace("-","").ToLowerInvariant();}
 }
}
