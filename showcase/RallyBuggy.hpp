#pragma once
#include "RallyDetail.hpp"
#include "RallyVehicle.hpp"

namespace rally {
struct Buggy {
    std::shared_ptr<Group> car=Group::create(),body=Group::create();
    std::vector<std::shared_ptr<Group>> pivots,rolls;
    std::vector<Mesh*> fixedMeshes;
    std::vector<SuspensionLink> links;
};
inline Buggy makeBuggy(){
    Buggy b;b.car->add(b.body);
    auto mat=[](unsigned c,float rough=.8f,float metal=0.f){auto m=MeshStandardMaterial::create();m->color=Color(c);m->roughness=rough;m->metalness=metal;return m;};
    auto frame=mat(0x18272a,.45f,.7f),tire=mat(0x202324),rim=mat(0xd1c5a5,.3f,.8f);
    auto part=[&](auto g,auto m,Vector3 p){auto o=Mesh::create(g,m);o->position.copy(p);o->castShadow=o->receiveShadow=true;b.body->add(o);return o;};
    part(BoxGeometry::create(1.6f,.18f,2.7f),frame,{0,.65f,0});
    part(BoxGeometry::create(1.5f,.08f,1.3f),frame,{0,1.98f,-.25f});
    part(BoxGeometry::create(1.8f,.14f,.15f),rim,{0,.58f,1.65f});
    part(BoxGeometry::create(1.8f,.14f,.15f),frame,{0,.6f,-1.6f});
    for(float x:{-.65f,.65f})for(float z:{-.85f,.4f})part(CylinderGeometry::create(.055f,.055f,1.05f,8),frame,{x,1.4f,z});
    for(float x:{-.4f,.4f})part(BoxGeometry::create(.5f,.65f,.4f),frame,{x,1.15f,-.4f});
    auto lamp=mat(0xffecd1);lamp->emissive=Color(0xffcd7b);lamp->emissiveIntensity=1.8f;
    for(float x:{-.5f,.5f})part(SphereGeometry::create(.15f,12,8),lamp,{x,.95f,1.65f});
    for(int i=0;i<4;++i){auto pivot=Group::create(),roll=Group::create();pivot->position.copy(wheelAnchor(i));pivot->position.y=.41f;pivot->add(roll);
        auto rubber=Mesh::create(CylinderGeometry::create(.48f,.48f,.38f,20),tire);rubber->rotation.z=pi/2;roll->add(rubber);
        auto hub=Mesh::create(CylinderGeometry::create(.25f,.25f,.4f,12),rim);hub->rotation.z=pi/2;roll->add(hub);b.pivots.push_back(pivot);b.rolls.push_back(roll);}
    addVehicleDetail(*b.body,b.rolls);
    // Capture only static bodywork before attaching wheels and moving links.
    b.body->traverseType<Mesh>([&](Mesh& m){b.fixedMeshes.push_back(&m);});
    for(auto& p:b.pivots)b.body->add(p);b.links=addSuspension(*b.body);
    b.car->traverseType<Mesh>([](Mesh& mesh){mesh.castShadow=mesh.receiveShadow=true;});return b;
}
// Conservative tyre envelopes in chassis space. No overlap here guarantees
// geometry clearance throughout steering and available bump/droop travel.
inline Box3 tyreEnvelope(int i,float travel,float steer){auto c=wheelAnchor(i);c.y=travel;float a=i<2?steer:0;
    const float x=tyreHalfWidth*std::abs(std::cos(a))+tyreRadius*std::abs(std::sin(a));
    const float z=tyreRadius*std::abs(std::cos(a))+tyreHalfWidth*std::abs(std::sin(a));
    return Box3(c.clone().sub(Vector3(x,tyreRadius,z)),c.clone().add(Vector3(x,tyreRadius,z)));}
inline std::vector<Box3> fixedBounds(Buggy& b){
    b.car->updateMatrixWorld(true);Matrix4 inv=*b.body->matrixWorld;inv.invert();std::vector<Box3> bounds;
    for(auto* mesh:b.fixedMeshes){auto g=mesh->geometry();g->computeBoundingBox();auto transform=inv;transform.multiply(*mesh->matrixWorld);bounds.push_back(g->boundingBox->clone().applyMatrix4(transform));}
    return bounds;
}
}
