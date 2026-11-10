using UnityEngine;
using System.IO;
namespace Cinder.View {
 [RequireComponent(typeof(Camera))] public sealed class CinderGrade:MonoBehaviour {
  Material material;
  public string EvidenceDirectory;
  public bool ColourControl;
  Texture2D control;
  bool recorded;
  [System.Serializable] sealed class Diagnostic {public string inputFormat,targetFormat,colorSpace,materialControl;public bool inputSrgb,targetSrgb,colourControl;public float[] centerLinearRgb,sampleCoordinates,linearSamples;}
  void OnRenderImage(RenderTexture source,RenderTexture target){
   if(!recorded&&!string.IsNullOrEmpty(EvidenceDirectory)){
    var prior=RenderTexture.active;RenderTexture.active=source;var pixel=new Texture2D(1,1,TextureFormat.RGBAFloat,false,true);
    pixel.ReadPixels(new Rect(source.width/2,source.height/2,1,1),0,0);pixel.Apply();var c=pixel.GetPixel(0,0);
    var coordinates=new float[18];var samples=new float[27];int sample=0;
    foreach(int y in new[]{270,290,310})foreach(int x in new[]{400,480,600}){pixel.ReadPixels(new Rect(x,y,1,1),0,0);pixel.Apply();var p=pixel.GetPixel(0,0);coordinates[sample*2]=x;coordinates[sample*2+1]=y;samples[sample*3]=p.r;samples[sample*3+1]=p.g;samples[sample*3+2]=p.b;sample++;}
    Destroy(pixel);RenderTexture.active=prior;
    File.WriteAllText(Path.Combine(EvidenceDirectory,"render-diagnostics.json"),JsonUtility.ToJson(new Diagnostic{inputFormat=source.format.ToString(),targetFormat=target?target.format.ToString():"backbuffer",colorSpace=QualitySettings.activeColorSpace.ToString(),inputSrgb=source.sRGB,targetSrgb=target&&target.sRGB,colourControl=ColourControl,materialControl=Cinder.Host.StandaloneHost.Arg("-material-control","none"),centerLinearRgb=new[]{c.r,c.g,c.b},sampleCoordinates=coordinates,linearSamples=samples},true));recorded=true;
   }
   if(!material)material=new Material(Shader.Find("Cinder/Grade"));
   // FXAA must filter the already tone-mapped/display-encoded image. Filtering
   // bright HDR samples before tone mapping leaves subpixel chrome saturated.
   Texture input=source;
   if(ColourControl){if(!control){control=new Texture2D(6,1,TextureFormat.RGBAFloat,false,true);control.filterMode=FilterMode.Point;control.wrapMode=TextureWrapMode.Clamp;control.SetPixels(new[]{new Color(.003f,.003f,.003f,1),new Color(.18f,.18f,.18f,1),Color.white,new Color(.5f,0,0,1),new Color(0,.5f,0,1),new Color(0,0,.5f,1)});control.Apply();}input=control;}
   var display=RenderTexture.GetTemporary(source.width,source.height,0,RenderTextureFormat.ARGB32,RenderTextureReadWrite.Linear);
   display.filterMode=FilterMode.Bilinear;
   bool priorEncoding=GL.sRGBWrite;
   try{GL.sRGBWrite=false;Graphics.Blit(input,display,material,0);GL.sRGBWrite=QualitySettings.activeColorSpace==ColorSpace.Linear&&(!target||target.sRGB);Graphics.Blit(display,target,material,1);}
   finally{GL.sRGBWrite=priorEncoding;RenderTexture.ReleaseTemporary(display);}
  }
  void OnDestroy(){if(material)Destroy(material);if(control)Destroy(control);}
 }
}
