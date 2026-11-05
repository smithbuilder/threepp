#pragma once
#include "RallyVehicle.hpp"

namespace rally {
inline constexpr VehicleDimensions bajaDimensions{.47f,.187f,1.025f,1.59f,.268f,.52f,.68f,.40f};
struct BajaFrontPose{Vector3 lower,upper,hub;float camber;};
inline BajaFrontPose bajaFrontPose(float target,int side){
    constexpr float lowerLength2=.29f*.29f+.04f*.04f,upperLength2=.27f*.27f+.06f*.06f,uprightLength=.15f;
    auto evaluate=[&](float y){
        Vector3 low(.68f+std::sqrt(std::max(.00001f,lowerLength2-(y-.27f)*(y-.27f))),y,0),anchor(.70f,.40f,0);
        auto delta=low.clone().sub(anchor);const float d=delta.length();delta.multiplyScalar(1/d);
        const float a=(upperLength2-uprightLength*uprightLength+d*d)/(2*d),h=std::sqrt(std::max(0.f,upperLength2-a*a));
        auto base=anchor.addScaledVector(delta,a);Vector3 perp(-delta.y,delta.x,0);
        const auto p=base.clone().addScaledVector(perp,h),q=base.clone().addScaledVector(perp,-h);
        auto upper=p.y>=q.y?p:q; // The physical branch keeps upper above lower.
        const float angle=-std::atan2(upper.x-low.x,upper.y-low.y);
        Vector3 hub(low.x+.055f*std::cos(angle)-.09f*std::sin(angle),low.y+.055f*std::sin(angle)+.09f*std::cos(angle),0);
        return BajaFrontPose{low,upper,hub,angle};
    };
    float y=std::clamp(target-.09f,.12f,.45f);
    for(int n=0;n<6;++n){auto p=evaluate(y);const float derivative=(evaluate(y+.0001f).hub.y-p.hub.y)/.0001f;y=std::clamp(y+(target-p.hub.y)/std::max(.2f,derivative),.12f,.45f);}
    auto p=evaluate(y);for(auto* v:{&p.lower,&p.upper,&p.hub}){v->x*=side;v->z=1.59f;}p.camber*=side;return p;
}
inline Vector3 bajaHubAtTravel(int i,float travel,const VehicleDimensions& =bajaDimensions){
    return i<2?bajaFrontPose(travel,i%2?1:-1).hub:Vector3(i%2?1.025f:-1.025f,travel,-1.59f);
}
struct BajaAxlePose{Vector3 center;float roll;};
inline BajaAxlePose bajaAxlePose(float left,float right){
    const float roll=std::asin(std::clamp((right-left)/2.05f,-.25f,.25f)),c=std::cos(roll),s=std::sin(roll),y=(left+right)*.5f;
    // Panhard lateral arc. Four parallel trailing links set the fore/aft arc;
    // their residual articulation is absorbed by the modelled rubber bushes.
    constexpr float panLength2=1.48f*1.48f+.15f*.15f;
    const float panY=y+.76f*s+.03f*c,panOffset=.76f*c-.03f*s;
    const float x=-.72f+std::sqrt(std::max(.1f,panLength2-(panY-.58f)*(panY-.58f)))-panOffset;
    constexpr float rodLength2=.13f*.13f+.01f*.01f+.87f*.87f;
    float z=0;
    for(int sign:{-1,1})for(float yy:{-.09f,.09f}){
        const float dx=x+sign*.77f*c-yy*s-sign*.64f;
        const float dy=y+sign*.77f*s+yy*c-(yy>0?.48f:.30f);
        z+=-.72f-std::sqrt(std::max(.1f,rodLength2-dx*dx-dy*dy));
    }return {{x,y,z*.25f},roll};
}
}
