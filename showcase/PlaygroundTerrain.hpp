#pragma once
#include "threepp/math/Vector3.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <vector>

namespace playground {
using threepp::Vector3;
inline float smooth(float a,float b,float x){float t=std::clamp((x-a)/(b-a),0.f,1.f);return t*t*(3-2*t);}
inline float window(float a,float b,float c,float d,float x){return smooth(a,b,x)*(1-smooth(c,d,x));}
enum class TrialKind { Drive, Jumps, Wind };
struct Station{const char* name;const char* description;float x,z,yaw;TrialKind kind=TrialKind::Drive;float defaultSpeed=2.2f,endZ=102;};
inline constexpr std::array<Station,8> stations{{
    {"Level pad","Settle, brake, accelerate and compare body movement",-50,-10,0},
    {"Cross-axle ruts","Alternating 22 cm humps unload opposite corners",-50,18,0},
    {"Bumps and whoops","Short ripples followed by broad rolling bumps",-25,14,0},
    {"Steep climb / descent","32 degree climb, rounded crest and downhill braking",0,9,0},
    {"Narrow ridge","3.6 m crown with steep shoulders; choose your line",25,10,0},
    {"Side slope","22 degree traverse: watch load move to downhill tyres",50,18,0},
    {"Jump line","Two ramp jumps. Start around 35 km/h and watch the landings",-50,94,0,TrialKind::Jumps,10,183},
    {"Wind tunnel","Steady wind and gusts. Compare body roll and tyre loads",25,137,0,TrialKind::Wind,0,160}
}};
// Gantry posts and overhead beams: [centre xyz, half extents xyz]. The same
// recipe constructs visible meshes and solid Bullet collision shapes.
inline constexpr std::array<std::array<float,6>,8> windFrame{{
    {17,1.9f,131,.10f,1.9f,.10f},{33,1.9f,131,.10f,1.9f,.10f},
    {17,1.9f,143,.10f,1.9f,.10f},{33,1.9f,143,.10f,1.9f,.10f},
    {25,3.8f,131,8,.10f,.10f},{25,3.8f,143,8,.10f,.10f},
    {17,3.8f,137,.10f,.10f,6},{33,3.8f,137,.10f,.10f,6}
}};
// One sampled surface feeds BOTH the render mesh and Bullet triangle mesh.
// Physics never drives on an invisible smooth substitute for these trails.
struct Terrain {
    static constexpr int nx=264,nz=440;
    static constexpr float step=.5f,minX=-66,minZ=-24;
    std::vector<float> vertices;
    std::vector<unsigned> indices;
    static float trailCenter(int station,float z){return station==4?25+1.4f*std::sin((z-12)*.055f)*window(12,25,85,105,z):stations[station].x;}
    static float roundedRamp(float x){return x<=0?0:x<.7f?x*x/1.4f:x-.35f;}
    static float kicker(float z,float start,float lip,float h){return h*(roundedRamp(z-start)-roundedRamp(z-lip))/(lip-start)*(1-smooth(lip+.7f,lip+1.8f,z));}
    static float design(float x,float z){
        float y=.018f*std::sin(x*.37f)*std::sin(z*.41f)*window(5,12,100,114,z);
        float track=window(17,21,82,90,z);
        // Smooth wheel-sized features rather than discontinuous collision steps.
        for(int n=0;n<9;++n){float side=n%2?1.f:-1.f,zz=28+n*5.f;
            y+=.22f*std::exp(-std::pow((x+50-side*1.05f)/.75f,2)-std::pow((z-zz)/1.25f,2));}
        y-=.08f*track*std::exp(-std::pow((std::abs(x+50)-1.05f)/.36f,2));
        float lane=std::exp(-std::pow((x+25)/3.8f,8));
        y+=lane*(.055f*std::sin((z-20)*5.23599f)*window(16,20,36,40,z)
                 +.24f*std::sin((z-44)*.785398f)*window(40,45,82,90,z));
        float hill=13.f*smooth(12,43,z)*(1-smooth(49,83,z));
        y+=hill*std::exp(-std::pow(x/7.f,6));
        float ridge=10.f*smooth(12,43,z)*(1-smooth(70,102,z));
        float dx=std::abs(x-trailCenter(4,z)),shoulder=1-smooth(1.8f,8.f,dx);
        y+=ridge*shoulder;
        y+=(x-50)*.404f*std::exp(-std::pow((x-50)/6.5f,8))*window(20,34,78,93,z);
        float jumpLane=std::exp(-std::pow((x+50)/4.7f,8));
        y+=jumpLane*(kicker(z,110,114,1.3f)+.40f*smooth(120,123,z)*(1-smooth(123,134,z))
                    +kicker(z,150,156,2.5f)+.75f*smooth(163,167,z)*(1-smooth(167,181,z)));
        return y;
    }
    Terrain(){
        vertices.reserve((nx+1)*(nz+1)*3);
        for(int iz=0;iz<=nz;++iz)for(int ix=0;ix<=nx;++ix){float x=minX+ix*step,z=minZ+iz*step;vertices.insert(vertices.end(),{x,design(x,z),z});}
        indices.reserve(nx*nz*6);
        for(int iz=0;iz<nz;++iz)for(int ix=0;ix<nx;++ix){unsigned a=iz*(nx+1)+ix,b=a+1,c=a+nx+1,d=c+1;indices.insert(indices.end(),{a,c,b,b,c,d});}
    }
    Vector3 vertex(unsigned i)const{return {vertices[i*3],vertices[i*3+1],vertices[i*3+2]};}
    float height(float x,float z)const{
        float gx=std::clamp((x-minX)/step,0.f,float(nx)-.0001f),gz=std::clamp((z-minZ)/step,0.f,float(nz)-.0001f);
        int ix=int(gx),iz=int(gz);float u=gx-ix,v=gz-iz;unsigned a=iz*(nx+1)+ix;
        float h00=vertices[a*3+1],h10=vertices[(a+1)*3+1],h01=vertices[(a+nx+1)*3+1],h11=vertices[(a+nx+2)*3+1];
        return u+v<=1?h00+(h10-h00)*u+(h01-h00)*v:h11+(h01-h11)*(1-u)+(h10-h11)*(1-v);
    }
};
}
