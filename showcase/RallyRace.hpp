#pragma once
#include "RallyBuggy.hpp"
#include "RallyPowertrain.hpp"
#include "RallyHud.hpp"
#include <limits>

namespace rally {
// Capture staging only. Both cars retain their own motion/ride controllers.
// A small AI catch-up governor keeps the two distinct cars in a useful shot;
// this film is not a handling, acceleration or lap-time benchmark.
template<class Track> Vector3 raceLane(Track track,float a,float offset){
    auto p=track(a),forward=track(a+.001f).sub(p).normalize();
    return p.addScaledVector(Vector3(forward.z,0,-forward.x),offset);
}
template<class D,class Height,class Nearest,class Track>
void stepOriginalRace(D& d,const D& safari,float step,float time,Height height,Nearest nearest,Track track,
        float lane=-2.15f,bool truck=false,float roadEdge=4.2f,bool coastFinish=false){
    if(!truck&&!d.ride.ready)d.ride.reset(d.position,d.heading,height,buggyDimensions,RideContactResponse::Legacy);
    if(d.finished){
        if(coastFinish){const float old=d.velocity;d.previousVelocity=old;d.velocity=std::max(0.f,old-8.f*step);if(old>.0001f)d.motion.multiplyScalar(d.velocity/old);else d.motion.set(0,0,0);d.position.addScaledVector(d.motion,step);d.position.y=height(d.position.x,d.position.z);d.wheelAngle+=d.velocity*step/(truck?.47f:buggyDimensions.tyreRadius);d.braking=d.velocity>.01f?.45f:0;d.throttle=0;if(!truck)d.ride.step(d.position,d.heading,d.steer*.4f,(d.velocity-old)/step,0,step,height);}
        else if(!truck)d.ride.step(d.position,d.heading,d.steer*.4f,0,0,step,height);return;
    }
    const auto near=nearest(d.position);
    const auto aim=raceLane(track,near.a+.105f,lane).sub(d.position);
    float angle=std::remainder(std::atan2(aim.x,aim.z)-d.heading,6.28318530718f);
    const float turn=std::clamp(angle*1.35f,-1.f,1.f);
    d.steer+=(turn-d.steer)*(1-std::exp(-7*step));
    const Vector3 forward(std::sin(d.heading),0,std::cos(d.heading));
    const float gap=safari.position.clone().sub(d.position).dot(forward);
    const float target=13.55f+.65f*std::sin(time*.32f+(truck?1.1f:0.f))+std::clamp(gap*.24f,-1.1f,1.1f);
    const float off=std::hypot(d.position.x-near.p.x,d.position.z-near.p.z);
    const float drag=off>roadEdge?1.25f:.24f;
    const float request=1.8f*(target-d.velocity)+d.velocity*drag+d.velocity*std::abs(d.velocity)*.014f;
    const float acceleration=truck?9.f:12.f;
    d.throttle=std::clamp(request/acceleration,0.f,1.f);d.braking=std::clamp(-request/18.f,0.f,1.f);
    const float old=d.velocity;
    d.velocity+=(d.throttle*acceleration-d.braking*18-d.velocity*drag-d.velocity*std::abs(d.velocity)*.014f)*step;
    const float targetYaw=std::tan(d.steer*.42f)*d.velocity/(truck?3.18f:2.45f);
    d.yawRate+=(targetYaw-d.yawRate)*(1-std::exp(-7*step));d.heading+=d.yawRate*step;
    const Vector3 desired(std::sin(d.heading)*d.velocity,0,std::cos(d.heading)*d.velocity);
    d.motion.lerp(desired,1-std::exp(-(off>roadEdge?3.f:7.f)*step));
    const float oldX=d.position.x;
    d.position.addScaledVector(d.motion,step);d.position.y=height(d.position.x,d.position.z);
    d.previousVelocity=old;
    d.wheelAngle+=d.velocity*step/(truck?.47f:buggyDimensions.tyreRadius);
    if(!truck)d.ride.step(d.position,d.heading,d.steer*.4f,(d.velocity-old)/step,d.velocity*d.yawRate,step,height);
    if(d.velocity>.5f)d.running=true;if(d.running)d.elapsed+=step;
    const auto gate=track(d.next*6.28318530718f/8);
    const bool finish=d.next==0&&d.elapsed>20&&oldX<0&&d.position.x>=0&&std::abs(d.position.z-90)<6;
    if(d.running&&((d.next!=0&&std::hypot(d.position.x-gate.x,d.position.z-gate.z)<7)||finish)){
        if(finish){d.finished=true;d.laps=1;d.lastLap=d.elapsed;if(!coastFinish){d.velocity=0;d.motion.set(0,0,0);}d.throttle=0;}
        d.next=(d.next+1)%8;
    }
}
template<class D,class Height> void poseOriginalRace(Buggy& car,D& d,Height height,std::array<WheelContact,4>& contacts){
    car.car->position.copy(d.ride.chassis);car.car->rotation.y=d.heading;
    car.body->rotation.x=d.ride.pitch;car.body->rotation.z=d.ride.roll;
    for(int i=0;i<4;++i){contacts[i]=d.ride.contact(i,d.heading,d.steer*.4f,height);
        car.pivots[i]->position.copy(contacts[i].local);car.pivots[i]->rotation.y=steeringAngle(i,d.steer*.4f,buggyDimensions);car.rolls[i]->rotation.x=d.wheelAngle;}
    updateSuspension(car.suspension,contacts,d.steer*.4f);
}
inline float raceEnvelopeGap(const Vector3& a,float ah,const Vector3& b,float bh,
        float aw=1.40f,float al=2.55f,float bw=1.80f,float bl=2.10f){
    Vector3 ar(std::cos(ah),0,-std::sin(ah)),af(std::sin(ah),0,std::cos(ah));
    Vector3 br(std::cos(bh),0,-std::sin(bh)),bf(std::sin(bh),0,std::cos(bh));
    const auto delta=b.clone().sub(a);float answer=-1e9f;
    for(const auto& axis:{ar,af,br,bf}){
        const float r=aw*std::abs(ar.dot(axis))+al*std::abs(af.dot(axis))+
                      bw*std::abs(br.dot(axis))+bl*std::abs(bf.dot(axis));
        answer=std::max(answer,std::abs(delta.dot(axis))-r);
    }return answer;
}
template<class D> void drawRaceHud(const D& a,const D& b,float time,float countdown,ImFont* font){
    auto* d=ImGui::GetBackgroundDrawList();
    const ImU32 ivory=IM_COL32(246,244,233,255),gold=IM_COL32(226,193,116,255),quiet=IM_COL32(224,229,219,255);
    auto text=[&](float x,float y,float sz,ImU32 c,const std::string& s){hudText(d,font,x,y,sz,c,s);};
    text(28,22,28,ivory,"SAFARI vs ORIGINAL BUGGY");
    text(28,54,14,quiet,"NATIVE ENGINE / SCRIPTED AI RACE / AUDIO REBUILT");
    text(28,548,18,gold,"SAFARI  "+std::to_string(static_cast<int>(std::abs(a.velocity)*3.6f))+" KM/H");
    text(670,548,18,ivory,"ORIGINAL  "+std::to_string(static_cast<int>(std::abs(b.velocity)*3.6f))+" KM/H");
    text(788,24,24,ivory,raceTime(std::max(0.f,time-3)));
    if(countdown>0)text(461,116,70,ivory,std::to_string(static_cast<int>(std::ceil(countdown))));
    else if(time<4.2f)text(442,122,42,gold,"GO");
    if(a.finished||b.finished){
        const bool safariWins=a.finished&&(!b.finished||a.lastLap<b.lastLap);
        text(300,91,27,gold,safariWins?"SAFARI TAKES THE FLAG":"ORIGINAL TAKES THE FLAG");
        if(a.finished&&b.finished){text(319,123,18,ivory,"SAFARI  "+raceTime(a.lastLap)+"    ORIGINAL  "+raceTime(b.lastLap));}
    }
}
template<class D> void drawThreeRaceHud(const D& a,const D& b,const D& truck,float time,float countdown,ImFont* font){
    auto* d=ImGui::GetBackgroundDrawList();const ImU32 ivory=IM_COL32(246,244,233,255),gold=IM_COL32(226,193,116,255);
    auto text=[&](float x,float y,float sz,ImU32 c,const std::string& s){hudText(d,font,x,y,sz,c,s);};
    text(28,22,27,ivory,"SAFARI / BAJA 427 / ORIGINAL BUGGY");
    text(28,53,14,ivory,"NATIVE ENGINE / SCRIPTED AI RACE / AUDIO REBUILT");
    text(28,548,18,ivory,"SAFARI  "+std::to_string(static_cast<int>(std::abs(a.velocity)*3.6f))+" KM/H");
    text(360,548,18,gold,"BAJA 427  "+std::to_string(static_cast<int>(std::abs(truck.velocity)*3.6f))+" KM/H");
    text(703,548,18,ivory,"ORIGINAL  "+std::to_string(static_cast<int>(std::abs(b.velocity)*3.6f))+" KM/H");
    const bool all=a.finished&&b.finished&&truck.finished;
    text(788,24,24,ivory,raceTime(all?std::max({a.lastLap,b.lastLap,truck.lastLap}):std::max(0.f,time-3)));
    if(countdown>0)text(461,110,70,ivory,std::to_string(static_cast<int>(std::ceil(countdown))));
    else if(time<4.2f)text(442,116,42,gold,"GO");
    if(a.finished||b.finished||truck.finished){
        float best=1e9f;std::string winner;
        for(const auto& pair:{std::pair<const D*,const char*>{&a,"SAFARI"},{&b,"ORIGINAL"},{&truck,"BAJA 427"}})
            if(pair.first->finished&&pair.first->lastLap<best){best=pair.first->lastLap;winner=pair.second;}
        text(330,83,27,gold,winner+" TAKES THE FLAG");
        if(all)text(235,115,17,ivory,"SAFARI "+raceTime(a.lastLap)+"   BAJA "+raceTime(truck.lastLap)+"   ORIGINAL "+raceTime(b.lastLap));
    }
}
}
