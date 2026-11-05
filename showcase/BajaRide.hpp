#pragma once
#include "BajaGeometry.hpp"
#include <limits>

namespace rally {
struct BajaRideTuning {
    float pitchInertia=3600.f,rollInertia=1700.f;
    float restingTravel=.40f,frontSpringRate=52762.9f,rearSpringRate=51138.8f;
    float lowCompression=3359.f,lowRebound=5598.f,damperKnee=.35f;
    float highCompression=1200.f,highRebound=2300.f;

};
// Seven vertical degrees of freedom: sprung heave/pitch/roll and one unsprung
// wheel coordinate per corner. Horizontal motion remains the rally controller.
// Compliant tyre contact and internal bump/droop impulses are distinct;
// rebound damping may pull on the body without pulling on the ground.
struct BajaRideState {
    static constexpr float sprungMass=2200.f,unsprungMass=70.f,gravity=9.81f;
    // The truck reuses the tested vertical solver in isolation from Safari. Actual integration and
    // energy calculations use the instance's tuning, including v2 comparisons.
    static constexpr float pitchInertia=BajaRideTuning{}.pitchInertia,rollInertia=BajaRideTuning{}.rollInertia;
    static constexpr float cgHeight=.75f,cgLongitudinal=.1272f;
    static constexpr float restingTravel=BajaRideTuning{}.restingTravel;
    static constexpr float integrationStep=1.f/360;
    static constexpr float tyreStiffness=340000.f,tyreDamping=2200.f,maximumTyreCompression=.055f;
    VehicleDimensions dimensions=bajaDimensions;
    BajaRideTuning tuning;
    Vector3 chassis,previousPosition,planarPosition;
    float heading=0,previousHeading=0,centerY=0;
    float heaveVelocity=0,pitch=0,roll=0,pitchVelocity=0,rollVelocity=0;
    std::array<float,4> wheelY{},wheelVelocity{},previousGround{},forces{},springForces{},travel{};
    std::array<bool,4> grounded{};
    bool ready=false;
    int bumpCorrections=0;
    float maxRoadVelocity=0,maxSpringForce=0,maxWheelVelocity=0;

    static float angleDelta(float a){while(a>3.14159265359f)a-=6.28318530718f;while(a<-3.14159265359f)a+=6.28318530718f;return a;}
    Vector3 cgOffset() const {return {0,cgHeight,cgLongitudinal};}
    Quaternion orientation()const{return chassisOrientation(heading,pitch,roll);}
    void updateOrigin(){const auto offset=cgOffset().applyQuaternion(orientation());Quaternion yaw;yaw.setFromAxisAngle(Vector3(0,1,0),heading);const auto levelOffset=cgOffset().applyQuaternion(yaw);
        chassis.x=planarPosition.x+levelOffset.x-offset.x;chassis.z=planarPosition.z+levelOffset.z-offset.z;chassis.y=centerY-offset.y;}
    float preload(int i)const {
        const float frontFraction=(dimensions.halfWheelbase+cgLongitudinal)/(2*dimensions.halfWheelbase);
        return sprungMass*gravity*(i<2?frontFraction:1-frontFraction)*.5f;
    }
    static float springRate(int i,const BajaRideTuning& tune=BajaRideTuning{}){return i<2?tune.frontSpringRate:tune.rearSpringRate;}
    static float damping(float speed,const BajaRideTuning& tune=BajaRideTuning{}){
        // Low shaft speeds control the body; the revised tune blows off at
        // impact speeds so the wheel can move rather than kicking the platform.
        const float v=std::abs(speed),knee=tune.damperKnee,low=speed>=0?tune.lowCompression:tune.lowRebound,high=speed>=0?tune.highCompression:tune.highRebound;
        return std::copysign(low*std::min(v,knee)+high*std::max(0.f,v-knee),speed);
    }
    float travelForHeight(int i,float y,const Quaternion& q)const {
        const auto up=Vector3(0,1,0).applyQuaternion(q);float t=travel[i];
        for(int n=0;n<5;++n){auto hub=bajaHubAtTravel(i,t,dimensions);hub.y=0;hub.applyQuaternion(q);
            t=(y-chassis.y-hub.y)/std::max(.6f,up.y);}
        return t;
    }
    void contactJacobians(int i,float t,float& jp,float& jr)const {
        const auto local=bajaHubAtTravel(i,t,dimensions).sub(cgOffset());
        const auto lever=local.clone().applyQuaternion(chassisOrientation(0,pitch,roll));
        jp=-lever.z;
        // Euler X/Z order: roll's vertical Jacobian includes the pitch cosine.
        jr=(local.x*std::cos(roll)-local.y*std::sin(roll))*std::cos(pitch);
    }
    template<class Height> WheelContact contact(int i,float steer,Height height)const {
        const auto q=orientation();WheelContact c;c.requested=travelForHeight(i,wheelY[i],q);
        c.local=bajaHubAtTravel(i,std::clamp(c.requested,dimensions.droop,dimensions.bump),dimensions);
        c.world=chassis.clone().add(c.local.clone().applyQuaternion(q));
        Quaternion camber;camber.setFromAxisAngle(Vector3(0,0,1),i<2?bajaFrontPose(std::clamp(c.requested,dimensions.droop,dimensions.bump),i%2?1:-1).camber:0);
        Quaternion steering;steering.setFromAxisAngle(Vector3(0,1,0),steeringAngle(i,steer,dimensions));
        const auto tyreRotation=q.clone().multiply(camber).multiply(steering);
        float floor=-std::numeric_limits<float>::infinity();
        for(int row=-1;row<=1;++row)for(int j=-4;j<=4;++j){
            const float axial=row*(dimensions.tyreHalfWidth*.63f),radius=dimensions.tyreRadius-(row==0?0.f:.008f),angle=j*.15f;
            auto offset=Vector3(axial,-radius*std::cos(angle),radius*std::sin(angle)).applyQuaternion(tyreRotation);
            const float x=c.world.x+offset.x,z=c.world.z+offset.z,y=height(x,z);
            if(y-offset.y>floor){floor=y-offset.y;c.ground={x,y,z};}
        }
        c.gap=c.world.y-floor;return c;
    }
    using Jacobian=std::array<float,4>; // body Y, pitch, roll, this wheel Y
    float inverseMass(const Jacobian& j)const{return j[0]*j[0]/sprungMass+j[1]*j[1]/tuning.pitchInertia+j[2]*j[2]/tuning.rollInertia+j[3]*j[3]/unsprungMass;}
    float normalVelocity(int i,const Jacobian& j)const{return j[0]*heaveVelocity+j[1]*pitchVelocity+j[2]*rollVelocity+j[3]*wheelVelocity[i];}
    void impulse(int i,const Jacobian& j,float amount){heaveVelocity+=j[0]*amount/sprungMass;pitchVelocity+=j[1]*amount/tuning.pitchInertia;rollVelocity+=j[2]*amount/tuning.rollInertia;wheelVelocity[i]+=j[3]*amount/unsprungMass;}
    void project(int i,const Jacobian& j,float amount){centerY+=j[0]*amount/sprungMass;pitch+=j[1]*amount/tuning.pitchInertia;roll+=j[2]*amount/tuning.rollInertia;wheelY[i]+=j[3]*amount/unsprungMass;updateOrigin();}
    template<class Height> float groundConstraint(int i,float steer,Height height)const {const auto c=contact(i,steer,height);return wheelY[i]-c.world.y+c.gap;}
    template<class Height> Jacobian groundJacobian(int i,float steer,Height height){
        Jacobian j;constexpr float e=.0005f;std::array<float*,4> coordinates{&centerY,&pitch,&roll,&wheelY[i]};
        for(int k=0;k<4;++k){const float saved=*coordinates[k];*coordinates[k]=saved+e;updateOrigin();const float a=groundConstraint(i,steer,height);
            *coordinates[k]=saved-e;updateOrigin();const float b=groundConstraint(i,steer,height);j[k]=(a-b)/(2*e);*coordinates[k]=saved;updateOrigin();}
        return j;
    }
    template<class Height> void reset(const Vector3& position,float yaw,Height height,const VehicleDimensions& dims=bajaDimensions){
        const auto selectedTuning=tuning;*this=BajaRideState{};tuning=selectedTuning;dimensions=dims;heading=previousHeading=yaw;previousPosition=planarPosition=position;
        const auto road=roadPose(position,yaw,height,dims);chassis={position.x,road.ride+dimensions.staticTravel-tuning.restingTravel,position.z};pitch=road.pitch;roll=road.roll;
        auto q=orientation();centerY=chassis.y+cgOffset().applyQuaternion(q).y;updateOrigin();
        for(int i=0;i<4;++i){travel[i]=.4f;wheelY[i]=bajaHubAtTravel(i,.4f).applyQuaternion(q).add(chassis).y;}
        for(int i=0;i<4;++i){const auto c=contact(i,0,height);travel[i]=c.requested;
            wheelY[i]=c.world.y;previousGround[i]=c.world.y-c.gap;grounded[i]=true;forces[i]=preload(i)+unsprungMass*gravity;springForces[i]=preload(i);}
        ready=true;
    }
    // Translate the complete sprung/unsprung system for controlled drop tests.
    void lift(float metres){centerY+=metres;chassis.y+=metres;for(auto& y:wheelY)y+=metres;forces.fill(0);grounded.fill(false);}
    template<class Height> void step(const Vector3& position,float yaw,float steer,float acceleration,float lateralAcceleration,float dt,Height height){
        if(!ready)reset(position,yaw,height,dimensions);
        const float duration=std::clamp(dt,0.f,.05f);if(duration<=0)return;
        const int count=std::max(1,static_cast<int>(std::ceil(duration/integrationStep-.00001f)));
        const float h=duration/count;const auto start=previousPosition;const float startYaw=previousHeading,deltaYaw=angleDelta(yaw-startYaw);
        for(int sub=0;sub<count;++sub){
            const float fraction=(sub+1.f)/count;planarPosition.x=start.x+(position.x-start.x)*fraction;planarPosition.z=start.z+(position.z-start.z)*fraction;
            heading=startYaw+deltaYaw*fraction;updateOrigin();auto q=orientation();
            std::array<float,4> jp{},jr{},roadY{},roadVelocity{},load{};
            std::array<Jacobian,4> groundJ;
            for(int i=0;i<4;++i){travel[i]=travelForHeight(i,wheelY[i],q);contactJacobians(i,std::clamp(travel[i],dimensions.droop,dimensions.bump),jp[i],jr[i]);
                const auto c=contact(i,steer,height);roadY[i]=c.world.y-c.gap;
                groundJ[i]=groundJacobian(i,steer,height);
                // Only prescribed horizontal movement is an external moving
                // boundary. Body roll/pitch and tyre support-radius changes
                // belong in the constraint Jacobian, not in a road-velocity
                // target that can feed angular motion back as impact energy.
                const float currentX=planarPosition.x,currentZ=planarPosition.z,currentYaw=heading;
                const float previousFraction=static_cast<float>(sub)/count;
                planarPosition.x=start.x+(position.x-start.x)*previousFraction;planarPosition.z=start.z+(position.z-start.z)*previousFraction;heading=startYaw+deltaYaw*previousFraction;updateOrigin();
                const float previousFloor=wheelY[i]-groundConstraint(i,steer,height);
                planarPosition.x=currentX;planarPosition.z=currentZ;heading=currentYaw;updateOrigin();
                roadVelocity[i]=(roadY[i]-previousFloor)/h;
                maxRoadVelocity=std::max(maxRoadVelocity,std::abs(roadVelocity[i]));
                // The wheel moves relative to its own body attachment. The
                // derivative comes from velocities, never a projection delta.
                const float rate=(wheelVelocity[i]-heaveVelocity-jp[i]*pitchVelocity-jr[i]*rollVelocity)/std::max(.6f,Vector3(0,1,0).applyQuaternion(q).y);
                const float compression=travel[i]-tuning.restingTravel;
                const float bump=std::max(0.f,travel[i]-(dimensions.bump-.035f));
                const float droop=std::max(0.f,dimensions.droop+.025f-travel[i]);
                springForces[i]=std::max(0.f,preload(i)+springRate(i,tuning)*compression)+damping(rate,tuning)*(i<2?1.f:.965f)+2200000.f*bump*bump-1400000.f*droop*droop;
                const float deflection=roadY[i]-wheelY[i];
                load[i]=deflection>0?std::max(0.f,tyreStiffness*deflection+tyreDamping*(roadVelocity[i]-normalVelocity(i,groundJ[i]))):0;
            }
            for(int axle=0;axle<2;++axle){const int l=2*axle,r=l+1;const float transfer=(axle==0?4500.f:3000.f)*(travel[r]-travel[l]);springForces[l]-=transfer;springForces[r]+=transfer;}
            float support=0;for(float f:forces)support+=f;
            const float coupling=std::clamp(support/((sprungMass+4*unsprungMass)*gravity),0.f,1.f);
            float fy=-sprungMass*gravity,tx=-sprungMass*cgHeight*std::clamp(acceleration,-20.f,15.f)*coupling,tz=sprungMass*cgHeight*std::clamp(lateralAcceleration,-18.f,18.f)*coupling;
            for(int i=0;i<4;++i){const float force=std::clamp(springForces[i],-15000.f,22000.f);springForces[i]=force;
                fy+=force+load[i]*groundJ[i][0];tx+=jp[i]*force+load[i]*groundJ[i][1];tz+=jr[i]*force+load[i]*groundJ[i][2];
                wheelVelocity[i]+=(-unsprungMass*gravity-force+load[i]*groundJ[i][3])/unsprungMass*h;wheelY[i]+=wheelVelocity[i]*h;}
            heaveVelocity+=fy/sprungMass*h;centerY+=heaveVelocity*h;
            pitchVelocity+=(tx-100*pitchVelocity)/tuning.pitchInertia*h;rollVelocity+=(tz-100*rollVelocity)/tuning.rollInertia*h;
            pitch+=pitchVelocity*h;roll+=rollVelocity*h;updateOrigin();
            // Both constraints retain the finite wheel mass. Alternating their
            // unilateral impulses handles bump-plus-ground contact without
            // turning a separating wheel into an infinite-mass ground partner.
            bool corrected=false;
            for(int pass=0;pass<64;++pass){
                bool touched=false;q=orientation();
                for(int i=0;i<4;++i){travel[i]=travelForHeight(i,wheelY[i],q);auto c=contact(i,steer,height);roadY[i]=c.world.y-c.gap;
                    const float penetration=roadY[i]-maximumTyreCompression-wheelY[i];
                    if(penetration>.000002f){project(i,groundJ[i],penetration/inverseMass(groundJ[i]));touched=true;q=orientation();}
                    if(penetration>=-.00005f){const float closing=roadVelocity[i]-normalVelocity(i,groundJ[i]);if(closing>0){const float amount=closing/inverseMass(groundJ[i]);impulse(i,groundJ[i],amount);load[i]+=amount/h;}}
                    travel[i]=travelForHeight(i,wheelY[i],q);
                    const bool bump=travel[i]>dimensions.bump,droop=travel[i]<dimensions.droop;
                    if(!bump&&!droop)continue;
                    const float limit=bump?dimensions.bump:dimensions.droop;
                    const auto hub=chassis.clone().add(bajaHubAtTravel(i,limit,dimensions).applyQuaternion(q));
                    const float sign=bump?1.f:-1.f,error=sign*(wheelY[i]-hub.y);if(error<.000002f)continue;
                    float p,r;contactJacobians(i,limit,p,r);
                    const Jacobian stopJ{sign,sign*p,sign*r,-sign};
                    project(i,stopJ,error/inverseMass(stopJ));
                    const float closing=-normalVelocity(i,stopJ);if(closing>0)impulse(i,stopJ,closing/inverseMass(stopJ));
                    updateOrigin();q=orientation();touched=corrected=true;
                }
                if(!touched)break;
            }
            if(corrected)++bumpCorrections;
            q=orientation();
            for(int i=0;i<4;++i){travel[i]=travelForHeight(i,wheelY[i],q);const auto c=contact(i,steer,height);previousGround[i]=c.world.y-c.gap;
                maxSpringForce=std::max(maxSpringForce,std::abs(springForces[i]));maxWheelVelocity=std::max(maxWheelVelocity,std::abs(wheelVelocity[i]));
                grounded[i]=c.gap<.0005f&&load[i]>0;forces[i]=std::max(0.f,load[i]);}
        }
        previousPosition=position;previousHeading=yaw;
    }
};
}
