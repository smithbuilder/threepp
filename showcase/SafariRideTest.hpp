#pragma once
#include "RallySafariRide.hpp"
#include <iostream>
#include <random>
#include <stdexcept>

namespace rally {
inline float safariKineticEnergy(const SafariRideState& s){
    float e=.5f*(s.sprungMass*s.heaveVelocity*s.heaveVelocity+s.tuning.pitchInertia*s.pitchVelocity*s.pitchVelocity+s.tuning.rollInertia*s.rollVelocity*s.rollVelocity);
    for(float v:s.wheelVelocity)e+=.5f*s.unsprungMass*v*v;return e;
}
struct SafariSingleWheelResponse {
    float wheelCompression=0,bodyHeave=0,bodyPitch=0,bodyRoll=0,damperStroke=0,settlingSeconds=0,unsupportedSeconds=0;
};
inline SafariSingleWheelResponse safariSingleWheelBump(const SafariRideTuning& tuning){
    // Tow the same vehicle over one spatial, rounded70mm bump at6m/s. Stop
    // between axle crossings so only front-left encounters it; all contacts
    // are on flat ground during the subsequent recovery. No longitudinal or
    // lateral body torque is applied in this isolated vertical-response test.
    auto height=[](float x,float z){const float across=(x+1.08f)/.44f,along=(z-3.f)/.75f;
        if(std::abs(across)>=1||std::abs(along)>=1)return 0.f;
        return .070f*.5f*(1+std::cos(3.14159265359f*across))*.5f*(1+std::cos(3.14159265359f*along));};
    SafariRideState state;state.tuning=tuning;state.reset({},0,height);
    for(int n=0;n<2160;++n)state.step({},0,0,0,0,state.integrationStep,height);
    const auto rest=state;SafariSingleWheelResponse result;float minimumLength=100,maximumLength=0;
    auto damperLength=[](float travel){auto hub=hubAtTravel(0,travel,safariDimensions);hub.x+=.20f;hub.y+=lowerBallOffset;
        const auto foot=Vector3(-safariDimensions.armPivotX,armPivotY,safariDimensions.halfWheelbase).lerp(hub,.78f);
        return foot.distanceTo(Vector3(-safariDimensions.armPivotX,.94f,safariDimensions.halfWheelbase));};
    float lastUnsettled=.5f;
    for(int n=0;n<1620;++n){const float time=(n+1)*state.integrationStep,z=std::min(3.f,time*6.f);
        state.step(Vector3(0,0,z),0,0,0,0,state.integrationStep,height);
        result.wheelCompression=std::max(result.wheelCompression,state.travel[0]-rest.travel[0]);
        result.bodyHeave=std::max(result.bodyHeave,std::abs(state.centerY-rest.centerY));
        result.bodyPitch=std::max(result.bodyPitch,std::abs(state.pitch-rest.pitch));result.bodyRoll=std::max(result.bodyRoll,std::abs(state.roll-rest.roll));
        const float length=damperLength(state.travel[0]);minimumLength=std::min(minimumLength,length);maximumLength=std::max(maximumLength,length);
        int grounded=0;bool wheelsQuiet=true;
        for(int i=0;i<4;++i){grounded+=state.grounded[i];wheelsQuiet&=std::abs(state.travel[i]-rest.travel[i])<.004f&&std::abs(state.wheelVelocity[i])<.05f;
            if(!std::isfinite(state.travel[i])||state.travel[i]<state.dimensions.droop-.00003f||state.travel[i]>state.dimensions.bump+.00003f)throw std::runtime_error("Single-wheel bump exceeds reviewed joint travel");
            if(state.contact(i,0,height).gap<-state.maximumTyreCompression-.00015f)throw std::runtime_error("Single-wheel bump exceeds tyre compression guard");}
        if(!grounded)result.unsupportedSeconds+=state.integrationStep;
        const bool quiet=wheelsQuiet&&std::abs(state.centerY-rest.centerY)<.003f&&std::abs(state.pitch-rest.pitch)<.003f&&std::abs(state.roll-rest.roll)<.003f
            &&std::abs(state.heaveVelocity)<.02f&&std::abs(state.pitchVelocity)<.02f&&std::abs(state.rollVelocity)<.02f;
        if(time>=.5f&&!quiet)lastUnsettled=time;
    }
    result.damperStroke=maximumLength-minimumLength;result.settlingSeconds=lastUnsettled-.5f;return result;
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
    for(const auto tune:{SafariRideTuning::previous(),SafariRideTuning{}})for(int n=0;n<10000;++n){SafariRideState s;s.tuning=tune;s.heaveVelocity=velocity(random);s.pitchVelocity=velocity(random);s.rollVelocity=velocity(random);for(auto& v:s.wheelVelocity)v=velocity(random);
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
    for(const auto tune:{SafariRideTuning::previous(),SafariRideTuning{}})for(float rate=-5;rate<=5;rate+=.025f)require(SafariRideState::damping(rate,tune)*rate>=0,"Safari damper adds energy");
    const auto previous=SafariRideTuning::previous(),revised=SafariRideTuning{};
    require(revised.highCompression<revised.lowCompression&&revised.highRebound<revised.lowRebound,"Revised Safari damper is not digressive");
    require(previous.pitchInertia==1800.f&&previous.rollInertia==950.f&&previous.restingTravel==.35f&&previous.frontSpringRate==22500.f&&previous.rearSpringRate==31500.f
        &&previous.damperKnee==.35f&&previous.lowCompression==2100.f&&previous.lowRebound==3200.f&&previous.highCompression==4200.f&&previous.highRebound==6400.f,"Previous Safari tune was not retained exactly");
    SafariRideState preserved;preserved.tuning=previous;preserved.reset({},0,flat);require(preserved.tuning.pitchInertia==1800.f&&preserved.tuning.restingTravel==.35f,"Safari reset lost selected tune");
    const auto oldBump=safariSingleWheelBump(previous),newBump=safariSingleWheelBump(revised);
    auto describe=[](const char* name,const SafariSingleWheelResponse& r){std::cout<<name<<" single-wheel bump: wheelCompression="<<r.wheelCompression<<"m bodyHeave="<<r.bodyHeave<<"m pitch="<<r.bodyPitch<<"rad roll="<<r.bodyRoll<<"rad actualDamperStroke="<<r.damperStroke<<"m settle="<<r.settlingSeconds<<"s unsupported="<<r.unsupportedSeconds<<"s\n";};
    describe("Previous",oldBump);describe("Revised",newBump);
    // More peak travel alone can reward overshoot. Retain the wheel's bump
    // response while transmitting materially less motion to the platform;
    // measure actual shaft/coilover work and a prompt, bounded recovery too.
    // Earlier extra-excursion diagnostics remain archived under build.
    require(newBump.wheelCompression>.025f&&newBump.wheelCompression>=oldBump.wheelCompression*.90f,"Revised Safari suppresses the wheel's single-bump response");
    require(newBump.bodyHeave<=oldBump.bodyHeave*.85f,"Revised Safari does not materially isolate the body from the single-wheel bump");
    require(newBump.damperStroke>.025f,"Revised Safari coilover does not visibly work through the rounded bump");
    require(newBump.settlingSeconds<.6f&&newBump.settlingSeconds<=oldBump.settlingSeconds+.10f,"Revised Safari fails to recover promptly after the rounded bump");
    require(newBump.unsupportedSeconds<.02f,"Single-wheel bump launches the entire revised Safari");
    std::cout<<"PASS: Safari seven-DOF static support, finite-wheel/passive impulses20000 across both tunes, unsupported moments, render cadence, flat/inclined1m drops, tyre-compression/travel, passive digressive damping and matched rounded single-wheel response; max impulse energy gain="<<maximumEnergyGain<<"J. No graphics/audio context.\n";
}
}
