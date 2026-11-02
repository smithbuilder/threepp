#pragma once
#include "threepp/threepp.hpp"
#include "threepp/extras/core/NoiseUtils.hpp"
#include "threepp/extras/core/TextureBake.hpp"
#include "threepp/extras/vegetation/GrassField.hpp"
#include "threepp/extras/vegetation/TreeGenerator.hpp"
#include "threepp/extras/terrain/RockGeometry.hpp"
#include "threepp/utils/BufferGeometryUtils.hpp"
#include "threepp/materials/MeshBasicMaterial.hpp"
#include "threepp/geometries/TextGeometry.hpp"
#include "threepp/loaders/FontLoader.hpp"
#include "RallySurface.hpp"
#include <random>

namespace rally {
using namespace threepp;
constexpr float pi = 3.14159265359f;
struct Collider { float x,z,radius; };
inline float height(float x, float z) {
    return 5.5f*std::sin(x*.024f) + 4.f*std::cos(z*.031f) +
        9.f*(noise::fbm(x*.021f,z*.021f,256,71,4)-.5f) + .17f*std::sin(x*.7f+z*.4f);
}
inline std::shared_ptr<DataTexture> groundTexture(bool road) {
    constexpr int n=256;
    std::vector<unsigned char> data(n*n*4);
    for(int y=0;y<n;++y) for(int x=0;x<n;++x) {
        float u=x/256.f, v=y/256.f;
        float a=noise::fbm(u*17,v*17,17,35,4);
        float grain=noise::hash2(x,y,12);
        float rut=std::exp(-std::pow((u-.29f)*22,2.f))+std::exp(-std::pow((u-.71f)*22,2.f));
        float s=road ? .67f+.36f*a+.14f*grain-.2f*rut : .58f+.5f*a+.12f*grain;
        float edge=road ? .85f+.15f*std::sin(pi*u) : 1.f;
        int i=(y*n+x)*4;
        data[i]=noise::toByte((road?.54f:.64f)*s*edge);
        data[i+1]=noise::toByte((road?.41f:.66f)*s*edge);
        data[i+2]=noise::toByte((road?.27f:.48f)*s*edge);
        data[i+3]=255;
    }
    auto t=DataTexture::create(data,n,n); texgen::finishTexture(t,true,true,2); return t;
}
inline std::shared_ptr<DataTexture> gravelNormal() {
    constexpr int n=128; auto t=DataTexture::create(4,n,n);
    texgen::writeNormalFromHeight(t,n,1.3f,[](float u,float v){return noise::fbm(u*26,v*26,26,6,3);},true);
    texgen::finishTexture(t,false,true,2); return t;
}
inline auto shadowMaterial(float opacity) {
    constexpr int n=64; std::vector<unsigned char> p(n*n*4,0);
    for(int y=0;y<n;++y) for(int x=0;x<n;++x) {
        float dx=(x-31.5f)/31.5f,dy=(y-31.5f)/31.5f;
        p[(y*n+x)*4+3]=noise::toByte(std::max(0.f,1-dx*dx-dy*dy)*.75f);
    }
    auto t=DataTexture::create(p,n,n); texgen::finishTexture(t,false,false);
    auto m=MeshBasicMaterial::create(); m->color=Color(0x11150e);m->map=t;
    m->transparent=true;m->opacity=opacity;m->depthWrite=false;m->alphaTest=.01f;return m;
}

// A chamfered silhouette instead of a stack of rectangular boxes.
inline auto bodyPanel(float width,float length,float frontHeight,float backHeight) {
    std::vector<float> vertices={-width*.72f,frontHeight,length/2,width*.72f,frontHeight,length/2,
        width,backHeight,-length/2,-width,backHeight,-length/2,
        -width*.72f,0,length/2,width*.72f,0,length/2,width,0,-length/2,-width,0,-length/2};
    auto g=BufferGeometry::create();g->setAttribute("position",FloatBufferAttribute::create(vertices,3));
    g->setIndex(std::vector<unsigned>{0,1,2,0,2,3,4,6,5,4,7,6,0,4,5,0,5,1,1,5,6,1,6,2,2,6,7,2,7,3,3,7,4,3,4,0});
    auto flat=g->toNonIndexed();flat->computeVertexNormals();return flat;
}
inline auto rod(const Vector3& a,const Vector3& b,float radius,std::shared_ptr<Material> material) {
    auto d=b.clone().sub(a);auto mesh=Mesh::create(CylinderGeometry::create(radius,radius,d.length(),8),material);
    mesh->position.copy(a).add(b).multiplyScalar(.5f);mesh->quaternion.setFromUnitVectors(Vector3(0,1,0),d.normalize());return mesh;
}
inline auto label(const std::string& text,float size,Color color) {
    auto mat=MeshBasicMaterial::create();mat->color=color;mat->side=Side::Double;
    auto g=TextGeometry::create(text,TextGeometry::Options(FontLoader{}.defaultFont(),size,2));
    g->center();return Mesh::create(g,mat);
}
inline void bakeOcclusion(BufferGeometry& geometry,const std::vector<Vector3>& trees) {
    auto p=geometry.getAttribute<float>("position");auto c=geometry.getAttribute<float>("color");
    if(!c)return;
    for(int i=0;i<p->count();++i){float x=p->getX(i),z=p->getZ(i),shade=1;
        for(auto& tree:trees){float dx=x-tree.x-6,dz=z-tree.z-2;
            if(std::abs(dx)>10||std::abs(dz)>8)continue;
            float r=dx*dx/36+dz*dz/25;
            if(r<2){float leaves=.65f+.35f*noise::valueNoise(x*1.7f,z*1.7f,256,19);
                shade=std::min(shade,1-.6f*std::exp(-r*1.8f)*leaves);}
        }
        c->setXYZ(i,c->getX(i)*shade,c->getY(i)*shade,c->getZ(i)*shade);
    }c->needsUpdate();
}
inline void addVehicleDetail(Group& body) {
    auto steel=surfaceMaterial(0x25292b,Surface::Paint,.72f,.06f);
    auto gold=surfaceMaterial(0xf7bc39,Surface::Paint,.59f,.04f);
    auto silver=surfaceMaterial(0xa0a6a3,Surface::Metal,.47f,.90f);
    auto black=surfaceMaterial(0x111719,Surface::Rubber,.96f,0);
    auto make=[&](auto g,auto m,Vector3 p){auto o=Mesh::create(g,m);o->position.copy(p);body.add(o);return o;};
    auto hood=make(bodyPanel(.85f,1.4f,.08f,.35f),gold,{0,.91f,.85f});
    make(bodyPanel(.91f,1.2f,.32f,.15f),gold,{0,.64f,-1.15f});
    for(float s:{-1.f,1.f}) {
        // Short side pods end between the axles, leaving actual wheel bays.
        make(bodyPanel(.14f,1.1f,.12f,.12f),gold,{s*.87f,.9f,0});
        body.add(rod({s*.82f,.75f,1.3f},{s*.66f,2.12f,.27f},.062f,steel));
        body.add(rod({s*.66f,2.12f,.27f},{s*.74f,2.02f,-.75f},.062f,steel));
        body.add(rod({s*.74f,2.02f,-.75f},{s*.88f,.8f,-1.5f},.062f,steel));
        body.add(rod({s*.85f,.85f,-.8f},{s*.85f,1.45f,.2f},.045f,steel));
        body.add(rod({s*.85f,1.45f,-.8f},{s*.85f,.85f,.2f},.045f,steel));
        body.add(rod({s*.29f,.72f,-1.22f},{s*.4f,.59f,-1.4f},.045f,steel));
        body.add(rod({s*.4f,.59f,-1.4f},{s*.47f,.4f,-1.57f},.045f,steel));
    }
    // Rear-mounted collector below the engine/deck, with a single low outlet.
    auto muffler=make(CylinderGeometry::create(.1f,.1f,.96f,14),silver,{0,.4f,-1.57f});muffler->rotation.z=pi/2;
    for(float side:{-1.f,1.f})body.add(rod({side*.42f,.64f,-1.55f},{side*.42f,.42f,-1.55f},.018f,steel));
    body.add(rod({-.48f,.4f,-1.57f},{-.62f,.39f,-1.78f},.063f,steel));
    const Vector3 outletStart(-.62f,.39f,-1.78f),outletEnd(-.62f,.34f,-1.97f);
    auto direction=outletEnd.clone().sub(outletStart);auto tip=make(CylinderGeometry::create(.07f,.07f,direction.length(),14,1,true),silver,outletStart.clone().add(outletEnd).multiplyScalar(.5f));
    tip->quaternion.setFromUnitVectors(Vector3(0,1,0),direction.clone().normalize());
    auto bore=make(CircleGeometry::create(.055f,14),black,outletEnd.clone().addScaledVector(direction.clone().normalize(),-.035f));
    bore->material()->side=Side::Double;bore->quaternion.setFromUnitVectors(Vector3(0,0,1),direction.normalize());
    body.add(rod({-.74f,2.02f,-.75f},{.74f,.82f,-1.45f},.045f,steel));
    body.add(rod({.74f,2.02f,-.75f},{-.74f,.82f,-1.45f},.045f,steel));
    for(int i=0;i<6;++i) make(BoxGeometry::create(.8f,.04f,.06f),steel,{0,1.04f+i*.025f,-1.18f+i*.11f});
    for(float z:{-.5f,.3f})body.add(rod({-.72f,2.09f,z},{.72f,2.09f,z},.045f,steel));
    auto number=label("07",.35f,Color(0x192021)); number->rotation.x=-pi/2; number->position.set(0,1.2f,.85f);body.add(number);
    auto brand=label("CINDER",.16f,Color(0xf3ca64));brand->rotation.y=pi;brand->position.set(0,.87f,-1.76f);body.add(brand);

}

template<class Track,class Nearest>
inline std::shared_ptr<GrassField> dress(Scene& scene,Track track,Nearest nearest,const std::vector<Vector3>& trees,std::vector<Collider>* colliders=nullptr) {
    std::mt19937 rng(902);std::uniform_real_distribution<float> random(0,1);
    auto shade=InstancedMesh::create(PlaneGeometry::create(1,1),shadowMaterial(.35f),trees.size());
    for(size_t i=0;i<trees.size();++i){Object3D o;o.position.copy(trees[i]);o.position.y+=.11f;o.rotation.x=-pi/2;o.scale.set(7,7,1);o.updateMatrix();shade->setMatrixAt(i,*o.matrix);}
    shade->instanceMatrix()->needsUpdate();scene.add(shade);
    vegetation::TreeParams fp;vegetation::applyPreset(1,fp);fp.seed=98;fp.whorlSpacing=1.3f;fp.branchesPerWhorl=4;
    fp.radialSegments=4;fp.leafDensity=.65f;fp.leavesPerCluster=2;
    vegetation::TreeGenerator fg(fp.seed);fg.buildSkeleton(fp);
    auto silhouette=MeshStandardMaterial::create();silhouette->color=Color(0x314633);silhouette->roughness=1;
    silhouette->map=vegetation::makeNeedleFrondTexture(128,fp.seed,fp.leafColor,fp.leafAtlasCells);
    silhouette->alphaTest=vegetation::kLeafAlphaTest;silhouette->side=Side::Double;silhouette->vertexColors=true;
    auto trunksMat=MeshStandardMaterial::create();trunksMat->color=Color(0x514c3e);
    auto farTrees=InstancedMesh::create(fg.makeLeafGeometry(fp),silhouette,240);
    auto farTrunks=InstancedMesh::create(fg.makeTrunkGeometry(fp),trunksMat,240);
    for(int i=0;i<240;++i){Vector3 p;
        for(int attempt=0;attempt<60;++attempt){float a=random(rng)*2*pi;p=track(a);auto d=track(a+.002f).sub(p).normalize();
            p.addScaledVector(Vector3(d.z,0,-d.x),(i%2?1.f:-1.f)*(35+random(rng)*65));
            auto n=nearest(p).p;if(Vector2(p.x-n.x,p.z-n.z).length()>30)break;}
        p.y=height(p.x,p.z);Object3D o;o.position.copy(p);o.scale.setScalar(1.1f+random(rng)*.7f);
        o.rotation.y=random(rng)*pi;o.updateMatrix();farTrees->setMatrixAt(i,*o.matrix);farTrunks->setMatrixAt(i,*o.matrix);}
    farTrees->instanceMatrix()->needsUpdate();farTrunks->instanceMatrix()->needsUpdate();scene.add(farTrees);scene.add(farTrunks);
    GrassField::Params gp;gp.segments=2;gp.topColor={.42f,.40f,.19f};gp.bottomColor={.075f,.12f,.055f};
    gp.sunColor={.7f,.58f,.35f};gp.ambient={.28f,.31f,.22f};gp.fogColor={.66f,.64f,.53f};gp.fogNear=45;gp.fogFar=150;
    auto grass=GrassField::create(9000,gp);
    for(int i=0;i<9000;++i){float a=random(rng)*2*pi;auto p=track(a),d=track(a+.002f).sub(p).normalize();
        Vector3 side(d.z,0,-d.x);p.addScaledVector(side,(i%2?1.f:-1.f)*(4.1f+std::pow(random(rng),2.f)*14));
        p.y=height(p.x,p.z)+.04f;Object3D o;o.position.copy(p);o.rotation.y=random(rng)*6.28f;
        o.scale.set(.14f+random(rng)*.16f,.25f+random(rng)*.7f,1);o.updateMatrix();grass->setMatrixAt(i,*o.matrix);}
    grass->instanceMatrix()->needsUpdate();scene.add(grass);
    auto rockMat=MeshStandardMaterial::create();rockMat->color=Color(0x514f43);rockMat->roughness=.95f;
    auto rocks=InstancedMesh::create(terrain::makeRockGeometry(31),rockMat,150);
    for(int i=0;i<150;++i){float a=random(rng)*2*pi;auto p=track(a),d=track(a+.002f).sub(p).normalize();
        p.addScaledVector(Vector3(d.z,0,-d.x),(i%2?1.f:-1.f)*(5+random(rng)*10));p.y=height(p.x,p.z)-.3f;
        Object3D o;o.position.copy(p);float s=.3f+std::pow(random(rng),2.f)*2.4f;o.scale.set(s,s*.7f,s*1.3f);
        if(colliders&&s>.7f)colliders->push_back({p.x,p.z,s*1.1f});
        o.rotation.set(random(rng),random(rng)*6.28f,random(rng));o.updateMatrix();rocks->setMatrixAt(i,*o.matrix);}
    rocks->instanceMatrix()->needsUpdate();scene.add(rocks);
    // Alternating chevrons, stakes and low timber barriers make corners legible.
    auto wood=MeshStandardMaterial::create();wood->color=Color(0x6d5740);wood->roughness=.9f;
    auto stripe=MeshBasicMaterial::create();stripe->color=Color(0xeac16c);
    for(int i=0;i<52;++i){float a=i*2*pi/52;auto p=track(a),d=track(a+.003f).sub(p).normalize();
        auto edge=p.clone().addScaledVector(Vector3(d.z,0,-d.x),i%2?5.f:-5.f);edge.y=height(edge.x,edge.z);
        auto pole=Mesh::create(CylinderGeometry::create(.065f,.085f,1.25f,6),wood);pole->position.copy(edge).add(Vector3(0,.62f,0));scene.add(pole);
        auto cap=Mesh::create(BoxGeometry::create(.16f,.25f,.16f),stripe);cap->position.copy(edge).add(Vector3(0,1.12f,0));scene.add(cap);
        if(i%5==0){Vector3 next=track(a+.05f).addScaledVector(Vector3(d.z,0,-d.x),i%2?5.f:-5.f);next.y=height(next.x,next.z)+.7f;
            scene.add(rod(edge.clone().add(Vector3(0,.7f,0)),next,.12f,wood));}
    }
    return grass;
}
}
