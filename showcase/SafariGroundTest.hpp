#pragma once
#include "RallyGround.hpp"
#include "RallyDressing.hpp"
#include "threepp/geometries/PlaneGeometry.hpp"
#include "threepp/loaders/TextureLoader.hpp"
#include "threepp/textures/DataTexture.hpp"
#include <array>
#include <filesystem>
#include <iostream>

namespace safari_ground_test {
inline void run(){
    using namespace threepp;
    auto check=[](bool ok,const char* text){if(!ok)throw std::runtime_error(text);};
    auto land=PlaneGeometry::create(520,520,20,20);land->rotateX(-1.57079632679f);
    auto* lp=land->getAttribute<float>("position");
    for(unsigned i=0;i<lp->count();++i)lp->setY(i,.03f*lp->getX(i)+.01f*lp->getZ(i));
    land->computeVertexNormals();
    // Deliberately unequal sampling tests the consumer contract: scan scale
    // must depend on physical distance, not on the number of route rings.
    constexpr std::array<float,8> angles={0,.15f,.6f,1.7f,2.8f,3.4f,4.8f,6.28318530718f};
    std::vector<float> p,uv;std::vector<unsigned> index;
    for(unsigned row=0;row<angles.size();++row){
        const float a=angles[row];
        for(unsigned j=0;j<=8;++j){
            const float radius=40.f+(j/8.f*2.f-1.f)*3.7f;
            const float x=radius*std::sin(a),z=radius*std::cos(a);
            p.insert(p.end(),{x,.03f*x+.01f*z,z});uv.insert(uv.end(),{j/8.f,row*.12f});
            if(row+1<angles.size()&&j<8){const unsigned b=row*9+j;
                index.insert(index.end(),{b,b+9,b+1,b+1,b+9,b+10});}
        }
    }
    auto road=BufferGeometry::create();road->setIndex(index);
    road->setAttribute("position",FloatBufferAttribute::create(p,3));
    road->setAttribute("uv",FloatBufferAttribute::create(uv,2));road->computeVertexNormals();
    const auto landBefore=lp->array();
    const auto landNormalBefore=land->getAttribute<float>("normal")->array();
    const auto landIndexBefore=land->getIndex()->array();
    const auto roadNormalBefore=road->getAttribute<float>("normal")->array();
    const auto roadIndexBefore=road->getIndex()->array();
    auto forest=MeshStandardMaterial::create(),dirt=MeshStandardMaterial::create();
    TextureLoader loader;const auto assets=std::filesystem::path(__FILE__).parent_path().parent_path()/"asset-library";
    auto load=[&](const std::string& name,bool srgb){
        const auto relative=name.starts_with("library/")?name.substr(8):name;
        auto t=loader.load(assets/relative);
        check(bool(t),"Safari surface scan cannot be loaded on the CPU");
        t->colorSpace=srgb?ColorSpace::sRGB:ColorSpace::NoColorSpace;
        t->wrapS=t->wrapT=TextureWrapping::Repeat;t->anisotropy=2;return t;
    };
    forest->map=load("materials/forest-floor/basecolor_1k.jpg",true);
    forest->normalMap=load("materials/forest-floor/normal_gl_1k.jpg",false);
    dirt->map=load("materials/gravel-road/basecolor_1k.jpg",true);
    dirt->normalMap=load("materials/gravel-road/normal_gl_1k.jpg",false);
    forest->alphaMap=DataTexture::create(4,2,2);const auto alpha=forest->alphaMap;
    auto nearest=[](const Vector3& point){
        struct Center {Vector3 p;};const float a=std::atan2(point.x,point.z);
        return Center{{40.f*std::sin(a),0,40.f*std::cos(a)}};
    };
    const auto report=rally::configureSafariGround(*land,*road,*forest,*dirt,load,nearest);
    check(lp->array()==landBefore&&land->getIndex()->array()==landIndexBefore&&
          road->getAttribute<float>("position")->array()==p&&road->getIndex()->array()==roadIndexBefore,
          "Ground art changes the visible/collision triangle surfaces");
    check(land->getAttribute<float>("normal")->array()==landNormalBefore&&
          road->getAttribute<float>("normal")->array()==roadNormalBefore,
          "Ground art replaces normals with an unrelated analytic surface");
    check(forest->alphaMap==alpha&&alpha->repeat.x==1&&alpha->repeat.y==1,
          "Ground scan scaling changes the road/land cutout coverage");
    const auto* newUv=road->getAttribute<float>("uv");
    const auto* rp=road->getAttribute<float>("position");
    Vector3 previous;float measured=0;
    for(unsigned row=0;row<angles.size();++row){
        const unsigned i=row*9;
        const Vector3 edge(rp->getX(i),rp->getY(i),rp->getZ(i));
        const Vector3 other(rp->getX(i+8),rp->getY(i+8),rp->getZ(i+8));
        const auto center=edge.clone().add(other).multiplyScalar(.5f);
        if(row)measured+=center.distanceTo(previous);
        check(std::abs(newUv->getY(i)*report.roadTileMetres-measured)<.0001f,
              "Safari road scan stretches with route sampling density");
        check(std::abs((newUv->getX(i+8)-newUv->getX(i))*2.f-edge.distanceTo(other))<.00001f,
              "Safari road scan width differs from its2m source scale");
        previous=center;
    }
    const float closure=newUv->getY(newUv->count()-1);
    check(std::abs(closure-std::round(closure))<.00001f&&std::abs(report.roadTileMetres-2)<.01f,
          "Safari road has a texture phase seam at the lap closure");
    for(auto* geometry:std::array<BufferGeometry*,2>{land.get(),road.get()}){
        const auto* color=geometry->getAttribute<float>("color");
        check(color&&color->count()==geometry->getAttribute<float>("position")->count(),
              "Ground art loses a vertex colour");
        for(float c:color->array())check(std::isfinite(c)&&c>.25f&&c<1.1f,
              "Ground macro colour is nonfinite, clipped or unbounded");
    }
    for(auto* material:{forest.get(),dirt.get()}){
        check(material->metalness==0&&material->roughness>.95f&&
              material->roughnessMap->colorSpace==ColorSpace::NoColorSpace&&
              material->map->colorSpace==ColorSpace::sRGB&&
              material->normalMap->colorSpace==ColorSpace::NoColorSpace,
              "Ground PBR data/colour spaces or dielectric contract changed");
        for(auto* texture:{material->map.get(),material->normalMap.get(),material->roughnessMap.get()})
            check(texture->image().width()==1024&&texture->image().height()==1024&&texture->anisotropy==2,
                  "Safari ground exceeds the1K/2x texture budget");
        check(material->map->repeat.equals(material->normalMap->repeat)&&
              material->map->repeat.equals(material->roughnessMap->repeat),
              "Ground PBR scan channels no longer share scale");
    }
    check(std::abs(520.f/forest->map->repeat.x-3.2f)<.00001f,
          "Forest-floor scan differs from its3.2m source scale");
    // An actual consumer verifies portable mesh import, shared map/storage and
    // grass placement contracts without constructing a graphics context.
    auto scene=Scene::create();auto tuftGrass=GrassField::create(9000,GrassField::Params{});
    auto rocks=InstancedMesh::create(road,MeshStandardMaterial::create(),150);
    scene->add(tuftGrass);scene->add(rocks);
    for(unsigned i=0;i<150;++i){Object3D o;o.position.set(i*.1f,.3f,-5);o.scale.set(1,.7f,1.3f);o.updateMatrix();rocks->setMatrixAt(i,*o.matrix);}
    const auto rockTransforms=rocks->instanceMatrix()->array();
    auto track=[](float a){return Vector3(40.f*std::sin(a),0,40.f*std::cos(a));};
    auto floor=[](float x,float z){return .03f*x+.01f*z;};
    const auto dressing=rally::refineSafariDressing(*scene,0,track,nearest,floor,assets/"models/fieldstone/boulder.obj",*forest);
    check(dressing.blades==9000&&dressing.tufts==1000&&dressing.rocks==150&&dressing.rockTriangles<=70&&scene->children.size()==2,
          "Safari dressing increases the existing instance/mesh budget");
    check(rocks->instanceMatrix()->array()==rockTransforms,"Fieldstone refinement changes gameplay obstacle transforms");
    check(dressing.minimumGrassRoadDistance>3.8f,"Safari grass tufts intrude onto the driven road");
    const auto* rockMaterial=rocks->material()->as<MeshStandardMaterial>();
    check(rockMaterial&&rockMaterial->map==forest->map&&rockMaterial->normalMap==forest->normalMap&&rockMaterial->roughnessMap==forest->roughnessMap,
          "Fieldstone refinement duplicates or replaces the shared PBR library maps");
    float shortest=1e9f,tallest=0;Vector3 first;
    for(unsigned i=0;i<9000;++i){Matrix4 m;tuftGrass->getMatrixAt(i,m);Vector3 p,scale;p.setFromMatrixPosition(m);scale.setFromMatrixScale(m);
        check(std::isfinite(p.x)&&std::isfinite(p.y)&&std::isfinite(p.z)&&std::abs(p.y-floor(p.x,p.z)-.012f)<.00001f,
              "Grass roots float away from the supplied physical ground");
        shortest=std::min(shortest,scale.y);tallest=std::max(tallest,scale.y);
        if(i==0)first=p;else if(i<9)check(std::hypot(p.x-first.x,p.z-first.z)<.8f,"Grass blades are not arranged in bounded tufts");
    }
    check(tallest>shortest*2.5f&&tuftGrass->instanceColor()!=nullptr&&
          tuftGrass->windMaterial().vertexShader.find("vSafariTuftColor = instanceColor;")!=std::string::npos,
          "Safari grass loses its varied height/cluster palette");
    std::cout<<"PASS: Safari ground preserves collision surfaces/normals/cutout, metre-scaled UVs/lap phase, finite macro colours and1K PBR. Portable fieldstone<=70tri shares maps/retains150 transforms;9000 rooted blades form1000 bounded tufts clear of the road. No GPU opened.\n";
}
}
