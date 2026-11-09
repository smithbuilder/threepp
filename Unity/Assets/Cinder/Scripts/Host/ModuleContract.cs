using UnityEngine;
namespace Cinder.Host {
 public interface IGameModule {
  ModuleInfo Info {get;} void Enter(ModuleContext ctx);void Tick(float dt,in PadState pad);void Pose(Camera cam);void Hud(Rect bar);ModuleResult Result {get;}void Exit();
 }
 public sealed class ModuleInfo {public string Id,Name,Verb,Controls;public int TypicalLengthSeconds;}
 public sealed class ModuleContext {public Frame Frame;public System.Func<double> Clock;public int Seed;public IHostAudio Audio;public IHostWorld World;}
 public struct Frame {public Vector3 Origin;public Quaternion Rotation;public float Scale;}
 public struct PadState {public Vector2 Left,Right;public float LT,RT;public bool A,B,X,Y,LB,RB,Start,View;public bool ADown,BDown,StartDown;}
 public sealed class ModuleResult {public string[] Lines;public int Tier;public string Fingerprint;}
 public interface IHostAudio {void Cue(string id,Vector3 position,float value,double delaySeconds);}
 public interface IHostWorld {Transform Root {get;} }
}
