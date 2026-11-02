#pragma once
#include "RallyDetail.hpp"
#include "RallyVehicle.hpp"
#include "threepp/geometries/LatheGeometry.hpp"

namespace rally {
// Original, unbranded desert/gravel wheel. Profile/rim ratios are informed by
// racing tyre/beadlock references, not a dimensionally certified replica.
struct WheelResources {
    std::shared_ptr<BufferGeometry> carcass,tread,barrel,spoke,beadRing,mount,rotor,sidewall,markings;
    std::shared_ptr<Material> rubber,blocks,metal,ring,hardware,brake;
};
inline auto axleLathe(const std::vector<Vector2>& profile,int segments=64){
    auto g=LatheGeometry::create(profile,segments);g->rotateZ(-pi/2);return g;
}
inline auto annulus(float inner,float outer,float start,float end){
    return axleLathe({{outer,start},{outer,end},{inner,end},{inner,start},{outer,start}});
}
inline float treadRadius(float x){x=std::abs(x);if(x<.07f)return .523f-x*.025f;if(x<.14f)return .52125f-(x-.07f)*.13f;return .51215f-(x-.14f)*.65f;}
inline float sideWidth(float r){if(r<.33f)return .178f+(r-.255f)*(.017f/.075f);if(r<.40f)return .195f-(r-.33f)*(.002f/.07f);return .193f-(r-.40f)*(.010f/.06f);}
inline auto bevelTile(float width,float length,float height){
    float x=width*.5f,z=length*.5f,c=std::min(width,length)*.18f;
    std::vector<Vector2> outline={{-x+c,-z},{x-c,-z},{x,-z+c},{x,z-c},{x-c,z},{-x+c,z},{-x,z-c},{-x,-z+c}};
    std::vector<float> points;std::vector<unsigned> indices;
    for(int ring=0;ring<3;++ring)for(auto p:outline){float scale=ring==2?.88f:1;float y=ring==0?-height*.5f:ring==1?height*.28f:height*.5f;points.insert(points.end(),{p.x*scale,y,p.y*scale});}
    for(int ring=0;ring<2;++ring)for(unsigned i=0;i<8;++i){unsigned a=ring*8+i,b=ring*8+(i+1)%8,c=a+8,d=b+8;indices.insert(indices.end(),{a,c,b,b,c,d});}
    for(unsigned i=1;i<7;++i){indices.insert(indices.end(),{16,16+i+1,16+i});indices.insert(indices.end(),{0,i,i+1});}
    auto g=BufferGeometry::create();g->setAttribute("position",FloatBufferAttribute::create(points,3));g->setIndex(indices);auto flat=g->toNonIndexed();flat->computeVertexNormals();return flat;
}
inline auto curvedSidewallText(const std::string& text,float size,float centerAngle){
    auto g=TextGeometry::create(text,TextGeometry::Options(FontLoader{}.defaultFont(),size,2));g->center();auto* p=g->getAttribute<float>("position");
    for(unsigned i=0;i<p->count();++i){float u=p->getX(i),v=p->getY(i),r=.365f+v,a=centerAngle-u/.365f;p->setXYZ(i,sideWidth(r)+.0012f,r*std::cos(a),r*std::sin(a));}
    g->computeVertexNormals();return g;
}
inline WheelResources makeWheelResources(){
    WheelResources w;
    auto standard=[](unsigned color,float rough,float metal){auto m=MeshStandardMaterial::create();m->color=Color(color);m->roughness=rough;m->metalness=metal;return m;};
    auto rubber=standard(0x292d2c,.94f,0);rubber->vertexColors=true;w.rubber=rubber;
    w.blocks=standard(0x303430,.93f,0);w.metal=standard(0x7e877f,.43f,.72f);w.ring=standard(0xabb0a3,.38f,.78f);w.hardware=standard(0xaaa18a,.4f,.75f);w.brake=standard(0x535a55,.56f,.65f);
    w.carcass=axleLathe({{.230f,-.145f},{.251f,-.174f},{.290f,-.189f},{.330f,-.195f},{.400f,-.193f},{.460f,-.183f},{.500f,-.158f},{.515f,-.120f},{.521f,-.070f},{.523f,0.f},
        {.521f,.070f},{.515f,.120f},{.500f,.158f},{.460f,.183f},{.400f,.193f},{.330f,.195f},{.290f,.189f},{.251f,.174f},{.230f,.145f},
        {.242f,.132f},{.330f,.163f},{.450f,.151f},{.491f,.108f},{.498f,0.f},{.491f,-.108f},{.450f,-.151f},{.330f,-.163f},{.242f,-.132f},{.230f,-.145f}});
    auto* p=w.carcass->getAttribute<float>("position");std::vector<float> color;
    for(unsigned i=0;i<p->count();++i){float a=std::atan2(p->getZ(i),p->getY(i));float v=.91f+.065f*std::sin(a*17+p->getX(i)*33)+.025f*std::sin(a*39);color.insert(color.end(),{v,v,v*.985f});}w.carcass->setAttribute("color",FloatBufferAttribute::create(color,3));
    w.tread=bevelTile(.066f,.063f,.017f);
    w.barrel=axleLathe({{.235f,-.170f},{.238f,-.158f},{.228f,-.146f},{.228f,.146f},{.240f,.166f},{.235f,.174f},{.216f,.148f},{.216f,-.146f},{.225f,-.170f},{.235f,-.170f}});
    w.beadRing=annulus(.208f,.250f,.163f,.181f);w.mount=annulus(.055f,.122f,.069f,.089f);w.rotor=annulus(.074f,.171f,.023f,.035f);
    auto spoke=bevelTile(.022f,.053f,.142f);auto* sp=spoke->getAttribute<float>("position");
    for(unsigned i=0;i<sp->count();++i){float y=sp->getY(i)+.145f;float t=std::clamp((y-.074f)/.142f,0.f,1.f);sp->setXYZ(i,sp->getX(i)+.075f+t*.073f,y,sp->getZ(i)*(1-t*.24f));}spoke->computeVertexNormals();w.spoke=spoke;
    std::vector<std::shared_ptr<BufferGeometry>> ribs;
    for(float radius:{.277f,.443f}){auto rib=TorusGeometry::create(radius,.0017f,4,64);rib->rotateY(pi/2);rib->translate(sideWidth(radius)+.0005f,0,0);ribs.push_back(rib);}w.sidewall=mergeBufferGeometries(ribs);
    w.markings=mergeBufferGeometries(std::vector<std::shared_ptr<BufferGeometry>>{curvedSidewallText("CINDER OFFROAD",.034f,0),curvedSidewallText("GRAVEL R/T",.027f,pi)});
    return w;
}
inline void addWheel(Group& pivot,Group& rolling,const WheelResources& w,int index){
    const float side=index%2?1.f:-1.f;
    rolling.add(Mesh::create(w.carcass,w.rubber));rolling.add(Mesh::create(w.barrel,w.metal));
    constexpr int stations=40,rows=6;auto tread=InstancedMesh::create(w.tread,w.blocks,stations*rows);
    constexpr float across[]={-.173f,-.126f,-.044f,.044f,.126f,.173f};
    for(int row=0;row<rows;++row)for(int i=0;i<stations;++i){float x=across[row],a=(i+(row%2?.46f:0))*2*pi/stations;
        float slope=(treadRadius(x+.001f)-treadRadius(x-.001f))/.002f;Object3D block;Quaternion spin,tilt;spin.setFromAxisAngle(Vector3(1,0,0),a);tilt.setFromAxisAngle(Vector3(0,0,1),std::atan(slope));block.quaternion.copy(spin).multiply(tilt);
        auto normal=Vector3(0,1,0).applyQuaternion(block.quaternion);block.position.set(x,treadRadius(x)*std::cos(a),treadRadius(x)*std::sin(a));block.position.addScaledVector(normal,.0065f);
        block.scale.set(row==0||row==5?.46f:1,1,1+(i%3-1)*.055f);block.updateMatrix();int k=row*stations+i;tread->setMatrixAt(k,*block.matrix);float shade=.91f+(i%5)*.018f;tread->setColorAt(k,Color(shade,shade,shade*.97f));}
    tread->instanceMatrix()->needsUpdate();tread->instanceColor()->needsUpdate();rolling.add(tread);
    auto face=Group::create();face->rotation.y=side<0?pi:0;rolling.add(face);
    face->add(Mesh::create(w.beadRing,w.ring));face->add(Mesh::create(w.mount,w.metal));face->add(Mesh::create(w.sidewall,w.blocks));
    auto labelMaterial=MeshStandardMaterial::create();labelMaterial->color=Color(0x454b43);labelMaterial->roughness=1;labelMaterial->side=Side::Double;face->add(Mesh::create(w.markings,labelMaterial));
    auto spokes=InstancedMesh::create(w.spoke,w.metal,8);for(int i=0;i<8;++i){Object3D o;o.rotation.x=i*pi/4;o.updateMatrix();spokes->setMatrixAt(i,*o.matrix);}spokes->instanceMatrix()->needsUpdate();face->add(spokes);
    auto boltGeometry=CylinderGeometry::create(.009f,.009f,.012f,6);boltGeometry->rotateZ(pi/2);
    auto bolts=InstancedMesh::create(boltGeometry,w.hardware,24);for(int i=0;i<24;++i){float a=i*2*pi/24;Object3D o;o.position.set(.188f,.232f*std::cos(a),.232f*std::sin(a));o.rotation.x=a;o.updateMatrix();bolts->setMatrixAt(i,*o.matrix);}bolts->instanceMatrix()->needsUpdate();face->add(bolts);
    auto lugGeometry=CylinderGeometry::create(.012f,.012f,.018f,6);lugGeometry->rotateZ(pi/2);auto lugs=InstancedMesh::create(lugGeometry,w.hardware,5);
    for(int i=0;i<5;++i){float a=i*2*pi/5;Object3D o;o.position.set(.097f,.094f*std::cos(a),.094f*std::sin(a));o.updateMatrix();lugs->setMatrixAt(i,*o.matrix);}lugs->instanceMatrix()->needsUpdate();face->add(lugs);
    auto cap=Mesh::create(CylinderGeometry::create(.052f,.052f,.072f,20),w.brake);cap->rotation.z=pi/2;cap->position.x=.095f;face->add(cap);
    face->add(Mesh::create(w.rotor,w.ring));
    auto valve=Mesh::create(CylinderGeometry::create(.005f,.005f,.024f,8),w.brake);valve->rotation.z=-pi/2;valve->position.set(.183f,.200f*std::cos(.72f),.200f*std::sin(.72f));face->add(valve);
    // The caliper steers with the upright, but does not spin with the wheel.
    auto caliper=Mesh::create(BoxGeometry::create(.060f,.096f,.061f),w.brake);caliper->position.set(side*.035f,0,index<2?-.153f:.153f);caliper->name="fixed-brake-caliper";pivot.add(caliper);
}
}
