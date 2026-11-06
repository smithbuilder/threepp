#pragma once

#include "RallySafariMotion.hpp"
#include "RallySafariCameraClearance.hpp"
#include <iostream>
#include <stdexcept>
#include <utility>

namespace safari_motion_test {
inline void run(){
    auto check=[](bool ok,const char* text){if(!ok)throw std::runtime_error(text);};
    const auto steady=rally::safariCruiseCommand(13.5f,false);
    const float resistance=rally::safariCoastAcceleration(13.5f,false);
    check(resistance>.4f&&resistance<.6f,"Safari coast resistance at49km/h is implausible");
    check(std::abs(steady.throttle*12-resistance)<.00001f&&steady.brake==0,
          "Safari cruise injects acceleration at its target speed");
    auto simulate=[&](int hz){float v=0,maxChange=0;double squaredAcceleration=0;int samples=0;
        for(int n=0;n<10*hz;++n){const auto c=rally::safariCruiseCommand(v,false);
            check(c.throttle>=0&&c.throttle<=1&&c.brake>=0&&c.brake<=1&&c.throttle*c.brake==0,
                  "Safari governor applies invalid or opposing pedals");
            const float a=c.throttle*12-c.brake*18-rally::safariCoastAcceleration(v,false);
            v+=a/hz;
            if(n>5*hz){squaredAcceleration+=a*a;++samples;maxChange=std::max(maxChange,std::abs(a));}
        }
        check(std::abs(v-13.5f)<.0001f&&maxChange<.005f,
              "Safari governor fails to settle at the unchanged cruise target");
        return std::pair{v,std::sqrt(squaredAcceleration/samples)};
    };
    const auto coarse=simulate(30),normal=simulate(120),fine=simulate(240);
    check(std::abs(coarse.first-fine.first)<.0001f&&normal.second<.001,
          "Safari balanced cruise depends on render interval or still chatters");
    const auto excess=rally::safariCruiseCommand(30,false);
    check(excess.brake>0&&excess.throttle==0,"Safari governor does not brake excessive speed");
    const auto airborne=rally::safariTractionCommand(12,8,0,10000);
    check(airborne.longitudinal==0&&airborne.lateral==0&&airborne.support==0,
          "Unsupported Safari tyres still accelerate or steer");
    const auto loaded=rally::safariTractionCommand(12,8,10000,10000);
    check(std::abs(std::hypot(loaded.longitudinal,loaded.lateral)-.9f*9.81f)<.00001f,
          "Safari combined steering/drive exceeds the contact grip budget");
    const auto half=rally::safariTractionCommand(12,8,5000,10000);
    check(std::abs(half.longitudinal*2-loaded.longitudinal)<.00001f&&half.support==.5f,
          "Safari grip does not release with tyre load");
    check(rally::safariPedalAcceleration(15,1,1)==-18,
          "Safari simultaneous pedals must prioritize braking");
    float reverseSpeed=0,reverseYaw=0,reverseHeading=0;threepp::Vector3 reverseMotion;
    float maximumReverseAcceleration=0;
    for(int i=0;i<2400;++i){const float previous=reverseSpeed;
        rally::safariIntegrateMotion(reverseSpeed,reverseYaw,reverseHeading,reverseMotion,0,0,1,false,false,10000,10000,1.f/120);
        maximumReverseAcceleration=std::max(maximumReverseAcceleration,std::abs(reverseSpeed-previous)*120);
    }
    check(reverseSpeed< -5.5f&&reverseSpeed> -6.f&&maximumReverseAcceleration<4.01f,
          "Safari reverse must settle below6m/s without full-braking acceleration or cutoff chatter");
    for(int i=0;i<240;++i)
        rally::safariIntegrateMotion(reverseSpeed,reverseYaw,reverseHeading,reverseMotion,0,1,0,false,false,10000,10000,1.f/120);
    check(reverseSpeed>2.f,"Safari cannot drive forward out of reverse");
    float airSpeed=13.5f,airYaw=0,airHeading=0;threepp::Vector3 airMotion(0,0,13.5f);
    for(int i=0;i<120;++i)rally::safariIntegrateMotion(airSpeed,airYaw,airHeading,airMotion,.4f,1,0,false,false,0,10000,1.f/120);
    check(airSpeed<13.5f&&airSpeed>13&&airMotion.x==0&&airYaw==0&&airHeading==0,
          "Airborne Safari still turns/accelerates from unsupported tyres");
    for(float mismatch:{.2617994f,1.5707963f}){
        float speed=13.5f,yaw=0,heading=mismatch;threepp::Vector3 motion(0,0,13.5f);
        const auto previous=motion;
        const auto pedals=rally::safariCruiseCommand(speed,false);
        rally::safariIntegrateMotion(speed,yaw,heading,motion,0,pedals.throttle,pedals.brake,false,false,10000,10000,1.f/120);
        check(motion.distanceTo(previous)*120<.9f*9.81f+.3f,
              "Safari landing/slip alignment bypasses actual traction acceleration budget");
    }

    // This is the actual gate geometry on flat ground, not a relaxed obstacle.
    using namespace threepp;
    std::vector<std::shared_ptr<Mesh>> barriers;
    for(float side:{-1.f,1.f}){auto m=Mesh::create(BoxGeometry::create(.16f,3.7f,.16f));m->position.set(side*4.3f,1.85f,0);m->updateMatrixWorld(true);barriers.push_back(m);}
    auto beam=Mesh::create(BoxGeometry::create(9,.42f,.2f));beam->position.set(0,3.7f,0);beam->updateMatrixWorld(true);barriers.push_back(beam);
    rally::SafariCameraTracking tracking;float minBoom=1;int clamps=0;
    for(int i=0;i<240;++i){const float z=-60+i*13.5f/30;
        Vector3 target(0,1.1f,z),desired=rally::safariSideCameraOffset();desired.z+=z;
        rally::SafariCameraClearanceReport r;
        const auto p=rally::safariTrackClearCamera(target,desired,Vector3(0,0,13.5f),1.f/30,i==0,barriers,tracking,&r,.30f,true);
        check(std::isfinite(p.x)&&!r.invalidInput&&!r.targetInsideBarrier,"Safari side-camera gate crossing invalid");
        minBoom=std::min(minBoom,r.boomFraction);clamps+=r.hardClamped;
        check(std::abs(p.distanceTo(target)-desired.distanceTo(target))<.001f,
              "Vehicle chase camera accumulates speed-dependent world-position lag");
    }
    check(minBoom>.999f&&clamps==0,"Safari side camera still breathes through a centered flat checkpoint");
    rally::SafariCameraTracking uphill;float minUphillBoom=1;int uphillClamps=0;
    for(int i=0;i<240;++i){const float z=-60+i*13.5f/30;
        Vector3 position(0,.3f*z,z),target(0,.3f*z+1.1f,z);
        const auto desired=rally::safariSideCameraPosition(position,Vector3(0,0,1),Vector3(1,0,0),[](float,float zz){return .3f*zz;});
        rally::SafariCameraClearanceReport r;
        const auto p=rally::safariTrackClearCamera(target,desired,Vector3(0,0,13.5f),1.f/30,i==0,barriers,uphill,&r,.30f,true);
        check(std::abs(p.distanceTo(target)-desired.distanceTo(target))<.001f,
              "Vehicle chase camera accumulates uphill translation lag");
        minUphillBoom=std::min(minUphillBoom,r.boomFraction);uphillClamps+=r.hardClamped;
    }
    check(minUphillBoom>.999f&&uphillClamps==0,"Safari uphill start camera rises into a cleared gantry");
    std::cout<<"PASS: Safari balanced cruise target="<<normal.first<<"m/s settled acceleration RMS="<<normal.second
             <<"m/s2; actual-gate side-camera flat/uphill minBoom="<<minBoom<<'/'<<minUphillBoom<<" hardClamps="<<clamps+uphillClamps<<".\n";
}
}
