using System;
using System.IO;
using UnityEngine;
using UnityEngine.Rendering;
namespace Cinder.Host {
 // Standalone host art direction. No sim state or gameplay clock is modified.
 public sealed class CityEveningLighting:IDisposable {
  Material sky;
  public static bool SunsetCity(int world)=>world==1&&StandaloneHost.Arg("-city-lighting","sunset")!="daylight";
  public void Apply(bool sunset,Light sun,Transform frame,string evidence,bool capture){
   string prefix=sunset?"sunset-":"";
   Vector3 direction=sunset?new Vector3(.70f,.20f,-.685f).normalized:new Vector3(-.6331052f,.743008f,-.2170646f);
   sun.transform.rotation=Quaternion.LookRotation(-direction,Vector3.up);
   sun.color=sunset?new Color(1,.62f,.35f,1).gamma:new Color(1,.9411765f,.8509804f);
   sun.intensity=(sunset?2.4f:2.9f)/Mathf.PI;
   var tex=Resources.Load<Texture2D>(sunset?"Cinder/sunset-sky":"Cinder/sky-oriented");
   var cube=Resources.Load<Cubemap>(sunset?"Cinder/sunset-reflection":"Cinder/sky-reflection-native");
   if(!tex||!cube)throw new InvalidOperationException("Missing coherent "+prefix+"environment");
   if(!sky)sky=new Material(Shader.Find("Skybox/Panoramic"));sky.SetTexture("_MainTex",tex);sky.SetFloat("_Rotation",0);sky.SetFloat("_Exposure",1);RenderSettings.skybox=sky;
   RenderSettings.defaultReflectionMode=DefaultReflectionMode.Custom;RenderSettings.customReflectionTexture=cube;RenderSettings.reflectionIntensity=Mathf.LinearToGammaSpace(.65f);
   RenderSettings.fog=true;RenderSettings.fogMode=FogMode.ExponentialSquared;RenderSettings.fogDensity=sunset?.0015f:.0018f;
   RenderSettings.fogColor=sunset?new Color(.66f,.59f,.64f,1):new Color(.7137255f,.7843137f,.8313725f);
   var source=Resources.Load<TextAsset>("Cinder/"+prefix+"ambient-sh");if(!source)throw new InvalidOperationException("Missing environment SH");
   var asset=JsonUtility.FromJson<AmbientAsset>(source.text);
   if(asset==null||asset.version!=1||!asset.whiteFurnacePass||!asset.hemispherePass||asset.coefficients==null||asset.coefficients.Length!=27)throw new InvalidOperationException("Invalid environment SH");
   var sh=new SphericalHarmonicsL2();for(int c=0;c<3;c++)for(int i=0;i<9;i++){float value=asset.coefficients[c*9+i];if(float.IsNaN(value)||float.IsInfinity(value))throw new InvalidOperationException("Nonfinite environment SH");sh[c,i]=value;}
   RenderSettings.ambientMode=AmbientMode.Skybox;RenderSettings.ambientIntensity=1;RenderSettings.ambientProbe=sh;
   float scale=Mathf.Max(.001f,frame.TransformVector(Vector3.up).magnitude);
   var lamps=new Vector4[8];int k=0;foreach(float x in new[]{-23.7f,23.7f,-44.7f,44.7f})foreach(float z in new[]{49f,85f}){var p=frame.TransformPoint(new Vector3(x+(x<0?-1.35f:1.35f),5.24f,z));lamps[k++]=new Vector4(p.x,p.y,p.z,48*scale*scale);}
   Shader.SetGlobalVectorArray("_CinderStreetLamps",lamps);Shader.SetGlobalVector("_CinderLampUp",frame.up);Shader.SetGlobalFloat("_CinderLampScale",scale);Shader.SetGlobalVector("_CinderLampColour",new Vector4(1,.66f,.32f,1));
   bool practicals=sunset&&StandaloneHost.Arg("-city-lighting")!="lamps-off";
   Shader.SetGlobalFloat("_CinderLampsEnabled",practicals?1:0);
   if(capture){File.WriteAllText(Path.Combine(evidence,"ambient-probe-runtime.json"),source.text);File.WriteAllText(Path.Combine(evidence,"city-lighting-runtime.json"),JsonUtility.ToJson(new Receipt{profile=sunset?"mercer-six-pm":"native-daylight",control=StandaloneHost.Arg("-city-lighting","none"),sunDirection=direction,sunColourApi=sun.color,sunUnityIntensity=sun.intensity,reflectionLinear=.65f,lampCount=sunset?8:0,practicalsEnabled=practicals,lampPositionsIntensity=lamps,scope="Fixed sunset art direction, not astronomical local time. Eight bounded PBR spot evaluations in base pass, no extra Light or shadow map. Static building visibility baked; dynamic lamp occlusion is approximate."},true));}
  }
  [Serializable] sealed class AmbientAsset {public int version;public bool whiteFurnacePass,hemispherePass;public float[] coefficients;}
  [Serializable] sealed class Receipt {public string profile,control,scope;public Vector3 sunDirection;public Color sunColourApi;public float sunUnityIntensity,reflectionLinear;public int lampCount;public bool practicalsEnabled;public Vector4[] lampPositionsIntensity;}
  public void Dispose(){Shader.SetGlobalFloat("_CinderLampsEnabled",0);if(sky)UnityEngine.Object.Destroy(sky);}
 }
}
