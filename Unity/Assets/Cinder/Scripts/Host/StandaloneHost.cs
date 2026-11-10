using System;
using System.IO;
using System.Linq;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using Cinder.Sim;
using UnityEngine;
using Unity.Profiling;
using Debug=UnityEngine.Debug;

namespace Cinder.Host {
 public sealed class StandaloneHost:MonoBehaviour,IHostWorld,IHostAudio {
  public const string DefaultRevision="cinder-unity-r1";
  public Transform Root=>transform;
  CinderModule module;Camera cam;Light sun;string page="garage",returnPage="garage",evidence,revision;
  int selected=4,world=1,area,focus,tab,frame,warmup,frames,mode;bool paused=true,capture,probe,silent,quit,reverse,boost,padHints,wasStick;
  float sensitivity=1;bool invert;int fps=60,window=0,vsync;float uiScale;double watchdog=120;readonly Stopwatch uptime=new Stopwatch(),frameClock=new Stopwatch();
  List<double> frameTimes=new List<double>();readonly int[] lowriders={4,5,6};GUIStyle title,body,small,button,big,eyebrow;Texture2D pixel;RenderTexture captureTarget;Texture2D capturePixels;
  PadState pad,previousPad;List<(string,Action)> menuActions=new List<(string,Action)>();float menuNext;MenuCanvas painter;Vector2 lastMouse;bool mouseMoved,serviceOpen,topRaised;float panelPhase,roofPhase;Dictionary<string,AudioClip> cueClips=new Dictionary<string,AudioClip>();List<AudioSource> voices=new List<AudioSource>();int voice;
  ProfilerRecorder drawCounter;int maximumDrawCalls;string materialControl="none";readonly HashSet<Material> controlledMaterials=new HashSet<Material>();
  bool uiProbe;int uiTick,savedFps,savedVsync;long pausedTick;readonly List<string> uiChecks=new List<string>();
  [Serializable] class Perf {public string revision,vehicle,world,fingerprint,scope;public int frames;public double medianMs,p99Ms;public long peakWorkingSetBytes,triangles;public int renderers;public int maximumDrawCalls;public bool drawCounterAvailable;public bool handheldVerified=false;}
  [Serializable] class AmbientProbeAsset {public int version=0;public bool whiteFurnacePass=false,hemispherePass=false;public float[] coefficients=null;}
  [Serializable] class MaterialControlReceipt {public string control,scope,ambientMode,ambientInputEncoding;public Color ambientLight;public float reflectionIntensity;public int standardMaterials,localReflectionProbesDisabled;}
  [Serializable] class PoseReceipt {public long tick;public string fingerprint;public SimState state;public SimInput input;public float panelPhase,roofPhase;}
  public static string Arg(string name,string fallback=""){var a=Environment.GetCommandLineArgs();int i=Array.IndexOf(a,name);return i>=0&&i+1<a.Length?a[i+1]:fallback;}
  public static bool Has(string name)=>Environment.GetCommandLineArgs().Contains(name);
  int IntArg(string name,int fallback)=>int.TryParse(Arg(name),out int n)?n:fallback;
  void Awake(){
   uptime.Start();frameClock.Start();probe=Has("-probe");capture=Has("-capture");uiProbe=Has("-ui-probe");silent=Has("-silent")||capture||probe;Application.wantsToQuit+=WantsQuit;
   evidence=Arg("-evidence",Path.Combine(Application.persistentDataPath,"reviews",DateTime.UtcNow.ToString("yyyyMMdd-HHmmss")));Directory.CreateDirectory(evidence);
   revision=Resources.Load<TextAsset>("Cinder/build")?.text.Trim()??DefaultRevision;
   if(Arg("-module","cinder-drive")!="cinder-drive"){Debug.LogError("Unknown module");Application.Quit(1);return;}
   watchdog=IntArg("-watchdog",capture?145:3600);warmup=IntArg("-warmup",120);frames=IntArg("-frames",180);area=Math.Clamp(IntArg("-area",0),0,7);mode=Math.Clamp(IntArg("-mode",0),0,8);
   if(probe){StartCoroutine(Probe());return;}
   materialControl=capture?Arg("-material-control","none"):"none";
   if(!new[]{"none","standard","ambient","reflection-off","reflection-direction","coat-normal","cube-lod0","cube-filtered","cube-decode","white-coat","sun-radiance"}.Contains(materialControl)){Debug.LogError("Unknown capture material control: "+materialControl);Application.Quit(1);return;}
   selected=VehicleCatalog.Index(Arg("-vehicle","catrina"));world=Arg("-world","city")=="city"?1:Arg("-world")=="forest"?2:0;
   fps=PlayerPrefs.GetInt("cinder.fps",60);vsync=PlayerPrefs.GetInt("cinder.vsync",0);savedFps=fps;savedVsync=vsync;window=PlayerPrefs.GetInt("cinder.window",0);sensitivity=PlayerPrefs.GetFloat("cinder.sensitivity",1);invert=PlayerPrefs.GetInt("cinder.invert",0)==1;
   Application.runInBackground=capture;AudioListener.pause=silent;Cursor.lockState=CursorLockMode.None;Cursor.visible=true;ApplySettings();
   var cameraObject=new GameObject("Host camera");cam=cameraObject.AddComponent<Camera>();cam.renderingPath=RenderingPath.Forward;cam.allowHDR=true;var grade=cameraObject.AddComponent<Cinder.View.CinderGrade>();grade.EvidenceDirectory=capture?evidence:null;grade.ColourControl=capture&&Has("-colour-probe");cam.clearFlags=CameraClearFlags.Skybox;cam.backgroundColor=new Color(.58f,.65f,.68f);cameraObject.AddComponent<AudioListener>();
   UnityEngine.Rendering.GraphicsSettings.lightsUseLinearIntensity=true;
   sun=new GameObject("Host afternoon sun").AddComponent<Light>();sun.type=LightType.Directional;sun.transform.rotation=Quaternion.LookRotation(-new Vector3(-.6331052f,.7430080f,-.2170646f),Vector3.up);sun.color=new Color(1,.9411765f,.8509804f);sun.intensity=2.9f/Mathf.PI;sun.shadows=LightShadows.Soft;sun.shadowCustomResolution=512;sun.shadowBias=.02f;sun.shadowNormalBias=.018f;
   RenderSettings.fog=true;RenderSettings.fogMode=FogMode.ExponentialSquared;RenderSettings.fogDensity=.0018f;RenderSettings.fogColor=new Color(.7137255f,.7843137f,.8313725f);
   // RenderSettings reflection strength reaches the GPU through gamma decoding;
   // encode the intended native linear .65 once. The r19/r20 GPU controls bind this.
   var skyTex=Resources.Load<Texture2D>("Cinder/sky-oriented");if(skyTex){var sky=new Material(Shader.Find("Skybox/Panoramic"));sky.SetTexture("_MainTex",skyTex);sky.SetFloat("_Rotation",0);sky.SetFloat("_Exposure",1);RenderSettings.skybox=sky;}var reflection=Resources.Load<Cubemap>("Cinder/sky-reflection-native");if(reflection){RenderSettings.defaultReflectionMode=UnityEngine.Rendering.DefaultReflectionMode.Custom;RenderSettings.customReflectionTexture=reflection;RenderSettings.reflectionIntensity=Mathf.LinearToGammaSpace(.65f);}
   ApplyBakedAmbientProbe();
   if(!silent){foreach(string name in new[]{"engine","pump","landing","impact"})cueClips[name]=Resources.Load<AudioClip>("Cinder/Audio/"+name);for(int i=0;i<12;i++){var source=new GameObject("Host event voice").AddComponent<AudioSource>();source.transform.SetParent(transform,false);source.playOnAwake=false;source.spatialBlend=.75f;source.minDistance=3;source.maxDistance=70;source.rolloffMode=AudioRolloffMode.Logarithmic;voices.Add(source);}}
   drawCounter=ProfilerRecorder.StartNew(ProfilerCategory.Render,"Draw Calls Count",1);painter=new MenuCanvas(cam);ResetModule();if(capture){page=Has("-menu")?"garage":"";paused=page!="";Time.captureFramerate=30;cam.enabled=false;painter.Camera.enabled=false;captureTarget=new RenderTexture(960,600,24,RenderTextureFormat.ARGB32);capturePixels=new Texture2D(960,600,TextureFormat.RGB24,false);StartCoroutine(CaptureFrames());}
  }
  IEnumerator Probe(){yield return null;try{var report=SimProbe.Run();foreach(var line in report.Lines)Debug.Log(line);Debug.Log((report.Success?"PASS ":"FAIL ")+"Fingerprint "+report.Fingerprint);File.WriteAllLines(Path.Combine(evidence,"probe.txt"),report.Lines.Concat(new[]{"Fingerprint "+report.Fingerprint}));File.WriteAllText(Path.Combine(evidence,"probe.json"),JsonUtility.ToJson(report,true));for(int i=0;i<report.Replays.Count;i++)File.WriteAllText(Path.Combine(evidence,"replay-"+i+".json"),JsonUtility.ToJson(report.Replays[i]));var rigs=Cinder.View.LoadedRigProbe.Run();foreach(string line in rigs.Lines)Debug.Log(line);File.WriteAllText(Path.Combine(evidence,"loaded-rig-probe.json"),JsonUtility.ToJson(rigs,true));var batches=Cinder.View.RuntimeBatchProbe.Run();foreach(string line in batches.Lines)Debug.Log(line);File.WriteAllText(Path.Combine(evidence,"runtime-batch-probe.json"),JsonUtility.ToJson(batches,true));Application.Quit(report.Success&&rigs.Success&&batches.Success?0:1);}catch(Exception e){Debug.LogException(e);File.WriteAllText(Path.Combine(evidence,"probe-failure.txt"),e.ToString());Application.Quit(1);}}
  void ResetModule(){
   SaveReplay();module?.Exit();reverse=false;serviceOpen=false;topRaised=false;panelPhase=roofPhase=0;module=new CinderModule{Vehicle=selected,Area=area,World=world,Mode=mode,Autodrive=Has("-autodrive"),ReviewScript=Arg("-review-script"),Daydream=Has("-daydream"),CameraMode=Math.Clamp(IntArg("-camera",0),0,6),LookSensitivity=sensitivity,InvertLook=invert};
   module.Enter(new ModuleContext{Frame=new Frame{Origin=Vector3.zero,Rotation=Quaternion.identity,Scale=1},Clock=()=>uptime.Elapsed.TotalSeconds,Seed=619,Audio=this,World=this});if(page=="garage"&&world==1){var state=module.Sim.State.Clone();state.Position.Z=65;module.Sim.Restore(state);module.Replay.Initial=state.Clone();}module.View.Pose(module.Sim.State);ApplyMaterialControl();module.Pose(cam);
  }
  void ApplyBakedAmbientProbe(){
   var source=Resources.Load<TextAsset>("Cinder/ambient-sh");if(!source)throw new InvalidOperationException("Missing CPU-baked native ambient SH");
   var asset=JsonUtility.FromJson<AmbientProbeAsset>(source.text);
   if(asset==null||asset.version!=1||!asset.whiteFurnacePass||!asset.hemispherePass||asset.coefficients==null||asset.coefficients.Length!=27||asset.coefficients.Any(value=>float.IsNaN(value)||float.IsInfinity(value)))throw new InvalidOperationException("Invalid CPU-baked native ambient SH");
   var sh=new UnityEngine.Rendering.SphericalHarmonicsL2();for(int channel=0;channel<3;channel++)for(int coefficient=0;coefficient<9;coefficient++)sh[channel,coefficient]=asset.coefficients[channel*9+coefficient];
   RenderSettings.ambientMode=UnityEngine.Rendering.AmbientMode.Skybox;RenderSettings.ambientIntensity=1;RenderSettings.ambientProbe=sh;
   if(capture)File.WriteAllText(Path.Combine(evidence,"ambient-probe-runtime.json"),source.text);
  }
  void ApplyMaterialControl(){
   if(!capture)return;int disabledProbes=0;
   Shader.SetGlobalFloat("_CinderMaterialDiagnostic",Array.IndexOf(new[]{"reflection-direction","coat-normal","cube-lod0","cube-filtered","cube-decode","white-coat","sun-radiance"},materialControl)+1);
   if(materialControl=="ambient"){
    // Diagnostic authored linear RGB .2, encoded explicitly for Unity's colour
    // API. This is an isolated flat-fill control, not an accepted lighting tune.
    RenderSettings.ambientMode=UnityEngine.Rendering.AmbientMode.Flat;
    RenderSettings.ambientLight=new Color(.2f,.2f,.2f,1).gamma;RenderSettings.ambientIntensity=1;
   }
   if(materialControl=="reflection-off"){
    RenderSettings.reflectionIntensity=0;
    foreach(var reflection in module.View.Root.GetComponentsInChildren<ReflectionProbe>(true)){reflection.intensity=0;disabledProbes++;}
   }
   if(materialControl=="standard"){
    var standard=Shader.Find("Standard");if(!standard)throw new InvalidOperationException("Standard material diagnostic shader missing");
    foreach(Transform car in module.View.Root){
     if(car!=module.View.Car&&!car.name.StartsWith(module.Sim.Tune.Id+"-",StringComparison.Ordinal))continue;
     foreach(var renderer in car.GetComponentsInChildren<Renderer>(true))foreach(var material in renderer.sharedMaterials){
      if(!material||controlledMaterials.Contains(material)||material.renderQueue>=3000||material.shader.name!="Cinder/Body")continue;
      int queue=material.renderQueue;bool cutout=material.IsKeywordEnabled("CINDER_CUTOUT");
      material.shader=standard;material.SetFloat("_Mode",cutout?1:0);
      material.SetOverrideTag("RenderType",cutout?"TransparentCutout":"Opaque");
      if(cutout)material.EnableKeyword("_ALPHATEST_ON");else material.DisableKeyword("_ALPHATEST_ON");
      material.DisableKeyword("_ALPHABLEND_ON");material.DisableKeyword("_ALPHAPREMULTIPLY_ON");
      material.SetInt("_SrcBlend",(int)UnityEngine.Rendering.BlendMode.One);material.SetInt("_DstBlend",(int)UnityEngine.Rendering.BlendMode.Zero);material.SetInt("_ZWrite",1);material.renderQueue=queue;
      if(material.GetColor("_EmissionColor").maxColorComponent>0)material.EnableKeyword("_EMISSION");
      controlledMaterials.Add(material);
     }
    }
   }
   File.WriteAllText(Path.Combine(evidence,"material-control.json"),JsonUtility.ToJson(new MaterialControlReceipt{control=materialControl,scope="Capture-only single-variable rendering diagnostic. Standard removes custom coat/GI/surface and does not consume donor vertex colour; this is not a visual acceptance result.",ambientMode=RenderSettings.ambientMode.ToString(),ambientInputEncoding=materialControl=="ambient"?"authored linear RGB 0.2 encoded with Color.gamma before RenderSettings.ambientLight":"unchanged",ambientLight=RenderSettings.ambientLight,reflectionIntensity=RenderSettings.reflectionIntensity,standardMaterials=controlledMaterials.Count,localReflectionProbesDisabled=disabledProbes},true));
  }
  void SaveReplay(){if(module?.Replay!=null&&module.Replay.Inputs.Count>0)File.WriteAllText(Path.Combine(evidence,"replay-last.json"),JsonUtility.ToJson(module.Replay));}
  void ApplySettings(){
   Application.targetFrameRate=capture?30:fps;QualitySettings.vSyncCount=capture?0:vsync;QualitySettings.antiAliasing=0;QualitySettings.shadowDistance=18;QualitySettings.shadowResolution=ShadowResolution.Low;QualitySettings.shadowCascades=0;
   if(capture)Screen.SetResolution(960,600,FullScreenMode.Windowed);else {var resolution=Screen.currentResolution;Screen.SetResolution(window==1?Math.Min(1600,resolution.width):resolution.width,window==1?Math.Min(900,resolution.height):resolution.height,window==0?FullScreenMode.FullScreenWindow:window==1?FullScreenMode.Windowed:FullScreenMode.ExclusiveFullScreen);}
   PlayerPrefs.SetInt("cinder.fps",fps);PlayerPrefs.SetInt("cinder.vsync",vsync);PlayerPrefs.SetInt("cinder.window",window);PlayerPrefs.SetFloat("cinder.sensitivity",sensitivity);PlayerPrefs.SetInt("cinder.invert",invert?1:0);PlayerPrefs.Save();
  }
  PadState ReadPad(){
   bool a=Input.GetKey(KeyCode.JoystickButton0)||Input.GetKey(KeyCode.Space),b=Input.GetKey(KeyCode.JoystickButton1),start=Input.GetKey(KeyCode.JoystickButton7)||Input.GetKey(KeyCode.Escape);
   var p=new PadState{Left=new Vector2(Input.GetAxisRaw("Horizontal"),Input.GetAxisRaw("Vertical")),Right=new Vector2(Input.GetAxisRaw("RightStickX"),Input.GetAxisRaw("RightStickY")),LT=Mathf.Max(0,Input.GetAxisRaw("LeftTrigger"),Input.GetKey(KeyCode.S)?1:0,Input.GetKey(KeyCode.LeftControl)?1:0),RT=Mathf.Max(0,Input.GetAxisRaw("RightTrigger"),Input.GetKey(KeyCode.W)?1:0,Input.GetKey(KeyCode.LeftShift)?1:0),A=a,B=b,X=Input.GetKey(KeyCode.JoystickButton2)||Input.GetKey(KeyCode.Q),Y=Input.GetKey(KeyCode.JoystickButton3)||Input.GetKey(KeyCode.F),LB=Input.GetKey(KeyCode.JoystickButton4),RB=Input.GetKey(KeyCode.JoystickButton5),Start=start,View=Input.GetKey(KeyCode.JoystickButton6)||Input.GetKey(KeyCode.F1),ADown=Input.GetKeyDown(KeyCode.JoystickButton0)||Input.GetKeyDown(KeyCode.Return)||(page!="garage"&&Input.GetKeyDown(KeyCode.E))||Input.GetKeyDown(KeyCode.Space),BDown=Input.GetKeyDown(KeyCode.JoystickButton1),StartDown=Input.GetKeyDown(KeyCode.JoystickButton7)||Input.GetKeyDown(KeyCode.Escape)};
   if(Input.GetMouseButton(1))p.Right+=new Vector2(Input.GetAxisRaw("Mouse X"),-Input.GetAxisRaw("Mouse Y"));
   if(Input.GetKeyDown(KeyCode.JoystickButton9)){module.LookYaw=0;module.LookPitch=17;}
   return p;
  }
  void Update(){
   if(uptime.Elapsed.TotalSeconds>watchdog){WritePerf();quit=true;Application.Quit(capture?1:0);return;}if(probe||module==null)return;
   pad=uiProbe?ScriptedUiPad(uiTick):ReadPad();UpdateHints(pad);if(!capture||uiProbe){
    if(pad.StartDown){if(page==""){page="pause";paused=true;focus=0;}else if(page=="pause"){page="";paused=false;}else if(page=="settings"){page=returnPage;focus=0;}else if(page=="quit"){page=returnPage;focus=0;}}
    if(pad.BDown&&page!=""){page=page=="garage"?"quit":returnPage;focus=0;}
    if(page!="")Navigate();else{
     if(Input.GetKeyDown(KeyCode.G)||(pad.RB&&!previousPad.RB)){reverse=!reverse;module.Reverse=reverse;}
     if(Input.GetKeyDown(KeyCode.R)||(pad.LB&&!previousPad.LB)){ResetModule();}
     if(Input.GetKeyDown(KeyCode.C)||Input.GetKeyDown(KeyCode.JoystickButton8))module.CameraMode=(module.CameraMode+1)%7;
     if(Input.GetKeyDown(KeyCode.J)){mode=1;module.Mode=mode;}if(Input.GetKeyDown(KeyCode.K)){mode=selected==4?2:2;module.Mode=mode;}if(Input.GetKeyDown(KeyCode.L)){mode=3;module.Mode=mode;}if(Input.GetKeyDown(KeyCode.N)){mode=0;module.Mode=mode;}
    }
   }
   if(!paused)module.Tick(capture?1f/30:Time.unscaledDeltaTime,in pad);
   if(Math.Abs(module.Sim.Speed)<.5){if(Input.GetKeyDown(KeyCode.F1)||Input.GetKeyDown(KeyCode.JoystickButton2))serviceOpen=!serviceOpen;if(selected==6&&(Input.GetKeyDown(KeyCode.T)||Input.GetKeyDown(KeyCode.JoystickButton6)))topRaised=!topRaised;}else serviceOpen=false;
   if(capture&&selected==6&&Has("-roof-cycle"))topRaised=module.Sim.Time<14.5;
   float visualDt=capture?1f/30:Time.unscaledDeltaTime;panelPhase=Mathf.MoveTowards(panelPhase,serviceOpen?1:0,visualDt);roofPhase=Mathf.MoveTowards(roofPhase,topRaised?1:0,visualDt/14);module.View.Panels(panelPhase,roofPhase);
   if(page=="garage"){float angle=24+(float)Math.Sin(uptime.Elapsed.TotalSeconds*.12)*8;module.View.GarageCamera(cam,angle);}else module.Pose(cam);
   if(module.Result!=null){page="result";paused=true;}
   mouseMoved=((Vector2)Input.mousePosition-lastMouse).sqrMagnitude>.01f;lastMouse=Input.mousePosition;DrawMenu();
   if(uiProbe){CheckUiFrame();uiTick++;}previousPad=pad;
   if(frameClock.IsRunning){frameTimes.Add(frameClock.Elapsed.TotalMilliseconds);frameClock.Restart();}
  }
  void UpdateHints(PadState p){bool active=p.Left.sqrMagnitude>.04f||p.Right.sqrMagnitude>.04f||p.LT>.1f||p.RT>.1f||p.A||p.B||p.X||p.Y||p.LB||p.RB||p.Start||p.View||p.ADown||p.BDown||p.StartDown;if(active||(!uiProbe&&(Mathf.Abs(Input.GetAxisRaw("DPadX"))+Mathf.Abs(Input.GetAxisRaw("DPadY"))>.2f)))padHints=true;if(!uiProbe){bool keyboard=new[]{KeyCode.W,KeyCode.A,KeyCode.S,KeyCode.D,KeyCode.UpArrow,KeyCode.DownArrow,KeyCode.LeftArrow,KeyCode.RightArrow,KeyCode.LeftShift,KeyCode.LeftControl,KeyCode.Space,KeyCode.Q,KeyCode.E,KeyCode.F,KeyCode.R,KeyCode.G,KeyCode.C,KeyCode.T,KeyCode.F1,KeyCode.Return,KeyCode.Escape}.Any(Input.GetKey);if(keyboard||Input.GetMouseButton(0)||Input.GetMouseButton(1)||Input.inputString.Length>0)padHints=false;}}
  void Navigate(){
   float y=pad.Left.y+Input.GetAxisRaw("DPadY");bool stick=Mathf.Abs(y)>.5f;
   if(stick&&(!wasStick||Time.unscaledTime>menuNext)){focus=Math.Clamp(focus+(y<0?1:-1),0,Math.Max(0,menuActions.Count-1));menuNext=Time.unscaledTime+.2f;}wasStick=stick;
   if(pad.ADown&&menuActions.Count>0){int index=Math.Clamp(focus,0,menuActions.Count-1);menuActions[index].Item2();}
   if(page=="garage"&&((pad.LB&&!previousPad.LB)||Input.GetKeyDown(KeyCode.Q)))CycleCar(-1);
   if(page=="garage"&&((pad.RB&&!previousPad.RB)||Input.GetKeyDown(KeyCode.E)))CycleCar(1);
  }
  void CycleCar(int direction){int n=Array.IndexOf(lowriders,selected);selected=lowriders[(n+direction+3)%3];mode=0;ResetModule();}
  void OnApplicationFocus(bool hasFocus){if(!hasFocus&&!capture&&module!=null){paused=true;if(page=="")page="pause";}}
  bool WantsQuit(){if(quit||capture||probe)return true;returnPage=page==""?"pause":page;page="quit";paused=true;focus=0;return false;}
  void OnApplicationQuit(){if(drawCounter.Valid)drawCounter.Dispose();SaveReplay();WritePerf();if(uiProbe){PlayerPrefs.SetInt("cinder.fps",savedFps);PlayerPrefs.SetInt("cinder.vsync",savedVsync);PlayerPrefs.Save();}module?.Exit();}
  public void Cue(string id,Vector3 position,float value,double delaySeconds){
   if(silent||voices.Count==0||!cueClips.TryGetValue(id,out var clip)||!clip)return;var source=voices[voice++%voices.Count];source.transform.position=position;source.clip=clip;source.volume=Mathf.Clamp01(id=="engine"?.6f+.4f*value:.7f);source.pitch=id=="engine"?.8f+.45f*value:1;double delay=Vector3.Distance(cam.transform.position,position)/343.0;source.PlayScheduled(AudioSettings.dspTime+delay);
  }
  void Styles(){if(title!=null)return;title=new GUIStyle{fontSize=94,fontStyle=FontStyle.Bold};title.normal.textColor=new Color(.96f,.91f,.79f);body=new GUIStyle{fontSize=26,wordWrap=true};body.normal.textColor=new Color(.91f,.89f,.83f);small=new GUIStyle(body){fontSize=24};eyebrow=new GUIStyle(body){fontSize=22,fontStyle=FontStyle.Bold};eyebrow.normal.textColor=new Color(.93f,.55f,.23f);big=new GUIStyle(body){fontSize=48,fontStyle=FontStyle.Bold};button=new GUIStyle(body){fontSize=25};}
  void Fill(Rect r,Color c)=>painter.Fill(r,c);
  void Label(float x,float y,float w,float h,string text,GUIStyle style=null){var s=style??body;painter.Text(new Rect(x,y,w,h),text,s.fontSize,s.normal.textColor,s.fontStyle==FontStyle.Bold);}
  Vector2 Pointer=>new Vector2(Input.mousePosition.x/uiScale,(Screen.height-Input.mousePosition.y)/uiScale);
  void Button(float x,float y,float w,string text,Action action){int n=menuActions.Count;menuActions.Add((text,action));var r=new Rect(x,y,w,58);if(mouseMoved&&r.Contains(Pointer))focus=n;Fill(r,focus==n?new Color(.72f,.29f,.08f):new Color(.12f,.15f,.16f));if(focus==n)Fill(new Rect(x,y,4,58),new Color(1,.69f,.32f));Label(x+22,y+13,w-38,40,text,button);if(Input.GetMouseButtonDown(0)&&r.Contains(Pointer)){focus=n;action();}}
  void DrawMenu(){if(probe||module==null||painter==null)return;painter.Begin();if(!Has("-clean"))DrawMenuContent();painter.End();}
  void DrawMenuContent(){Styles();uiScale=Screen.height/1080f;float width=Screen.width/uiScale;menuActions.Clear();
   if(page==""){
    Fill(new Rect(24,950,width-48,100),new Color(.045f,.06f,.065f,.88f));Label(50,969,width-100,40,$"{module.Sim.Tune.Name}   {Math.Abs(module.Sim.Speed):F1} m/s   {module.Sim.ContactCount}/4 tyres   {(module.Reverse?"REVERSE":"DRIVE")}   {module.ModeName}");Label(50,1010,width-100,32,padHints?"RT / LT pedals   A handbrake   Y hydraulics   LB reset   RB reverse   Start pause":"W / S pedals   A / D steer   Space handbrake   F hydraulics   R reset   C camera   Esc pause",small);return;
   }
   Fill(new Rect(0,0,page=="garage"?690:width,1080),new Color(.035f,.05f,.055f,page=="garage"?.94f:.86f));
   if(page=="garage"){
    Label(64,58,560,35,"SMITHBUILDER   /   LOWRIDER CULTURE",eyebrow);Label(56,105,610,120,"CINDER",title);Fill(new Rect(64,246,72,4),new Color(.91f,.42f,.14f));Label(64,272,560,100,"Slow streets.\nA little more soul.",big);Label(64,402,548,94,"Cruise Mercer. Work the hydraulics.\nMake the street your stage.",body);
    Button(64,526,548,"CRUISE MERCER",()=>StartDrive(1));Button(64,600,548,selected==6?"AIR SESSION":"HYDRAULIC SESSION",()=>{mode=1;StartDrive(1);});Button(64,674,548,"WORKSHOP / TEST GROUNDS",()=>StartDrive(0));Button(64,748,548,"SETTINGS",()=>{returnPage="garage";page="settings";focus=0;});Button(64,822,548,"QUIT",()=>{returnPage="garage";page="quit";focus=0;});
    Fill(new Rect(745,820,width-809,188),new Color(.035f,.05f,.055f,.90f));Label(776,839,width-870,32,"THE CURRENT GARAGE",eyebrow);Label(776,878,width-870,62,module.Sim.Tune.Name,big);Label(776,951,width-870,36,padHints?"LB / RB choose   X coachwork":"Q / E choose   F1 coachwork",small);
    Button(width-244,866,72,"<",()=>CycleCar(-1));Button(width-156,866,72,">",()=>CycleCar(1));
    Label(64,989,560,55,"MERCER DISTRICT / AFTERNOON",small);return;
   }
   float left=(width-760)/2;Label(left,120,900,90,page=="pause"?"TAKE A BREATHER":page=="settings"?"MAKE IT YOURS":page=="quit"?"LEAVE THE STREET?":"DRIVE COMPLETE",big);
   if(page=="pause"){
    Button(left,280,760,"KEEP CRUISING",()=>{page="";paused=false;});Button(left,360,760,"CAMERA / "+(module.CameraMode+1),()=>module.CameraMode=(module.CameraMode+1)%7);Button(left,440,760,"HYDRAULICS / "+module.ModeName.ToUpperInvariant(),()=>module.Mode=(module.Mode+1)%(selected==4?5:selected==5?3:9));Button(left,520,760,"SETTINGS",()=>{returnPage="pause";page="settings";focus=0;});Button(left,600,760,"RETURN TO GARAGE",()=>{ReturnGarage();});Button(left,680,760,"QUIT",()=>{returnPage="pause";page="quit";focus=0;});
   }else if(page=="settings"){
    Button(left,270,760,"FRAME LIMIT / "+fps,()=>{fps=fps==30?60:fps==60?120:30;ApplySettings();});Button(left,350,760,"V-SYNC / "+(vsync==0?"OFF":"ON"),()=>{vsync=1-vsync;ApplySettings();});Button(left,430,760,"DISPLAY / "+new[]{"BORDERLESS","WINDOWED","EXCLUSIVE"}[window],()=>{window=(window+1)%3;ApplySettings();});Button(left,510,760,"INVERT LOOK / "+(invert?"ON":"OFF"),()=>{invert=!invert;module.InvertLook=invert;ApplySettings();});Button(left,590,760,"LOOK SENSITIVITY / "+sensitivity.ToString("F1"),()=>{sensitivity=sensitivity>=2?.5f:sensitivity+.25f;module.LookSensitivity=sensitivity;ApplySettings();});Fill(new Rect(left,698,760,4),new Color(.3f,.34f,.34f));Fill(new Rect(left+(sensitivity-.5f)/1.5f*716,680,44,44),new Color(.93f,.55f,.23f));if(Input.GetMouseButton(0)&&new Rect(left,680,760,44).Contains(Pointer)){sensitivity=Mathf.Lerp(.5f,2,Mathf.Clamp01((Pointer.x-left)/760));module.LookSensitivity=sensitivity;}
    Button(left,770,760,"BACK",()=>{ApplySettings();page=returnPage;focus=0;});
   }else if(page=="quit"){Label(left,250,760,80,"Your settings are saved. Ready to call it a night?",body);Button(left,390,760,"STAY HERE",()=>{page=returnPage;focus=0;});Button(left,480,760,"QUIT CINDER",()=>{quit=true;Application.Quit();});}
   else {Label(left,270,760,120,string.Join("\n",module.Result?.Lines??Array.Empty<string>()));Button(left,450,760,"RETURN TO GARAGE",()=>{ReturnGarage();});}
  }
  void ReturnGarage(){world=1;page="garage";paused=true;focus=0;ResetModule();}
  void StartDrive(int targetWorld){world=targetWorld;page="";paused=false;focus=0;ResetModule();}
  PadState ScriptedUiPad(int t){var p=new PadState();if(t==5||t==10)p.RB=true;if(t==15)p.LB=true;if(new[]{20,60,70,80,85,115,125,160,165}.Contains(t))p.ADown=true;if(new[]{50,130,170}.Contains(t))p.StartDown=true;if(new[]{55,65,75,95,100,105,110,135,140,145,150,155}.Contains(t))p.Left.y=-1;if(t==90)p.BDown=true;if(t>20&&t<50)p.RT=.4f;return p;}
  void CheckUiFrame(){bool check=false,ok=true;string name="";switch(uiTick){case 8:name="RB selects Media Luna without starting";ok=selected==5&&page=="garage"&&padHints;check=true;break;case 13:name="RB selects Nocturne";ok=selected==6&&page=="garage";check=true;break;case 18:name="LB selects previous lowrider";ok=selected==5&&page=="garage";check=true;break;case 23:name="A enters Mercer driving";ok=page==""&&!paused&&world==1;check=true;break;case 53:pausedTick=module.Sim.State.Tick;name="Start pauses";ok=page=="pause"&&paused;check=true;break;case 83:name="pad enters settings while sim stays paused";ok=page=="settings"&&module.Sim.State.Tick==pausedTick;check=true;break;case 93:name="B returns from settings";ok=page=="pause"&&module.Sim.State.Tick==pausedTick;check=true;break;case 118:name="pad returns to lowrider garage";ok=page=="garage"&&selected==5&&module.Sim.State.Tick==0;check=true;break;case 163:name="quit requires explicit confirmation";ok=page=="quit"&&!quit;check=true;break;case 168:name="cancel quit returns to pause";ok=page=="pause"&&!quit;check=true;break;}if(check)uiChecks.Add((ok?"PASS ":"FAIL ")+name+" page="+page+" vehicle="+selected+" tick="+module.Sim.State.Tick);}
  IEnumerator CaptureFrames(){
   for(int i=0;i<warmup+frames;i++){yield return new WaitForEndOfFrame();cam.targetTexture=captureTarget;Canvas.ForceUpdateCanvases();cam.Render();painter.Render(captureTarget);if(drawCounter.Valid)maximumDrawCalls=Math.Max(maximumDrawCalls,(int)drawCounter.LastValue);if(i<warmup){cam.targetTexture=null;continue;}var prior=RenderTexture.active;RenderTexture.active=captureTarget;capturePixels.ReadPixels(new Rect(0,0,960,600),0,0);capturePixels.Apply(false);RenderTexture.active=prior;cam.targetTexture=null;File.WriteAllBytes(Path.Combine(evidence,$"frame-{frame:D4}.png"),capturePixels.EncodeToPNG());if(frame%30==0)File.WriteAllText(Path.Combine(evidence,$"pose-{frame:D4}.json"),JsonUtility.ToJson(new PoseReceipt{tick=module.Sim.State.Tick,fingerprint=module.Sim.Fingerprint(),state=module.Sim.State.Clone(),input=module.LastInput,panelPhase=panelPhase,roofPhase=roofPhase},true));frame++;}
   WritePerf();SaveReplay();if(uiProbe){File.WriteAllLines(Path.Combine(evidence,"ui-probe.txt"),uiChecks);Application.Quit(uiChecks.Count==10&&uiChecks.All(x=>x.StartsWith("PASS "))?0:1);}else Application.Quit(0);
  }
  void WritePerf(){if(module==null)return;var a=frameTimes.Skip(30).OrderBy(x=>x).ToArray();module.View.MeasureBudget(out long triangleCount,out int rendererCount);var p=new Perf{revision=revision,vehicle=module.Sim.Tune.Id,world=world==1?"city":world==2?"forest":"playground",fingerprint=module.Sim.Fingerprint(),frames=frame,medianMs=a.Length>0?a[a.Length/2]:0,p99Ms=a.Length>0?a[Math.Min(a.Length-1,(int)(a.Length*.99))]:0,peakWorkingSetBytes=Process.GetCurrentProcess().PeakWorkingSet64,triangles=triangleCount,renderers=rendererCount,maximumDrawCalls=maximumDrawCalls,drawCounterAvailable=maximumDrawCalls>0,scope="Conservative 960x600/30 capture with PNG IO. Not a 1080p/60 handheld benchmark."};File.WriteAllText(Path.Combine(evidence,"performance.json"),JsonUtility.ToJson(p,true));}
 }
}
