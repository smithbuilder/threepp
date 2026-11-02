#pragma once
#include "RallyDetail.hpp"

namespace rally {
struct Cockpit {std::shared_ptr<Group> steering,speedNeedle,rpmNeedle;};
inline Cockpit addCockpit(Group& body,float verticalOffset=0){
    auto cockpitRoot=Group::create();cockpitRoot->position.y=verticalOffset;body.add(cockpitRoot);
    Cockpit c;auto black=MeshStandardMaterial::create();black->color=Color(0x171f20);black->roughness=.82f;
    auto metal=MeshStandardMaterial::create();metal->color=Color(0x777e7a);metal->roughness=.42f;metal->metalness=.7f;
    auto ink=MeshBasicMaterial::create();ink->color=Color(0xe5debd);
    auto needleMat=MeshBasicMaterial::create();needleMat->color=Color(0xe7b64c);
    auto dash=Mesh::create(BoxGeometry::create(1.30f,.14f,.18f),black);dash->position.set(0,1.34f,.54f);cockpitRoot->add(dash);
    cockpitRoot->add(rod({-.40f,1.28f,.25f},{-.40f,1.12f,.67f},.027f,metal));
    auto column=Group::create();column->position.set(-.4f,1.28f,.25f);column->rotation.x=.28f;cockpitRoot->add(column);c.steering=Group::create();column->add(c.steering);
    c.steering->add(Mesh::create(TorusGeometry::create(.185f,.018f,8,32),black));
    for(int i=0;i<3;++i){float a=i*2*pi/3;auto spoke=rod({0,0,0},{.158f*std::sin(a),.158f*std::cos(a),0},.012f,metal);c.steering->add(spoke);}
    auto hub=Mesh::create(CylinderGeometry::create(.044f,.044f,.05f,12),black);hub->rotation.x=pi/2;c.steering->add(hub);
    auto gauge=[&](float x){auto root=Group::create();root->position.set(x,1.44f,.438f);root->rotation.y=pi;cockpitRoot->add(root);
        auto housing=Mesh::create(CylinderGeometry::create(.091f,.091f,.05f,24),black);housing->rotation.x=pi/2;housing->position.z=-.03f;root->add(housing);
        auto face=Mesh::create(CircleGeometry::create(.085f,24),black);root->add(face);
        auto rim=Mesh::create(TorusGeometry::create(.087f,.006f,6,24),metal);root->add(rim);
        for(int i=0;i<11;++i){float a=(-125+i*25.f)*pi/180;auto tick=Mesh::create(BoxGeometry::create(.004f,.012f,.003f),ink);tick->position.set(std::sin(a)*.068f,std::cos(a)*.068f,.002f);tick->rotation.z=-a;root->add(tick);}
        auto pointer=Group::create();root->add(pointer);auto bar=Mesh::create(BoxGeometry::create(.006f,.059f,.004f),needleMat);bar->position.set(0,.026f,.006f);pointer->add(bar);return pointer;
    };
    c.rpmNeedle=gauge(-.51f);c.speedNeedle=gauge(-.29f);return c;
}
inline void updateCockpit(Cockpit& c,float steer,float speed,float rpm){
    c.steering->rotation.z=-steer*2.2f;
    c.rpmNeedle->rotation.z=(125-250*std::clamp(rpm/7500.f,0.f,1.f))*pi/180;
    c.speedNeedle->rotation.z=(125-250*std::clamp(std::abs(speed)*3.6f/120.f,0.f,1.f))*pi/180;
}
}
