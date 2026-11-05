#pragma once
#include "RallyPowertrain.hpp"
#include "RallySafariPowertrain.hpp"
#include "RallyVehicle.hpp"
#include <iostream>
#include <stdexcept>

namespace safari_powertrain_test {
inline void run(){
    auto check=[](bool x,const char* msg){if(!x)throw std::runtime_error(msg);};
    check(rally::SafariPowertrain::tyreRadius==rally::safariDimensions.tyreRadius,"Safari audio gearing uses wrong tyre radius");
    rally::SafariPowertrain cruise;
    rally::Powertrain previous;
    for(int i=0;i<900;++i){cruise.update(13.5f,.30f,1.f/30,false);previous.update(13.5f,.30f,1.f/30,false);}
    check(cruise.gear==2&&cruise.rpm>2600&&cruise.rpm<2800,"Safari cruise must not sound like sustained high RPM");
    check(previous.rpm>5700,"Original buggy powertrain response changed");
    const float cruiseRpm=cruise.rpm;
    int gearChanges=0,oldGear=cruise.gear;
    for(int i=0;i<600;++i){cruise.update(i%2?13.49f:13.51f,i%3?0.f:1.f,1.f/30,false);gearChanges+=cruise.gear!=oldGear;oldGear=cruise.gear;}
    check(gearChanges==0,"Cruise control pulses cause Safari gearbox hunting");
    for(float hz:{30.f,60.f,120.f}){
        rally::SafariPowertrain p;
        for(int i=0;i<int(hz*10);++i)p.update(13.5f,.30f,1/hz,false);
        check(p.gear==2&&std::abs(p.rpm-cruiseRpm)<.02f,"Safari settled RPM depends on render cadence");
        for(int i=0;i<int(hz*5);++i)p.update(0,0,1/hz,true);
        check(p.gear==1&&std::abs(p.rpm-980)<.02f&&p.load<.0001f,"Safari idle does not settle");
    }
    for(float rpm=800;rpm<=7200;rpm+=10)for(float load:{0.f,.3f,1.f})for(float shift:{0.f,.06f,.12f,.18f,.24f}){
        cruise.rpm=rpm;cruise.load=load;cruise.shift=shift;float squared=0;
        for(int i=0;i<3;++i){auto b=cruise.band(i,false);check(std::isfinite(b.pitch)&&std::isfinite(b.gain)&&b.pitch>0&&b.gain>=0&&b.gain<=.761f,"Safari audio controls are nonfinite or unbounded");check(cruise.band(i,true).gain==0,"Safari exhaust mute failed");squared+=b.gain*b.gain;}
        check(squared<=.578f,"Safari equal-power band energy bound exceeded");
    }
    cruise.rpm=2800;cruise.shift=0;cruise.load=0;const float coast=cruise.band(1,false).gain;
    cruise.load=1;check(cruise.band(1,false).gain>2.5f*coast,"Safari loaded exhaust has insufficient presence change");
    std::cout<<"PASS: Safari audio physical-radius gearing (49km/h~2670RPM), no cruise hunting, settled30/60/120Hz, idle/mute/load/shift and bounded band-energy checks. Recorded source/subjective output remain separate.\n";
}
}
