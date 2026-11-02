#pragma once
#include "threepp/threepp.hpp"
#include <array>
#include <algorithm>
#include <cmath>

namespace rally {
using namespace threepp;
inline constexpr float tyreRadius=.54f,tyreHalfWidth=.20f,halfTrack=1.5f,halfWheelbase=1.35f;
// Existing arcade circle approximation, now sized to the transverse stance.
inline constexpr float obstacleFootprint=halfTrack+tyreHalfWidth;
inline constexpr float droop=.16f,bump=.68f;
inline Vector3 wheelAnchor(int i){return {(i%2?1.f:-1.f)*halfTrack,0,i<2?halfWheelbase:-halfWheelbase};}
// This model faces +Z; a driver's right turn is negative mathematical yaw.
inline float steerInput(bool left,bool right){return (left?1.f:0.f)-(right?1.f:0.f);}
inline constexpr float armPivotX=.80f,armPivotY=.36f,lowerBallOffset=-.10f,uprightHeight=.36f;
inline constexpr float armLength=.50249378f;
inline Vector3 hubAtTravel(int i,float travel){
    const float dy=std::clamp(travel,droop,bump)+lowerBallOffset-armPivotY;
    auto hub=wheelAnchor(i);hub.x=(i%2?1.f:-1.f)*(armPivotX+std::sqrt(std::max(0.f,armLength*armLength-dy*dy))+.20f);hub.y=travel;return hub;
}
inline float steeringAngle(int i,float central){
    if(i>1||std::abs(central)<.0001f)return 0;
    const float radius=2*halfWheelbase/std::tan(std::abs(central));
    const bool inner=(central>0)==(i%2==1);
    return std::copysign(std::atan2(2*halfWheelbase,radius+(inner?-halfTrack:halfTrack)),central);
}
inline Quaternion chassisOrientation(float heading,float pitch,float roll){
    Quaternion q;q.setFromAxisAngle(Vector3(0,1,0),heading);
    Quaternion body;body.setFromEuler(Euler(pitch,0,roll));return q.multiply(body);
}
struct RoadPose {float ride,pitch,roll;};
template<class Height>
inline RoadPose roadPose(const Vector3& position,float heading,Height height){
    Vector3 f(std::sin(heading),0,std::cos(heading)),r(std::cos(heading),0,-std::sin(heading));std::array<float,4> h;
    for(int i=0;i<4;++i){auto p=wheelAnchor(i);h[i]=height(position.x+r.x*p.x+f.x*p.z,position.z+r.z*p.x+f.z*p.z);}
    return {(h[0]+h[1]+h[2]+h[3])*.25f+.13f,-std::atan2((h[0]+h[1]-h[2]-h[3])*.5f,2*halfWheelbase),std::atan2((h[1]+h[3]-h[0]-h[2])*.5f,2*halfTrack)};
}
struct WheelContact {Vector3 local,world,ground;float requested=0,gap=0;};
template<class Height>
inline WheelContact wheelContact(int i,const Vector3& chassis,const Quaternion& q,float steer,Height height,bool clampTravel=true){
    auto offset=wheelAnchor(i).applyQuaternion(q);
    auto up=Vector3(0,1,0).applyQuaternion(q);
    Quaternion steering;steering.setFromAxisAngle(Vector3(0,1,0),steeringAngle(i,steer));
    auto axle=Vector3(1,0,0).applyQuaternion(steering).applyQuaternion(q);
    const float support=tyreRadius*std::sqrt(std::max(0.f,1-axle.y*axle.y))+tyreHalfWidth*std::abs(axle.y);
    float travel=.41f;Vector3 world;
    for(int pass=0;pass<4;++pass){auto hub=hubAtTravel(i,travel);hub.y=0;offset=hub.applyQuaternion(q);world=chassis.clone().add(offset).addScaledVector(up,travel);
        travel=(height(world.x,world.z)+support-chassis.y-offset.y)/std::max(.6f,up.y);}
    WheelContact result;result.requested=travel;
    result.local=hubAtTravel(i,clampTravel?std::clamp(travel,droop,bump):travel);
    result.world=chassis.clone().add(result.local.clone().applyQuaternion(q));
    result.ground={result.world.x,height(result.world.x,result.world.z),result.world.z};
    result.gap=result.world.y-support-result.ground.y;return result;
}
// Enforce available travel in the chassis's tilted coordinate frame. Feed-forward
// terrain following supplies the spring target; this catches its residual lag.
template<class Height>
inline void constrainRide(Vector3& chassis,const Quaternion& q,float steer,Height height){
    const float up=Vector3(0,1,0).applyQuaternion(q).y;
    for(int pass=0;pass<2;++pass){float lo=-1e6f,hi=1e6f;
        for(int i=0;i<4;++i){auto c=wheelContact(i,chassis,q,steer,height,false);
            lo=std::max(lo,chassis.y+(c.requested-bump)*up);
            hi=std::min(hi,chassis.y+(c.requested-droop)*up);}
        chassis.y=lo<=hi?std::clamp(chassis.y,lo+.0001f,hi+.0001f):(lo+hi)*.5f;
    }
}
struct SuspensionLink {std::shared_ptr<Mesh> mesh;Vector3 mount;int wheel;float height;};
inline void fitLink(Mesh& mesh,const Vector3& a,const Vector3& b){auto d=b.clone().sub(a);float length=d.length();
    mesh.position.copy(a).add(b).multiplyScalar(.5f);mesh.quaternion.setFromUnitVectors(Vector3(0,1,0),d.multiplyScalar(1/std::max(.001f,length)));mesh.scale.y=length;}
}
