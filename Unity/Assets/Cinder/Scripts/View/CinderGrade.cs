using UnityEngine;
namespace Cinder.View {
 [RequireComponent(typeof(Camera))] public sealed class CinderGrade:MonoBehaviour {
  Material material;
  void OnRenderImage(RenderTexture source,RenderTexture target){if(!material)material=new Material(Shader.Find("Cinder/Grade"));Graphics.Blit(source,target,material);}
  void OnDestroy(){if(material)Destroy(material);}
 }
}
