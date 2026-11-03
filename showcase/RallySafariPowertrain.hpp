#pragma once
#include "RallyPowertrain.hpp"
#include <algorithm>
#include <cmath>

namespace rally {
// Safari-only presentation gearbox and recorded exhaust voice. This computes
// instrument/audio state, not a longitudinal engine/tyre force simulation.
// The tyre radius matches safariDimensions; ratios are original tuning values,
// not a claim about any production 911's transmission or this recording's RPM.
struct SafariPowertrain {
    int gear=1;
    float rpm=980.f,load=0,shift=0;
    float shiftCooldown=0;
    static constexpr float tyreRadius=.49f,finalDrive=4.7f,shiftDuration=.24f;
    static constexpr float ratios[5]={3.60f,2.15f,1.48f,1.12f,.89f};
    static constexpr float recordedBandRpm[3]={1050.f,2800.f,4800.f};

    void update(float speed,float throttle,float dt,bool stopped) {
        dt=std::clamp(dt,0.f,.1f);
        throttle=stopped?0.f:std::clamp(throttle,0.f,1.f);
        load+=(throttle-load)*(1-std::exp(-(throttle>load?8.f:4.5f)*dt));
        shift=std::max(0.f,shift-dt);
        shiftCooldown=std::max(0.f,shiftCooldown-dt);
        const float wheelRpm=std::abs(speed)*60.f/(6.28318530718f*tyreRadius);
        float coupled=wheelRpm*ratios[gear-1]*finalDrive;
        if(!stopped&&shiftCooldown==0){
            const int old=gear;
            if(gear<5&&coupled>3300.f+1200.f*load)++gear;
            else if(gear>1&&coupled<1450.f+500.f*load)--gear;
            if(old!=gear){shift=shiftDuration;shiftCooldown=.55f;}
            coupled=wheelRpm*ratios[gear-1]*finalDrive;
        }
        if(stopped&&std::abs(speed)<.5f)gear=1;
        // A little clutch slip permits a loaded launch; road speed drives cruise
        // RPM directly. Do not add idle RPM onto wheel-coupled RPM as the old
        // cosmetic gearbox did: it made 49 km/h sound like a sustained redline.
        const float launch=980.f+950.f*load*std::clamp(1-std::abs(speed)/8.f,0.f,1.f);
        const float target=stopped?980.f:std::clamp(std::max(launch,coupled*(1+.018f*load)),980.f,6600.f);
        rpm+=(target-rpm)*(1-std::exp(-(target>rpm?8.f:6.f)*dt));
    }
    using Band=Powertrain::Band;
    Band band(int i,bool silent) const {
        auto smooth=[](float x){x=std::clamp(x,0.f,1.f);return x*x*(3-2*x);};
        const float a=smooth((rpm-1300.f)/1300.f),b=smooth((rpm-3300.f)/2100.f);
        const float weight=i==0?std::sqrt(1-a):i==1?std::sqrt(a*(1-b)):std::sqrt(a*b);
        const float lower=i==0?.74f:i==1?.56f:.64f;
        const float upper=i==0?1.58f:i==1?1.45f:1.38f;
        const float pitch=std::clamp(rpm/recordedBandRpm[i],lower,upper);
        // Recorded pressure/texture opens with load. The upper band falls back
        // on lift, retaining low exhaust body rather than a constant bright rev.
        const float character=i==2?.46f+.54f*load:i==1?.90f+.10f*load:1.f;
        const float phase=std::clamp(shift/shiftDuration,0.f,1.f);
        const float shiftDip=1-.28f*std::sin(3.14159265359f*phase);
        return {pitch,silent?0.f:weight*(.28f+.48f*load)*character*shiftDip};
    }
};
}
