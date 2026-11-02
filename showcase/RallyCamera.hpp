#pragma once
#include "RallyVehicle.hpp"

namespace rally {
struct CameraModes {
    int view=0,lastExterior=0;bool cut=true;
    explicit CameraModes(int initial=0):view(std::clamp(initial,0,3)),lastExterior(initial<3?view:0){}
    void cycle(){view=(view+1)%4;if(view<3)lastExterior=view;cut=true;}
    void toggleCockpit(){if(view==3)view=lastExterior;else{lastExterior=view;view=3;}cut=true;}
};
inline Vector3 driverEye(){return {-.40f,1.68f,-.30f};}
struct CockpitPose {Vector3 eye,target,up;};
inline CockpitPose cockpitPose(const Vector3& chassis,const Quaternion& q){
    auto eye=driverEye().applyQuaternion(q).add(chassis);
    auto direction=Vector3(0,-.025f,1).applyQuaternion(q).normalize();
    auto bodyUp=Vector3(0,1,0).applyQuaternion(q);
    // Head position stays in the seat. Partial roll stabilization and a fixed
    // field of view avoid extra head shake or speed-dependent zoom.
    return {eye,eye.clone().addScaledVector(direction,12),Vector3(0,1,0).lerp(bodyUp,.30f).normalize()};
}
}
