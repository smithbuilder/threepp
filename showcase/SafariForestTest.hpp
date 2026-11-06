#pragma once
#include "RallyForest.hpp"
#include <filesystem>
#include <iostream>

namespace safari_forest_test {
inline void run(){
    using namespace threepp;
    auto check=[](bool ok,const char* message){if(!ok)throw std::runtime_error(message);};
    std::size_t baselineTriangles=0;
    for(int species=0;species<3;++species){
        vegetation::TreeParams p;vegetation::applyPreset(species==0?1:species==1?2:0,p);
        p.seed=123+species;p.attractorCount=300;
        vegetation::TreeGenerator generator(p.seed);generator.buildSkeleton(p);
        for(const auto& g:{generator.makeTrunkGeometry(p),generator.makeLeafGeometry(p)})
            baselineTriangles+=(g->getIndex()?g->getIndex()->count():g->getAttribute<float>("position")->count())/3;
    }
    auto scene=Scene::create();
    auto track=[](float a){return Vector3(60*std::sin(a),0,60*std::cos(a));};
    auto nearest=[](const Vector3& p){struct Center{Vector3 p;};const float a=std::atan2(p.x,p.z);return Center{{60*std::sin(a),0,60*std::cos(a)}};};
    auto height=[](float,float){return 0.f;};
    rally::SafariForestBudget budget;
    // Runtime assets are staged by the build for this CPU-only consumer check.
    const auto runtime=std::filesystem::path(__FILE__).parent_path().parent_path()/"build/windows-gl/bin/Release/rally-assets";
    const auto trees=rally::addSafariForest(*scene,track,nearest,height,&budget,runtime);
    check(trees.size()==180&&scene->children.size()==6,"Safari forest changes near instance/draw budget");
    check(budget.prototypeTriangles<=baselineTriangles,"Safari forest exceeds original prototype triangle budget");
    vegetation::TreeParams farParams;vegetation::applyPreset(1,farParams);farParams.seed=98;
    farParams.whorlSpacing=1.3f;farParams.branchesPerWhorl=4;farParams.radialSegments=4;
    farParams.leafDensity=.65f;farParams.leavesPerCluster=2;
    vegetation::TreeGenerator farGenerator(farParams.seed);farGenerator.buildSkeleton(farParams);
    std::size_t baselineFar=0,authoredFar=0;
    for(const auto& g:{farGenerator.makeTrunkGeometry(farParams),farGenerator.makeLeafGeometry(farParams)})
        baselineFar+=(g->getIndex()?g->getIndex()->count():g->getAttribute<float>("position")->count())/3;
    const auto& far=rally::forest_detail::loadAuthoredTree(runtime/"library/models/trees/fir_tree_01-c-lod2.glb");
    for(const auto& g:far.geometry)
        authoredFar+=(g->getIndex()?g->getIndex()->count():g->getAttribute<float>("position")->count())/3;
    check(authoredFar<=baselineFar,"Portable distant tree exceeds original far prototype triangle budget");
    for(auto* child:scene->children){
        auto* mesh=dynamic_cast<InstancedMesh*>(child);check(mesh&&mesh->count()==60,"Safari forest loses instancing");
        const auto* p=mesh->geometry()->getAttribute<float>("position");
        check(p&&p->count()>0,"Safari forest has an empty geometry");
        for(float v:p->array())check(std::isfinite(v),"Safari forest contains a nonfinite vertex");
        const auto* material=mesh->material()->as<MeshStandardMaterial>();
        check(material!=nullptr,"Portable tree loses its PBR material");
        for(auto* texture:{material->map.get(),material->normalMap.get(),material->roughnessMap.get()})
            if(texture)check(texture->image().width()<=1024&&texture->image().height()<=1024,"Portable tree exceeds1K map budget");
    }
    for(const auto& pos:trees)check(pos.y==0&&(std::hypot(pos.x,pos.z)>67.4f||std::hypot(pos.x,pos.z)<52.6f),
        "Safari forest intrudes into the driven corridor");
    std::cout<<"PASS: portable forest180near/6draws, finite instantiated PBR geometry, triangles="<<budget.prototypeTriangles
        <<" <=original="<<baselineTriangles<<", far="<<authoredFar<<" <=original="<<baselineFar
        <<", rooted outside road. No GPU opened.\n";
}
}
