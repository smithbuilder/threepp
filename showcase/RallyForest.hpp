#pragma once

#include "threepp/threepp.hpp"
#include "threepp/extras/vegetation/TreeGenerator.hpp"
#include "threepp/renderers/shaders/ShaderLib.hpp"
#include "threepp/loaders/GLTFLoader.hpp"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <random>
#include <filesystem>
#include <array>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

namespace rally {
namespace forest_detail {
using namespace threepp;
constexpr float forestPi=3.14159265359f;

// The generator supplies deliberately smoothed CANOPY normals, rather than the
// geometric normal of every crossed card. Reversing those volume normals when
// a card's back face becomes visible makes whole grey shelves appear/disappear
// as the camera moves. Keep the volume lighting independent of card winding.
// This is a cheap diffuse-canopy approximation, not thin-leaf transmission.
// The opt-in define leaves every ordinary standard material unchanged.
inline void configureCanopyMaterial(MeshStandardMaterial& material) {
    static const bool installed=[] {
        auto& source=shaders::ShaderLib::instance().standard.fragmentShader;
        const std::string anchor="#include <normal_fragment_begin>";
        const auto at=source.find(anchor);
        if(at==std::string::npos||source.find(anchor,at+anchor.size())!=std::string::npos)
            throw std::runtime_error("Forest canopy normal shader anchor changed");
        source.replace(at,anchor.size(),anchor+R"GLSL(
#ifdef RALLY_FOREST_CANOPY_NORMALS
    // Undo the stock DOUBLE_SIDED flip only for our crown-volume normals.
    normal *= faceDirection;
    geometryNormal = normal;
#endif
)GLSL");
        return true;
    }();
    (void)installed;
    material.defines["RALLY_FOREST_CANOPY_NORMALS"]="1";
    material.side=Side::Double;
    material.roughness=.96f;
    material.metalness=0;
    material.alphaTest=vegetation::kLeafAlphaTest;
    material.transparent=false;
    material.vertexColors=true;
}

inline Vector3 point(const FloatBufferAttribute& a,unsigned i) {
    return {a.getX(i),a.getY(i),a.getZ(i)};
}

// Reuse the exact original skeleton and indexed card topology. Narrowing and
// folding existing cards spends zero additional triangles/vertices. In
// particular, the conifer's four flat blades per twig no longer form a broad
// repeated horizontal saw-tooth shelf. UVs and the four-sprig 256px atlas stay
// unchanged; RGB dilation/mip filtering remain owned by TreeTextures.hpp.
inline void refineCanopyGeometry(BufferGeometry& geometry,const vegetation::TreeParams& p) {
    auto* positions=geometry.getAttribute<float>("position");
    auto* normals=geometry.getAttribute<float>("normal");
    const auto count=positions->count();
    if(count%4!=0)throw std::runtime_error("Forest expects indexed four-vertex foliage cards");
    const Vector3 crown(0,p.trunkHeight+p.crownHeight*.52f,0);
    const bool conifer=p.leafStyle==vegetation::LeafStyle::Frond;
    std::mt19937 random(p.seed+6401);
    std::uniform_real_distribution<float> unit(0,1);
    for(unsigned first=0;first<count;first+=4) {
        const auto a=point(*positions,first),b=point(*positions,first+1),c=point(*positions,first+2),d=point(*positions,first+3);
        const auto centre=a.clone().add(b).add(c).add(d).multiplyScalar(.25f);
        auto side=b.clone().sub(a).multiplyScalar(.5f);
        auto along=d.clone().sub(a).multiplyScalar(.5f);
        auto axis=along.clone().normalize();
        const float angle=(unit(random)-.5f)*(conifer?1.05f:.28f);
        const auto across=Vector3().crossVectors(axis,side);
        side.multiplyScalar(std::cos(angle)).addScaledVector(across,std::sin(angle));
        side.multiplyScalar(conifer?.73f+.16f*unit(random):.90f+.07f*unit(random));
        auto fold=Vector3().crossVectors(side,along).normalize();
        fold.multiplyScalar(along.length()*(unit(random)-.5f)*.19f);
        // A subtle twist breaks the planar card without adding a centre vertex.
        const Vector3 offsets[4]={side.clone().negate().sub(along).sub(fold),
            side.clone().sub(along).add(fold),side.clone().add(along).sub(fold),
            side.clone().negate().add(along).add(fold)};
        auto outward=centre.clone().sub(crown).normalize();
        auto normal=Vector3(outward.x*.58f,.80f+outward.y*.35f,outward.z*.58f).normalize();
        for(unsigned j=0;j<4;++j) {
            const auto q=centre.clone().add(offsets[j]);
            positions->setXYZ(first+j,q.x,q.y,q.z);
            normals->setXYZ(first+j,normal.x,normal.y,normal.z);
        }
    }
    positions->needsUpdate();normals->needsUpdate();
    geometry.computeBoundingBox();geometry.computeBoundingSphere();
}

inline vegetation::TreeParams treeParameters(int species) {
    vegetation::TreeParams p;
    vegetation::applyPreset(species==0?1:species==1?2:0,p);
    p.seed=123+species;p.attractorCount=300;
    // These changes affect surface appearance only. Skeleton generation and
    // card counts stay identical to the three baseline prototypes.
    p.leafColor=species==0?std::array<float,3>{.25f,.32f,.22f}:
        species==1?std::array<float,3>{.37f,.44f,.27f}:
        std::array<float,3>{.31f,.39f,.22f};
    p.barkColor=species==0?std::array<float,3>{.31f,.26f,.20f}:
        species==1?std::array<float,3>{.70f,.68f,.62f}:
        std::array<float,3>{.32f,.28f,.22f};
    return p;
}

struct AuthoredTreePrototype {
    std::array<std::shared_ptr<BufferGeometry>,2> geometry; // bark, foliage
    std::array<std::shared_ptr<Material>,2> material;
    float height=1;
};

inline const AuthoredTreePrototype& loadAuthoredTree(const std::filesystem::path& path,
        const AuthoredTreePrototype* sharedMaterials=nullptr,bool shareFoliage=true) {
    static std::map<std::filesystem::path,AuthoredTreePrototype> cache;
    if(const auto found=cache.find(path);found!=cache.end())return found->second;
    auto asset=GLTFLoader{}.load(path);
    if(!asset||!asset->scene)throw std::runtime_error("Cannot load portable forest tree: "+path.string());
    asset->scene->updateMatrixWorld(true);
    AuthoredTreePrototype result;Box3 bounds;
    asset->scene->traverseType<Mesh>([&](Mesh& mesh) {
        if(mesh.materials().size()!=1)throw std::runtime_error("Portable forest expects one material per primitive");
        const int role=mesh.material()->name.find(".foliage")!=std::string::npos?1:0;
        if(result.geometry[role])throw std::runtime_error("Portable forest exceeds its two-draw prototype budget");
        auto geometry=mesh.geometry()->clone();geometry->applyMatrix4(*mesh.matrixWorld);
        const auto* p=geometry->getAttribute<float>("position");
        for(int i=0;i<p->count();++i)bounds.expandByPoint({p->getX(i),p->getY(i),p->getZ(i)});
        result.geometry[role]=geometry;
        result.material[role]=sharedMaterials&&(role==0||shareFoliage)?sharedMaterials->material[role]:mesh.material();
        auto* standard=result.material[role]->as<MeshStandardMaterial>();
        if(!standard)throw std::runtime_error("Portable forest requires standard PBR materials");
        standard->transparent=false;standard->depthWrite=true;
        if(role==1){standard->side=Side::Double;standard->alphaTest=.30f;}
        // Authored model normals/normal maps are kept. The procedural canopy
        // normal workaround above is deliberately not applied to these GLBs.
    });
    if(!result.geometry[0]||!result.geometry[1])throw std::runtime_error("Portable tree must contain bark and foliage");
    result.height=std::max(.01f,bounds.max().y-bounds.min().y);
    return cache.emplace(path,std::move(result)).first->second;
}
}

struct SafariForestBudget {
    std::size_t nearTrees=180,nearDraws=6,prototypeVertices=0,prototypeTriangles=0;
};

// Safari-only replacement for rally.cpp's near-tree loop. The original buggy
// should continue using that loop. The returned positions feed the existing
// ground occlusion and dress() calls exactly as before. Draw/instance/shadow
// budgets stay fixed; the portable model's maps are explicitly bounded at1K.
template<class Track,class Nearest,class Height>
inline std::vector<threepp::Vector3> addSafariForest(threepp::Scene& scene,
        Track track,Nearest nearest,Height height,SafariForestBudget* budget=nullptr,
        const std::filesystem::path& assetDir=std::filesystem::path(__FILE__).parent_path()/"assets") {
    using namespace threepp;
    std::vector<Vector3> positions;positions.reserve(180);
    std::mt19937 rng(29);std::uniform_real_distribution<float> unit(0,1);
    SafariForestBudget measured;
    const auto treeDir=assetDir/"library/models/trees";
    const std::array<std::string,3> files{"fir_tree_01-c-lod1.glb","fir_tree_01-b-lod1.glb","fir_tree_01-c-mirrored-lod1.glb"};
    const bool authored=std::all_of(files.begin(),files.end(),[&](const auto& file){return std::filesystem::exists(treeDir/file);});
    const forest_detail::AuthoredTreePrototype* pineMaterials=nullptr;
    for(int species=0;species<3;++species) {
        std::shared_ptr<BufferGeometry> trunkGeometry,foliageGeometry;
        std::shared_ptr<Material> trunkMaterial,foliageMaterial;
        float sourceHeight=1;
        if(authored) {
            // The adult variants use the same original foliage atlas and
            // consolidated bark PBR set; share them across all three meshes.
            const auto& prototype=forest_detail::loadAuthoredTree(treeDir/files[species],species>0?pineMaterials:nullptr,true);
            if(species==0)pineMaterials=&prototype;
            trunkGeometry=prototype.geometry[0];foliageGeometry=prototype.geometry[1];
            trunkMaterial=prototype.material[0];foliageMaterial=prototype.material[1];sourceHeight=prototype.height;
        } else {
            const auto p=forest_detail::treeParameters(species);
            vegetation::TreeGenerator generator(p.seed);generator.buildSkeleton(p);
            auto bark=vegetation::makeBarkTextures(128,p.seed,p.barkColor,p.barkStyle);
            auto tm=MeshStandardMaterial::create();tm->map=bark.first;tm->normalMap=bark.second;
            tm->normalScale.set(.65f,.65f);tm->roughness=.96f;tm->vertexColors=true;trunkMaterial=tm;
            auto fm=MeshStandardMaterial::create();forest_detail::configureCanopyMaterial(*fm);
            fm->map=p.leafStyle==vegetation::LeafStyle::Frond?
                vegetation::makeNeedleFrondTexture(128,p.seed,p.leafColor,p.leafAtlasCells):
                vegetation::makeLeafClusterTexture(128,p.seed,p.leafColor,p.leafShape,8,p.leafAtlasCells);
            foliageMaterial=fm;trunkGeometry=generator.makeTrunkGeometry(p);foliageGeometry=generator.makeLeafGeometry(p);
            forest_detail::refineCanopyGeometry(*foliageGeometry,p);
        }
        for(const auto& g:{trunkGeometry,foliageGeometry}) {
            measured.prototypeVertices+=g->getAttribute<float>("position")->count();
            measured.prototypeTriangles+=(g->getIndex()?g->getIndex()->count():g->getAttribute<float>("position")->count())/3;
        }
        auto trunks=InstancedMesh::create(trunkGeometry,trunkMaterial,60);
        auto leaves=InstancedMesh::create(foliageGeometry,foliageMaterial,60);
        trunks->name="safari.forest.near.trunks."+std::to_string(species);
        leaves->name="safari.forest.near.canopy."+std::to_string(species);
        trunks->castShadow=trunks->receiveShadow=leaves->receiveShadow=true;
        leaves->castShadow=false;
        for(int i=0;i<60;++i) {
            // Four-tree patches, with quiet stretches between them, replace
            // the old regular roadside picket spacing. The exact road-nearest
            // check keeps crowns out of the playable corridor on tight bends.
            const int patch=i/4,within=i%4;
            float a=(patch+(within+.35f+unit(rng)*.45f)/5.f)*2*forest_detail::forestPi/15.f;
            a+=species*.107f;
            auto centre=track(a),tangent=track(a+.002f).sub(centre).normalize();
            const float side=(patch+species)%2?1.f:-1.f;
            const Vector3 across(tangent.z,0,-tangent.x);
            const float offset=authored?(unit(rng)<.80f?8.f+unit(rng)*6.f:14.f+unit(rng)*8.f):9.f+unit(rng)*25.f;
            centre.addScaledVector(across,side*offset);
            for(int attempt=0;attempt<5;++attempt) {
                const auto road=nearest(centre).p;
                const float dx=centre.x-road.x,dz=centre.z-road.z;
                if(dx*dx+dz*dz>=(authored?56.25f:81.f))break;
                centre.addScaledVector(across,side*(authored?2.f:3.f));
            }
            Object3D transform;transform.position.set(centre.x,height(centre.x,centre.z),centre.z);
            transform.rotation.y=unit(rng)*2*forest_detail::forestPi;
            // Age/width variation is independent of height. The procedural
            // fallback retains its old scale envelope.
            // Portable files retain the source adults'14–15m metre scale.
            // Roadside trees vary from7–14m while retaining the crown aspect.
            const float heightScale=authored?(7.f+unit(rng)*7.f)/sourceHeight:1.10f+unit(rng)*.72f;
            const float widthScale=heightScale*(authored?.94f+unit(rng)*.12f:.72f+unit(rng)*.16f);
            transform.scale.set(widthScale,heightScale,widthScale*(.94f+unit(rng)*.12f));
            transform.updateMatrix();trunks->setMatrixAt(i,*transform.matrix);leaves->setMatrixAt(i,*transform.matrix);
            positions.push_back(transform.position);
        }
        trunks->instanceMatrix()->needsUpdate();leaves->instanceMatrix()->needsUpdate();
        scene.add(trunks);scene.add(leaves);
    }
    if(budget)*budget=measured;
    return positions;
}

// Call immediately after existing dress(), passing its starting child index.
// Its two 240-instance distant-tree batches are retained at the exact existing
// count/topology/texture size. Other dressing, grass, obstacles and shadows are
// deliberately left alone. The far canopy's old dark material tint multiplied
// an already-dark green atlas; remove that accidental double tint.
inline void refineSafariDistantForest(threepp::Scene& scene,std::size_t firstDressingChild,
        const std::filesystem::path& assetDir=std::filesystem::path(__FILE__).parent_path()/"assets") {
    using namespace threepp;
    const auto treeDir=assetDir/"library/models/trees";
    const auto nearPath=treeDir/"fir_tree_01-c-lod1.glb",farPath=treeDir/"fir_tree_01-c-lod2.glb";
    const forest_detail::AuthoredTreePrototype* authored=nullptr;
    if(std::filesystem::exists(nearPath)&&std::filesystem::exists(farPath)) {
        const auto& near=forest_detail::loadAuthoredTree(nearPath);
        // The far representation has a full-tree silhouette atlas rather than
        // the near mesh's individual sprig atlas. Only its bark is shared.
        authored=&forest_detail::loadAuthoredTree(farPath,&near,false);
    }
    for(std::size_t i=firstDressingChild;i<scene.children.size();++i) {
        auto* instanced=dynamic_cast<InstancedMesh*>(scene.children[i]);
        if(!instanced||instanced->count()!=240)continue;
        auto* material=instanced->material()->as<MeshStandardMaterial>();
        if(!material)continue;
        if(authored) {
            const int role=material->alphaTest>0&&material->map?1:0;
            instanced->setGeometry(authored->geometry[role]);instanced->setMaterial(authored->material[role]);
            instanced->name=role?"safari.forest.far.authored.canopy":"safari.forest.far.authored.trunks";
            for(std::size_t j=0;j<instanced->count();++j) {
                Matrix4 matrix;instanced->getMatrixAt(j,matrix);
                Vector3 position,scale;Quaternion rotation;matrix.decompose(position,rotation,scale);
                const float targetHeight=10.f+(j%13)/12.f*8.f;
                const float factor=targetHeight/authored->height;
                matrix.compose(position,rotation,Vector3(factor,factor,factor));instanced->setMatrixAt(j,matrix);
            }
            instanced->instanceMatrix()->needsUpdate();instanced->castShadow=false;
            continue;
        }
        if(material->alphaTest>0&&material->map) {
            material->color.setHex(0xffffff);forest_detail::configureCanopyMaterial(*material);
            vegetation::TreeParams p;vegetation::applyPreset(1,p);p.seed=98;
            forest_detail::refineCanopyGeometry(*instanced->geometry(),p);
            // Reuse the existing 256px atlas allocation and sprig layout.
            material->map=vegetation::makeNeedleFrondTexture(128,98,{.25f,.32f,.22f},p.leafAtlasCells);
            instanced->name="safari.forest.far.canopy";
        } else {
            material->color.setHex(0x514a3e);material->roughness=.96f;
            instanced->name="safari.forest.far.trunks";
        }
        instanced->castShadow=false;
    }
}
}
