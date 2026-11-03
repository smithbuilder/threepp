#pragma once
#include <algorithm>
#include <cmath>

namespace rally {
inline constexpr float safariStageRippleAmplitude=.045f;

// Grade the actual rendered road, not an invisible collision-only surface.
// Broad hills/banks remain. The old 170mm sine (340mm crest to trough) forced
// 1.5-2.1g vertical input at 49km/h, close to sprung-body pitch resonance.
// The maintained centre retains 45mm roughness; shoulders meet the old land.
inline float safariStageRoadHeight(float x,float z,float lateral,float originalGround){
    const float edge=std::clamp((std::abs(lateral)-.62f)/.38f,0.f,1.f);
    const float shoulder=edge*edge*(3-2*edge);
    return originalGround-(.17f-safariStageRippleAmplitude)*(1-shoulder)*std::sin(x*.7f+z*.4f)+.02f;
}
}
