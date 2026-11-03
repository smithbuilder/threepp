#pragma once
#include "threepp/materials/MeshStandardMaterial.hpp"
#include "threepp/renderers/shaders/ShaderLib.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <stdexcept>

namespace rally {
struct ThinGlassWeights { float reflection,background,opacity; };
inline ThinGlassWeights thinGlassWeights(float normalViewCosine,float bulkTransmission){
    const float cosine=std::clamp(std::abs(normalViewCosine),0.f,1.f);
    // Schlick's dielectric approximation, n=1.5 in air (F0=0.04).
    const float reflection=.04f+.96f*std::pow(1-cosine,5.f);
    const float background=(1-reflection)*std::clamp(bulkTransmission,0.f,1.f);
    return {reflection,background,1-background};
}
inline void installSafariGlassShading(){
    // The rally composer already blends scene geometry into linear HalfFloat
    // targets before its OutputPass. This uses those existing targets/passes;
    // it adds neither screen-space transmission nor a refraction render.
    static const bool installed=[] {
        auto& library=threepp::shaders::ShaderLib::instance();
        for(auto* shader:std::array{&library.standard,&library.physical}){
            auto& source=shader->fragmentShader;
            const std::string opaque="#include <opaque_fragment>",fog="#include <fog_fragment>";
            const auto outputAt=source.find(opaque),fogAt=source.find(fog);
            if(outputAt==std::string::npos||fogAt==std::string::npos)
                throw std::runtime_error("Safari glass shader anchors changed; review before rendering");
            const std::string glass=R"GLSL(
#ifdef RALLY_GLASS_BULK_TRANSMISSION
    float rallyGlassNoV = clamp(abs(dot(geometry.normal, geometry.viewDir)), 0.0, 1.0);
    float rallyGlassF = 0.04 + 0.96 * pow(1.0 - rallyGlassNoV, 5.0);
    diffuseColor.a = 1.0 - (1.0 - rallyGlassF) * RALLY_GLASS_BULK_TRANSMISSION;
    // The PBR specular lobe already includes Fresnel. Do not attenuate it
    // again by BLEND opacity or add a fictitious diffuse glass surface.
    outgoingLight = totalSpecular;
#endif
)GLSL";
            source.insert(outputAt,glass);
            const std::string glassFog=R"GLSL(
#ifdef RALLY_GLASS_BULK_TRANSMISSION
    #ifdef USE_FOG
        #ifdef FOG_EXP2
            float rallyFogFactor = 1.0 - exp(-fogDensity * fogDensity * fogDepth * fogDepth);
        #else
            float rallyFogFactor = smoothstep(fogNear, fogFar, fogDepth);
        #endif
        // Source RGB is already reflection-weighted. Weight fog's contribution
        // by source opacity too, so fogged glass does not double the fog light.
        gl_FragColor.rgb = mix(gl_FragColor.rgb, fogColor * gl_FragColor.a, rallyFogFactor);
    #endif
#else
    #include <fog_fragment>
#endif
)GLSL";
            source.replace(source.find(fog),fog.size(),glassFog);
        }
        return true;
    }();
    (void)installed;
}
inline bool configureSafariThinGlass(threepp::Material& material){
    float bulk=0;
    const bool inner=material.name=="safari.headlamp_internal_prism_glass"||material.name=="safari.rear_internal_prism_glass";
    if(material.name=="safari.smoky_glazing")bulk=.90f;
    else if(material.name=="safari.clear_lamp_glass"||material.name=="safari.rear_optical_cover")bulk=.96f;
    else if(inner)bulk=1.f; // Outer surface owns the slab's absorption once.
    else return false;
    auto* pbr=material.as<threepp::MeshStandardMaterial>();
    if(!pbr)throw std::runtime_error("Safari thin glass requires the PBR material");
    installSafariGlassShading();
    // Defines participate in threepp's program cache key. Materials without
    // this explicit opt-in retain the stock shader and blending behavior.
    pbr->defines["RALLY_GLASS_BULK_TRANSMISSION"]=std::to_string(bulk);
    material.transparent=true;material.depthTest=true;material.depthWrite=false;
    material.blending=threepp::Blending::Custom;
    material.blendSrc=threepp::BlendFactor::One;
    material.blendDst=threepp::BlendFactor::OneMinusSrcAlpha;
    material.blendSrcAlpha=threepp::BlendFactor::One;
    material.blendDstAlpha=threepp::BlendFactor::OneMinusSrcAlpha;
    material.blendEquation=threepp::BlendEquation::Add;
    material.blendEquationAlpha=threepp::BlendEquation::Add;
    material.premultipliedAlpha=false;
    // Internal back interfaces face into the lamp. Outside observers see their
    // back faces; preserve both viewing directions instead of culling them.
    if(inner)material.side=threepp::Side::Double;
    else if(material.name=="safari.rear_optical_cover"||material.name=="safari.clear_lamp_glass")material.side=threepp::Side::Front;
    return true;
}
}
