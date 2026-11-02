// CINDER FOREST: an isolated successor to the original driving study.
// Ground-following handling is custom arcade motion, not a PhysX simulation.
#include "FrameBudget.hpp"
#include "RallyDetail.hpp"
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
    bool running = false;
    float message = 0;
    float heave=groundHeight(0,90), heaveVelocity=0, pitch=0, roll=0, yawRate=0, lateral=0, previousVelocity=0;
    float lastLap=0, maxHeave=0, maxRoll=0;
    float contactCooldown=0;
    Vector3 motion;
    void reset() { float oldBest = best; *this = Driver{}; best = oldBest; }
};

int main(int argc, char** argv) {
    try {
        bool scripted = false; int frames = 0, limit = 0, view=0; std::string shot, telemetry;
        for (int i = 1; i < argc; ++i) {
            std::string a = argv[i];
            if (a == "--autodrive") scripted = true;
            else if (a == "--frames" && i + 1 < argc) limit = std::max(1, std::stoi(argv[++i]));
            else if (a == "--shot" && i + 1 < argc) shot = argv[++i];
            else if (a == "--telemetry" && i + 1 < argc) telemetry = argv[++i];
            else if (a == "--view" && i + 1 < argc) view = std::clamp(std::stoi(argv[++i]),0,2);
        }
        const bool bounded = limit > 0;
        auto assetDir=std::filesystem::absolute(argv[0]).parent_path()/"rally-assets";
        TextureLoader textureLoader;
        auto assetTexture=[&](const std::string& name,bool srgb){auto t=textureLoader.load(assetDir/name);
            if(!t)throw std::runtime_error("Missing rally texture: "+name);
            t->colorSpace=srgb?ColorSpace::sRGB:ColorSpace::NoColorSpace;t->wrapS=t->wrapT=TextureWrapping::Repeat;t->anisotropy=2;return t;};
        Canvas canvas(Canvas::Parameters().title("CINDER FOREST | rally candidate").size(960, 600).vsync(true).headless(!shot.empty()));
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
        // Authored vehicle silhouette: exposed wheels, roll cage, nose, cabin,
        // lamps and visible suspension travel. It is not a downloaded car model.
        auto car = Group::create(), body = Group::create(); car->add(body); scene->add(car);
        auto paint = material(0xefbd43, .3f, .35f), frameMat = material(0x18272a, .45f, .7f), tire = material(0x202324), rim = material(0xd1c5a5, .3f, .8f);
        auto part = [&](std::shared_ptr<BufferGeometry> g, std::shared_ptr<Material> m, Vector3 p) {
            auto o = Mesh::create(g, m); o->position.copy(p); o->castShadow = o->receiveShadow = true; body->add(o); return o;
        };
        part(BoxGeometry::create(1.6f, .18f, 2.7f), frameMat, {0, .65f, 0});
        part(BoxGeometry::create(1.5f, .08f, 1.3f), frameMat, {0, 1.98f, -.25f});
        part(BoxGeometry::create(1.8f, .14f, .15f), rim, {0, .58f, 1.65f});
        part(BoxGeometry::create(1.8f, .14f, .15f), frameMat, {0, .6f, -1.6f});
        for (float x : {-.65f, .65f}) for (float z : {-.85f, .4f})
            part(CylinderGeometry::create(.055f, .055f, 1.05f, 8), frameMat, {x, 1.4f, z});
        for (float x : {-.4f, .4f}) part(BoxGeometry::create(.5f, .65f, .4f), frameMat, {x, 1.15f, -.4f});
        auto lightMat = material(0xffecd1); lightMat->emissive = Color(0xffcd7b); lightMat->emissiveIntensity = 1.8f;
        for (float x : {-.5f, .5f}) part(SphereGeometry::create(.15f, 12, 8), lightMat, {x, .95f, 1.65f});
        std::vector<std::shared_ptr<Group>> wheelPivots, wheelRolls;
        for (float z : {1.02f, -1.05f}) for (float x : {-1.0f, 1.0f}) {
            auto pivot = Group::create(), roll = Group::create(); pivot->position.set(x, .49f, z); pivot->add(roll); car->add(pivot);
            auto rubber = Mesh::create(CylinderGeometry::create(.48f, .48f, .38f, 20), tire); rubber->rotation.z = PI/2; rubber->castShadow = true; roll->add(rubber);
            auto hub = Mesh::create(CylinderGeometry::create(.25f, .25f, .4f, 12), rim); hub->rotation.z = PI/2; roll->add(hub);
            wheelPivots.push_back(pivot); wheelRolls.push_back(roll);
        }
        rally::addVehicleDetail(*body,wheelRolls);
        car->traverseType<Mesh>([](Mesh& mesh){mesh.castShadow=true;});
        auto carShadow=Mesh::create(PlaneGeometry::create(3.2f,4.6f),rally::shadowMaterial(.55f));carShadow->rotation.x=-PI/2;scene->add(carShadow);
        auto dustMat = material(0xb79b72); dustMat->transparent = true; dustMat->opacity = .22f; dustMat->depthWrite = false;
        auto dust = InstancedMesh::create(IcosahedronGeometry::create(.22f), dustMat, 48); dust->frustumCulled = false; scene->add(dust);
        std::vector<Vector3> dustPos(48); std::vector<float> dustLife(48, 0); int dustIndex = 0;
        Driver driver;
        std::unique_ptr<AudioListener> soundListener;
        std::unique_ptr<Audio> engineSound;
        bool muted=true;
        auto camera = PerspectiveCamera::create(59, canvas.aspect(), .1f, 750);
        bool paused = false; int inputEvents = 0;
        auto snapCamera = [&] { camera->position.copy(driver.position).add(Vector3(-6.2f, 3.2f, 0)); };
        snapCamera();
        EffectComposer::Options options; options.samples = 0; EffectComposer composer(renderer, options);
        composer.addPass(std::make_shared<RenderPass>(*scene, *camera));
        auto bloom = std::make_shared<UnrealBloomPass>(Vector2(960, 600), .14f, .3f, 1.8f); bloom->enabled = false;
        composer.addPass(bloom); composer.addPass(std::make_shared<OutputPass>());
        composer.addPass(std::make_shared<FXAAPass>());
        ImguiFunctionalContext ui(canvas, [&] {
            const auto size=canvas.size();
            const auto flags=ImGuiWindowFlags_NoDecoration|ImGuiWindowFlags_NoMove|ImGuiWindowFlags_AlwaysAutoResize|ImGuiWindowFlags_NoSavedSettings;
            ImGui::SetNextWindowPos(ImVec2(22,20),ImGuiCond_Always);ImGui::SetNextWindowBgAlpha(.65f);
            ImGui::Begin("Stage",nullptr,flags);
            ImGui::TextColored(ImVec4(.95f,.76f,.35f,1),"CINDER FOREST");
            ImGui::TextDisabled("07 / GRAVEL SPRINT");
            if(scripted)ImGui::TextDisabled("AUTODRIVE CAPTURE");
            ImGui::End();
            ImGui::SetNextWindowPos(ImVec2(size.width()-195.f,20),ImGuiCond_Always);ImGui::SetNextWindowBgAlpha(.65f);
            ImGui::Begin("Timing",nullptr,flags);ImGui::TextDisabled("STAGE TIME");ImGui::SetWindowFontScale(1.6f);
            ImGui::Text("%05.2f",driver.elapsed);ImGui::SetWindowFontScale(1);
            ImGui::Text("SECTOR %d / 8",driver.next==0?8:driver.next);
            if(driver.best>0)ImGui::Text("BEST  %.2f",driver.best);ImGui::End();
            ImGui::SetNextWindowPos(ImVec2(24,size.height()-109.f),ImGuiCond_Always);ImGui::SetNextWindowBgAlpha(.6f);
            ImGui::Begin("Speed",nullptr,flags);ImGui::SetWindowFontScale(2.5f);ImGui::Text("%03.0f",std::abs(driver.velocity)*3.6f);
            ImGui::SetWindowFontScale(1);ImGui::TextDisabled("KM/H   |   %s",driver.velocity<0?"R":driver.velocity<12?"2":"3");ImGui::End();
            ImGui::SetNextWindowPos(ImVec2(size.width()*.5f,size.height()-32.f),ImGuiCond_Always,ImVec2(.5f,0));
            ImGui::SetNextWindowBgAlpha(.65f);ImGui::Begin("Hint",nullptr,flags);
            ImGui::TextDisabled("WASD drive  SPACE handbrake  C camera  R reset  P pause  M sound");ImGui::End();
            if(!driver.running&&!scripted) {
                ImGui::SetNextWindowPos(ImVec2(size.width()*.5f,120),ImGuiCond_Always,ImVec2(.5f,0));
                ImGui::SetNextWindowBgAlpha(.8f);ImGui::Begin("Start",nullptr,flags);
                ImGui::Text("ONE LAP. EIGHT SECTORS.");ImGui::TextDisabled("Follow the green markers. W starts the clock.");ImGui::End();
            }
            if(driver.message>0||paused) {
                ImGui::SetNextWindowPos(ImVec2(size.width()*.5f,130),ImGuiCond_Always,ImVec2(.5f,0));
                ImGui::Begin("Result",nullptr,flags);ImGui::TextColored(ImVec4(.95f,.76f,.35f,1),paused?"PAUSED":"STAGE COMPLETE");
                if(!paused)ImGui::Text("%.2f SECONDS",driver.lastLap);ImGui::End();
            }
        });
        ImGui::StyleColorsDark(); ImGui::GetStyle().WindowRounding = 8; ui.setFontScale(1.f);
        canvas.onKeyPressed([&](KeyEvent e) {
            if (e.key == Key::R) { driver.reset(); snapCamera(); }
            if (e.key == Key::C) view=(view+1)%3;
            if (e.key == Key::P) paused = !paused;
            if (e.key == Key::M && shot.empty()) {
                try {
                    if(!engineSound){soundListener=std::make_unique<AudioListener>();soundListener->setMasterVolume(.35f);
                        engineSound=std::make_unique<Audio>(*soundListener,assetDir/"cinder_engine.wav");engineSound->setLooping(true);}
                    muted=!muted;
                }catch(const std::exception& error){std::cerr<<"[audio] "<<error.what()<<'\n';muted=true;}
            }
            if (e.key == Key::ESCAPE) canvas.close();
            if (e.key == Key::W || e.key == Key::A || e.key == Key::S || e.key == Key::D) { ++inputEvents; std::cout << "[input] driving key received\n"; }
        });
        canvas.onWindowResize([&](WindowSize s) { camera->aspect = s.aspect(); camera->updateProjectionMatrix(); renderer.setSize(s); composer.setSize(s.width(), s.height()); });
        Clock clock; float accumulator = 0, worldTime = 0;
        canvas.animate([&] {
            FrameBudget frameBudget;
            float dt = bounded ? 1.f/30 : std::min(clock.getDelta(), .05f);
            if (!paused) accumulator += dt;
            while (accumulator >= 1.f/120) {
                constexpr float step = 1.f/120; accumulator -= step; worldTime += step;
                auto near = nearest(driver.position);
                const float off = Vector2(driver.position.x-near.p.x, driver.position.z-near.p.z).length();
                float throttle = (canvas.isKeyDown(Key::W) || canvas.isKeyDown(Key::UP)) ? 1.f : 0.f;
                float brake = (canvas.isKeyDown(Key::S) || canvas.isKeyDown(Key::DOWN)) ? 1.f : 0.f;
                float turn = (canvas.isKeyDown(Key::D) || canvas.isKeyDown(Key::RIGHT) ? 1.f : 0.f) - (canvas.isKeyDown(Key::A) || canvas.isKeyDown(Key::LEFT) ? 1.f : 0.f);
                bool handbrake = canvas.isKeyDown(Key::SPACE);
                if (scripted) {
                    Vector3 aim = track(near.a + .11f).sub(driver.position);
                    turn = std::clamp(wrap(std::atan2(aim.x, aim.z)-driver.heading) * 1.35f, -1.f, 1.f);
                    throttle = driver.velocity < 18 ? 1.f : 0; brake = driver.velocity > 20 ? .3f : 0;
                }
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
                float heaveTarget=driver.position.y+.16f;
                driver.heaveVelocity+=((heaveTarget-driver.heave)*90-driver.heaveVelocity*15)*step;
                driver.heave+=driver.heaveVelocity*step;
                driver.maxHeave=std::max(driver.maxHeave,std::abs(driver.heave-heaveTarget));
                Vector3 f(std::sin(driver.heading),0,std::cos(driver.heading)),r(std::cos(driver.heading),0,-std::sin(driver.heading));
                float front=groundHeight(driver.position.x+f.x*1.1f,driver.position.z+f.z*1.1f);
                float rear=groundHeight(driver.position.x-f.x*1.1f,driver.position.z-f.z*1.1f);
                float slope=std::atan2(front-rear,2.2f);
                driver.pitch+=(-slope-driver.pitch)*(1-std::exp(-9*step));
                float lean=-driver.yawRate*driver.velocity*.008f;
                float sideSlope=(groundHeight(driver.position.x+r.x,driver.position.z+r.z)-groundHeight(driver.position.x-r.x,driver.position.z-r.z))*.5f;
                driver.roll+=(std::clamp(sideSlope+lean,-.23f,.23f)-driver.roll)*(1-std::exp(-6*step));
                driver.maxRoll=std::max(driver.maxRoll,std::abs(driver.roll));
                driver.wheelAngle += driver.velocity * step / .48f;
                driver.contactCooldown=std::max(0.f,driver.contactCooldown-step);
                auto collide=[&](float px,float pz,float radius){float x=driver.position.x-px,z=driver.position.z-pz,d=x*x+z*z;
                    if(d<radius*radius&&d>.0001f){float inv=radius/std::sqrt(d);driver.position.x=px+x*inv;driver.position.z=pz+z*inv;
                        if(driver.contactCooldown==0){driver.velocity*=-.18f;driver.motion.multiplyScalar(-.15f);++driver.contacts;driver.contactCooldown=.5f;}}
                };
                for(const auto& p:treePositions)collide(p.x,p.z,1.4f);
                for(const auto& p:obstacles)collide(p.x,p.z,p.radius+.85f);
                if (std::abs(driver.velocity) > .5f) driver.running = true;
                if (driver.running) driver.elapsed += step;
                Vector3 gate = track(driver.next * 2 * PI / 8);
                if (driver.running && Vector2(driver.position.x-gate.x, driver.position.z-gate.z).length() < 7) {
                    if (driver.next == 0) { ++driver.laps; driver.lastLap=driver.elapsed; if (driver.best == 0 || driver.elapsed < driver.best) driver.best = driver.elapsed; driver.elapsed = 0; driver.message = 4; }
                    driver.next = (driver.next + 1) % 8;
                }
                driver.message = std::max(0.f, driver.message-step);
                if (std::abs(driver.position.x) > 235 || std::abs(driver.position.z) > 235) { driver.reset(); snapCamera(); }
            }
            car->position.copy(driver.position);car->position.y=driver.heave; car->rotation.y = driver.heading;
            Vector3 forward(std::sin(driver.heading), 0, std::cos(driver.heading)), right(std::cos(driver.heading), 0, -std::sin(driver.heading));
            body->rotation.x = driver.pitch; body->rotation.z = driver.roll;
            body->position.y = .018f * std::sin(worldTime * (10 + std::abs(driver.velocity))) * std::min(1.f, std::abs(driver.velocity)*.1f);
            for (int i = 0; i < 4; ++i) {
                auto& pivot = wheelPivots[i]; pivot->rotation.y = i < 2 ? driver.steer * .4f : 0;
                Vector3 wp = driver.position.clone().addScaledVector(right, pivot->position.x).addScaledVector(forward, pivot->position.z);
                pivot->position.y = std::clamp(.65f + groundHeight(wp.x, wp.z)-driver.heave,.2f,.9f);
                wheelRolls[i]->rotation.x = driver.wheelAngle;
            }
            for (int i = 0; i < 8; ++i) banners[i]->setMaterial(i == driver.next ? activeMat : bannerMat);
            if (!paused && std::abs(driver.velocity) > 5) { dustPos[dustIndex] = driver.position.clone().addScaledVector(forward, -1.5f); dustLife[dustIndex] = 1; dustIndex = (dustIndex+1)%48; }
            Object3D puff;
            for (int i = 0; i < 48; ++i) {
                if (!paused) dustLife[i] = std::max(0.f, dustLife[i]-dt*.6f);
                puff.position.copy(dustPos[i]); puff.position.y += .3f + (1-dustLife[i])*1.3f;
                puff.scale.setScalar(dustLife[i] > 0 ? .4f+(1-dustLife[i])*2.7f : 0); puff.updateMatrix(); dust->setMatrixAt(i,*puff.matrix);
            }
            dust->instanceMatrix()->needsUpdate();
            carShadow->position.copy(driver.position);carShadow->position.y+=.19f;carShadow->rotation.z=-driver.heading;
            roadsideGrass->setTime(worldTime);
            if(engineSound){float speed=std::abs(driver.velocity);float rev=.35f+.65f*std::fmod(speed,7.f)/7.f;
                engineSound->setPlaybackRate(.7f+rev*1.6f);engineSound->setVolume(muted||paused?0.f:.18f+speed*.003f);
                if(!muted&&!paused&&!engineSound->isPlaying())engineSound->play();}
            Vector3 desired=driver.position.clone().addScaledVector(forward,view==1?-4.8f:view==2?-3.7f:-6.6f).add(Vector3(0,view==1?2.1f:3.0f,0));
            if(view==2)desired.addScaledVector(right,4.1f);
            desired.y=std::max(desired.y,groundHeight(desired.x,desired.z)+1.25f);
            camera->position.lerp(desired,1-std::exp(-5*dt));camera->lookAt(driver.position.clone().addScaledVector(forward,view==2?0.f:2.8f).add(Vector3(0,1.1f,0)));
            camera->fov=(view==2?50.f:59.f)+std::abs(driver.velocity)*.14f;camera->updateProjectionMatrix();
            Vector3 lightAnchor(std::floor(driver.position.x*8)/8,driver.position.y,std::floor(driver.position.z*8)/8);
            sun->position.copy(lightAnchor).add(Vector3(-35,50,-12)); sunTarget->position.copy(lightAnchor);
            composer.render(dt); ui.render();
            ++frames;
            if (bounded && frames >= limit) {
                if (!shot.empty()) renderer.writeFramebuffer(shot);
                std::cout << "[drive] frames=" << frames << " laps=" << driver.laps << " nextGate=" << driver.next << " speed=" << driver.velocity << '\n'; canvas.close();
            }
        });
        if (!telemetry.empty()) { std::ofstream out(telemetry); out << "{\"frames\":" << frames << ",\"x\":" << driver.position.x << ",\"z\":" << driver.position.z << ",\"speed\":" << driver.velocity << ",\"laps\":" << driver.laps << ",\"nextGate\":" << driver.next << ",\"contacts\":" << driver.contacts << ",\"maxHeave\":" << driver.maxHeave << ",\"maxRoll\":" << driver.maxRoll << ",\"lastLap\":" << driver.lastLap << ",\"inputEvents\":" << inputEvents << "}"; }
        return 0;
    } catch (std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
