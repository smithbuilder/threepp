#pragma once
#include "RallyVehicle.hpp"

namespace rally {
// Reference-sheet dimensions, metres. The road solver uses the authored
// coupe's narrow whitewall tyres and 3.0226 m wheelbase.
inline constexpr VehicleDimensions catrinaDimensions{
    .2891f,.0775f,.765f,1.5113f,.19f,.42f,.18f,.2891f};
inline constexpr float catrinaRearHalfTrack=.755f;
inline constexpr float catrinaFrontDroopStop=-.12f,catrinaRearDroopStop=-.28f;
}
