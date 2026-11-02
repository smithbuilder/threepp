#pragma once
#include "RallyVehicle.hpp"

namespace rally {
// Reduced sprung-body model: three dynamic axes supported by four kinematic
// wheel contacts. SI units, fixed 120 Hz, no tyre forces/unsprung-mass solver.
struct RideDynamics {
    static constexpr float mass=620,gravity=9.81f,springRate=18000;
    static constexpr float compressionDamping=1700,reboundDamping=2400,antiRollRate=2600;
    static constexpr float pitchInertia=540,rollInertia=460,cgHeight=.68f,staticTravel=.41f;
    VehicleDimensions dimensions=buggyDimensions;
    Vector3 chassis;
    float heaveVelocity=0,pitch=0,roll=0,pitchVelocity=0,rollVelocity=0;
    std::array<float,4> previousTravel{},forces{},travel{};
    std::array<bool,4> grounded{};
    bool ready=false;
    int bumpCorrections=0;

    template<class Height> void reset(const Vector3& position,float heading,Height height,const VehicleDimensions& dims=buggyDimensions){
        const auto selected=dims;*this=RideDynamics{};dimensions=selected;auto road=roadPose(position,heading,height,dimensions);
        chassis={position.x,road.ride,position.z};pitch=road.pitch;roll=road.roll;
        auto q=chassisOrientation(heading,pitch,roll);constrainRide(chassis,q,0,height,dimensions);
        for(int i=0;i<4;++i)previousTravel[i]=wheelContact(i,chassis,q,0,height,false,dimensions).requested;
        ready=true;
    }
    template<class Height> void step(const Vector3& position,float heading,float steer,float acceleration,float lateralAcceleration,float dt,Height height){
        if(!ready)reset(position,heading,height,dimensions);
        // Fixed-size internal steps also bound callers with a slow render frame.
        float remaining=std::clamp(dt,0.f,.05f);
        chassis.x=position.x;chassis.z=position.z;
        while(remaining>1e-6f){float h=std::min(remaining,1.f/120);remaining-=h;
            auto q=chassisOrientation(heading,pitch,roll);
            for(int i=0;i<4;++i){auto c=wheelContact(i,chassis,q,steer,height,false,dimensions);travel[i]=c.requested;
                float rate=std::clamp((travel[i]-previousTravel[i])/h,-5.f,5.f);previousTravel[i]=travel[i];
                grounded[i]=travel[i]>=dimensions.droop;
                float span=dimensions.bump-dimensions.droop;
                float endSpan=span*(.15f/(buggyDimensions.bump-buggyDimensions.droop));
                float endZone=std::clamp((travel[i]-(dimensions.bump-endSpan))/endSpan,0.f,1.f);
                float damping=(rate>=0?compressionDamping:reboundDamping)*(1+2*endZone*endZone);
                float stop=std::max(0.f,travel[i]-(dimensions.bump-span*(.045f/(buggyDimensions.bump-buggyDimensions.droop))));
                forces[i]=grounded[i]?mass*gravity*.25f+springRate*(travel[i]-dimensions.staticTravel)+damping*rate+180000*stop*stop:0;
            }
            // An axle's anti-roll bar transfers load only while both tyres touch.
            for(int axle=0;axle<2;++axle){int l=2*axle,r=l+1;if(grounded[l]&&grounded[r]){
                float transfer=antiRollRate*(travel[r]-travel[l]);forces[l]-=transfer;forces[r]+=transfer;}}
            float fy=-mass*gravity,tx=-mass*cgHeight*std::clamp(acceleration,-20.f,15.f),tz=mass*cgHeight*std::clamp(lateralAcceleration,-18.f,18.f);
            for(int i=0;i<4;++i){forces[i]=std::clamp(forces[i],0.f,20000.f);
                // Pitch/roll are chassis axes: yaw must not rotate their torques.
                auto lever=hubAtTravel(i,std::clamp(travel[i],dimensions.droop,dimensions.bump),dimensions);lever.y-=cgHeight;
                lever.applyQuaternion(chassisOrientation(0,pitch,roll));
                fy+=forces[i];tx-=lever.z*forces[i];tz+=lever.x*forces[i];}
            heaveVelocity+=fy/mass*h;chassis.y+=heaveVelocity*h;
            pitchVelocity+=(tx-120*pitchVelocity)/pitchInertia*h;rollVelocity+=(tz-100*rollVelocity)/rollInertia*h;
            pitch+=pitchVelocity*h;roll+=rollVelocity*h;
            if(std::abs(pitch)>.65f){pitch=std::clamp(pitch,-.65f,.65f);pitchVelocity=0;}
            if(std::abs(roll)>.70f){roll=std::clamp(roll,-.70f,.70f);rollVelocity=0;}
            // Hard bump limit prevents ground penetration without forcing droop
            // tyres back onto the terrain. Droop is free to lose contact.
            q=chassisOrientation(heading,pitch,roll);float lift=0;
            float up=Vector3(0,1,0).applyQuaternion(q).y;
            for(int i=0;i<4;++i){auto c=wheelContact(i,chassis,q,steer,height,false,dimensions);lift=std::max(lift,(c.requested-dimensions.bump)*up);}
            if(lift>0){chassis.y+=lift+.0001f;heaveVelocity=std::max(0.f,heaveVelocity);++bumpCorrections;}
        }
    }
};
}
