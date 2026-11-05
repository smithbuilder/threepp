#pragma once
#include "RallyBuggy.hpp"
#include "RallySafariInterior.hpp"
#include "RallySafariCockpitFinish.hpp"
#include "RallyThinGlass.hpp"
#include "threepp/loaders/GLTFLoader.hpp"
#include <filesystem>
#include <stdexcept>
#include <map>
#include <limits>

namespace rally {
inline void gatherSafariRearGroundProbes(Buggy& b){
    b.car->updateMatrixWorld(true);Matrix4 inverse=*b.body->matrixWorld;inverse.invert();
    std::map<std::pair<int,int>,Vector3> lowest;
    std::array<float,25> scores;scores.fill(std::numeric_limits<float>::infinity());
    std::array<Vector3,25> extrema;
    for(auto* mesh:b.fixedMeshes){
        const auto& name=mesh->name;
        const bool component=name.starts_with("rear.frame")||name.starts_with("rear.engine")||name.starts_with("rear.exhaust")
            ||name.starts_with("rear.heat_shield")||name.starts_with("rear.bash_plate")||name.starts_with("rear.bumper");
        if(!component)continue;
        auto* p=mesh->geometry()->getAttribute<float>("position");auto transform=inverse;transform.multiply(*mesh->matrixWorld);
        for(unsigned i=0;i<p->count();++i){auto v=Vector3(p->getX(i),p->getY(i),p->getZ(i)).applyMatrix4(transform);
            const auto key=std::pair(static_cast<int>(std::floor(v.x/.30f)),static_cast<int>(std::floor(v.z/.30f)));
            auto found=lowest.find(key);if(found==lowest.end()||v.y<found->second.y)lowest[key]=v;
            for(int x=-2;x<=2;++x)for(int z=-2;z<=2;++z){int k=(x+2)*5+z+2;float score=v.y+.25f*(x*v.x+z*v.z);
                if(score<scores[k]){scores[k]=score;extrema[k]=v;}}
        }
    }
    auto append=[&](const Vector3& p){for(const auto& prior:b.rearGroundProbes)if(prior.distanceToSquared(p)<1e-8f)return;b.rearGroundProbes.push_back(p);};
    for(const auto& [_,p]:lowest)append(p);
    for(int i=0;i<25;++i)if(std::isfinite(scores[i]))append(extrema[i]);
}
// Original dense coupe mesh, authored by scripts/generate-safari-body.py.
// Body transforms/normals are baked into the self-contained GLB. The live rig
// remains separate: suspension, brakes, tyre rotation and instruments animate.
inline Buggy makeSafari(const std::filesystem::path& assetDir=std::filesystem::path(__FILE__).parent_path()/"assets",const VehicleDimensions& dims=safariDimensions){
    Buggy b;b.dimensions=dims;b.contactResponse=RideContactResponse::Projected;b.eye={-.4f,1.43f,-.3f};b.car->add(b.body);
    const auto path=assetDir/"safari-body.glb";
    auto asset=GLTFLoader{}.load(path);
    if(!asset||!asset->scene)throw std::runtime_error("Cannot load Safari body: "+path.string());
    asset->scene->name="Cinder Safari original body";
    // Thin alpha-blended panes must not hide the reflector/interior or other
    // glass layers by writing opaque depth. Opaque body and lamp bowls retain
    // their normal depth tests and writes.
    asset->scene->traverseType<Mesh>([](Mesh& mesh){
        for(const auto& material:mesh.materials()){
            if(material->transparent)material->depthWrite=false;
            if(material->name=="safari.clear_lamp_glass")material->side=Side::Front;
            configureSafariThinGlass(*material);
        }
    });
    b.body->add(asset->scene);
    addSafariSeats(*b.body);
    // The instrument housings sit behind the coupe's sloping windscreen.
    b.cockpit=addCockpit(*b.body,-.25f,-.025f);
    finishSafariCockpit(b.cockpit);
    b.body->traverseType<Mesh>([&](Mesh& mesh){b.fixedMeshes.push_back(&mesh);});
    auto wheelResources=makeWheelResources();weatherSafariWheelResources(wheelResources);
    for(int i=0;i<4;++i){auto pivot=Group::create(),roll=Group::create();pivot->position.copy(hubAtTravel(i,dims.staticTravel,dims));pivot->add(roll);addWheel(*pivot,*roll,wheelResources,i,dims);b.pivots.push_back(pivot);b.rolls.push_back(roll);b.body->add(pivot);}
    b.suspension=addSuspension(*b.body,dims,SuspensionProfile::Safari);b.fixedMeshes.insert(b.fixedMeshes.end(),b.suspension.fixedMeshes.begin(),b.suspension.fixedMeshes.end());
    b.car->traverseType<Mesh>([](Mesh& mesh){mesh.castShadow=mesh.receiveShadow=true;
        // The depth-only shadow pass does not model BLEND transmission. Thin
        // panes and cut-glass edges must not become opaque reflector occluders.
        for(const auto& material:mesh.materials())if(material->transparent)mesh.castShadow=false;
    });
    gatherSafariRearGroundProbes(b);return b;
}
}
