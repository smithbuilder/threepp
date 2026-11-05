#pragma once
#include "RallyDynamics.hpp"
#include "RallyRideReplay.hpp"
#include "RallyRoadContact.hpp"
#include "RallySafariStage.hpp"
#include "RallySuspension.hpp"
#include "SafariRideTest.hpp"
#include "threepp/extras/core/NoiseUtils.hpp"
#include <cstdlib>
#include <iomanip>

namespace rally {
inline void compareRideReplay(const std::filesystem::path& source,const std::filesystem::path& output){
    const auto inputs=readRideReplay(source);
    auto terrain=[](float x,float z){return 5.5f*std::sin(x*.024f)+4.f*std::cos(z*.031f)+9.f*(noise::fbm(x*.021f,z*.021f,256,71,4)-.5f)+.17f*std::sin(x*.7f+z*.4f);};
    auto track=[&](float a){float x=64*std::sin(a)+8*std::sin(3*a),z=90*std::cos(a);return Vector3(x,terrain(x,z),z);};
    std::vector<float> vertices;std::vector<unsigned> indices;
    for(int i=0;i<=320;++i){const float a=i*2*3.14159265359f/320;auto p=track(a),t=track(a+.001f).sub(p).normalize();Vector3 side(t.z,0,-t.x);
        for(int j=0;j<=8;++j){float s=j*.25f-1,x=p.x+s*3.7f*side.x,z=p.z+s*3.7f*side.z;vertices.insert(vertices.end(),{x,safariStageRoadHeight(x,z,s,terrain(x,z)),z});}
        if(i<320)for(int j=0;j<8;++j){unsigned b=i*9+j;indices.insert(indices.end(),{b,b+9,b+1,b+1,b+9,b+10});}}
    std::vector<float> land;std::vector<unsigned> landIndices;
    for(int j=0;j<=160;++j)for(int i=0;i<=160;++i){float x=-260+i*3.25f,z=-260+j*3.25f;land.insert(land.end(),{x,terrain(x,z),z});if(i<160&&j<160){unsigned b=j*161+i;landIndices.insert(landIndices.end(),{b,b+161,b+1,b+161,b+162,b+1});}}
    RoadContactSurface road(vertices,indices),landSurface(land,landIndices);
    auto height=[&](float x,float z){if(auto y=road.height(x,z))return *y;if(auto y=landSurface.height(x,z))return *y;return terrain(x,z);};
    std::filesystem::create_directories(output);
    std::ofstream summary(output/"matched-comparison.json");summary<<std::setprecision(9)<<"{\"scope\":\"identical prescribed planar inputs on the unchanged rendered graded road; not human controls\",\"models\":[";
    struct Configuration {std::string name;SafariRideTuning tuning;};
    std::vector<Configuration> configurations{{"original-buggy",{}},{"safari-previous",SafariRideTuning::previous()},{"safari-revised",{}}};
    for(int model=0;model<static_cast<int>(configurations.size());++model){
        const auto& configuration=configurations[model];const auto& name=configuration.name;
        const auto dims=model==0?buggyDimensions:safariDimensions;
        RideDynamics ride;ride.compliant.tuning=configuration.tuning;
        ride.reset({0,height(0,90),90},3.14159265359f/2,height,dims,model==0?RideContactResponse::Legacy:RideContactResponse::Compliant);
        auto group=Group::create();auto rig=addSuspension(*group,dims,model==0?SuspensionProfile::Legacy:SuspensionProfile::Safari);
        std::array<float,4> low,high,shockLow,shockHigh;low.fill(10);high.fill(-10);shockLow.fill(10);shockHigh.fill(-10);
        float maxGap=0,maxPenetration=0,airSeconds=0,maxRelativePitch=0,maxRelativeRoll=0;double pitchEnergy=0,rollEnergy=0;
        std::ofstream csv(output/(name+".csv"));csv<<std::setprecision(9)<<"frame,time,x,z,pitch,roll,bodyY,relativePitch,relativeRoll,travelFL,travelFR,travelRL,travelRR,shockFL,shockFR,shockRL,shockRR,gapFL,gapFR,gapRL,gapRR\n";
        for(std::size_t n=0;n<inputs.size();++n){const auto& row=inputs[n];Vector3 p(row.x,0,row.z);
            ride.step(p,row.heading,row.steer,row.acceleration,row.lateral,row.dt,height);
            const auto roadPoseAt=roadPose(p,row.heading,height,dims);const float relativePitch=ride.pitch-roadPoseAt.pitch,relativeRoll=ride.roll-roadPoseAt.roll;
            pitchEnergy+=relativePitch*relativePitch;rollEnergy+=relativeRoll*relativeRoll;maxRelativePitch=std::max(maxRelativePitch,std::abs(relativePitch));maxRelativeRoll=std::max(maxRelativeRoll,std::abs(relativeRoll));
            int supported=0;std::array<WheelContact,4> wheels;
            for(int i=0;i<4;++i){wheels[i]=ride.contact(i,row.heading,row.steer,height);maxGap=std::max(maxGap,wheels[i].gap);maxPenetration=std::max(maxPenetration,-wheels[i].gap);supported+=ride.grounded[i];low[i]=std::min(low[i],wheels[i].local.y);high[i]=std::max(high[i],wheels[i].local.y);}
            if(!supported)airSeconds+=row.dt;
            if(n+1<inputs.size()&&inputs[n+1].frame==row.frame)continue;
            updateSuspension(rig,wheels,row.steer);
            csv<<row.frame<<','<<row.time<<','<<row.x<<','<<row.z<<','<<ride.pitch<<','<<ride.roll<<','<<ride.chassis.y<<','<<relativePitch<<','<<relativeRoll;
            for(const auto& wheel:wheels)csv<<','<<wheel.local.y;
            for(int i=0;i<4;++i){const float length=rig.shocks[i].length;shockLow[i]=std::min(shockLow[i],length);shockHigh[i]=std::max(shockHigh[i],length);csv<<','<<length;}
            for(const auto& wheel:wheels)csv<<','<<wheel.gap;csv<<'\n';
            if(row.frame%30==0)if(const char* heartbeat=std::getenv("THREEPP_EVALUATION_HEARTBEAT")){std::ofstream beat(heartbeat);beat<<row.frame;}
        }
        if(model)summary<<',';
        const auto& tune=configuration.tuning;
        summary<<"{\"name\":\""<<name<<"\",\"pitchInertia\":"<<(model==0?RideDynamics::pitchInertia:tune.pitchInertia)<<",\"lowCompression\":"<<(model==0?RideDynamics::compressionDamping:tune.lowCompression)<<",\"lowRebound\":"<<(model==0?RideDynamics::reboundDamping:tune.lowRebound)<<",\"damperKnee\":"<<(model==0?0:tune.damperKnee)<<",\"maxGap\":"<<maxGap<<",\"maxPenetration\":"<<maxPenetration<<",\"airSeconds\":"<<airSeconds<<",\"pitchRms\":"<<std::sqrt(pitchEnergy/inputs.size())<<",\"rollRms\":"<<std::sqrt(rollEnergy/inputs.size())<<",\"maxRelativePitch\":"<<maxRelativePitch<<",\"maxRelativeRoll\":"<<maxRelativeRoll<<",\"wheelRange\":[";
        for(int i=0;i<4;++i){if(i)summary<<',';summary<<high[i]-low[i];}summary<<"],\"shockRange\":[";for(int i=0;i<4;++i){if(i)summary<<',';summary<<shockHigh[i]-shockLow[i];}summary<<']';
        if(model!=0){const auto bump=safariSingleWheelBump(tune);summary<<",\"singleWheelBump\":{\"wheelCompression\":"<<bump.wheelCompression<<",\"bodyHeave\":"<<bump.bodyHeave<<",\"bodyPitch\":"<<bump.bodyPitch<<",\"bodyRoll\":"<<bump.bodyRoll<<",\"damperStroke\":"<<bump.damperStroke<<",\"settlingSeconds\":"<<bump.settlingSeconds<<'}';}
        summary<<'}';
    }
    summary<<"]}\n";
    if(!summary)throw std::runtime_error("Cannot write matched suspension comparison");
}
}
