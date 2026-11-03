#pragma once
#include "RallyVehicle.hpp"

namespace rally {
enum class SuspensionProfile { Legacy, Safari };
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
    std::shared_ptr<Mesh> topPin,lowerNeck;std::shared_ptr<Group> lowerClevis;
    std::array<std::shared_ptr<Mesh>,2> saddleBraces;
    Vector3 top;int wheel;float length=0;
    Vector3 nominalPinAxis{0,0,1};
    float barrelLength=.31f,shaftStart=.35f,springStart=.06f,lowerInboard=0;
};
struct TieRod {std::shared_ptr<Mesh> mesh;Vector3 rack;int wheel;};
struct SuspensionRig {
    VehicleDimensions dimensions=buggyDimensions;
    SuspensionProfile profile=SuspensionProfile::Legacy;
    std::vector<SuspensionLink> arms;std::vector<Coilover> shocks;
    std::array<std::shared_ptr<Mesh>,4> uprights,lowerJoints,upperJoints;
    std::array<std::shared_ptr<Mesh>,2> axles;
    std::vector<TieRod> steering;
    std::vector<Mesh*> fixedMeshes;
};
inline Vector3 coiloverFoot(int wheel,const Vector3& hub,const VehicleDimensions& dims,float inboard=0){
    const float side=wheel%2?1.f:-1.f;auto lower=hub;lower.x-=side*.20f;lower.y+=lowerBallOffset;
    const Vector3 mount=wheel<2?Vector3(side*dims.armPivotX,armPivotY,wheelAnchor(wheel,dims).z):Vector3(side*(dims.halfTrack-.20f),armPivotY,rearPivotZFor(dims));
    auto foot=mount.clone().lerp(lower,.78f);foot.x-=side*inboard;return foot;
}
// Real annular clevis plates, with an open pin bore rather than painted discs.
inline auto clevisPlate(){
    constexpr int segments=20;std::vector<float> p;std::vector<unsigned> index;
    for(float z:{-.005f,.005f})for(float r:{.0235f,.050f})for(int i=0;i<segments;++i){float a=i*6.2831853f/segments;p.insert(p.end(),{r*std::cos(a),r*std::sin(a),z});}
    for(unsigned i=0;i<segments;++i){unsigned j=(i+1)%segments;
        for(auto face:std::array<std::array<unsigned,4>,4>{{{i,j,segments+j,segments+i},{2*segments+i,3*segments+i,3*segments+j,2*segments+j},{i,2*segments+i,2*segments+j,j},{segments+i,segments+j,3*segments+j,3*segments+i}}})index.insert(index.end(),{face[0],face[1],face[2],face[0],face[2],face[3]});}
    auto g=BufferGeometry::create();g->setAttribute("position",FloatBufferAttribute::create(p,3));g->setIndex(index);g->computeVertexNormals();return g;
}
inline SuspensionRig addSuspension(Group& body,const VehicleDimensions& dims=buggyDimensions,SuspensionProfile profile=SuspensionProfile::Legacy){
    auto dark=MeshStandardMaterial::create();dark->color=Color(0x303738);dark->metalness=.65f;dark->roughness=.5f;
    auto bright=MeshStandardMaterial::create();bright->color=Color(0xb1b5ae);bright->metalness=.9f;bright->roughness=.22f;
    auto springMat=MeshStandardMaterial::create();springMat->color=Color(0xddd7bb);springMat->metalness=.4f;springMat->roughness=.42f;
    auto rubber=MeshStandardMaterial::create();rubber->color=Color(0x131a1b);rubber->roughness=.7f;
    SuspensionRig rig;rig.dimensions=dims;rig.profile=profile;const bool safari=profile==SuspensionProfile::Safari;
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
        Coilover shock;shock.wheel=i;shock.top=safari&&i<2?Vector3(side*dims.armPivotX,.94f,a.z):Vector3(side*dims.armPivotX,1.14f,a.z+(i<2?-.22f:.15f));shock.assembly=Group::create();body.add(shock.assembly);
        if(safari){shock.barrelLength=i<2?.42f:.58f;shock.shaftStart=.12f+shock.barrelLength;shock.springStart=.14f;shock.lowerInboard=i>1?.06f:0;}
        shock.barrel=Mesh::create(CylinderGeometry::create(.049f,.049f,shock.barrelLength,12),rubber);shock.barrel->position.y=safari?.12f+shock.barrelLength*.5f:.20f;shock.assembly->add(shock.barrel);
        if(safari){auto neck=Mesh::create(CylinderGeometry::create(.028f,.028f,.09f,12),dark);neck->position.y=.075f;shock.assembly->add(neck);
            shock.lowerNeck=Mesh::create(CylinderGeometry::create(.028f,.028f,.045f,12),bright);shock.assembly->add(shock.lowerNeck);}
        shock.shaft=Mesh::create(CylinderGeometry::create(.018f,.018f,1,10),bright);shock.assembly->add(shock.shaft);
        shock.spring=Mesh::create(springGeometry(),springMat);shock.spring->position.y=shock.springStart;shock.spring->frustumCulled=false;shock.assembly->add(shock.spring);
        auto seatGeometry=CylinderGeometry::create(.099f,.099f,.024f,14);
        auto topSeat=Mesh::create(seatGeometry,dark);topSeat->position.y=shock.springStart;shock.assembly->add(topSeat);
        shock.lowerSeat=Mesh::create(seatGeometry,dark);shock.assembly->add(shock.lowerSeat);
        auto eyeGeometry=TorusGeometry::create(.041f,.013f,6,12);
        auto eye=Mesh::create(eyeGeometry,dark);shock.assembly->add(eye);shock.lowerEye=Mesh::create(eyeGeometry,dark);shock.assembly->add(shock.lowerEye);
        auto pinGeometry=CylinderGeometry::create(.022f,.022f,.11f,8);auto pin=Mesh::create(pinGeometry,bright);pin->rotation.x=1.5707963f;shock.topPin=pin;
        if(safari){auto axis=coiloverFoot(i,hubAtTravel(i,dims.staticTravel,dims),dims,shock.lowerInboard).sub(shock.top).normalize();Quaternion q;q.setFromUnitVectors(Vector3(0,1,0),axis);shock.nominalPinAxis=Vector3(0,0,1).applyQuaternion(q);
            pin->position.copy(shock.top);pin->quaternion.setFromUnitVectors(Vector3(0,1,0),shock.nominalPinAxis);body.add(pin);rig.fixedMeshes.push_back(pin.get());
            auto bearing=Mesh::create(SphereGeometry::create(.027f,12,8),bright);bearing->position.copy(shock.top);body.add(bearing);rig.fixedMeshes.push_back(bearing.get());
            auto plates=Group::create();plates->position.copy(shock.top);plates->quaternion.setFromUnitVectors(Vector3(0,0,1),shock.nominalPinAxis);body.add(plates);
            for(float z:{-.026f,.026f}){auto ear=Mesh::create(clevisPlate(),dark);ear->position.z=z;ear->name="safari.upper-clevis";plates->add(ear);rig.fixedMeshes.push_back(ear.get());}
        }else shock.assembly->add(pin);
        // Piggyback reservoir and protected fluid passage stay with the body of
        // the damper. They do not stretch with its polished piston shaft.
        const float reservoirX=safari?-side*.137f:.137f;
        auto reservoir=Mesh::create(CylinderGeometry::create(.043f,.043f,safari?.28f:.24f,12),dark);reservoir->position.set(reservoirX,safari?.30f:.205f,0);shock.assembly->add(reservoir);
        for(float y:safari?std::array<float,2>{.15f,.45f}:std::array<float,2>{.10f,.31f}){auto cap=Mesh::create(CylinderGeometry::create(.046f,.046f,.018f,12),bright);cap->position.set(reservoirX,y,0);shock.assembly->add(cap);}
        auto passage=Mesh::create(CylinderGeometry::create(.018f,.018f,.137f,8),dark);passage->rotation.z=1.5707963f;passage->position.set(reservoirX*.5f,safari?.17f:.09f,0);shock.assembly->add(passage);
        for(float y:safari?std::array<float,3>{.155f,.185f,.215f}:std::array<float,3>{.075f,.105f,.135f}){auto preload=Mesh::create(TorusGeometry::create(.053f,.004f,4,12),bright);preload->rotation.x=1.5707963f;preload->position.y=y;shock.assembly->add(preload);}
        shock.lowerPin=Mesh::create(pinGeometry,bright);shock.lowerPin->rotation.x=1.5707963f;
        if(safari){body.add(shock.lowerPin);shock.lowerClevis=Group::create();body.add(shock.lowerClevis);
            for(float z:{-.026f,.026f}){auto ear=Mesh::create(clevisPlate(),dark);ear->position.z=z;shock.lowerClevis->add(ear);}
            auto bearing=Mesh::create(SphereGeometry::create(.027f,12,8),bright);shock.lowerClevis->add(bearing);
            if(i>1)for(auto& brace:shock.saddleBraces){brace=Mesh::create(CylinderGeometry::create(.018f,.018f,1,8),dark);body.add(brace);}
        }else shock.assembly->add(shock.lowerPin);
        shock.bridge=Mesh::create(CylinderGeometry::create(.025f,.025f,1,8),dark);body.add(shock.bridge);
        if(!safari){auto brace=Mesh::create(CylinderGeometry::create(.035f,.035f,1,8),dark);fitLink(*brace,{side*(dims.armPivotX-.04f),.75f,a.z},shock.top);body.add(brace);rig.fixedMeshes.push_back(brace.get());}
        rig.shocks.push_back(shock);
        if(i<2){auto tie=strut(.018f,bright);rig.steering.push_back({tie,{side*(dims.armPivotX-.17f),.49f,a.z-.24f},i});}
    }
    if(safari){auto frame=[&](const Vector3& from,const Vector3& to,float radius,const std::string& name){auto mesh=Mesh::create(CylinderGeometry::create(radius,radius,1,10),dark);mesh->name=name;fitLink(*mesh,from,to);body.add(mesh);rig.fixedMeshes.push_back(mesh.get());};
        // Front rails continue to the existing rear hinge crossmember, so the
        // bonnet's towers have a chassis load path rather than floating braces.
        for(float side:{-1.f,1.f}){const float x=side*dims.armPivotX;
            frame({x,.34f,rearPickupZ},{x,.34f,1.65f},.0275f,"front.frame.safari-rail");
            for(float z:{1.11f,1.59f})frame({x,.36f,z},{side*.26f,.90f,1.35f},.0275f,"front.frame.safari-tower-leg");
            for(float z:{-.05f,.05f})frame({side*.26f,.90f,1.35f},{x-side*.04f,.92f,1.35f+z},.018f,"front.frame.safari-clevis-gusset");
            const auto& rear=rig.shocks[side<0?2:3];Quaternion clevis;clevis.setFromUnitVectors(Vector3(0,0,1),rear.nominalPinAxis);
            for(int j=0;j<2;++j){auto lug=Vector3(-side*.04f,-.02f,j?.05f:-.05f).applyQuaternion(clevis).add(rear.top);
                frame({side*.60f,.38f,j?-1.05f:-1.45f},lug,.0275f,"rear.frame.safari-shock-tower");}
        }
        frame({-dims.armPivotX,.34f,1.11f},{dims.armPivotX,.34f,1.11f},.030f,"front.frame.safari-crossmember");
        frame({-dims.armPivotX,.34f,1.59f},{dims.armPivotX,.34f,1.59f},.030f,"front.frame.safari-crossmember");
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
        Vector3 mount= s.wheel<2?Vector3(side*dims.armPivotX,armPivotY,wheelAnchor(s.wheel,dims).z):Vector3(side*(dims.halfTrack-.20f),armPivotY,rearPivotZFor(dims));auto foot=mount.clone().lerp(lower,.78f);foot.x-=side*s.lowerInboard;auto axis=foot.clone().sub(s.top);s.length=axis.length();
        if(rig.profile==SuspensionProfile::Safari&&s.wheel>1){auto bridge=foot.clone().add(Vector3(side*s.lowerInboard,0,0));fitLink(*s.bridge,bridge.clone().add(Vector3(-.022f,0,0)),bridge.clone().add(Vector3(.022f,0,0)));
        }else fitLink(*s.bridge,foot.clone().add(Vector3(0,0,-.0528f)),foot.clone().add(Vector3(0,0,.0528f)));
        s.assembly->position.copy(s.top);s.assembly->quaternion.setFromUnitVectors(Vector3(0,1,0),axis.normalize());
        const float extension=std::max(.04f,s.length-s.shaftStart),visible=rig.profile==SuspensionProfile::Safari?extension-.06f:extension;s.shaft->scale.y=visible;s.shaft->position.y=s.shaftStart+visible*.5f;
        shapeSpring(*s.spring->geometry(),rig.profile==SuspensionProfile::Legacy?s.length-.16f:s.length-s.springStart-.10f);s.lowerSeat->position.y=s.length-.10f;s.lowerEye->position.y=s.length;
        if(rig.profile==SuspensionProfile::Safari){auto pinAxis=s.nominalPinAxis;
            s.lowerNeck->position.y=s.length-.0575f;
            if(s.wheel>1){float angle=std::asin((wheels[s.wheel].local.y+lowerBallOffset-armPivotY)/rearArmLength)-std::asin((dims.staticTravel+lowerBallOffset-armPivotY)/rearArmLength);Quaternion arm;arm.setFromAxisAngle(Vector3(1,0,0),angle);pinAxis.applyQuaternion(arm);}
            s.lowerPin->position.copy(foot);s.lowerPin->quaternion.setFromUnitVectors(Vector3(0,1,0),pinAxis);s.lowerClevis->position.copy(foot);s.lowerClevis->quaternion.setFromUnitVectors(Vector3(0,0,1),pinAxis);
            if(s.wheel>1){auto bridge=foot.clone().add(Vector3(side*s.lowerInboard,0,0));for(int j=0;j<2;++j){auto lug=Vector3(side*.04f,-.02f,j?.05f:-.05f).applyQuaternion(s.lowerClevis->quaternion).add(foot);fitLink(*s.saddleBraces[j],bridge.clone().add(Vector3(j?.022f:-.022f,0,0)),lug);}}
        }else s.lowerPin->position.y=s.length;
    }
    for(auto& t:rig.steering){int i=t.wheel;float side=i%2?1.f:-1.f;Quaternion q;q.setFromAxisAngle(Vector3(0,1,0),steeringAngle(i,steer,dims));
        auto point=Vector3(-side*.20f,0,-.16f).applyQuaternion(q).add(wheels[i].local);auto rack=t.rack;rack.x+=steer*.1f;fitLink(*t.mesh,rack,point);}
}
}
