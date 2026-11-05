// Offline asset preparation only. Never constructs Canvas, renderer or audio.
#include "threepp/threepp.hpp"
#include "threepp/utils/BVH.hpp"
#include "threepp/loaders/GLTFLoader.hpp"
#include "threepp/materials/interfaces.hpp"
#include <nlohmann/json.hpp>
#include <algorithm>
#include <array>
#include <chrono>
#include <cctype>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <unordered_map>
#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <bcrypt.h>
#include <psapi.h>
#endif

using namespace threepp;
using json=nlohmann::json;
namespace fs=std::filesystem;
namespace {
constexpr int samples=16;
constexpr float radius=.25f,bias=.002f,pi=3.14159265358979323846f;
void require(bool ok,const std::string& what){if(!ok)throw std::runtime_error(what);}
std::vector<unsigned char> bytes(const fs::path& path){require(fs::file_size(path)<128*1024*1024,"GLB exceeds offline preparation bound");std::ifstream in(path,std::ios::binary);require(bool(in),"Cannot read "+path.string());return {std::istreambuf_iterator<char>(in),{}};}
uint32_t word(const std::vector<unsigned char>& b,size_t at){require(at+4<=b.size(),"Truncated GLB");uint32_t out;std::memcpy(&out,b.data()+at,4);return out;}
std::string sha256(const std::vector<unsigned char>& b){
#ifdef _WIN32
    BCRYPT_ALG_HANDLE algorithm=nullptr;BCRYPT_HASH_HANDLE hash=nullptr;
    require(BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,nullptr,0)>=0,"CNG SHA256 provider failed");
    DWORD size=0,written=0;BCryptGetProperty(algorithm,BCRYPT_OBJECT_LENGTH,reinterpret_cast<PUCHAR>(&size),sizeof(size),&written,0);
    std::vector<unsigned char> object(size),digest(32);auto status=BCryptCreateHash(algorithm,&hash,object.data(),size,nullptr,0,0);
    if(status>=0)status=BCryptHashData(hash,const_cast<PUCHAR>(b.data()),static_cast<ULONG>(b.size()),0);
    if(status>=0)status=BCryptFinishHash(hash,digest.data(),32,0);
    if(hash)BCryptDestroyHash(hash);BCryptCloseAlgorithmProvider(algorithm,0);require(status>=0,"CNG SHA256 failed");
    std::ostringstream text;for(auto c:digest)text<<std::hex<<std::setw(2)<<std::setfill('0')<<int(c);return text.str();
#else
    throw std::runtime_error("This local helper uses Windows CNG for source identity");
#endif
}
struct Source {
    std::vector<unsigned char> file;json doc;size_t binary=0,binarySize=0;std::string hash;
    explicit Source(const fs::path& path):file(bytes(path)){
        require(file.size()<128*1024*1024&&word(file,0)==0x46546c67&&word(file,4)==2,"Expected bounded GLB2");
        require(word(file,8)==file.size(),"GLB length mismatch");
        for(size_t at=12;at<file.size();){auto n=word(file,at),kind=word(file,at+4);require(at+8+n<=file.size(),"GLB chunk overrun");
            if(kind==0x4e4f534a)doc=json::parse(file.begin()+at+8,file.begin()+at+8+n);
            if(kind==0x004e4942){binary=at+8;binarySize=n;}at+=8+n;}
        require(!doc.is_null()&&binary,"Missing GLB chunks");hash=sha256(file);
        require(!doc.contains("animations")&&!doc.contains("skins"),"AO requires static geometry");
        std::vector<int> used(doc.at("meshes").size());
        for(const auto& node:doc.at("nodes")){
            require(!node.contains("matrix")&&!node.contains("translation")&&!node.contains("rotation")&&!node.contains("scale"),"Node transforms must be baked before AO");
            if(node.contains("mesh"))++used.at(node["mesh"].get<int>());}
        for(int n:used)require(n==1,"Each AO mesh must have one identity node instance");
    }
    const unsigned char* element(int accessor,size_t index,size_t componentBytes,int components)const{
        const auto& a=doc.at("accessors").at(accessor);require(!a.contains("sparse")&&index<a.at("count").get<size_t>(),"Unsupported sparse/accessor bounds");
        const auto& v=doc.at("bufferViews").at(a.at("bufferView").get<int>());require(v.value("buffer",0)==0,"External buffer unsupported");
        size_t offset=a.value("byteOffset",size_t(0))+index*v.value("byteStride",componentBytes*components);
        require(offset+componentBytes*components<=v.at("byteLength").get<size_t>(),"Accessor exceeds bufferView");
        offset+=v.value("byteOffset",size_t(0));require(offset+componentBytes*components<=binarySize,"Accessor exceeds BIN");return file.data()+binary+offset;
    }
    std::vector<float> floats(int accessor,int components)const{
        const auto& a=doc.at("accessors").at(accessor);require(a.at("componentType")==5126,"Positions/normals must be float32");
        size_t count=a.at("count");std::vector<float> out(count*components);
        for(size_t i=0;i<count;++i){std::memcpy(out.data()+i*components,element(accessor,i,4,components),components*4);for(int c=0;c<components;++c)require(std::isfinite(out[i*components+c]),"Non-finite geometry");}return out;
    }
    std::vector<unsigned> indices(int accessor)const{
        const auto& a=doc.at("accessors").at(accessor);int type=a.at("componentType");size_t count=a.at("count");std::vector<unsigned> out(count);require(type==5123||type==5125,"Unsupported indices");
        for(size_t i=0;i<count;++i){if(type==5125)std::memcpy(&out[i],element(accessor,i,4,1),4);else{uint16_t v;std::memcpy(&v,element(accessor,i,2,1),2);out[i]=v;}}require(count%3==0,"Non-triangle index count");return out;
    }
};
struct Primitive {int mesh,primitive,material;std::string name;std::vector<float> p,n;std::vector<unsigned> indices;bool occluder,receiver;};
std::vector<Primitive> primitives(const Source& source){std::vector<Primitive> out;
    for(size_t m=0;m<source.doc.at("meshes").size();++m){const auto& mesh=source.doc["meshes"][m];int part=0;
        for(const auto& primitive:mesh.at("primitives")){
            require(primitive.value("mode",4)==4,"Only triangle meshes supported");require(!primitive.contains("targets"),"Morphing geometry unsupported");
            int mi=primitive.at("material");const auto& mat=source.doc.at("materials").at(mi);const auto& attributes=primitive.at("attributes");
            std::string name=mesh.value("name","mesh_"+std::to_string(m)),lower=name;std::transform(lower.begin(),lower.end(),lower.begin(),[](unsigned char c){return char(std::tolower(c));});
            bool blend=mat.value("alphaMode",std::string("OPAQUE"))=="BLEND",opaque=mat.value("alphaMode",std::string("OPAQUE"))=="OPAQUE";
            bool decal=lower.find("livery")!=std::string::npos||lower.find("decal")!=std::string::npos||lower.find("roundel")!=std::string::npos||lower.find("legend")!=std::string::npos;
            bool emissive=false;if(mat.contains("emissiveFactor"))for(float e:mat["emissiveFactor"].get<std::vector<float>>())emissive|=e>0;
            auto p=source.floats(attributes.at("POSITION"),3),n=source.floats(attributes.at("NORMAL"),3);require(p.size()==n.size(),"Normal/position count mismatch");
            auto idx=source.indices(primitive.at("indices"));for(auto index:idx)require(index<p.size()/3,"Index exceeds vertex count");
            out.push_back({int(m),part++,mi,name,std::move(p),std::move(n),std::move(idx),opaque&&!decal,!blend&&!emissive});
        }}return out;
}
struct QueryKey {std::array<uint32_t,6> values;bool operator==(const QueryKey& b)const{return values==b.values;}};
struct KeyHash{size_t operator()(const QueryKey& k)const{size_t h=1469598103934665603ull;for(auto v:k.values){h^=v;h*=1099511628211ull;}return h;}};
QueryKey key(const Vector3& p,const Vector3& n){float f[]={p.x,p.y,p.z,n.x,n.y,n.z};QueryKey out{};std::memcpy(out.values.data(),f,sizeof(f));return out;}
float radicalInverse(unsigned v){v=(v<<16)|(v>>16);v=((v&0x55555555u)<<1)|((v&0xaaaaaaaau)>>1);v=((v&0x33333333u)<<2)|((v&0xccccccccu)>>2);v=((v&0x0f0f0f0fu)<<4)|((v&0xf0f0f0f0u)>>4);v=((v&0x00ff00ffu)<<8)|((v&0xff00ff00u)>>8);return v*2.3283064365386963e-10f;}
float visibility(const BVH& bvh,const Vector3& p,const Vector3& normal){
    auto n=normal.clone().normalize();auto u=(std::abs(n.y)<.95f?Vector3(0,1,0):Vector3(1,0,0)).cross(n).normalize();auto v=n.clone().cross(u);
    auto origin=p.clone().addScaledVector(n,bias);int blocked=0;
    for(int s=0;s<samples;++s){float r=std::sqrt((s+.5f)/samples),phi=2*pi*radicalInverse(s);
        auto direction=n.clone().multiplyScalar(std::sqrt(1-r*r)).addScaledVector(u,r*std::cos(phi)).addScaledVector(v,r*std::sin(phi));
        blocked+=bvh.raycastAny(Ray(origin,direction),radius);}
    return 1-blocked/static_cast<float>(samples);
}
void selfTest(){BVH open(8,20);open.build(std::vector<float>{-1,0,-1,1,0,-1,0,0,1});require(visibility(open,{0,0,0},{0,1,0})==1,"Open plane self-occludes");
    BVH roof(8,20);roof.build(std::vector<float>{-1,.04f,-1,1,.04f,-1,1,.04f,1,-1,.04f,-1,1,.04f,1,-1,.04f,1});require(visibility(roof,{0,0,0},{0,1,0})<.1f,"Nearby roof fails to occlude");
    BVH distant(8,20);distant.build(std::vector<float>{-1,.4f,-1,1,.4f,-1,1,.4f,1,-1,.4f,-1,1,.4f,1,-1,.4f,1});require(visibility(distant,{0,0,0},{0,1,0})==1,"AO ignores distance limit");std::cout<<"PASS: open hemisphere, nearby cover and radius cutoff; no graphics context\n";}
void validate(const fs::path& path){Source source(path);auto loaded=GLTFLoader{}.load(path);require(loaded&&loaded->scene,"CPU GLTF load failed");int meshes=0,receivers=0;size_t triangles=0;
    loaded->scene->traverseType<Mesh>([&](Mesh& mesh){++meshes;auto g=mesh.geometry();auto* position=g->getAttribute<float>("position");triangles+=(g->hasIndex()?g->getIndex()->count():position->count())/3;
        if(auto* mat=dynamic_cast<MaterialWithAoMap*>(mesh.material().get());mat&&mat->aoMap){++receivers;auto* uv=g->getAttribute<float>("uv2");require(uv&&uv->count()==position->count(),"AO mesh has no complete uv2");
            require(mat->aoMap->channel==1&&mat->aoMap->minFilter==Filter::Linear&&!mat->aoMap->generateMipmaps,"AO sampler/channel wrong in actual loader");require(std::abs(mat->aoMapIntensity-.5f)<1e-6f,"AO strength changed");}});
    require(receivers>0,"No AO receivers loaded");std::cout<<json{{"ok",true},{"meshes",meshes},{"aoMeshes",receivers},{"triangles",triangles},{"sourceSha256",source.hash},{"graphicsContext",false}}.dump()<<'\n';}
}
int main(int argc,char** argv){try{
    if(argc==2&&std::string(argv[1])=="--self-test"){selfTest();return 0;}
    if(argc==3&&std::string(argv[1])=="--validate"){validate(argv[2]);return 0;}
    require(argc==3,"Usage: safari_ao_bake INPUT.glb OUTPUT.json | --self-test | --validate FILE.glb");
    const auto started=std::chrono::steady_clock::now();Source source(argv[1]);auto parts=primitives(source);std::vector<float> p;std::vector<unsigned> indices;size_t degenerate=0;
    for(const auto& part:parts)if(part.occluder){unsigned base=p.size()/3;p.insert(p.end(),part.p.begin(),part.p.end());for(size_t i=0;i<part.indices.size();i+=3){unsigned a=part.indices[i],b=part.indices[i+1],c=part.indices[i+2];Vector3 pa(part.p[a*3],part.p[a*3+1],part.p[a*3+2]),pb(part.p[b*3],part.p[b*3+1],part.p[b*3+2]),pc(part.p[c*3],part.p[c*3+1],part.p[c*3+2]);
            if(pb.sub(pa).cross(pc.sub(pa)).lengthSq()<1e-16f){++degenerate;continue;}indices.insert(indices.end(),{base+a,base+b,base+c});}}
    BVH bvh(8,20);bvh.build(p,indices);const auto built=std::chrono::steady_clock::now();
    fs::path metadata=fs::absolute(argv[2]);require(metadata.lexically_normal()!=fs::absolute(argv[1]).lexically_normal(),"Never overwrite source GLB");fs::create_directories(metadata.parent_path());auto binary=metadata;binary.replace_extension(".bin");std::ofstream data(binary,std::ios::binary);require(bool(data),"Cannot write AO values");
    std::unordered_map<QueryKey,float,KeyHash> cache;json meshes=json::array();size_t offset=0,receiverVertices=0,unreferenced=0,normalFallbacks=0,normalSkipped=0;double total=0;float minimum=1,maximum=0;
    for(size_t m=0;m<parts.size();++m){auto& part=parts[m];size_t count=part.p.size()/3;std::vector<float> values(count,1);
        std::vector<bool> referenced(count);std::vector<Vector3> fallback(count);
        if(part.receiver)for(size_t t=0;t<part.indices.size();t+=3)for(int corner=0;corner<3;++corner){auto i=part.indices[t+corner];referenced[i]=true;
            Vector3 normal(part.n[3*i],part.n[3*i+1],part.n[3*i+2]);if(normal.lengthSq()>.1f)continue;
            for(int other=0;other<3;++other){auto j=part.indices[t+other];Vector3 neighbor(part.n[3*j],part.n[3*j+1],part.n[3*j+2]);if(neighbor.lengthSq()>.1f)fallback[i].add(neighbor);}}
        if(part.receiver)for(size_t i=0;i<count;++i){Vector3 point(part.p[3*i],part.p[3*i+1],part.p[3*i+2]),normal(part.n[3*i],part.n[3*i+1],part.n[3*i+2]);
            if(!referenced[i]){++unreferenced;continue;}
            // Some authored pole vertices have zero normals. Preserve source
            // shading bytes; neighbor directions are for AO queries only.
            if(normal.lengthSq()<.1f){normal=fallback[i];if(normal.lengthSq()<.001f){++normalSkipped;continue;}normal.normalize();++normalFallbacks;}
            auto k=key(point,normal);auto found=cache.find(k);float value;
            if(found!=cache.end())value=found->second;else{value=visibility(bvh,point,normal);cache.emplace(k,value);}values[i]=value;total+=value;minimum=std::min(minimum,value);maximum=std::max(maximum,value);++receiverVertices;}
        data.write(reinterpret_cast<const char*>(values.data()),values.size()*sizeof(float));require(bool(data),"AO value write failed");
        meshes.push_back({{"mesh",part.mesh},{"primitive",part.primitive},{"name",part.name},{"material",part.material},{"vertexCount",count},{"floatOffset",offset},{"occluder",part.occluder},{"receiver",part.receiver}});offset+=count;
        if(m%10==0)std::cerr<<"AO "<<m+1<<'/'<<parts.size()<<" meshes, "<<cache.size()<<" unique queries\n";
    }data.close();const auto finished=std::chrono::steady_clock::now();size_t peak=0;
#ifdef _WIN32
    PROCESS_MEMORY_COUNTERS memory{};memory.cb=sizeof(memory);if(GetProcessMemoryInfo(GetCurrentProcess(),&memory,sizeof(memory)))peak=memory.PeakWorkingSetSize;
#endif
    json report={{"version",1},{"sourceSha256",source.hash},{"sourceBytes",source.file.size()},{"valuesFile",binary.filename().string()},{"format","little-endian float32 visibility"},{"samples",samples},{"maxDistanceMetres",radius},{"originBiasMetres",bias},{"hemisphere","cosine weighted deterministic Hammersley"},{"strength",.5},{"nodeTransforms","asserted identity, one instance per mesh"},{"occluderTriangles",bvh.triangleCount()},{"degenerateOccluderTrianglesSkipped",degenerate},{"receiverVertices",receiverVertices},{"unreferencedReceiverVerticesSkipped",unreferenced},{"queryNormalFallbackVertices",normalFallbacks},{"unrecoverableNormalVerticesNeutral",normalSkipped},{"uniqueQueries",cache.size()},{"rayQueries",cache.size()*samples},{"visibilityMinimum",minimum},{"visibilityMaximum",maximum},{"visibilityMean",receiverVertices?total/receiverVertices:1},{"buildSeconds",std::chrono::duration<double>(built-started).count()},{"bakeSeconds",std::chrono::duration<double>(finished-built).count()},{"peakWorkingSetBytes",peak},{"graphicsContext",false},{"meshes",meshes}};
    std::ofstream out(metadata);out<<report.dump(2)<<'\n';require(bool(out),"AO metadata write failed");std::cout<<"AO complete: "<<metadata.string()<<", "<<cache.size()<<" unique vertices, "<<report["bakeSeconds"]<<" seconds\n";return 0;
}catch(const std::exception& error){std::cerr<<"AO bake failed: "<<error.what()<<'\n';return 1;}}
