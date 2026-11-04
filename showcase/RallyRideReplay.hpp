#pragma once
#include "RallyVehicle.hpp"
#include <filesystem>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <vector>

namespace rally {
// Inspection-only prescribed planar inputs. All compared suspensions see the
// same positions, speed, steering and acceleration, on the same rendered road.
// This is not a second driving controller or a playable handling test.
struct RideReplayInput {
    int frame=0;
    bool driving=false;
    float time=0,dt=0,x=0,z=0,heading=0,steer=0,acceleration=0,lateral=0;
};
inline std::vector<RideReplayInput> readRideReplay(const std::filesystem::path& path){
    std::ifstream file(path);
    std::string line;
    if(!file||!std::getline(file,line))throw std::runtime_error("Cannot read suspension comparison inputs");
    if(!line.empty()&&line.back()=='\r')line.pop_back();
    if(line!="frame,driving,time,dt,x,z,heading,steer,acceleration,lateral")throw std::runtime_error("Unknown suspension comparison CSV format");
    std::vector<RideReplayInput> rows;
    while(std::getline(file,line)){
        if(line.empty())continue;
        std::replace(line.begin(),line.end(),',',' ');std::istringstream values(line);
        RideReplayInput row;int driving;
        if(!(values>>row.frame>>driving>>row.time>>row.dt>>row.x>>row.z>>row.heading>>row.steer>>row.acceleration>>row.lateral))throw std::runtime_error("Invalid suspension comparison row");
        row.driving=driving!=0;
        for(float value:{row.time,row.dt,row.x,row.z,row.heading,row.steer,row.acceleration,row.lateral})if(!std::isfinite(value))throw std::runtime_error("Nonfinite suspension comparison input");
        if(row.frame<0||row.frame>=900||row.time<0||row.time>45||row.dt<=0||row.dt>.05f||std::abs(row.x)>235||std::abs(row.z)>235||std::abs(row.heading)>1000||std::abs(row.steer)>.401f||std::abs(row.acceleration)>1000||std::abs(row.lateral)>1000||rows.size()>=10800)throw std::runtime_error("Suspension comparison input exceeds bounded review limits");
        if(rows.empty()?row.frame!=0:row.frame<rows.back().frame||row.frame>rows.back().frame+1)throw std::runtime_error("Suspension comparison frames are not contiguous");
        rows.push_back(row);
    }
    if(rows.empty())throw std::runtime_error("Suspension comparison has no inputs");
    return rows;
}
}
