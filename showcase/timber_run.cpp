// TIMBER RUN: an original, bounded arcade driving evaluation. No external art.
// Ground-following handling is custom arcade motion, not a PhysX simulation.
#include "FrameBudget.hpp"
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
#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <random>

using namespace threepp;
constexpr float PI = 3.14159265359f;
float terrain(float x, float z) { return 1.8f * std::sin(x * .035f) + 2.1f * std::sin(z * .029f) + .65f * std::sin((x + z) * .08f); }
Vector3 track(float a) { float x = 64 * std::sin(a) + 8 * std::sin(3 * a), z = 90 * std::cos(a); return {x, terrain(x, z), z}; }
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
    void reset() { float oldBest = best; *this = Driver{}; best = oldBest; }
};

int main(int argc, char** argv) {
    try {
        bool scripted = false; int frames = 0, limit = 0; std::string shot, telemetry;
        for (int i = 1; i < argc; ++i) {
            std::string a = argv[i];
            if (a == "--autodrive") scripted = true;
            else if (a == "--frames" && i + 1 < argc) limit = std::max(1, std::stoi(argv[++i]));
            else if (a == "--shot" && i + 1 < argc) shot = argv[++i];
            else if (a == "--telemetry" && i + 1 < argc) telemetry = argv[++i];
        }
        const bool bounded = limit > 0;
        Canvas canvas(Canvas::Parameters().title("TIMBER RUN | conservative mode, 30 fps").size(960, 600).vsync(true).headless(!shot.empty()));
        GLRenderer renderer(canvas); renderer.checkShaderErrors = true;
        renderer.toneMapping = ToneMapping::ACESFilmic; renderer.toneMappingExposure = .92f;
        renderer.shadowMap().enabled = false; renderer.shadowMap().type = ShadowMap::PFC;
        auto scene = Scene::create(); scene->fog = FogExp2(Color(0xc4c9ad), .0035f);
        PMREMGenerator pmrem(renderer); RoomEnvironment room; scene->environment = pmrem.fromScene(room, .04f); scene->environmentIntensity = .32f;
        auto sky = Sky::create(); sky->scale.setScalar(2500);
        auto& uniforms = sky->materialAs<ShaderMaterial>()->uniforms;
        uniforms.at("turbidity").value<float>() = 4;
        uniforms.at("rayleigh").value<float>() = 1.4f;
        uniforms.at("sunPosition").value<Vector3>().set(-.65f, .32f, -.7f); scene->add(sky);
        scene->add(HemisphereLight::create(0xd8e8f4, 0x566345, 1.25f));
        auto sun = DirectionalLight::create(0xffdfa5, 3.2f); sun->castShadow = true;
        sun->shadow->mapSize.set(2048, 2048); sun->shadow->bias = -.0006f;
        auto shadowCamera = sun->shadow->camera->as<OrthographicCamera>();
        shadowCamera->left = shadowCamera->bottom = -45; shadowCamera->right = shadowCamera->top = 45;
        shadowCamera->nearPlane = 1; shadowCamera->farPlane = 170;
        auto sunTarget = Group::create(); sun->setTarget(*sunTarget);
        scene->add(sun); scene->add(sunTarget);
        auto add = [&](std::shared_ptr<BufferGeometry> geo, std::shared_ptr<Material> mat, Vector3 p) {
            auto m = Mesh::create(geo, mat); m->position.copy(p); m->castShadow = m->receiveShadow = true; scene->add(m); return m;
        };
        auto land = PlaneGeometry::create(520, 520, 160, 160); land->rotateX(-PI / 2);
        auto positions = land->getAttribute<float>("position"); std::vector<float> colors;
        for (unsigned i = 0; i < positions->count(); ++i) {
            float x = positions->getX(i), z = positions->getZ(i); positions->setY(i, terrain(x, z));
            float s = .5f + .5f * std::sin(x * .31f) * std::cos(z * .17f);
            Color c(0x566c3b); c.multiplyScalar(.78f + .3f * s);
            colors.insert(colors.end(), {c.r, c.g, c.b});
        }
        land->setAttribute("color", FloatBufferAttribute::create(colors, 3)); land->computeVertexNormals();
        auto grass = material(0xffffff); grass->vertexColors = true; add(land, grass, {});
        std::vector<CoursePoint> route; std::vector<float> ribbon, roadUv, roadColors; std::vector<unsigned> indices;
        constexpr int across = 8;
        for (int i = 0; i <= 320; ++i) {
            float a = i * 2 * PI / 320;
            Vector3 p = track(a), tangent = track(a + .001f).sub(p).normalize();
            Vector3 side(tangent.z, 0, -tangent.x);
            route.push_back({p, a});
            for (int j = 0; j <= across; ++j) {
                float s = j * 2.f / across - 1;
                float x = p.x + s * 5.5f * side.x, z = p.z + s * 5.5f * side.z;
                ribbon.insert(ribbon.end(), {x, terrain(x, z) + .16f, z});
                roadUv.insert(roadUv.end(), {j * 1.f/across, i * .28f});
                const float rut = .85f + .15f * std::pow(std::abs(s), .5f);
                roadColors.insert(roadColors.end(), {rut, rut, rut});
            }
            if (i < 320) for (int j = 0; j < across; ++j) {
                unsigned b = i * (across+1) + j;
                indices.insert(indices.end(), {b, b + across + 1, b + 1, b + 1, b + across + 1, b + across + 2});
            }
        }
        auto road = BufferGeometry::create(); road->setAttribute("position", FloatBufferAttribute::create(ribbon, 3)); road->setIndex(indices); road->computeVertexNormals();
        road->setAttribute("uv", FloatBufferAttribute::create(roadUv, 2)); road->setAttribute("color", FloatBufferAttribute::create(roadColors, 3));
        std::mt19937 gravelRng(7); std::vector<unsigned char> gravel(128*128*4);
        for (int i = 0; i < 128*128; ++i) {
            const unsigned char value = static_cast<unsigned char>(170 + gravelRng()%80);
            gravel[4*i] = value; gravel[4*i+1] = value; gravel[4*i+2] = value; gravel[4*i+3] = 255;
        }
        auto gravelTex = DataTexture::create(gravel,128,128); gravelTex->wrapS = gravelTex->wrapT = TextureWrapping::Repeat;
        gravelTex->magFilter = gravelTex->minFilter = Filter::Linear;
        auto dirt = material(0x9c8260); dirt->map = gravelTex; dirt->vertexColors = true; dirt->side = Side::Double;
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
            trunks->castShadow = trunks->receiveShadow = leaves->castShadow = leaves->receiveShadow = true;
            for (int i = 0; i < 60; ++i) {
                float x, z;
                float distance;
                do { x = (random(rng) - .5f) * 340; z = (random(rng) - .5f) * 360;
                    auto near = nearest({x, 0, z}); distance = Vector2(x-near.p.x,z-near.p.z).length(); }
                while (distance < 10 || distance > 67);
                Object3D transform; transform.position.set(x, terrain(x, z), z); transform.rotation.y = random(rng) * 2 * PI;
                transform.scale.setScalar(.9f + random(rng) * .9f); transform.updateMatrix();
                trunks->setMatrixAt(i, *transform.matrix); leaves->setMatrixAt(i, *transform.matrix);
                treePositions.push_back(transform.position);
            }
            trunks->instanceMatrix()->needsUpdate(); leaves->instanceMatrix()->needsUpdate(); scene->add(trunks); scene->add(leaves);
        }
        auto postMat = material(0xf2d6a2), bannerMat = material(0xdb642e), activeMat = material(0x70dfcc);
        activeMat->emissive = Color(0x148577); activeMat->emissiveIntensity = .7f;
        std::vector<std::shared_ptr<Mesh>> banners;
        for (int i = 0; i < 8; ++i) {
            auto p = track(i * 2 * PI / 8); auto ahead = track(i * 2 * PI / 8 + .01f).sub(p);
            float yaw = std::atan2(ahead.x, ahead.z); auto gate = Group::create(); gate->position.copy(p); gate->rotation.y = yaw;
            for (int side : {-1, 1}) {
                auto post = Mesh::create(BoxGeometry::create(.25f, 4.4f, .25f), postMat); post->position.set(side * 5.5f, 2.2f, 0); post->castShadow = true; gate->add(post);
            }
            auto top = Mesh::create(BoxGeometry::create(11.5f, .65f, .3f), bannerMat); top->position.y = 4.5f; gate->add(top); banners.push_back(top); scene->add(gate);
        }
        // Authored vehicle silhouette: exposed wheels, roll cage, nose, cabin,
        // lamps and visible suspension travel. It is not a downloaded car model.
        auto car = Group::create(), body = Group::create(); car->add(body); scene->add(car);
        auto paint = material(0xe88632, .3f, .35f), frameMat = material(0x18272a, .45f, .7f), tire = material(0x202324), rim = material(0xd1c5a5, .3f, .8f);
        auto part = [&](std::shared_ptr<BufferGeometry> g, std::shared_ptr<Material> m, Vector3 p) {
            auto o = Mesh::create(g, m); o->position.copy(p); o->castShadow = o->receiveShadow = true; body->add(o); return o;
        };
        part(BoxGeometry::create(1.65f, .4f, 2.8f), paint, {0, .72f, 0});
        auto nose = part(BoxGeometry::create(1.5f, .22f, 1.05f), paint, {0, .98f, 1.1f}); nose->rotation.x = -.12f;
        part(BoxGeometry::create(1.5f, .12f, 1.3f), frameMat, {0, 1.87f, -.25f});
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
        auto dustMat = material(0xb79b72); dustMat->transparent = true; dustMat->opacity = .22f; dustMat->depthWrite = false;
        auto dust = InstancedMesh::create(IcosahedronGeometry::create(.22f), dustMat, 48); dust->frustumCulled = false; scene->add(dust);
        std::vector<Vector3> dustPos(48); std::vector<float> dustLife(48, 0); int dustIndex = 0;
        Driver driver;
        auto camera = PerspectiveCamera::create(58, canvas.aspect(), .1f, 1100);
        bool closeCamera = false, paused = false; int inputEvents = 0;
        auto snapCamera = [&] { camera->position.copy(driver.position).add(Vector3(-9, 5, 1)); };
        snapCamera();
        EffectComposer::Options options; options.samples = 0; EffectComposer composer(renderer, options);
        composer.addPass(std::make_shared<RenderPass>(*scene, *camera));
        auto bloom = std::make_shared<UnrealBloomPass>(Vector2(960, 600), .14f, .3f, 1.8f); bloom->enabled = false;
        composer.addPass(bloom); composer.addPass(std::make_shared<OutputPass>());
        ImguiFunctionalContext ui(canvas, [&] {
            ImGui::SetNextWindowPos(ImVec2(24, 24), ImGuiCond_Always); ImGui::SetNextWindowSize(ImVec2(270, 0));
            ImGui::Begin("TIMBER RUN", nullptr, ImGuiWindowFlags_NoResize | ImGuiWindowFlags_NoCollapse);
            ImGui::TextDisabled("A THREEPP DRIVING STUDY"); ImGui::Spacing();
            ImGui::SetWindowFontScale(1.8f); ImGui::Text("%03.0f", std::abs(driver.velocity) * 3.6f); ImGui::SetWindowFontScale(1); ImGui::SameLine(); ImGui::TextDisabled("km/h");
            ImGui::Separator(); ImGui::Text("TIME        %06.2f", driver.elapsed);
            if (driver.best > 0) ImGui::Text("BEST        %06.2f", driver.best); else ImGui::TextDisabled("BEST        --");
            ImGui::Text("NEXT GATE   %d / 8", driver.next == 0 ? 8 : driver.next);
            ImGui::Text("LAPS        %d", driver.laps); ImGui::Spacing();
            if (driver.message > 0) ImGui::TextColored(ImVec4(.5f, 1, .8f, 1), "LAP COMPLETE");
            ImGui::TextWrapped("Follow the dirt loop through the green gates. The timer starts when you drive.");
            ImGui::Spacing(); ImGui::TextDisabled("W / arrows   Accelerate\nS            Brake / reverse\nA / D        Steer\nSpace        Handbrake\nC            Chase camera\nR            Restart lap\nP            Pause\nEsc          Exit");
            ImGui::Spacing(); if (ImGui::Button("Restart [R]", ImVec2(-1, 26))) { driver.reset(); snapCamera(); }
            if (ImGui::Button(paused ? "Resume [P]" : "Pause [P]", ImVec2(-1, 26))) paused = !paused;
            ImGui::TextDisabled("%s  |  %.0f fps", scripted ? "AUTODRIVE" : "LIVE INPUT", ImGui::GetIO().Framerate);
            ImGui::End();
        });
        ImGui::StyleColorsDark(); ImGui::GetStyle().WindowRounding = 8; ui.setFontScale(1.15f);
        canvas.onKeyPressed([&](KeyEvent e) {
            if (e.key == Key::R) { driver.reset(); snapCamera(); }
            if (e.key == Key::C) closeCamera = !closeCamera;
            if (e.key == Key::P) paused = !paused;
            if (e.key == Key::ESCAPE) canvas.close();
            if (e.key == Key::W || e.key == Key::A || e.key == Key::S || e.key == Key::D) { ++inputEvents; std::cout << "[input] driving key received\n"; }
        });
        canvas.onWindowResize([&](WindowSize s) { camera->aspect = s.aspect(); camera->updateProjectionMatrix(); renderer.setSize(s); composer.setSize(s.width(), s.height()); });
        Clock clock; float accumulator = 0, worldTime = 0;
        canvas.animate([&] {
            FrameBudget frameBudget;
            float dt = bounded ? 1.f/60 : std::min(clock.getDelta(), .05f);
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
                    Vector3 aim = track(near.a + .14f).sub(driver.position);
                    turn = std::clamp(wrap(std::atan2(aim.x, aim.z)-driver.heading) * 2.4f, -1.f, 1.f);
                    throttle = driver.velocity < 18 ? 1.f : 0; brake = driver.velocity > 20 ? .3f : 0;
                }
                driver.steer += (turn - driver.steer) * (1-std::exp(-7*step));
                const float drag = off > 6 ? 1.1f : .24f;
                driver.velocity += (throttle * 12 - brake * 18 - driver.velocity * drag - (handbrake ? driver.velocity * 1.5f : 0)) * step;
                driver.velocity = std::clamp(driver.velocity, -6.f, 30.f);
                driver.heading += driver.steer * driver.velocity * .042f * (handbrake ? 1.8f : 1.f) * step;
                driver.position.x += std::sin(driver.heading) * driver.velocity * step;
                driver.position.z += std::cos(driver.heading) * driver.velocity * step;
                driver.position.y = terrain(driver.position.x, driver.position.z);
                driver.wheelAngle += driver.velocity * step / .48f;
                for (const auto& p : treePositions) {
                    float x = driver.position.x-p.x, z = driver.position.z-p.z, d = x*x+z*z;
                    if (d < 1.9f && d > .0001f) { float inv = 1.4f/std::sqrt(d); driver.position.x = p.x+x*inv; driver.position.z = p.z+z*inv; driver.velocity *= -.18f; ++driver.contacts; }
                }
                if (std::abs(driver.velocity) > .5f) driver.running = true;
                if (driver.running) driver.elapsed += step;
                Vector3 gate = track(driver.next * 2 * PI / 8);
                if (driver.running && Vector2(driver.position.x-gate.x, driver.position.z-gate.z).length() < 7) {
                    if (driver.next == 0) { ++driver.laps; if (driver.best == 0 || driver.elapsed < driver.best) driver.best = driver.elapsed; driver.elapsed = 0; driver.message = 4; }
                    driver.next = (driver.next + 1) % 8;
                }
                driver.message = std::max(0.f, driver.message-step);
                if (std::abs(driver.position.x) > 235 || std::abs(driver.position.z) > 235) { driver.reset(); snapCamera(); }
            }
            car->position.copy(driver.position); car->rotation.y = driver.heading;
            Vector3 forward(std::sin(driver.heading), 0, std::cos(driver.heading)), right(std::cos(driver.heading), 0, -std::sin(driver.heading));
            float pitch = -(terrain(driver.position.x+forward.x, driver.position.z+forward.z)-terrain(driver.position.x-forward.x, driver.position.z-forward.z))*.5f;
            body->rotation.x = pitch; body->rotation.z = -driver.steer * driver.velocity * .0035f;
            body->position.y = .035f * std::sin(worldTime * (10 + std::abs(driver.velocity))) * std::min(1.f, std::abs(driver.velocity)*.1f);
            for (int i = 0; i < 4; ++i) {
                auto& pivot = wheelPivots[i]; pivot->rotation.y = i < 2 ? driver.steer * .4f : 0;
                Vector3 wp = driver.position.clone().addScaledVector(right, pivot->position.x).addScaledVector(forward, pivot->position.z);
                pivot->position.y = .49f + terrain(wp.x, wp.z)-driver.position.y;
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
            float distance = closeCamera ? 6.5f : 10.5f;
            Vector3 desired = driver.position.clone().addScaledVector(forward,-distance).add(Vector3(0,closeCamera ? 3.2f : 5.2f,0));
            desired.y = std::max(desired.y,terrain(desired.x,desired.z)+2);
            camera->position.lerp(desired,1-std::exp(-4*dt)); camera->lookAt(driver.position.clone().addScaledVector(forward,5).add(Vector3(0,1.1f,0)));
            camera->fov = 58 + std::abs(driver.velocity)*.25f; camera->updateProjectionMatrix();
            sun->position.copy(driver.position).add(Vector3(-45,65,-35)); sunTarget->position.copy(driver.position);
            composer.render(dt); ui.render();
            if (bounded && ++frames >= limit) {
                if (!shot.empty()) renderer.writeFramebuffer(shot);
                if (!telemetry.empty()) { std::ofstream out(telemetry); out << "{\"frames\":" << frames << ",\"x\":" << driver.position.x << ",\"z\":" << driver.position.z << ",\"speed\":" << driver.velocity << ",\"laps\":" << driver.laps << ",\"nextGate\":" << driver.next << ",\"contacts\":" << driver.contacts << ",\"inputEvents\":" << inputEvents << "}"; }
                std::cout << "[drive] frames=" << frames << " laps=" << driver.laps << " nextGate=" << driver.next << " speed=" << driver.velocity << '\n'; canvas.close();
            }
        });
        return 0;
    } catch (std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
