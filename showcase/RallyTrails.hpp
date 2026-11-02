#pragma once
#include "RallyVehicle.hpp"
#include "threepp/materials/ShaderMaterial.hpp"
#include "threepp/geometries/IcosahedronGeometry.hpp"

namespace rally {
struct TrailSegment {float age=99,strength=0;};
struct TyreTrails {
    static constexpr int capacity=768;
    std::array<TrailSegment,capacity> segments;
    std::array<Vector3,4> previous{};
    std::array<bool,4> connected{};
    std::shared_ptr<Mesh> mesh;
    unsigned emitted=0;int next=0;
    TyreTrails(){auto g=BufferGeometry::create();
        g->setAttribute("position",FloatBufferAttribute::create(std::vector<float>(capacity*18),3));
        g->setAttribute("uv",FloatBufferAttribute::create(std::vector<float>(capacity*12),2));
        g->setAttribute("strength",FloatBufferAttribute::create(std::vector<float>(capacity*6),1));
        auto m=ShaderMaterial::create();m->transparent=true;m->depthWrite=false;m->side=Side::Double;
        m->vertexShader=R"(varying vec2 vUv;varying float vStrength;attribute float strength;
void main(){vUv=uv;vStrength=strength;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);})";
        m->fragmentShader=R"(varying vec2 vUv;varying float vStrength;
void main(){float edge=smoothstep(0.,.15,vUv.x)*(1.-smoothstep(.85,1.,vUv.x));
float blocks=mix(.42,1.,step(.30,fract(vUv.y*11.+step(.5,vUv.x)*.45)));
float groove=mix(.52,1.,step(.08,abs(fract(vUv.x*4.)-.5)));
float alpha=vStrength*edge*blocks*groove;if(alpha<.003)discard;
gl_FragColor=vec4(.14,.105,.065,alpha);
#include <tonemapping_fragment>
#include <encodings_fragment>
})";
        mesh=Mesh::create(g,m);mesh->frustumCulled=false;
    }
    void reset(){segments={};for(auto& s:segments)s.age=99;connected={};next=0;emitted=0;update(0);}
    void update(float dt){auto* alpha=mesh->geometry()->getAttribute<float>("strength");
        for(int i=0;i<capacity;++i){auto& s=segments[i];s.age+=dt;float fade=std::clamp((32-s.age)/8,0.f,1.f)*std::min(1.f,s.age/.06f);
            for(int v=0;v<6;++v)alpha->setX(i*6+v,s.strength*fade);}alpha->needsUpdate();}
    template<class Height> void contact(int wheel,const Vector3& p,bool touching,float strength,Height height){
        if(!touching){connected[wheel]=false;return;}
        if(!connected[wheel]){previous[wheel]=p;connected[wheel]=true;return;}
        auto d=p.clone().sub(previous[wheel]);d.y=0;float distance=d.length();if(distance<.25f)return;
        if(distance>2.4f){previous[wheel]=p;return;}
        auto side=Vector3(d.z,0,-d.x).multiplyScalar(.17f/distance);
        std::array<Vector3,4> corners={previous[wheel].clone().sub(side),previous[wheel].clone().add(side),p.clone().sub(side),p.clone().add(side)};
        for(auto& v:corners)v.y=height(v.x,v.z)+.040f;
        constexpr int order[]={0,2,1,1,2,3};auto* pos=mesh->geometry()->getAttribute<float>("position");auto* uv=mesh->geometry()->getAttribute<float>("uv");
        // World-distance UV prevents each segment from repeating one huge block.
        for(int k=0;k<6;++k){int c=order[k],v=next*6+k;pos->setXYZ(v,corners[c].x,corners[c].y,corners[c].z);uv->setXY(v,c%2?1.f:0.f,(c<2?0.f:distance));}
        segments[next]={0,std::clamp(strength,0.f,.45f)};next=(next+1)%capacity;++emitted;previous[wheel]=p;pos->needsUpdate();uv->needsUpdate();
    }
};
struct GravelParticle{Vector3 position,velocity;float age=2,life=1,size=.02f;bool bounced=false;};
struct GravelSpray{
    static constexpr int capacity=64;std::array<GravelParticle,capacity> particles;
    std::shared_ptr<InstancedMesh> mesh;int next=0;unsigned emitted=0;
    GravelSpray(){auto m=MeshStandardMaterial::create();m->color=Color(0x80705a);m->roughness=1;
        mesh=InstancedMesh::create(IcosahedronGeometry::create(1,0),m,capacity);mesh->frustumCulled=false;draw();}
    void reset(){for(auto& p:particles)p.age=2;next=0;emitted=0;draw();}
    void spawn(const Vector3& contact,const Vector3& forward,const Vector3& right,const Vector3& motion,float activity){
        auto& p=particles[next];next=(next+1)%capacity;float seed=std::fmod(++emitted*.61803399f,1.f);
        p.position=contact.clone().add(Vector3(0,.04f,0));p.velocity=motion.clone().multiplyScalar(.13f).addScaledVector(forward,-2.4f-activity*2).addScaledVector(right,(seed-.5f)*3);
        p.velocity.y=1.1f+seed*1.7f;p.age=0;p.life=.55f+seed*.35f;p.size=.012f+seed*.018f;p.bounced=false;
    }
    template<class Height> void update(float dt,Height height){for(auto& p:particles)if(p.age<p.life){p.age+=dt;p.velocity.y-=9.81f*dt;p.position.addScaledVector(p.velocity,dt);
            float floor=height(p.position.x,p.position.z)+p.size;if(p.position.y<floor){p.position.y=floor;if(p.bounced)p.age=p.life;else{p.velocity.y=std::abs(p.velocity.y)*.22f;p.velocity.x*=.45f;p.velocity.z*=.45f;p.bounced=true;}}}draw();}
    void draw(){Object3D stone;for(int i=0;i<capacity;++i){auto& p=particles[i];stone.position.copy(p.position);stone.rotation.set(p.age*8,i*.7f,p.age*5);stone.scale.setScalar(p.age<p.life?p.size:0);stone.updateMatrix();mesh->setMatrixAt(i,*stone.matrix);}mesh->instanceMatrix()->needsUpdate();}
};
}
