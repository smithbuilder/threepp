#pragma once
#include "RallySafariPowertrain.hpp"
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <limits>
#include <stdexcept>

namespace rally {
// CPU-only audition, deliberately separate from a driving/handling test.
// Export the actual runtime controller rather than duplicating its math in
// the offline WAV mixer. Prescribed speed/pedal states are not a simulated lap.
inline void writeSafariAudioAudit(const std::filesystem::path& directory){
    std::ofstream csv(directory/"audio-controls.csv");
    csv<<std::setprecision(std::numeric_limits<float>::max_digits10)
       <<"time,speed,throttle,rpm,load,gear,shift,exhaustPitch0,exhaustGain0,exhaustPitch1,exhaustGain1,exhaustPitch2,exhaustGain2\n";
    SafariPowertrain state;
    for(int frame=0;frame<720;++frame){
        const float t=frame/30.f;
        const float speed=t<3?0:t<9?(t-3)*22.f/6:t<14?22.f:t<18?(18-t)*5.5f:0;
        const float throttle=t<3?0:t<9?1:t<14?.18f:0;
        state.update(speed,throttle,1.f/30,t<3||t>=18);
        csv<<t<<','<<speed<<','<<throttle<<','<<state.rpm<<','<<state.load<<','<<state.gear<<','<<state.shift;
        for(int band=0;band<3;++band){const auto control=state.band(band,false);csv<<','<<control.pitch<<','<<control.gain;}
        csv<<'\n';
    }
    if(!csv)throw std::runtime_error("Cannot write Safari CPU audio audition controls");
}
}
