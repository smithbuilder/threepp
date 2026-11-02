#pragma once
#include "RallyVehicle.hpp"

namespace rally {
inline constexpr int coilTurns=7,coilSegments=84,coilSides=6;
inline constexpr float coilRadius=.078f,wireRadius=.012f;
inline auto springGeometry(){
    auto g=BufferGeometry::create();g->setAttribute("position",FloatBufferAttribute::create(std::vector<float>((coilSegments+1)*coilSides*3),3));
    g->setAttribute("normal",FloatBufferAttribute::create(std::vector<float>((coilSegments+1)*coilSides*3),3));
    std::vector<unsigned> indices;for(int i=0;i<coilSegments;++i)for(int j=0;j<coilSides;++j){unsigned a=i*coilSides+j,b=i*coilSides+(j+1)%coilSides,c=a+coilSides,d=b+coilSides;indices.insert(indices.end(),{a,b,c,b,d,c});}g->setIndex(indices);return g;
}
inline void shapeSpring(BufferGeometry& g,float length){
    auto* p=g.getAttribute<float>("position");auto* n=g.getAttribute<float>("normal");
    constexpr float angleRate=6.2831853f*coilTurns;
    for(int i=0;i<=coilSegments;++i){float t=i/static_cast<float>(coilSegments),a=t*angleRate;
        Vector3 center(coilRadius*std::cos(a),t*length,coilRadius*std::sin(a)),radial(std::cos(a),0,std::sin(a));
        auto tangent=Vector3(-coilRadius*std::sin(a)*angleRate,length,coilRadius*std::cos(a)*angleRate).normalize();
        auto binormal=tangent.clone().cross(radial).normalize();
        for(int j=0;j<coilSides;++j){float b=j*6.2831853f/coilSides;auto normal=radial.clone().multiplyScalar(std::cos(b)).addScaledVector(binormal,std::sin(b));auto v=center.clone().addScaledVector(normal,wireRadius);int k=i*coilSides+j;p->setXYZ(k,v.x,v.y,v.z);n->setXYZ(k,normal.x,normal.y,normal.z);}
    }p->needsUpdate();n->needsUpdate();
}
struct Coilover {
    std::shared_ptr<Group> assembly;std::shared_ptr<Mesh> barrel,shaft,spring,lowerSeat,lowerEye,lowerPin,bridge;
    Vector3 top;int wheel;float length=0;
};
struct TieRod {std::shared_ptr<Mesh> mesh;Vector3 rack;int wheel;};
struct SuspensionRig {
    VehicleDimensions dimensions=buggyDimensions;
    std::vector<SuspensionLink> arms;std::vector<Coilover> shocks;
    std::array<std::shared_ptr<Mesh>,4> uprights,lowerJoints,upperJoints;
    std::array<std::shared_ptr<Mesh>,2> axles;
    std::vector<TieRod> steering;
    std::vector<Mesh*> fixedMeshes;
};
inline SuspensionRig addSuspension(Group& body,const VehicleDimensions& dims=buggyDimensions){
    auto dark=MeshStandardMaterial::create();dark->color=Color(0x303738);dark->metalness=.65f;dark->roughness=.5f;
    auto bright=MeshStandardMaterial::create();bright->color=Color(0xb1b5ae);bright->metalness=.9f;bright->roughness=.22f;
    auto springMat=MeshStandardMaterial::create();springMat->color=Color(0xddd7bb);springMat->metalness=.4f;springMat->roughness=.42f;
    auto rubber=MeshStandardMaterial::create();rubber->color=Color(0x131a1b);rubber->roughness=.7f;
    SuspensionRig rig;rig.dimensions=dims;
    const float rearPickupX=dims.halfTrack-.20f,rearPickupZ=rearPivotZFor(dims);
    auto unit=CylinderGeometry::create(1,1,1,10);
    auto strut=[&](float radius,auto material){auto m=Mesh::create(unit,material);m->scale.set(radius,1,radius);body.add(m);return m;};
    for(int i=0;i<4;++i){auto a=wheelAnchor(i,dims);float side=i%2?1.f:-1.f;
        if(i<2)for(int upper=0;upper<2;++upper)for(float front:{-1.f,1.f}){
            float z=a.z+front*(upper?.20f:.24f),y=armPivotY+(upper?uprightHeight:0);
            auto mesh=strut(upper?.024f:.030f,dark);rig.arms.push_back({mesh,{side*dims.armPivotX,y,z},i,lowerBallOffset+(upper?uprightHeight:0)});
            auto bracket=Mesh::create(BoxGeometry::create(.09f,.09f,.10f),dark);bracket->position.set(side*dims.armPivotX,y,z);body.add(bracket);rig.fixedMeshes.push_back(bracket.get());
            auto bolt=Mesh::create(CylinderGeometry::create(.031f,.031f,.13f,6),bright);bolt->rotation.x=1.5707963f;bolt->position.copy(bracket->position);body.add(bolt);rig.fixedMeshes.push_back(bolt.get());
            auto brace=Mesh::create(CylinderGeometry::create(.024f,.024f,1,8),dark);fitLink(*brace,{side*(dims.armPivotX-.04f),.65f,a.z},{side*dims.armPivotX,y,z});body.add(brace);rig.fixedMeshes.push_back(brace.get());
        }
        else {
            // Rear fork rotates around a transverse chassis hinge. Its hub
            // follows a fore/aft arc rather than the front wishbone's track arc.
            for(float fork:{-.10f,.10f}){Vector3 pickup(side*rearPickupX+fork,armPivotY,rearPickupZ);
                auto arm=Mesh::create(BoxGeometry::create(.10f,1,.14f),dark);body.add(arm);rig.arms.push_back({arm,pickup,i,lowerBallOffset});
                auto bracket=Mesh::create(BoxGeometry::create(.10f,.13f,.14f),dark);bracket->position.copy(pickup);body.add(bracket);rig.fixedMeshes.push_back(bracket.get());}
            auto pivot=Mesh::create(CylinderGeometry::create(.041f,.041f,.36f,10),bright);pivot->rotation.z=1.5707963f;pivot->position.set(side*rearPickupX,armPivotY,rearPickupZ);body.add(pivot);rig.fixedMeshes.push_back(pivot.get());
            rig.axles[i-2]=strut(.027f,bright);
        }
        rig.uprights[i]=strut(.046f,dark);
        rig.lowerJoints[i]=Mesh::create(SphereGeometry::create(.052f,10,6),bright);rig.upperJoints[i]=Mesh::create(SphereGeometry::create(.048f,10,6),bright);body.add(rig.lowerJoints[i]);body.add(rig.upperJoints[i]);
        Coilover shock;shock.wheel=i;shock.top={side*dims.armPivotX,1.14f,a.z+(i<2?-.22f:.15f)};shock.assembly=Group::create();body.add(shock.assembly);
        shock.barrel=Mesh::create(CylinderGeometry::create(.049f,.049f,.31f,12),rubber);shock.barrel->position.y=.20f;shock.assembly->add(shock.barrel);
        shock.shaft=Mesh::create(CylinderGeometry::create(.018f,.018f,1,10),bright);shock.assembly->add(shock.shaft);
        shock.spring=Mesh::create(springGeometry(),springMat);shock.spring->position.y=.06f;shock.spring->frustumCulled=false;shock.assembly->add(shock.spring);
        auto seatGeometry=CylinderGeometry::create(.099f,.099f,.024f,14);
        auto topSeat=Mesh::create(seatGeometry,dark);topSeat->position.y=.06f;shock.assembly->add(topSeat);
        shock.lowerSeat=Mesh::create(seatGeometry,dark);shock.assembly->add(shock.lowerSeat);
        auto eyeGeometry=TorusGeometry::create(.041f,.013f,6,12);
        auto eye=Mesh::create(eyeGeometry,dark);shock.assembly->add(eye);shock.lowerEye=Mesh::create(eyeGeometry,dark);shock.assembly->add(shock.lowerEye);
        auto pinGeometry=CylinderGeometry::create(.022f,.022f,.11f,8);auto pin=Mesh::create(pinGeometry,bright);pin->rotation.x=1.5707963f;shock.assembly->add(pin);
        // Piggyback reservoir and protected fluid passage stay with the body of
        // the damper. They do not stretch with its polished piston shaft.
        auto reservoir=Mesh::create(CylinderGeometry::create(.043f,.043f,.24f,12),dark);reservoir->position.set(.137f,.205f,0);shock.assembly->add(reservoir);
        for(float y:{.10f,.31f}){auto cap=Mesh::create(CylinderGeometry::create(.046f,.046f,.018f,12),bright);cap->position.set(.137f,y,0);shock.assembly->add(cap);}
        auto passage=Mesh::create(CylinderGeometry::create(.018f,.018f,.137f,8),dark);passage->rotation.z=1.5707963f;passage->position.set(.0685f,.09f,0);shock.assembly->add(passage);
        for(float y:{.075f,.105f,.135f}){auto preload=Mesh::create(TorusGeometry::create(.053f,.004f,4,12),bright);preload->rotation.x=1.5707963f;preload->position.y=y;shock.assembly->add(preload);}
        shock.lowerPin=Mesh::create(pinGeometry,bright);shock.lowerPin->rotation.x=1.5707963f;shock.assembly->add(shock.lowerPin);
        shock.bridge=Mesh::create(CylinderGeometry::create(.025f,.025f,1,8),dark);body.add(shock.bridge);
        auto brace=Mesh::create(CylinderGeometry::create(.035f,.035f,1,8),dark);fitLink(*brace,{side*(dims.armPivotX-.04f),.75f,a.z},shock.top);body.add(brace);rig.fixedMeshes.push_back(brace.get());
        rig.shocks.push_back(shock);
        if(i<2){auto tie=strut(.018f,bright);rig.steering.push_back({tie,{side*(dims.armPivotX-.17f),.49f,a.z-.24f},i});}
    }return rig;
}
inline void updateSuspension(SuspensionRig& rig,const std::array<WheelContact,4>& wheels,float steer){
    const auto& dims=rig.dimensions;
    for(auto& link:rig.arms){auto ball=wheels[link.wheel].local;ball.x+=(link.wheel%2?-1.f:1.f)*.20f;ball.y+=link.height;fitLink(*link.mesh,link.mount,ball);}
    for(int i=0;i<4;++i){auto lower=wheels[i].local;lower.x+=(i%2?-1.f:1.f)*.20f;lower.y+=lowerBallOffset;auto upper=lower.clone().add(Vector3(0,uprightHeight,0));
        if(i>1){float angle=std::asin((wheels[i].local.y+lowerBallOffset-armPivotY)/rearArmLength);upper=lower.clone().add(Vector3(0,uprightHeight*std::cos(angle),-uprightHeight*std::sin(angle)));
            float side=i%2?1.f:-1.f;fitLink(*rig.axles[i-2],{side*dims.halfTrack*.38f,.48f,-dims.halfWheelbase+.05f},wheels[i].local.clone().add(Vector3(-side*.21f,0,0)));}
        fitLink(*rig.uprights[i],lower,upper);rig.lowerJoints[i]->position.copy(lower);rig.upperJoints[i]->position.copy(upper);}
    for(auto& s:rig.shocks){auto lower=wheels[s.wheel].local;float side=s.wheel%2?1.f:-1.f;lower.x-=side*.20f;lower.y+=lowerBallOffset;
        Vector3 mount= s.wheel<2?Vector3(side*dims.armPivotX,armPivotY,wheelAnchor(s.wheel,dims).z):Vector3(side*(dims.halfTrack-.20f),armPivotY,rearPivotZFor(dims));auto foot=mount.clone().lerp(lower,.78f);auto axis=foot.clone().sub(s.top);s.length=axis.length();
        fitLink(*s.bridge,foot.clone().add(Vector3(0,0,-.0528f)),foot.clone().add(Vector3(0,0,.0528f)));
        s.assembly->position.copy(s.top);s.assembly->quaternion.setFromUnitVectors(Vector3(0,1,0),axis.normalize());
        const float extension=std::max(.04f,s.length-.35f);s.shaft->scale.y=extension;s.shaft->position.y=.35f+extension*.5f;
        shapeSpring(*s.spring->geometry(),s.length-.16f);s.lowerSeat->position.y=s.length-.10f;s.lowerEye->position.y=s.length;s.lowerPin->position.y=s.length;
    }
    for(auto& t:rig.steering){int i=t.wheel;float side=i%2?1.f:-1.f;Quaternion q;q.setFromAxisAngle(Vector3(0,1,0),steeringAngle(i,steer,dims));
        auto point=Vector3(-side*.20f,0,-.16f).applyQuaternion(q).add(wheels[i].local);auto rack=t.rack;rack.x+=steer*.1f;fitLink(*t.mesh,rack,point);}
}
}
