#pragma once
#include "RallySurface.hpp"
#include "threepp/extras/core/Shape.hpp"
#include "threepp/geometries/ExtrudeGeometry.hpp"

namespace rally {
// Static cabin furniture. Real openings in the moulded back let the shoulder
// webbing pass through; the front pads stop below those openings.
inline void addSafariSeats(Group& body){
    Shape outline;
    outline.moveTo(-.19f,0).lineTo(.19f,0)
        .quadraticCurveTo(.25f,.12f,.25f,.35f)
        .quadraticCurveTo(.25f,.43f,.15f,.50f)
        .lineTo(.15f,.61f).quadraticCurveTo(.15f,.67f,.09f,.67f)
        .lineTo(-.09f,.67f).quadraticCurveTo(-.15f,.67f,-.15f,.61f)
        .lineTo(-.15f,.50f).quadraticCurveTo(-.25f,.43f,-.25f,.35f)
        .quadraticCurveTo(-.25f,.12f,-.19f,0);
    for(float x:{-.085f,.085f}){
        auto slot=std::make_shared<Path>();slot->absellipse(x,.455f,.036f,.021f,0,2*pi,true);
        outline.holes.push_back(slot);
    }
    ExtrudeGeometry::Options options;options.depth=.026f;options.steps=1;
    options.curveSegments=8;options.bevelEnabled=true;
    options.bevelThickness=.005f;options.bevelSize=.007f;options.bevelSegments=2;
    auto shellGeometry=ExtrudeGeometry::create({outline},options);
    auto* positions=shellGeometry->getAttribute<float>("position");
    for(unsigned i=0;i<positions->count();++i){
        float x=positions->getX(i),y=positions->getY(i),z=positions->getZ(i);
        positions->setXYZ(i,x,.82f+y,-.57f-.17f*y+.08f*(x/.25f)*(x/.25f)+z);
    }
    shellGeometry->computeVertexNormals();
    auto shell=surfaceMaterial(0x181e1b,Surface::Paint,.62f,0);
    auto fabric=surfaceMaterial(0x2a302b,Surface::Rubber,.96f,0);
    fabric->normalScale.setScalar(.12f);
    auto webbing=surfaceMaterial(0xa95d32,Surface::Rubber,.91f,0);
    webbing->side=Side::Double;webbing->normalScale.setScalar(.10f);
    auto buckle=surfaceMaterial(0x858b83,Surface::Metal,.36f,.85f);
    auto padGeometry=SphereGeometry::create(1,20,12);
    for(float seatX:{-.4f,.4f}){
        auto seat=Group::create();seat->position.x=seatX;body.add(seat);
        seat->add(Mesh::create(shellGeometry,shell));
        auto pad=[&](Vector3 position,Vector3 scale){
            auto mesh=Mesh::create(padGeometry,fabric);mesh->position=position;mesh->scale=scale;seat->add(mesh);
        };
        pad({0,.82f,-.37f},{.195f,.075f,.25f});
        pad({0,1.045f,-.585f},{.17f,.155f,.039f});
        pad({0,1.405f,-.642f},{.118f,.067f,.028f});
        for(float side:{-1.f,1.f}){
            pad({side*.215f,.88f,-.40f},{.045f,.085f,.23f});
            pad({side*.211f,1.04f,-.525f},{.042f,.175f,.055f});
        }
        auto strap=[&](const std::vector<Vector3>& points,float width){
            std::vector<float> p,uv;std::vector<unsigned> indices;
            for(unsigned i=0;i<points.size();++i){const auto& v=points[i];
                p.insert(p.end(),{v.x-width*.5f,v.y,v.z,v.x+width*.5f,v.y,v.z});
                uv.insert(uv.end(),{0,static_cast<float>(i),1,static_cast<float>(i)});
                if(i){unsigned a=(i-1)*2;indices.insert(indices.end(),{a,a+1,a+2,a+1,a+3,a+2});}}
            auto g=BufferGeometry::create();g->setAttribute("position",FloatBufferAttribute::create(p,3));
            g->setAttribute("uv",FloatBufferAttribute::create(uv,2));g->setIndex(indices);g->computeVertexNormals();
            seat->add(Mesh::create(g,webbing));
        };
        for(float side:{-1.f,1.f}){
            strap({{side*.085f,1.288f,-.609f},{side*.10f,1.15f,-.532f},
                   {side*.085f,.96f,-.425f},{side*.035f,.878f,-.223f}},.031f);
            strap({{side*.22f,.887f,-.32f},{side*.11f,.88f,-.265f},{side*.035f,.878f,-.223f}},.034f);
        }
        auto latch=Mesh::create(BoxGeometry::create(.065f,.035f,.018f),buckle);
        latch->position.set(0,.882f,-.213f);seat->add(latch);
    }
}
}
