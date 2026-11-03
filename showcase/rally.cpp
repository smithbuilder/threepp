// CINDER FOREST: an isolated successor to the original driving study.
// Ground-following handling is custom arcade motion, not a PhysX simulation.
#include "FrameBudget.hpp"
#include "RallyDetail.hpp"
#include "RallyHud.hpp"
#include "RallyPowertrain.hpp"
#include "RallySafariPowertrain.hpp"
#include "RallyBuggy.hpp"
#include "RallyDust.hpp"
#include "RallyCamera.hpp"
#include "RallyDynamics.hpp"
#include "RallyTrails.hpp"
#include "RallyLighting.hpp"
#include "RallySafari.hpp"
#include "RallySafariShadows.hpp"
#include "RallySafariCameraClearance.hpp"
#include "RallySafariMotion.hpp"
#include "RallyRoadContact.hpp"
#include "RallySafariStage.hpp"
#include "SafariRideAudit.hpp"
#include "threepp/threepp.hpp"
#include "threepp/extras/imgui/ImguiContext.hpp"
#include "threepp/extras/vegetation/TreeGenerator.hpp"
#include "threepp/geometries/IcosahedronGeometry.hpp"
#include "threepp/materials/ShaderMaterial.hpp"
#include "threepp/postprocessing/postprocessing.hpp"
#include "threepp/textures/DataTexture.hpp"
#include "threepp/audio/Audio.hpp"
#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <random>
#include <cstdio>
#include <cstdlib>
#include <limits>
#include <array>

using namespace threepp;
constexpr float PI = 3.14159265359f;
float groundHeight(float x, float z) { return rally::height(x,z); }
float supportHeight(float x,float z){return groundHeight(x,z)+.02f;}
Vector3 track(float a) { float x = 64 * std::sin(a) + 8 * std::sin(3 * a), z = 90 * std::cos(a); return {x, groundHeight(x, z), z}; }
float wrap(float a) { while (a > PI) a -= 2 * PI; while (a < -PI) a += 2 * PI; return a; }
auto material(unsigned c, float rough = .8f, float metal = 0) {
    auto m = MeshStandardMaterial::create(); m->color = Color(c); m->roughness = rough; m->metalness = metal; return m;
}

struct CoursePoint { Vector3 p; float a; };
// Cut the coarse terrain out beneath the finer road ribbon. This avoids
// intersecting surfaces without floating the driving road above tyre support.
auto roadCutout(const std::vector<CoursePoint>& route){
    constexpr int size=1024;constexpr float extent=520,radius=3.18f;
    std::vector<unsigned char> pixels(size*size*4,255);
    for(size_t i=0;i+1<route.size();++i){auto a=route[i].p,b=route[i+1].p;float dx=b.x-a.x,dz=b.z-a.z,length2=dx*dx+dz*dz;
        int x0=std::clamp(static_cast<int>((std::min(a.x,b.x)-radius+260)*size/extent),0,size-1),x1=std::clamp(static_cast<int>((std::max(a.x,b.x)+radius+260)*size/extent)+1,0,size-1);
        int y0=std::clamp(static_cast<int>((260-std::max(a.z,b.z)-radius)*size/extent),0,size-1),y1=std::clamp(static_cast<int>((260-std::min(a.z,b.z)+radius)*size/extent)+1,0,size-1);
        for(int y=y0;y<=y1;++y)for(int x=x0;x<=x1;++x){float wx=(x+.5f)*extent/size-260,wz=260-(y+.5f)*extent/size;
            float t=std::clamp(((wx-a.x)*dx+(wz-a.z)*dz)/std::max(.0001f,length2),0.f,1.f);
            float px=wx-a.x-t*dx,pz=wz-a.z-t*dz;if(px*px+pz*pz<radius*radius)pixels[(y*size+x)*4+1]=0;}}
    auto map=DataTexture::create(pixels,size,size);texgen::finishTexture(map,false,false);return map;
}
struct Driver {
    Vector3 position = track(0);
    float heading = PI / 2, velocity = 0, steer = 0, wheelAngle = 0, elapsed = 0, best = 0;
    int next = 1, laps = 0, contacts = 0;
    bool running = false, finished=false;
    float throttle=0,braking=0;
    float message = 0;
    float heave=groundHeight(0,90), pitch=0, roll=0, yawRate=0, previousVelocity=0;
    rally::RideDynamics ride;
    float lastLap=0, maxHeave=0, maxRoll=0;
    float contactCooldown=0;
    Vector3 motion;
    void reset() { float oldBest = best; *this = Driver{}; best = oldBest; }
};

int main(int argc, char** argv) {
    try {
        if(argc>1&&std::string(argv[1])=="--physics-audit"){
            if(argc<3||!std::getenv("THREEPP_EVALUATION_MODE"))throw std::runtime_error("CPU physics audit requires its supervised output directory");
            return rally::runSafariRideAudit(argv[2]); // No Canvas/audio/renderer.
        }
        bool scripted = false,wheelInspect=false,portrait=false,portraitOrbit=false,safari=false; int frames = 0, limit = 0, initialView=0, warmup=0,captureScale=1; std::string shot, telemetry, sequence,portraitAngle="front",portraitLight="rear",portraitEnvironment="forest",portraitShadows="default";
        for (int i = 1; i < argc; ++i) {
            std::string a = argv[i];
            if (a == "--autodrive") scripted = true;
            else if (a == "--wheel-inspect") wheelInspect=true;
            else if (a == "--portrait") portrait=true;
            else if(a=="--portrait-angle"&&i+1<argc)portraitAngle=argv[++i];
            else if(a=="--portrait-orbit")portraitOrbit=true;
            else if(a=="--portrait-light"&&i+1<argc){portraitLight=argv[++i];if(portraitLight!="rear"&&portraitLight!="front")throw std::runtime_error("Unknown portrait lighting angle");}
            else if(a=="--portrait-environment"&&i+1<argc){portraitEnvironment=argv[++i];if(portraitEnvironment!="forest"&&portraitEnvironment!="daylight")throw std::runtime_error("Unknown portrait environment");}
            else if(a=="--portrait-shadows"&&i+1<argc){portraitShadows=argv[++i];if(portraitShadows!="default"&&portraitShadows!="stock"&&portraitShadows!="off")throw std::runtime_error("Unknown portrait shadow profile");}
            else if(a=="--vehicle"&&i+1<argc){std::string choice=argv[++i];if(choice!="buggy"&&choice!="safari")throw std::runtime_error("Unknown vehicle");safari=choice=="safari";}
            else if (a == "--frames" && i + 1 < argc) limit = std::max(1, std::stoi(argv[++i]));
            else if (a == "--shot" && i + 1 < argc) shot = argv[++i];
            else if(a=="--capture-scale"&&i+1<argc){captureScale=std::stoi(argv[++i]);if(captureScale!=1&&captureScale!=2)throw std::runtime_error("Capture scale must be 1 or 2");}
            else if (a == "--telemetry" && i + 1 < argc) telemetry = argv[++i];
            else if (a == "--view" && i + 1 < argc) initialView = std::clamp(std::stoi(argv[++i]),0,3);
            else if (a == "--sequence" && i + 1 < argc) sequence=argv[++i];
            else if (a == "--warmup" && i + 1 < argc) warmup=std::clamp(std::stoi(argv[++i]),0,900);
        }
        if(!sequence.empty()&&(!shot.empty()||limit<1||limit>900))throw std::runtime_error("Sequence capture requires 1..900 frames and no --shot");
        rally::CameraModes cameras(initialView);int& view=cameras.view;
        rally::SafariCameraTracking safariCameraTracking;
        const bool captureMode=!shot.empty()||!sequence.empty();
        if(captureScale==2&&(!captureMode||(sequence.empty()?(limit!=1||warmup!=0):(limit+warmup>180))))throw std::runtime_error("High-resolution profile allows one still or at most 180 total sequence frames");
        if(captureScale==2&&!std::getenv("THREEPP_EVALUATION_MODE"))throw std::runtime_error("High-resolution inspection requires the evaluation supervisor");
        std::ofstream rideInputs;
        if(!telemetry.empty()){
            auto inputPath=std::filesystem::path(telemetry);inputPath.replace_extension(".ride.csv");rideInputs.open(inputPath);
            if(!rideInputs)throw std::runtime_error("Cannot write ride input diagnostics");
            rideInputs<<std::setprecision(std::numeric_limits<float>::max_digits10)
                <<"frame,driving,time,dt,x,z,heading,steer,acceleration,lateral\n";
        }
        const float inspectionFloor=groundHeight(0,90)+.02f;
        const bool safariStage=safari; // Course stays fixed when switching cars.
        std::shared_ptr<rally::RoadContactSurface> roadContact,landContact;
        auto vehicleHeight=[&](float x,float z){
            if(portrait)return inspectionFloor;
            if((safari||safariStage)&&roadContact)if(const auto y=roadContact->height(x,z))return *y;
            if((safari||safariStage)&&landContact)if(const auto y=landContact->height(x,z))return *y;
            return supportHeight(x,z);
        };
        if((wheelInspect||portrait)&&!captureMode)throw std::runtime_error("Wheel inspection is capture-only");
        if(portraitEnvironment!="forest"&&!portrait)throw std::runtime_error("Daylight inspection environment requires portrait capture");
        if(portraitShadows!="default"&&!portrait)throw std::runtime_error("Shadow diagnostics require portrait capture");
        if(portraitOrbit&&(!portrait||sequence.empty()||(portraitAngle!="front"&&portraitAngle!="side"&&portraitAngle!="rear")))throw std::runtime_error("Portrait orbit requires an inspection sequence");
        std::ofstream frameData;
        if(!sequence.empty()){std::filesystem::create_directories(sequence);frameData.open(std::filesystem::path(sequence)/"frame-data.csv");
            if(!frameData)throw std::runtime_error("Cannot write sequence telemetry");frameData<<"frame,simulation_time,speed,view,rpm,load,gear,shift,finished,wheelFL,wheelFR,wheelRL,wheelRR,dustEmitted,heave,pitch,roll,forceFL,forceFR,forceRL,forceRR,cameraBoomFraction,cameraBlocked,cameraForecastFraction,cameraHardClamped,exhaustPitch0,exhaustGain0,exhaustPitch1,exhaustGain1,exhaustPitch2,exhaustGain2,gapFL,gapFR,gapRL,gapRR\n";}
        const bool bounded = limit > 0;
        auto assetDir=std::filesystem::absolute(argv[0]).parent_path()/"rally-assets";
        TextureLoader textureLoader;
        auto assetTexture=[&](const std::string& name,bool srgb){auto t=textureLoader.load(assetDir/name);
            if(!t)throw std::runtime_error("Missing rally texture: "+name);
            t->colorSpace=srgb?ColorSpace::sRGB:ColorSpace::NoColorSpace;t->wrapS=t->wrapT=TextureWrapping::Repeat;t->anisotropy=2;return t;};
        Canvas canvas(Canvas::Parameters().title("CINDER FOREST | rally candidate").size(960*captureScale,600*captureScale).vsync(true).headless(captureMode));
        GLRenderer renderer(canvas); renderer.checkShaderErrors = true;
        auto scene=Scene::create();auto lighting=rally::makeRallyLighting(renderer,*scene,assetDir,!(portrait&&portraitEnvironment=="daylight"));
        if(portrait&&portraitShadows=="off")renderer.shadowMap().enabled=false;
        auto add = [&](std::shared_ptr<BufferGeometry> geo, std::shared_ptr<Material> mat, Vector3 p) {
            auto m = Mesh::create(geo, mat); m->position.copy(p); m->castShadow = m->receiveShadow = true; scene->add(m); return m;
        };
        auto land = PlaneGeometry::create(520, 520, 160, 160); land->rotateX(-PI / 2);
        auto positions = land->getAttribute<float>("position"); std::vector<float> colors;
        for (unsigned i = 0; i < positions->count(); ++i) {
            float x = positions->getX(i), z = positions->getZ(i); positions->setY(i, groundHeight(x, z));
            float s = noise::fbm(x*.05f,z*.05f,256,8,4);
            float slope=std::abs(groundHeight(x+1,z)-groundHeight(x-1,z))*.5f;
            Color c(slope>.55f?0xa69d87:0xd9d6c3); c.multiplyScalar(.62f + .6f * s);
            colors.insert(colors.end(), {c.r, c.g, c.b});
        }
        land->setAttribute("color", FloatBufferAttribute::create(colors, 3)); land->computeVertexNormals();
        std::vector<float> landContactVertices;std::vector<unsigned> landContactIndices;
        landContactVertices.reserve(positions->count()*3);
        for(unsigned i=0;i<positions->count();++i)landContactVertices.insert(landContactVertices.end(),{positions->getX(i),positions->getY(i),positions->getZ(i)});
        const auto* landIndex=land->getIndex();landContactIndices.reserve(landIndex->count());
        for(unsigned i=0;i<landIndex->count();++i)landContactIndices.push_back(landIndex->getX(i));
        landContact=std::make_shared<rally::RoadContactSurface>(landContactVertices,landContactIndices);
        auto grass = material(0xffffff); grass->vertexColors = true;
        grass->map=assetTexture("forest_ground_04_diff_1k.jpg",true);grass->map->repeat.set(65,65);
        grass->normalMap=assetTexture("forest_ground_04_nor_gl_1k.jpg",false);grass->normalMap->repeat.set(65,65);grass->normalScale.set(.55f,.55f);
        add(land, grass, {});
        std::vector<CoursePoint> route; std::vector<float> ribbon, roadUv, roadColors; std::vector<unsigned> indices;
        constexpr int across = 8;
        for (int i = 0; i <= 320; ++i) {
            float a = i * 2 * PI / 320;
            Vector3 p = track(a), tangent = track(a + .001f).sub(p).normalize();
            Vector3 side(tangent.z, 0, -tangent.x);
            route.push_back({p, a});
            for (int j = 0; j <= across; ++j) {
                float s = j * 2.f / across - 1;
                float x = p.x + s * 3.7f * side.x, z = p.z + s * 3.7f * side.z;
                const float roadY=safariStage?rally::safariStageRoadHeight(x,z,s,groundHeight(x,z)):groundHeight(x,z)+.02f;
                ribbon.insert(ribbon.end(), {x,roadY,z});
                roadUv.insert(roadUv.end(), {j * 1.f/across, i * .12f});
                const float rut = .8f + .2f * std::pow(std::abs(s), .5f);
                roadColors.insert(roadColors.end(), {rut, rut, rut});
            }
            if (i < 320) for (int j = 0; j < across; ++j) {
                unsigned b = i * (across+1) + j;
                indices.insert(indices.end(), {b, b + across + 1, b + 1, b + 1, b + across + 1, b + across + 2});
            }
        }
        grass->alphaMap=roadCutout(route);grass->alphaTest=.5f;
        auto road = BufferGeometry::create(); road->setAttribute("position", FloatBufferAttribute::create(ribbon, 3)); road->setIndex(indices); road->computeVertexNormals();
        roadContact=std::make_shared<rally::RoadContactSurface>(ribbon,indices);
        road->setAttribute("uv", FloatBufferAttribute::create(roadUv, 2)); road->setAttribute("color", FloatBufferAttribute::create(roadColors, 3));
        auto dirt = material(0xffffff); dirt->map = assetTexture("gravel_road_diff_1k.jpg",true); dirt->vertexColors = true; dirt->side = Side::Double;
        dirt->map->repeat.set(2,2);dirt->normalMap=assetTexture("gravel_road_nor_gl_1k.jpg",false);dirt->normalMap->repeat.set(2,2);dirt->normalScale.set(.7f,.7f);
        auto trail = add(road, dirt, {}); trail->castShadow = false;
        auto nearest = [&](Vector3 p) {
            CoursePoint answer = route.front(); float best = 1e20f;
            for (auto& r : route) { float d = (p.x-r.p.x)*(p.x-r.p.x)+(p.z-r.p.z)*(p.z-r.p.z); if (d < best) { best = d; answer = r; } }
            return answer;
        };
        // Reuse three generated tree species across 180 placements. Geometry and
        // textures are shared; trunks and foliage each draw in one instanced batch.
        std::mt19937 rng(29); std::uniform_real_distribution<float> random(0, 1);
        std::vector<Vector3> treePositions;
        for (int species = 0; species < 3; ++species) {
            vegetation::TreeParams p; vegetation::applyPreset(species == 0 ? 1 : species == 1 ? 2 : 0, p);
            p.seed = 123 + species; p.attractorCount = 300;
            vegetation::TreeGenerator g(p.seed); g.buildSkeleton(p);
            auto bark = vegetation::makeBarkTextures(128, p.seed, p.barkColor, p.barkStyle);
            auto bm = material(0xffffff); bm->map = bark.first; bm->normalMap = bark.second; bm->vertexColors = true;
            auto lm = material(0xffffff); lm->vertexColors = true; lm->side = Side::Double; lm->alphaTest = vegetation::kLeafAlphaTest;
            lm->map = p.leafStyle == vegetation::LeafStyle::Frond
                ? vegetation::makeNeedleFrondTexture(128, p.seed, p.leafColor, p.leafAtlasCells)
                : vegetation::makeLeafClusterTexture(128, p.seed, p.leafColor, p.leafShape, 8, p.leafAtlasCells);
            auto trunks = InstancedMesh::create(g.makeTrunkGeometry(p), bm, 60), leaves = InstancedMesh::create(g.makeLeafGeometry(p), lm, 60);
            trunks->castShadow = trunks->receiveShadow = leaves->receiveShadow = true;
            leaves->castShadow = false; // Keep alpha-tested canopy out of the local shadow pass.
            for (int i = 0; i < 60; ++i) {
                float a=(i+random(rng))*2*PI/60;
                auto centre=track(a),tangent=track(a+.002f).sub(centre).normalize();
                centre.addScaledVector(Vector3(tangent.z,0,-tangent.x),(species%2?1.f:-1.f)*(7+random(rng)*28));
                float x=centre.x,z=centre.z;
                Object3D transform; transform.position.set(x, groundHeight(x, z), z); transform.rotation.y = random(rng) * 2 * PI;
                transform.scale.setScalar(1.25f + random(rng) * .9f); transform.updateMatrix();
                trunks->setMatrixAt(i, *transform.matrix); leaves->setMatrixAt(i, *transform.matrix);
                treePositions.push_back(transform.position);
            }
            trunks->instanceMatrix()->needsUpdate(); leaves->instanceMatrix()->needsUpdate(); scene->add(trunks); scene->add(leaves);
        }
        rally::bakeOcclusion(*land,treePositions);rally::bakeOcclusion(*road,treePositions);
        std::vector<rally::Collider> obstacles;
        auto roadsideGrass=rally::dress(*scene,track,nearest,treePositions,&obstacles);
        auto postMat = material(0xf2d6a2), bannerMat = material(0xdb642e), activeMat = material(0x70dfcc);
        activeMat->emissive = Color(0x148577); activeMat->emissiveIntensity = .7f;
        std::vector<std::shared_ptr<Mesh>> banners;
        std::vector<std::shared_ptr<Mesh>> cameraBarriers;
        for (int i = 0; i < 8; ++i) {
            auto p = track(i * 2 * PI / 8); auto ahead = track(i * 2 * PI / 8 + .01f).sub(p);
            if(safariStage)if(const auto y=roadContact->height(p.x,p.z))p.y=*y;
            float yaw = std::atan2(ahead.x, ahead.z); auto gate = Group::create(); gate->position.copy(p); gate->rotation.y = yaw;
            for (int side : {-1, 1}) {
                auto post = Mesh::create(BoxGeometry::create(.16f, 3.7f, .16f), postMat); post->position.set(side * 4.3f, 1.85f, 0); post->castShadow = true; gate->add(post);
                cameraBarriers.push_back(post);
            }
            auto top = Mesh::create(BoxGeometry::create(9.f, .42f, .2f), bannerMat); top->position.y = 3.7f; gate->add(top); banners.push_back(top);
            cameraBarriers.push_back(top);
            auto text=rally::label(i==0?"CINDER / FINISH":("SECTOR 0"+std::to_string(i)),.18f,Color(0x17201b));
            text->position.set(0,3.7f,-.12f);text->rotation.y=PI;gate->add(text);scene->add(gate);
        }
        if(portrait){
            // A flat capture-only inspection court makes all body angles visible
            // without roadside objects. It uses the actual mesh and daylight rig.
            for(const auto& object:scene->children)if(!dynamic_cast<Light*>(object)&&object!=lighting.sky.get()&&object!=lighting.target.get())object->visible=false;
            lighting.sky->visible=false;scene->background=Color(0x303638);scene->fog=FogExp2(Color(0x303638),.012f);
            auto floorMaterial=material(0x8d8171,.92f);floorMaterial->map=assetTexture("gravel_road_diff_1k.jpg",true);floorMaterial->map->repeat.set(250,250);floorMaterial->normalMap=assetTexture("gravel_road_nor_gl_1k.jpg",false);floorMaterial->normalMap->repeat.set(250,250);floorMaterial->normalScale.set(.30f,.30f);
            auto floor=Mesh::create(PlaneGeometry::create(1000,1000),floorMaterial);floor->rotation.x=-PI/2;floor->position.set(0,inspectionFloor,90);floor->receiveShadow=true;scene->add(floor);
        }
        auto applySafariConfiguration=[&](rally::Buggy& vehicle){
            if(safari)vehicle.contactResponse=rally::RideContactResponse::Compliant;
            if(safari&&!(portrait&&portraitShadows=="stock"))vehicle.car->traverseType<Mesh>([](Mesh& mesh){
                for(const auto& mat:mesh.materials())rally::configureSafariReceiverPlaneShadows(*mat);
            });
        };
        auto buggy=safari?rally::makeSafari(assetDir):rally::makeBuggy();applySafariConfiguration(buggy);auto car=buggy.car,body=buggy.body;scene->add(car);
        const auto& dimensions=buggy.dimensions;
        auto& wheelPivots=buggy.pivots;auto& wheelRolls=buggy.rolls;
        // Conform the cheap ambient shadow to the actual surface, not a floating plane.
        auto carShadowGeometry=PlaneGeometry::create(2.7f,3.6f,4,6);carShadowGeometry->rotateX(-PI/2);
        auto carShadow=Mesh::create(carShadowGeometry,rally::shadowMaterial(.20f));carShadow->frustumCulled=false;scene->add(carShadow);
        std::array<std::shared_ptr<Mesh>,4> contactShadows;
        for(auto& shadow:contactShadows){shadow=Mesh::create(PlaneGeometry::create(.48f,.70f),rally::shadowMaterial(.48f));shadow->rotation.x=-PI/2;scene->add(shadow);}
        auto dust=rally::makeDustMesh();scene->add(dust);rally::DustSimulation dustSimulation;
        rally::TyreTrails tyreTrails;scene->add(tyreTrails.mesh);rally::GravelSpray gravelSpray;scene->add(gravelSpray.mesh);
        std::array<rally::WheelContact,4> wheelContacts;
        float maxWheelGap=0,maxPenetration=0,minWheelTravel=1,maxWheelTravel=0,maxDustSpeed=0;
        float minRearGroundClearance=std::numeric_limits<float>::infinity();int rearClearanceSamples=0,minRearClearanceFrame=-1;
        int cameraBlocks=0,cameraInvalid=0,cameraTargetInside=0,cameraHardClamps=0,cameraForecastRejected=0;
        float minCameraBoom=1,cameraBoomFraction=1,cameraForecastFraction=1;bool cameraWasBlocked=false,cameraHardClamped=false;
        Driver driver;
        if(safari||safariStage)driver.position.y=vehicleHeight(driver.position.x,driver.position.z);
        // Diagnostic car orientation only: the same world sun, probe and
        // exposure also illuminate the front quarter in a second still.
        if(portrait&&portraitLight=="front")driver.heading=-2.55f;
        std::unique_ptr<AudioListener> soundListener;
        std::array<std::unique_ptr<Audio>,3> exhaust;
        rally::Powertrain powertrain;
        rally::SafariPowertrain safariPowertrain;
        auto exhaustBand=[&](int i,bool silent){return safari?safariPowertrain.band(i,silent):powertrain.band(i,silent);};
        bool muted=true;
        auto toggleSound=[&]{
            if(captureMode)return;
            try {
                if(!soundListener){
                    soundListener=std::make_unique<AudioListener>();soundListener->setMasterVolume(.75f);
                    const char* names[]={"idle","mid","high"};
                    for(int i=0;i<3;++i){exhaust[i]=std::make_unique<Audio>(*soundListener,assetDir/(std::string(safari?"safari_exhaust_":"cinder_exhaust_")+names[i]+".wav"));exhaust[i]->setLooping(true);exhaust[i]->setVolume(0);exhaust[i]->play();}
                }
                muted=!muted;
            }catch(const std::exception& error){std::cerr<<"[audio] "<<error.what()<<'\n';for(auto& e:exhaust)e.reset();soundListener.reset();muted=true;}
        };
        auto camera = PerspectiveCamera::create(59, canvas.aspect(), .1f, 750);
        bool paused = false, raceStarted=scripted, resetClockRequested=false; float countdown=0; int inputEvents = 0;
        auto snapCamera = [&] { cameras.cut=true; };
        snapCamera();
        auto resetRun=[&](bool start){
            driver.reset();if(safari||safariStage)driver.position.y=vehicleHeight(driver.position.x,driver.position.z);
            dustSimulation.reset();tyreTrails.reset();gravelSpray.reset();powertrain=rally::Powertrain{};safariPowertrain=rally::SafariPowertrain{};
            paused=false;raceStarted=scripted||start;countdown=start&&!scripted?3.f:0.f;resetClockRequested=true;snapCamera();
        };
        auto selectVehicle=[&]{
            const bool restoreSound=!muted;for(auto& audio:exhaust)audio.reset();soundListener.reset();muted=true;
            scene->remove(*car);safari=!safari;buggy=safari?rally::makeSafari(assetDir):rally::makeBuggy();applySafariConfiguration(buggy);car=buggy.car;body=buggy.body;scene->add(car);resetRun(false);
            if(restoreSound)toggleSound();
        };
        EffectComposer::Options options; options.samples = 0; EffectComposer composer(renderer, options);
        composer.addPass(std::make_shared<RenderPass>(*scene, *camera));
        auto bloom = std::make_shared<UnrealBloomPass>(Vector2(960, 600), .14f, .3f, 1.8f); bloom->enabled = false;
        composer.addPass(bloom); composer.addPass(std::make_shared<OutputPass>());
        composer.addPass(std::make_shared<FXAAPass>());
        ImFont* hudFont=nullptr;
        ImguiFunctionalContext ui(canvas, [&] {
            auto& hudStyle=ImGui::GetStyle();hudStyle.WindowRounding=4;hudStyle.WindowPadding=ImVec2(16,16);hudStyle.ItemSpacing=ImVec2(8,10);
            hudStyle.Colors[ImGuiCol_WindowBg]=ImVec4(.05f,.085f,.075f,.96f);hudStyle.Colors[ImGuiCol_Text]=ImVec4(.96f,.94f,.87f,1);
            hudStyle.Colors[ImGuiCol_Button]=ImVec4(.35f,.31f,.16f,1);hudStyle.Colors[ImGuiCol_ButtonHovered]=ImVec4(.53f,.44f,.20f,1);hudStyle.Colors[ImGuiCol_ButtonActive]=ImVec4(.67f,.54f,.22f,1);
            const auto size=canvas.size();
            const auto near=nearest(driver.position);
            const auto gate=track(driver.next*2*PI/8);
            rally::HudState h;
            h.width=static_cast<float>(size.width());h.height=static_cast<float>(size.height());
            h.speed=driver.velocity;h.rpm=powertrain.rpm;h.gear=powertrain.gear;
            h.time=driver.finished?driver.lastLap:driver.elapsed;h.best=driver.best;
            h.progress=driver.finished?1.f:near.a/(2*PI);h.heading=driver.heading;h.x=driver.position.x;h.z=driver.position.z;
            h.nextDistance=Vector2(driver.position.x-gate.x,driver.position.z-gate.z).length();h.next=driver.next;
            h.inspection=portrait;h.scripted=scripted;h.finished=driver.finished;h.muted=muted;h.menu=!raceStarted||paused||driver.finished||wheelInspect||portrait;h.safari=safari;
            rally::drawHud(h,hudFont);
            const auto flags=ImGuiWindowFlags_NoDecoration|ImGuiWindowFlags_NoMove|ImGuiWindowFlags_AlwaysAutoResize|ImGuiWindowFlags_NoSavedSettings|ImGuiWindowFlags_NoBackground;
            ImGui::PushFont(hudFont);
            auto beginPanel=[&](const char* name){ImGui::SetNextWindowPos(ImVec2(48,162),ImGuiCond_Always);ImGui::SetNextWindowSize(ImVec2(416,0));ImGui::Begin(name,nullptr,flags);ImGui::SetWindowFontScale(.8f);};
            auto menuText=[&](const std::string& value,float size=19.f,ImU32 color=IM_COL32(246,244,233,255)){
                auto p=ImGui::GetCursorScreenPos();rally::hudText(ImGui::GetWindowDrawList(),hudFont,p.x,p.y,size,color,value);ImGui::Dummy(ImVec2(384,size+3));
            };
            auto action=[&](const char* name){
                auto p=ImGui::GetCursorScreenPos();ImGui::PushStyleColor(ImGuiCol_Button,ImVec4(0,0,0,0));ImGui::PushStyleColor(ImGuiCol_ButtonHovered,ImVec4(0,0,0,0));ImGui::PushStyleColor(ImGuiCol_ButtonActive,ImVec4(0,0,0,0));ImGui::PushStyleColor(ImGuiCol_Text,ImVec4(0,0,0,0));
                bool clicked=ImGui::Button(name,ImVec2(340,38));bool focus=ImGui::IsItemHovered()||ImGui::IsItemFocused();ImGui::PopStyleColor(4);
                auto* d=ImGui::GetWindowDrawList();ImU32 color=focus?IM_COL32(226,193,116,255):IM_COL32(246,244,233,255);
                rally::hudText(d,hudFont,p.x,p.y+4,21,color,name);d->AddLine(ImVec2(p.x,p.y+36),ImVec2(p.x+340,p.y+36),focus?color:IM_COL32(235,238,225,95),focus?1.5f:.75f);
                if(focus){d->AddLine(ImVec2(p.x+329,p.y+12),ImVec2(p.x+335,p.y+18),color,1.5f);d->AddLine(ImVec2(p.x+335,p.y+18),ImVec2(p.x+329,p.y+24),color,1.5f);}return clicked;
            };
            if(portrait){
                // Inspection sequences keep their native inspection label;
                // interactive panels belong to the playable race view.
            }else if(!raceStarted&&!scripted){
                beginPanel("Race start");menuText("CINDER FOREST",38);menuText("ONE LAP / EIGHT CHECKPOINTS",17);ImGui::Spacing();
                if(action(safari?"VEHICLE: SAFARI COUPE":"VEHICLE: OPEN BUGGY"))selectVehicle();
                menuText("WASD / ARROWS   Drive   SPACE   Handbrake",17);
                menuText("C  Cameras   V  Cockpit   P  Pause   R  Restart",17);ImGui::Spacing();
                if(action("START RUN + SOUND")){if(muted)toggleSound();raceStarted=true;countdown=3;}
                menuText("Or press W to start. M toggles exhaust sound.",15);ImGui::End();
            }else if(paused){
                beginPanel("Pause menu");menuText("RACE PAUSED",38);ImGui::Spacing();
                if(action("RESUME"))paused=false;
                if(action(muted?"EXHAUST SOUND: OFF":"EXHAUST SOUND: ON"))toggleSound();
                if(action("RESTART STAGE"))resetRun(true);
                if(action("BACK TO GRID"))resetRun(false);
                if(action("QUIT"))canvas.close();ImGui::End();
            }else if(driver.finished){
                beginPanel("Stage results");menuText("STAGE COMPLETE",30);menuText(rally::raceTime(driver.lastLap),58);ImGui::Spacing();
                menuText("BEST   "+rally::raceTime(driver.best),17);
                menuText("CHECKPOINTS  8 / 8     CONTACTS  "+std::to_string(driver.contacts),17);ImGui::Spacing();
                if(action("RACE AGAIN"))resetRun(true);if(action("BACK TO GRID"))resetRun(false);ImGui::End();
            }
            if(countdown>0){
                const std::string n=std::to_string(static_cast<int>(std::ceil(countdown)));
                rally::hudText(ImGui::GetForegroundDrawList(),hudFont,size.width()*.5f-25,225,94,IM_COL32(246,244,233,255),n);
            }
            ImGui::PopFont();
        });
        ImGui::StyleColorsDark();ui.setFontScale(1.f);
        hudFont=ImGui::GetIO().Fonts->AddFontFromFileTTF((assetDir/"Rajdhani-SemiBold.ttf").string().c_str(),24);
        if(!hudFont)throw std::runtime_error("Missing licensed rally HUD font");
        canvas.onKeyPressed([&](KeyEvent e) {
            if (e.key == Key::R) resetRun(true);
            if (e.key == Key::C) cameras.cycle();
            if (e.key == Key::V) cameras.toggleCockpit();
            if (e.key == Key::P && raceStarted && countdown<=0 && !driver.finished) paused = !paused;
            if (e.key == Key::M) toggleSound();
            if ((e.key==Key::W||e.key==Key::UP)&&!raceStarted&&!scripted){raceStarted=true;countdown=3;}
            if (e.key == Key::ESCAPE) canvas.close();
            if (e.key == Key::W || e.key == Key::A || e.key == Key::S || e.key == Key::D) { ++inputEvents; std::cout << "[input] driving key received\n"; }
        });
        canvas.onWindowResize([&](WindowSize s) { camera->aspect = s.aspect(); camera->updateProjectionMatrix(); renderer.setSize(s); composer.setSize(s.width(), s.height()); });
        Clock clock; float accumulator = 0, worldTime = 0;
        auto recordRideInput=[&](bool driving,float dt,float acceleration,float lateral){
            if(rideInputs)rideInputs<<frames<<','<<driving<<','<<worldTime<<','<<dt<<','<<driver.position.x<<','<<driver.position.z<<','
                <<driver.heading<<','<<driver.steer*.4f<<','<<acceleration<<','<<lateral<<'\n';
        };
        canvas.animate([&] {
            FrameBudget frameBudget;
            float dt = bounded ? 1.f/30 : std::min(clock.getDelta(), .05f);
            if(!driver.ride.ready)driver.ride.reset(driver.position,driver.heading,vehicleHeight,dimensions,buggy.contactResponse);
            if(resetClockRequested){accumulator=0;resetClockRequested=false;}
            const bool counting=countdown>0;
            if(counting)countdown=std::max(0.f,countdown-dt);
            if (!paused && !driver.finished && raceStarted && !counting) accumulator += dt;
            while (accumulator >= 1.f/120) {
                constexpr float step = 1.f/120; accumulator -= step; worldTime += step;
                auto near = nearest(driver.position);
                const float off = Vector2(driver.position.x-near.p.x, driver.position.z-near.p.z).length();
                float throttle = (canvas.isKeyDown(Key::W) || canvas.isKeyDown(Key::UP)) ? 1.f : 0.f;
                float brake = (canvas.isKeyDown(Key::S) || canvas.isKeyDown(Key::DOWN)) ? 1.f : 0.f;
                float turn = rally::steerInput(canvas.isKeyDown(Key::A)||canvas.isKeyDown(Key::LEFT),canvas.isKeyDown(Key::D)||canvas.isKeyDown(Key::RIGHT));
                bool handbrake = canvas.isKeyDown(Key::SPACE);
                if (scripted) {
                    Vector3 aim = track(near.a + .11f).sub(driver.position);
                    turn = std::clamp(wrap(std::atan2(aim.x, aim.z)-driver.heading) * 1.35f, -1.f, 1.f);
                    // The coupe uses a balanced governor at the same measured
                    // pace, rather than alternating full throttle and lift.
                    if(safari){
                        const auto pedals=rally::safariCruiseCommand(driver.velocity,off>4.2f);
                        throttle=pedals.throttle;brake=pedals.brake;
                    }else{
                        throttle=driver.velocity<18.f?1.f:0;brake=driver.velocity>20.f?.3f:0;
                    }
                }
                driver.throttle=throttle;driver.braking=handbrake?1.f:brake;
                driver.steer += (turn - driver.steer) * (1-std::exp(-7*step));
                driver.previousVelocity=driver.velocity;
                if(safari){
                    float normalLoad=0;for(float load:driver.ride.forces)normalLoad+=std::max(0.f,load);
                    const float weight=(rally::SafariRideState::sprungMass+4*rally::SafariRideState::unsprungMass)*rally::SafariRideState::gravity;
                    rally::safariIntegrateMotion(driver.velocity,driver.yawRate,driver.heading,driver.motion,driver.steer*.4f,
                                                 throttle,brake,handbrake,off>4.2f,normalLoad,weight,step);
                }else{
                    const float drag=off>4.2f?1.25f:.24f;
                    driver.velocity+=(throttle*12-brake*18-driver.velocity*drag-driver.velocity*std::abs(driver.velocity)*.014f-(handbrake?driver.velocity*1.5f:0))*step;
                    driver.velocity=std::clamp(driver.velocity,-6.f,30.f);
                    const float targetYaw=std::tan(driver.steer*.42f)*driver.velocity/2.45f;
                    driver.yawRate+=(targetYaw-driver.yawRate)*(1-std::exp(-7*step));driver.heading+=driver.yawRate*step;
                    const Vector3 desiredMotion(std::sin(driver.heading)*driver.velocity,0,std::cos(driver.heading)*driver.velocity);
                    driver.motion.lerp(desiredMotion,1-std::exp(-(handbrake?1.5f:off>4.2f?3.f:7.f)*step));
                }
                driver.position.x += driver.motion.x * step;
                driver.position.z += driver.motion.z * step;
                driver.position.y = (safari||safariStage)?vehicleHeight(driver.position.x,driver.position.z):groundHeight(driver.position.x,driver.position.z);
                driver.wheelAngle += driver.velocity * step / dimensions.tyreRadius;
                driver.contactCooldown=std::max(0.f,driver.contactCooldown-step);
                auto collide=[&](float px,float pz,float radius){float x=driver.position.x-px,z=driver.position.z-pz,d=x*x+z*z;
                    if(d<radius*radius&&d>.0001f){float inv=radius/std::sqrt(d);driver.position.x=px+x*inv;driver.position.z=pz+z*inv;
                        if(driver.contactCooldown==0){driver.velocity*=-.18f;driver.motion.multiplyScalar(-.15f);++driver.contacts;driver.contactCooldown=.5f;}}
                };
                for(const auto& p:treePositions)collide(p.x,p.z,.55f+(dimensions.halfTrack+dimensions.tyreHalfWidth));
                for(const auto& p:obstacles)collide(p.x,p.z,p.radius+(dimensions.halfTrack+dimensions.tyreHalfWidth));
                recordRideInput(true,step,(driver.velocity-driver.previousVelocity)/step,driver.velocity*driver.yawRate);
                driver.ride.step(driver.position,driver.heading,driver.steer*.4f,(driver.velocity-driver.previousVelocity)/step,driver.velocity*driver.yawRate,step,vehicleHeight);
                auto road=rally::roadPose(driver.position,driver.heading,vehicleHeight,dimensions);
                driver.maxHeave=std::max(driver.maxHeave,std::abs(driver.ride.chassis.y-road.ride));
                driver.maxRoll=std::max(driver.maxRoll,std::abs(driver.ride.roll));
                if (std::abs(driver.velocity) > .5f) driver.running = true;
                if (driver.running) driver.elapsed += step;
                Vector3 gate = track(driver.next * 2 * PI / 8);
                if (driver.running && Vector2(driver.position.x-gate.x, driver.position.z-gate.z).length() < 7) {
                    if (driver.next == 0) { ++driver.laps; driver.lastLap=driver.elapsed; if (driver.best == 0 || driver.elapsed < driver.best) driver.best = driver.elapsed; driver.elapsed = 0; driver.message = 4;driver.finished=true;driver.velocity=0;driver.throttle=0; }
                    driver.next = (driver.next + 1) % 8;
                }
                if(driver.finished){accumulator=0;break;}
                driver.message = std::max(0.f, driver.message-step);
                if (std::abs(driver.position.x) > 235 || std::abs(driver.position.z) > 235) { driver.reset();driver.ride.reset(driver.position,driver.heading,vehicleHeight,dimensions,buggy.contactResponse);snapCamera(); }
            }
            if(!paused&&(!raceStarted||counting||driver.finished)){
                recordRideInput(false,dt,0,0);driver.ride.step(driver.position,driver.heading,driver.steer*.4f,0,0,dt,vehicleHeight);
            }
            driver.heave=driver.ride.chassis.y;driver.pitch=driver.ride.pitch;driver.roll=driver.ride.roll;
            const auto chassisQ=rally::chassisOrientation(driver.heading,driver.pitch,driver.roll);
            const Vector3 chassis=driver.ride.chassis;
            car->position.copy(chassis);car->rotation.y=driver.heading;
            Vector3 forward(std::sin(driver.heading),0,std::cos(driver.heading)),right(std::cos(driver.heading),0,-std::sin(driver.heading));
            body->rotation.x=driver.pitch;body->rotation.z=driver.roll;body->position.y=0;
            // Audit actual low rear vertices through the driven pose. These
            // are sampled packaging measurements, not extra collision forces.
            for(const auto& p:buggy.rearGroundProbes){auto world=p.clone().applyQuaternion(chassisQ).add(chassis);
                float clearance=world.y-vehicleHeight(world.x,world.z);++rearClearanceSamples;
                if(clearance<minRearGroundClearance){minRearGroundClearance=clearance;minRearClearanceFrame=frames;}}
            for(int i=0;i<4;++i){wheelContacts[i]=driver.ride.contact(i,driver.heading,driver.steer*.4f,vehicleHeight);
                wheelPivots[i]->position.copy(wheelContacts[i].local);wheelPivots[i]->rotation.y=rally::steeringAngle(i,driver.steer*.4f,dimensions);
                wheelRolls[i]->rotation.x=driver.wheelAngle;maxWheelGap=std::max(maxWheelGap,std::max(0.f,wheelContacts[i].gap));maxPenetration=std::max(maxPenetration,std::max(0.f,-wheelContacts[i].gap));
                minWheelTravel=std::min(minWheelTravel,wheelContacts[i].local.y);maxWheelTravel=std::max(maxWheelTravel,wheelContacts[i].local.y);}
            rally::updateSuspension(buggy.suspension,wheelContacts,driver.steer*.4f);
            for(int i=0;i<8;++i)banners[i]->setMaterial(i==driver.next?activeMat:bannerMat);
            if(!paused){
                dustSimulation.update(dt);tyreTrails.update(dt);gravelSpray.update(dt,vehicleHeight);
                float slip=std::clamp(std::abs(driver.motion.dot(right))/6.f,0.f,1.f);
                float activity=std::clamp(driver.throttle*.35f+driver.braking*.8f+slip,0.f,1.f);
                bool moving=raceStarted&&!counting&&!driver.finished&&std::abs(driver.velocity)>2;
                for(int i=0;i<4;++i)tyreTrails.contact(i,wheelContacts[i].ground,moving&&std::abs(wheelContacts[i].gap)<.04f&&driver.ride.forces[i]>100,.10f+slip*.22f+driver.braking*.12f,vehicleHeight);
                if(moving&&std::abs(driver.velocity)>4){dustSimulation.distance+=std::abs(driver.velocity)*dt;
                    float spacing=.48f-activity*.16f;
                    while(dustSimulation.distance>=spacing){dustSimulation.distance-=spacing;
                        for(int i=2;i<4;++i)if(std::abs(wheelContacts[i].gap)<.04f&&driver.ride.forces[i]>100){dustSimulation.spawn(wheelContacts[i].ground,forward,right,driver.motion,std::abs(driver.velocity),i%2?1.f:-1.f);
                            if(activity>.12f)gravelSpray.spawn(wheelContacts[i].ground,forward,right,driver.motion,activity);}}}
            }
            for(const auto& p:dustSimulation.particles)if(p.age<p.life)maxDustSpeed=std::max(maxDustSpeed,p.velocity.length());
            auto* shadowVertices=carShadowGeometry->getAttribute<float>("position");
            float wheelLift=0;for(const auto& contact:wheelContacts)wheelLift+=std::max(0.f,contact.gap)*.25f;
            if(safari)carShadow->material()->opacity=.20f*std::exp(-2*wheelLift);
            for(unsigned i=0;i<shadowVertices->count();++i){float x=(static_cast<int>(i%5)-2)*(dimensions.halfTrack*1.8f)/4,z=(static_cast<int>(i/5)-3)*3.6f/6;
                auto point=(safari?chassis:driver.position).clone().addScaledVector(right,x).addScaledVector(forward,z);point.y=vehicleHeight(point.x,point.z)+.012f;shadowVertices->setXYZ(i,point.x,point.y,point.z);}
            shadowVertices->needsUpdate();
            for(int i=0;i<4;++i){auto& shadow=contactShadows[i];auto p=wheelContacts[i].ground;p.y+=.014f;shadow->position.copy(p);shadow->scale.set(dimensions.tyreHalfWidth/.20f,dimensions.tyreRadius/.54f,1);
                float dx=(vehicleHeight(p.x+.15f,p.z)-vehicleHeight(p.x-.15f,p.z))/.30f,dz=(vehicleHeight(p.x,p.z+.15f)-vehicleHeight(p.x,p.z-.15f))/.30f;
                Quaternion align,yaw;align.setFromUnitVectors(Vector3(0,1,0),Vector3(-dx,1,-dz).normalize());yaw.setFromAxisAngle(Vector3(0,1,0),driver.heading+rally::steeringAngle(i,driver.steer*.4f,dimensions));
                Quaternion flat;flat.setFromAxisAngle(Vector3(1,0,0),-PI/2);shadow->quaternion.copy(align).multiply(yaw).multiply(flat);
                shadow->material()->opacity=.48f*std::clamp(1-std::max(0.f,wheelContacts[i].gap)*5,0.f,1.f);
                if(safari){
                    const float lift=std::max(0.f,wheelContacts[i].gap),spread=1+2*std::min(lift,.4f);
                    shadow->scale.set(dimensions.tyreHalfWidth/.20f*.88f*spread,dimensions.tyreRadius/.54f*.42f*spread,1);
                    shadow->material()->opacity=.70f*std::exp(-14*lift);
                }
            }

            roadsideGrass->setTime(worldTime);
            if(safari){
                safariPowertrain.update(driver.velocity,driver.throttle,dt,paused||driver.finished||!raceStarted||counting);
                powertrain.gear=safariPowertrain.gear;powertrain.rpm=safariPowertrain.rpm;powertrain.load=safariPowertrain.load;powertrain.shift=safariPowertrain.shift;
            }else powertrain.update(driver.velocity,driver.throttle,dt,paused||driver.finished||!raceStarted||counting);
            rally::updateCockpit(buggy.cockpit,driver.steer,driver.velocity,powertrain.rpm);
            for(int i=0;i<3;++i)if(exhaust[i]){auto band=exhaustBand(i,muted||paused);exhaust[i]->setPlaybackRate(band.pitch);exhaust[i]->setVolume(band.gain);}
            cameraBoomFraction=1;cameraWasBlocked=false;cameraForecastFraction=1;cameraHardClamped=false;
            if(portrait){
                const bool rearDetail=portraitAngle=="rear-detail",frontDetail=portraitAngle=="front-detail";
                Vector3 offset=rearDetail?Vector3(1.4f,.42f,-4.55f):frontDetail?Vector3(1.4f,.90f,4.55f):portraitAngle=="tail"?Vector3(0,1.2f,-6.8f):portraitAngle=="side"?Vector3(-6.8f,1.6f,.6f):portraitAngle=="rear"?Vector3(4.2f,2.1f,-4.8f):portraitAngle=="top"?Vector3(0,8,.001f):Vector3(4.2f,2.1f,4.8f);
                if(portraitOrbit){
                    // Deterministic native camera travel, without retiming the
                    // simulation or transforming a rendered still afterward.
                    const float t=std::clamp((frames-warmup)/static_cast<float>(std::max(1,limit-1)),0.f,1.f);
                    const float angle=(-10.f+20.f*t)*PI/180,x=offset.x,z=offset.z;
                    offset.x=x*std::cos(angle)+z*std::sin(angle);offset.z=z*std::cos(angle)-x*std::sin(angle);
                }
                camera->position.copy(chassis).addScaledVector(right,offset.x).addScaledVector(forward,offset.z).add(Vector3(0,offset.y,0));camera->up.copy(portraitAngle=="top"?forward:Vector3(0,1,0));
                auto target=chassis.clone().add(Vector3(0,rearDetail?.55f:frontDetail?.92f:portraitAngle=="tail"?.90f:1.0f,0));
                if(rearDetail)target.addScaledVector(forward,-1.9f);
                if(frontDetail)target.addScaledVector(forward,1.75f);
                camera->lookAt(target);camera->nearPlane=.05f;camera->fov=35;
            }else if(wheelInspect){
                const auto center=wheelContacts[3].world;
                camera->position.copy(center).add(Vector3(1.9f,.40f,-.9f).applyQuaternion(chassisQ));camera->up.set(0,1,0);
                camera->lookAt(center.clone().add(Vector3(0,.03f,0)));camera->nearPlane=.05f;camera->fov=42;
            }else if(view==3){
                const auto pose=rally::cockpitPose(chassis,chassisQ,buggy.eye);camera->position.copy(pose.eye);camera->up.copy(pose.up);camera->lookAt(pose.target);
                camera->nearPlane=.055f;camera->fov=74;
            }else{
                camera->up.set(0,1,0);camera->nearPlane=.1f;
                Vector3 desired=driver.position.clone().addScaledVector(forward,view==1?-4.8f:view==2?-3.7f:-6.6f).add(Vector3(0,view==1?2.1f:3.0f,0));
                if(view==2)desired.addScaledVector(right,4.1f);
                if(safari&&view==2){
                    desired=rally::safariSideCameraPosition(driver.position,forward,right,vehicleHeight);
                }
                desired.y=std::max(desired.y,groundHeight(desired.x,desired.z)+1.25f);
                const auto cameraTarget=driver.position.clone().addScaledVector(forward,view==2?0.f:2.8f).add(Vector3(0,1.1f,0));
                if(safari){
                    rally::SafariCameraClearanceReport cameraCheck;
                    const auto cameraVelocity=(!paused&&raceStarted&&!counting&&!driver.finished)?driver.motion:Vector3();
                    camera->position.copy(rally::safariTrackClearCamera(cameraTarget,desired,cameraVelocity,dt,cameras.cut,cameraBarriers,safariCameraTracking,&cameraCheck,.30f,true));
                    cameraBoomFraction=cameraCheck.boomFraction;cameraWasBlocked=cameraCheck.shortened;
                    cameraForecastFraction=cameraCheck.forecastBoomFraction;cameraHardClamped=cameraCheck.hardClamped;
                    cameraBlocks+=cameraCheck.shortened;cameraInvalid+=cameraCheck.invalidInput;
                    cameraTargetInside+=cameraCheck.targetInsideBarrier;minCameraBoom=std::min(minCameraBoom,cameraBoomFraction);
                    cameraHardClamps+=cameraCheck.hardClamped;cameraForecastRejected+=cameraCheck.forecastRejected;
                }else if(cameras.cut)camera->position.copy(desired);else camera->position.lerp(desired,1-std::exp(-5*dt));
                camera->lookAt(cameraTarget);
                camera->fov=(view==2?50.f:59.f)+std::abs(driver.velocity)*.14f;
            }
            cameras.cut=false;camera->updateProjectionMatrix();
            rally::drawDust(*dust,dustSimulation,camera->quaternion);
            lighting.follow(driver.position);
            composer.render(dt); ui.render();
            if(!sequence.empty()&&frames>=warmup){char name[40];std::snprintf(name,sizeof(name),"frame_%05d.png",frames-warmup);
                renderer.writeFramebuffer(std::filesystem::path(sequence)/name);
                frameData<<frames-warmup<<','<<worldTime<<','<<driver.velocity<<','<<view<<','<<powertrain.rpm<<','<<powertrain.load<<','<<powertrain.gear<<','<<powertrain.shift<<','<<driver.finished<<','<<wheelContacts[0].local.y<<','<<wheelContacts[1].local.y<<','<<wheelContacts[2].local.y<<','<<wheelContacts[3].local.y<<','<<dustSimulation.serial<<','<<driver.heave<<','<<driver.pitch<<','<<driver.roll;for(float force:driver.ride.forces)frameData<<','<<force;frameData<<','<<cameraBoomFraction<<','<<cameraWasBlocked<<','<<cameraForecastFraction<<','<<cameraHardClamped;
                for(int i=0;i<3;++i){const auto band=exhaustBand(i,paused);frameData<<','<<band.pitch<<','<<band.gain;}
                for(const auto& contact:wheelContacts)frameData<<','<<contact.gap;frameData<<'\n';}
            ++frames;
            if (bounded && frames >= limit + (sequence.empty()?0:warmup)) {
                if (!shot.empty()) renderer.writeFramebuffer(shot);
                std::cout << "[drive] frames=" << frames << " laps=" << driver.laps << " nextGate=" << driver.next << " speed=" << driver.velocity << '\n'; canvas.close();
            }
        });
        if (!telemetry.empty()) { std::ofstream out(telemetry); out << "{\"vehicle\":\""<<(safari?"safari":"buggy")<<"\",\"rideModel\":\""<<(driver.ride.contactResponse==rally::RideContactResponse::Compliant?"compliant-7dof":driver.ride.contactResponse==rally::RideContactResponse::Projected?"projected":"legacy")<<"\",\"frames\":" << frames << ",\"x\":" << driver.position.x << ",\"z\":" << driver.position.z << ",\"speed\":" << driver.velocity << ",\"laps\":" << driver.laps << ",\"nextGate\":" << driver.next << ",\"contacts\":" << driver.contacts << ",\"maxHeave\":" << driver.maxHeave << ",\"maxRoll\":" << driver.maxRoll << ",\"lastLap\":" << driver.lastLap << ",\"maxWheelGap\":"<<maxWheelGap<<",\"maxPenetration\":"<<maxPenetration<<",\"bumpCorrections\":"<<driver.ride.bumpCorrections<<",\"minWheelTravel\":"<<minWheelTravel<<",\"maxWheelTravel\":"<<maxWheelTravel<<",\"dustEmitted\":"<<dustSimulation.serial<<",\"trailSegments\":"<<tyreTrails.emitted<<",\"gravelEmitted\":"<<gravelSpray.emitted<<",\"maxDustSpeed\":"<<maxDustSpeed
            <<",\"rearClearanceSamples\":"<<rearClearanceSamples<<",\"minRearGroundClearance\":"<<(rearClearanceSamples?minRearGroundClearance:0)<<",\"minRearClearanceFrame\":"<<minRearClearanceFrame<<",\"inputEvents\":" << inputEvents
            <<",\"cameraBlocks\":"<<cameraBlocks<<",\"cameraInvalid\":"<<cameraInvalid<<",\"cameraTargetInside\":"<<cameraTargetInside<<",\"minCameraBoom\":"<<minCameraBoom
            <<",\"cameraHardClamps\":"<<cameraHardClamps<<",\"cameraForecastRejected\":"<<cameraForecastRejected
            <<",\"stageProfile\":\""<<(safariStage?"graded-safari-45mm":"original-rough-170mm")<<"\",\"audioProfile\":\""<<(safari?"safari-deep-v1":"cinder-recorded")<<"\"}"; }
        return 0;
    } catch (std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
