using UnityEngine;
using System.IO;
namespace Cinder.View {
 [RequireComponent(typeof(Camera))] public sealed class CinderGrade:MonoBehaviour {
  Material material;
  public string EvidenceDirectory;
  public bool ColourControl;
  Texture2D control;
  bool recorded;
  [System.Serializable] sealed class Diagnostic {public string inputFormat,targetFormat,colorSpace,materialControl,lightingControl;public bool inputSrgb,targetSrgb,colourControl;public float[] centerLinearRgb,sampleCoordinates,linearSamples;}
  void OnRenderImage(RenderTexture source,RenderTexture target){
   if(!recorded&&!string.IsNullOrEmpty(EvidenceDirectory)){
    var prior=RenderTexture.active;RenderTexture.active=source;var pixel=new Texture2D(1,1,TextureFormat.RGBAFloat,false,true);
    pixel.ReadPixels(new Rect(source.width/2,source.height/2,1,1),0,0);pixel.Apply();var c=pixel.GetPixel(0,0);
    var coordinates=new float[18];var samples=new float[27];int sample=0;
    foreach(int y in new[]{270,290,310})foreach(int x in new[]{400,480,600}){pixel.ReadPixels(new Rect(x,y,1,1),0,0);pixel.Apply();var p=pixel.GetPixel(0,0);coordinates[sample*2]=x;coordinates[sample*2+1]=y;samples[sample*3]=p.r;samples[sample*3+1]=p.g;samples[sample*3+2]=p.b;sample++;}
    Destroy(pixel);RenderTexture.active=prior;
    File.WriteAllText(Path.Combine(EvidenceDirectory,"render-diagnostics.json"),JsonUtility.ToJson(new Diagnostic{inputFormat=source.format.ToString(),targetFormat=target?target.format.ToString():"backbuffer",colorSpace=QualitySettings.activeColorSpace.ToString(),inputSrgb=source.sRGB,targetSrgb=target&&target.sRGB,colourControl=ColourControl,materialControl=Cinder.Host.StandaloneHost.Arg("-material-control","none"),lightingControl=Cinder.Host.StandaloneHost.Arg("-lighting-control","none"),centerLinearRgb=new[]{c.r,c.g,c.b},sampleCoordinates=coordinates,linearSamples=samples},true));recorded=true;
   }
   if(!material)material=new Material(Shader.Find("Cinder/Grade"));
   // FXAA must filter the already tone-mapped/display-encoded image. Filtering
   // bright HDR samples before tone mapping leaves subpixel chrome saturated.
   Texture input=source;
   if(ColourControl){if(!control){control=new Texture2D(6,1,TextureFormat.RGBAFloat,false,true);control.filterMode=FilterMode.Point;control.wrapMode=TextureWrapMode.Clamp;control.SetPixels(new[]{new Color(.003f,.003f,.003f,1),new Color(.18f,.18f,.18f,1),Color.white,new Color(.5f,0,0,1),new Color(0,.5f,0,1),new Color(0,0,.5f,1)});control.Apply();}input=control;}
   string lighting=Cinder.Host.StandaloneHost.Arg("-lighting-control","none");
   bool legacy=lighting=="legacy",bloom=!ColourControl&&!legacy&&lighting!="bloom-off";
   // Keep display-encoded values in half precision until FXAA finishes. Static
   // sub-LSB dither is applied only at the final display quantization, never UI.
   var display=RenderTexture.GetTemporary(source.width,source.height,0,legacy?RenderTextureFormat.ARGB32:RenderTextureFormat.ARGBHalf,RenderTextureReadWrite.Linear);
   display.filterMode=FilterMode.Bilinear;
   RenderTexture near=null,wide=null,glow=null;
   bool priorEncoding=GL.sRGBWrite;
   try{
    GL.sRGBWrite=false;
    if(bloom){
     int w=Mathf.Max(1,source.width/2),h=Mathf.Max(1,source.height/2);
     near=RenderTexture.GetTemporary(w,h,0,RenderTextureFormat.ARGBHalf,RenderTextureReadWrite.Linear);
     wide=RenderTexture.GetTemporary(Mathf.Max(1,w/2),Mathf.Max(1,h/2),0,RenderTextureFormat.ARGBHalf,RenderTextureReadWrite.Linear);
     glow=RenderTexture.GetTemporary(w,h,0,RenderTextureFormat.ARGBHalf,RenderTextureReadWrite.Linear);
     foreach(var rt in new[]{near,wide,glow}){rt.filterMode=FilterMode.Bilinear;rt.wrapMode=TextureWrapMode.Clamp;}
     Graphics.Blit(source,near,material,2);Graphics.Blit(near,wide,material,3);
     material.SetTexture("_NearBloom",near);Graphics.Blit(wide,glow,material,4);
    }
    material.SetTexture("_BloomTex",glow?(Texture)glow:Texture2D.blackTexture);
    material.SetFloat("_BloomStrength",bloom?.10f:0);
    material.SetFloat("_DitherStrength",!legacy&&lighting!="dither-off"?.5f/255:0);
    Graphics.Blit(input,display,material,0);
    GL.sRGBWrite=QualitySettings.activeColorSpace==ColorSpace.Linear&&(!target||target.sRGB);Graphics.Blit(display,target,material,1);
   }
   finally{GL.sRGBWrite=priorEncoding;RenderTexture.ReleaseTemporary(display);if(near)RenderTexture.ReleaseTemporary(near);if(wide)RenderTexture.ReleaseTemporary(wide);if(glow)RenderTexture.ReleaseTemporary(glow);}
  }
  void OnDestroy(){if(material)Destroy(material);if(control)Destroy(control);}
 }
}
