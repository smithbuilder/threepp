// CPU-only checks against the actual rendered model and particle simulation.
#include "RallyBuggy.hpp"
#include "RallyDust.hpp"
#include "RallyCamera.hpp"
#include "RallyDynamics.hpp"
#include "RallyTrails.hpp"
#include "RallySafari.hpp"
#include "RallySafariShadows.hpp"
#include "RallySafariCameraClearance.hpp"
#include "RallyClearance.hpp"
#include "SafariSuspensionTest.hpp"
#include "threepp/math/Triangle.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <regex>
#include "threepp/renderers/shaders/ShaderChunk.hpp"
using namespace threepp;

void require(bool condition,const std::string& message){if(!condition)throw std::runtime_error(message);}

namespace {
void verifySafariShadowPlanes(){
    auto ordinary=MeshStandardMaterial::create();
    require(!ordinary->defines.contains("RALLY_SAFARI_RECEIVER_PLANE_PCF"),"Ordinary materials opt into Safari shadows");
    auto safari=MeshStandardMaterial::create();safari->side=Side::Double;
    const auto side=safari->side;const auto depth=safari->depthWrite;
    require(rally::configureSafariReceiverPlaneShadows(*safari)&&safari->side==side&&safari->depthWrite==depth&&!safari->transparent,
        "Receiver-plane filtering changes caster/culling/depth behavior");
    require(!ordinary->defines.contains("RALLY_SAFARI_RECEIVER_PLANE_PCF"),"Safari filtering leaks to another material");
    const std::array<double,2> map{512,512};
    const auto singular=rally::safariShadowDepthGradient({1,1,1},{2,2,2},map);
    require(!singular.valid,"Singular shadow projection did not use stock fallback");
    const auto extreme=rally::safariShadowDepthGradient({1,0,20},{0,1,20},map);
    require(!extreme.valid,"Near-parallel shadow slope did not use stock fallback");
    for(int i=0;i<4096;++i){
        const double q=.1+.9*((i*149)%4096)/4095.,angle=i*2.399963229728653;
        const double slope=20./119.*std::sqrt(1-q*q)/q;
        const double gu=slope*std::cos(angle),gv=slope*std::sin(angle);
        const auto g=rally::safariShadowDepthGradient({.0013,.0002,gu*.0013+gv*.0002},{-.0001,.002,gu*-.0001+gv*.002},map);
        require(g.valid&&std::abs(g.u-gu)<1e-10&&std::abs(g.v-gv)<1e-10,"Receiver-plane gradient changed the geometric plane");
        const std::array<double,2> uv{((i*137)%4096+.5)/4096.,((i*719)%4096+.5)/4096.};
        // Existing receiver normal/depth separation is preserved.
        const double base=.5-(.015/q/119.+.00012);
        for(int tap=0;tap<5;++tap){
            const double r=std::sqrt((tap+.5)/5.)*1.05/512.,phi=angle+tap*2.399963229728653;
            const std::array<double,2> offset{r*std::cos(phi),r*std::sin(phi)};
            const double ref=rally::safariShadowPcfReference(base,uv,offset,g,map);
            const double u0=(std::floor((uv[0]+offset[0])*512-.5)+.5)/512.;
            const double v0=(std::floor((uv[1]+offset[1])*512-.5)+.5)/512.;
            double highest=-1e10;
            for(int x=0;x<2;++x)for(int y=0;y<2;++y){
                const double u=std::clamp(u0+x/512.,.5/512.,1-.5/512.);
                const double v=std::clamp(v0+y/512.,.5/512.,1-.5/512.);
                const double caster=.5+gu*(u-uv[0])+gv*(v-uv[1]);
                require(ref<=caster+1e-12,"Perfect receiver plane shadows itself");
                highest=std::max(highest,caster);
            }
            // A distinct foreground caster remains fully shadowing. This
            // would fail if the repair simply disabled shadow comparisons.
            require(ref>highest-.025,"Separated foreground occluder loses its shadow");
        }
    }
}

void verifyThinGlassCompositing(){
    const float f0=std::pow((1.5f-1)/(1.5f+1),2.f);
    const auto normal=rally::thinGlassWeights(1,.96f),edge=rally::thinGlassWeights(0,.96f);
    require(std::abs(normal.reflection-f0)<1e-6f&&std::abs(normal.background-.9216f)<1e-6f,"Glass attenuates its dielectric reflection or loses clear transmission");
    require(edge.reflection==1&&edge.background==0&&edge.opacity==1,"Glass does not reflect at grazing incidence");
    for(int v=0;v<=100;++v)for(float bulk:{0.f,.5f,.90f,.96f,1.f}){
        const auto w=rally::thinGlassWeights(v/100.f,bulk);
        require(w.opacity>=0&&w.opacity<=1&&w.reflection+w.background<=1.000001f,"Glass creates energy on a uniform white environment");
        for(float fog:{0.f,.3f,1.f}){
            const float reflected=1.8f,behind=.27f,fogLight=.63f;
            const float source=(1-fog)*w.reflection*reflected+fog*w.opacity*fogLight;
            const float destination=(1-fog)*behind+fog*fogLight;
            const float composited=source+w.background*destination;
            const float expected=(1-fog)*(w.reflection*reflected+w.background*behind)+fog*fogLight;
            require(std::abs(composited-expected)<1e-6f,"Glass fog adds a bright veil at the pane");
        }
    }
    auto paint=MeshStandardMaterial::create();paint->name="safari.cream_enamel";const auto paintDefines=paint->defines;
    require(!rally::configureSafariThinGlass(*paint)&&!paint->transparent&&paint->blending==Blending::Normal&&paint->defines==paintDefines,"Safari glass opt-in changes ordinary paint");
    auto glass=MeshStandardMaterial::create();glass->name="safari.clear_lamp_glass";
    require(rally::configureSafariThinGlass(*glass)&&glass->blendSrc==BlendFactor::One&&glass->blendDst==BlendFactor::OneMinusSrcAlpha&&!glass->premultipliedAlpha&&!glass->depthWrite,"Glass blend state attenuates the Fresnel lobe a second time");
    for(const auto* name:{"safari.headlamp_internal_prism_glass","safari.rear_internal_prism_glass"}){
        auto inner=MeshStandardMaterial::create();inner->name=name;inner->side=Side::Front;
        require(rally::configureSafariThinGlass(*inner)&&inner->side==Side::Double&&inner->defines.at("RALLY_GLASS_BULK_TRANSMISSION")=="1.000000","Lamp back interface is culled, opacity attenuates Fresnel, or slab absorption is counted twice");
    }
    const auto inner=rally::thinGlassWeights(1,1.f);
    const float layeredReflection=normal.reflection+normal.background*inner.reflection;
    const float layeredBackground=normal.background*inner.background;
    require(std::abs(layeredReflection-.076864f)<1e-6f&&std::abs(layeredBackground-.884736f)<1e-6f&&layeredReflection+layeredBackground<=1,"Lamp front/back interfaces lose reflection or apply bulk absorption twice");
    std::cout<<"PASS: thin dielectric normal/grazing reflection, bounded energy and fog compositing math; explicit glass opt-in preserves ordinary paint. Native shader verification remains separate.\n";
}
struct RecordedRideInput {int frame;bool driving;float time,dt,x,z,heading,steer,acceleration,lateral;};
std::vector<RecordedRideInput> recordedRideInputs(){
    const auto path=std::filesystem::path(__FILE__).parent_path()/"testdata"/"safari-native-18mps.ride.csv";
    std::ifstream stream(path);require(static_cast<bool>(stream),"Missing tracked native ride regression fixture");
    std::string line;std::getline(stream,line);std::vector<RecordedRideInput> rows;
    while(std::getline(stream,line)){if(line.empty())continue;std::stringstream row(line);std::string field;std::vector<float> values;
        while(std::getline(row,field,','))values.push_back(std::stof(field));require(values.size()==10,"Invalid native ride fixture row");
        rows.push_back({static_cast<int>(values[0]),values[1]!=0,values[2],values[3],values[4],values[5],values[6],values[7],values[8],values[9]});}
    require(rows.size()==3483,"Native ride regression fixture lost part of its 900-frame lap");return rows;
}
float kineticEnergy(const rally::RideDynamics& r){return .5f*(rally::RideDynamics::mass*r.heaveVelocity*r.heaveVelocity+rally::RideDynamics::pitchInertia*r.pitchVelocity*r.pitchVelocity+rally::RideDynamics::rollInertia*r.rollVelocity*r.rollVelocity);}
void sameRide(const rally::RideDynamics& a,const rally::RideDynamics& b,const std::string& message){
    require(a.chassis.equals(b.chassis)&&a.pitch==b.pitch&&a.roll==b.roll&&a.heaveVelocity==b.heaveVelocity&&a.pitchVelocity==b.pitchVelocity&&a.rollVelocity==b.rollVelocity&&a.travel==b.travel&&a.previousTravel==b.previousTravel&&a.forces==b.forces&&a.grounded==b.grounded&&a.bumpCorrections==b.bumpCorrections,message);
}
void rideContactRegressions(){
    using rally::RideContactResponse;using rally::RideDynamics;const auto dims=rally::safariDimensions;const auto flat=[](float,float){return 0.f;};const Vector3 origin;
    const auto rows=recordedRideInputs();auto height=[](float x,float z){return rally::height(x,z)+.02f;};
    RideDynamics legacy,projected,defaultBuggy,explicitBuggy;
    legacy.reset({0,0,90},rally::pi/2,height,dims);projected.reset({0,0,90},rally::pi/2,height,dims,RideContactResponse::Projected);
    defaultBuggy.reset({0,0,90},rally::pi/2,height);explicitBuggy.reset({0,0,90},rally::pi/2,height,rally::buggyDimensions,RideContactResponse::Legacy);
    float oldHeave=0,oldRoll=0,oldGap=0,oldPenetration=0,newHeave=0,newRoll=0,newPitch=0,newGap=0,newPenetration=0,buggyHeave=0,buggyRoll=0,buggyGap=0;
    for(size_t row=0;row<rows.size();++row){const auto& in=rows[row];const Vector3 p(in.x,0,in.z);
        for(auto* r:{&legacy,&projected,&defaultBuggy,&explicitBuggy})r->step(p,in.heading,in.steer,in.acceleration,in.lateral,in.dt,height);
        sameRide(defaultBuggy,explicitBuggy,"The open buggy's default response changed from explicit Legacy");
        if(in.driving){const auto road=rally::roadPose(p,in.heading,height,dims);oldHeave=std::max(oldHeave,std::abs(legacy.chassis.y-road.ride));oldRoll=std::max(oldRoll,std::abs(legacy.roll));
            newHeave=std::max(newHeave,std::abs(projected.chassis.y-road.ride));newRoll=std::max(newRoll,std::abs(projected.roll));newPitch=std::max(newPitch,std::abs(projected.pitch));
            const auto buggyRoad=rally::roadPose(p,in.heading,height);buggyHeave=std::max(buggyHeave,std::abs(defaultBuggy.chassis.y-buggyRoad.ride));buggyRoll=std::max(buggyRoll,std::abs(defaultBuggy.roll));}
        // Check projected contact on EVERY physics update, not only rendered frames.
        for(int i=0;i<4;++i){auto c=rally::wheelContact(i,projected.chassis,rally::chassisOrientation(in.heading,projected.pitch,projected.roll),in.steer,height,true,dims);newPenetration=std::max(newPenetration,std::max(0.f,-c.gap));
            require(std::isfinite(projected.forces[i])&&projected.forces[i]>=0&&projected.forces[i]<=20000,"Projected corner force invalid");
            if(row+1==rows.size()||rows[row+1].frame!=in.frame){newGap=std::max(newGap,std::max(0.f,c.gap));auto old=rally::wheelContact(i,legacy.chassis,rally::chassisOrientation(in.heading,legacy.pitch,legacy.roll),in.steer,height,true,dims);oldGap=std::max(oldGap,std::max(0.f,old.gap));oldPenetration=std::max(oldPenetration,std::max(0.f,-old.gap));
                auto buggy=rally::wheelContact(i,defaultBuggy.chassis,rally::chassisOrientation(in.heading,defaultBuggy.pitch,defaultBuggy.roll),in.steer,height);buggyGap=std::max(buggyGap,std::max(0.f,buggy.gap));}}
    }
    // These values came from the native pre-repair run, not the new algorithm.
    require(std::abs(oldHeave-1.46689415f)<.00002f&&std::abs(oldRoll-.7f)<.000001f&&std::abs(oldGap-2.02992916f)<.00002f&&std::abs(oldPenetration-.00351142883f)<.000002f&&legacy.bumpCorrections==259,"Legacy no longer reproduces the recorded native baseline");
    require(std::abs(buggyHeave-.614215374f)<.00002f&&std::abs(buggyRoll-.397410423f)<.00002f&&std::abs(buggyGap-.852802753f)<.00002f&&defaultBuggy.bumpCorrections==0,"Accepted open-buggy Legacy rough-route response changed");
    require(newRoll<.40f&&newPitch<.45f,"Projected rough-route response reached an angular hard limit");
    require(newHeave<.80f&&newGap<.95f&&newHeave<oldHeave*.6f&&newGap<oldGap*.5f,"Projected rough-route response still jacks the chassis upward");
    require(newPenetration<.0001f,"Projected rough-route tyre penetrates terrain");

    RideDynamics settled;settled.reset(origin,0,flat,dims,RideContactResponse::Projected);settled.chassis.y+=.10f;
    for(int i=0;i<720;++i)settled.step(origin,0,0,0,0,1.f/120,flat);
    require(std::abs(settled.chassis.y-(dims.tyreRadius-dims.staticTravel))<.003f&&std::abs(settled.heaveVelocity)<.003f,"Projected body fails to settle at unchanged Safari ride height");
    float support=0;for(float f:settled.forces)support+=f;require(std::abs(support-RideDynamics::mass*RideDynamics::gravity)<5,"Projected static support differs from sprung weight");
    auto freeFlight=settled;freeFlight.chassis.y+=1;auto noInput=freeFlight;
    for(int i=0;i<12;++i){freeFlight.step(origin,0,.2f,12,18,1.f/120,flat);noInput.step(origin,0,.2f,0,0,1.f/120,flat);sameRide(freeFlight,noInput,"Unsupported tyres apply an inertial body moment");
        for(int wheel=0;wheel<4;++wheel)require(!freeFlight.grounded[wheel]&&freeFlight.forces[wheel]==0,"Projected droop retains tyre load");}
    require(freeFlight.heaveVelocity<0,"Projected free flight does not fall under gravity");
    for(int i=0;i<720;++i){freeFlight.step(origin,0,0,0,0,1.f/120,flat);auto q=rally::chassisOrientation(0,freeFlight.pitch,freeFlight.roll);
        for(int wheel=0;wheel<4;++wheel)require(rally::wheelContact(wheel,freeFlight.chassis,q,0,flat,true,dims).gap>-.0001f,"Projected landing penetrates flat terrain");}
    require(std::abs(freeFlight.chassis.y-(dims.tyreRadius-dims.staticTravel))<.003f&&std::abs(freeFlight.heaveVelocity)<.003f,"Projected landing fails to dissipate and settle");
    for(float dropHeight:{.3f,1.f,2.f}){auto dropped=settled;dropped.chassis.y+=dropHeight;const float releaseHeight=dropped.chassis.y;
        for(int i=0;i<960;++i){dropped.step(origin,0,0,0,0,1.f/120,flat);require(dropped.chassis.y<=releaseHeight+.01f,"Static-ground landing gains height above its unforced release");}
        require(std::abs(dropped.chassis.y-settled.chassis.y)<.003f&&kineticEnergy(dropped)<.01f,"Unforced projected drop retains landing energy");}

    // Independently check the physical impulse property at varied corner arms
    // and approach velocities: stationary ground cannot add kinetic energy.
    for(float jp:{-1.35f,.4f,1.35f})for(float jr:{-1.08f,.2f,1.08f})for(float vertical:{-6.f,-1.f,2.f}){
        RideDynamics impact;impact.heaveVelocity=vertical;impact.pitchVelocity=.8f;impact.rollVelocity=-1.1f;float before=kineticEnergy(impact);
        impact.resolveBumpVelocity(jp,jr,0);require(kineticEnergy(impact)<=before+.01f,"Stationary bump impulse adds kinetic energy");
        require(impact.heaveVelocity+jp*impact.pitchVelocity+jr*impact.rollVelocity>=-.00001f,"Bump impulse leaves closing normal velocity");}

    auto coarse=settled,fine=settled;for(int n=0;n<90;++n)coarse.step(origin,0,.1f,4,3,1.f/30,flat);for(int n=0;n<360;++n)fine.step(origin,0,.1f,4,3,1.f/120,flat);
    require(coarse.chassis.distanceTo(fine.chassis)<.0001f&&std::abs(coarse.roll-fine.roll)<.0001f&&std::abs(coarse.pitch-fine.pitch)<.0001f,"Projected ride depends on render interval");
    for(float yaw:{-2.8f,-1.5f,.7f,2.4f}){RideDynamics rotated,reference;rotated.reset(origin,yaw,flat,dims,RideContactResponse::Projected);reference.reset(origin,0,flat,dims,RideContactResponse::Projected);
        rotated.chassis.y-=.04f;reference.chassis.y-=.04f;rotated.rollVelocity=reference.rollVelocity=.5f;
        for(int n=0;n<360;++n){rotated.step(origin,yaw,.1f,4,3,1.f/120,flat);reference.step(origin,0,.1f,4,3,1.f/120,flat);}
        require(std::abs(rotated.pitch-reference.pitch)<.0001f&&std::abs(rotated.roll-reference.roll)<.0001f&&std::abs(rotated.chassis.y-reference.chassis.y)<.0001f,"Projected contact response changes with world yaw");}
    RideDynamics automatic;automatic.dimensions=dims;automatic.contactResponse=RideContactResponse::Projected;automatic.step(origin,0,0,0,0,1.f/120,flat);
    require(automatic.contactResponse==RideContactResponse::Projected&&automatic.dimensions.droop==dims.droop,"Automatic reset lost selected response or dimensions");
    std::cout<<"PASS: 900-frame native-input Legacy replay preserved; projected rough lap heave="<<newHeave<<"m, roll="<<newRoll<<"rad, gap="<<newGap<<"m, penetration="<<newPenetration<<"m; unsupported moments, static weight, dissipative impulses, settling/landing, yaw and render-interval checks pass.\n";
}
}
int main(int argc,char** argv){try{
    verifyThinGlassCompositing();
    verifySafariShadowPlanes();
    const auto cameraRegression=rally::safariCameraClearanceRegressions();
    std::cout<<"PASS: Safari camera tracking "<<cameraRegression.summary()<<'\n';
    require(argc<=2,"Usage: RallyVehicle_test [asset-directory]");
    const auto safariAssets=argc==2?std::filesystem::absolute(argv[1]):std::filesystem::path(__FILE__).parent_path()/"assets";
    auto dustMesh=rally::makeDustMesh();auto shader=dustMesh->material()->as<ShaderMaterial>();
    const std::regex include("#include +<([\\w.]+)>");
    for(const auto& source:{shader->vertexShader,shader->fragmentShader})for(auto i=std::sregex_iterator(source.begin(),source.end(),include);i!=std::sregex_iterator();++i)
        require(!threepp::shaders::ShaderChunk::instance().get((*i)[1].str()).empty(),"Dust shader includes missing chunk");
    auto buggy=rally::makeBuggy();auto boxes=rally::fixedBounds(buggy);float minClear=1e6f;
    for(int i=0;i<4;++i){auto envelope=rally::sweptTyreEnvelope(i);auto lo=envelope.min(),hi=envelope.max();
        for(size_t j=0;j<boxes.size();++j){require(!envelope.intersectsBox(boxes[j]),"Tyre swept envelope intersects fixed body mesh "+std::to_string(j));
            auto gap=[](float a,float b,float c,float d){return std::max({0.f,a-d,c-b});};
            float x=gap(lo.x,hi.x,boxes[j].min().x,boxes[j].max().x),y=gap(lo.y,hi.y,boxes[j].min().y,boxes[j].max().y),z=gap(lo.z,hi.z,boxes[j].min().z,boxes[j].max().z);
            minClear=std::min(minClear,std::sqrt(x*x+y*y+z*z));}
    }
    require(minClear>.025f,"Insufficient tyre/body clearance");
    // Triangle clipping must detect a face spanning the cylinder even when
    // every triangle vertex is outside its circular cross-section.
    require(rally::triangleCylinder({0,-2,-2},{0,2,-2},{0,0,2},.5f,.2f),"Cylinder misses spanning triangle");
    require(!rally::triangleCylinder({.5f,-2,-2},{.5f,2,-2},{.5f,0,2},.5f,.2f),"Cylinder ignores finite axial width");
    require(!rally::triangleCylinder({0,1,1},{0,2,1},{0,1,2},.5f,.2f),"Cylinder falsely fills arch opening");
    auto safari=rally::makeSafari(safariAssets);
    require(safari.body->parent==safari.car.get()&&safari.body->position.lengthSq()==0
        &&safari.body->scale==Vector3(1,1,1)&&safari.body->quaternion.x==0&&safari.body->quaternion.y==0
        &&safari.body->quaternion.z==0&&safari.body->quaternion.w==1,
        "Safari constructor/helper moved the body relative to its audited car frame");
    const auto cockpitFinish=rally::validateSafariCockpitFinish(safari.cockpit);
    std::cout<<"PASS: Safari cockpit finish envelope/closed-mesh/animation checks; "<<cockpitFinish.meshes
        <<" meshes, "<<cockpitFinish.supplementalTriangles<<" net detail triangles, "
        <<cockpitFinish.gaugeSilhouetteInflation<<"m bezel chord inflation, "
        <<cockpitFinish.dashboardFaceRelief<<"m dashboard face relief.\n";
    auto safariTriangles=rally::bodyTriangles(safari);const auto& sd=safari.dimensions;
    require(buggy.contactResponse==rally::RideContactResponse::Legacy&&safari.contactResponse==rally::RideContactResponse::Projected,"Vehicle-specific contact response selection lost");
    int transparentShadowChecks=0;safari.car->traverseType<Mesh>([&](Mesh& mesh){for(const auto& material:mesh.materials())if(material->name=="safari.smoky_glazing"||material->name=="safari.clear_lamp_glass"){require(!mesh.castShadow&&mesh.receiveShadow,"Safari blended glass casts an opaque depth shadow");++transparentShadowChecks;}});
    require(transparentShadowChecks>2,"Safari transparent shadow regression missed glass/lamp meshes");
    rideContactRegressions();
    safari_test::run(safari,safariTriangles);
    require(sd.halfTrack<buggy.dimensions.halfTrack&&sd.tyreRadius<buggy.dimensions.tyreRadius,"Safari proportions did not reach actual chassis");
    int safariPoses=0;
    for(int wheel=0;wheel<4;++wheel)for(int t=0;t<=76;++t)for(int a=0;a<=(wheel<2?40:0);++a){
        float travel=sd.droop+(sd.bump-sd.droop)*t/76.f,steer=wheel<2?-.4f+.8f*a/40.f:0;
        auto hit=rally::bodyTyreIntersection(safariTriangles,wheel,travel,steer,sd,.020f);
        if(hit)std::cerr<<"Collision triangle in chassis metres: ("<<hit->a.x<<","<<hit->a.y<<","<<hit->a.z
            <<") ("<<hit->b.x<<","<<hit->b.y<<","<<hit->b.z<<") ("<<hit->c.x<<","<<hit->c.y<<","<<hit->c.z<<")\n";
        require(!hit,"Safari tyre/body surface collision: "+(hit?hit->name:std::string())+" wheel="+std::to_string(wheel)+" travel="+std::to_string(travel)+" steer="+std::to_string(steer));++safariPoses;}
    float eyeClearance=1e6f;for(const auto& face:safariTriangles){Vector3 closest;Triangle(face.a,face.b,face.c).closestPointToPoint(safari.eye,closest);eyeClearance=std::min(eyeClearance,closest.distanceTo(safari.eye));}
    require(eyeClearance>.055f,"Safari cockpit camera too close to actual body surface");
    float meshRadius=0,meshHalfWidth=0;
    for(int wheel=0;wheel<4;++wheel){auto& rolling=*buggy.rolls[wheel];Matrix4 inverse=*rolling.matrixWorld;inverse.invert();
        rolling.traverseType<Mesh>([&](Mesh& mesh){auto* p=mesh.geometry()->getAttribute<float>("position");Matrix4 relative=inverse;relative.multiply(*mesh.matrixWorld);
            auto audit=[&](const Matrix4& transform){for(unsigned j=0;j<p->count();++j){auto v=Vector3(p->getX(j),p->getY(j),p->getZ(j)).applyMatrix4(transform);require(std::isfinite(v.x)&&std::isfinite(v.y)&&std::isfinite(v.z),"Wheel contains invalid vertices");meshHalfWidth=std::max(meshHalfWidth,std::abs(v.x));meshRadius=std::max(meshRadius,std::hypot(v.y,v.z));}};
            if(auto* instanced=dynamic_cast<InstancedMesh*>(&mesh)){for(size_t k=0;k<instanced->count();++k){Matrix4 instance;instanced->getMatrixAt(k,instance);auto transform=relative;transform.multiply(instance);audit(transform);}}else audit(relative);
        });
        Mesh* caliper=nullptr;buggy.pivots[wheel]->traverseType<Mesh>([&](Mesh& m){if(m.name=="fixed-brake-caliper")caliper=&m;});require(caliper!=nullptr,"Wheel has no fixed caliper");
        Vector3 before,after;caliper->getWorldPosition(before);rolling.rotation.x=1.1f;buggy.car->updateMatrixWorld(true);caliper->getWorldPosition(after);require(before.distanceTo(after)<.00001f,"Brake caliper spins with rim");rolling.rotation.x=0;buggy.car->updateMatrixWorld(true);
    }
    require(meshRadius<=rally::tyreRadius+.0001f,"Wheel geometry exceeds rolling radius");require(meshHalfWidth<=rally::tyreHalfWidth+.0001f,"Wheel geometry exceeds lateral envelope");
    require(meshRadius>.53f&&meshHalfWidth>.19f,"Wheel profile unexpectedly undersized");
    // Narrow Safari wheels are physically resized, not only moved inward.
    safari.car->updateMatrixWorld(true);float safariRadius=0,safariWidth=0;
    for(int i=0;i<4;++i){Matrix4 inverse=*safari.pivots[i]->matrixWorld;inverse.invert();
        safari.rolls[i]->traverseType<Mesh>([&](Mesh& mesh){auto* p=mesh.geometry()->getAttribute<float>("position");auto relative=inverse;relative.multiply(*mesh.matrixWorld);
            auto audit=[&](const Matrix4& transform){for(unsigned n=0;n<p->count();++n){auto v=Vector3(p->getX(n),p->getY(n),p->getZ(n)).applyMatrix4(transform);safariRadius=std::max(safariRadius,std::hypot(v.y,v.z));safariWidth=std::max(safariWidth,std::abs(v.x));}};
            if(auto* instanced=dynamic_cast<InstancedMesh*>(&mesh)){for(size_t n=0;n<instanced->count();++n){Matrix4 instance;instanced->getMatrixAt(n,instance);auto transform=relative;transform.multiply(instance);audit(transform);}}else audit(relative);});}
    require(safariRadius<=sd.tyreRadius+.0001f&&safariRadius>sd.tyreRadius*.98f,"Safari actual radius does not match support model");
    require(safariWidth<=sd.tyreHalfWidth+.0001f&&safariWidth>sd.tyreHalfWidth*.95f,"Safari width does not match support model");
    rally::RideDynamics safariRide;auto flatSafari=[](float,float){return 0.f;};safariRide.reset(Vector3(),0,flatSafari,sd);safariRide.chassis.y+=.10f;
    for(int i=0;i<600;++i)safariRide.step(Vector3(),0,0,0,0,1.f/120,flatSafari);
    require(std::abs(safariRide.chassis.y-(sd.tyreRadius-sd.staticTravel))<.003f,"Safari sprung body fails to settle at its own ride height");
    std::vector<float> safariArmLengths;std::array<rally::WheelContact,4> safariWheels;
    for(int i=0;i<4;++i)safariWheels[i].local=rally::hubAtTravel(i,sd.staticTravel,sd);rally::updateSuspension(safari.suspension,safariWheels,0);
    for(auto& arm:safari.suspension.arms)safariArmLengths.push_back(arm.mesh->scale.y);
    for(int t=0;t<=76;++t){float travel=sd.droop+(sd.bump-sd.droop)*t/76.f;
        for(int i=0;i<4;++i)safariWheels[i].local=rally::hubAtTravel(i,travel,sd);rally::updateSuspension(safari.suspension,safariWheels,.4f);
        for(size_t i=0;i<safariArmLengths.size();++i)require(std::abs(safari.suspension.arms[i].mesh->scale.y-safariArmLengths[i])<.00001f,"Narrow Safari arm stretches through travel");}
    float maxGap=0;
    for(int k=0;k<360;++k){float a=k*6.2831853f/360;float x=64*std::sin(a)+8*std::sin(3*a),z=90*std::cos(a);
        float dx=64*std::cos(a)+24*std::cos(3*a),dz=-90*std::sin(a),heading=std::atan2(dx,dz);
        Vector3 f(std::sin(heading),0,std::cos(heading)),r(std::cos(heading),0,-std::sin(heading));std::array<float,4> h;
        for(int i=0;i<4;++i){auto p=rally::wheelAnchor(i);h[i]=rally::height(x+r.x*p.x+f.x*p.z,z+r.z*p.x+f.z*p.z);}
        float pitch=-std::atan2((h[0]+h[1]-h[2]-h[3])*.5f,2*rally::halfWheelbase),roll=std::atan2((h[1]+h[3]-h[0]-h[2])*.5f,2*rally::halfTrack);
        auto q=rally::chassisOrientation(heading,pitch,roll);Vector3 chassis(x,(h[0]+h[1]+h[2]+h[3])*.25f+.13f,z);
        rally::constrainRide(chassis,q,.4f,rally::height);
        for(int i=0;i<4;++i){auto c=rally::wheelContact(i,chassis,q,.4f,rally::height);maxGap=std::max(maxGap,std::abs(c.gap));
            require(std::isfinite(c.gap)&&std::abs(c.gap)<.025f,"Tyre contact lost on course sample "+std::to_string(k));
            require(c.local.y>=rally::droop&&c.local.y<=rally::bump,"Suspension exceeded travel");}
    }
    // Exercise the exact reduced dynamic model without a graphics context.
    auto flat=[](float,float){return 0.f;};Vector3 at(0,0,0);rally::RideDynamics settled;settled.reset(at,0,flat);
    settled.chassis.y+=.12f;float peakAfter=0;bool crossed=false;
    for(int n=0;n<600;++n){settled.step(at,0,0,0,0,1.f/120,flat);if(settled.chassis.y<.13f)crossed=true;if(n>480)peakAfter=std::max(peakAfter,std::abs(settled.chassis.y-.13f));}
    require(crossed&&peakAfter<.003f,"Sprung body fails to settle after displacement");
    require(std::abs(settled.heaveVelocity)<.003f,"Damper leaves persistent bounce");
    float load=0;for(float f:settled.forces)load+=f;require(std::abs(load-rally::RideDynamics::mass*rally::RideDynamics::gravity)<5,"Static springs fail to support sprung weight");
    rally::RideDynamics transfer;transfer.reset(at,0,flat);
    for(int n=0;n<360;++n)transfer.step(at,0,0,8,7,1.f/120,flat);
    require(transfer.pitch<-.01f&&transfer.roll>.01f,"Acceleration/cornering weight transfer has wrong sign");
    require(transfer.forces[2]+transfer.forces[3]>transfer.forces[0]+transfer.forces[1],"Acceleration does not transfer load rearward");
    for(int n=0;n<480;++n)transfer.step(at,0,0,-10,0,1.f/120,flat);
    require(transfer.pitch>.01f&&transfer.forces[0]+transfer.forces[1]>transfer.forces[2]+transfer.forces[3],"Braking does not load front axle");
    auto a=settled,b=settled;for(int n=0;n<90;++n)a.step(at,0,.1f,4,3,1.f/30,flat);for(int n=0;n<360;++n)b.step(at,0,.1f,4,3,1.f/120,flat);
    require(a.chassis.distanceTo(b.chassis)<.0001f&&std::abs(a.roll-b.roll)<.0001f&&std::abs(a.pitch-b.pitch)<.0001f,"Ride depends on render frequency");
    for(float yaw:{-2.8f,-1.5f,.7f,2.4f}){rally::RideDynamics rotated,reference;rotated.reset(at,yaw,flat);reference.reset(at,0,flat);
        for(int n=0;n<360;++n){rotated.step(at,yaw,.1f,4,3,1.f/120,flat);reference.step(at,0,.1f,4,3,1.f/120,flat);}
        require(std::abs(rotated.pitch-reference.pitch)<.0001f&&std::abs(rotated.roll-reference.roll)<.0001f,"Suspension torque changes with world heading");}
    auto airborne=settled;airborne.chassis.y+=1;airborne.step(at,0,0,0,0,1.f/120,flat);
    for(int i=0;i<4;++i)require(!airborne.grounded[i]&&airborne.forces[i]==0,"Airborne tyre retains ground load");
    require(airborne.heaveVelocity<0,"Airborne chassis fails to fall");
    for(int n=0;n<480;++n){airborne.step(at,0,0,0,0,1.f/120,flat);auto q=rally::chassisOrientation(0,airborne.pitch,airborne.roll);
        for(int i=0;i<4;++i){auto c=rally::wheelContact(i,airborne.chassis,q,0,flat);require(c.gap>-.002f,"Landing tyre penetrates ground");}}
    require(std::abs(airborne.chassis.y-.13f)<.003f,"Landing fails to settle");
    auto splitBump=[](float x,float z){return x>0&&z>0?.14f:0.f;};auto articulationRide=settled;
    for(int n=0;n<360;++n)articulationRide.step(at,0,.3f,0,0,1.f/120,splitBump);
    require(articulationRide.travel[1]>articulationRide.travel[0]+.015f,"Four corners fail to react independently");
    for(float f:articulationRide.forces)require(std::isfinite(f)&&f>=0&&f<=20000,"Corner spring load invalid");
    rally::TyreTrails trails;trails.contact(0,{0,0,0},true,.3f,flat);trails.contact(0,{0,0,1},true,.3f,flat);trails.update(.2f);
    require(trails.emitted==1&&trails.mesh->geometry()->getAttribute<float>("strength")->getX(0)>.2f,"Tyre trail not rendered");
    auto* trailPosition=trails.mesh->geometry()->getAttribute<float>("position");float fixedTrail=trailPosition->getZ(1);trails.update(2);
    require(trailPosition->getZ(1)==fixedTrail,"Tyre trail drifts away from ground");
    trails.contact(0,{0,0,2},false,.3f,flat);trails.contact(0,{0,0,3},true,.3f,flat);require(trails.emitted==1,"Trail bridges an airborne wheel");
    trails.update(33);require(trails.mesh->geometry()->getAttribute<float>("strength")->getX(0)==0,"Old trail fails to fade");trails.reset();require(trails.emitted==0&&!trails.connected[0],"Restart retains tyre trails");
    rally::GravelSpray gravel;gravel.spawn({0,0,0},{0,0,1},{1,0,0},{0,0,18},1);auto stoneStart=gravel.particles[0].position;
    gravel.update(.1f,flat);require(gravel.particles[0].position.distanceTo(stoneStart)>.1f,"Gravel remains stationary");
    for(int n=0;n<180;++n)gravel.update(1.f/120,flat);require(gravel.particles[0].age>=gravel.particles[0].life,"Gravel never expires");gravel.reset();require(gravel.emitted==0,"Restart retains gravel");
    std::vector<float> referenceLengths;std::array<rally::WheelContact,4> articulation;
    for(int i=0;i<4;++i)articulation[i].local=rally::hubAtTravel(i,.41f);
    rally::updateSuspension(buggy.suspension,articulation,0);
    for(auto& arm:buggy.suspension.arms)referenceLengths.push_back(arm.mesh->scale.y);
    float longest=0,shortest=10;
    for(int step=0;step<=52;++step){float travel=rally::droop+step*.01f;
        for(int i=0;i<4;++i)articulation[i].local=rally::hubAtTravel(i,travel);
        rally::updateSuspension(buggy.suspension,articulation,.4f);
        for(size_t i=0;i<referenceLengths.size();++i)require(std::abs(buggy.suspension.arms[i].mesh->scale.y-referenceLengths[i])<.00001f,"Wishbone changes length through travel");
        for(auto& shock:buggy.suspension.shocks){longest=std::max(longest,shock.length);shortest=std::min(shortest,shock.length);
            require(shock.barrel->scale.y==1,"Damper barrel stretches");
            auto* p=shock.spring->geometry()->getAttribute<float>("position");int ring=42*rally::coilSides;
            Vector3 a(p->getX(ring),p->getY(ring),p->getZ(ring)),b(p->getX(ring+3),p->getY(ring+3),p->getZ(ring+3));
            require(std::abs(a.distanceTo(b)-2*rally::wireRadius)<.00001f,"Spring wire thickness changes under compression");
            require((shock.length-.16f)/rally::coilTurns>2*rally::wireRadius,"Spring coils intersect");}
    }
    require(longest-shortest>.25f,"Coilover does not articulate");
    require(std::abs(rally::steeringAngle(1,.4f))>std::abs(rally::steeringAngle(0,.4f)),"Inside wheel lacks Ackermann steering");
    const auto screenRight=Vector3(0,0,1).cross(Vector3(0,1,0));
    float rightTurn=rally::steerInput(false,true)*.1f,leftTurn=rally::steerInput(true,false)*.1f;
    require(Vector3(std::sin(rightTurn),0,std::cos(rightTurn)).dot(screenRight)>0,"Right input turns left in cockpit");
    require(Vector3(std::sin(leftTurn),0,std::cos(leftTurn)).dot(screenRight)<0,"Left input turns right in cockpit");
    for(auto& box:boxes)require(!box.containsPoint(rally::driverEye()),"Cockpit eye lies inside bodywork");
    rally::CameraModes modes;for(int i=0;i<4;++i)modes.cycle();require(modes.view==0,"Camera cycle fails to wrap all four views");
    modes.cycle();modes.cycle();modes.toggleCockpit();require(modes.view==3,"Cockpit shortcut fails");modes.toggleCockpit();require(modes.view==2,"Cockpit shortcut loses prior exterior mode");
    for(float heading:{-3.f,0.f,2.f}){auto q=rally::chassisOrientation(heading,.25f,.3f);Vector3 origin(8,3,-9);auto pose=rally::cockpitPose(origin,q);
        auto local=pose.eye.clone().sub(origin).applyQuaternion(q.clone().invert());require(local.distanceTo(rally::driverEye())<.00001f,"Cockpit camera drifts out of seat");require(std::abs(pose.up.length()-1)<.00001f,"Cockpit up vector invalid");}
    rally::DustSimulation dust;dust.spawn(Vector3(0,0,0),Vector3(0,0,1),Vector3(1,0,0),Vector3(0,0,18),18,1);
    auto start=dust.particles[0].position;for(int i=0;i<36;++i)dust.update(1.f/120);
    require(dust.particles[0].position.distanceTo(start)>.25f,"Dust remains fixed in world space");
    require(rally::DustSimulation::opacity(dust.particles[0])>0,"Dust never becomes visible");
    rally::drawDust(*dustMesh,dust,Quaternion());Matrix4 renderedA,renderedB;dustMesh->getMatrixAt(0,renderedA);Color alphaA,alphaB;dustMesh->getColorAt(0,alphaA);
    for(int i=0;i<24;++i)dust.update(1.f/120);rally::drawDust(*dustMesh,dust,Quaternion());dustMesh->getMatrixAt(0,renderedB);dustMesh->getColorAt(0,alphaB);
    require(std::abs(renderedA.elements[14]-renderedB.elements[14])>.05f,"Dust simulation moves but render transform stays fixed");
    require(alphaB.r<alphaA.r&&alphaB.r>0,"Rendered dust opacity fails to fade with age");
    for(int i=0;i<180;++i)dust.update(1.f/120);
    require(rally::DustSimulation::opacity(dust.particles[0])==0,"Dust fails to expire");dust.reset();
    require(dust.serial==0&&rally::DustSimulation::opacity(dust.particles[0])==0,"Restart leaves old dust");
    std::cout<<"PASS: swept tyre/body clearance="<<minClear<<"m; Safari padded surface poses="<<safariPoses<<", eye clearance="<<eyeClearance<<"m; 360 course poses max contact gap="<<maxGap<<"m; actual wheel vertices fit radius/width and calipers remain fixed; spring settling, weight transfer, render-rate independence, airborne load release and landing pass; rigid wishbones, coilovers, Ackermann and seated camera pass; dust advects/fades/resets. No graphics/audio context opened.\n";
    return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
