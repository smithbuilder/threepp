#pragma once
#include "RallyDetail.hpp"
#include "RallyVehicle.hpp"
#include "RallyDynamics.hpp"
#include "RallySuspension.hpp"
#include "RallyCockpit.hpp"
#include "RallyWheels.hpp"

namespace rally {
struct Buggy {
    VehicleDimensions dimensions=buggyDimensions;
    RideContactResponse contactResponse=RideContactResponse::Legacy;
    Vector3 eye{-.40f,1.68f,-.30f};
    std::shared_ptr<Group> car=Group::create(),body=Group::create();
    std::vector<std::shared_ptr<Group>> pivots,rolls;
    std::vector<Mesh*> fixedMeshes;
    std::vector<Vector3> rearGroundProbes;
    SuspensionRig suspension;Cockpit cockpit;
};
inline Buggy makeBuggy(){
    Buggy b;b.car->add(b.body);
    auto mat=[](unsigned c,float rough=.8f,float metal=0.f){auto m=MeshStandardMaterial::create();m->color=Color(c);m->roughness=rough;m->metalness=metal;return m;};
    auto frame=surfaceMaterial(0x18272a,Surface::Paint,.72f,.06f),rim=surfaceMaterial(0xb6b3a2,Surface::Metal,.46f,.85f);
    auto upholstery=surfaceMaterial(0x242b29,Surface::Rubber,.98f,0);
    auto part=[&](auto g,auto m,Vector3 p){auto o=Mesh::create(g,m);o->position.copy(p);o->castShadow=o->receiveShadow=true;b.body->add(o);return o;};
    part(BoxGeometry::create(1.6f,.18f,2.7f),frame,{0,.65f,0});
    part(BoxGeometry::create(1.5f,.08f,1.3f),frame,{0,2.15f,-.25f});
    part(BoxGeometry::create(1.8f,.14f,.15f),rim,{0,.58f,1.65f});
    part(BoxGeometry::create(1.8f,.14f,.15f),frame,{0,.6f,-1.6f});
    for(float x:{-.65f,.65f})for(float z:{-.85f,.4f})part(CylinderGeometry::create(.055f,.055f,1.22f,8),frame,{x,1.485f,z});
    for(float x:{-.4f,.4f})part(BoxGeometry::create(.5f,.65f,.4f),upholstery,{x,1.15f,-.4f});
    auto lamp=mat(0xffecd1);lamp->emissive=Color(0xffcd7b);lamp->emissiveIntensity=1.8f;
    for(float x:{-.5f,.5f})part(SphereGeometry::create(.15f,12,8),lamp,{x,.95f,1.65f});
    const auto wheelResources=makeWheelResources();
    for(int i=0;i<4;++i){auto pivot=Group::create(),roll=Group::create();pivot->position.copy(hubAtTravel(i,.41f));pivot->add(roll);
        addWheel(*pivot,*roll,wheelResources,i);b.pivots.push_back(pivot);b.rolls.push_back(roll);}
    addVehicleDetail(*b.body);
    b.cockpit=addCockpit(*b.body);
    weatherBody(*b.body);
    // Capture only static bodywork before attaching wheels and moving links.
    b.body->traverseType<Mesh>([&](Mesh& m){b.fixedMeshes.push_back(&m);});
    for(auto& p:b.pivots)b.body->add(p);b.suspension=addSuspension(*b.body);
    b.fixedMeshes.insert(b.fixedMeshes.end(),b.suspension.fixedMeshes.begin(),b.suspension.fixedMeshes.end());
    b.car->traverseType<Mesh>([](Mesh& mesh){mesh.castShadow=mesh.receiveShadow=true;});return b;
}
// Conservative tyre envelopes in chassis space. No overlap here guarantees
// geometry clearance throughout steering and available bump/droop travel.
inline Box3 tyreEnvelope(int i,float travel,float steer,const VehicleDimensions& dims=buggyDimensions){auto c=hubAtTravel(i,travel,dims);float a=steeringAngle(i,steer,dims);
    const float x=dims.tyreHalfWidth*std::abs(std::cos(a))+dims.tyreRadius*std::abs(std::sin(a));
    const float z=dims.tyreRadius*std::abs(std::cos(a))+dims.tyreHalfWidth*std::abs(std::sin(a));
    return Box3(c.clone().sub(Vector3(x,dims.tyreRadius,z)),c.clone().add(Vector3(x,dims.tyreRadius,z)));}
inline Box3 sweptTyreEnvelope(int i,const VehicleDimensions& dims=buggyDimensions){
    const float maxAngle=std::max(std::abs(steeringAngle(i,.4f,dims)),std::abs(steeringAngle(i,-.4f,dims)));
    const float x=dims.tyreHalfWidth*std::cos(maxAngle)+dims.tyreRadius*std::sin(maxAngle);
    const float z=i<2?std::hypot(dims.tyreRadius,dims.tyreHalfWidth):dims.tyreRadius;
    const float minX=std::min(std::abs(hubAtTravel(i,dims.droop,dims).x),std::abs(hubAtTravel(i,dims.bump,dims).x));
    const float maxX=std::abs(hubAtTravel(i,armPivotY-lowerBallOffset,dims).x);
    auto anchor=wheelAnchor(i,dims);float lo=i%2?minX-x:-maxX-x,hi=i%2?maxX+x:-minX+x;
    float minZ=anchor.z,maxZ=anchor.z;
    if(i>1){minZ=rearPivotZFor(dims)-rearArmLength;maxZ=std::max(hubAtTravel(i,dims.droop,dims).z,hubAtTravel(i,dims.bump,dims).z);lo=anchor.x-x;hi=anchor.x+x;}
    return Box3(Vector3(lo,dims.droop-dims.tyreRadius,minZ-z),Vector3(hi,dims.bump+dims.tyreRadius,maxZ+z));
}
inline std::vector<Box3> fixedBounds(Buggy& b){
    b.car->updateMatrixWorld(true);Matrix4 inv=*b.body->matrixWorld;inv.invert();std::vector<Box3> bounds;
    for(auto* mesh:b.fixedMeshes){auto g=mesh->geometry();g->computeBoundingBox();auto transform=inv;transform.multiply(*mesh->matrixWorld);bounds.push_back(g->boundingBox->clone().applyMatrix4(transform));}
    return bounds;
}
}
