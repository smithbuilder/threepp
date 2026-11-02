#pragma once
#include "threepp/threepp.hpp"
#include <array>
#include <algorithm>
#include <cmath>

namespace rally {
using namespace threepp;
inline constexpr float tyreRadius=.54f,tyreHalfWidth=.23f,halfTrack=1.5f,halfWheelbase=1.35f;
// Existing arcade circle approximation, now sized to the transverse stance.
inline constexpr float obstacleFootprint=halfTrack+tyreHalfWidth;
inline constexpr float droop=.16f,bump=.68f;
inline Vector3 wheelAnchor(int i){return {(i%2?1.f:-1.f)*halfTrack,0,i<2?halfWheelbase:-halfWheelbase};}
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
    const auto anchor=wheelAnchor(i);auto offset=anchor.clone().applyQuaternion(q);
    auto up=Vector3(0,1,0).applyQuaternion(q);
    Quaternion steering;steering.setFromAxisAngle(Vector3(0,1,0),i<2?steer:0);
    auto axle=Vector3(1,0,0).applyQuaternion(steering).applyQuaternion(q);
    const float support=tyreRadius*std::sqrt(std::max(0.f,1-axle.y*axle.y))+tyreHalfWidth*std::abs(axle.y);
    float travel=.41f;Vector3 world;
    for(int pass=0;pass<3;++pass){world=chassis.clone().add(offset).addScaledVector(up,travel);
        travel=(height(world.x,world.z)+support-chassis.y-offset.y)/std::max(.6f,up.y);}
    WheelContact result;result.requested=travel;
    result.local=anchor;result.local.y=clampTravel?std::clamp(travel,droop,bump):travel;
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
inline std::vector<SuspensionLink> addSuspension(Group& body){
    auto dark=MeshStandardMaterial::create();dark->color=Color(0x252c2c);dark->metalness=.65f;dark->roughness=.4f;
    auto bright=MeshStandardMaterial::create();bright->color=Color(0xb1b5ae);bright->metalness=.75f;bright->roughness=.32f;
    std::vector<SuspensionLink> links;
    for(int i=0;i<4;++i){auto a=wheelAnchor(i);float side=i%2?1.f:-1.f;
        for(float z:{-.22f,.22f})for(int upper=0;upper<2;++upper){auto mesh=Mesh::create(CylinderGeometry::create(.025f,.025f,1,8),dark);
            body.add(mesh);links.push_back({mesh,{side*.82f,upper?.89f:.43f,a.z+z},i,upper?.14f:-.05f});}
        auto shock=Mesh::create(CylinderGeometry::create(.055f,.055f,1,10),bright);body.add(shock);
        links.push_back({shock,{side*.96f,1.08f,a.z-.13f},i,0});
    }return links;
}
inline void updateSuspension(std::vector<SuspensionLink>& links,const std::array<WheelContact,4>& wheels){
    for(auto& link:links){auto hub=wheels[link.wheel].local;hub.x+=(link.wheel%2?-1.f:1.f)*.20f;hub.y+=link.height;fitLink(*link.mesh,link.mount,hub);}
}
}
