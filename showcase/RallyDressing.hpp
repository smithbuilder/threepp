#pragma once
#include "RallyGround.hpp"
#include "threepp/extras/vegetation/GrassField.hpp"
#include "threepp/loaders/OBJLoader.hpp"
#include "threepp/scenes/Scene.hpp"
#include <filesystem>
#include <random>

namespace rally {

struct SafariDressingReport {unsigned blades=0,tufts=0,rocks=0,rockTriangles=0;float minimumGrassRoadDistance=1e9f;};

inline void safariDressingReplace(std::string& source,const std::string& anchor,const std::string& replacement){
    const auto at=source.find(anchor);
    if(at==std::string::npos||source.find(anchor,at+anchor.size())!=std::string::npos)
        throw std::runtime_error("Safari grass adapter shader anchor changed");
    source.replace(at,anchor.size(),replacement);
}

// Renderer adapter only: the reusable grass geometry stays unchanged. Existing
// instancing colours select dry/olive clusters in one draw, without an atlas or
// extra shader pass. The existing wind/fog/output encoding remains in charge.
inline void safariDressingGrassPalette(threepp::GrassField& grass){
    using namespace threepp;
    auto& material=grass.windMaterial();
    if(material.name=="safari.shoulder-tufts")return;
    material.name="safari.shoulder-tufts";
    material.vertexShader="varying vec3 vSafariTuftColor;\n"+material.vertexShader;
    safariDressingReplace(material.vertexShader,"vHeight = uv.y;",R"GLSL(vHeight = uv.y;
#ifdef USE_INSTANCING_COLOR
                    vSafariTuftColor = instanceColor;
#else
                    vSafariTuftColor = vec3(1.0);
#endif
)GLSL");
    material.fragmentShader="varying vec3 vSafariTuftColor;\n"+material.fragmentShader;
    safariDressingReplace(material.fragmentShader,"vec3 base = mix(bottomColor, topColor, vHeight);",
        "vec3 base = mix(bottomColor, topColor, vHeight) * vSafariTuftColor;");
    material.uniforms.at("topColor").setValue(Vector3(.34f,.33f,.19f));
    material.uniforms.at("bottomColor").setValue(Vector3(.065f,.085f,.035f));
    grass.setWind(.105f,{.8f,.6f});material.needsUpdate();
}

// Called immediately after dress(), only for Safari. The same 9,000 blades are
// distributed as 1,000 irregular shoulder tufts, leaving the driven road clear.
// Trees, obstacles, collider records and every rock instance transform survive.
// The fieldstone is a portable, authored OBJ; this adapter never generates it.
template<class Track,class Nearest,class Height>
inline SafariDressingReport refineSafariDressing(threepp::Scene& scene,size_t firstChild,
        Track track,Nearest nearest,Height height,const std::filesystem::path& fieldstonePath,
        const threepp::MeshStandardMaterial& forestSurface){
    using namespace threepp;
    SafariDressingReport report;
    GrassField* grass=nullptr;InstancedMesh* rocks=nullptr;
    for(size_t i=firstChild;i<scene.children.size();++i){
        if(auto* candidate=dynamic_cast<GrassField*>(scene.children[i]);candidate&&candidate->count()==9000)grass=candidate;
        else if(auto* candidate=dynamic_cast<InstancedMesh*>(scene.children[i]);candidate&&candidate->count()==150)rocks=candidate;
    }
    if(!grass||!rocks)throw std::runtime_error("Safari dressing expects the bounded9000-blade/150-rock pools");
    std::mt19937 rng(24017);std::uniform_real_distribution<float> unit(0,1);
    constexpr float tau=6.28318530718f;
    for(unsigned tuft=0;tuft<1000;++tuft){
        Vector3 center,side,forward;
        for(int attempt=0;attempt<40;++attempt){
            const float a=unit(rng)*tau;
            center=track(a);forward=track(a+.002f).sub(center).normalize();side={forward.z,0,-forward.x};
            const float distance=unit(rng)<.72f?4.35f+std::pow(unit(rng),1.5f)*3.2f:7.f+unit(rng)*10.f;
            center.addScaledVector(side,(tuft%2?1.f:-1.f)*distance);
            const auto n=nearest(center).p;
            if(std::hypot(center.x-n.x,center.z-n.z)>4.2f)break;
        }
        const float dry=safariGroundSmooth(.28f,.72f,safariGroundMacro(center.x,center.z));
        const float tuftHeight=.27f+.45f*unit(rng),radius=.17f+.20f*unit(rng);
        const Color olive(.67f,.91f,.59f),straw(1.12f,.96f,.63f);
        Color tint;tint.lerpColors(olive,straw,dry);
        for(unsigned blade=0;blade<9;++blade){
            Vector3 p=center;
            const float angle=blade*tau/9.f+unit(rng)*.35f,r=std::sqrt(unit(rng))*radius;
            p.x+=r*std::cos(angle);p.z+=r*std::sin(angle);
            auto n=nearest(p).p;float distance=std::hypot(p.x-n.x,p.z-n.z);
            if(distance<3.85f){
                Vector3 outward(p.x-n.x,0,p.z-n.z);outward.normalize();
                p.addScaledVector(outward,3.85f-distance);n=nearest(p).p;
                distance=std::hypot(p.x-n.x,p.z-n.z);
            }
            p.y=height(p.x,p.z)+.012f;
            Object3D o;o.position.copy(p);o.rotation.set((unit(rng)-.5f)*.23f,angle,(unit(rng)-.5f)*.20f);
            o.scale.set(.15f+.13f*unit(rng),tuftHeight*(.7f+.55f*unit(rng)),1);
            o.updateMatrix();const unsigned i=tuft*9+blade;grass->setMatrixAt(i,*o.matrix);
            grass->setColorAt(i,tint);report.minimumGrassRoadDistance=std::min(report.minimumGrassRoadDistance,distance);
        }
    }
    grass->instanceMatrix()->needsUpdate();grass->instanceColor()->needsUpdate();
    safariDressingGrassPalette(*grass);grass->boundingSphere.reset();grass->boundingBox.reset();
    report.blades=9000;report.tufts=1000;

    auto asset=OBJLoader{}.load(fieldstonePath,false);
    std::shared_ptr<BufferGeometry> boulder;
    if(asset)asset->traverseType<Mesh>([&](Mesh& mesh){if(!boulder)boulder=mesh.geometry()->clone();});
    if(!boulder)throw std::runtime_error("Cannot load portable fieldstone OBJ");
    report.rockTriangles=boulder->hasIndex()?boulder->getIndex()->count()/3:boulder->getAttribute<float>("position")->count()/3;
    if(report.rockTriangles>70)throw std::runtime_error("Fieldstone exceeds the existing rock triangle budget");
    auto* uv=boulder->getAttribute<float>("uv");
    if(!uv||!forestSurface.map||!forestSurface.normalMap||!forestSurface.roughnessMap)
        throw std::runtime_error("Portable fieldstone requires UVs and the existing forest PBR binding");
    // Share the very same scan textures/storage. Compensate for the floor's
    // large texture transform in the adapter UVs, instead of duplicating maps.
    const auto repeat=forestSurface.map->repeat;
    for(unsigned i=0;i<uv->count();++i)uv->setXY(i,uv->getX(i)*2.f/repeat.x,uv->getY(i)*.52f/repeat.y);
    uv->needsUpdate();
    auto stone=MeshStandardMaterial::create();stone->name="safari.fieldstone";stone->color=Color(1.10f,1.13f,1.10f);
    stone->map=forestSurface.map;stone->normalMap=forestSurface.normalMap;stone->roughnessMap=forestSurface.roughnessMap;
    stone->normalScale.set(.65f,.65f);stone->roughness=.97f;stone->metalness=0;
    rocks->setGeometry(boulder);rocks->setMaterial(stone);rocks->name="safari.fieldstone-pool";
    for(unsigned i=0;i<150;++i){const float v=.72f+.38f*unit(rng);rocks->setColorAt(i,Color(v,v*(.98f+.05f*unit(rng)),v*.96f));}
    rocks->instanceColor()->needsUpdate();rocks->boundingSphere.reset();rocks->boundingBox.reset();report.rocks=150;
    return report;
}

} // namespace rally
