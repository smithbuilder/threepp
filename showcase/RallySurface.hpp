#pragma once
#include "threepp/threepp.hpp"
#include "threepp/extras/core/TextureBake.hpp"

namespace rally {
using namespace threepp;
// Original tileable surface detail. These maps add no geometry, shader pass or
// per-frame work. The three sets are shared by every matching buggy component.
enum class Surface {Paint,Metal,Rubber};
struct SurfaceMaps {std::shared_ptr<DataTexture> albedo,roughness,normal;};
inline SurfaceMaps makeSurfaceMaps(Surface kind){
    constexpr int size=256;constexpr float tau=6.2831853f;
    int seed=kind==Surface::Paint?317:kind==Surface::Metal?619:947;
    std::vector<unsigned char> color(size*size*4),rough(size*size*4);
    auto field=[=](float u,float v){return noise::fbm(u*8,v*8,8,seed,3);};
    for(int y=0;y<size;++y)for(int x=0;x<size;++x){float u=x/static_cast<float>(size),v=y/static_cast<float>(size);
        float broad=field(u,v),fine=noise::hash2(x,y,seed),dust=std::clamp((broad-.48f)*1.9f,0.f,.34f);
        // Sparse machining lines and mould grain stay below the large-scale
        // dust variation, so filtering leaves readable materials at game size.
        float brush=kind==Surface::Metal?(.5f+.5f*std::sin(v*tau*64))*.004f:0;
        float value=.98f-dust*(kind==Surface::Paint?.055f:.12f)+(fine-.5f)*.008f-brush;
        if(kind==Surface::Rubber)value=.94f+(broad-.5f)*.075f+(fine-.5f)*.018f;
        float r=kind==Surface::Paint?.87f+.10f*broad:kind==Surface::Metal?.78f+.18f*broad+brush:.77f+.22f*broad;
        int i=(y*size+x)*4;
        color[i]=noise::toByte(value);color[i+1]=noise::toByte(value-dust*.025f);color[i+2]=noise::toByte(value-dust*.065f);color[i+3]=255;
        rough[i]=rough[i+1]=rough[i+2]=noise::toByte(r);rough[i+3]=255;
    }
    SurfaceMaps result;result.albedo=DataTexture::create(color,size,size);result.roughness=DataTexture::create(rough,size,size);
    texgen::finishTexture(result.albedo,true,true,2);texgen::finishTexture(result.roughness,false,true,2);
    result.normal=DataTexture::create(4,size,size);
    texgen::writeNormalFromHeight(result.normal,size,1.4f,[=](float u,float v){
        float grain=noise::valueNoise(u*64,v*64,64,seed+1);
        if(kind==Surface::Metal)return .012f*std::sin(v*tau*64)+grain*.04f;
        if(kind==Surface::Paint)return field(u,v)*.025f+grain*.07f;
        return field(u,v)*.22f+grain*.32f;
    },true);
    texgen::finishTexture(result.normal,false,true,2);return result;
}
inline const SurfaceMaps& surfaceMaps(Surface kind){
    static const auto paint=makeSurfaceMaps(Surface::Paint),metal=makeSurfaceMaps(Surface::Metal),rubber=makeSurfaceMaps(Surface::Rubber);
    return kind==Surface::Paint?paint:kind==Surface::Metal?metal:rubber;
}
inline auto surfaceMaterial(unsigned color,Surface kind,float roughness,float metalness){
    auto m=MeshStandardMaterial::create();m->name=kind==Surface::Paint?"cinder.paint":kind==Surface::Metal?"cinder.metal":"cinder.rubber";
    m->color=Color(color);m->roughness=roughness;m->metalness=metalness;
    const auto& maps=surfaceMaps(kind);m->map=maps.albedo;m->roughnessMap=maps.roughness;m->normalMap=maps.normal;
    m->normalScale.setScalar(kind==Surface::Rubber?.28f:kind==Surface::Metal?.06f:.045f);return m;
}
// Custom unwrapped panels/tread pieces previously had no texture coordinates.
// Project each hard face in its dominant plane; existing generated UVs survive.
inline void ensureSurfaceUv(BufferGeometry& g){
    if(g.getAttribute<float>("uv"))return;
    auto* p=g.getAttribute<float>("position");auto* n=g.getAttribute<float>("normal");std::vector<float> uv;uv.reserve(p->count()*2);
    for(unsigned i=0;i<p->count();++i){float x=p->getX(i),y=p->getY(i),z=p->getZ(i);
        float nx=n?std::abs(n->getX(i)):0,ny=n?std::abs(n->getY(i)):1,nz=n?std::abs(n->getZ(i)):0;
        if(ny>=nx&&ny>=nz)uv.insert(uv.end(),{x,z});else if(nx>=nz)uv.insert(uv.end(),{z,y});else uv.insert(uv.end(),{x,y});}
    g.setAttribute("uv",FloatBufferAttribute::create(uv,2));
}
// Dust gathers on low bodywork. This is a restrained vertex tint, not a new
// dirt mesh or an all-over grunge overlay. Paint/metal maps remain reusable.
inline void weatherBody(Group& body){
    body.updateMatrixWorld(true);Matrix4 inverse=*body.matrixWorld;inverse.invert();
    body.traverseType<Mesh>([&](Mesh& mesh){auto* material=mesh.material()->as<MeshStandardMaterial>();if(!material||material->name.rfind("cinder.",0)!=0)return;
        auto g=mesh.geometry();ensureSurfaceUv(*g);auto* p=g->getAttribute<float>("position");auto transform=inverse;transform.multiply(*mesh.matrixWorld);
        std::vector<float> colors;colors.reserve(p->count()*3);
        for(unsigned i=0;i<p->count();++i){auto v=Vector3(p->getX(i),p->getY(i),p->getZ(i)).applyMatrix4(transform);
            float lower=std::clamp((1.18f-v.y)/.90f,0.f,1.f);float mottling=.65f+.35f*noise::valueNoise(v.x*5,v.z*5,256,128);
            float dust=lower*mottling*.21f;
            colors.insert(colors.end(),{1-dust*.12f,1-dust*.22f,1-dust*.45f});}
        g->setAttribute("color",FloatBufferAttribute::create(colors,3));material->vertexColors=true;
    });
}
}
