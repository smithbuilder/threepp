#pragma once
#include "RallyBuggy.hpp"
#include "threepp/loaders/GLTFLoader.hpp"
#include <filesystem>
#include <stdexcept>

namespace rally {
// Original dense coupe mesh, authored by scripts/generate-safari-body.py.
// Body transforms/normals are baked into the self-contained GLB. The live rig
// remains separate: suspension, brakes, tyre rotation and instruments animate.
inline Buggy makeSafari(const std::filesystem::path& assetDir=std::filesystem::path(__FILE__).parent_path()/"assets",const VehicleDimensions& dims=safariDimensions){
    Buggy b;b.dimensions=dims;b.eye={-.4f,1.43f,-.3f};b.car->add(b.body);
    const auto path=assetDir/"safari-body.glb";
    auto asset=GLTFLoader{}.load(path);
    if(!asset||!asset->scene)throw std::runtime_error("Cannot load Safari body: "+path.string());
    asset->scene->name="Cinder Safari original body";b.body->add(asset->scene);
    auto seat=surfaceMaterial(0x27302b,Surface::Rubber,.96f,0);
    for(float side:{-1.f,1.f}){
        auto cushion=Mesh::create(SphereGeometry::create(1,16,10),seat);cushion->position.set(side*.4f,.83f,-.40f);cushion->scale.set(.25f,.12f,.31f);b.body->add(cushion);
        auto back=Mesh::create(SphereGeometry::create(1,16,10),seat);back->position.set(side*.4f,1.14f,-.57f);back->scale.set(.25f,.30f,.11f);back->rotation.x=-.12f;b.body->add(back);
    }
    b.cockpit=addCockpit(*b.body,-.25f);
    b.body->traverseType<Mesh>([&](Mesh& mesh){b.fixedMeshes.push_back(&mesh);});
    const auto wheelResources=makeWheelResources();
    for(int i=0;i<4;++i){auto pivot=Group::create(),roll=Group::create();pivot->position.copy(hubAtTravel(i,dims.staticTravel,dims));pivot->add(roll);addWheel(*pivot,*roll,wheelResources,i,dims);b.pivots.push_back(pivot);b.rolls.push_back(roll);b.body->add(pivot);}
    b.suspension=addSuspension(*b.body,dims);b.fixedMeshes.insert(b.fixedMeshes.end(),b.suspension.fixedMeshes.begin(),b.suspension.fixedMeshes.end());
    b.car->traverseType<Mesh>([](Mesh& mesh){mesh.castShadow=mesh.receiveShadow=true;});return b;
}
}
