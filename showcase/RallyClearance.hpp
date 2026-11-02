#pragma once
#include "RallyBuggy.hpp"

namespace rally {
// Test actual body triangles against a solid finite tyre cylinder. Unlike one
// AABB for an entire fender, this respects the empty space in a wheel opening.
// Callers sweep steering/travel and pad the cylinder to cover sample spacing.
struct BodyTriangle {Vector3 a,b,c;Box3 bounds;std::string name;};
inline std::vector<BodyTriangle> bodyTriangles(Buggy& b){
    b.car->updateMatrixWorld(true);Matrix4 inverse=*b.body->matrixWorld;inverse.invert();
    std::vector<BodyTriangle> triangles;
    for(auto* mesh:b.fixedMeshes){auto geometry=mesh->geometry();auto* positions=geometry->getAttribute<float>("position");auto* index=geometry->getIndex();
        auto transform=inverse;transform.multiply(*mesh->matrixWorld);
        unsigned count=index?index->count():positions->count();
        auto vertex=[&](unsigned i){unsigned k=index?index->getX(i):i;return Vector3(positions->getX(k),positions->getY(k),positions->getZ(k)).applyMatrix4(transform);};
        for(unsigned i=0;i+2<count;i+=3){auto a=vertex(i),c=vertex(i+1),d=vertex(i+2);Box3 bounds;bounds.setFromPoints(std::vector<Vector3>{a,c,d});triangles.push_back({a,c,d,bounds,mesh->name});}}
    return triangles;
}
inline bool triangleCylinder(const Vector3& a,const Vector3& b,const Vector3& c,float radius,float halfWidth){
    std::array<Vector3,8> polygon,next;polygon[0]=a;polygon[1]=b;polygon[2]=c;int count=3;
    for(int plane=0;plane<2;++plane){int out=0;
        auto distance=[&](const Vector3& p){return plane?halfWidth-p.x:p.x+halfWidth;};
        for(int i=0;i<count;++i){const auto& p=polygon[i];const auto& q=polygon[(i+1)%count];float dp=distance(p),dq=distance(q);
            if(dp>=0)next[out++]=p;
            if((dp>=0)!=(dq>=0)){auto crossing=p.clone().lerp(q,dp/(dp-dq));next[out++]=crossing;}}
        count=out;if(count==0)return false;polygon=next;
    }
    float radius2=radius*radius;bool containsOrigin=false;
    for(int i=0;i<count;++i){const auto& p=polygon[i];const auto& q=polygon[(i+1)%count];
        float dy=q.y-p.y,dz=q.z-p.z,length2=dy*dy+dz*dz;
        float t=length2>1e-12f?std::clamp(-(p.y*dy+p.z*dz)/length2,0.f,1.f):0;
        float y=p.y+t*dy,z=p.z+t*dz;if(y*y+z*z<=radius2)return true;
        if((p.z>0)!=(q.z>0)){float crossing=p.y+(q.y-p.y)*(-p.z)/(q.z-p.z);if(crossing>0)containsOrigin=!containsOrigin;}}
    return containsOrigin;
}
inline const BodyTriangle* bodyTyreIntersection(const std::vector<BodyTriangle>& triangles,int wheel,float travel,float centralSteer,const VehicleDimensions& dims,float margin=.02f){
    const auto hub=hubAtTravel(wheel,travel,dims);float angle=-steeringAngle(wheel,centralSteer,dims),c=std::cos(angle),s=std::sin(angle);
    auto envelope=tyreEnvelope(wheel,travel,centralSteer,dims);envelope.expandByScalar(margin*1.5f);
    auto local=[&](const Vector3& v){auto p=v.clone().sub(hub);return Vector3(c*p.x+s*p.z,p.y,-s*p.x+c*p.z);};
    for(const auto& triangle:triangles){if(!triangle.bounds.intersectsBox(envelope))continue;
        if(triangleCylinder(local(triangle.a),local(triangle.b),local(triangle.c),dims.tyreRadius+margin,dims.tyreHalfWidth+margin))return &triangle;}
    return nullptr;
}
}
