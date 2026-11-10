using System;
using UnityEngine;
namespace Cinder.Editor {
 public static class CubemapCardinals {
  [Serializable] public sealed class Sample {public string face;public float[] panorama,cube;public float relativeError;}
  public static Texture2D PrepareForCylindricalImport(Texture2D panorama){
   // Unity's cylindrical cube importer starts longitude one quarter-turn away
   // from Skybox/Panoramic. This was measured with six cardinal colour samples.
   var source=panorama.GetPixels();var target=new Color[source.Length];int width=panorama.width,height=panorama.height;
   for(int y=0;y<height;y++)for(int x=0;x<width;x++)target[y*width+x]=source[y*width+(x-width/4+width)%width];
   var result=new Texture2D(width,height,TextureFormat.RGBAFloat,false,true);result.wrapModeU=TextureWrapMode.Repeat;result.wrapModeV=TextureWrapMode.Clamp;result.SetPixels(target);result.Apply();return result;
  }
  public static Sample[] Read(Texture2D panorama,Cubemap cube){
   var faces=new[]{CubemapFace.PositiveX,CubemapFace.NegativeX,CubemapFace.PositiveY,CubemapFace.NegativeY,CubemapFace.PositiveZ,CubemapFace.NegativeZ};
   var directions=new[]{Vector3.right,Vector3.left,Vector3.up,Vector3.down,Vector3.forward,Vector3.back};
   var rows=new Sample[6];int a=cube.width/2-1,b=cube.width/2;
   for(int i=0;i<6;i++){Vector3 d=directions[i];float u=Mathf.Repeat(.5f-Mathf.Atan2(d.z,d.x)/(2*Mathf.PI),1),v=1-Mathf.Acos(d.y)/Mathf.PI;Color expected=panorama.GetPixelBilinear(u,v);Color actual=(cube.GetPixel(faces[i],a,a)+cube.GetPixel(faces[i],a,b)+cube.GetPixel(faces[i],b,a)+cube.GetPixel(faces[i],b,b))*.25f;float error=(new Vector3(expected.r-actual.r,expected.g-actual.g,expected.b-actual.b)).magnitude/Mathf.Max(.05f,new Vector3(expected.r,expected.g,expected.b).magnitude);rows[i]=new Sample{face=faces[i].ToString(),panorama=new[]{expected.r,expected.g,expected.b},cube=new[]{actual.r,actual.g,actual.b},relativeError=error};}
   return rows;
  }
 }
}
