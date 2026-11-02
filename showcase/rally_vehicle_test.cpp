// CPU-only checks against the actual rendered model and particle simulation.
#include "RallyBuggy.hpp"
#include "RallyDust.hpp"
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
    for(int i=0;i<4;++i){auto envelope=rally::tyreEnvelope(i,rally::droop,.4f);
        // Union of all available travel and all steering angles (including the
        // slightly larger fore/aft extent at an interior steering angle).
        float z=i<2?std::hypot(rally::tyreRadius,rally::tyreHalfWidth):rally::tyreRadius;
        auto a=rally::wheelAnchor(i);auto lo=envelope.min(),hi=envelope.max();lo.y=rally::droop-rally::tyreRadius;hi.y=rally::bump+rally::tyreRadius;lo.z=a.z-z;hi.z=a.z+z;envelope.set(lo,hi);
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
    std::cout<<"PASS: swept tyre/body clearance="<<minClear<<"m; 360 course poses max contact gap="<<maxGap<<"m; dust advects, fades, expires and resets. No graphics/audio context opened.\n";
    return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
