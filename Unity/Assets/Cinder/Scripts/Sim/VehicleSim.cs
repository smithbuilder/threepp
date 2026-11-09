using System;
using System.Collections.Generic;
using static Cinder.Sim.SimMath;

namespace Cinder.Sim {
    // Deterministic managed rigid body solver. The donor's coefficients and rules
    // are retained; this replaces Bullet rather than embedding a second runtime.
    // It is not bitwise Bullet parity or a deformable tyre / multibody simulation.
    public sealed class VehicleSim {
        public const double Dt=1.0/60;
        const double H=Dt/4;
        public SimState State { get; private set; }
        public VehicleTune Tune { get {return VehicleCatalog.Get(State.Vehicle);} }
        public TerrainModel Terrain { get; private set; }
        // Transient output, not an authoritative input. A host drains this list.
        public readonly List<SimEvent> Events=new List<SimEvent>();
        readonly DVec3[] patches=new DVec3[4],normals=new DVec3[4],levers=new DVec3[4],forward=new DVec3[4],sideways=new DVec3[4];
        readonly double[] raw=new double[4],stopImpulse=new double[4],lonImpulse=new double[4],latImpulse=new double[4];
        public double Speed {get {return DVec3.Dot(State.Velocity,State.Rotation.Rotate(new DVec3(0,0,1)));}}
        public int ContactCount {get {int n=0;for(int i=0;i<4;i++)if(State.Grounded[i])n++;return n;}}
        public double Time {get {return State.Tick*Dt;}}
        public DVec3 TyreForward(int wheel) {if(wheel<0||wheel>=4)throw new ArgumentOutOfRangeException("wheel");return forward[wheel];}
        public VehicleSim(int vehicle=0,int area=0,bool city=false,int seed=1) {Reset(vehicle,area,city,seed);}
        DVec3 Cg {get {return new DVec3(0,Tune.CgY,Tune.CgZ);}}
        DVec3 Com {get {return State.Position+State.Rotation.Rotate(Cg);}}
        public void Reset(int vehicle,int area,bool city,int seed=1) {
            if(vehicle<0||vehicle>=VehicleCatalog.Count)throw new ArgumentOutOfRangeException("vehicle");
            if(area<0||area>=TerrainModel.Stations.Length)throw new ArgumentOutOfRangeException("area");
            State=new SimState {Vehicle=vehicle,Area=area,City=city,RNG=(uint)seed==0?1:(uint)seed};Terrain=new TerrainModel(city);Events.Clear();
            Station station=TerrainModel.StationAt(area);double x=city?-33:station.X,z=city?42:station.Z;VehicleTune t=Tune;
            double[] h=new double[4];for(int i=0;i<4;i++)h[i]=Terrain.Height(x+(i%2!=0?1:-1)*t.TrackAt(i),z+(i<2?1:-1)*t.HalfWheelbase);
            double pitch=-Math.Atan2((h[0]+h[1]-h[2]-h[3])*.5,2*t.HalfWheelbase),roll=Math.Atan2((h[1]+h[3]-h[0]-h[2])*.5,2*t.HalfTrack);
            State.Rotation=(DQuat.AxisAngle(DVec3.Up,station.Yaw)*DQuat.AxisAngle(new DVec3(1,0,0),pitch)*DQuat.AxisAngle(new DVec3(0,0,1),roll)).Normalized;
            State.Position=new DVec3(x,(h[0]+h[1]+h[2]+h[3])*.25+t.TyreRadius-t.StaticTravel+.07,z);
            for(int i=0;i<4;i++){State.Travel[i]=t.StaticTravel;State.WheelLocal[i]=WheelKinematics.Hub(t,i,State.Travel,0);}
        }
        public void Restore(SimState state) {
            if(state==null||state.Vehicle<0||state.Vehicle>=VehicleCatalog.Count||state.Area<0||state.Area>=TerrainModel.Stations.Length)throw new ArgumentException("Invalid simulation state");
            State=state.Clone();Terrain=new TerrainModel(state.City);Events.Clear();
        }
        public void Step(SimInput input) {
            Validate(input.Steer);Validate(input.Throttle);Validate(input.Brake);Validate(input.WindX);Validate(input.WindZ);
            if(input.Reset){int v=State.Vehicle,a=State.Area;bool c=State.City;uint seed=State.RNG;Reset(v,a,c,(int)seed);Events.Add(new SimEvent("reset",State.Position,0,State.Tick));return;}
            State.Throttle=Clamp(input.Throttle,0,1);State.Brake=Clamp(input.Brake,0,1);State.Reverse=input.Reverse;State.Mode=input.Mode;State.Wind=new DVec3(input.WindX,0,input.WindZ);State.WindGusts=input.WindGusts;
            DVec3 previous=State.Position;
            for(int sub=0;sub<4;sub++)Substep(input,sub);
            State.Distance+=(State.Position-previous).Length;State.MaximumSpeed=Math.Max(State.MaximumSpeed,Math.Abs(Speed));State.Tick++;
            if(!Finite(State.Position.X)||!Finite(State.Position.Y)||!Finite(State.Position.Z)||State.Velocity.LengthSquared>1e8)throw new InvalidOperationException("Simulation diverged");
        }
        static void Validate(double x) {if(!Finite(x))throw new ArgumentException("Input must be finite");}
        static bool Finite(double x) {return !double.IsNaN(x)&&!double.IsInfinity(x);}
        DVec3 InvInertia(DVec3 world) {DVec3 l=State.Rotation.Inverse.Rotate(world);return State.Rotation.Rotate(new DVec3(l.X/Tune.PitchInertia,l.Y/Tune.YawInertia,l.Z/Tune.RollInertia));}
        DVec3 PointVelocity(DVec3 lever) {return State.Velocity+DVec3.Cross(State.AngularVelocity,lever);}
        double EffectiveMass(DVec3 lever,DVec3 normal) {return 1/Tune.Mass+DVec3.Dot(normal,DVec3.Cross(InvInertia(DVec3.Cross(lever,normal)),lever));}
        void Impulse(DVec3 impulse,DVec3 lever) {State.Velocity+=impulse/Tune.Mass;State.AngularVelocity+=InvInertia(DVec3.Cross(lever,impulse));}
        void Substep(SimInput input,int sub) {
            VehicleTune t=Tune;double speed=Speed,time=(State.Tick*4+sub)*H;
            StepActuators(H,time);
            double target=Clamp(input.Steer,-1,1)*.48/(1+Math.Abs(speed)*.025);State.Steer=Approach(State.Steer,target,1.1*H,1.1*H);
            int oldContacts=ContactCount;double oldVertical=State.Velocity.Y;
            State.Velocity+=new DVec3(0,-9.81*H,0);
            DVec3 air=State.Wind*(State.WindGusts?1+.32*Math.Sin(time*2.1)+.12*Math.Sin(time*5.3):1);
            DVec3 relative=State.Rotation.Inverse.Rotate(State.Velocity-air);
            DVec3 aerodynamic=new DVec3(-.6125*t.LateralCdA*relative.X*Math.Abs(relative.X),-.6125*t.VerticalCdA*relative.Y*Math.Abs(relative.Y),-.6125*t.FrontalCdA*relative.Z*Math.Abs(relative.Z));
            State.AerodynamicForce=State.Rotation.Rotate(aerodynamic);Impulse(State.AerodynamicForce*H,State.Rotation.Rotate(new DVec3(0,t.PressureY,t.PressureZ)));
            ComputeContacts();
            // Linear spring and compression/rebound damper, limited to unilateral support.
            for(int i=0;i<4;i++) {
                State.Load[i]=0;stopImpulse[i]=lonImpulse[i]=latImpulse[i]=0;
                if(!State.Grounded[i])continue;
                double rate=t.RateAt(i),droop=t.DroopAt(i),rest=droop-State.Actuator[i];
                if(t.Id=="nocturne") {double share=i<2?(t.HalfWheelbase+t.CgZ)/(2*t.HalfWheelbase):(t.HalfWheelbase-t.CgZ)/(2*t.HalfWheelbase);rest=t.StaticTravel-t.Mass*9.81*share*.5/rate-State.Actuator[i];}
                double normalUp=Math.Max(.1,DVec3.Dot(normals[i],State.Rotation.Rotate(DVec3.Up)));
                double relativeSpeed=DVec3.Dot(PointVelocity(levers[i]),normals[i])/normalUp;
                double damping=relativeSpeed<0?(i>=2&&t.RearCompression>0?t.RearCompression:t.Compression):(i>=2&&t.RearRebound>0?t.RearRebound:t.Rebound);
                double force=Clamp(rate*(raw[i]-rest)/normalUp-damping*relativeSpeed,0,t.Mass*9.81*2);
                State.Load[i]=force;Impulse(normals[i]*(force*H),levers[i]);
            }
            // Bump-stop constraints accumulate one unilateral impulse each.
            for(int pass=0;pass<16;pass++)for(int i=0;i<4;i++) {
                if(!State.Grounded[i])continue;double penetration=raw[i]-t.BumpAt(i);if(penetration<-.002)continue;
                double targetVelocity=Math.Max(0,penetration-.001)*.15/H;
                double next=Math.Max(0,stopImpulse[i]+(targetVelocity-DVec3.Dot(PointVelocity(levers[i]),normals[i]))/EffectiveMass(levers[i],normals[i]));
                Impulse(normals[i]*(next-stopImpulse[i]),levers[i]);stopImpulse[i]=next;
            }
            double factor=Boost(input.Boost,input.Handbrake?0:ContactCount,H);
            double drive=t.DriveForce*State.Throttle*factor*(State.Reverse?-1:1)/(1+Sqr(Math.Abs(speed)/14));
            for(int i=0;i<4;i++) {
                State.Load[i]+=stopImpulse[i]/H;
                DQuat wheel=WheelKinematics.Pose(t,i,State.Travel,State.Steer).Rotation;
                DVec3 axle=State.Rotation.Rotate(wheel.Rotate(new DVec3(-1,0,0)));sideways[i]=(axle-normals[i]*DVec3.Dot(axle,normals[i])).Normalized;forward[i]=DVec3.Cross(normals[i],sideways[i]).Normalized;
            }
            // Twelve sequential-impulse passes, one Coulomb circle per tyre.
            for(int pass=0;pass<12;pass++)for(int i=0;i<4;i++) {
                if(!State.Grounded[i]||State.Load[i]<=0)continue;
                double limit=State.Load[i]*H*t.Grip;
                double engine=drive*(t.RearWheelDrive?(i<2?0:.5):.25)*H;
                double rolling=Math.Abs(speed)>.08?t.Mass*9.81*.014*.25:0;
                double brake=(State.Brake*t.Mass*9.81*.45+(input.Handbrake&&i>=2?t.Mass*9.81*.5:0)+rolling)*H;
                DVec3 velocity=PointVelocity(levers[i]);
                double lon=Clamp(lonImpulse[i]-DVec3.Dot(velocity,forward[i])/EffectiveMass(levers[i],forward[i]),engine-brake,engine+brake);
                double lat=latImpulse[i]-DVec3.Dot(velocity,sideways[i])/EffectiveMass(levers[i],sideways[i]);
                double length=Hypot(lon,lat);if(length>limit){lon*=limit/length;lat*=limit/length;}
                Impulse(forward[i]*(lon-lonImpulse[i])+sideways[i]*(lat-latImpulse[i]),levers[i]);lonImpulse[i]=lon;latImpulse[i]=lat;
            }
            SolveHull();
            // Damping matches the donor's per-second exponential convention.
            State.Velocity*=Math.Pow(1-.008,H);State.AngularVelocity*=Math.Pow(1-.015,H);
            DVec3 com=Com+State.Velocity*H;double angularSpeed=State.AngularVelocity.Length;
            if(angularSpeed>1e-12)State.Rotation=(DQuat.AxisAngle(State.AngularVelocity/angularSpeed,angularSpeed*H)*State.Rotation).Normalized;
            State.Position=com-State.Rotation.Rotate(Cg);
            for(int i=0;i<4;i++)State.Spin[i]+=Speed*H/t.TyreRadius;
            if(oldContacts==0&&ContactCount>0&&oldVertical<-.8)Emit("landing",Math.Abs(oldVertical));
            if(State.Tick%6==0&&sub==0&&State.Throttle>.05)Emit("engine",State.Throttle);
        }
        double Boost(bool requested,int contacts,double dt) {
            State.BoostActive=requested&&contacts>=2&&State.Throttle>.15&&State.Brake<.1&&!State.Reverse&&State.BoostCharge>0;
            double fraction=State.BoostActive?Math.Min(State.BoostCharge,dt/2.5)/(dt/2.5):0;
            if(State.BoostActive)State.BoostCharge=Math.Max(0,State.BoostCharge-dt/2.5);else if(!requested)State.BoostCharge=Math.Min(1,State.BoostCharge+dt/6);return 1+fraction;
        }
        void ComputeContacts() {
            VehicleTune t=Tune;DVec3 up=State.Rotation.Rotate(DVec3.Up),com=Com;
            for(int i=0;i<4;i++) {
                double minimum=t.DroopAt(i);
                if(t.Id=="catrina")minimum=Math.Max(i<2?-.12:-.28,minimum-State.Actuator[i]);
                if(t.Id=="media-luna"&&i<2)minimum=Math.Max(-.035,minimum-State.Actuator[i]);
                double travel=State.Travel[i],required=double.NegativeInfinity;DVec3 patch=new DVec3();
                for(int iteration=0;iteration<3;iteration++) {
                    State.Travel[i]=travel;WheelPose pose=WheelKinematics.Pose(t,i,State.Travel,State.Steer);DVec3 basePoint=State.Position+State.Rotation.Rotate(pose.Hub);
                    required=double.NegativeInfinity;
                    for(int row=-1;row<=1;row++)for(int arc=-3;arc<=3;arc++) {
                        double a=arc*.24;DVec3 offset=State.Rotation.Rotate(pose.Rotation.Rotate(new DVec3(row*t.TyreHalfWidth*.70,-t.TyreRadius*Math.Cos(a),t.TyreRadius*Math.Sin(a))));
                        DVec3 sample=basePoint+offset;
                        double h=Terrain.Height(sample.X,sample.Z);
                        double request=travel+(h-sample.Y)/Math.Max(.1,up.Y);
                        if(request>required){required=request;patch=new DVec3(sample.X,h,sample.Z);}
                    }
                    double next=Clamp(required,minimum,t.BumpAt(i));if(Math.Abs(next-travel)<.0003){travel=next;break;}travel=next;
                }
                raw[i]=required;State.Travel[i]=travel;State.WheelLocal[i]=WheelKinematics.Hub(t,i,State.Travel,State.Steer);
                State.Grounded[i]=up.Y>.1&&required>=minimum-.0001;
                patches[i]=patch;normals[i]=Terrain.Normal(patch.X,patch.Z);levers[i]=patch-com;
            }
        }
        void SolveHull() {
            VehicleTune t=Tune;
            // Six-point approach/departure outline on both sides, same donor dimensions.
            double end=t.Length*.5,flat=t.HalfWheelbase*.82;
            double[] zs={-end+t.HullOffsetZ,-flat,flat,end+t.HullOffsetZ,end+t.HullOffsetZ,-end+t.HullOffsetZ};
            double[] ys={t.HullBottom+t.TailRise,t.HullBottom,t.HullBottom,t.HullBottom+t.NoseRise,t.HullBottom+t.Height,t.HullBottom+t.Height};
            DVec3 com=Com;
            for(int pass=0;pass<4;pass++)for(int s=-1;s<=1;s+=2)for(int j=0;j<6;j++) {
                DVec3 p=State.Position+State.Rotation.Rotate(new DVec3(s*t.Width*.5,ys[j],zs[j]));
                double depth=Terrain.Height(p.X,p.Z)+.025-p.Y;if(depth<=0)continue;
                DVec3 n=Terrain.Normal(p.X,p.Z),r=p-com;double vn=DVec3.Dot(PointVelocity(r),n),target=Math.Max(0,depth-.001)*.15/H;
                double impulse=Math.Max(0,(target-vn)/EffectiveMass(r,n));Impulse(n*impulse,r);
                DVec3 tangent=PointVelocity(r)-n*DVec3.Dot(PointVelocity(r),n);double len=tangent.Length;
                if(len>1e-9){DVec3 dir=tangent/len;Impulse(-dir*Math.Min(impulse*t.HullFriction,len/EffectiveMass(r,dir)),r);}
            }
            foreach(WorldSolid solid in Terrain.CollisionSolids)SolveSolid(solid);
            // Finite world boundary, represented in the view by perimeter markers.
            double radius=t.Width*.5;
            if(com.X<-66+radius)Wall(new DVec3(1,0,0),(-66+radius)-com.X);
            if(com.X>66-radius)Wall(new DVec3(-1,0,0),com.X-(66-radius));
            if(com.Z<-24+radius)Wall(new DVec3(0,0,1),(-24+radius)-com.Z);
            if(com.Z>196-radius)Wall(new DVec3(0,0,-1),com.Z-(196-radius));
        }
        void Wall(DVec3 normal,double depth) {double v=DVec3.Dot(State.Velocity,normal);Impulse(normal*(Math.Max(0,depth*.15/H-v)*Tune.Mass),DVec3.Zero);}
        void SolveSolid(WorldSolid solid) {
            VehicleTune t=Tune;
            DVec3 center=State.Position+State.Rotation.Rotate(new DVec3(0,t.HullBottom+t.Height*.5,t.HullOffsetZ));
            DVec3 half=new DVec3(t.Width*.5,t.Height*.5,t.Length*.5),delta=center-solid.Center;
            DVec3[] a={State.Rotation.Rotate(new DVec3(1,0,0)),State.Rotation.Rotate(DVec3.Up),State.Rotation.Rotate(new DVec3(0,0,1))};
            DVec3[] b={new DVec3(1,0,0),DVec3.Up,new DVec3(0,0,1)};
            double best=double.MaxValue;DVec3 normal=new DVec3();
            for(int k=0;k<15;k++) {
                DVec3 n=k<3?a[k]:k<6?b[k-3]:DVec3.Cross(a[(k-6)/3],b[(k-6)%3]);double len=n.Length;if(len<1e-8)continue;n/=len;
                double ra=half.X*Math.Abs(DVec3.Dot(n,a[0]))+half.Y*Math.Abs(DVec3.Dot(n,a[1]))+half.Z*Math.Abs(DVec3.Dot(n,a[2]));
                double rb=solid.HalfSize.X*Math.Abs(n.X)+solid.HalfSize.Y*Math.Abs(n.Y)+solid.HalfSize.Z*Math.Abs(n.Z);
                double d=DVec3.Dot(delta,n),overlap=ra+rb-Math.Abs(d);if(overlap<=0)return;if(overlap<best){best=overlap;normal=n*(d<0?-1:1);}
            }
            DVec3 p=center-normal*(Math.Abs(DVec3.Dot(normal,a[0]))*half.X+Math.Abs(DVec3.Dot(normal,a[1]))*half.Y+Math.Abs(DVec3.Dot(normal,a[2]))*half.Z),r=p-Com;
            double closing=DVec3.Dot(PointVelocity(r),normal),impulse=Math.Max(0,(Math.Min(5,best*.15/H)-closing)/EffectiveMass(r,normal));Impulse(normal*impulse,r);
            if(closing<-1&&State.Tick%8==0)Emit("impact",-closing);
        }
        void StepActuators(double dt,double time) {
            VehicleTune t=Tune;State.SpeedInterlock=false;
            if(t.Id=="catrina") {
                if(State.Mode!=State.PreviousMode){State.ActuatorPhase=0;State.PreviousMode=State.Mode;}
                State.SpeedInterlock=Math.Abs(Speed)>6;double raise=.30,lower=.45;double[] target=new double[4];
                if(!State.SpeedInterlock)switch(State.Mode){case 1:State.ActuatorPhase=(State.ActuatorPhase+dt)%1.85;if(State.ActuatorPhase>.32&&State.ActuatorPhase<.66)target[0]=target[1]=.50;raise=4.6;lower=2.6;break;case 2:target[2]=.58;break;case 3:target[3]=.58;break;case 4:for(int i=0;i<4;i++)target[i]=.16;break;}
                for(int i=0;i<4;i++){double before=State.Actuator[i];State.Actuator[i]=Clamp(Approach(before,target[i],lower*dt,raise*dt),0,.58);State.Valve[i]=Math.Sign(State.Actuator[i]-before);}
            } else if(t.Id=="media-luna") {
                // State stores wheel-equivalent extension; cylinder stroke is half this.
                double mean=(State.Actuator[0]+State.Actuator[1])*.25;
                if(State.Mode==1)mean=Math.Min(.152,mean+.095*dt);
                if(State.Mode==0)mean=Math.Max(0,mean-.115*Clamp((State.Load[0]+State.Load[1])/5000,0,1)*dt);
                double limit=Math.Min(mean,.19-mean),target=Clamp((State.Travel[1]-State.Travel[0])*.25,-limit,limit),previous=(State.Actuator[0]-State.Actuator[1])*.25;
                double split=Clamp(Approach(previous,target,.045*dt,.045*dt),-limit,limit);State.Actuator[0]=(mean+split)*2;State.Actuator[1]=(mean-split)*2;
            } else if(t.Id=="nocturne") {
                int mode=State.Mode;if(mode==8){double tt=time%24;mode=tt<2?0:tt<6?1:tt<8?2:tt<15?3:tt<18?0:tt<21?4:0;}
                for(int i=0;i<4;i++){if(mode==2){State.Valve[i]=0;continue;}double target=mode==1?.055:mode==3?-.050:mode>=4&&mode<=7&&i==mode-4?.055:0;State.Valve[i]=Math.Abs(target-State.Actuator[i])<.0001?0:Math.Sign(target-State.Actuator[i]);State.Actuator[i]=Approach(State.Actuator[i],target,.018*dt,.018*dt);}
            }
            bool pump=false;for(int i=0;i<4;i++)pump|=State.Valve[i]>0;if(pump&&State.Tick%12==0)Emit("pump",.3);
        }
        void Emit(string kind,double value) {
            // Four physics substeps may generate one audible cue at this tick.
            for(int i=Events.Count-1;i>=0&&Events[i].Tick==State.Tick;i--)if(Events[i].Kind==kind){if(Events[i].Value<value)Events[i]=new SimEvent(kind,State.Position,value,State.Tick);return;}
            Events.Add(new SimEvent(kind,State.Position,value,State.Tick));
        }
        public uint NextRandom() {uint x=State.RNG;x^=x<<13;x^=x>>17;x^=x<<5;State.RNG=x;return x;}
        public string Fingerprint() {
            // Every authoritative scalar, including actuator phase and seed, is hashed.
            // Events are a drainable output queue, not state that changes future steps.
            ulong hash=14695981039346656037UL;Action<long> add=v=>{unchecked{ulong bits=(ulong)v;for(int i=0;i<8;i++){hash^=(byte)(bits>>(i*8));hash*=1099511628211UL;}}};Action<double> d=v=>add(BitConverter.DoubleToInt64Bits(v));Action<DVec3> vec=v=>{d(v.X);d(v.Y);d(v.Z);};
            add(State.Tick);add(State.Vehicle);add(State.Area);add(State.Mode);add(State.PreviousMode);add(State.City?1:0);add(State.Reverse?1:0);add(State.BoostActive?1:0);add(State.SpeedInterlock?1:0);add(State.WindGusts?1:0);add(State.RNG);
            vec(State.Position);vec(State.Velocity);vec(State.AngularVelocity);vec(State.Wind);vec(State.AerodynamicForce);d(State.Rotation.X);d(State.Rotation.Y);d(State.Rotation.Z);d(State.Rotation.W);d(State.Steer);d(State.Throttle);d(State.Brake);d(State.BoostCharge);d(State.ActuatorPhase);d(State.Distance);d(State.MaximumSpeed);
            for(int i=0;i<4;i++){d(State.Travel[i]);d(State.Load[i]);d(State.Spin[i]);d(State.Actuator[i]);add(State.Grounded[i]?1:0);vec(State.WheelLocal[i]);add(State.Valve[i]);}return hash.ToString("x16");
        }
    }
}
