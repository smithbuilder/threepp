#pragma once
#include "RallyVehicle.hpp"
#include "BajaGeometry.hpp"
#include <string>
#include <stdexcept>

namespace playground {
// Add vehicle specifications here. The solver and acceptance suite consume
// every entry; a new mesh/rig needs its own rendering adapter, never a new
// steering or terrain-following controller. All quantities are SI.
enum class VisualRig { Safari, OriginalBuggy, Baja };
struct Tune {
    const char* id;const char* name;VisualRig visualRig;
    rally::VehicleDimensions dims;
    float mass,cgY,cgZ,width,height,length,frontRate,rearRate,compression,rebound,grip,driveForce;
    float pitchInertia,yawInertia,rollInertia,hullBottom,noseRise,tailRise;
    bool straightWheelPath=false;
    float frontalCdA=.75f,lateralCdA=3.4f,verticalCdA=2.f,pressureY=.18f,pressureZ=0;
};
// Engineering estimates for these authored vehicles, not measured production-car data.
inline constexpr std::array<Tune,3> tunes{{
    {"safari","Safari",VisualRig::Safari,rally::safariDimensions,
        1072,.68f,-.25f,1.55f,.65f,3.50f,22500,31500,2100,3500,.88f,6200,
        1800,1900,700,.24f,.30f,.30f,false},
    {"buggy","Original buggy",VisualRig::OriginalBuggy,rally::buggyDimensions,
        780,.90f,0,1.45f,1.15f,2.75f,12000,14000,1400,2300,.90f,5100,
        1050,1150,650,.50f,.30f,.30f,false,.95f,2.6f,1.7f,.20f,0},
    {"baja","Baja 427",VisualRig::Baja,rally::bajaDimensions,
        2480,.75f,.1272f,1.72f,1.05f,4.25f,52762.9f,51138.8f,3359,5598,.92f,13400,
        5300,5600,2000,.20f,.55f,.30f,true,1.30f,4.7f,2.8f,.25f,-.15f}
}};
inline int vehicleIndex(const std::string& id){for(size_t i=0;i<tunes.size();++i)if(id==tunes[i].id)return static_cast<int>(i);throw std::runtime_error("Unknown playground vehicle: "+id);}
}
