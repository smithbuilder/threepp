#pragma once
#include <array>
#include <algorithm>
#include <cmath>

namespace playground {
enum class HydraulicMode { Cruise=0, FrontHop=1, ThreeWheelLeft=2, ThreeWheelRight=3, Raised=4 };
inline constexpr std::array<const char*,5> hydraulicModeNames{
    "Cruise low","Front hop","Three wheel - left up","Three wheel - right up","Raised ride"};

// Four hydraulic spring seats, fed by isolated front/rear axle circuits.
// Extension is wheel-rate-equivalent spring preload, not wheel position.
// The authored actuator linkage uses a 0.42 cylinder/wheel motion ratio.
// A fast pressure charge stores spring energy; a dump valve releases it.
// The shared chassis solver owns all resulting lift, pitch, flight and landing.
struct CatrinaHydraulics {
    HydraulicMode mode=HydraulicMode::Cruise,previousMode=HydraulicMode::Cruise;
    std::array<float,4> extension{};
    std::array<float,4> cylinderStroke{};
    float phase=0;
    bool pumping=false,speedInterlock=false;
    static constexpr float maximumExtension=.58f,maximumSpeed=6.f;
    void step(bool enabled,float speed,float dt){
        if(mode!=previousMode){phase=0;previousMode=mode;}
        speedInterlock=enabled&&std::abs(speed)>maximumSpeed;
        std::array<float,4> target{};float raiseRate=.30f,lowerRate=.45f;
        if(enabled&&!speedInterlock){
            switch(mode){
                case HydraulicMode::FrontHop:{
                    // Rest, charge, hold briefly, dump and allow the chassis
                    // to land. This commands valves; it never prescribes pose.
                    phase=std::fmod(phase+dt,1.85f);
                    if(phase>.32f&&phase<.66f)target[0]=target[1]=.50f;
                    raiseRate=4.6f;lowerRate=2.6f;break;
                }
                case HydraulicMode::ThreeWheelLeft: target[2]=maximumExtension;break;
                case HydraulicMode::ThreeWheelRight: target[3]=maximumExtension;break;
                case HydraulicMode::Raised: target.fill(.16f);break;
                default: break;
            }
        }
        pumping=false;
        for(int i=0;i<4;++i){const float difference=target[i]-extension[i];
            const float change=std::clamp(difference,-lowerRate*dt,raiseRate*dt);
            extension[i]=std::clamp(extension[i]+change,0.f,maximumExtension);
            cylinderStroke[i]=extension[i]*.42f;
            pumping=pumping||change>.00001f;
        }
    }
};
}
