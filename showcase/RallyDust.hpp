#pragma once
#include "threepp/threepp.hpp"
#include "threepp/materials/ShaderMaterial.hpp"
#include <array>
#include <cmath>
#include <algorithm>

namespace rally {
using namespace threepp;
struct DustParticle {Vector3 position,velocity;float age=2,life=1,seed=0;};
struct DustSimulation {
    static constexpr int capacity=96;
    std::array<DustParticle,capacity> particles;
    int next=0;unsigned serial=0;float distance=0;
    void reset(){*this=DustSimulation{};}
    void spawn(Vector3 contact,Vector3 forward,Vector3 right,Vector3 motion,float speed,float side){
        auto& p=particles[next];next=(next+1)%capacity;
        p.seed=std::fmod(++serial*.61803398875f,1.f);p.position=contact.add(Vector3(0,.07f,0));
        p.velocity=motion.multiplyScalar(.08f).addScaledVector(forward,-.8f-speed*.1f).addScaledVector(right,side*(.4f+p.seed*.35f));
        p.velocity.add(Vector3(.4f,.45f+p.seed*.25f,.15f));p.age=0;p.life=.85f+p.seed*.4f;
    }
    void update(float dt){for(auto& p:particles)if(p.age<p.life){p.age+=dt;
        p.position.addScaledVector(p.velocity,dt);p.velocity.x+=(.45f-p.velocity.x)*(1-std::exp(-.8f*dt));
        p.velocity.z+=(.2f-p.velocity.z)*(1-std::exp(-.8f*dt));p.velocity.y+=.08f*dt;}}
    static float opacity(const DustParticle& p){float t=p.age/p.life;return t>=1?0.f:.105f*std::min(1.f,p.age/.09f)*(1-t)*(1-t);}
};
inline auto makeDustMesh(){
    auto m=ShaderMaterial::create();m->transparent=true;m->depthWrite=false;m->side=Side::Double;
    m->vertexShader=R"(
varying vec2 vUv;varying float vOpacity;varying float vSeed;
void main(){vUv=uv;vOpacity=instanceColor.r;vSeed=instanceColor.g;
gl_Position=projectionMatrix*modelViewMatrix*instanceMatrix*vec4(position,1.0);})";
    m->fragmentShader=R"(
varying vec2 vUv;varying float vOpacity;varying float vSeed;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float noise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.0-2.0*f);return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+1.0),f.x),f.y);}
void main(){vec2 p=(vUv-.5)*2.0;float edge=1.0-smoothstep(.15,1.0,dot(p,p));
float wisps=.5+.5*noise(p*3.5+vSeed*17.0);float alpha=vOpacity*edge*wisps;
if(alpha<.002)discard;gl_FragColor=vec4(.56,.45,.32,alpha);
#include <tonemapping_fragment>
#include <encodings_fragment>
})";
    auto mesh=InstancedMesh::create(PlaneGeometry::create(1,1),m,DustSimulation::capacity);mesh->frustumCulled=false;
    for(int i=0;i<DustSimulation::capacity;++i)mesh->setColorAt(i,Color(0,0,0));return mesh;
}
inline void drawDust(InstancedMesh& mesh,const DustSimulation& simulation,const Quaternion& camera){
    Object3D puff;for(int i=0;i<DustSimulation::capacity;++i){const auto& p=simulation.particles[i];float t=p.age/p.life,alpha=DustSimulation::opacity(p);
        puff.position.copy(p.position);puff.quaternion.copy(camera);Quaternion spin;spin.setFromAxisAngle(Vector3(0,0,1),p.seed*6.2831853f+p.age*.22f);puff.quaternion.multiply(spin);
        puff.scale.setScalar(alpha>0?.26f+std::min(t,1.f)*1.25f:0);puff.updateMatrix();mesh.setMatrixAt(i,*puff.matrix);mesh.setColorAt(i,Color(alpha,p.seed,0));}
    mesh.instanceMatrix()->needsUpdate();mesh.instanceColor()->needsUpdate();
}
}
