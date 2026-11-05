#pragma once
#include "SafariRideTest.hpp"
#include "RallyDynamics.hpp"
#include "RallyRoadContact.hpp"
#include "RallySafariMotion.hpp"
#include "RallySafariStage.hpp"
#include <filesystem>
#include <sstream>
#include <stdexcept>
#include "threepp/extras/core/NoiseUtils.hpp"
#include <fstream>
#include <iostream>
#include <iomanip>
#include <memory>
namespace rally::ride_audit {
using namespace threepp;
inline float terrain(float x,float z){return 5.5f*std::sin(x*.024f)+4.f*std::cos(z*.031f)+9.f*(noise::fbm(x*.021f,z*.021f,256,71,4)-.5f)+.17f*std::sin(x*.7f+z*.4f);}
inline Vector3 track(float a){float x=64*std::sin(a)+8*std::sin(3*a),z=90*std::cos(a);return {x,terrain(x,z),z};}
inline std::string scenario(bool compliant,bool legacy,bool graded,const std::filesystem::path& out){
 std::vector<Vector3> route;std::vector<float> vertices,land;std::vector<unsigned> indices,landIndices;
 for(int i=0;i<=320;++i){float a=i*2*3.14159265359f/320;auto p=track(a),t=track(a+.001f).sub(p).normalize();Vector3 side(t.z,0,-t.x);route.push_back(p);for(int j=0;j<=8;++j){float s=j*2.f/8-1,x=p.x+s*3.7f*side.x,z=p.z+s*3.7f*side.z;vertices.insert(vertices.end(),{x,graded?safariStageRoadHeight(x,z,s,terrain(x,z)):terrain(x,z)+.02f,z});}if(i<320)for(int j=0;j<8;++j){unsigned b=i*9+j;indices.insert(indices.end(),{b,b+9,b+1,b+1,b+9,b+10});}}
 for(int j=0;j<=160;++j)for(int i=0;i<=160;++i){float x=-260+i*3.25f,z=-260+j*3.25f;land.insert(land.end(),{x,terrain(x,z),z});if(i<160&&j<160){unsigned b=j*161+i;landIndices.insert(landIndices.end(),{b,b+161,b+1,b+161,b+162,b+1});}}
 rally::RoadContactSurface road(vertices,indices),landSurface(land,landIndices);unsigned roadHits=0,roadMisses=0;float maxDifference=0;
 auto height=[&](float x,float z){if(legacy)return terrain(x,z)+.02f;if(auto y=road.height(x,z)){++roadHits;maxDifference=std::max(maxDifference,std::abs(*y-terrain(x,z)-.02f));return *y;}++roadMisses;if(auto y=landSurface.height(x,z))return *y;return terrain(x,z);};
 Vector3 position=track(0),motion;float heading=3.14159265359f/2,velocity=0,steer=0,yawRate=0;
 rally::RideDynamics ride;ride.reset(position,heading,height,rally::safariDimensions,compliant?rally::RideContactResponse::Compliant:rally::RideContactResponse::Projected);
 constexpr float step=1.f/120;float maxGap=0,maxPen=0,maxHeave=0,maxRate=0,maxLoad=0,maxSpring=0,previousPitch=ride.pitch,minSpeed=100,maxSpeed=0,maxOff=0,airTime=0;int next=1;
 std::ofstream csv(out);csv<<"time,x,z,speed,pitch,roll,heave,load,gap,penetration,grounded,throttle,yaw,steer\n";csv<<std::setprecision(9);
 for(int n=0;n<3600;++n){int nearest=0;float nearD=1e9f;for(int j=0;j<321;++j){auto d=position.clone().sub(route[j]);float dd=d.x*d.x+d.z*d.z;if(dd<nearD){nearD=dd;nearest=j;}}
  float off=std::sqrt(nearD),a=nearest*2*3.14159265359f/320;auto aim=track(a+.11f).sub(position);float turn=std::clamp(rally::SafariRideState::angleDelta(std::atan2(aim.x,aim.z)-heading)*1.35f,-1.f,1.f);
  float throttle=velocity<13.5f?1.f:0,brake=velocity>14.5f?.3f:0,drag=off>4.2f?1.25f:.24f;
  if(!legacy){auto pedal=rally::safariCruiseCommand(velocity,off>4.2f);throttle=pedal.throttle;brake=pedal.brake;}
  steer+=(turn-steer)*(1-std::exp(-7*step));const float previous=velocity;float support=1,targetYaw=std::tan(steer*.42f)*velocity/2.45f;
  if(!legacy){float load=0;for(float f:ride.forces)load+=std::max(0.f,f);float weight=(compliant?rally::SafariRideState::sprungMass+4*rally::SafariRideState::unsprungMass:rally::RideDynamics::mass)*9.81f;rally::safariIntegrateMotion(velocity,yawRate,heading,motion,steer*.4f,throttle,brake,false,off>4.2f,load,weight,step);}
  else {velocity+=(throttle*12-brake*18-velocity*drag-velocity*std::abs(velocity)*.014f)*step;velocity=std::clamp(velocity,-6.f,30.f);targetYaw=std::tan(steer*.42f)*velocity/2.45f;yawRate+=(targetYaw-yawRate)*(1-std::exp(-7*step));heading+=yawRate*step;Vector3 desired(std::sin(heading)*velocity,0,std::cos(heading)*velocity);motion.lerp(desired,1-std::exp(-(off>4.2f?3.f:7.f)*step));}position.x+=motion.x*step;position.z+=motion.z*step;
  ride.step(position,heading,steer*.4f,(velocity-previous)/step,velocity*yawRate,step,height);
  auto pose=rally::roadPose(position,heading,height,rally::safariDimensions);float heave=ride.chassis.y-pose.ride,gap=0,pen=0,load=0;int grounded=0;for(int i=0;i<4;++i){auto c=ride.contact(i,heading,steer*.4f,height);gap=std::max(gap,c.gap);pen=std::max(pen,-c.gap);grounded+=ride.grounded[i];load+=ride.forces[i];}
  for(int i=0;i<4;++i){maxLoad=std::max(maxLoad,ride.forces[i]);maxSpring=std::max(maxSpring,std::abs(ride.compliant.springForces[i]));if(!std::isfinite(ride.forces[i])||!std::isfinite(ride.pitch)||!std::isfinite(ride.roll))throw std::runtime_error("Nonfinite ride audit state");if(compliant&&(ride.compliant.travel[i]<safariDimensions.droop-.00005f||ride.compliant.travel[i]>safariDimensions.bump+.00005f))throw std::runtime_error("Ride audit exceeds reviewed travel");} maxGap=std::max(maxGap,gap);maxPen=std::max(maxPen,pen);maxHeave=std::max(maxHeave,std::abs(heave));maxRate=std::max(maxRate,std::abs(ride.pitch-previousPitch)/step);previousPitch=ride.pitch;maxOff=std::max(maxOff,off);if(!grounded)airTime+=step;if(n>360)minSpeed=std::min(minSpeed,velocity);maxSpeed=std::max(maxSpeed,velocity);
  auto gate=track(next*2*3.14159265359f/8);if(std::hypot(position.x-gate.x,position.z-gate.z)<7)next=(next+1)%8;
  if(n%4==3)csv<<(n+1)*step<<','<<position.x<<','<<position.z<<','<<velocity<<','<<ride.pitch<<','<<ride.roll<<','<<heave<<','<<load<<','<<gap<<','<<pen<<','<<grounded<<','<<throttle<<','<<yawRate<<','<<steer<<'\n';
 }
 std::ostringstream summary;summary<<"{\"compliant\":"<<compliant<<",\"gradedStage\":"<<graded<<",\"maxTyreNormalLoad\":"<<maxLoad<<",\"maxSpringForce\":"<<maxSpring<<",\"legacyController\":"<<legacy<<",\"gap\":"<<maxGap<<",\"penetration\":"<<maxPen<<",\"heave\":"<<maxHeave<<",\"pitchRateDegrees\":"<<maxRate*180/3.14159265359f<<",\"airTime\":"<<airTime<<",\"minSpeedAfter3s\":"<<minSpeed<<",\"maxSpeed\":"<<maxSpeed<<",\"maxOff\":"<<maxOff<<",\"nextGate\":"<<next<<",\"roadMaxAnalyticDifference\":"<<maxDifference<<",\"roadHits\":"<<roadHits<<",\"roadMisses\":"<<roadMisses<<"}\n";
 return summary.str();
}

} // namespace rally::ride_audit

namespace rally {
// Call before Canvas/audio construction from the signed review executable.
// This audit exercises CPU physics and the actual shared planar controller;
// its invariant result is separate from native visual/motion acceptance.
inline int runSafariRideAudit(const std::filesystem::path& outputDirectory){
    std::filesystem::create_directories(outputDirectory);
    safariRideRegressions();
    const std::array<std::string,4> names{"projected-original-controller-original-road","projected-current-controller-graded-road","compliant-current-controller-original-road","compliant-current-controller-graded-road"};
    std::ofstream summary(outputDirectory/"audit.json");summary<<"{\"scope\":\"CPU invariants and closed-loop diagnosis, not native/human acceptance\",\"physicalInvariantsPassed\":true,\"secondsPerScenario\":30,\"scenarios\":[";
    for(int i=0;i<4;++i){const bool compliant=i>=2,legacy=i==0,graded=i==1||i==3;
        const auto report=ride_audit::scenario(compliant,legacy,graded,outputDirectory/(names[i]+".csv"));
        if(i)summary<<',';summary<<"{\"name\":\""<<names[i]<<"\",\"result\":"<<report<<'}';std::cout<<names[i]<<' '<<report;
    }
    summary<<"]}\n";return summary?0:1;
}
}
