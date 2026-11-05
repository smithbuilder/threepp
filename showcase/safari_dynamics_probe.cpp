// CPU-only replay of the exact ride inputs recorded by timber_rally.
// The baseline calls the shipping RideDynamics; experimental coefficients below
// are deliberately confined to this diagnostic and never modify the game.
#include "RallyDynamics.hpp"
#include "threepp/extras/core/NoiseUtils.hpp"
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace threepp;
namespace {
struct Input { int frame=0; bool driving=true; float time=0,dt=0,x=0,z=0,heading=0,steer=0,acceleration=0,lateral=0; };
std::vector<std::string> fields(const std::string& line){std::stringstream s(line);std::string value;std::vector<std::string> result;while(std::getline(s,value,','))result.push_back(value);return result;}
std::vector<Input> readInputs(const std::filesystem::path& path){
    std::ifstream file(path);if(!file)throw std::runtime_error("Cannot open ride CSV: "+path.string());
    std::string line;std::getline(file,line);auto header=fields(line);std::map<std::string,int> columns;
    for(int i=0;i<static_cast<int>(header.size());++i){if(!header[i].empty()&&header[i].back()=='\r')header[i].pop_back();columns[header[i]]=i;}
    auto index=[&](std::initializer_list<const char*> names){for(auto name:names)if(columns.contains(name))return columns.at(name);return -1;};
    int frame=index({"frame"}),driving=index({"driving","active"}),time=index({"time","t"}),dt=index({"dt"});
    int x=index({"x"}),z=index({"z"}),heading=index({"heading"}),steer=index({"steer"}),acceleration=index({"acceleration","longitudinal"}),lateral=index({"lateral","lateralAcceleration"});
    if(dt<0||x<0||z<0||heading<0||steer<0||acceleration<0||lateral<0)throw std::runtime_error("Missing required ride CSV column");
    std::vector<Input> inputs;float elapsed=0;
    while(std::getline(file,line)){if(line.empty())continue;auto f=fields(line);auto get=[&](int i,float fallback=0){return i<0?fallback:std::stof(f.at(i));};
        Input r;r.dt=get(dt);elapsed+=r.dt;r.time=get(time,elapsed);r.frame=static_cast<int>(get(frame,static_cast<float>(inputs.size()/4)));r.driving=get(driving,r.dt<.02f?1.f:0.f)>0;
        r.x=get(x);r.z=get(z);r.heading=get(heading);r.steer=get(steer);r.acceleration=get(acceleration);r.lateral=get(lateral);inputs.push_back(r);}
    if(inputs.empty())throw std::runtime_error("Empty ride CSV");return inputs;
}
struct Config {
    std::string name="baseline";bool noLateral=false,noLongitudinal=false,noRipple=false,flat=false,contactTorque=false,coupledBump=false;
    float spring=18000,compression=1700,rebound=2400,antiRoll=2600,cg=.68f,rollI=460,pitchI=540;
};
float terrain(float x,float z,const Config& c){
    if(c.flat)return .02f;
    return 5.5f*std::sin(x*.024f)+4.f*std::cos(z*.031f)+9.f*(noise::fbm(x*.021f,z*.021f,256,71,4)-.5f)+(c.noRipple?0.f:.17f*std::sin(x*.7f+z*.4f))+.02f;
}
// A parameterized copy exists only for causal comparisons. Its default output
// is checked against the real solver at every recorded input before trusting it.
struct ExperimentalRide: rally::RideDynamics {
    Config config;
    template<class Height> void step(const Vector3& position,float heading,float steer,float acceleration,float lateralAcceleration,float dt,Height height){
        float remaining=std::clamp(dt,0.f,.05f);chassis.x=position.x;chassis.z=position.z;
        while(remaining>1e-6f){float h=std::min(remaining,1.f/120);remaining-=h;
            auto q=rally::chassisOrientation(heading,pitch,roll);std::array<float,4> surfaceVelocity{};
            for(int i=0;i<4;++i){auto c=rally::wheelContact(i,chassis,q,steer,height,false,dimensions);travel[i]=c.requested;
                float rate=std::clamp((travel[i]-previousTravel[i])/h,-5.f,5.f);previousTravel[i]=travel[i];grounded[i]=travel[i]>=dimensions.droop;
                auto lever=rally::hubAtTravel(i,std::clamp(travel[i],dimensions.droop,dimensions.bump),dimensions);lever.y-=config.cg;lever.applyQuaternion(rally::chassisOrientation(0,pitch,roll));
                surfaceVelocity[i]=rate*Vector3(0,1,0).applyQuaternion(q).y+heaveVelocity-lever.z*pitchVelocity+lever.x*rollVelocity;
                float span=dimensions.bump-dimensions.droop,endSpan=span*(.15f/(rally::buggyDimensions.bump-rally::buggyDimensions.droop));
                float endZone=std::clamp((travel[i]-(dimensions.bump-endSpan))/endSpan,0.f,1.f);
                float damping=(rate>=0?config.compression:config.rebound)*(1+2*endZone*endZone);
                float stop=std::max(0.f,travel[i]-(dimensions.bump-span*(.045f/(rally::buggyDimensions.bump-rally::buggyDimensions.droop))));
                forces[i]=grounded[i]?mass*gravity*.25f+config.spring*(travel[i]-dimensions.staticTravel)+damping*rate+180000*stop*stop:0;}
            for(int axle=0;axle<2;++axle){int l=2*axle,r=l+1;if(grounded[l]&&grounded[r]){float transfer=config.antiRoll*(travel[r]-travel[l]);forces[l]-=transfer;forces[r]+=transfer;}}
            float support=0;for(float f:forces)support+=std::clamp(f,0.f,20000.f);float coupling=config.contactTorque?std::clamp(support/(mass*gravity),0.f,1.f):1.f;
            float fy=-mass*gravity,tx=-mass*config.cg*std::clamp(acceleration,-20.f,15.f)*coupling,tz=mass*config.cg*std::clamp(lateralAcceleration,-18.f,18.f)*coupling;
            for(int i=0;i<4;++i){forces[i]=std::clamp(forces[i],0.f,20000.f);auto lever=rally::hubAtTravel(i,std::clamp(travel[i],dimensions.droop,dimensions.bump),dimensions);lever.y-=config.cg;
                lever.applyQuaternion(rally::chassisOrientation(0,pitch,roll));fy+=forces[i];tx-=lever.z*forces[i];tz+=lever.x*forces[i];}
            heaveVelocity+=fy/mass*h;chassis.y+=heaveVelocity*h;pitchVelocity+=(tx-120*pitchVelocity)/config.pitchI*h;rollVelocity+=(tz-100*rollVelocity)/config.rollI*h;
            pitch+=pitchVelocity*h;roll+=rollVelocity*h;
            if(std::abs(pitch)>.65f){pitch=std::clamp(pitch,-.65f,.65f);pitchVelocity=0;}if(std::abs(roll)>.70f){roll=std::clamp(roll,-.70f,.70f);rollVelocity=0;}
            if(config.coupledBump){bool corrected=false;for(int pass=0;pass<12;++pass){q=rally::chassisOrientation(heading,pitch,roll);float depth=0;int wheel=-1;
                for(int i=0;i<4;++i){auto c=rally::wheelContact(i,chassis,q,steer,height,true,dimensions);if(-c.gap>depth){depth=-c.gap;wheel=i;}}
                if(wheel<0||depth<.00001f)break;corrected=true;
                auto lever=rally::hubAtTravel(wheel,dimensions.bump,dimensions);lever.y-=config.cg;lever.applyQuaternion(rally::chassisOrientation(0,pitch,roll));
                float jp=-lever.z,jr=lever.x,k=1/mass+jp*jp/config.pitchI+jr*jr/config.rollI;
                float correction=(depth+.00001f)/k;chassis.y+=correction/mass;pitch+=jp*correction/config.pitchI;roll+=jr*correction/config.rollI;
                float normal=heaveVelocity+jp*pitchVelocity+jr*rollVelocity,impulse=std::max(0.f,surfaceVelocity[wheel]-normal)/k;
                heaveVelocity+=impulse/mass;pitchVelocity+=jp*impulse/config.pitchI;rollVelocity+=jr*impulse/config.rollI;
            }if(corrected)++bumpCorrections;continue;}
            q=rally::chassisOrientation(heading,pitch,roll);float lift=0,up=Vector3(0,1,0).applyQuaternion(q).y;
            for(int i=0;i<4;++i){auto c=rally::wheelContact(i,chassis,q,steer,height,false,dimensions);lift=std::max(lift,(c.requested-dimensions.bump)*up);}
            if(lift>0){chassis.y+=lift+.0001f;heaveVelocity=std::max(0.f,heaveVelocity);++bumpCorrections;}
        }
    }
};
struct Correlation {
    double n=0,x=0,y=0,xx=0,yy=0,xy=0;
    void add(double a,double b){++n;x+=a;y+=b;xx+=a*a;yy+=b*b;xy+=a*b;}
    double value()const{double d=(n*xx-x*x)*(n*yy-y*y);return d>1e-12?(n*xy-x*y)/std::sqrt(d):0;}
};
struct Stats {
    int rows=0,frames=0,bumpCorrections=0,rollLimitRows=0,pitchLimitRows=0,lowLoadRows=0,twoWheelsRows=0,airborneRows=0;
    double drivingSeconds=0,aboveTipSeconds=0,aboveGripSeconds=0,hardStopSeconds=0,airborneSeconds=0;
    float maxHeave=0,maxRoll=0,maxPitch=0,maxRelativeRoll=0,maxRelativePitch=0,maxWheelGap=0,maxPenetration=0,maxInputLateral=0,maxAppliedLateral=0,maxLoad=0,minLoad=1e9f,maxHeaveSpeed=0;
    float worstRollTime=0,worstHeaveTime=0,worstGapTime=0,minRequested=1e9f,maxRequested=-1e9f;
    Correlation lateralRoll,rippleHeave;std::vector<float> lateralSamples;
};
template<class Ride> Stats replay(const std::vector<Input>& inputs,const rally::VehicleDimensions& dims,const Config& config,Ride& ride,std::ostream* detail=nullptr,rally::RideContactResponse response=rally::RideContactResponse::Legacy){
    auto height=[&](float x,float z){return terrain(x,z,config);};
    ride.reset(Vector3(0,0,90),3.14159265359f/2,height,dims,response);
    Stats stats;
    if(detail)*detail<<"row,frame,driving,time,dt,x,z,lateral,roadRoll,roll,relativeRoll,roadPitch,pitch,relativePitch,heave,heaveVelocity,wheelGap,penetration,grounded,bumpCorrections,force0,force1,force2,force3,travel0,travel1,travel2,travel3\n";
    for(size_t row=0;row<inputs.size();++row){const auto& in=inputs[row];Vector3 p(in.x,0,in.z);float acceleration=config.noLongitudinal?0:in.acceleration,lateral=config.noLateral?0:in.lateral;
        int previousBumps=ride.bumpCorrections;ride.step(p,in.heading,in.steer,acceleration,lateral,in.dt,height);++stats.rows;
        auto road=rally::roadPose(p,in.heading,height,dims);auto q=rally::chassisOrientation(in.heading,ride.pitch,ride.roll);
        auto relative=rally::chassisOrientation(in.heading,road.pitch,road.roll).invert().multiply(q);Euler angles;angles.setFromQuaternion(relative);
        float heave=ride.chassis.y-road.ride,gap=0,penetration=0;int grounded=0;for(int i=0;i<4;++i){auto c=rally::wheelContact(i,ride.chassis,q,in.steer,height,true,dims);gap=std::max(gap,std::max(0.f,c.gap));penetration=std::max(penetration,std::max(0.f,-c.gap));
            grounded+=ride.grounded[i]?1:0;stats.maxLoad=std::max(stats.maxLoad,ride.forces[i]);stats.minLoad=std::min(stats.minLoad,ride.forces[i]);stats.minRequested=std::min(stats.minRequested,ride.travel[i]);stats.maxRequested=std::max(stats.maxRequested,ride.travel[i]);}
        if(in.driving){stats.drivingSeconds+=in.dt;stats.lateralSamples.push_back(std::abs(in.lateral));stats.maxInputLateral=std::max(stats.maxInputLateral,std::abs(in.lateral));stats.maxAppliedLateral=std::max(stats.maxAppliedLateral,std::abs(std::clamp(lateral,-18.f,18.f)));
            if(std::abs(in.lateral)>rally::RideDynamics::gravity*dims.halfTrack/config.cg)stats.aboveTipSeconds+=in.dt;if(std::abs(in.lateral)>rally::RideDynamics::gravity)stats.aboveGripSeconds+=in.dt;
            if(std::abs(ride.roll)>=.6999f)++stats.rollLimitRows;if(std::abs(ride.pitch)>=.6499f)++stats.pitchLimitRows;
            if(std::abs(heave)>stats.maxHeave){stats.maxHeave=std::abs(heave);stats.worstHeaveTime=in.time;}if(std::abs(ride.roll)>stats.maxRoll){stats.maxRoll=std::abs(ride.roll);stats.worstRollTime=in.time;}
            stats.maxPitch=std::max(stats.maxPitch,std::abs(ride.pitch));stats.maxRelativeRoll=std::max(stats.maxRelativeRoll,std::abs(static_cast<float>(angles.z)));stats.maxRelativePitch=std::max(stats.maxRelativePitch,std::abs(static_cast<float>(angles.x)));
            stats.maxHeaveSpeed=std::max(stats.maxHeaveSpeed,std::abs(ride.heaveVelocity));if(grounded<4)++stats.lowLoadRows;if(grounded<=2)++stats.twoWheelsRows;if(!grounded){++stats.airborneRows;stats.airborneSeconds+=in.dt;}
            if(ride.bumpCorrections>previousBumps)stats.hardStopSeconds+=in.dt;stats.lateralRoll.add(std::abs(lateral),std::abs(static_cast<float>(angles.z)));
            stats.rippleHeave.add(std::abs(.17f*std::sin(in.x*.7f+in.z*.4f)),std::abs(heave));}
        const bool frameEnd=row+1==inputs.size()||inputs[row+1].frame!=in.frame;
        if(frameEnd){++stats.frames;if(gap>stats.maxWheelGap){stats.maxWheelGap=gap;stats.worstGapTime=in.time;}stats.maxPenetration=std::max(stats.maxPenetration,penetration);}
        if(detail){*detail<<row<<','<<in.frame<<','<<in.driving<<','<<in.time<<','<<in.dt<<','<<in.x<<','<<in.z<<','<<lateral<<','<<road.roll<<','<<ride.roll<<','<<angles.z<<','<<road.pitch<<','<<ride.pitch<<','<<angles.x<<','<<heave<<','<<ride.heaveVelocity<<','<<gap<<','<<penetration<<','<<grounded<<','<<ride.bumpCorrections;
            for(float f:ride.forces)*detail<<','<<f;for(float t:ride.travel)*detail<<','<<t;*detail<<'\n';}
    }stats.bumpCorrections=ride.bumpCorrections;return stats;
}
void printStats(std::ostream& out,const Config& c,Stats s){std::sort(s.lateralSamples.begin(),s.lateralSamples.end());float p95=s.lateralSamples.empty()?0:s.lateralSamples[static_cast<size_t>((s.lateralSamples.size()-1)*.95)];
    out<<std::setprecision(9)<<"{\"variant\":\""<<c.name<<"\",\"rows\":"<<s.rows<<",\"frames\":"<<s.frames<<",\"drivingSeconds\":"<<s.drivingSeconds<<",\"maxHeave\":"<<s.maxHeave<<",\"maxRoll\":"<<s.maxRoll<<",\"maxPitch\":"<<s.maxPitch<<",\"maxRelativeRoll\":"<<s.maxRelativeRoll<<",\"maxRelativePitch\":"<<s.maxRelativePitch<<",\"maxWheelGap\":"<<s.maxWheelGap<<",\"maxPenetration\":"<<s.maxPenetration<<",\"bumpCorrections\":"<<s.bumpCorrections<<",\"hardStopSeconds\":"<<s.hardStopSeconds<<",\"rollLimitRows\":"<<s.rollLimitRows<<",\"pitchLimitRows\":"<<s.pitchLimitRows<<",\"lowLoadRows\":"<<s.lowLoadRows<<",\"twoWheelsRows\":"<<s.twoWheelsRows<<",\"airborneRows\":"<<s.airborneRows<<",\"airborneSeconds\":"<<s.airborneSeconds<<",\"maxInputLateral\":"<<s.maxInputLateral<<",\"p95InputLateral\":"<<p95<<",\"maxAppliedLateral\":"<<s.maxAppliedLateral<<",\"aboveTipSeconds\":"<<s.aboveTipSeconds<<",\"aboveGripSeconds\":"<<s.aboveGripSeconds<<",\"minLoad\":"<<s.minLoad<<",\"maxLoad\":"<<s.maxLoad<<",\"minRequestedTravel\":"<<s.minRequested<<",\"maxRequestedTravel\":"<<s.maxRequested<<",\"maxHeaveSpeed\":"<<s.maxHeaveSpeed<<",\"worstRollTime\":"<<s.worstRollTime<<",\"worstHeaveTime\":"<<s.worstHeaveTime<<",\"worstGapTime\":"<<s.worstGapTime<<",\"lateralRelativeRollCorrelation\":"<<s.lateralRoll.value()<<",\"rippleHeaveCorrelation\":"<<s.rippleHeave.value()<<",\"cg\":"<<c.cg<<",\"spring\":"<<c.spring<<",\"compression\":"<<c.compression<<",\"rebound\":"<<c.rebound<<",\"antiRoll\":"<<c.antiRoll<<"}\n";
}
}
int main(int argc,char** argv){try{
    std::filesystem::path csv,out;bool sweep=false,shippingProjected=false,validateProjected=false;std::string vehicle="safari";Config config;
    for(int i=1;i<argc;++i){std::string a=argv[i];auto next=[&](){if(i+1==argc)throw std::runtime_error("Missing value for "+a);return std::string(argv[++i]);};
        if(a=="--csv")csv=next();else if(a=="--out")out=next();else if(a=="--vehicle")vehicle=next();else if(a=="--sweep")sweep=true;else if(a=="--contact-torque")config.contactTorque=true;else if(a=="--coupled-bump")config.coupledBump=true;else if(a=="--projected")shippingProjected=true;else if(a=="--validate-projected")validateProjected=true;
        else if(a=="--cg")config.cg=std::stof(next());else if(a=="--spring")config.spring=std::stof(next());else if(a=="--compression")config.compression=std::stof(next());else if(a=="--rebound")config.rebound=std::stof(next());else if(a=="--antiroll")config.antiRoll=std::stof(next());else if(a=="--roll-inertia")config.rollI=std::stof(next());else if(a=="--pitch-inertia")config.pitchI=std::stof(next());
        else throw std::runtime_error("Unknown argument: "+a);}
    if(csv.empty())throw std::runtime_error("Usage: safari_dynamics_probe --csv ride.csv [--out prefix] [--vehicle safari|buggy] [--sweep] [--cg metres --spring N/m --compression Ns/m --rebound Ns/m --antiroll N/m]");
    if(vehicle!="safari"&&vehicle!="buggy")throw std::runtime_error("Unknown vehicle");const auto dims=vehicle=="safari"?rally::safariDimensions:rally::buggyDimensions;auto inputs=readInputs(csv);
    Config defaults;auto height=[&](float x,float z){return terrain(x,z,defaults);};
    auto validate=[&](rally::RideContactResponse response){rally::RideDynamics real;ExperimentalRide clone;clone.config.contactTorque=clone.config.coupledBump=response==rally::RideContactResponse::Projected;
        real.reset(Vector3(0,0,90),3.14159265359f/2,height,dims,response);clone.reset(Vector3(0,0,90),3.14159265359f/2,height,dims);float divergence=0;
        for(const auto& in:inputs){Vector3 p(in.x,0,in.z);real.step(p,in.heading,in.steer,in.acceleration,in.lateral,in.dt,height);clone.step(p,in.heading,in.steer,in.acceleration,in.lateral,in.dt,height);
            divergence=std::max({divergence,real.chassis.distanceTo(clone.chassis),std::abs(real.roll-clone.roll),std::abs(real.pitch-clone.pitch),std::abs(real.heaveVelocity-clone.heaveVelocity),std::abs(real.pitchVelocity-clone.pitchVelocity),std::abs(real.rollVelocity-clone.rollVelocity)});
            for(int i=0;i<4;++i){divergence=std::max({divergence,std::abs(real.travel[i]-clone.travel[i]),std::abs(real.previousTravel[i]-clone.previousTravel[i]),std::abs(real.forces[i]-clone.forces[i])});if(real.grounded[i]!=clone.grounded[i])throw std::runtime_error("Diagnostic clone has divergent contact flags");}
            if(real.bumpCorrections!=clone.bumpCorrections)throw std::runtime_error("Diagnostic clone has divergent hard-stop count");}
        std::cerr<<(response==rally::RideContactResponse::Projected?"Projected":"Legacy")<<" diagnostic clone max state divergence="<<divergence<<"; CPU only.\n";if(divergence>1e-6f)throw std::runtime_error("Diagnostic clone diverged from RideDynamics");};
    validate(rally::RideContactResponse::Legacy);if(validateProjected||shippingProjected)validate(rally::RideContactResponse::Projected);
    std::ofstream summary,detail;if(!out.empty()){summary.open(out.string()+".jsonl");detail.open(out.string()+".csv");detail<<std::setprecision(9);}
    auto emit=[&](const Config& c,const Stats& s){printStats(std::cout,c,s);if(summary)printStats(summary,c,s);};
    rally::RideDynamics baseline;Config baselineConfig=defaults;if(shippingProjected)baselineConfig.name="shipping-projected";emit(baselineConfig,replay(inputs,dims,baselineConfig,baseline,detail?&detail:nullptr,shippingProjected?rally::RideContactResponse::Projected:rally::RideContactResponse::Legacy));
    if(config.cg!=defaults.cg||config.spring!=defaults.spring||config.compression!=defaults.compression||config.rebound!=defaults.rebound||config.antiRoll!=defaults.antiRoll||config.rollI!=defaults.rollI||config.pitchI!=defaults.pitchI||config.contactTorque||config.coupledBump){config.name="custom";ExperimentalRide trial;trial.config=config;emit(config,replay(inputs,dims,config,trial));}
    if(sweep){for(const auto& name:{"no-lateral","no-longitudinal","no-inertial","no-ripple","flat","contact-torque","coupled-bump","contact-torque-coupled-bump"}){Config c;c.name=name;c.noLateral=c.name=="no-lateral"||c.name=="no-inertial";c.noLongitudinal=c.name=="no-longitudinal"||c.name=="no-inertial";c.noRipple=c.name=="no-ripple";c.flat=c.name=="flat";c.contactTorque=c.name=="contact-torque"||c.name=="contact-torque-coupled-bump";c.coupledBump=c.name=="coupled-bump"||c.name=="contact-torque-coupled-bump";ExperimentalRide trial;trial.config=c;emit(c,replay(inputs,dims,c,trial));}}
    return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
