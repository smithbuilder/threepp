#pragma once
#include "CatrinaDimensions.hpp"
#include "threepp/loaders/GLTFLoader.hpp"
#include <filesystem>
#include <fstream>
#include <stdexcept>

namespace rally {
// Presentation only. Bullet owns the chassis, contact forces and requested hub
// heights. Fixed-length arm/axle arcs introduce lateral/fore-aft offsets relative
// to the solver's straight suspension queries; this is not a multibody solver.
struct CatrinaRig {
    std::shared_ptr<Group> car=Group::create();
    std::array<Object3D*,4> wheel{},steer{},spin{},hydraulic{},rod{},coil{};
    std::array<Object3D*,4> damper{},damperRod{};
    std::array<Object3D*,4> damperTopJoint{},damperLowerJoint{};
    std::array<Vector3,4> damperPinAxis{},damperEndTarget{};
    std::array<Object3D*,4> springSeat{},brakeSpin{};
    std::array<Object3D*,4> hydraulicBarrelTip{},hydraulicRodTip{},hydraulicCupTop{};
    std::array<Vector3,4> springSeatTarget{};
    std::array<Vector3,4> damperFrame{},damperMountOffset{};
    std::array<Object3D*,2> lower{},upper{},upright{};
    Object3D *axle{},*trunk{},*hood{},*shaft{};
    Object3D *shaftSlip{},*shaftFrontJoint{},*shaftRearJoint{},*shaftTubeEnd{},*shaftSlipTip{};
    Vector3 shaftEndTarget{};
    struct Link {Object3D* node{};Vector3 a,b;float length=0;};
    std::array<Link,4> rearLinks{};
    std::array<Vector3,4> hubs{};
    bool trunkOpen=false,hoodOpen=false;
    float maxRigidLinkError=0,maxRearLinkError=0,maxAxleSpanError=0,minRodOverlap=1;
    float maxHubHeightError=0;
    float minimumHydraulicHeadClearance=1;
    float minimumDamperOverlap=1,minimumDamperHeadClearance=1,maximumDamperEyeError=0;
    float maximumSeatAttachmentError=0,maximumSeatScaleError=0,maximumBrakeRotationError=0;
    float minimumSignedSpringLength=10,minimumSpringSolidClearance=10,minimumCupGlandClearance=10,maximumUnrealizedCupCommand=0;
    float maximumPinAttachmentError=0,maximumPinAxisError=0,maximumBearingMisalignment=0;
    float maximumRigidMetalScaleError=0;
    float maximumShaftScaleError=0,maximumShaftEndpointError=0,maximumTubeLengthError=0,maximumSlipLengthError=0,minimumSlipEngagement=10;
    static constexpr float restHub=.2891f,frontZ=1.5113f,armLength=.535f;
    // Authored long-travel rear dampers live below the trunk, with an inboard
    // lower-eye bracket on each trailing arm; mirrored in catrina_hardware.py.
    static constexpr float rearDamperRatio=.84f,rearDamperInboard=.10f;
    static constexpr float rearDamperTopX=.20f,rearDamperTopY=.50f,rearDamperTopZ=-2.00f;
    static constexpr float rearDamperBarrelEnd=.665f,rearDamperRodLength=.660f;
    static constexpr float hydraulicBarrelEnd=.245f,hydraulicRodLength=.245f;
    static constexpr float cupRestDistance=.310f,cupMinimumDistance=.280f,cupMaximumDistance=.430f;
    static constexpr float springSolidHeight=.102f,minimumSpringLength=.114f;
    static constexpr float shaftTubeLength=1.600f,shaftSlipLength=.550f;

    Object3D* required(const std::string& name){
        auto* n=car->getObjectByName(name);
        if(!n)throw std::runtime_error("Missing La Catrina interface: "+name);
        return n;
    }
    Link makeLink(const std::string& name,const Vector3& end){
        auto* n=required(name);return {n,n->position,end,n->position.distanceTo(end)};
    }
    explicit CatrinaRig(const std::filesystem::path& path){
        auto a=GLTFLoader{}.load(path);
        if(!a||!a->scene)throw std::runtime_error("Cannot load La Catrina GLB");
        car->add(a->scene);
        for(int i=0;i<4;++i){const auto n=std::to_string(i);
            wheel[i]=required("wheel_"+n);steer[i]=required("wheel_"+n+"_steer");spin[i]=required("wheel_"+n+"_spin");
            hydraulic[i]=required("hydraulic_"+n);rod[i]=required("hydraulic_"+n+"_rod");coil[i]=required("coil_"+n);
            damper[i]=required("damper_"+n);damperRod[i]=required("damper_"+n+"_rod");
            damperTopJoint[i]=required("damper_"+n+"_top_joint");damperLowerJoint[i]=required("damper_"+n+"_lower_joint");
            springSeat[i]=required("coil_"+n+"_seat");brakeSpin[i]=required("brake_"+n+"_spin");
            hydraulicBarrelTip[i]=required("hydraulic_"+n+"_barrel_end");hydraulicRodTip[i]=required("hydraulic_"+n+"_rod_tip");hydraulicCupTop[i]=required("hydraulic_"+n+"_cup_top");
            const float sign=i%2?1.f:-1.f;
            damperFrame[i]=i<2?Vector3(sign*.48f,.78f,frontZ+.12f):Vector3(sign*rearDamperTopX,rearDamperTopY,rearDamperTopZ);
            damperMountOffset[i]=i<2?Vector3(sign*armLength*.38f,.03f,.12f):Vector3(-sign*rearDamperInboard,.02f,(-frontZ+.45f)*rearDamperRatio);
            damperPinAxis[i]=i<2?Vector3(0,0,1):Vector3(.9f,-.25f,-sign*.35f).normalize();
            if(i<2){lower[i]=required("front_"+n+"_lower");upper[i]=required("front_"+n+"_upper");upright[i]=required("upright_"+n);}
        }
        axle=required("rear_axle");trunk=required("trunk_hinge");hood=required("hood_hinge");shaft=required("driveshaft");
        shaftSlip=required("driveshaft_slip");shaftFrontJoint=required("driveshaft_front_joint");shaftRearJoint=required("driveshaft_rear_joint");shaftTubeEnd=required("driveshaft_tube_end");shaftSlipTip=required("driveshaft_slip_tip");
        rearLinks[0]=makeLink("rear_2_lower",{-.56f,.33f,-frontZ});
        rearLinks[1]=makeLink("rear_3_lower",{ .56f,.33f,-frontZ});
        rearLinks[2]=makeLink("rear_upper",{0,.42f,-frontZ});
        rearLinks[3]=makeLink("rear_panhard",{.56f,.35f,-1.30f});
        car->traverseType<Mesh>([](Mesh& mesh){
            mesh.castShadow=mesh.receiveShadow=true;
            for(auto& material:mesh.materials())if(material->transparent){material->depthWrite=false;mesh.castShadow=false;}
        });
    }
    static Quaternion rearRotation(float roll,float yaw,float pitch){
        Quaternion q,r,p;q.setFromAxisAngle({0,1,0},yaw);r.setFromAxisAngle({0,0,1},roll);p.setFromAxisAngle({1,0,0},pitch);
        return q.multiply(r).multiply(p);
    }
    struct AxlePose {Vector3 center;Quaternion orientation;};
    AxlePose rearPose(float left,float right){
        const float roll=std::asin(std::clamp((right-left)/1.51f,-.99f,.99f)),y=(left+right)*.5f;
        // Four closed constraints: two lower trailing arms, central upper arm,
        // and Panhard bar. Solve the remaining axle x/z/yaw/pitch coordinates.
        // All steel lengths and the 1.51 m axle span stay unchanged.
        std::array<float,4> v{0,-frontZ,0,0};
        auto residual=[&](const std::array<float,4>& x){
            std::array<float,4> out{};auto q=rearRotation(roll,x[2],x[3]);Vector3 c(x[0],y,x[1]);
            for(int j=0;j<4;++j){auto end=rearLinks[j].b.clone().sub(Vector3(0,restHub,-frontZ)).applyQuaternion(q).add(c);out[j]=end.distanceTo(rearLinks[j].a)-rearLinks[j].length;}
            return out;
        };
        for(int iteration=0;iteration<24;++iteration){
            auto f=residual(v);float error=0;for(float e:f)error=std::max(error,std::abs(e));if(error<.000002f)break;
            float matrix[4][5]{};
            for(int j=0;j<4;++j){auto shifted=v;shifted[j]+=.001f;auto df=residual(shifted);for(int i=0;i<4;++i)matrix[i][j]=(df[i]-f[i])/.001f;}
            for(int i=0;i<4;++i)matrix[i][4]=-f[i];
            bool valid=true;
            for(int j=0;j<4;++j){int pivot=j;for(int i=j+1;i<4;++i)if(std::abs(matrix[i][j])>std::abs(matrix[pivot][j]))pivot=i;
                if(std::abs(matrix[pivot][j])<1e-7f){valid=false;break;}
                for(int k=j;k<5;++k)std::swap(matrix[pivot][k],matrix[j][k]);const float divisor=matrix[j][j];for(int k=j;k<5;++k)matrix[j][k]/=divisor;
                for(int i=0;i<4;++i)if(i!=j){const float factor=matrix[i][j];for(int k=j;k<5;++k)matrix[i][k]-=factor*matrix[j][k];}
            }
            if(!valid)break;
            for(int j=0;j<4;++j)v[j]+=std::clamp(matrix[j][4],-.15f,.15f);
        }
        return {{v[0],y,v[1]},rearRotation(roll,v[2],v[3])};
    }
    static void orientLink(Object3D& node,const Vector3& a,const Vector3& oldEnd,const Vector3& newEnd){
        node.position.copy(a);node.quaternion.setFromUnitVectors(oldEnd.clone().sub(a).normalize(),newEnd.clone().sub(a).normalize());node.scale.set(1,1,1);
    }
    static Quaternion aimDamper(const Vector3& axis,const Vector3& pinAxis){
        Quaternion aim;aim.setFromUnitVectors({0,-1,0},axis);
        const auto current=Vector3(0,0,1).applyQuaternion(aim);
        auto target=pinAxis.clone().addScaledVector(axis,-pinAxis.dot(axis)).normalize();
        const float twistAngle=std::atan2(axis.dot(current.clone().cross(target)),current.dot(target));
        Quaternion twist;twist.setFromAxisAngle(axis,twistAngle);return twist.multiply(aim);
    }
    void panels(){trunk->rotation.x=trunkOpen?1.08f:0;hood->rotation.x=hoodOpen?-1.10f:0;}
    void present(const Vector3& p,const Quaternion& q,const std::array<float,4>& travel,float steering,
                 const std::array<float,4>& spins,const std::array<float,4>& extension={}){
        car->position.copy(p);car->quaternion.copy(q);
        std::array<Vector3,4> springBottom{};
        for(int i=0;i<2;++i){const float sign=i?1.f:-1.f;
            const float target=std::clamp(travel[i],catrinaFrontDroopStop,catrinaDimensions.bump),dy=target-restHub;
            const float span=std::sqrt(std::max(.0001f,armLength*armLength-dy*dy));
            const Vector3 low(sign*(.18f+span),.25f+dy,frontZ),high(low.x,.43f+dy,frontZ);
            const Vector3 a(sign*.18f,.25f,frontZ),b(sign*.18f,.43f,frontZ);
            orientLink(*lower[i],a,{sign*.715f,.25f,frontZ},low);orientLink(*upper[i],b,{sign*.715f,.43f,frontZ},high);
            maxRigidLinkError=std::max({maxRigidLinkError,std::abs(low.distanceTo(a)-armLength),std::abs(high.distanceTo(b)-armLength)});
            Quaternion yaw;yaw.setFromAxisAngle({0,1,0},steeringAngle(i,steering,catrinaDimensions));
            // Steering knuckle offset moves around its ball-joint axis.
            hubs[i]=Vector3(sign*.05f,.0391f,0).applyQuaternion(yaw).add(low);
            wheel[i]->position.copy(hubs[i]);wheel[i]->quaternion.identity();steer[i]->quaternion.copy(yaw);
            upright[i]->position.copy(hubs[i]);upright[i]->quaternion.copy(yaw);
            springBottom[i]=a.clone().lerp(low,(.55f-.18f)/armLength).add(Vector3(0,.02f,0));
            maxHubHeightError=std::max(maxHubHeightError,std::abs(hubs[i].y-target));
        }
        const float rearL=std::clamp(travel[2],catrinaRearDroopStop,catrinaDimensions.bump),rearR=std::clamp(travel[3],catrinaRearDroopStop,catrinaDimensions.bump);
        const auto rear=rearPose(rearL,rearR);axle->position.copy(rear.center);axle->quaternion.copy(rear.orientation);
        auto axlePoint=[&](Vector3 point){return point.sub(Vector3(0,restHub,-frontZ)).applyQuaternion(rear.orientation).add(rear.center);};
        for(int i=2;i<4;++i){float sign=i==3?1.f:-1.f;hubs[i]=axlePoint({sign*.755f,restHub,-frontZ});wheel[i]->position.copy(hubs[i]);wheel[i]->quaternion.copy(rear.orientation);steer[i]->quaternion.identity();springBottom[i]=axlePoint({sign*.56f,.33f,-frontZ});maxHubHeightError=std::max(maxHubHeightError,std::abs(hubs[i].y-(i==2?rearL:rearR)));}
        maxAxleSpanError=std::max(maxAxleSpanError,std::abs(hubs[2].distanceTo(hubs[3])-1.51f));
        for(auto& link:rearLinks){const auto end=axlePoint(link.b);orientLink(*link.node,link.a,link.b,end);maxRearLinkError=std::max(maxRearLinkError,std::abs(end.distanceTo(link.a)-link.length));}
        // Separate shocks pivot at frame and lower-arm eyes. Only the inner
        // rod translates; neither the barrel nor the steel shaft is stretched.
        // Reduced-motion custom mounts are authored in catrina_hardware.py.
        for(int i=0;i<4;++i){
            auto* mount=i<2?lower[i]:rearLinks[i-2].node;
            const auto end=damperMountOffset[i].clone().applyQuaternion(mount->quaternion).add(mount->position);
            const auto axis=end.clone().sub(damperFrame[i]);const float length=axis.length();
            const auto direction=axis.clone().normalize();const auto movingPin=damperPinAxis[i].clone().applyQuaternion(mount->quaternion);
            damper[i]->position.copy(damperFrame[i]);damper[i]->quaternion.copy(aimDamper(direction,damperPinAxis[i]));
            damper[i]->scale.set(1,1,1);damperRod[i]->position.set(0,-length,0);damperRod[i]->scale.set(1,1,1);
            damperRod[i]->quaternion.copy(damper[i]->quaternion.clone().invert().multiply(aimDamper(direction,movingPin)));
            damperEndTarget[i].copy(end);
            const float barrelEnd=i<2?.39f:rearDamperBarrelEnd,rodLength=i<2?.36f:rearDamperRodLength;
            minimumDamperOverlap=std::min(minimumDamperOverlap,barrelEnd+rodLength-length);
            minimumDamperHeadClearance=std::min(minimumDamperHeadClearance,length-rodLength-.035f);
            const auto actual=damperRod[i]->position.clone().applyQuaternion(damper[i]->quaternion).add(damperFrame[i]);
            maximumDamperEyeError=std::max(maximumDamperEyeError,actual.distanceTo(end));
        }
        // Both steel members retain their length. Extension is a telescoping
        // slip joint, with the rear member anchored at the moving pinion.
        const Vector3 shaftStart(0,.30f,.59f),shaftRest(0,restHub,-1.2913f);const auto shaftEnd=axlePoint(shaftRest);
        const auto next=shaftEnd.clone().sub(shaftStart);shaftEndTarget.copy(shaftEnd);
        shaft->matrixAutoUpdate=true;shaft->position.copy(shaftStart);shaft->quaternion.setFromUnitVectors({0,1,0},next.clone().normalize());shaft->scale.set(1,1,1);
        shaftSlip->position.set(0,next.length(),0);shaftSlip->quaternion.identity();shaftSlip->scale.set(1,1,1);
        for(int i=0;i<4;++i){
            spin[i]->rotation.x=spins[i];brakeSpin[i]->rotation.x=spins[i];const float sign=i%2?1.f:-1.f;
            const Vector3 top(sign*(i<2?.55f:.56f),.86f,i<2?frontZ:-frontZ);
            const auto toSeat=springBottom[i].clone().sub(top);const float seatDistance=toSeat.length();
            const auto axis=toSeat.clone().normalize();Quaternion aimDown;aimDown.setFromUnitVectors({0,-1,0},axis);
            hydraulic[i]->position.copy(top);hydraulic[i]->quaternion.copy(aimDown);
            hydraulic[i]->scale.set(1,1,1);rod[i]->scale.set(1,1,1);
            // The requested pressure/preload command remains in the vehicle
            // solver. This presentation ram stops at its real stroke and at
            // the coil's compression limit instead of crossing the lower seat.
            const float requestedCup=cupRestDistance+std::clamp(extension[i]*.42f,0.f,.244f);
            const float upperStop=std::min(cupMaximumDistance,seatDistance-minimumSpringLength);
            const float cupDistance=std::clamp(requestedCup,cupMinimumDistance,std::max(cupMinimumDistance,upperStop));
            rod[i]->position.set(0,-cupDistance,0);
            const float springLength=seatDistance-cupDistance;const auto springAxis=axis.clone().negate();
            coil[i]->position.copy(springBottom[i]);coil[i]->quaternion.setFromUnitVectors({0,1,0},springAxis);coil[i]->scale.set(1,springLength/(i<2?.28f:.22f),1);
            springSeatTarget[i].copy(springBottom[i]);springSeat[i]->position.copy(springBottom[i]);
            springSeat[i]->quaternion.copy(coil[i]->quaternion);springSeat[i]->scale.set(1,1,1);
            minRodOverlap=std::min(minRodOverlap,hydraulicBarrelEnd+hydraulicRodLength-cupDistance);
            minimumHydraulicHeadClearance=std::min(minimumHydraulicHeadClearance,cupDistance-hydraulicRodLength-.030f);
            minimumSignedSpringLength=std::min(minimumSignedSpringLength,springLength);
            minimumSpringSolidClearance=std::min(minimumSpringSolidClearance,springLength-springSolidHeight);
            minimumCupGlandClearance=std::min(minimumCupGlandClearance,cupDistance-.015f-(hydraulicBarrelEnd+.004f));
            maximumUnrealizedCupCommand=std::max(maximumUnrealizedCupCommand,requestedCup-cupDistance);
        }
        panels();
    }
    void audit(const std::filesystem::path& directory){
        auto require=[](bool ok,const char* message){if(!ok)throw std::runtime_error(message);};int poses=0;
        auto orientationError=[&](const Quaternion& a,const Quaternion& b){
            // Matrix decomposition returns float quaternions whose norms can
            // differ slightly from one. acos(dot(a,b)) can then report an
            // error even for identical rotations. Normalize in double and
            // measure the shortest angle of conjugate(a)*b with atan2.
            std::array<double,4> qa{a.x,a.y,a.z,a.w},qb{b.x,b.y,b.z,b.w};
            double na=0,nb=0;for(int k=0;k<4;++k){na+=qa[k]*qa[k];nb+=qb[k]*qb[k];}
            require(std::isfinite(na)&&std::isfinite(nb)&&na>1e-20&&nb>1e-20,"La Catrina invalid brake orientation");
            na=std::sqrt(na);nb=std::sqrt(nb);for(int k=0;k<4;++k){qa[k]/=na;qb[k]/=nb;}
            const double x=qa[3]*qb[0]-qa[0]*qb[3]-qa[1]*qb[2]+qa[2]*qb[1];
            const double y=qa[3]*qb[1]+qa[0]*qb[2]-qa[1]*qb[3]-qa[2]*qb[0];
            const double z=qa[3]*qb[2]-qa[0]*qb[1]+qa[1]*qb[0]-qa[2]*qb[3];
            const double w=qa[3]*qb[3]+qa[0]*qb[0]+qa[1]*qb[1]+qa[2]*qb[2];
            return static_cast<float>(2*std::atan2(std::sqrt(x*x+y*y+z*z),std::abs(w)));
        };
        std::filesystem::create_directories(directory);
        std::ofstream poseFile(directory/"catrina-rig-poses.csv");
        poseFile<<"pose,wheel,x,y,z,qx,qy,qz,qw\n";
        for(int l=0;l<=8;++l)for(int r=0;r<=8;++r)for(float steering:{-.48f,0.f,.48f}){
            std::array<float,4> travel{catrinaFrontDroopStop+l*(.42f-catrinaFrontDroopStop)/8,catrinaFrontDroopStop+r*(.42f-catrinaFrontDroopStop)/8,catrinaRearDroopStop+l*(.42f-catrinaRearDroopStop)/8,catrinaRearDroopStop+r*(.42f-catrinaRearDroopStop)/8};
            present({},Quaternion(),travel,steering,{.4f,.5f,.6f,.7f},{.58f,.58f,.58f,.58f});car->updateMatrixWorld(true);++poses;
            for(int i=0;i<4;++i){Vector3 p;Quaternion orientation;spin[i]->getWorldPosition(p);spin[i]->getWorldQuaternion(orientation);require(std::isfinite(p.x)&&std::isfinite(p.y)&&std::isfinite(p.z),"La Catrina non-finite hub");require(p.distanceTo(hubs[i])<.0001f,"La Catrina wheel separated from hub");
                poseFile<<poses<<','<<i<<','<<p.x<<','<<p.y<<','<<p.z<<','<<orientation.x<<','<<orientation.y<<','<<orientation.z<<','<<orientation.w<<'\n';}
            for(int i=0;i<4;++i){Vector3 p,scale;Quaternion brakeQ,wheelQ;
                springSeat[i]->getWorldPosition(p);springSeat[i]->getWorldScale(scale);
                maximumSeatAttachmentError=std::max(maximumSeatAttachmentError,p.distanceTo(springSeatTarget[i]));
                maximumSeatScaleError=std::max({maximumSeatScaleError,std::abs(scale.x-1),std::abs(scale.y-1),std::abs(scale.z-1)});
                brakeSpin[i]->getWorldQuaternion(brakeQ);spin[i]->getWorldQuaternion(wheelQ);
                maximumBrakeRotationError=std::max(maximumBrakeRotationError,orientationError(brakeQ,wheelQ));
                Vector3 top,cup,tip,barrelEnd,cupTop;hydraulic[i]->getWorldPosition(top);rod[i]->getWorldPosition(cup);
                hydraulicRodTip[i]->getWorldPosition(tip);hydraulicBarrelTip[i]->getWorldPosition(barrelEnd);hydraulicCupTop[i]->getWorldPosition(cupTop);
                const auto down=p.clone().sub(top).normalize();
                minimumSignedSpringLength=std::min(minimumSignedSpringLength,p.clone().sub(cup).dot(down));
                minimumSpringSolidClearance=std::min(minimumSpringSolidClearance,p.clone().sub(cup).dot(down)-springSolidHeight);
                minimumCupGlandClearance=std::min(minimumCupGlandClearance,cupTop.clone().sub(barrelEnd).dot(down)-.004f);
                minRodOverlap=std::min(minRodOverlap,barrelEnd.clone().sub(tip).dot(down));
                minimumHydraulicHeadClearance=std::min(minimumHydraulicHeadClearance,tip.clone().sub(top).dot(down)-.030f);
                Vector3 fixed,moving;Quaternion fixedQ,movingQ,outerQ,innerQ;
                damperTopJoint[i]->getWorldPosition(fixed);damperLowerJoint[i]->getWorldPosition(moving);
                maximumPinAttachmentError=std::max({maximumPinAttachmentError,fixed.distanceTo(damperFrame[i]),moving.distanceTo(damperEndTarget[i])});
                damperTopJoint[i]->getWorldQuaternion(fixedQ);damperLowerJoint[i]->getWorldQuaternion(movingQ);damper[i]->getWorldQuaternion(outerQ);damperRod[i]->getWorldQuaternion(innerQ);
                fixedQ.normalize();movingQ.normalize();outerQ.normalize();innerQ.normalize();
                const auto fixedAxis=Vector3(0,0,1).applyQuaternion(fixedQ),movingAxis=Vector3(0,0,1).applyQuaternion(movingQ);
                auto* mount=i<2?lower[i]:rearLinks[i-2].node;const auto expectedMoving=damperPinAxis[i].clone().applyQuaternion(mount->quaternion);
                maximumPinAxisError=std::max({maximumPinAxisError,fixedAxis.distanceTo(damperPinAxis[i]),movingAxis.distanceTo(expectedMoving)});
                for(float cosine:{std::abs(fixedAxis.dot(Vector3(0,0,1).applyQuaternion(outerQ))),std::abs(movingAxis.dot(Vector3(0,0,1).applyQuaternion(innerQ)))})
                    maximumBearingMisalignment=std::max(maximumBearingMisalignment,std::acos(std::clamp(cosine,0.f,1.f)));
                for(auto* rigid:{damper[i],damperRod[i],damperTopJoint[i],damperLowerJoint[i],hydraulic[i],rod[i]}){
                    rigid->getWorldScale(scale);maximumRigidMetalScaleError=std::max({maximumRigidMetalScaleError,std::abs(scale.x-1),std::abs(scale.y-1),std::abs(scale.z-1)});
                }
            }
            Vector3 shaftA,shaftB,tubeEnd,slipTip,shaftScale,slipScale;
            shaftFrontJoint->getWorldPosition(shaftA);shaftRearJoint->getWorldPosition(shaftB);shaftTubeEnd->getWorldPosition(tubeEnd);shaftSlipTip->getWorldPosition(slipTip);
            shaft->getWorldScale(shaftScale);shaftSlip->getWorldScale(slipScale);
            maximumShaftScaleError=std::max({maximumShaftScaleError,std::abs(shaftScale.x-1),std::abs(shaftScale.y-1),std::abs(shaftScale.z-1),std::abs(slipScale.x-1),std::abs(slipScale.y-1),std::abs(slipScale.z-1)});
            maximumShaftEndpointError=std::max({maximumShaftEndpointError,shaftA.distanceTo(Vector3(0,.30f,.59f)),shaftB.distanceTo(shaftEndTarget)});
            maximumTubeLengthError=std::max(maximumTubeLengthError,std::abs(shaftA.distanceTo(tubeEnd)-shaftTubeLength));
            maximumSlipLengthError=std::max(maximumSlipLengthError,std::abs(shaftB.distanceTo(slipTip)-shaftSlipLength));
            minimumSlipEngagement=std::min(minimumSlipEngagement,tubeEnd.clone().sub(slipTip).dot(shaftB.clone().sub(shaftA).normalize()));
            if(const char* heartbeat=std::getenv("THREEPP_EVALUATION_HEARTBEAT")){std::ofstream f(heartbeat);f<<"La Catrina CPU rig audit";}
        }
        require(maxRigidLinkError<.0001f,"La Catrina front arm stretches");require(maxRearLinkError<.0002f,"La Catrina rear linkage loses closure");require(maxAxleSpanError<.0001f,"La Catrina rear axle span changes");require(maxHubHeightError<.0001f,"La Catrina visual hub height diverges");require(minRodOverlap>.05f,"La Catrina hydraulic rod disengages");
        require(minimumDamperOverlap>.025f,"La Catrina damper rod disengages");require(minimumDamperHeadClearance>0,"La Catrina damper rod strikes upper eye");require(maximumDamperEyeError<.0001f,"La Catrina damper eye separates from mount");
        require(maximumSeatAttachmentError<.0001f,"La Catrina lower spring seat separates");require(maximumSeatScaleError<.0001f,"La Catrina rigid lower spring seat stretches");require(maximumBrakeRotationError<.001f,"La Catrina drum does not follow wheel rotation");
        require(minimumSignedSpringLength>=minimumSpringLength-.00001f,"La Catrina spring cup crosses compression stop");require(minimumSpringSolidClearance>.0119f,"La Catrina spring exceeds solid height");require(minimumCupGlandClearance>.005f,"La Catrina spring cup enters hydraulic casing");
        require(maximumPinAttachmentError<.0001f,"La Catrina damper pin leaves clevis");require(maximumPinAxisError<.0001f,"La Catrina damper pin axis leaves fork axis");require(maximumBearingMisalignment<.5236f,"La Catrina spherical bearing exceeds30degrees");
        require(maximumRigidMetalScaleError<.0001f,"La Catrina rigid actuator or bearing stretches");
        require(maximumShaftScaleError<.0001f,"La Catrina steel driveshaft stretches");require(maximumTubeLengthError<.0001f&&maximumSlipLengthError<.0001f,"La Catrina rigid driveshaft member changes length");require(maximumShaftEndpointError<.0001f,"La Catrina driveshaft separates from joint");require(minimumSlipEngagement>.10f,"La Catrina driveshaft slip joint disengages");
        trunkOpen=hoodOpen=true;panels();require(std::abs(trunk->rotation.x-1.08f)<.0001f,"La Catrina trunk does not open");trunkOpen=hoodOpen=false;
        present({},Quaternion(),{restHub,restHub,restHub,restHub},0,{0,0,0,0});car->updateMatrixWorld(true);
        require(minimumHydraulicHeadClearance>.005f,"La Catrina hydraulic rod strikes upper head");
        for(int i=0;i<4;++i){const float sign=i%2?1.f:-1.f;require(hubs[i].distanceTo(Vector3(sign*(i<2?.765f:.755f),restHub,i<2?frontZ:-frontZ))<.0001f,"La Catrina authored hub dimensions mismatch");}
        std::filesystem::create_directories(directory);std::ofstream out(directory/"catrina-rig-audit.json");
        out<<"{\"status\":\"PASS\",\"poses\":"<<poses<<",\"maximumFrontArmError\":"<<maxRigidLinkError<<",\"maximumRearLinkError\":"<<maxRearLinkError<<",\"maximumAxleSpanError\":"<<maxAxleSpanError<<",\"maximumHubHeightError\":"<<maxHubHeightError<<",\"minimumRodOverlap\":"<<minRodOverlap<<",\"minimumHydraulicHeadClearance\":"<<minimumHydraulicHeadClearance<<",\"minimumDamperOverlap\":"<<minimumDamperOverlap<<",\"minimumDamperHeadClearance\":"<<minimumDamperHeadClearance<<",\"maximumDamperEyeError\":"<<maximumDamperEyeError<<",\"maximumSeatAttachmentError\":"<<maximumSeatAttachmentError<<",\"maximumSeatScaleError\":"<<maximumSeatScaleError<<",\"maximumBrakeRotationError\":"<<maximumBrakeRotationError<<",\"minimumSignedSpringLength\":"<<minimumSignedSpringLength<<",\"minimumSpringSolidClearance\":"<<minimumSpringSolidClearance<<",\"minimumCupGlandClearance\":"<<minimumCupGlandClearance<<",\"maximumUnrealizedCupCommand\":"<<maximumUnrealizedCupCommand<<",\"maximumPinAttachmentError\":"<<maximumPinAttachmentError<<",\"maximumPinAxisError\":"<<maximumPinAxisError<<",\"maximumBearingMisalignmentRadians\":"<<maximumBearingMisalignment<<",\"maximumRigidMetalScaleError\":"<<maximumRigidMetalScaleError<<",\"maximumShaftScaleError\":"<<maximumShaftScaleError<<",\"maximumShaftEndpointError\":"<<maximumShaftEndpointError<<",\"maximumTubeLengthError\":"<<maximumTubeLengthError<<",\"maximumSlipLengthError\":"<<maximumSlipLengthError<<",\"minimumSlipEngagement\":"<<minimumSlipEngagement<<",\"scope\":\"Loaded GLB hierarchy; rigid front arms and closed rear linkage; fixed axle track; hub pivots, hydraulic and separate damper rod engagement. Visual linkage arcs differ laterally from straight suspension rays; not exhaustive mesh clearance.\"}\n";
    }
};
}
