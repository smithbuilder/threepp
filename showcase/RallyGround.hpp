#pragma once

#include "threepp/core/BufferGeometry.hpp"
#include "threepp/extras/core/NoiseUtils.hpp"
#include "threepp/materials/MeshStandardMaterial.hpp"
#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <vector>

namespace rally {

// Opt-in Safari dressing. Geometry positions, triangle indices and collision
// surfaces never change. All variation is baked once into the existing vertex
// colour/UV attributes, so it adds no per-frame noise, draw call or render pass.
struct SafariGroundReport {
    unsigned terrainVertices{}, roadVertices{};
    float routeLength{}, roadTileMetres{}, forestTileMetres=3.2f;
};

inline float safariGroundSmooth(float a,float b,float x){
    const float t=std::clamp((x-a)/(b-a),0.f,1.f);
    return t*t*(3.f-2.f*t);
}

// Broad 3.5-9m material patches break visible repetition without enlarging scans.
// The same world field reaches both surfaces and has no road-segment seam.
inline float safariGroundMacro(float x,float z){
    return .65f*threepp::noise::valueNoise(x*.11f,z*.11f,256,481)
          +.35f*threepp::noise::valueNoise(x*.28f,z*.28f,256,719);
}

template<class LoadTexture,class Nearest>
inline SafariGroundReport configureSafariGround(
        threepp::BufferGeometry& land,threepp::BufferGeometry& road,
        threepp::MeshStandardMaterial& forest,threepp::MeshStandardMaterial& dirt,
        LoadTexture loadTexture,Nearest nearest,unsigned across=8){
    using namespace threepp;
    auto* lp=land.getAttribute<float>("position");
    auto* rp=road.getAttribute<float>("position");
    auto* ru=road.getAttribute<float>("uv");
    const unsigned stride=across+1;
    if(!lp||!rp||!ru||ru->count()!=rp->count()||across<2||rp->count()%stride||rp->count()<2*stride)
        throw std::runtime_error("Safari ground requires the existing indexed road ribbon");

    SafariGroundReport report;
    report.terrainVertices=lp->count();report.roadVertices=rp->count();
    const unsigned rows=rp->count()/stride;
    std::vector<Vector3> centers;centers.reserve(rows);
    std::vector<float> distance(rows,0.f);
    for(unsigned row=0;row<rows;++row){
        const unsigned a=row*stride,b=a+across;
        centers.emplace_back((rp->getX(a)+rp->getX(b))*.5f,
                             (rp->getY(a)+rp->getY(b))*.5f,
                             (rp->getZ(a)+rp->getZ(b))*.5f);
        if(row)distance[row]=distance[row-1]+centers[row].distanceTo(centers[row-1]);
    }
    report.routeLength=distance.back();
    if(!(report.routeLength>1.f))throw std::runtime_error("Degenerate Safari road");
    // Poly Haven's source dimensions: gravel_road is 2m; forest_ground_04 3.2m.
    // Closing on a whole tile eliminates the lap seam. Arc length replaces the
    // old ring-index UV, whose stretch changed with the course's sampling speed.
    const float tiles=std::max(1.f,std::round(report.routeLength/2.f));
    report.roadTileMetres=report.routeLength/tiles;
    std::vector<float> roadColor;roadColor.reserve(rp->count()*3);
    for(unsigned row=0;row<rows;++row){
        const unsigned first=row*stride;
        const Vector3 edge(rp->getX(first),rp->getY(first),rp->getZ(first));
        const float v=distance[row]/report.roadTileMetres;
        for(unsigned j=0;j<stride;++j){
            const unsigned i=first+j;
            const Vector3 p(rp->getX(i),rp->getY(i),rp->getZ(i));
            const float acrossMetres=p.distanceTo(edge);
            // Tile every 2m across as well as along, rather than stretching
            // each scan over a 3.7m width and roughly 7-9m road distance.
            ru->setXY(i,acrossMetres/2.f,v);
            const float signedSide=(static_cast<float>(j)/across*2.f-1.f)*3.7f;
            const float macro=safariGroundMacro(p.x,p.z);
            const float scatter=noise::valueNoise(p.x*.43f,p.z*.43f,256,337);
            const float edgeStart=2.18f+.70f*(scatter-.5f);
            const float shoulder=safariGroundSmooth(edgeStart,3.65f,std::abs(signedSide));
            // A broad dry centre ridge and two compacted tyre lanes. These
            // remain albedo variation, not fake raised ruts or collision work.
            const float wander=.06f*std::sin(distance[row]*.21f);
            const float lane=std::exp(-std::pow((std::abs(signedSide)-.88f-wander)/.46f,2.f));
            const float dry=safariGroundSmooth(.28f,.72f,macro);
            const float value=(.59f+.44f*dry)*(1-.22f*lane);
            const Color driven(value*.97f,value*.99f,value);
            const Color litter(value*.67f,value*.82f,value*.68f);
            Color c; c.lerpColors(driven,litter,shoulder);
            roadColor.insert(roadColor.end(),{c.r,c.g,c.b});
        }
    }
    ru->needsUpdate();
    road.setAttribute("color",FloatBufferAttribute::create(roadColor,3));

    std::vector<float> forestColor;forestColor.reserve(lp->count()*3);
    const auto* normals=land.getAttribute<float>("normal");
    for(unsigned i=0;i<lp->count();++i){
        const Vector3 p(lp->getX(i),lp->getY(i),lp->getZ(i));
        const auto center=nearest(p).p;
        const float roadDistance=std::hypot(p.x-center.x,p.z-center.z);
        const float macro=safariGroundMacro(p.x,p.z);
        const float moisture=noise::valueNoise(p.x*.12f,p.z*.12f,256,211);
        const float steep=normals?1.f-std::abs(normals->getY(i)):0.f;
        const float bank=safariGroundSmooth(.12f,.40f,steep);
        const float trackside=1.f-safariGroundSmooth(3.f,9.f,roadDistance);
        const float dry=safariGroundSmooth(.25f,.75f,macro);
        const Color damp(.43f,.50f,.36f),dryEarth(1.04f,.98f,.83f);
        Color earth;earth.lerpColors(damp,dryEarth,dry);
        const Color mineral(.90f,.94f,.89f);
        Color c;c.lerpColors(earth,mineral,std::clamp(bank*.65f+trackside*.12f,0.f,1.f));
        const float mottling=1.f-.09f*moisture;c.multiplyScalar(mottling);
        forestColor.insert(forestColor.end(),{c.r,c.g,c.b});
    }
    land.setAttribute("color",FloatBufferAttribute::create(forestColor,3));
    forest.vertexColors=dirt.vertexColors=true;
    forest.roughness=.99f;dirt.roughness=.98f;
    forest.metalness=dirt.metalness=0;
    forest.normalScale.set(.42f,.42f);dirt.normalScale.set(.47f,.47f);
    // Native PBR green-channel maps, matched to the exact existing scan sets.
    // They are data (linear), not colour. No guessed albedo-to-roughness proxy.
    forest.roughnessMap=loadTexture("library/materials/forest-floor/roughness_1k.jpg",false);
    dirt.roughnessMap=loadTexture("library/materials/gravel-road/roughness_1k.jpg",false);
    for(auto* t:{forest.map.get(),forest.normalMap.get(),forest.roughnessMap.get()})
        if(t)t->repeat.setScalar(520.f/report.forestTileMetres);
    for(auto* t:{dirt.map.get(),dirt.normalMap.get(),dirt.roughnessMap.get()})
        if(t)t->repeat.set(1,1);
    forest.name="safari.forest-floor-v2";dirt.name="safari.graded-gravel-v2";
    return report;
}

} // namespace rally
