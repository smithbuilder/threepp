#pragma once
#include "RallyVehicle.hpp"
#include "BajaGeometry.hpp"
#include "CatrinaDimensions.hpp"
#include <string>
#include <stdexcept>

namespace playground {
// Add vehicle specifications here. The solver and acceptance suite consume
// every entry; a new mesh/rig needs its own rendering adapter, never a new
// steering or terrain-following controller. All quantities are SI.
enum class VisualRig { Safari, OriginalBuggy, Baja, Catrina };
struct Tune {
    const char* id;const char* name;VisualRig visualRig;
    rally::VehicleDimensions dims;
    float mass,cgY,cgZ,width,height,length,frontRate,rearRate,compression,rebound,grip,driveForce;
    float pitchInertia,yawInertia,rollInertia,hullBottom,noseRise,tailRise;
    bool straightWheelPath=false;
    float frontalCdA=.75f,lateralCdA=3.4f,verticalCdA=2.f,pressureY=.18f,pressureZ=0;
    // Optional axle-specific damping and travel. Existing tunes retain their values.
    float rearCompression=0,rearRebound=0,rearDroop=0,rearBump=0;
    float rearHalfTrack=0;
    bool rearWheelDrive=false;
    float hullOffsetZ=0;
    float hullFriction=.65f;
};
// Engineering estimates for these authored vehicles, not measured production-car data.
inline constexpr std::array<Tune,4> tunes{{
    {"safari","Safari",VisualRig::Safari,rally::safariDimensions,
        1072,.68f,-.25f,1.55f,.65f,3.50f,22500,31500,2100,3500,.88f,6200,
        1800,1900,700,.24f,.30f,.30f,false},
    {"buggy","Original buggy",VisualRig::OriginalBuggy,rally::buggyDimensions,
        780,.90f,0,1.45f,1.15f,2.75f,12000,14000,1400,2300,.90f,5100,
        1050,1150,650,.50f,.30f,.30f,false,.95f,2.6f,1.7f,.20f,0},
    {"baja","Baja 427",VisualRig::Baja,rally::bajaDimensions,
        2480,.75f,.1272f,1.72f,1.05f,4.25f,52762.9f,51138.8f,3359,5598,.92f,13400,
        5300,5600,2000,.20f,.55f,.30f,true,1.30f,4.7f,2.8f,.25f,-.15f},
    {"catrina","La Catrina",VisualRig::Catrina,rally::catrinaDimensions,
        1850,.62f,-.18f,2.02f,.65f,5.33f,42000,36000,2400,3700,.95f,8800,
        4100,4500,950,.19f,.20f,.18f,true,.92f,3.6f,2.1f,.19f,-.10f,
        2200,3300,.15f,.42f,rally::catrinaRearHalfTrack,true,-.19f,.30f}
}};
inline int vehicleIndex(const std::string& id){for(size_t i=0;i<tunes.size();++i)if(id==tunes[i].id)return static_cast<int>(i);throw std::runtime_error("Unknown playground vehicle: "+id);}
}
