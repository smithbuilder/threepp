#pragma once
#include "threepp/threepp.hpp"
#include "threepp/objects/Sky.hpp"
#include "threepp/materials/ShaderMaterial.hpp"
#include "threepp/renderers/gl/PMREMGenerator.hpp"
#include "threepp/loaders/RGBELoader.hpp"
#include <cmath>
#include <filesystem>

namespace rally {
using namespace threepp;

// One sun direction drives the visible sky, outdoor IBL and shadow camera.
// Epping Forest01's brightest sky patch is at elevation42.715deg. Rotate its
// azimuth to the accepted sun side; the visible sky and key share that direction.
// See assets/ENVIRONMENT-SOURCE.json for the source-pixel/orientation receipt.
inline Vector3 daylightDirection(){return Vector3(-.695033f,.678350f,-.238297f).normalize();}
inline auto daylightSky(){
    auto sky=Sky::create();sky->scale.setScalar(2500);sky->frustumCulled=false;
    auto& u=sky->materialAs<ShaderMaterial>()->uniforms;
    u.at("turbidity").value<float>()=2.6f;
    u.at("rayleigh").value<float>()=1.8f;
    u.at("mieCoefficient").value<float>()=.004f;
    u.at("mieDirectionalG").value<float>()=.78f;
    u.at("sunPosition").value<Vector3>().copy(daylightDirection());
    return sky;
}

// A local photographic sky replaces (rather than layers over) the analytic
// dome for the Safari environment study. The same linear HDR texels light the
// materials through the existing PMREM. No extra sky pass or render target.
inline void usePhotographicSky(Sky& sky,Texture& panorama,float rotationY){
    // atan's longitude seam has a discontinuous implicit derivative. Mip
    // selection there can produce a dotted vertical bright streak in the sky.
    // This 1K distant dome uses base-level linear filtering; the separate
    // existing PMREM still owns roughness prefiltering for scene materials.
    panorama.minFilter=Filter::Linear;
    panorama.magFilter=Filter::Linear;
    panorama.generateMipmaps=false;
    auto m=sky.materialAs<ShaderMaterial>();
    m->name="Safari photographic daylight";
    m->uniforms.clear();
    m->uniforms.emplace("rallySkyPanorama",Uniform(&panorama));
    Matrix4 transform;transform.makeRotationFromEuler(Euler(0,rotationY,0));
    Matrix3 rotation;rotation.setFromMatrix4(transform).transpose();
    m->uniforms.emplace("rallySkyRotation",Uniform(rotation));
    m->vertexShader=R"(
varying vec3 vWorldPosition;
void main(){
    vec4 worldPosition=modelMatrix*vec4(position,1.0);
    vWorldPosition=worldPosition.xyz;
    gl_Position=projectionMatrix*viewMatrix*worldPosition;
    gl_Position.z=gl_Position.w;
})";
    m->fragmentShader=R"(
uniform sampler2D rallySkyPanorama;
uniform mat3 rallySkyRotation;
varying vec3 vWorldPosition;
void main(){
    // Exactly GLPMREM's equirectangular mapping and GLRenderer's inverse
    // environment rotation. RGBELoader has already decoded RGBE to linear RGB.
    vec3 direction=rallySkyRotation*normalize(vWorldPosition-cameraPosition);
    vec2 panoUv=vec2(atan(direction.z,direction.x)*0.15915494309+0.5,
                     asin(clamp(direction.y,-1.0,1.0))*0.31830988618+0.5);
    gl_FragColor=vec4(texture2D(rallySkyPanorama,panoUv).rgb,1.0);
    #include <tonemapping_fragment>
    #include <encodings_fragment>
})";
    m->needsUpdate();
}

struct RallyLighting {
    static constexpr int shadowSize=512;
    static constexpr float shadowHalfExtent=10.f;
    std::shared_ptr<Sky> sky;
    std::shared_ptr<DirectionalLight> sun;
    std::shared_ptr<Group> target;
    Vector3 sunDirection=daylightDirection();
    bool photographicSky=false;

    // Snap in the fixed LIGHT basis, rather than world X/Z. World-space
    // snapping still moves a tilted shadow projection by fractional texels.
    void follow(const Vector3& position){
        const auto& n=sunDirection;
        const auto u=Vector3(0,1,0).cross(n).normalize();
        const auto v=n.clone().cross(u).normalize();
        constexpr float texel=2*shadowHalfExtent/shadowSize;
        auto anchor=u.clone().multiplyScalar(std::round(position.dot(u)/texel)*texel)
            .addScaledVector(v,std::round(position.dot(v)/texel)*texel)
            .addScaledVector(n,position.dot(n));
        target->position.copy(anchor);sun->position.copy(anchor).addScaledVector(n,70.f);
    }
};

inline RallyLighting makeRallyLighting(GLRenderer& renderer,Scene& scene,
        const std::filesystem::path& assetDir=std::filesystem::path(__FILE__).parent_path()/"assets",
        bool useForestProbe=true,bool safariAtmosphere=false){
    RallyLighting light;
    renderer.toneMapping=ToneMapping::ACESFilmic;
    renderer.toneMappingExposure=.90f;
    renderer.shadowMap().enabled=true;
    renderer.shadowMap().type=ShadowMap::PFC;
    scene.fog=FogExp2(Color(0xb6c3c7),.0055f);

    light.sky=daylightSky();scene.add(light.sky);
    // Real branches, canopy openings and ground supply structured reflections:
    // broad uniform sky/floor fill was making glass and enamel read as plastic.
    // The 1K CC0 source uses the renderer's existing once-only PMREM prefilter.
    const auto skyPath=assetDir/"library/environments/kloofendal-partly-cloudy/sky_1k.hdr";
    if(safariAtmosphere&&useForestProbe&&std::filesystem::exists(skyPath)){
        scene.environment=RGBELoader{}.load(skyPath);
        if(scene.environment){
            // Brightest source pixel609,119 at1024x512: elevation47.988deg.
            // Keep the established key azimuth; turn the photo and IBL together.
            light.photographicSky=true;
            light.sunDirection.set(-.6331052f,.7430080f,-.2170646f);
            scene.environmentRotation.y=3.4095478f;
            scene.environmentIntensity=.55f;
            usePhotographicSky(*light.sky,*scene.environment,scene.environmentRotation.y);
            // Less uniform veiling restores middle-distance terrain contrast.
            // This is the existing exponential approximation, not volumetric fog.
            scene.fog=FogExp2(Color(0xb8c8d3),.0038f);
        }
    }
    if(!light.photographicSky){
        const auto probePath=assetDir/"epping_forest_01_1k.hdr";
        if(useForestProbe&&std::filesystem::exists(probePath))scene.environment=RGBELoader{}.load(probePath);
        if(scene.environment){scene.environmentRotation.y=3.2377420f;scene.environmentIntensity=.80f;}
    }
    if(!scene.environment){
        // Source checkouts without the optional probe retain a coherent sky.
        auto environmentScene=Scene::create();environmentScene->name="Cinder daylight fallback";
        auto environmentSky=Mesh::create(light.sky->geometry(),light.sky->material());
        environmentSky->scale.copy(light.sky->scale);environmentSky->frustumCulled=false;environmentScene->add(environmentSky);
        auto groundMaterial=MeshBasicMaterial::create();groundMaterial->color=Color(0x565b3e);
        auto ground=Mesh::create(PlaneGeometry::create(10000,10000),groundMaterial);
        ground->rotation.x=-1.5707963f;ground->position.y=-4;environmentScene->add(ground);
        PMREMGenerator pmrem(renderer);scene.environment=pmrem.fromScene(*environmentScene,.045f,.1f,3000.f);
        scene.environmentRotation.set(0,0,0);scene.environmentIntensity=.70f;
    }

    // Modest fill preserves dark undercuts; the probe and shadowed key describe
    // the material instead of washing every surface with uniform hemisphere.
    scene.add(HemisphereLight::create(light.photographicSky?0xc6dcf2:0xd7e4f3,
        light.photographicSky?0x73634d:0x65543b,light.photographicSky?.12f:.18f));
    light.sun=DirectionalLight::create(light.photographicSky?0xfff4e6:0xffe4bd,
        light.photographicSky?2.7f:3.f);light.sun->castShadow=true;
    light.sun->shadow->mapSize.set(RallyLighting::shadowSize,RallyLighting::shadowSize);
    // Depth bias -0.0008 over the old 119m depth range detached shadows by
    // nearly 10cm. A smaller bias and 1.5cm normal offset preserve tyre contact.
    light.sun->shadow->bias=-.00012f;light.sun->shadow->normalBias=.015f;
    light.sun->shadow->radius=1.05f;light.sun->shadow->intensity=.88f;
    auto camera=light.sun->shadow->camera->as<OrthographicCamera>();
    camera->left=camera->bottom=-RallyLighting::shadowHalfExtent;
    camera->right=camera->top=RallyLighting::shadowHalfExtent;
    camera->nearPlane=1;camera->farPlane=120;camera->updateProjectionMatrix();
    light.target=Group::create();light.sun->setTarget(*light.target);
    scene.add(light.sun);scene.add(light.target);light.follow(Vector3());
    return light;
}
}
