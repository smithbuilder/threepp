using System;
using System.Collections.Generic;
using System.Globalization;
using static Cinder.Sim.SimMath;

namespace Cinder.Sim {
    [Serializable] public sealed class ProbeReport {
        public bool Success=true;public int Checks;public string Fingerprint;
        public List<string> Lines=new List<string>();
        public List<SimReplay> Replays=new List<SimReplay>();
        public void Check(string name,bool pass,string detail="") {Checks++;Success&=pass;Lines.Add((pass?"PASS ":"FAIL ")+name+(detail.Length>0?" "+detail:""));}
    }
    public static class SimProbe {
        static string N(double x) {return x.ToString("F6",CultureInfo.InvariantCulture);}
        static double Sum(double[] a) {double sum=0;foreach(double v in a)sum+=v;return sum;}
        static double Up(VehicleSim s) {return s.State.Rotation.Rotate(DVec3.Up).Y;}
        static void Steps(VehicleSim s,int count,SimInput input) {for(int i=0;i<count;i++)s.Step(input);}
        public static ProbeReport Run() {
            var report=new ProbeReport();var fingerprints=new List<string>();
            report.Check("catalog seven vehicles",VehicleCatalog.All.Length==7);
            report.Check("terrain eight areas",TerrainModel.Stations.Length==8);
            for(int v=0;v<VehicleCatalog.All.Length;v++) {
                VehicleTune tune=VehicleCatalog.All[v];string id=tune.Id;var s=new VehicleSim(v,0,false,8675309);
                Steps(s,300,new SimInput());
                report.Check(id+" settled support",s.ContactCount==4,"contacts="+s.ContactCount);
                report.Check(id+" static weight",Math.Abs(Sum(s.State.Load)-tune.Mass*9.81)<tune.Mass*9.81*.03,"N="+N(Sum(s.State.Load)));
                DVec3 position=s.State.Position;Steps(s,120,new SimInput());
                report.Check(id+" stationary drift",(s.State.Position-position).Length<.02,"m="+N((s.State.Position-position).Length));
                SimState settled=s.State.Clone();Steps(s,180,new SimInput{Throttle=.7});
                report.Check(id+" accelerates through tyre forces",s.Speed>3,"m/s="+N(s.Speed));
                Steps(s,180,new SimInput{Brake=1});report.Check(id+" brakes",Math.Abs(s.Speed)<.15,"m/s="+N(s.Speed));
                var replay=new SimReplay(settled);s.Restore(settled);
                SimState middle=null;for(int i=0;i<360;i++){SimInput input=new SimInput{Throttle=i<240?.45:0,Brake=i>=240?.7:0,Steer=i>=60&&i<160?.45:i>=160&&i<240?-.35:0,Boost=i<90,WindX=2,WindGusts=true};replay.Inputs.Add(input);s.Step(input);if(i==179)middle=s.State.Clone();}
                string expected=s.Fingerprint();VehicleSim other=replay.Play();report.Check(id+" seeded replay",expected==other.Fingerprint(),expected);
                other.Restore(middle);for(int i=180;i<360;i++)other.Step(replay.Inputs[i]);report.Check(id+" midpoint restore",other.Fingerprint()==expected);
                SimState clone=settled.Clone();clone.Travel[0]+=1;report.Check(id+" clone isolates wheel arrays",Math.Abs(clone.Travel[0]-settled.Travel[0]-1)<1e-12);
                report.Replays.Add(replay);fingerprints.Add(expected);
                var air=new VehicleSim(v);air.Restore(settled);SimState suspended=air.State.Clone();suspended.Position.Y+=20;suspended.Velocity=new DVec3(2,0,3);suspended.AngularVelocity=DVec3.Zero;air.Restore(suspended);var powered=new VehicleSim(v);powered.Restore(suspended);
                Steps(air,30,new SimInput());Steps(powered,30,new SimInput{Throttle=1,Boost=true});
                report.Check(id+" no airborne thrust",air.ContactCount==0&&powered.ContactCount==0&&(air.State.Velocity-powered.State.Velocity).Length<1e-12&&!powered.State.BoostActive,"delta m/s="+N((air.State.Velocity-powered.State.Velocity).Length));
                report.Check(id+" ballistic fall",air.State.Velocity.Y<-4.7&&air.State.Velocity.Y>-4.95,"m/s="+N(air.State.Velocity.Y));
                // Hold the body on the steep donor lane, then release the brakes.
                var grade=new VehicleSim(v,3);SimState gs=grade.State.Clone();double gz=26,gx=0;double front=grade.Terrain.Height(gx,gz+tune.HalfWheelbase),rear=grade.Terrain.Height(gx,gz-tune.HalfWheelbase);gs.Rotation=DQuat.AxisAngle(new DVec3(1,0,0),-Math.Atan2(front-rear,2*tune.HalfWheelbase));gs.Position=new DVec3(gx,grade.Terrain.Height(gx,gz)+tune.TyreRadius-tune.StaticTravel+.07,gz);grade.Restore(gs);
                Steps(grade,300,new SimInput{Brake=1});DVec3 held=grade.State.Position;Steps(grade,120,new SimInput{Brake=1});
                report.Check(id+" grade hold",(grade.State.Position-held).Length<.08,"m="+N((grade.State.Position-held).Length));
                double before=grade.State.Position.Z;Steps(grade,120,new SimInput());report.Check(id+" grade release rolls downhill",grade.State.Position.Z<before-.15,"m="+N(before-grade.State.Position.Z));
                for(int area=0;area<8;area++) {
                    var trial=new VehicleSim(v,area);Steps(trial,120,new SimInput{Brake=1});
                    for(int i=0;i<240;i++){double target=area==6?10:area==7?0:2.2;trial.Step(new SimInput{Throttle=Clamp((target-trial.Speed)*.5,0,.65),Brake=area==7?1:Clamp((trial.Speed-target)*.5,0,1),Steer=area==4?Clamp((TerrainModel.TrailCenter(4,trial.State.Position.Z)-trial.State.Position.X)*.4,-.6,.6):0,WindX=area==7?15:0,WindGusts=area==7});}
                    report.Check(id+" area "+area+" stable",Up(trial)>.5&&trial.State.Position.Y>-5&&trial.State.Position.Y<30,"up="+N(Up(trial)));
                    if(area>=1&&area<=5) {
                        // Exercise the centre of the actual feature as well as its approach.
                        double fixtureZ=area==1?48:area==2?65:area==3?28:55;
                        PutOnSurface(trial,TerrainModel.TrailCenter(area,fixtureZ),fixtureZ);Steps(trial,180,new SimInput{Brake=1});
                        double worst=1;for(int k=0;k<180;k++){trial.Step(TrialAssist.Drive(trial,2.2));worst=Math.Min(worst,Up(trial));}
                        report.Check(id+" area "+area+" feature support",worst>.5&&trial.ContactCount>0,"min up="+N(worst));
                    }
                }
            }
            CheckJumps(report);CheckMechanisms(report);CheckWorld(report);
            report.Fingerprint=string.Join("-",fingerprints.ToArray());report.Lines.Add((report.Success?"PASS ":"FAIL ")+"Fingerprint "+report.Fingerprint);return report;
        }
        static void PutOnSurface(VehicleSim s,double x,double z) {
            VehicleTune t=s.Tune;SimState state=s.State.Clone();double[] h=new double[4];for(int i=0;i<4;i++)h[i]=s.Terrain.Height(x+(i%2!=0?1:-1)*t.TrackAt(i),z+(i<2?1:-1)*t.HalfWheelbase);
            double pitch=-Math.Atan2((h[0]+h[1]-h[2]-h[3])*.5,2*t.HalfWheelbase),roll=Math.Atan2((h[1]+h[3]-h[0]-h[2])*.5,2*t.HalfTrack);
            state.Rotation=DQuat.AxisAngle(new DVec3(1,0,0),pitch)*DQuat.AxisAngle(new DVec3(0,0,1),roll);state.Position=new DVec3(x,(h[0]+h[1]+h[2]+h[3])*.25+t.TyreRadius-t.StaticTravel+.07,z);state.Velocity=state.AngularVelocity=DVec3.Zero;s.Restore(state);
        }
        static void CheckJumps(ProbeReport r) {
            // Baja is the donor suspension/boost hero. Two takeoffs and real landings.
            var s=new VehicleSim(2,6);Steps(s,180,new SimInput{Brake=1});SimState start=s.State.Clone();start.Velocity=new DVec3(0,0,10);s.Restore(start);var replay=new SimReplay(start);int flights=0,airTicks=0;bool wasAir=false;double worstUp=1;
            for(int i=0;i<750;i++) {double target=s.State.Position.Z>182?0:10;SimInput input=TrialAssist.Drive(s,target);replay.Inputs.Add(input);s.Step(input);bool airborne=s.ContactCount==0;if(airborne){airTicks++;if(!wasAir)flights++;}wasAir=airborne;worstUp=Math.Min(worstUp,Up(s));}
            r.Check("baja two physical jumps",flights>=2&&airTicks>=5,"flights="+flights+" air seconds="+N(airTicks*VehicleSim.Dt));r.Check("baja jump landing upright",Up(s)>.8&&s.ContactCount==4&&worstUp>.3,"up="+N(Up(s))+" min="+N(worstUp));r.Replays.Add(replay);
            r.Check("baja jump course completes",s.State.Position.Z>182,"z m="+N(s.State.Position.Z));
        }
        static void CheckMechanisms(ProbeReport r) {
            var catrina=new VehicleSim(4);Steps(catrina,300,new SimInput());double y=catrina.State.Position.Y,maxY=y,maxPreload=0;int frontAir=0;for(int i=0;i<360;i++){catrina.Step(new SimInput{Mode=1,Brake=1});maxY=Math.Max(maxY,catrina.State.Position.Y);maxPreload=Math.Max(maxPreload,catrina.State.Actuator[0]);if(!catrina.State.Grounded[0]&&!catrina.State.Grounded[1])frontAir++;}
            r.Check("catrina physical hop",maxY-y>.08&&maxPreload>.4&&frontAir>0,"lift m="+N(maxY-y)+" front air ticks="+frontAir);
            for(int mode=2;mode<=3;mode++){catrina.Reset(4,0,false);Steps(catrina,240,new SimInput{Brake=1});Steps(catrina,300,new SimInput{Mode=mode,Brake=1});r.Check("catrina three-wheel stance "+mode,catrina.ContactCount==3,"contacts="+catrina.ContactCount);}
            catrina.Reset(4,0,false);SimState moving=catrina.State.Clone();moving.Velocity=new DVec3(0,0,7);catrina.Restore(moving);catrina.Step(new SimInput{Mode=1});r.Check("catrina speed interlock",catrina.State.SpeedInterlock&&Sum(catrina.State.Actuator)==0);
            var luna=new VehicleSim(5);Steps(luna,300,new SimInput());double low=luna.State.Position.Y;Steps(luna,180,new SimInput{Mode=1,Brake=1});double raised=luna.State.Position.Y;double extension=(luna.State.Actuator[0]+luna.State.Actuator[1])*.5;Steps(luna,120,new SimInput{Mode=2,Brake=1});
            r.Check("media-luna paired front pump",raised-low>.06&&extension>.25,"lift m="+N(raised-low));r.Check("media-luna hold traps fluid",Math.Abs((luna.State.Actuator[0]+luna.State.Actuator[1])*.5-extension)<1e-10);
            SimState flight=luna.State.Clone();flight.Position.Y+=20;luna.Restore(flight);double trapped=Sum(luna.State.Actuator);Steps(luna,20,new SimInput{Mode=2});trapped=Sum(luna.State.Actuator);Steps(luna,20,new SimInput{Mode=0});r.Check("media-luna airborne dump cannot retract",Math.Abs(Sum(luna.State.Actuator)-trapped)<1e-10);
            var nocturne=new VehicleSim(6);Steps(nocturne,300,new SimInput());Steps(nocturne,240,new SimInput{Mode=4,Brake=1});r.Check("nocturne independent corner",nocturne.State.Actuator[0]>.05&&Math.Abs(nocturne.State.Actuator[1])<1e-10&&Math.Abs(nocturne.State.Actuator[2])<1e-10);
            double held=Sum(nocturne.State.Actuator);Steps(nocturne,180,new SimInput{Mode=2,Brake=1});r.Check("nocturne hold keeps preload",Math.Abs(Sum(nocturne.State.Actuator)-held)<1e-10);Steps(nocturne,420,new SimInput{Mode=3,Brake=1});r.Check("nocturne park lowers four corners",Sum(nocturne.State.Actuator)<-.19&&nocturne.ContactCount==4);
            double[] h={.28,.39,.27,.41};AxlePose c=WheelKinematics.CatrinaRear(h[2],h[3]),n=WheelKinematics.NocturneRear(h[2],h[3]),b=WheelKinematics.BajaRear(h[2],h[3]),l=WheelKinematics.LunaRear(h[2],h[3]);
            r.Check("catrina rear four-link closure",c.ClosureError<.00001,"m="+N(c.ClosureError));r.Check("nocturne rear four-link closure",n.ClosureError<.00001,"m="+N(n.ClosureError));
            foreach(int v in new[]{2,4,5,6}){VehicleTune t=VehicleCatalog.All[v];DVec3 a=WheelKinematics.Hub(t,2,h,0),d=WheelKinematics.Hub(t,3,h,0);r.Check(t.Id+" rigid rear axle span",Math.Abs((a-d).Length-t.TrackAt(2)*2)<1e-10,"m="+N((a-d).Length));}
            foreach(int v in new[]{5,6}) {
                var sim=new VehicleSim(v,5);PutOnSurface(sim,50,55);Steps(sim,180,new SimInput{Brake=1});for(int k=0;k<20;k++)sim.Step(new SimInput{Steer=.7,Brake=1});
                double agreement=1;for(int i=0;i<4;i++){WheelPose wheel=WheelKinematics.Pose(sim.Tune,i,sim.State.Travel,sim.State.Steer);DVec3 axle=sim.State.Rotation.Rotate(wheel.Rotation.Rotate(new DVec3(-1,0,0))),hub=sim.State.Position+sim.State.Rotation.Rotate(wheel.Hub),normal=sim.Terrain.Normal(hub.X,hub.Z);DVec3 expected=DVec3.Cross(normal,(axle-normal*DVec3.Dot(axle,normal)).Normalized).Normalized;agreement=Math.Min(agreement,DVec3.Dot(expected,sim.TyreForward(i)));}
                r.Check(sim.Tune.Id+" traction follows mechanical tyre axes",agreement>.999,"dot="+N(agreement));
            }
        }
        static void CheckWorld(ProbeReport r) {
            var city=new VehicleSim(2,0,true);Steps(city,180,new SimInput{Brake=1});r.Check("Mercer world settles",city.ContactCount==4&&Up(city)>.99);r.Check("Mercer collision solids",city.Terrain.Solids.Length==15);
            SimState state=city.State.Clone();state.Position=new DVec3(-33,city.State.Position.Y,49);state.Velocity=new DVec3(8,0,0);city.Restore(state);double furthest=-33;for(int i=0;i<240;i++){city.Step(new SimInput());furthest=Math.Max(furthest,city.State.Position.X);}r.Check("Mercer building blocks chassis",furthest<-22.7,"max x m="+N(furthest));
            var wind=new VehicleSim(2,7);Steps(wind,180,new SimInput{Brake=1});Steps(wind,120,new SimInput{WindX=20,Brake=1});double f20=wind.State.AerodynamicForce.X;var wind2=new VehicleSim(2,7);Steps(wind2,180,new SimInput{Brake=1});Steps(wind2,120,new SimInput{WindX=10,Brake=1});double f10=wind2.State.AerodynamicForce.X;
            r.Check("aero relative wind squared",f20/f10>3.5&&f20/f10<4.5,"ratio="+N(f20/f10));
            VehicleTune[] copy=VehicleCatalog.All;copy[0]=copy[1];r.Check("catalog exposure cannot replace definitions",new VehicleSim().Tune.Id=="safari");WorldSolid[] solids=city.Terrain.Solids;solids[0]=new WorldSolid();r.Check("solid exposure cannot mutate collision world",city.Terrain.Solids[0].HalfSize.X==9);
        }
    }
}
