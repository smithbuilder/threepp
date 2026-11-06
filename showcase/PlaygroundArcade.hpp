#pragma once
#include <algorithm>

namespace playground {
// Portable game rule: only multiply tyre drive force while supported. No
// engine/render dependency, launch impulse, pose editing or airborne thrust.
struct ArcadeBoost {
    float charge=1;
    bool active=false;
    float step(bool requested,int supportingTyres,float throttle,float brake,bool reverse,float dt){
        if(dt<=0){active=false;return 1;}
        active=requested&&supportingTyres>=2&&throttle>.15f&&brake<.1f&&!reverse&&charge>0;
        float fraction=active?std::min(charge,dt/2.5f)/(dt/2.5f):0;
        if(active)charge=std::max(0.f,charge-dt/2.5f);
        else if(!requested)charge=std::min(1.f,charge+dt/6.f);
        return 1+fraction; // At most twice normal drive force; tyre grip still limits it.
    }
};
}
