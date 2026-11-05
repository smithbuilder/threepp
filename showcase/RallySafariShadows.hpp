#pragma once
#include "threepp/materials/MeshStandardMaterial.hpp"
#include "threepp/renderers/shaders/ShaderChunk.hpp"
#include "threepp/renderers/shaders/ShaderLib.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <stdexcept>
#include <string>

namespace rally {

// CPU equivalents of the GLSL below, for checking the actual comparison math.
// Coordinates and depths are normalized shadow-map coordinates, after divide.
struct SafariShadowGradient { double u{},v{}; bool valid{}; };
inline SafariShadowGradient safariShadowDepthGradient(
        const std::array<double,3>& dx,const std::array<double,3>& dy,
        const std::array<double,2>& mapSize){
    const double det=dx[0]*dy[1]-dx[1]*dy[0];
    const double scale=(dx[0]*dx[0]+dx[1]*dx[1])*(dy[0]*dy[0]+dy[1]*dy[1]);
    if(!(det*det>1e-8*std::max(scale,1e-30)))return {};
    const double u=(dx[2]*dy[1]-dy[2]*dx[1])/det;
    const double v=(dx[0]*dy[2]-dy[0]*dx[2])/det;
    const double footprint=std::abs(u)/mapSize[0]+std::abs(v)/mapSize[1];
    if(!(footprint<=.005))return {}; // Also rejects non-finite results.
    return {u,v,true};
}
inline double safariShadowPcfReference(double depth,const std::array<double,2>& uv,
        const std::array<double,2>& offset,const SafariShadowGradient& gradient,
        const std::array<double,2>& mapSize){
    if(!gradient.valid)return depth;
    const std::array<double,2> g{gradient.u,gradient.v};
    double delta=0;
    for(int i=0;i<2;++i){
        const double texel=1/mapSize[i],sample=uv[i]+offset[i];
        const double low=(std::floor(sample*mapSize[i]-.5)+.5)*texel;
        const double lo=std::clamp(low,.5*texel,1-.5*texel);
        const double hi=std::clamp(low+texel,.5*texel,1-.5*texel);
        delta+=g[i]*offset[i]+std::min(g[i]*(lo-sample),g[i]*(hi-sample));
    }
    return depth+(std::abs(delta)<=.01?delta:0);
}

inline void safariShadowReplaceOnce(std::string& source,const std::string& anchor,
        const std::string& replacement){
    const auto at=source.find(anchor);
    if(at==std::string::npos||source.find(anchor,at+anchor.size())!=std::string::npos)
        throw std::runtime_error("Safari shadow shader anchor changed; review before rendering");
    source.replace(at,anchor.size(),replacement);
}

inline std::string safariReceiverPlaneShadowChunk(){
    // Copy the engine chunk. Only this rally shader's explicit macro branch
    // uses the additions; the engine's immutable chunk stays untouched.
    auto source=threepp::shaders::ShaderChunk::instance().shadowmap_pars_fragment();
    const std::string anchor="\n\t#elif defined( SHADOWMAP_TYPE_VSM )";
    const std::string helpers=R"GLSL(

        // Directional light visibility is uniform across the fragment quad.
        // Do not call this derivative path from a spot-light visibility branch.
        vec2 rallySafariShadowDepthGradient(vec3 coord, vec2 texelSize) {
            vec3 dx = dFdx(coord);
            vec3 dy = dFdy(coord);
            float determinant = dx.x * dy.y - dx.y * dy.x;
            float jacobianScale = dot(dx.xy, dx.xy) * dot(dy.xy, dy.xy);
            if (!(determinant * determinant > 1e-8 * max(jacobianScale, 1e-30)))
                return vec2(0.0);
            vec2 gradient = vec2(dx.z * dy.y - dy.z * dx.y,
                                 dx.x * dy.z - dy.x * dx.z) / determinant;
            // A near-parallel receiver has unbounded light-space slope. Use
            // stock comparisons for that case instead of unbounded light leaks.
            // At the current 20m/119m projection, all planar |N.L| >= .1 pass.
            float footprint = dot(abs(gradient), texelSize);
            if (!(footprint <= 0.005)) return vec2(0.0);
            return gradient;
        }

        float rallySafariPlanePcfTap(sampler2DShadow shadowMap, vec3 coord,
                vec2 mapSize, vec2 texelSize, vec2 offset, vec2 gradient) {
            vec2 sampleUv = coord.xy + offset;
            vec2 low = (floor(sampleUv * mapSize - 0.5) + 0.5) * texelSize;
            // Match CLAMP_TO_EDGE, including taps crossing the shadow frustum.
            vec2 lo = clamp(low, 0.5 * texelSize, vec2(1.0) - 0.5 * texelSize);
            vec2 hi = clamp(low + texelSize, 0.5 * texelSize, vec2(1.0) - 0.5 * texelSize);
            vec2 nearestDepth = min(gradient * (lo - sampleUv), gradient * (hi - sampleUv));
            // First follow the receiver plane to the Vogel sample. Hardware
            // linear comparison uses one reference for four texel centres:
            // their minimum plane depth is the least conservative reference
            // that prevents any of those same-plane texels shadowing itself.
            float delta = dot(gradient, offset) + nearestDepth.x + nearestDepth.y;
            if (!(abs(delta) <= 0.01)) delta = 0.0;
            return texture(shadowMap, vec3(sampleUv, coord.z + delta));
        }

        float rallySafariDirectionalShadow(sampler2DShadow shadowMap, vec2 shadowMapSize,
                float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord) {
            shadowCoord.xyz /= shadowCoord.w;
            vec2 texelSize = vec2(1.0) / shadowMapSize;
            // Evaluate derivatives before the per-fragment frustum branch.
            vec2 gradient = rallySafariShadowDepthGradient(shadowCoord.xyz, texelSize);
            shadowCoord.z += shadowBias;
            bool inFrustum = shadowCoord.x >= 0.0 && shadowCoord.x <= 1.0
                          && shadowCoord.y >= 0.0 && shadowCoord.y <= 1.0;
            bool frustumTest = inFrustum && shadowCoord.z <= 1.0;
            float shadow = 1.0;
            if (frustumTest) {
                float radius = shadowRadius * texelSize.x;
                float phi = interleavedGradientNoise(gl_FragCoord.xy) * PI2;
                shadow = (
                    rallySafariPlanePcfTap(shadowMap, shadowCoord.xyz, shadowMapSize, texelSize, vogelDiskSample(0, 5, phi) * radius, gradient) +
                    rallySafariPlanePcfTap(shadowMap, shadowCoord.xyz, shadowMapSize, texelSize, vogelDiskSample(1, 5, phi) * radius, gradient) +
                    rallySafariPlanePcfTap(shadowMap, shadowCoord.xyz, shadowMapSize, texelSize, vogelDiskSample(2, 5, phi) * radius, gradient) +
                    rallySafariPlanePcfTap(shadowMap, shadowCoord.xyz, shadowMapSize, texelSize, vogelDiskSample(3, 5, phi) * radius, gradient) +
                    rallySafariPlanePcfTap(shadowMap, shadowCoord.xyz, shadowMapSize, texelSize, vogelDiskSample(4, 5, phi) * radius, gradient)
                ) * 0.2;
            }
            return mix(1.0, shadow, shadowIntensity);
        }
)GLSL";
    safariShadowReplaceOnce(source,anchor,helpers+anchor);
    return source;
}

inline std::string safariReceiverPlaneLightingChunk(){
    auto source=threepp::shaders::ShaderChunk::instance().lights_fragment_begin();
    const std::string anchor="getShadow( directionalShadowMap[ i ]";
    safariShadowReplaceOnce(source,anchor,"rallySafariDirectionalShadow( directionalShadowMap[ i ]");
    return source;
}

inline void installSafariReceiverPlaneShadows(){
    static const bool installed=[] {
        auto& library=threepp::shaders::ShaderLib::instance();
        const auto shadow=safariReceiverPlaneShadowChunk();
        const auto lighting=safariReceiverPlaneLightingChunk();
        for(auto* shader:std::array{&library.standard,&library.physical}){
            auto& source=shader->fragmentShader;
            const std::string shadowAnchor="#include <shadowmap_pars_fragment>";
            const std::string lightingAnchor="#include <lights_fragment_begin>";
            const std::string guard="#if defined(RALLY_SAFARI_RECEIVER_PLANE_PCF) && defined(SHADOWMAP_TYPE_PCF)\n";
            safariShadowReplaceOnce(source,shadowAnchor,guard+shadow+"\n#else\n"+shadowAnchor+"\n#endif\n");
            safariShadowReplaceOnce(source,lightingAnchor,guard+lighting+"\n#else\n"+lightingAnchor+"\n#endif\n");
        }
        return true;
    }();
    (void)installed;
}

// Caller opts in only the Safari car's materials, after its construction. No
// material name/side/transparency/cast/depth state is changed. Live Safari
// wheels and suspension are included if the caller visits those materials.
inline bool configureSafariReceiverPlaneShadows(threepp::Material& material){
    auto* pbr=material.as<threepp::MeshStandardMaterial>();
    if(!pbr)return false;
    installSafariReceiverPlaneShadows();
    pbr->defines["RALLY_SAFARI_RECEIVER_PLANE_PCF"]="1";
    return true;
}

}
