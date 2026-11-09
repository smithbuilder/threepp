using System;
using System.Collections.Generic;

namespace Cinder.Sim {
    [Serializable] public struct SimInput {
        public double Steer,Throttle,Brake,WindX,WindZ;
        public bool Handbrake,Reverse,Boost,Reset,WindGusts;
        // Catrina: 0 cruise, 1 hop, 2/3 three wheel, 4 raised.
        // Luna: 0 lower, 1 raise, 2 hold. Nocturne: donor NocturneAirMode 0..8.
        public int Mode;
    }
    [Serializable] public struct SimEvent {
        public string Kind;public DVec3 Position;public double Value;public long Tick;
        public SimEvent(string kind,DVec3 position,double value,long tick) {Kind=kind;Position=position;Value=value;Tick=tick;}
    }
    [Serializable] public sealed class SimState {
        public long Tick;
        public int Vehicle,Area,Mode,PreviousMode;
        public bool City,Reverse,BoostActive,SpeedInterlock,WindGusts;
        public DVec3 Position,Velocity,AngularVelocity,Wind,AerodynamicForce;
        public DQuat Rotation=DQuat.Identity;
        public double Steer,Throttle,Brake,BoostCharge=1,ActuatorPhase,Distance,MaximumSpeed;
        public uint RNG=1;
        public double[] Travel=new double[4],Load=new double[4],Spin=new double[4],Actuator=new double[4];
        public bool[] Grounded=new bool[4];
        public DVec3[] WheelLocal=new DVec3[4];
        public int[] Valve=new int[4];
        public SimState Clone() {
            var c=(SimState)MemberwiseClone();c.Travel=(double[])Travel.Clone();c.Load=(double[])Load.Clone();c.Spin=(double[])Spin.Clone();c.Actuator=(double[])Actuator.Clone();c.Grounded=(bool[])Grounded.Clone();c.WheelLocal=(DVec3[])WheelLocal.Clone();c.Valve=(int[])Valve.Clone();return c;
        }
        public void Restore(SimState from) {
            if(from==null)throw new ArgumentNullException("from");
            Tick=from.Tick;Vehicle=from.Vehicle;Area=from.Area;Mode=from.Mode;PreviousMode=from.PreviousMode;City=from.City;Reverse=from.Reverse;BoostActive=from.BoostActive;SpeedInterlock=from.SpeedInterlock;WindGusts=from.WindGusts;
            Position=from.Position;Velocity=from.Velocity;AngularVelocity=from.AngularVelocity;Wind=from.Wind;AerodynamicForce=from.AerodynamicForce;Rotation=from.Rotation;Steer=from.Steer;Throttle=from.Throttle;Brake=from.Brake;BoostCharge=from.BoostCharge;ActuatorPhase=from.ActuatorPhase;Distance=from.Distance;MaximumSpeed=from.MaximumSpeed;RNG=from.RNG;
            Array.Copy(from.Travel,Travel,4);Array.Copy(from.Load,Load,4);Array.Copy(from.Spin,Spin,4);Array.Copy(from.Actuator,Actuator,4);Array.Copy(from.Grounded,Grounded,4);Array.Copy(from.WheelLocal,WheelLocal,4);Array.Copy(from.Valve,Valve,4);
        }
    }
    [Serializable] public sealed class SimReplay {
        public SimState Initial;
        public List<SimInput> Inputs=new List<SimInput>();
        public SimReplay() {}
        public SimReplay(SimState initial) {Initial=initial.Clone();}
        public VehicleSim Play() {if(Initial==null)throw new InvalidOperationException("Replay has no initial state");var s=new VehicleSim();s.Restore(Initial);foreach(var input in Inputs)s.Step(input);return s;}
    }
}
