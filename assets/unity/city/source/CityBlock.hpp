#pragma once
#include "CityLayout.hpp"
#include "PlaygroundTerrain.hpp"
#include "RallyForest.hpp"
#include "threepp/threepp.hpp"
#include <map>

namespace city {
using namespace threepp;

// Merge static geometry by material. Facade detail never becomes thousands of
// individual draw calls. Opaque glazing avoids transparency sorting/overdraw.
struct Batch {
    std::shared_ptr<MeshStandardMaterial> material;
    std::vector<float> p,n,uv,c;std::vector<unsigned> index;
    float tile=0;
};
class Block {
    std::map<std::string,Batch> batches;
    std::shared_ptr<BoxGeometry> cube=BoxGeometry::create();
    std::shared_ptr<CylinderGeometry> tube=CylinderGeometry::create(1,1,1,8);
    std::array<std::shared_ptr<BufferGeometry>,3> treeBark,treeLeaves;
    Batch& material(const std::string& id,unsigned color,float roughness= .85f,float metal=0){
        auto& b=batches[id];b.material=MeshStandardMaterial::create();b.material->color=Color(color);
        b.material->roughness=roughness;b.material->metalness=metal;b.material->vertexColors=true;return b;
    }
    void add(const std::string& id,const BufferGeometry& g,Vector3 pos,Vector3 scale,float yaw=0,float tint=1,int sign=-1){
        auto& b=batches.at(id);const auto* a=g.getAttribute<float>("position");const auto* normal=g.getAttribute<float>("normal");const auto* tex=g.getAttribute<float>("uv");
        unsigned base=static_cast<unsigned>(b.p.size()/3);const float cs=std::cos(yaw),sn=std::sin(yaw);
        for(unsigned i=0;i<a->count();++i){float x=a->getX(i)*scale.x,y=a->getY(i)*scale.y,z=a->getZ(i)*scale.z;
            b.p.insert(b.p.end(),{pos.x+x*cs+z*sn,pos.y+y,pos.z-x*sn+z*cs});
            Vector3 nn(normal->getX(i)/scale.x,normal->getY(i)/scale.y,normal->getZ(i)/scale.z);nn.normalize();
            b.n.insert(b.n.end(),{nn.x*cs+nn.z*sn,nn.y,-nn.x*sn+nn.z*cs});
            float u=tex?tex->getX(i):0,v=tex?tex->getY(i):0;
            if(b.tile>0){float sx=std::abs(nn.x)>.5f?scale.z:scale.x,sy=std::abs(nn.y)>.5f?scale.z:scale.y;u*=sx/b.tile;v*=sy/b.tile;}
            if(sign>=0){u=.01f+u*.98f;v=(7-sign+.04f+v*.92f)/8.f;}
            b.uv.insert(b.uv.end(),{u,v});
            // Soft contact darkening at the foot of masonry, authored in the
            // vertex data rather than adding another real-time render pass.
            float ao=id.starts_with("brick")||id=="plaster"?.80f+.20f*std::clamp((pos.y+y)/4.f,0.f,1.f):1;
            const float shadow=shade(pos.x+x*cs+z*sn+(nn.x*cs+nn.z*sn)*.04f,pos.y+y+nn.y*.04f,pos.z-x*sn+z*cs+(-nn.x*sn+nn.z*cs)*.04f);
            const auto* colors=(id=="leaf"||id=="bark")?g.getAttribute<float>("color"):nullptr;
            float variation=.96f+.04f*std::sin((pos.x+x*cs+z*sn)*.31f+(pos.z-x*sn+z*cs)*.17f);
            b.c.insert(b.c.end(),{tint*ao*shadow*variation*(colors?colors->getX(i):1),tint*ao*shadow*variation*(colors?colors->getY(i):1),tint*ao*shadow*variation*(colors?colors->getZ(i):1)});
        }
        if(g.hasIndex()){auto* ix=g.getIndex();for(unsigned i=0;i<ix->count();++i)b.index.push_back(base+ix->getX(i));}
        else for(unsigned i=0;i<a->count();++i)b.index.push_back(base+i);
    }
    void box(const std::string& m,float x,float y,float z,float w,float h,float d,float yaw=0,float tint=1,int sign=-1){add(m,*cube,{x,y,z},{w,h,d},yaw,tint,sign);}
    void pole(const std::string& m,float x,float y,float z,float r,float h){add(m,*tube,{x,y,z},{r,h,r});}
    void roadPatch(float x,float z,int seed){
        auto g=BufferGeometry::create();std::vector<float> p{x,.012f,z},n{0,1,0},uv{x,z};std::vector<unsigned> ix;
        for(int i=0;i<=8;++i){float a=(i%8)*6.2831853f/8,r=1+.16f*std::sin((i%8)*7.3f+seed*1.91f);
            float xx=x+std::cos(a)*.62f*r,zz=z+std::sin(a)*1.45f*r;p.insert(p.end(),{xx,.012f,zz});n.insert(n.end(),{0,1,0});uv.insert(uv.end(),{xx,zz});if(i<8)ix.insert(ix.end(),{0,unsigned(i+2),unsigned(i+1)});}
        g->setAttribute("position",FloatBufferAttribute::create(p,3));g->setAttribute("normal",FloatBufferAttribute::create(n,3));g->setAttribute("uv",FloatBufferAttribute::create(uv,2));g->setIndex(ix);
        add("repair",*g,{0,0,0},{1,1,1});
    }
    void roadCrack(float x,float z,int seed){
        for(int i=0;i<11;++i){float nx=x+std::sin(seed*2.1f+i*1.87f)*.32f,nz=z+.65f+.35f*(1+std::sin(i*3.4f+seed));
            float dx=nx-x,dz=nz-z;box("dark",(x+nx)*.5f,.009f,(z+nz)*.5f,.022f,.008f,std::hypot(dx,dz),std::atan2(dx,dz));
            if(i%4==1)box("dark",nx+.23f,.009f,nz+.12f,.014f,.008f,.65f,1.06f);
            x=nx;z=nz;}
    }
    void contextBuilding(float x,float z,float w,float d,float h,int finish){
        const char* m=finish%2?"brick-buff":"brick-red";box(m,x,h*.5f,z,w,h,d,0,.75f+(finish%3)*.06f);box("roof",x,h+.05f,z,w+.12f,.15f,d+.12f);
        for(float side:{-1.f,1.f})for(float y=5;y<h-1;y+=3.3f){
            for(float u=-w*.5f+2;u<w*.5f-1;u+=3.4f)box("glass",x+u,y,z+side*(d*.5f+.025f),1.3f,1.9f,.035f,0,.65f+.06f*std::sin(u*3+y));
            for(float u=-d*.5f+2;u<d*.5f-1;u+=3.4f)box("glass",x+side*(w*.5f+.025f),y,z+u,.035f,1.9f,1.3f,0,.65f+.06f*std::sin(u*3+y));}
    }
    void tree(float x,float z,int variant){
        box("soil",x,.19f,z,1.65f,.04f,1.65f);box("metal",x,.22f,z,1.8f,.045f,1.8f);
        box("soil",x,.25f,z,1.4f,.035f,1.4f);
        const int species=variant%3;
        if(!treeBark[species]){vegetation::TreeParams p;vegetation::applyPreset(0,p);p.seed=427+species*79;
            p.trunkHeight=2.6f;p.trunkRadius=.13f;p.crownRadiusX=1.5f;p.crownRadiusZ=1.35f;p.crownHeight=3.3f;
            p.attractorCount=330;p.influenceDistance=1.7f;p.killDistance=.24f;p.segmentLength=.21f;p.maxIterations=140;p.radialSegments=5;
            p.leafSize=.53f;p.leavesPerCluster=3;p.leafDensity=.96f;p.leafSpread=.19f;p.leafAtlasCells=2;
            p.foliageOcclusion=.5f;
            p.leafColor={1,1,1};p.barkColor={1,1,1};p.leafShape=vegetation::LeafShape::Lobed;
            vegetation::TreeGenerator generator(p.seed);generator.buildSkeleton(p);
            treeBark[species]=generator.makeTrunkGeometry(p);treeLeaves[species]=generator.makeLeafGeometry(p);
            rally::forest_detail::refineCanopyGeometry(*treeLeaves[species],p);
        }
        float s=.9f+.065f*(variant%4);Vector3 scale(s,s,s);float yaw=variant*1.37f+x*.07f;
        add("bark",*treeBark[species],{x,.25f,z},scale,yaw);
        add("leaf",*treeLeaves[species],{x,.25f,z},scale,yaw,.90f+.035f*(variant%3));
    }
    void lamp(float x,float z,float yaw){
        pole("metal",x,2.8f,z,.07f,5.3f);pole("metal",x,.35f,z,.14f,.5f);
        box("metal",x+std::sin(yaw)*.68f,5.42f,z+std::cos(yaw)*.68f,.11f,.1f,1.5f,yaw);
        box("metal",x+std::sin(yaw)*1.35f,5.34f,z+std::cos(yaw)*1.35f,.5f,.16f,.9f,yaw);
        box("lamp",x+std::sin(yaw)*1.35f,5.24f,z+std::cos(yaw)*1.35f,.35f,.025f,.68f,yaw);
    }
    void bench(float x,float z,float yaw){
        for(int i=0;i<5;++i)box("wood",x,.67f,z+(i-2)*.095f,1.8f,.065f,.075f,yaw);
        for(float dx:{-.67f,.67f}){box("metal",x+dx,.42f,z,.055f,.5f,.48f);box("metal",x+dx,1,z+.25f,.055f,.75f,.05f);}
        for(int i=0;i<3;++i)box("wood",x,.91f+i*.14f,z+.25f,1.8f,.105f,.055f,yaw);
    }
    void facade(const Building& b,float yaw,float span,float depth,int label){
        float cs=std::cos(yaw),sn=std::sin(yaw);
        auto part=[&](const std::string& m,float u,float y,float out,float w,float h,float d,float tint=1,int sign=-1){
            float localZ=depth*.5f+out;box(m,b.x+u*cs+localZ*sn,.16f+y,b.z-u*sn+localZ*cs,w,h,d,yaw,tint,sign);};
        int bays=std::max(2,int(span/3.4f)),floors=int((b.h-4.2f)/3.25f);float spacing=(span-1.5f)/bays;
        const std::string masonry=b.finish==0?"brick-red":b.finish==1?"brick-buff":"plaster";
        // Model the facade around its openings. The main wall core sits behind
        // these piers, leaving real depth between the masonry and window panes.
        float left=-span*.5f;
        for(int k=0;k<bays;++k){float u=(k-(bays-1)*.5f)*spacing,right=u-.85f;
            if(right>left)part(masonry,(left+right)*.5f,(b.h+4)*.5f,0,right-left,b.h-4,.28f);
            left=u+.85f;}
        if(left<span*.5f)part(masonry,(left+span*.5f)*.5f,(b.h+4)*.5f,0,span*.5f-left,b.h-4,.28f);
        float below=4;
        for(int floor=0;floor<floors;++floor){float lo=5.5f+floor*3.25f-1.18f;
            if(lo>below)part(masonry,0,(below+lo)*.5f,0,span,lo-below,.28f);below=lo+2.36f;}
        if(b.h>below)part(masonry,0,(below+b.h)*.5f,0,span,b.h-below,.28f);
        for(int k=0;k<=bays;++k)part(masonry,(k-bays*.5f)*spacing,2.1f,.02f,.28f,3.65f,.32f);
        part("stone",0,.5f,.08f,span,.85f,.22f);
        part("stone",0,3.9f,.20f,span+.2f,.26f,.42f);
        part("dark",0,3.68f,.1f,span,.12f,.20f);
        for(int k=0;k<bays;++k){float u=(k-(bays-1)*.5f)*spacing;
            part("dark",u,1.95f,-.18f,spacing-.35f,2.65f,.08f);
            part("glass",u,1.95f,-.11f,spacing-.53f,2.47f,.065f,.73f+(k%3)*.12f);
            part("metal",u,1.95f,.015f,.065f,2.65f,.085f);
            part("metal",u,1.13f,.015f,spacing-.35f,.06f,.085f);
            if(k==bays/2){part("stone",u,.20f,.42f,spacing-.3f,.13f,.85f);part("brass",u+.34f,1.55f,.22f,.035f,.5f,.035f);}
            for(int floor=0;floor<floors;++floor){float y=5.5f+floor*3.25f;
                const int treatment=(k*7+floor*3+b.finish)%11;
                part("dark",u,y,-.18f,1.7f,2.35f,.065f);
                part(treatment==2?"litglass":"glass",u,y,-.11f,1.45f,2.05f,.07f,.65f+((k+floor*3)%5)*.08f);
                part("stone",u,y-1.2f,.22f,1.95f,.17f,.46f);
                part("stone",u,y+1.23f,.12f,1.95f,.14f,.28f);
                part("frame",u,y,.015f,.055f,2.1f,.055f);part("frame",u,y+.25f,.015f,1.45f,.05f,.055f);
                if(treatment<4){part("curtain",u-.48f,y,-.045f,.22f,1.98f,.015f);part("curtain",u+.48f,y,-.045f,.22f,1.98f,.015f);}
                if(treatment==6)for(int j=0;j<5;++j)part("curtain",u,y+.84f-j*.095f,-.035f,1.4f,.05f,.015f);
                if(treatment==8&&floor<2){part("metal",u,y-.82f,.38f,.85f,.36f,.68f);for(int j=0;j<5;++j)part("dark",u-.32f+j*.16f,y-.82f,.73f,.025f,.25f,.015f);}
            }
        }
        if(label>=0){part("sign",0,3.32f,.29f,std::min(span-1.2f,11.f),.93f,.16f,1,label);
            // Canvas canopy with a valance and slim supports.
            part(label==0?"awning":"dark",0,2.96f,1.0f,span-.75f,.13f,1.8f);
            part(label==0?"awning":"dark",0,2.77f,1.88f,span-.75f,.34f,.07f);
        }
        part("dark",0,b.h-.47f,.09f,span+.25f,.18f,.25f);
        part("stone",0,b.h-.16f,.18f,span+.45f,.28f,.44f);
        if(label==1&&yaw< -1){
            const float u=-spacing*.5f;
            for(int floor=0;floor<floors;++floor){float y=4.35f+floor*3.25f;
                part("metal",u,y,.83f,2.4f,.08f,1.7f);
                for(float side:{-1.f,1.f}){part("metal",u+side*1.12f,y+.5f,1.58f,.045f,1,.045f);part("metal",u+side*1.12f,y+.95f,.83f,.045f,.045f,1.7f);}
                part("metal",u,y+.95f,1.58f,2.3f,.045f,.045f);part("metal",u,y+.42f,1.58f,2.3f,.035f,.035f);
                for(float side:{-1.f,1.f})part("metal",u+.7f+side*.32f,y-1.55f,1.36f,.045f,3.2f,.045f);
                for(int j=0;j<11;++j)part("metal",u+.7f,y-j*.29f,1.36f,.64f,.04f,.04f);
            }
        }
    }
public:
    std::shared_ptr<Group> root=Group::create();size_t triangles=0,draws=0;
    explicit Block(const std::filesystem::path& assets,const playground::Terrain& terrain){
        material("asphalt",0xc8cbcb,1).tile=4.5f;
        material("paving",0xffffff,.94f).tile=4;
        material("brick-red",0xffffff,.94f).tile=1.65f;
        material("brick-buff",0xffffff,.94f).tile=1.65f;
        material("plaster",0xe7e1cf,.93f).tile=5;
        material("stone",0xb3b0a0);material("dark",0x222928);material("metal",0x343c3b,.58f,.55f);
        material("glass",0x667a7c,.19f,.25f);material("frame",0x9c978a,.62f,.15f);
        material("litglass",0x6c6a5c,.38f,.12f);material("white",0xc9c5b2,.97f);material("yellow",0xc29a42,.96f);
        material("wood",0x795337,.88f);material("bark",0xffffff);material("leaf",0xffffff);
        material("curtain",0xa6a393,.95f);material("roof",0x616460,.94f).tile=5;
        material("repair",0x7b7f7e,.94f).tile=4.5f;
        material("soil",0x3d4034);material("awning",0x3a6158);material("brass",0xa68c50,.35f,.65f);
        material("sign",0xffffff,.75f);material("lamp",0xffe3a0,.4f);material("red",0xa64428);
        batches.at("lamp").material->emissive=Color(0xffcc71);batches.at("lamp").material->emissiveIntensity=.6f;
        TextureLoader loader;
        std::map<std::string,std::shared_ptr<Texture>> photoMaps;
        for(auto [id,file]:std::vector<std::pair<std::string,std::string>>{{"asphalt","asphalt.jpg"},{"paving","paving.jpg"},{"brick-red","brick.jpg"},{"brick-buff","buff-brick.jpg"},{"plaster","concrete.jpg"},{"sign","signs.png"}}){
            auto t=loader.load(assets/"city"/file);if(!t)throw std::runtime_error("Missing city texture: "+file);
            t->colorSpace=ColorSpace::sRGB;t->wrapS=t->wrapT=TextureWrapping::Repeat;t->anisotropy=4;batches.at(id).material->map=t;}
        for(auto [id,prefix]:std::vector<std::pair<std::string,std::string>>{{"asphalt","asphalt"},{"repair","cracked"},{"brick-red","red-brick"},{"brick-buff","buff-brick"},{"plaster","plaster"},{"bark","bark"},{"roof","plaster"}}){
            auto& m=*batches.at(id).material;
            auto load=[&](const std::string& kind,bool color){std::string file="ph-"+prefix+"-"+kind+".jpg";auto& t=photoMaps[file];if(!t){t=loader.load(assets/"city"/file);if(!t)throw std::runtime_error("Missing city PBR map");t->wrapS=t->wrapT=TextureWrapping::Repeat;t->anisotropy=4;if(color)t->colorSpace=ColorSpace::sRGB;}return t;};
            m.map=load("color",true);m.normalMap=load("normal",false);m.roughnessMap=load("roughness",false);m.normalScale.set(.55f,.55f);
        }
        auto& foliage=*batches.at("leaf").material;rally::forest_detail::configureCanopyMaterial(foliage);
        foliage.map=vegetation::makeLeafClusterTexture(256,427,{.40f,.50f,.22f},vegetation::LeafShape::Lobed,12,2);
        foliage.color=Color(0xffffff);foliage.alphaTest=.36f;foliage.roughness=.93f;
        auto wear=loader.load(assets/"city/paint-wear.png");wear->wrapS=wear->wrapT=TextureWrapping::Repeat;wear->colorSpace=ColorSpace::sRGB;
        for(const char* paint:{"white","yellow"}){batches.at(paint).material->map=wear;batches.at(paint).material->alphaTest=.4f;batches.at(paint).tile=1.3f;}
        auto& paving=*batches.at("paving").material;paving.normalMap=loader.load(assets/"city/paving-normal.png");paving.roughnessMap=loader.load(assets/"city/paving-roughness.jpg");
        for(const auto& t:{paving.normalMap,paving.roughnessMap})t->wrapS=t->wrapT=TextureWrapping::Repeat;paving.normalScale.set(.6f,.6f);
        auto& stone=batches.at("stone");stone.tile=2;stone.material->map=photoMaps.at("ph-plaster-color.jpg");stone.material->normalMap=photoMaps.at("ph-plaster-normal.jpg");stone.material->normalScale.set(.2f,.2f);
        batches.at("litglass").material->emissive=Color(0xa08b66);batches.at("litglass").material->emissiveIntensity=.035f;
        // Partition the exact physics mesh at its existing half-metre grid.
        for(size_t i=0;i<terrain.indices.size();i+=3){auto a=terrain.vertex(terrain.indices[i]),b=terrain.vertex(terrain.indices[i+1]),c=terrain.vertex(terrain.indices[i+2]);
            // Both triangles on each bevel belong to the sidewalk. A midpoint
            // threshold assigned alternate triangles to asphalt and made teeth.
            auto& batch=batches.at((a.y+b.y+c.y)>.001f?"paving":"asphalt");unsigned start=static_cast<unsigned>(batch.p.size()/3);
            auto n=b.clone().sub(a).cross(c.clone().sub(a)).normalize();
            for(auto p:{a,b,c}){batch.p.insert(batch.p.end(),{p.x,p.y,p.z});batch.n.insert(batch.n.end(),{n.x,n.y,n.z});batch.uv.insert(batch.uv.end(),{p.x/batch.tile,p.z/batch.tile});float s=shade(p.x,p.y+.025f,p.z);
                if(p.y<.01f)s*=.93f+.045f*std::sin(p.x*.17f+p.z*.035f)+.025f*std::sin(p.z*.29f-p.x*.08f);
                batch.c.insert(batch.c.end(),{s*.98f,s,s*1.015f});}
            batch.index.insert(batch.index.end(),{start,start+1,start+2});}
        for(size_t k=0;k<buildings.size();++k){const auto& b=buildings[k];const char* m=b.finish==0?"brick-red":b.finish==1?"brick-buff":"plaster";
            box("stone",b.x,.09f,b.z,b.w+.1f,.18f,b.d+.1f);
            box(m,b.x,.16f+b.h*.5f,b.z,b.w-.5f,b.h,b.d-.5f,0,.92f+(k%3)*.04f);
            box("roof",b.x,b.h+.18f,b.z,b.w-.4f,.12f,b.d-.4f);
            // Four connected facades with actual window frames and projecting sills.
            facade(b,0,b.w,b.d,k==2||k==4?int(k):-1);facade(b,3.14159265f,b.w,b.d,k==0||k==3?int(k):-1);
            facade(b,1.5707963f,b.d,b.w,k==3||k==4?int(k):-1);facade(b,-1.5707963f,b.d,b.w,k<3?int(k):-1);
            for(float side:{-1.f,1.f}){
                box(m,b.x+side*(b.w*.5f-.14f),b.h+.43f,b.z,.28f,.7f,b.d);
                box(m,b.x,b.h+.43f,b.z+side*(b.d*.5f-.14f),b.w,.7f,.28f);
            }
            for(int j=0;j<2;++j){float x=b.x-2+j*4,z=b.z+2;
                box("metal",x,b.h+.75f,z,2.8f,1.1f,1.9f);box("dark",x,b.h+1.32f,z,2.3f,.04f,1.5f);
                for(int slat=0;slat<6;++slat)box("frame",x,b.h+.8f,z+.97f,2.4f,.035f,.025f,0,.8f+slat*.03f);
                pole("plaster",b.x+b.w*.3f,b.h+1.2f,b.z-b.d*.3f,.36f,2.2f);}
            // Downspouts, wall footing and roof-edge contact lines.
            for(float side:{-1.f,1.f})pole("metal",b.x+side*(b.w*.5f+.08f),b.h*.5f,b.z+b.d*.5f-.3f,.045f,b.h);
        }
        // Twin centre lines and broken lane paint leave the intersections open.
        for(float x:{-34.f,34.f})for(float dx:{-.12f,.12f})box("yellow",x+dx,.014f,70,.085f,.018f,61);
        for(float z:{26.f,114.f})for(float dz:{-.12f,.12f})box("yellow",0,.014f,z+dz,45,.018f,.085f);
        for(float x:{-41.5f,41.5f})for(int i=0;i<10;++i)box("white",x,.016f,42+i*6,.11f,.02f,2.4f);
        // Four intersections: stop bars and zebra crossings on every approach.
        for(float x:{-34.f,34.f})for(float z:{26.f,114.f}){
            for(int i=0;i<7;++i){float v=(i-3)*1.45f;
                box("white",x+v,.018f,z-6.4f,.72f,.02f,2.2f);box("white",x+v,.018f,z+6.4f,.72f,.02f,2.2f);
                box("white",x-6.4f,.019f,z+v,2.2f,.02f,.72f);box("white",x+6.4f,.019f,z+v,2.2f,.02f,.72f);}
            box("white",x-3.8f,.018f,z-9.1f,5.8f,.02f,.25f);box("white",x+3.8f,.018f,z+9.1f,5.8f,.02f,.25f);
        }
        // Street-edge kerbstones, parking bays and storm drains.
        for(float side:{-1.f,1.f})for(int i=0;i<34;++i){float z=36+i*2;
            box("stone",side*24.94f,.12f,z,.13f,.15f,1.92f,0,.88f+(i%4)*.035f);
            if(i%5==1){box("dark",side*25.45f,.019f,z,.65f,.025f,.8f);for(int j=0;j<6;++j)box("metal",side*25.45f,.037f,z-.33f+j*.13f,.62f,.02f,.035f);}}
        for(float side:{-1.f,1.f})for(int i=0;i<7;++i){float z=43+i*8;
            box("white",side*28,.016f,z,3.7f,.018f,.10f);box("white",side*26.15f,.016f,z+3,.1f,.018f,6);}
        for(float x:{-34.f,34.f})for(float z:{53.f,88.f}){pole("metal",x,.014f,z,.48f,.028f);for(int i=0;i<5;++i)box("dark",x,.032f,z-.3f+i*.15f,.65f,.012f,.025f);}
        // Repaired asphalt patches: subtle, irregularly spaced, tyre-scale.
        for(int i=0;i<12;++i)roadPatch((i%2?-37.f:37.f)+std::sin(i*4.f),44+i*4.4f,i);
        for(int i=0;i<6;++i)roadCrack(i%2?-36.5f:30.5f,42+i*9.4f,i);
        for(float x:{-23.7f,23.7f,-44.7f,44.7f})for(int i=0;i<4;++i){float z=42+i*18;tree(x,z,i);if(i%2==0)lamp(x,z+7,x<0?-1.5708f:1.5708f);}
        for(float x:{-20.f,20.f}){tree(x,36.8f,2);tree(x,103.2f,4);bench(x,33.0f,0);}
        // Courtyard pocket between the western and eastern building rows.
        for(int i=0;i<5;++i){box("stone",.5f,.45f,47+i*11,3,.55f,2.4f);box("soil",.5f,.74f,47+i*11,2.75f,.04f,2.15f);tree(.5f,47+i*11,i);}
        // Corner signals, street names, speed sign, bins and fire hydrants.
        for(float x:{-25.7f,25.7f})for(float z:{34.f,106.f}){
            pole("metal",x,2,z,.065f,3.7f);box("metal",x,3.25f,z,.32f,.9f,.26f);
            for(int i=0;i<3;++i)box(i==0?"red":"dark",x,3.53f-i*.28f,z-.15f,.19f,.19f,.04f);
            box("sign",x,2.6f,z,2.2f,.30f,.07f,0,1,5);
            pole("red",x+1.5f,.45f,z,.13f,.55f);box("red",x+1.5f,.5f,z,.46f,.15f,.16f);
        }
        pole("metal",-44,1.6f,69,.045f,2.9f);box("sign",-44,2.6f,69,.8f,1.1f,.06f,1.5708f,1,6);
        for(float z:{46.f,75.f,98.f}){box("metal",-23.8f,.65f,z,.5f,.9f,.5f);box("dark",-23.8f,1.12f,z,.55f,.08f,.55f);}
        // Low masonry boundaries retain the existing finite physical test area.
        for(const auto& s:solids())if(s[4]==1)box("stone",s[0],s[1],s[2],s[3]*2,s[4]*2,s[5]*2);
        // Modest context beyond those bounds keeps street views connected to a
        // larger city. These distant shells are outside the playable area.
        box("asphalt",0,-.11f,85,360,.12f,420);
        for(float side:{-1.f,1.f})for(int i=0;i<4;++i)contextBuilding(side*(88+(i%2)*7),9+i*49,24,30,18+(i*11%26),i);
        for(int i=0;i<4;++i)contextBuilding(-59+i*43,218+(i%2)*9,31,28,23+(i*13%31),i+1);
        for(int i=0;i<3;++i)contextBuilding(-42+i*45,-49,28,25,19+i*7,i);
        for(auto& [id,b]:batches){if(b.p.empty())continue;auto g=BufferGeometry::create();
            g->setAttribute("position",FloatBufferAttribute::create(b.p,3));g->setAttribute("normal",FloatBufferAttribute::create(b.n,3));
            g->setAttribute("uv",FloatBufferAttribute::create(b.uv,2));g->setAttribute("color",FloatBufferAttribute::create(b.c,3));g->setIndex(b.index);g->computeBoundingSphere();
            auto mesh=Mesh::create(g,b.material);mesh->name="city."+id;mesh->receiveShadow=true;
            mesh->castShadow=false; // static shade is baked; dynamic map belongs to the vehicle
            root->add(mesh);triangles+=b.index.size()/3;++draws;
        }
        root->name="Mercer City Block";
    }
};
}
