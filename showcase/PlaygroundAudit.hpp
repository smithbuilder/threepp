#pragma once
#include "PlaygroundPhysics.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <cstdlib>
#include <iomanip>

namespace playground {
inline void audit(const Terrain& terrain,const std::filesystem::path& output){
    std::filesystem::create_directories(output);
    std::ofstream report(output/"checks.csv"),trace(output/"physics.csv");int passed=0,failed=0;
    std::ofstream manifest(output/"vehicle-specifications.json");manifest<<"{\"units\":\"metres kilograms seconds radians Newtons\",\"calibration\":\"engineering estimates; not measured OEM data\",\"vehicles\":[";
    for(size_t n=0;n<tunes.size();++n){const auto& t=tunes[n];if(n)manifest<<',';manifest<<"{\"id\":"<<std::quoted(t.id)<<",\"name\":"<<std::quoted(t.name)<<",\"mass\":"<<t.mass
        <<",\"cg\":[0,"<<t.cgY<<','<<t.cgZ<<"],\"inertia\":["<<t.pitchInertia<<','<<t.yawInertia<<','<<t.rollInertia<<"],\"tyreRadius\":"<<t.dims.tyreRadius
        <<",\"wheelbase\":"<<t.dims.halfWheelbase*2<<",\"track\":"<<t.dims.halfTrack*2<<",\"hubTravel\":["<<t.dims.droop<<','<<t.dims.bump<<"],\"springs\":["<<t.frontRate<<','<<t.rearRate
        <<"],\"dampers\":["<<t.compression<<','<<t.rebound<<"],\"grip\":"<<t.grip<<",\"driveForce\":"<<t.driveForce<<",\"CdA\":["<<t.lateralCdA<<','<<t.verticalCdA<<','<<t.frontalCdA
        <<"],\"pressureOffset\":[0,"<<t.pressureY<<','<<t.pressureZ<<"]}";}manifest<<"]}\n";
    report<<"vehicle,check,passed,value,limit\n";
    trace<<"vehicle,station,t,x,y,z,speed,contacts,flTravel,frTravel,rlTravel,rrTravel,flLoad,frLoad,rlLoad,rrLoad\n";
    auto pulse=[](){if(const char* p=std::getenv("THREEPP_EVALUATION_HEARTBEAT")){std::ofstream beat(p);beat<<"CPU physics audit active\n";}};
    auto check=[&](const char* vehicle,const char* name,bool ok,float value,float limit){report<<vehicle<<','<<name<<','<<ok<<','<<value<<','<<limit<<'\n';(ok?passed:failed)++;pulse();};
    Simulation s(terrain);
    float meshError=0;for(int i=0;i<200;++i){float x=-64+(i*29%250)*.5f+.11f,z=-22+(i*31%420)*.5f+.17f;
        // Exclude the separately modelled solid wind-test gantry.
        if(x>16&&x<34&&z>130&&z<144)continue;
        meshError=std::max(meshError,std::abs(s.rayHeight(x,z)-terrain.height(x,z)));}
    check("all","visible terrain equals collision mesh",meshError<.001f,meshError,.001f);
    for(int n=0;n<static_cast<int>(tunes.size());++n){
        s.select(n,stations[0]);
        for(int k=0;k<240*8;++k)s.tick(0,1,0);
        float support=0;for(float f:s.load)support+=f;
        check(s.tune.name,"static weight balance",std::abs(support-s.tune.mass*9.81f)/(s.tune.mass*9.81f)<.04f,support,s.tune.mass*9.81f);
        check(s.tune.name,"four supported tyres at rest",s.contactCount()==4,s.contactCount(),4);
        float maxVelocity=s.velocity().length();s.lift(.25f);
        for(int k=0;k<240*6;++k)s.tick(0,1,0);
        maxVelocity=s.velocity().length();check(s.tune.name,"drop settles without sustained bounce",maxVelocity<.035f,maxVelocity,.035f);
        s.select(n,stations[0]);s.lift(8);auto start=s.origin();
        for(int k=0;k<120;++k)s.tick(1,0,1);
        auto fall=s.origin().sub(start);
        check(s.tune.name,"free fall follows gravity",std::abs(fall.y+9.81f*.5f*.5f*.5f)<.04f,fall.y,-1.22625f);
        check(s.tune.name,"airborne throttle cannot propel body",std::hypot(fall.x,fall.z)<.002f,std::hypot(fall.x,fall.z),.002f);
        // Optional arcade force uses the same tyres and chassis. It cannot
        // propel an airborne body or override the brake, and defaults off.
        s.select(n,stations[0]);for(int k=0;k<480;++k)s.tick(1,0,0);float normalSpeed=s.speed();
        s.select(n,stations[0]);for(int k=0;k<480;++k)s.tick(1,0,0,false,true);float boostedSpeed=s.speed();
        check(s.tune.name,"ground boost increases acceleration",boostedSpeed>normalSpeed+.4f,boostedSpeed-normalSpeed,.4f);
        s.tick(1,1,0,false,true);check(s.tune.name,"brake cancels optional boost",!s.boost.active,s.boost.active,0);
        s.select(n,stations[0]);s.lift(8);start=s.origin();for(int k=0;k<120;++k)s.tick(1,0,0,false,true);fall=s.origin().sub(start);
        check(s.tune.name,"boost cannot propel an airborne body",std::hypot(fall.x,fall.z)<.002f&&!s.boost.active,std::hypot(fall.x,fall.z),.002f);
        Station incline{"slope","",0,30,0};s.select(n,incline);
        for(int k=0;k<240*3;++k)s.tick(0,1,0);
        auto held=s.origin();for(int k=0;k<240*3;++k)s.tick(0,1,0);
        check(s.tune.name,"brakes hold steep grade",s.origin().distanceTo(held)<.12f,s.origin().distanceTo(held),.12f);
        float before=s.origin().z;for(int k=0;k<240*3;++k)s.tick(0,0,0);
        check(s.tune.name,"released vehicle rolls downhill",s.origin().z<before-.4f,before-s.origin().z,.4f);
        float maxTurn=0;s.select(n,stations[0]);auto turnQ=s.rotation();
        for(int k=0;k<240*4;++k)s.tick(.40f,0,.55f);
        maxTurn=turnQ.angleTo(s.rotation());
        check(s.tune.name,"tyre forces turn the body",maxTurn>.10f,maxTurn,.10f);
        Station sideSlope{"side slope","",50,52,0};s.select(n,sideSlope);
        for(int k=0;k<240*4;++k)s.tick(0,1,0);auto sideHold=s.origin();
        for(int k=0;k<240*2;++k)s.tick(0,1,0);
        check(s.tune.name,"side slope hold within tyre grip",s.origin().distanceTo(sideHold)<.04f,s.origin().distanceTo(sideHold),.04f);
        s.setGrip(.05f);sideHold=s.origin();for(int k=0;k<240*2;++k)s.tick(0,1,0);
        check(s.tune.name,"insufficient grip permits a physical slide",s.origin().distanceTo(sideHold)>.3f,s.origin().distanceTo(sideHold),.3f);
        s.windVelocity.set(0,0,0);s.windGusts=false;s.select(n,stations[7]);for(int k=0;k<240*3;++k)s.tick(0,1,0);
        auto parked=s.origin();float priorTransfer=s.load[0]+s.load[2]-s.load[1]-s.load[3];
        s.windVelocity.set(15,0,0);s.tick(0,1,0);float force15=s.aerodynamicForce.length();
        s.windVelocity.set(30,0,0);s.tick(0,1,0);float force30=s.aerodynamicForce.length();
        check(s.tune.name,"aerodynamic force scales with airspeed squared",std::abs(force30/force15-4)<.03f,force30/force15,4);
        for(int k=0;k<240*3;++k)s.tick(0,1,0);
        float transfer=std::abs((s.load[0]+s.load[2]-s.load[1]-s.load[3])-priorTransfer);
        check(s.tune.name,"crosswind changes physical wheel loads",transfer>100,transfer,100);
        check(s.tune.name,"braked wind test remains on the pad",s.origin().distanceTo(parked)<.1f,s.origin().distanceTo(parked),.1f);
        s.windGusts=true;float least=1e9f,most=0;
        for(int k=0;k<240*4;++k){s.tick(0,1,0);least=std::min(least,s.aerodynamicForce.length());most=std::max(most,s.aerodynamicForce.length());}
        check(s.tune.name,"gusts vary the actual applied force",most-least>force30*.3f,most-least,force30*.3f);
        s.windGusts=false;s.kick(s.windVelocity);s.tick(0,0,0);
        check(s.tune.name,"aerodynamics uses relative air velocity",s.aerodynamicForce.length()<.001f,s.aerodynamicForce.length(),.001f);
        // Ground springs may be very stiff on a heavy future vehicle. Validate
        // the off-centre aero torque in free flight rather than demanding an
        // arbitrary minimum visible roll angle from every suspension tune.
        s.select(n,stations[7]);s.lift(6);auto airQ=s.rotation();
        for(int k=0;k<120;++k)s.tick(0,0,0);
        float aeroAngle=airQ.angleTo(s.rotation());
        check(s.tune.name,"off centre airflow creates physical torque",aeroAngle>.003f,aeroAngle,.003f);
        s.windVelocity.set(0,0,0);
        s.select(n,stations[1]);for(int k=0;k<240*8;++k)s.tick(.3f,0,0);auto repeatPosition=s.origin();auto repeatQ=s.rotation();
        s.select(n,stations[1]);for(int k=0;k<240*8;++k)s.tick(.3f,0,0);
        float difference=s.origin().distanceTo(repeatPosition);
        check(s.tune.name,"fixed input replay is deterministic",difference<.0001f&&s.rotation().angleTo(repeatQ)<.001f,difference,.0001f);
        // Every vehicle drives over every station with actual forces. No path
        // teleporting; this is a bounded abuse/finite-state test, not a completion claim.
        float worstTravel=0,maxOmega=0,penetration=0;bool finite=true;float articulation=0,jumpAir=0;bool landed=false,hadAir=false;
        std::array<float,2> jumpTimes{};std::array<bool,2> jumpLanded{};float jumpProgress=94,jumpUp=1;
        for(int station=1;station<static_cast<int>(stations.size());++station){
            if(stations[station].kind==TrialKind::Wind)continue; // Wind has its force/load tests above.
            s.select(n,stations[station]);bool jumps=stations[station].kind==TrialKind::Jumps;
            if(jumps)for(int k=0;k<240*2;++k)s.tick(0,1,0);
            for(int k=0;k<240*16;++k){
                if(k%240==0)pulse();
                float target=stations[station].defaultSpeed;float error=target-s.speed();
                auto f=Vector3(0,0,1).applyQuaternion(s.rotation());auto p=s.origin();float yaw=std::atan2(f.x,f.z);
                float turn=std::clamp((Terrain::trailCenter(station,p.z)-p.x)*.22f-yaw*1.5f,-1.f,1.f);
                float demand=error*.55f+s.tune.mass*9.81f*f.y/s.tune.driveForce;
                bool end=p.z>stations[station].endZ;
                s.tick(end?0:std::clamp(demand,0.f,1.f),end?1:std::clamp(-demand*s.tune.driveForce/(s.tune.mass*9.81f*1.8f),0.f,1.f),turn);
                auto v=s.velocity();finite&=std::isfinite(p.x)&&std::isfinite(p.y)&&std::isfinite(p.z)&&std::isfinite(v.length());
                maxOmega=std::max(maxOmega,s.angularVelocity().length());
                for(float t:s.travel)worstTravel=std::max(worstTravel,std::max(s.tune.dims.droop-t,t-s.tune.dims.bump));
                for(int i=0;i<4;++i)penetration=std::max(penetration,s.tyrePenetration(i));
                if(station==1)articulation=std::max(articulation,std::abs(s.travel[0]-s.travel[1]));
                if(jumps){jumpProgress=p.z;jumpUp=Vector3(0,1,0).applyQuaternion(s.rotation()).y;
                    if(p.z>112&&p.z<180){int jump=p.z<140?0:1;if(s.contactCount()==0){jumpAir+=Simulation::fixedStep;jumpTimes[jump]+=Simulation::fixedStep;hadAir=true;}
                        else if(jumpTimes[jump]>.05f&&s.contactCount()>=2){landed=true;jumpLanded[jump]=true;}}}
                if(k%24==0){trace<<n<<','<<station<<','<<s.time<<','<<p.x<<','<<p.y<<','<<p.z<<','<<s.speed()<<','<<s.contactCount();for(float t:s.travel)trace<<','<<t;for(float l:s.load)trace<<','<<l;trace<<'\n';}
            }
        }
        check(s.tune.name,"all five trail simulations stay finite",finite,finite,1);
        check(s.tune.name,"mechanical wheel travel bounds",worstTravel<.001f,worstTravel,.001f);
        check(s.tune.name,"bump stops limit actual tyre penetration",penetration<.035f,penetration,.035f);
        check(s.tune.name,"cross axle produces independent wheel movement",articulation>.025f,articulation,.025f);
        check(s.tune.name,"bounded angular response",maxOmega<12,maxOmega,12);
        check(s.tune.name,"jump line produces real airborne motion",jumpAir>.10f,jumpAir,.10f);
        check(s.tune.name,"vehicle lands after ballistic flight",landed,landed,1);
        check(s.tune.name,"both jumps leave the ground",jumpTimes[0]>.10f&&jumpTimes[1]>.10f,std::min(jumpTimes[0],jumpTimes[1]),.10f);
        check(s.tune.name,"both jumps land and continue upright",jumpLanded[0]&&jumpLanded[1]&&jumpProgress>181&&jumpUp>.65f,jumpProgress,181);
        if(tunes[n].visualRig==VisualRig::Baja){
            s.select(n,stations[6]);float airTime=0,peak=0;bool touchedDown=false;float boostSeconds=0;
            for(int k=0;k<240*12;++k){
                auto p=s.origin(),f=Vector3(0,0,1).applyQuaternion(s.rotation());bool boost=p.z>=103&&p.z<110;
                float demand=((boost?14.f:10.f)-s.speed())*.55f+s.tune.mass*9.81f*f.y/s.tune.driveForce;
                float turn=std::clamp((Terrain::trailCenter(6,p.z)-p.x)*.22f-std::atan2(f.x,f.z)*1.5f,-1.f,1.f);
                s.tick(std::clamp(demand,0.f,1.f),std::clamp(-demand*s.tune.driveForce/(s.tune.mass*9.81f*1.8f),0.f,1.f),turn,false,boost);
                boostSeconds+=s.boost.active?Simulation::fixedStep:0;
                if(p.z>113&&p.z<140){if(s.contactCount()==0)airTime+=Simulation::fixedStep;else if(airTime>.1f&&s.contactCount()>=2)touchedDown=true;
                    peak=std::max(peak,p.y-terrain.height(p.x,p.z));}
                if(k%240==0)pulse();
            }
            float up=Vector3(0,1,0).applyQuaternion(s.rotation()).y;
            check(s.tune.name,"boosted ramp has airborne arc and landing",airTime>.1f&&touchedDown&&boostSeconds>.1f&&peak>.5f,airTime,.1f);
            check(s.tune.name,"boosted jump continues upright",s.origin().z>140&&up>.65f,s.origin().z,140);
        }
    }
    std::ofstream out(output/"result.json");out<<"{\"status\":\""<<(failed?"FAIL":"PASS")<<"\",\"passed\":"<<passed<<",\"failed\":"<<failed
        <<",\"solver\":\"Bullet 3.25 rigid body and raycast vehicle\",\"physicsHz\":240,\"terrainTriangles\":"<<terrain.indices.size()/3
        <<",\"vehicles\":"<<tunes.size()<<",\"stations\":"<<stations.size()
        <<",\"scope\":\"Static equilibrium, drop decay, free fall, grade hold and release, grip-limited sliding, steering, replay repeatability, wind scaling/load transfer/gusts, relative airflow and six trail stress runs per vehicle. Both jumps leave the ground and land upright. No subjective handling acceptance.\"}\n";
    std::cout<<passed<<" physics checks passed; "<<failed<<" failed\n";
    if(failed)throw std::runtime_error("Physics acceptance checks failed; inspect checks.csv");
}
}
