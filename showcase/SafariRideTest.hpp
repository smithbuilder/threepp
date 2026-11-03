#pragma once
#include "RallySafariRide.hpp"
#include <iostream>
#include <random>
#include <stdexcept>

namespace rally {
inline float safariKineticEnergy(const SafariRideState& s){
    float e=.5f*(s.sprungMass*s.heaveVelocity*s.heaveVelocity+s.pitchInertia*s.pitchVelocity*s.pitchVelocity+s.rollInertia*s.rollVelocity*s.rollVelocity);
    for(float v:s.wheelVelocity)e+=.5f*s.unsprungMass*v*v;return e;
}
inline void safariRideRegressions(){
    auto require=[](bool ok,const char* text){if(!ok)throw std::runtime_error(text);};
    auto validate=[&](const SafariRideState& s){
        require(std::isfinite(s.centerY)&&std::isfinite(s.pitch)&&std::isfinite(s.roll),"Safari vertical state is nonfinite");
        for(int i=0;i<4;++i){require(std::isfinite(s.travel[i])&&s.travel[i]>=s.dimensions.droop-.00003f&&s.travel[i]<=s.dimensions.bump+.00003f,"Safari joint leaves reviewed travel envelope");
            require(std::isfinite(s.forces[i])&&s.forces[i]>=0,"Safari tyre reaction is invalid");}
    };
    auto flat=[](float,float){return 0.f;};SafariRideState settled;settled.reset({},0,flat);
    for(int n=0;n<2160;++n){settled.step({},0,0,0,0,settled.integrationStep,flat);validate(settled);}
    float support=0;for(float f:settled.forces)support+=f;
    require(std::abs(support-(settled.sprungMass+4*settled.unsprungMass)*settled.gravity)<8,"Safari static tyre load differs from total mass");
    require(std::abs(settled.heaveVelocity)<.002f&&std::abs(settled.pitchVelocity)<.002f&&std::abs(settled.rollVelocity)<.002f,"Safari fails to settle on flat ground");
    for(int i=0;i<4;++i)require(settled.contact(i,0,flat).gap>=-settled.maximumTyreCompression-.00008f,"Safari static tyre over-compresses");

    // A separating wheel retains its finite mass. Static-ground impulses must
    // never accelerate the body to the wheel's velocity for free.
    std::mt19937 random(9948);std::uniform_real_distribution<float> velocity(-4,4),arm(-1.8f,1.8f);
    float maximumEnergyGain=0;
    for(int n=0;n<10000;++n){SafariRideState s;s.heaveVelocity=velocity(random);s.pitchVelocity=velocity(random);s.rollVelocity=velocity(random);for(auto& v:s.wheelVelocity)v=velocity(random);
        const SafariRideState::Jacobian j{1,arm(random),arm(random),-1};const float before=safariKineticEnergy(s),normal=s.normalVelocity(0,j);
        if(normal<0)s.impulse(0,j,-normal/s.inverseMass(j));const float delta=safariKineticEnergy(s)-before;maximumEnergyGain=std::max(maximumEnergyGain,delta);
        require(delta<=.02f,"Safari stationary internal-stop impulse creates kinetic energy");require(s.normalVelocity(0,j)>=-.00001f,"Safari impulse leaves closing velocity");
    }
    SafariRideState separating;separating.wheelVelocity[0]=1;
    const SafariRideState::Jacobian stop{1,0,0,-1};const float initial=safariKineticEnergy(separating);
    separating.impulse(0,stop,-separating.normalVelocity(0,stop)/separating.inverseMass(stop));
    require(separating.heaveVelocity<.05f&&safariKineticEnergy(separating)<=initial,"Separating finite wheel was treated as infinite-mass ground");

    // Prescribed driver inputs have no new body moment without ground load.
    auto a=settled;a.lift(2);auto b=a;
    for(int n=0;n<18;++n){a.step({},0,.2f,12,18,a.integrationStep,flat);b.step({},0,.2f,0,0,b.integrationStep,flat);
        require(std::abs(a.pitch-b.pitch)<.000001f&&std::abs(a.roll-b.roll)<.000001f,"Unsupported Safari receives a driver body moment");
        for(float f:a.forces)require(f==0,"Airborne Safari retains tyre normal force");}

    auto coarse=settled,fine=settled;
    for(int n=0;n<90;++n)coarse.step({},0,.1f,4,3,1.f/30,flat);
    for(int n=0;n<360;++n)fine.step({},0,.1f,4,3,1.f/120,flat);
    require(coarse.chassis.distanceTo(fine.chassis)<.0002f&&std::abs(coarse.pitch-fine.pitch)<.0002f&&std::abs(coarse.roll-fine.roll)<.0002f,"Safari ride changes with render cadence on identical inputs");

    for(const float slope:{0.f,.10f,-.16f}){
        auto ground=[&](float x,float z){return slope*x+.07f*z;};SafariRideState s;s.reset({},.5f,ground);
        for(int n=0;n<2160;++n)s.step({},.5f,0,0,0,s.integrationStep,ground);
        const float rest=s.centerY;s.lift(1);const float release=s.centerY;float highest=release;
        for(int n=0;n<2880;++n){s.step({},.5f,0,0,0,s.integrationStep,ground);highest=std::max(highest,s.centerY);validate(s);
            for(int i=0;i<4;++i)require(s.contact(i,0,ground).gap>=-s.maximumTyreCompression-.00015f,"Safari landing exceeds tyre-compression guard");}
        require(highest<=release+.01f,"Safari static-ground landing exceeds its release height");
        require(std::abs(s.centerY-rest)<.006f&&safariKineticEnergy(s)<.05f,"Safari drop fails to dissipate and settle on flat/inclined ground");
    }
    for(float rate=-5;rate<=5;rate+=.025f)require(SafariRideState::damping(rate)*rate>=0,"Safari damper adds energy");
    std::cout<<"PASS: Safari seven-DOF static support, finite-wheel/passive impulses10000, unsupported moments, render cadence, flat/inclined1m drops, tyre-compression/travel and damper power; max impulse energy gain="<<maximumEnergyGain<<"J. No graphics/audio context.\n";
}
}
