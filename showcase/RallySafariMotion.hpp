#pragma once

#include "RallyVehicle.hpp"
#include <algorithm>
#include <cmath>

namespace rally {
struct SafariCruiseCommand { float throttle=0,brake=0; };
struct SafariTractionCommand {float longitudinal=0,lateral=0,support=0;};

// A bounded arcade friction circle driven by actual previous-step tyre loads.
// Unloaded tyres cannot supply new propulsion or a steering force in mid-air.
inline SafariTractionCommand safariTractionCommand(float longitudinal,float lateral,float normalLoad,float weight){
    if(!std::isfinite(longitudinal)||!std::isfinite(lateral)||!std::isfinite(normalLoad)||
       !std::isfinite(weight)||weight<=0)return {};
    const float support=std::clamp(normalLoad/weight,0.f,1.f);
    const float limit=.9f*9.81f*support,demand=std::hypot(longitudinal,lateral);
    const float scale=demand>0?std::min(1.f,limit/demand):1.f;
    return {longitudinal*scale,lateral*scale,support};
}

// Balance the same drag used by the arcade longitudinal controller, then
// request a smooth acceleration toward the unchanged demonstration speed.
// A full-on/full-off governor injected +/-6 m/s^2 into the sprung-body model
// even at steady cruise, and also made engine load chatter.
inline float safariCoastAcceleration(float speed,bool offRoad,float support=1.f){
    // Gravel rolling resistance plus quadratic aerodynamic loss for this
    // fictional 1072kg coupe. The previous shared arcade drag removed 0.59g
    // at 49km/h, requiring half throttle even on a level road.
    return (offRoad?.075f:.035f)*9.81f*std::tanh(speed/.5f)*std::clamp(support,0.f,1.f)
           +.001f*speed*std::abs(speed);
}
inline SafariCruiseCommand safariCruiseCommand(float speed,bool offRoad){
    if(!std::isfinite(speed))return {0,1};
    constexpr float cruise=13.5f;
    const float drag=safariCoastAcceleration(speed,offRoad);
    const float effort=drag+2.f*(cruise-speed);
    return {std::clamp(effort/12.f,0.f,1.f),std::clamp(-effort/18.f,0.f,1.f)};
}

// Shared by the native controller and CPU closed-loop replay. This remains a
// horizontal arcade bicycle model; it adds contact-limited forces and uses the
// same 2.7m wheelbase/central steering angle as the visible Safari wheels.
inline void safariIntegrateMotion(float& speed,float& yawRate,float& heading,threepp::Vector3& motion,
                                  float centralSteer,float throttle,float brake,bool handbrake,bool offRoad,
                                  float normalLoad,float weight,float dt){
    if(dt<=0||!std::isfinite(dt))return;
    const float support=safariTractionCommand(0,0,normalLoad,weight).support;
    const float grip=.9f*9.81f*support;
    const float yawLimit=grip/std::max(1.f,std::abs(speed));
    const float yaw=std::clamp(std::tan(centralSteer)*speed/(2*safariDimensions.halfWheelbase),-yawLimit,yawLimit);
    yawRate+=(yaw-yawRate)*(1-std::exp(-7*support*dt));
    heading+=yawRate*dt;
    const threepp::Vector3 forward(std::sin(heading),0,std::cos(heading)),right(std::cos(heading),0,-std::sin(heading));
    const float rolling=safariCoastAcceleration(speed,offRoad,support)-.001f*speed*std::abs(speed);
    const float drive=throttle*12-(speed> -6.f?brake*18:0)-(handbrake?speed*1.5f:0)-rolling;
    const float side=-motion.dot(right)*(handbrake?1.5f:offRoad?3.f:7.f);
    const auto traction=safariTractionCommand(drive,side,normalLoad,weight);
    // Apply the bounded acceleration itself. A velocity lerp could bypass the
    // friction circle with >2g of snap alignment after a landing or drift.
    motion.addScaledVector(forward,traction.longitudinal*dt).addScaledVector(right,traction.lateral*dt);
    motion.multiplyScalar(std::exp(-.001f*motion.length()*dt));
    const float length=motion.length();
    if(length>30)motion.multiplyScalar(30/length);
    speed=std::copysign(std::min(length,30.f),motion.dot(forward));
}

// Remain inside the checkpoint posts and below the beam. Keeping the same
// approximate boom length avoids the side view repeatedly zooming into the
// car when the old high/wide camera crossed that checkpoint structure.
inline threepp::Vector3 safariSideCameraOffset(){return {2.2f,2.25f,-5.1f};}
template<class Height>
inline threepp::Vector3 safariSideCameraPosition(const threepp::Vector3& position,const threepp::Vector3& forward,
                                                const threepp::Vector3& right,Height height){
    const auto offset=safariSideCameraOffset();
    auto desired=position.clone().addScaledVector(forward,offset.z).addScaledVector(right,offset.x);
    // On an uphill start, mounting Y to the car's ground put the trailing
    // camera up inside a gantry that the car had already cleared. Follow the
    // actual ground under the camera, then let the existing tracker smooth it.
    desired.y=height(desired.x,desired.z)+offset.y;
    return desired;
}
}
