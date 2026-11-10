#include "CityBlock.hpp"
#include <nlohmann/json.hpp>
#include <fstream>
#include <iostream>
#include <map>
using nlohmann::json;
using namespace threepp;
namespace fs=std::filesystem;
static void binary(const fs::path& p,const void* data,size_t size){std::ofstream f(p,std::ios::binary);if(!f)throw std::runtime_error("Cannot create "+p.string());f.write(static_cast<const char*>(data),size);if(!f)throw std::runtime_error("Cannot write "+p.string());}
int main(int argc,char** argv){try{
 if(argc!=3)throw std::runtime_error("usage: export_city <repo> <new-output-folder>");fs::path repo=fs::absolute(argv[1]),out=fs::absolute(argv[2]);if(fs::exists(out))throw std::runtime_error("Output exists; preserve it and select a new folder");fs::create_directories(out);
 playground::Terrain terrain(true);city::Block block(repo/"showcase/assets",terrain);json j={{"format","cinder-native-city-v1"},{"source","showcase/CityBlock.hpp"},{"triangles",block.triangles},{"batches",block.draws},{"meshes",json::array()},{"textures",json::array()},{"sunDirection",city::sunDirection},{"skyRotationRadians",city::skyRotation}};
 std::map<unsigned,std::string> textureNames;
 auto texture=[&](const std::shared_ptr<Texture>& t)->json{if(!t)return nullptr;if(textureNames.contains(t->id))return textureNames.at(t->id);std::string name="texture-"+std::to_string(textureNames.size());textureNames[t->id]=name;json row={{"id",name},{"source",t->sourceFile.generic_string()},{"repeat",{t->repeat.x,t->repeat.y}},{"offset",{t->offset.x,t->offset.y}},{"flipY",true}};if(t->sourceFile.empty()){const auto& im=t->image();if(im.isFloat()||im.isHalfFloat())throw std::runtime_error("Unexpected HDR city texture");row["width"]=im.width();row["height"]=im.height();row["channels"]=im.channels();row["raw"]=name+".raw";binary(out/(name+".raw"),im.data().data(),im.byteSize());}j["textures"].push_back(row);return name;};
 std::map<std::string,size_t> groundIndices;for(size_t i=0;i<terrain.indices.size();i+=3){auto a=terrain.vertex(terrain.indices[i]),b=terrain.vertex(terrain.indices[i+1]),c=terrain.vertex(terrain.indices[i+2]);groundIndices[(a.y+b.y+c.y)>.001f?"paving":"asphalt"]+=3;}
 for(auto& obj:block.root->children){auto* mesh=dynamic_cast<Mesh*>(obj);if(!mesh)throw std::runtime_error("Unexpected non-mesh city object");auto m=std::dynamic_pointer_cast<MeshStandardMaterial>(mesh->material());if(!m)throw std::runtime_error("Unexpected material");auto g=mesh->geometry();std::string id=mesh->name.substr(5);json mat={{"id",id},{"name",mesh->name},{"color",{m->color.r,m->color.g,m->color.b}},{"roughness",m->roughness},{"metalness",m->metalness},{"normalScale",{m->normalScale.x,m->normalScale.y}},{"alphaCutoff",m->alphaTest},{"doubleSided",m->side==Side::Double},{"emissive",{m->emissive.r*m->emissiveIntensity,m->emissive.g*m->emissiveIntensity,m->emissive.b*m->emissiveIntensity}},{"maps",{{"color",texture(m->map)},{"normal",texture(m->normalMap)},{"roughness",texture(m->roughnessMap)}}}};
 json row={{"id",id},{"name",mesh->name},{"material",mat},{"attributes",json::object()},{"groundIndexCount",groundIndices[id]}};
 for(auto key:{"position","normal","uv","color"}){auto* a=g->getAttribute<float>(key);if(!a)throw std::runtime_error("Required city attribute missing");std::string file=id+"-"+key+".bin";binary(out/file,a->data(),a->byteLength());row["attributes"][key]={{"file",file},{"count",a->count()},{"itemSize",a->itemSize()},{"bytes",a->byteLength()}};}
 auto* indices=g->getIndex();if(!indices)throw std::runtime_error("City indices missing");std::string file=id+"-indices.bin";binary(out/file,indices->data(),indices->byteLength());row["indices"]={{"file",file},{"count",indices->count()},{"bytes",indices->byteLength()}};j["meshes"].push_back(row);
 }
 std::ofstream(out/"native-city.json")<<j.dump(2)<<'\n';std::cout<<"PASS CPU native city export: "<<block.triangles<<" triangles, "<<block.draws<<" batches\n";return 0;
 }catch(const std::exception& e){std::cerr<<"FAIL "<<e.what()<<'\n';return 1;}}

