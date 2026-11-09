using System;
using Cinder.Sim;
using Cinder.View;
using UnityEngine;
namespace Cinder.Host {
 public sealed class CinderModule:IGameModule {
  public ModuleInfo Info {get;}=new ModuleInfo{Id="cinder-drive",Name="Cinder",Verb="DRIVE",Controls="RT accelerate | LT brake | left stick steer | A handbrake",TypicalLengthSeconds=75};
  public ModuleResult Result {get;private set;}
  public VehicleSim Sim {get;private set;}public SimReplay Replay {get;private set;}
  public CinderView View {get;private set;}
  public int Vehicle,Area,World,Mode,CameraMode;public bool Reverse,Boost,Autodrive,Daydream;public string ReviewScript;
  public SimInput LastInput;public float LookYaw,LookPitch=17,LookSensitivity=1;public bool InvertLook;
  ModuleContext ctx;double accumulator;bool actionHeld;
  public void Enter(ModuleContext context){if(Sim!=null)throw new InvalidOperationException("Module already entered");ctx=context;Sim=new VehicleSim(Vehicle,Area,World==1,ctx.Seed);for(int i=0;i<300;i++)Sim.Step(new SimInput());var initial=Sim.State.Clone();initial.Tick=0;initial.Distance=0;initial.MaximumSpeed=0;if(World==1)initial.Position.Z=65;Sim.Restore(initial);Replay=new SimReplay(Sim.State);View=new CinderView(ctx,Sim,World);Result=null;accumulator=0;}
  public void Tick(float dt,in PadState pad){
   if(Sim==null||Result!=null)return;if(!float.IsFinite(dt)||dt<0)throw new ArgumentOutOfRangeException(nameof(dt));
   LookYaw+=pad.Right.x*LookSensitivity*dt*100;LookPitch=Mathf.Clamp(LookPitch+pad.Right.y*(InvertLook?1:-1)*LookSensitivity*dt*70,-8,65);
   var input=new SimInput{Throttle=pad.RT,Brake=pad.LT,Steer=pad.Left.x,Handbrake=pad.A,Reverse=Reverse,Boost=Boost&&pad.X,Mode=Mode};
   if(pad.Y&&!actionHeld){Mode=(Mode+1)%(Vehicle==4?5:Vehicle==5?3:Vehicle==6?9:1);input.Mode=Mode;}actionHeld=pad.Y;
   if(Autodrive){double desired=Area==6?10:Area==3?4:3;if(World==1){var s=Sim.State;double z=s.Position.Z;double targetX=z<110?-33:33;double yaw=Math.Atan2(s.Rotation.Rotate(new DVec3(0,0,1)).X,s.Rotation.Rotate(new DVec3(0,0,1)).Z);input.Throttle=Math.Clamp((desired-Sim.Speed)*.4,0,.8);input.Brake=Math.Clamp((Sim.Speed-desired)*.4,0,1);input.Steer=Math.Clamp((Math.Atan2(targetX-s.Position.X,12)-yaw)*1.4,-1,1);}else input=TrialAssist.Drive(Sim,desired,Boost);input.Mode=Mode;}
   if(ReviewScript=="culture-flow"){
    double t=Sim.Time;input=new SimInput();
    if(Vehicle==4){input.Mode=t<1?0:t<5?1:t<9?2:t<13?3:0;if(t>=15&&t<18){input.Throttle=.45;input.Steer=t<16?0:.15;}else if(t>=18&&t<19.5)input.Brake=1;else if(t>=19.5&&t<22.5){input.Reverse=true;input.Throttle=.35;}else if(t>=22.5){input.Reverse=true;input.Brake=1;}}
    else if(Vehicle==5)input.Mode=t<1?0:t<3?1:t<5?2:0;
    Mode=input.Mode;Reverse=input.Reverse;
   }
   LastInput=input;accumulator+=dt;int catchUp=0;while(accumulator>=VehicleSim.Dt&&catchUp++<120){Sim.Step(input);Replay.Inputs.Add(input);accumulator-=VehicleSim.Dt;}
   View.Pose(Sim.State);Drain();
   if(Daydream&&Sim.Time>=75){int tier=Sim.State.Distance>150?3:Sim.State.Distance>60?2:1;Result=new ModuleResult{Tier=tier,Lines=new[]{"Drive complete",$"Distance {Sim.State.Distance:F0} m"},Fingerprint=Sim.Fingerprint()};}
  }
  void Drain(){foreach(var e in Sim.Events){Vector3 p=View.Root.TransformPoint(CinderView.V(e.Position));double delay=Vector3.Distance(p,ctx.Frame.Origin)/343.0;ctx.Audio?.Cue(e.Kind,p,(float)e.Value,delay);}Sim.Events.Clear();}
  public void Pose(Camera cam){View?.Camera(cam,CameraMode,LookYaw,LookPitch);}
  public string ModeName {get{string[] modes=Vehicle==4?new[]{"Cruise low","Front hop","Three wheel left","Three wheel right","Raised ride"}:Vehicle==5?new[]{"Lower front","Pump front","Hold front"}:Vehicle==6?new[]{"Cruise height","Raise all","Hold height","Park low","Front left","Front right","Rear left","Rear right","Demonstration"}:new[]{"Cruise"};return modes[Math.Clamp(Mode,0,modes.Length-1)];}}
  public void Hud(Rect bar){if(Sim==null)return;GUI.Label(bar,$"{Sim.Tune.Name}   {Math.Abs(Sim.Speed):F1} m/s   {Sim.ContactCount}/4 tyres   {(Reverse?"REVERSE":"DRIVE")}   {ModeName}");}
  public void Exit(){View?.Dispose();View=null;Sim=null;Replay=null;ctx=null;accumulator=0;}
 }
}
