#pragma once
#include <array>
#include <algorithm>
#include <vector>
#include <cmath>

// Engine-independent, metre-scale layout shared by rendering and collision.
namespace city {
// Aligned to the brightest patch in the packaged 48-degree photographic sky.
inline constexpr std::array<float,3> sunDirection{-.6331052f,.7430080f,-.2170646f};
inline constexpr float skyRotation=3.4095478f;
struct Building {float x,z,w,d,h;int finish;const char* name;};
inline constexpr std::array<Building,11> buildings{{
    {-13,49,18,18,14.4f,0,"CORNER / COFFEE"},
    {-13,71,18,22,20.8f,1,"MERCER / LOFTS"},
    {-13,94,18,16,11.2f,2,"NORTH / SUPPLY"},
    {14,52,16,24,10.8f,2,"CINDER / MOTOR WORKS"},
    {14,84,16,36,17.6f,0,"BAY / WAREHOUSE"},
    {-55,49,17,24,18,1,"WEST / STUDIOS"},
    {-55,85,17,38,25,0,"MERCER / HOUSE"},
    {55,52,17,30,21,1,"EAST / HOUSE"},
    {55,93,17,28,14,2,"DOCK / STORAGE"},
    {-16,142,38,24,23,0,"NORTH / MILL"},
    {32,145,28,30,31,1,"THE / EXCHANGE"}
}};
using Solid=std::array<float,6>; // centre XYZ, half extents XYZ
inline std::vector<Solid> solids(){
    std::vector<Solid> out;
    for(const auto& b:buildings)out.push_back({b.x,.16f+b.h*.5f,b.z,b.w*.5f,b.h*.5f,b.d*.5f});
    // Visible low perimeter planters also bound the finite test world.
    out.insert(out.end(),{{-65,1,85,.5f,1,109},{65,1,85,.5f,1,109},
                         {0,1,-23,65,1,.5f},{0,1,195,65,1,.5f}});
    return out;
}
inline float surface(float x,float z){
    // Half-metre bevels are represented by the same sampled triangle mesh.
    auto edge=[](float v,float lo,float hi){return std::clamp(std::min(v-lo,hi-v)*2,0.f,1.f);};
    float raised=std::max({edge(x,-25,25)*edge(z,35,105),edge(x,-66,-43)*edge(z,35,105),
        edge(x,43,66)*edge(z,35,105),edge(x,-66,66)*edge(z,123,196),edge(x,-66,66)*edge(z,-24,17)});
    return raised*.16f;
}
// Fixed afternoon sun, baked at static vertices. This supplies long building
// shadows without expanding the single vehicle-local shadow map or adding a pass.
inline float shade(float x,float y,float z){
    for(const auto& b:buildings){
        float near=.03f,far=100;
        auto slab=[&](float p,float d,float lo,float hi){float a=(lo-p)/d,c=(hi-p)/d;if(a>c)std::swap(a,c);near=std::max(near,a);far=std::min(far,c);};
        slab(x,sunDirection[0]/sunDirection[1],b.x-b.w*.5f,b.x+b.w*.5f);
        slab(y,1,.16f,b.h+.16f);slab(z,sunDirection[2]/sunDirection[1],b.z-b.d*.5f,b.z+b.d*.5f);
        if(far>=near)return .52f;
    }
    float result=1;
    if(y<.3f){
        auto treeShadow=[&](float tx,float tz){
            float r=std::hypot((x-tx+4.7f*sunDirection[0]/sunDirection[1])/1.15f,z-tz+4.7f*sunDirection[2]/sunDirection[1]);
            result=std::min(result,.72f+.28f*std::clamp((r-1.2f)/1.8f,0.f,1.f));
            float contact=std::hypot(x-tx,z-tz);result=std::min(result,.78f+.22f*std::clamp(contact/1.2f,0.f,1.f));};
        for(float tx:{-23.7f,23.7f,-44.7f,44.7f})for(int i=0;i<4;++i)treeShadow(tx,42+i*18);
        for(float tx:{-20.f,20.f}){treeShadow(tx,36.8f);treeShadow(tx,103.2f);}
    }
    return result;
}
inline constexpr std::array<std::array<float,2>,8> route{{
    {-33,42},{-33,99},{-24,114},{24,114},{33,99},{33,42},{24,26},{-24,26}
}};
struct Controls {float gas,brake,turn;};
inline Controls tour(float x,float z,float yaw,float speed,float targetSpeed,int& waypoint){
    auto goal=route[waypoint];
    if(std::hypot(goal[0]-x,goal[1]-z)<5){waypoint=(waypoint+1)%route.size();goal=route[waypoint];}
    float error=std::remainder(std::atan2(goal[0]-x,goal[1]-z)-yaw,6.2831853f);
    float desired=std::min(targetSpeed,std::abs(error)>.3f?2.5f:5.f);
    return {std::clamp((desired-speed)*.5f,0.f,.6f),std::clamp((speed-desired)*.5f,0.f,1.f),std::clamp(error*1.7f,-1.f,1.f)};
}
}
