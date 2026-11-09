using System;
using static Cinder.Sim.SimMath;

namespace Cinder.Sim {
    // Scripted input generator. It uses the same pedals and steering as a pad;
    // it never edits chassis pose or supplies airborne forces.
    public static class TrialAssist {
        public static SimInput Drive(VehicleSim sim,double targetSpeed=2.2,bool boost=false) {
            DVec3 forward=sim.State.Rotation.Rotate(new DVec3(0,0,1));double yaw=Math.Atan2(forward.X,forward.Z),z=sim.State.Position.Z;
            Station station=TerrainModel.StationAt(sim.State.Area);double x=TerrainModel.TrailCenter(sim.State.Area,z+5);
            double desired=Math.Atan2(x-sim.State.Position.X,5),error=Math.IEEERemainder(desired-yaw,2*Math.PI);
            if(z>station.EndZ)targetSpeed=0;
            return new SimInput {Steer=Clamp(error*2,-1,1),Throttle=Clamp((targetSpeed-sim.Speed)*.6,0,.75),Brake=Clamp((sim.Speed-targetSpeed)*.5,0,1),Boost=boost};
        }
    }
}
