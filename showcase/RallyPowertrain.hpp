#pragma once
#include <algorithm>
#include <cmath>

namespace rally {
// Cosmetic automatic gearbox drives both the instruments and exhaust. Motion
// remains the explicitly documented arcade model in rally.cpp.
struct Powertrain {
    int gear=1;
    float rpm=1050, load=0, shift=0;
    void update(float speed,float throttle,float dt,bool stopped) {
        const float v=std::abs(speed);
        const int old=gear;
        if(gear<4 && v>(gear==1?8.5f:gear==2?15.f:23.f))++gear;
        if(gear>1 && v<(gear==2?6.3f:gear==3?12.5f:20.f))--gear;
        if(old!=gear)shift=.18f;
        shift=std::max(0.f,shift-dt);
        constexpr float ratios[]={590,350,250,190};
        float target=stopped?1050.f:std::clamp(1050+v*ratios[gear-1]+throttle*240,1050.f,7200.f);
        if(shift>.07f)target*=.82f;
        rpm+=(target-rpm)*(1-std::exp(-9*dt));
        load+=((stopped?0:throttle)-load)*(1-std::exp(-5*dt));
    }
    struct Band {float pitch,gain;};
    Band band(int i,bool silent) const {
        const float a=std::clamp((rpm-1600)/1900.f,0.f,1.f);
        const float b=std::clamp((rpm-3400)/2100.f,0.f,1.f);
        float weight=i==0?std::sqrt(1-a):i==1?std::sqrt(a*(1-b)):std::sqrt(b);
        const float base=i==0?2600.f:i==1?3900.f:5600.f;
        // Avoid the two-octave speed modulo sweep that made the old loop buzz.
        const float pitch=std::clamp(rpm/base,i==0?.48f:.72f,i==0?1.12f:1.3f);
        return {pitch,silent?0.f:weight*(.22f+.3f*load)*(shift>.05f?.45f:1.f)};
    }
};
}
