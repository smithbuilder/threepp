// CINDER FOREST: an isolated successor to the original driving study.
// Ground-following handling is custom arcade motion, not a PhysX simulation.
#include "FrameBudget.hpp"
#include "RallyDetail.hpp"
#include "RallyHud.hpp"
#include "RallyPowertrain.hpp"
#include "RallyBuggy.hpp"
#include "RallyDust.hpp"
#include "RallyCamera.hpp"
#include "threepp/threepp.hpp"
#include "threepp/extras/environments/RoomEnvironment.hpp"
#include "threepp/extras/imgui/ImguiContext.hpp"
#include "threepp/extras/vegetation/TreeGenerator.hpp"
#include "threepp/geometries/IcosahedronGeometry.hpp"
#include "threepp/objects/Sky.hpp"
#include "threepp/materials/ShaderMaterial.hpp"
#include "threepp/postprocessing/postprocessing.hpp"
#include "threepp/renderers/gl/PMREMGenerator.hpp"
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
#include <array>

using namespace threepp;
constexpr float PI = 3.14159265359f;
float groundHeight(float x, float z) { return rally::height(x,z); }
Vector3 track(float a) { float x = 64 * std::sin(a) + 8 * std::sin(3 * a), z = 90 * std::cos(a); return {x, groundHeight(x, z), z}; }
float wrap(float a) { while (a > PI) a -= 2 * PI; while (a < -PI) a += 2 * PI; return a; }
auto material(unsigned c, float rough = .8f, float metal = 0) {
    auto m = MeshStandardMaterial::create(); m->color = Color(c); m->roughness = rough; m->metalness = metal; return m;
}

struct CoursePoint { Vector3 p; float a; };
struct Driver {
    Vector3 position = track(0);
    float heading = PI / 2, velocity = 0, steer = 0, wheelAngle = 0, elapsed = 0, best = 0;
    int next = 1, laps = 0, contacts = 0;
    bool running = false, finished=false;
    float throttle=0;
    float message = 0;
    float heave=groundHeight(0,90), heaveVelocity=0, pitch=0, roll=0, yawRate=0, lateral=0, previousVelocity=0;
    float lastLap=0, maxHeave=0, maxRoll=0,previousRoad=0;bool suspensionReady=false;
    float contactCooldown=0;
    Vector3 motion;
    void reset() { float oldBest = best; *this = Driver{}; best = oldBest; }
};

int main(int argc, char** argv) {
    try {
        bool scripted = false; int frames = 0, limit = 0, initialView=0, warmup=0; std::string shot, telemetry, sequence;
        for (int i = 1; i < argc; ++i) {
            std::string a = argv[i];
            if (a == "--autodrive") scripted = true;
            else if (a == "--frames" && i + 1 < argc) limit = std::max(1, std::stoi(argv[++i]));
            else if (a == "--shot" && i + 1 < argc) shot = argv[++i];
            else if (a == "--telemetry" && i + 1 < argc) telemetry = argv[++i];
            else if (a == "--view" && i + 1 < argc) initialView = std::clamp(std::stoi(argv[++i]),0,3);
            else if (a == "--sequence" && i + 1 < argc) sequence=argv[++i];
            else if (a == "--warmup" && i + 1 < argc) warmup=std::clamp(std::stoi(argv[++i]),0,900);
        }
        if(!sequence.empty()&&(!shot.empty()||limit<1||limit>900))throw std::runtime_error("Sequence capture requires 1..900 frames and no --shot");
        rally::CameraModes cameras(initialView);int& view=cameras.view;
        const bool captureMode=!shot.empty()||!sequence.empty();
        std::ofstream frameData;
        if(!sequence.empty()){std::filesystem::create_directories(sequence);frameData.open(std::filesystem::path(sequence)/"frame-data.csv");
            if(!frameData)throw std::runtime_error("Cannot write sequence telemetry");frameData<<"frame,simulation_time,speed,view,rpm,load,gear,shift,finished,wheelFL,wheelFR,wheelRL,wheelRR,dustEmitted\n";}
        const bool bounded = limit > 0;
        auto assetDir=std::filesystem::absolute(argv[0]).parent_path()/"rally-assets";
        TextureLoader textureLoader;
        auto assetTexture=[&](const std::string& name,bool srgb){auto t=textureLoader.load(assetDir/name);
            if(!t)throw std::runtime_error("Missing rally texture: "+name);
            t->colorSpace=srgb?ColorSpace::sRGB:ColorSpace::NoColorSpace;t->wrapS=t->wrapT=TextureWrapping::Repeat;t->anisotropy=2;return t;};
        Canvas canvas(Canvas::Parameters().title("CINDER FOREST | rally candidate").size(960, 600).vsync(true).headless(captureMode));
        GLRenderer renderer(canvas); renderer.checkShaderErrors = true;
        renderer.toneMapping = ToneMapping::ACESFilmic; renderer.toneMappingExposure = .85f;
        renderer.shadowMap().enabled = true; renderer.shadowMap().type = ShadowMap::PFC;
        auto scene = Scene::create(); scene->fog = FogExp2(Color(0xb7baa0), .007f);
        PMREMGenerator pmrem(renderer); RoomEnvironment room; scene->environment = pmrem.fromScene(room, .04f); scene->environmentIntensity = .32f;
        auto sky = Sky::create(); sky->scale.setScalar(2500);
        auto& uniforms = sky->materialAs<ShaderMaterial>()->uniforms;
        uniforms.at("turbidity").value<float>() = 6;
        uniforms.at("rayleigh").value<float>() = 1.7f;
        uniforms.at("sunPosition").value<Vector3>().set(-.7f, .22f, -.3f); scene->add(sky);
        scene->add(HemisphereLight::create(0xdde9ed, 0x41472d, .85f));
        auto sun = DirectionalLight::create(0xffd59c, 2.8f); sun->castShadow = true;
        sun->shadow->mapSize.set(512, 512); sun->shadow->bias = -.0008f;
        auto shadowCamera = sun->shadow->camera->as<OrthographicCamera>();
        shadowCamera->left = shadowCamera->bottom = -22; shadowCamera->right = shadowCamera->top = 22;
        shadowCamera->nearPlane = 1; shadowCamera->farPlane = 120;
        auto sunTarget = Group::create(); sun->setTarget(*sunTarget);
        scene->add(sun); scene->add(sunTarget);
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
                ribbon.insert(ribbon.end(), {x, groundHeight(x, z) + .16f, z});
                roadUv.insert(roadUv.end(), {j * 1.f/across, i * .12f});
                const float rut = .8f + .2f * std::pow(std::abs(s), .5f);
                roadColors.insert(roadColors.end(), {rut, rut, rut});
            }
            if (i < 320) for (int j = 0; j < across; ++j) {
                unsigned b = i * (across+1) + j;
                indices.insert(indices.end(), {b, b + across + 1, b + 1, b + 1, b + across + 1, b + across + 2});
            }
        }
        auto road = BufferGeometry::create(); road->setAttribute("position", FloatBufferAttribute::create(ribbon, 3)); road->setIndex(indices); road->computeVertexNormals();
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
        for (int i = 0; i < 8; ++i) {
            auto p = track(i * 2 * PI / 8); auto ahead = track(i * 2 * PI / 8 + .01f).sub(p);
            float yaw = std::atan2(ahead.x, ahead.z); auto gate = Group::create(); gate->position.copy(p); gate->rotation.y = yaw;
            for (int side : {-1, 1}) {
                auto post = Mesh::create(BoxGeometry::create(.16f, 3.7f, .16f), postMat); post->position.set(side * 4.3f, 1.85f, 0); post->castShadow = true; gate->add(post);
            }
            auto top = Mesh::create(BoxGeometry::create(9.f, .42f, .2f), bannerMat); top->position.y = 3.7f; gate->add(top); banners.push_back(top);
            auto text=rally::label(i==0?"CINDER / FINISH":("SECTOR 0"+std::to_string(i)),.18f,Color(0x17201b));
            text->position.set(0,3.7f,-.12f);text->rotation.y=PI;gate->add(text);scene->add(gate);
        }
        auto buggy=rally::makeBuggy();auto car=buggy.car,body=buggy.body;scene->add(car);
        auto& wheelPivots=buggy.pivots;auto& wheelRolls=buggy.rolls;
        auto carShadow=Mesh::create(PlaneGeometry::create(3.9f,4.5f),rally::shadowMaterial(.45f));carShadow->rotation.x=-PI/2;scene->add(carShadow);
        auto dust=rally::makeDustMesh();scene->add(dust);rally::DustSimulation dustSimulation;
        std::array<rally::WheelContact,4> wheelContacts;
        float maxWheelGap=0,minWheelTravel=1,maxWheelTravel=0,maxDustSpeed=0;
        Driver driver;
        std::unique_ptr<AudioListener> soundListener;
        std::array<std::unique_ptr<Audio>,3> exhaust;
        rally::Powertrain powertrain;
        bool muted=true;
        auto toggleSound=[&]{
            if(captureMode)return;
            try {
                if(!soundListener){
                    soundListener=std::make_unique<AudioListener>();soundListener->setMasterVolume(.75f);
                    const char* names[]={"idle","mid","high"};
                    for(int i=0;i<3;++i){exhaust[i]=std::make_unique<Audio>(*soundListener,assetDir/(std::string("cinder_exhaust_")+names[i]+".wav"));exhaust[i]->setLooping(true);exhaust[i]->setVolume(0);exhaust[i]->play();}
                }
                muted=!muted;
            }catch(const std::exception& error){std::cerr<<"[audio] "<<error.what()<<'\n';for(auto& e:exhaust)e.reset();soundListener.reset();muted=true;}
        };
        auto camera = PerspectiveCamera::create(59, canvas.aspect(), .1f, 750);
        bool paused = false, raceStarted=scripted, resetClockRequested=false; float countdown=0; int inputEvents = 0;
        auto snapCamera = [&] { cameras.cut=true; };
        snapCamera();
        auto resetRun=[&](bool start){driver.reset();dustSimulation.reset();powertrain=rally::Powertrain{};paused=false;raceStarted=scripted||start;countdown=start&&!scripted?3.f:0.f;resetClockRequested=true;snapCamera();};
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
            h.scripted=scripted;h.finished=driver.finished;h.muted=muted;h.menu=!raceStarted||paused||driver.finished;
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
            if(!raceStarted&&!scripted){
                beginPanel("Race start");menuText("CINDER FOREST",38);menuText("ONE LAP / EIGHT CHECKPOINTS",17);ImGui::Spacing();
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
        canvas.animate([&] {
            FrameBudget frameBudget;
            float dt = bounded ? 1.f/30 : std::min(clock.getDelta(), .05f);
            if(!driver.suspensionReady){auto road=rally::roadPose(driver.position,driver.heading,groundHeight);driver.heave=driver.previousRoad=road.ride;driver.pitch=road.pitch;driver.roll=road.roll;driver.suspensionReady=true;}
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
                    throttle = driver.velocity < 18 ? 1.f : 0; brake = driver.velocity > 20 ? .3f : 0;
                }
                driver.throttle=throttle;
                driver.steer += (turn - driver.steer) * (1-std::exp(-7*step));
                const float drag = off > 4.2f ? 1.25f : .24f;
                driver.previousVelocity=driver.velocity;
                driver.velocity += (throttle * 12 - brake * 18 - driver.velocity * drag - driver.velocity*std::abs(driver.velocity)*.014f - (handbrake ? driver.velocity * 1.5f : 0)) * step;
                driver.velocity = std::clamp(driver.velocity, -6.f, 30.f);
                float targetYaw=std::tan(driver.steer*.42f)*driver.velocity/2.45f;
                driver.yawRate+=(targetYaw-driver.yawRate)*(1-std::exp(-7*step));
                driver.heading += driver.yawRate*step;
                Vector3 desiredMotion(std::sin(driver.heading)*driver.velocity,0,std::cos(driver.heading)*driver.velocity);
                driver.motion.lerp(desiredMotion,1-std::exp(-(handbrake?1.5f:off>4.2f?3.f:7.f)*step));
                driver.position.x += driver.motion.x * step;
                driver.position.z += driver.motion.z * step;
                driver.position.y = groundHeight(driver.position.x, driver.position.z);
                const auto road=rally::roadPose(driver.position,driver.heading,groundHeight);
                const float heaveTarget=road.ride;
                const float roadVelocity=std::clamp((heaveTarget-driver.previousRoad)/step,-15.f,15.f);driver.previousRoad=heaveTarget;
                driver.heaveVelocity+=((heaveTarget-driver.heave)*90-(driver.heaveVelocity-roadVelocity)*15)*step;
                driver.heave+=driver.heaveVelocity*step;
                driver.heave=std::clamp(driver.heave,heaveTarget-.12f,heaveTarget+.12f);
                driver.maxHeave=std::max(driver.maxHeave,std::abs(driver.heave-heaveTarget));
                driver.pitch+=(road.pitch-driver.pitch)*(1-std::exp(-14*step));
                const float lean=std::clamp(-driver.yawRate*driver.velocity*.004f,-.035f,.035f);
                driver.roll+=(road.roll+lean-driver.roll)*(1-std::exp(-14*step));
                driver.maxRoll=std::max(driver.maxRoll,std::abs(driver.roll));
                driver.wheelAngle += driver.velocity * step / rally::tyreRadius;
                driver.contactCooldown=std::max(0.f,driver.contactCooldown-step);
                auto collide=[&](float px,float pz,float radius){float x=driver.position.x-px,z=driver.position.z-pz,d=x*x+z*z;
                    if(d<radius*radius&&d>.0001f){float inv=radius/std::sqrt(d);driver.position.x=px+x*inv;driver.position.z=pz+z*inv;
                        if(driver.contactCooldown==0){driver.velocity*=-.18f;driver.motion.multiplyScalar(-.15f);++driver.contacts;driver.contactCooldown=.5f;}}
                };
                for(const auto& p:treePositions)collide(p.x,p.z,.55f+rally::obstacleFootprint);
                for(const auto& p:obstacles)collide(p.x,p.z,p.radius+rally::obstacleFootprint);
                if (std::abs(driver.velocity) > .5f) driver.running = true;
                if (driver.running) driver.elapsed += step;
                Vector3 gate = track(driver.next * 2 * PI / 8);
                if (driver.running && Vector2(driver.position.x-gate.x, driver.position.z-gate.z).length() < 7) {
                    if (driver.next == 0) { ++driver.laps; driver.lastLap=driver.elapsed; if (driver.best == 0 || driver.elapsed < driver.best) driver.best = driver.elapsed; driver.elapsed = 0; driver.message = 4;driver.finished=true;driver.velocity=0;driver.throttle=0; }
                    driver.next = (driver.next + 1) % 8;
                }
                if(driver.finished){accumulator=0;break;}
                driver.message = std::max(0.f, driver.message-step);
                if (std::abs(driver.position.x) > 235 || std::abs(driver.position.z) > 235) { driver.reset(); snapCamera(); }
            }
            const auto chassisQ=rally::chassisOrientation(driver.heading,driver.pitch,driver.roll);
            Vector3 chassis(driver.position.x,driver.heave,driver.position.z);
            rally::constrainRide(chassis,chassisQ,driver.steer*.4f,groundHeight);driver.heave=chassis.y;
            car->position.copy(chassis);car->rotation.y=driver.heading;
            Vector3 forward(std::sin(driver.heading),0,std::cos(driver.heading)),right(std::cos(driver.heading),0,-std::sin(driver.heading));
            body->rotation.x=driver.pitch;body->rotation.z=driver.roll;body->position.y=0;
            for(int i=0;i<4;++i){wheelContacts[i]=rally::wheelContact(i,chassis,chassisQ,driver.steer*.4f,groundHeight);
                wheelPivots[i]->position.copy(wheelContacts[i].local);wheelPivots[i]->rotation.y=rally::steeringAngle(i,driver.steer*.4f);
                wheelRolls[i]->rotation.x=driver.wheelAngle;maxWheelGap=std::max(maxWheelGap,std::abs(wheelContacts[i].gap));
                minWheelTravel=std::min(minWheelTravel,wheelContacts[i].local.y);maxWheelTravel=std::max(maxWheelTravel,wheelContacts[i].local.y);}
            rally::updateSuspension(buggy.suspension,wheelContacts,driver.steer*.4f);
            for(int i=0;i<8;++i)banners[i]->setMaterial(i==driver.next?activeMat:bannerMat);
            if(!paused){
                dustSimulation.update(dt);
                if(raceStarted&&!counting&&!driver.finished&&std::abs(driver.velocity)>4){dustSimulation.distance+=std::abs(driver.velocity)*dt;
                    while(dustSimulation.distance>=.65f){dustSimulation.distance-=.65f;
                        for(int i=2;i<4;++i)if(std::abs(wheelContacts[i].gap)<.08f)dustSimulation.spawn(wheelContacts[i].ground,forward,right,driver.motion,std::abs(driver.velocity),i%2?1.f:-1.f);}}
            }
            for(const auto& p:dustSimulation.particles)if(p.age<p.life)maxDustSpeed=std::max(maxDustSpeed,p.velocity.length());
            carShadow->position.copy(driver.position);carShadow->position.y+=.19f;carShadow->rotation.z=-driver.heading;
            roadsideGrass->setTime(worldTime);
            powertrain.update(driver.velocity,driver.throttle,dt,paused||driver.finished||!raceStarted||counting);
            rally::updateCockpit(buggy.cockpit,driver.steer,driver.velocity,powertrain.rpm);
            for(int i=0;i<3;++i)if(exhaust[i]){auto band=powertrain.band(i,muted||paused);exhaust[i]->setPlaybackRate(band.pitch);exhaust[i]->setVolume(band.gain);}
            if(view==3){
                const auto pose=rally::cockpitPose(chassis,chassisQ);camera->position.copy(pose.eye);camera->up.copy(pose.up);camera->lookAt(pose.target);
                camera->nearPlane=.055f;camera->fov=74;
            }else{
                camera->up.set(0,1,0);camera->nearPlane=.1f;
                Vector3 desired=driver.position.clone().addScaledVector(forward,view==1?-4.8f:view==2?-3.7f:-6.6f).add(Vector3(0,view==1?2.1f:3.0f,0));
                if(view==2)desired.addScaledVector(right,4.1f);
                desired.y=std::max(desired.y,groundHeight(desired.x,desired.z)+1.25f);
                if(cameras.cut)camera->position.copy(desired);else camera->position.lerp(desired,1-std::exp(-5*dt));
                camera->lookAt(driver.position.clone().addScaledVector(forward,view==2?0.f:2.8f).add(Vector3(0,1.1f,0)));
                camera->fov=(view==2?50.f:59.f)+std::abs(driver.velocity)*.14f;
            }
            cameras.cut=false;camera->updateProjectionMatrix();
            rally::drawDust(*dust,dustSimulation,camera->quaternion);
            Vector3 lightAnchor(std::floor(driver.position.x*8)/8,driver.position.y,std::floor(driver.position.z*8)/8);
            sun->position.copy(lightAnchor).add(Vector3(-35,50,-12)); sunTarget->position.copy(lightAnchor);
            composer.render(dt); ui.render();
            if(!sequence.empty()&&frames>=warmup){char name[40];std::snprintf(name,sizeof(name),"frame_%05d.png",frames-warmup);
                renderer.writeFramebuffer(std::filesystem::path(sequence)/name);
                frameData<<frames-warmup<<','<<worldTime<<','<<driver.velocity<<','<<view<<','<<powertrain.rpm<<','<<powertrain.load<<','<<powertrain.gear<<','<<powertrain.shift<<','<<driver.finished<<','<<wheelContacts[0].local.y<<','<<wheelContacts[1].local.y<<','<<wheelContacts[2].local.y<<','<<wheelContacts[3].local.y<<','<<dustSimulation.serial<<'\n';}
            ++frames;
            if (bounded && frames >= limit + (sequence.empty()?0:warmup)) {
                if (!shot.empty()) renderer.writeFramebuffer(shot);
                std::cout << "[drive] frames=" << frames << " laps=" << driver.laps << " nextGate=" << driver.next << " speed=" << driver.velocity << '\n'; canvas.close();
            }
        });
        if (!telemetry.empty()) { std::ofstream out(telemetry); out << "{\"frames\":" << frames << ",\"x\":" << driver.position.x << ",\"z\":" << driver.position.z << ",\"speed\":" << driver.velocity << ",\"laps\":" << driver.laps << ",\"nextGate\":" << driver.next << ",\"contacts\":" << driver.contacts << ",\"maxHeave\":" << driver.maxHeave << ",\"maxRoll\":" << driver.maxRoll << ",\"lastLap\":" << driver.lastLap << ",\"maxWheelGap\":"<<maxWheelGap<<",\"minWheelTravel\":"<<minWheelTravel<<",\"maxWheelTravel\":"<<maxWheelTravel<<",\"dustEmitted\":"<<dustSimulation.serial<<",\"maxDustSpeed\":"<<maxDustSpeed << ",\"inputEvents\":" << inputEvents << "}"; }
        return 0;
    } catch (std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
