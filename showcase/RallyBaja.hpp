#pragma once
#include "BajaRide.hpp"
#include "RallyPowertrain.hpp"
#include "threepp/loaders/GLTFLoader.hpp"
#include <filesystem>
#include <fstream>

namespace rally {
// Force-based vertical ride, rigid wishbones/steel links and telescopic dampers.
// The five-link bushes permit small elastic articulation; this is a reduced
// vehicle model, not manufacturing geometry or a complete tyre/steering solver.
struct BajaRace {
    std::shared_ptr<Group> car=Group::create();Object3D *body{},*axle{};
    std::array<Object3D*,4> steer{},roll{},rotor{};
    std::array<Object3D*,2> upright{},rackSlide{};
    std::array<WheelContact,4> contacts{};BajaRideState ride;Powertrain powertrain;
    struct Link{Object3D* node;Vector3 a,b;};
    struct Telescope{Object3D *node,*shaft,*coil,*upperSeat,*lowerSeat;Vector3 a,b;int kind;};
    std::array<Link,2> lowerArm{},upperArm{},tieRod{};
    std::array<Link,4> rearLinks{};Link panhard;
    std::array<Telescope,2> frontShock{},rearShock{},halfshaft{},rearSpring{};Telescope prop;
    float axleRoll=0,maxArmLengthError=0,maxRearBushingDeflection=0,minDamperEngagement=1e9f;
    Object3D* required(const std::string& name){auto* n=car->getObjectByName(name);if(!n)throw std::runtime_error("Missing Baja v3 interface: "+name);return n;}
    Link link(const std::string& name,Vector3 b){auto* n=required(name);return {n,n->position,b};}
    Telescope telescope(const std::string& name,Vector3 b,int kind){
        auto* n=required(name);auto* shaft=required(kind==3?"driveline.slip":name+(kind>=2?".slip":".shaft"));
        return {n,shaft,kind==0?required(name+".spring"):nullptr,kind==0?required(name+".upper_seat"):nullptr,kind==0?required(name+".lower_seat"):nullptr,n->position,b,kind};
    }
    explicit BajaRace(const std::filesystem::path& path){
        auto asset=GLTFLoader{}.load(path);if(!asset||!asset->scene)throw std::runtime_error("Missing Baja truck GLB");
        car->add(asset->scene);body=required("body");axle=required("rear_axle");
        for(int i=0;i<4;++i){const auto label=std::array<std::string,4>{"FL","FR","RL","RR"}[i];steer[i]=required("wheel."+label+".steer");roll[i]=required("wheel."+label+".roll");rotor[i]=required("brake."+label+".rotor");}
        for(int i=0;i<2;++i){const int s=i?1:-1;const std::string side=i?"R":"L",front="front."+side,rear="rear."+side;
            lowerArm[i]=link(front+".lower_arm",{s*.97f,.31f,1.59f});upperArm[i]=link(front+".upper_arm",{s*.97f,.46f,1.59f});upright[i]=required(front+".upright");
            tieRod[i]=link(front+".tie_rod",{s*.988f,.34f,1.48f});rackSlide[i]=required(front+".rack_slide");
            halfshaft[i]=telescope(front+".halfshaft",{s*.90f,.40f,1.59f},2);
            frontShock[i]=telescope(front+".coilover",{s*.9149f,.3024f,1.59f},0);
            rearShock[i]=telescope(rear+".damper",{s*.76f,.41f,-1.76f},1);
            auto* spring=required(rear+".spring");rearSpring[i]={spring,nullptr,required(rear+".spring.coil"),required(rear+".spring.upper_seat"),required(rear+".spring.lower_seat"),spring->position,{s*.76f,.44f,-1.59f},4};
            rearLinks[i*2]=link(rear+".lower_link",{s*.77f,.31f,-1.59f});rearLinks[i*2+1]=link(rear+".upper_link",{s*.77f,.49f,-1.59f});
        }
        panhard=link("rear.panhard",{.76f,.43f,-1.36f});prop=telescope("driveline.shaft",{0,.4f,-1.28f},3);
        car->traverseType<Mesh>([](Mesh& m){m.castShadow=m.receiveShadow=true;for(const auto& material:m.materials())if(material->transparent){material->depthWrite=false;m.castShadow=false;}});
    }
    static void rigid(Link& l,const Vector3& a,const Vector3& end){
        l.node->matrixAutoUpdate=true;l.node->position.copy(a);l.node->quaternion.setFromUnitVectors(l.b.clone().sub(l.a).normalize(),end.clone().sub(a).normalize());l.node->scale.set(1,1,1);
    }
    static void axialSpring(Object3D& n,const Vector3& axis,float scale){
        Quaternion q;q.setFromUnitVectors(Vector3(0,1,0),axis);Matrix4 r,inv,s,t;r.makeRotationFromQuaternion(q);inv.copy(r).invert();s.makeScale(1,scale,1);t.makeTranslation(n.position);
        n.matrixAutoUpdate=false;n.matrix->copy(t).multiply(r).multiply(s).multiply(inv);n.matrixWorldNeedsUpdate=true;
    }
    void extend(Telescope& t,const Vector3& end){
        const auto old=t.b.clone().sub(t.a);const float rest=old.length();const auto axis=old.clone().multiplyScalar(1/rest),next=end.clone().sub(t.a);const float length=next.length();
        t.node->position.copy(t.a);t.node->quaternion.setFromUnitVectors(axis,next.clone().normalize());t.node->scale.set(1,1,1);
        const float bodyEnd=(t.kind>=2?.72f:.63f)*rest,rod=(t.kind==0?.60f:t.kind==1?.68f:t.kind==2?.45f:.40f)*rest;
        t.shaft->position.copy(axis).multiplyScalar(length);t.shaft->scale.set(1,1,1);minDamperEngagement=std::min(minDamperEngagement,bodyEnd-(length-rod));
        if(t.kind==0){t.lowerSeat->position.copy(axis).multiplyScalar(length-.12f*rest);axialSpring(*t.coil,axis,(length-.30f*rest)/(.70f*rest));}
    }
    template<class Height> void step(const Vector3& p,float heading,float acceleration,float lateral,float dt,Height height,float steering=0){ride.step(p,heading,steering,acceleration,lateral,dt,height);}
    template<class Height> void present(const Vector3& position,const Quaternion& orientation,const std::array<float,4>& travel,float steering,float spin,Height height){
        car->position.copy(position);car->quaternion.copy(orientation);
        const auto rear=bajaAxlePose(travel[2],travel[3]);axleRoll=rear.roll;Quaternion aq;aq.setFromAxisAngle(Vector3(0,0,1),axleRoll);
        axle->position.copy(rear.center);axle->quaternion.copy(aq);
        auto axlePoint=[&](Vector3 p){return p.applyQuaternion(aq).add(rear.center);};
        for(int i=0;i<2;++i){const int side=i?1:-1;const auto p=bajaFrontPose(travel[i],side);Quaternion camber,yaw;camber.setFromAxisAngle(Vector3(0,0,1),p.camber);yaw.setFromAxisAngle(Vector3(0,1,0),steeringAngle(i,steering,bajaDimensions));auto kq=camber.clone().multiply(yaw);
            rigid(lowerArm[i],lowerArm[i].a,p.lower);rigid(upperArm[i],upperArm[i].a,p.upper);
            maxArmLengthError=std::max({maxArmLengthError,std::abs(p.lower.distanceTo(lowerArm[i].a)-lowerArm[i].b.distanceTo(lowerArm[i].a)),std::abs(p.upper.distanceTo(upperArm[i].a)-upperArm[i].b.distanceTo(upperArm[i].a))});
            upright[i]->position.copy(p.lower);upright[i]->quaternion.copy(kq);
            const auto hub=Vector3(side*.055f,.09f,0).applyQuaternion(kq).add(p.lower);steer[i]->position.copy(hub);steer[i]->quaternion.copy(kq);
            contacts[i].local=hub;
            const auto tieEnd=Vector3(side*.018f,.03f,-.11f).applyQuaternion(kq).add(p.lower);auto tieStart=tieRod[i].a;
            const float length=tieRod[i].a.distanceTo(tieRod[i].b),dy=tieEnd.y-tieStart.y,dz=tieEnd.z-tieStart.z;
            tieStart.x=tieEnd.x-side*std::sqrt(std::max(.01f,length*length-dy*dy-dz*dz));rigid(tieRod[i],tieStart,tieEnd);rackSlide[i]->position.set(tieStart.x-side*.08f,tieStart.y,tieStart.z);
            extend(halfshaft[i],Vector3(side*-.07f,.09f,0).applyQuaternion(kq).add(p.lower));
            extend(frontShock[i],lowerArm[i].a.clone().lerp(p.lower,.81f));
            extend(rearShock[i],axlePoint({side*.76f,.01f,-.17f}));
            auto& spring=rearSpring[i];const auto v=spring.b.clone().sub(spring.a),end=axlePoint({side*.76f,.04f,0});const auto axis=v.clone().normalize(),next=end.clone().sub(spring.a);spring.node->quaternion.setFromUnitVectors(axis,next.clone().normalize());spring.lowerSeat->position.copy(axis).multiplyScalar(next.length());axialSpring(*spring.coil,axis,next.length()/v.length());
            for(int j=0;j<2;++j){auto& link=rearLinks[i*2+j];auto end=axlePoint({side*.77f,j?.09f:-.09f,0});maxRearBushingDeflection=std::max(maxRearBushingDeflection,std::abs(end.distanceTo(link.a)-link.b.distanceTo(link.a)));rigid(link,link.a,end);}
            contacts[i+2].local=axlePoint({side*1.025f,0,0});
        }
        rigid(panhard,panhard.a,axlePoint({.76f,.03f,.23f}));extend(prop,axlePoint({0,0,.31f}));
        for(int i=0;i<4;++i){roll[i]->rotation.x=spin;rotor[i]->rotation.x=spin;contacts[i].requested=travel[i];contacts[i].world=contacts[i].local.clone().applyQuaternion(orientation).add(position);
            Quaternion wq=orientation;if(i<2)wq.multiply(steer[i]->quaternion);else wq.multiply(aq);float floor=-1e9f;
            for(int row=-1;row<=1;++row)for(int j=-4;j<=4;++j){auto off=Vector3(row*.14f,-.47f*std::cos(j*.15f),.47f*std::sin(j*.15f)).applyQuaternion(wq);const float x=contacts[i].world.x+off.x,z=contacts[i].world.z+off.z,y=height(x,z);if(y-off.y>floor){floor=y-off.y;contacts[i].ground={x,y,z};}}
            contacts[i].gap=contacts[i].world.y-floor;
        }
    }
    template<class Height> void pose(const Vector3&,float,float steering,float spin,Height height){
        std::array<float,4> travel;for(int i=0;i<4;++i)travel[i]=std::clamp(ride.travelForHeight(i,ride.wheelY[i],ride.orientation()),bajaDimensions.droop,bajaDimensions.bump);
        present(ride.chassis,ride.orientation(),travel,steering,spin,height);
    }
    void updatePowertrain(float speed,float throttle,float dt,bool stopped){
        powertrain.gear=std::abs(speed)<8?1:std::abs(speed)<17?2:3;const float ratio=powertrain.gear==1?320.f:powertrain.gear==2?180.f:125.f;
        const float target=stopped?950.f:std::clamp(950+std::abs(speed)*ratio+throttle*180,950.f,5600.f);
        powertrain.rpm+=(target-powertrain.rpm)*(1-std::exp(-8*dt));powertrain.load+=((stopped?0:throttle)-powertrain.load)*(1-std::exp(-5*dt));
    }
};
inline void writeBajaRaceAudit(const std::filesystem::path& asset,const std::filesystem::path& directory){
    auto beat=[](){if(const auto* p=std::getenv("THREEPP_EVALUATION_HEARTBEAT")){std::ofstream f(p);f<<"Baja CPU audit";}};
    auto require=[](bool yes,const char* message){if(!yes)throw std::runtime_error(message);};beat();BajaRace rig(asset);auto flat=[](float,float){return 0.f;};int poses=0;
    // Actual loaded hierarchy: fixed arms, seated hubs, rigid axle and damper overlap.
    for(int l=0;l<=8;++l)for(int r=0;r<=8;++r){std::array<float,4> travel{.268f+l*.252f/8,.268f+r*.252f/8,.268f+l*.252f/8,.268f+r*.252f/8};
        for(float steer:{-.32f,0.f,.32f}){rig.present(Vector3(0,.07f,0),Quaternion(),travel,steer,0,flat);rig.car->updateMatrixWorld(true);++poses;
            for(int i=0;i<4;++i){Vector3 actual;rig.roll[i]->getWorldPosition(actual);require(actual.distanceTo(rig.contacts[i].world)<.0001f,"Baja wheel separates from hub");}
            require(std::abs(rig.contacts[2].local.distanceTo(rig.contacts[3].local)-2.05f)<.00001f,"Baja rear track changes");}
        beat();}
    require(rig.maxArmLengthError<.00003f,"Baja rigid wishbones stretch");require(rig.maxRearBushingDeflection<.0068f,"Baja rear joint exceeds rubber bushing clearance");require(rig.minDamperEngagement>.015f,"Baja damper/CV rod disengages from fixed body");
    auto settle=[&](BajaRideState& state,int frames,float dt,auto height,float speed){for(int n=0;n<frames;++n){Vector3 p(0,0,(n+1)*speed*dt);state.step(p,0,0,0,0,dt,height);if(n%30==0)beat();}};
    BajaRideState settled;settle(settled,360,1.f/120,flat,0);const float rest=settled.chassis.y;
    require(std::abs(settled.heaveVelocity)<.005f&&std::abs(settled.pitchVelocity)<.005f&&std::abs(settled.rollVelocity)<.005f,"Baja fails to settle at rest");
    auto accelerating=settled,braking=settled;
    for(int n=0;n<240;++n){accelerating.step(Vector3(),0,0,3,0,1.f/120,flat);braking.step(Vector3(),0,0,-3,0,1.f/120,flat);if(n%30==0)beat();}
    require(accelerating.pitch<-.004f&&braking.pitch>.004f,"Baja pitch fails to respond to weight transfer");
    require(accelerating.springForces[0]+accelerating.springForces[1]<settled.springForces[0]+settled.springForces[1]-500,"Baja acceleration does not unload front suspension");
    require(braking.springForces[0]+braking.springForces[1]>settled.springForces[0]+settled.springForces[1]+500,"Baja braking does not load front suspension");
    auto bump=[](float x,float z){return .075f*std::exp(-((z-9.f)*(z-9.f))/.6f)*(x<0?1.f:.35f);};
    BajaRideState a,b;settle(a,720,1.f/120,bump,8);settle(b,180,1.f/30,bump,8);
    require(a.chassis.distanceTo(b.chassis)<.004f&&std::abs(a.roll-b.roll)<.003f,"Baja motion depends on render frame rate");
    require(std::abs(a.chassis.y-rest)<.012f&&std::abs(a.heaveVelocity)<.02f&&std::abs(a.roll)<.01f,"Baja bump motion does not settle");
    auto drop=settled;drop.lift(.25f);drop.step(Vector3(),0,0,0,0,1.f/120,flat);float airborne=0;for(float f:drop.forces)airborne+=f;require(airborne<100,"Baja airborne tyres retain support");settle(drop,720,1.f/120,flat,0);require(std::abs(drop.chassis.y-rest)<.012f&&std::abs(drop.heaveVelocity)<.02f,"Baja drop fails to settle");
    std::ofstream out(directory/"baja-race-audit.json");out<<"{\"status\":\"PASS\",\"mechanicalPoses\":"<<poses<<",\"maximumRigidArmLengthError\":"<<rig.maxArmLengthError<<",\"maximumElasticRearJointDeflection\":"<<rig.maxRearBushingDeflection<<",\"minimumDamperEngagement\":"<<rig.minDamperEngagement<<",\"renderRatePositionDifference\":"<<a.chassis.distanceTo(b.chassis)<<",\"restHeight\":"<<rest<<",\"scope\":\"Loaded v3 GLB, rigid wishbones, rigid axle, fixed damper bodies/rods and bushing clearances. Force-based2200kg seven-coordinate ride passes rest, asymmetric bump,30/120Hz and airborne-drop settling.\"}\n";
}
}
