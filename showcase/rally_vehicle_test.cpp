// CPU-only checks against the actual rendered model and particle simulation.
#include "RallyBuggy.hpp"
#include "RallyDust.hpp"
#include "RallyCamera.hpp"
#include <iostream>
#include <stdexcept>
#include <regex>
#include "threepp/renderers/shaders/ShaderChunk.hpp"
using namespace threepp;

void require(bool condition,const std::string& message){if(!condition)throw std::runtime_error(message);}
int main(){try{
    auto dustMesh=rally::makeDustMesh();auto shader=dustMesh->material()->as<ShaderMaterial>();
    const std::regex include("#include +<([\\w.]+)>");
    for(const auto& source:{shader->vertexShader,shader->fragmentShader})for(auto i=std::sregex_iterator(source.begin(),source.end(),include);i!=std::sregex_iterator();++i)
        require(!threepp::shaders::ShaderChunk::instance().get((*i)[1].str()).empty(),"Dust shader includes missing chunk");
    auto buggy=rally::makeBuggy();auto boxes=rally::fixedBounds(buggy);float minClear=1e6f;
    for(int i=0;i<4;++i){auto envelope=rally::sweptTyreEnvelope(i);auto lo=envelope.min(),hi=envelope.max();
        for(size_t j=0;j<boxes.size();++j){require(!envelope.intersectsBox(boxes[j]),"Tyre swept envelope intersects fixed body mesh "+std::to_string(j));
            auto gap=[](float a,float b,float c,float d){return std::max({0.f,a-d,c-b});};
            float x=gap(lo.x,hi.x,boxes[j].min().x,boxes[j].max().x),y=gap(lo.y,hi.y,boxes[j].min().y,boxes[j].max().y),z=gap(lo.z,hi.z,boxes[j].min().z,boxes[j].max().z);
            minClear=std::min(minClear,std::sqrt(x*x+y*y+z*z));}
    }
    require(minClear>.025f,"Insufficient tyre/body clearance");
    float maxGap=0;
    for(int k=0;k<360;++k){float a=k*6.2831853f/360;float x=64*std::sin(a)+8*std::sin(3*a),z=90*std::cos(a);
        float dx=64*std::cos(a)+24*std::cos(3*a),dz=-90*std::sin(a),heading=std::atan2(dx,dz);
        Vector3 f(std::sin(heading),0,std::cos(heading)),r(std::cos(heading),0,-std::sin(heading));std::array<float,4> h;
        for(int i=0;i<4;++i){auto p=rally::wheelAnchor(i);h[i]=rally::height(x+r.x*p.x+f.x*p.z,z+r.z*p.x+f.z*p.z);}
        float pitch=-std::atan2((h[0]+h[1]-h[2]-h[3])*.5f,2*rally::halfWheelbase),roll=std::atan2((h[1]+h[3]-h[0]-h[2])*.5f,2*rally::halfTrack);
        auto q=rally::chassisOrientation(heading,pitch,roll);Vector3 chassis(x,(h[0]+h[1]+h[2]+h[3])*.25f+.13f,z);
        rally::constrainRide(chassis,q,.4f,rally::height);
        for(int i=0;i<4;++i){auto c=rally::wheelContact(i,chassis,q,.4f,rally::height);maxGap=std::max(maxGap,std::abs(c.gap));
            require(std::isfinite(c.gap)&&std::abs(c.gap)<.025f,"Tyre contact lost on course sample "+std::to_string(k));
            require(c.local.y>=rally::droop&&c.local.y<=rally::bump,"Suspension exceeded travel");}
    }
    std::vector<float> referenceLengths;std::array<rally::WheelContact,4> articulation;
    for(int i=0;i<4;++i)articulation[i].local=rally::hubAtTravel(i,.41f);
    rally::updateSuspension(buggy.suspension,articulation,0);
    for(auto& arm:buggy.suspension.arms)referenceLengths.push_back(arm.mesh->scale.y);
    float longest=0,shortest=10;
    for(int step=0;step<=52;++step){float travel=rally::droop+step*.01f;
        for(int i=0;i<4;++i)articulation[i].local=rally::hubAtTravel(i,travel);
        rally::updateSuspension(buggy.suspension,articulation,.4f);
        for(size_t i=0;i<referenceLengths.size();++i)require(std::abs(buggy.suspension.arms[i].mesh->scale.y-referenceLengths[i])<.00001f,"Wishbone changes length through travel");
        for(auto& shock:buggy.suspension.shocks){longest=std::max(longest,shock.length);shortest=std::min(shortest,shock.length);
            require(shock.barrel->scale.y==1,"Damper barrel stretches");
            auto* p=shock.spring->geometry()->getAttribute<float>("position");int ring=42*rally::coilSides;
            Vector3 a(p->getX(ring),p->getY(ring),p->getZ(ring)),b(p->getX(ring+3),p->getY(ring+3),p->getZ(ring+3));
            require(std::abs(a.distanceTo(b)-2*rally::wireRadius)<.00001f,"Spring wire thickness changes under compression");
            require((shock.length-.16f)/rally::coilTurns>2*rally::wireRadius,"Spring coils intersect");}
    }
    require(longest-shortest>.25f,"Coilover does not articulate");
    require(std::abs(rally::steeringAngle(1,.4f))>std::abs(rally::steeringAngle(0,.4f)),"Inside wheel lacks Ackermann steering");
    const auto screenRight=Vector3(0,0,1).cross(Vector3(0,1,0));
    float rightTurn=rally::steerInput(false,true)*.1f,leftTurn=rally::steerInput(true,false)*.1f;
    require(Vector3(std::sin(rightTurn),0,std::cos(rightTurn)).dot(screenRight)>0,"Right input turns left in cockpit");
    require(Vector3(std::sin(leftTurn),0,std::cos(leftTurn)).dot(screenRight)<0,"Left input turns right in cockpit");
    for(auto& box:boxes)require(!box.containsPoint(rally::driverEye()),"Cockpit eye lies inside bodywork");
    rally::CameraModes modes;for(int i=0;i<4;++i)modes.cycle();require(modes.view==0,"Camera cycle fails to wrap all four views");
    modes.cycle();modes.cycle();modes.toggleCockpit();require(modes.view==3,"Cockpit shortcut fails");modes.toggleCockpit();require(modes.view==2,"Cockpit shortcut loses prior exterior mode");
    for(float heading:{-3.f,0.f,2.f}){auto q=rally::chassisOrientation(heading,.25f,.3f);Vector3 origin(8,3,-9);auto pose=rally::cockpitPose(origin,q);
        auto local=pose.eye.clone().sub(origin).applyQuaternion(q.clone().invert());require(local.distanceTo(rally::driverEye())<.00001f,"Cockpit camera drifts out of seat");require(std::abs(pose.up.length()-1)<.00001f,"Cockpit up vector invalid");}
    rally::DustSimulation dust;dust.spawn(Vector3(0,0,0),Vector3(0,0,1),Vector3(1,0,0),Vector3(0,0,18),18,1);
    auto start=dust.particles[0].position;for(int i=0;i<36;++i)dust.update(1.f/120);
    require(dust.particles[0].position.distanceTo(start)>.25f,"Dust remains fixed in world space");
    require(rally::DustSimulation::opacity(dust.particles[0])>0,"Dust never becomes visible");
    rally::drawDust(*dustMesh,dust,Quaternion());Matrix4 renderedA,renderedB;dustMesh->getMatrixAt(0,renderedA);Color alphaA,alphaB;dustMesh->getColorAt(0,alphaA);
    for(int i=0;i<24;++i)dust.update(1.f/120);rally::drawDust(*dustMesh,dust,Quaternion());dustMesh->getMatrixAt(0,renderedB);dustMesh->getColorAt(0,alphaB);
    require(std::abs(renderedA.elements[14]-renderedB.elements[14])>.05f,"Dust simulation moves but render transform stays fixed");
    require(alphaB.r<alphaA.r&&alphaB.r>0,"Rendered dust opacity fails to fade with age");
    for(int i=0;i<180;++i)dust.update(1.f/120);
    require(rally::DustSimulation::opacity(dust.particles[0])==0,"Dust fails to expire");dust.reset();
    require(dust.serial==0&&rally::DustSimulation::opacity(dust.particles[0])==0,"Restart leaves old dust");
    std::cout<<"PASS: swept tyre/body clearance="<<minClear<<"m; 360 course poses max contact gap="<<maxGap<<"m; rigid wishbones, constant-wire coilovers, Ackermann steering and seated camera pass; dust advects/fades/resets. No graphics/audio context opened.\n";
    return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
