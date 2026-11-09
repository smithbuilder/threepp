using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
namespace Cinder.Host {
 // The same camera-space canvas renders in the player and hidden review target.
 public sealed class MenuCanvas {
  readonly Canvas canvas;readonly List<GameObject> objects=new List<GameObject>();readonly Font font;int cursor;public Camera Camera {get;private set;}
  public MenuCanvas(Camera camera){Camera=new GameObject("Host interface camera").AddComponent<Camera>();Camera.cullingMask=1<<31;Camera.clearFlags=CameraClearFlags.Depth;Camera.depth=camera.depth+10;Camera.orthographic=true;Camera.orthographicSize=540;Camera.nearClipPlane=.01f;Camera.farClipPlane=10;Camera.transform.position=new Vector3(0,0,-1000);camera.cullingMask&=~(1<<31);var go=new GameObject("Cinder interface",typeof(RectTransform),typeof(Canvas),typeof(CanvasScaler));go.layer=31;canvas=go.GetComponent<Canvas>();canvas.renderMode=RenderMode.ScreenSpaceCamera;canvas.worldCamera=Camera;canvas.planeDistance=1;canvas.sortingOrder=100;var scaler=go.GetComponent<CanvasScaler>();scaler.uiScaleMode=CanvasScaler.ScaleMode.ScaleWithScreenSize;scaler.referenceResolution=new Vector2(1920,1080);scaler.screenMatchMode=CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;scaler.matchWidthOrHeight=1;font=Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");}
  public void Begin(){cursor=0;}
  GameObject Item(string kind,Rect r){GameObject g;if(cursor<objects.Count){g=objects[cursor];if(g.name!=kind){g.SetActive(false);Object.Destroy(g);g=Create(kind);objects[cursor]=g;}}else{g=Create(kind);objects.Add(g);}g.transform.SetSiblingIndex(cursor);cursor++;g.SetActive(true);var t=(RectTransform)g.transform;t.anchorMin=t.anchorMax=new Vector2(0,1);t.pivot=new Vector2(0,1);t.anchoredPosition=new Vector2(r.x,-r.y);t.sizeDelta=r.size;return g;}
  GameObject Create(string kind){var g=new GameObject(kind,typeof(RectTransform));g.layer=31;g.transform.SetParent(canvas.transform,false);if(kind=="text")g.AddComponent<Text>();else g.AddComponent<Image>();return g;}
  public void Fill(Rect r,Color color){var g=Item("fill",r);var im=g.GetComponent<Image>();im.color=color;im.raycastTarget=false;}
  public void Text(Rect r,string value,int size,Color color,bool bold=false){var g=Item("text",r);var t=g.GetComponent<Text>();t.font=font;t.text=value;t.fontSize=size;t.fontStyle=bold?FontStyle.Bold:FontStyle.Normal;t.color=color;t.alignment=TextAnchor.UpperLeft;t.horizontalOverflow=HorizontalWrapMode.Wrap;t.verticalOverflow=VerticalWrapMode.Overflow;t.raycastTarget=false;}
  public void End(){for(int i=cursor;i<objects.Count;i++)objects[i].SetActive(false);Canvas.ForceUpdateCanvases();}
  public void Render(RenderTexture target){Camera.targetTexture=target;Canvas.ForceUpdateCanvases();Camera.Render();Camera.targetTexture=null;}
 }
}
