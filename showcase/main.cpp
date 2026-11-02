// Original evaluation scenes. All meshes and textures are generated locally.
#include "FrameBudget.hpp"
#include "threepp/threepp.hpp"
#include "threepp/extras/environments/RoomEnvironment.hpp"
#include "threepp/extras/imgui/ImguiContext.hpp"
#include "threepp/extras/vegetation/TreeGenerator.hpp"
#include "threepp/objects/Sky.hpp"
#include "threepp/objects/Water.hpp"
#include "threepp/postprocessing/postprocessing.hpp"
#include "threepp/renderers/gl/PMREMGenerator.hpp"
#include "threepp/textures/DataTexture.hpp"
#include "threepp/materials/ShaderMaterial.hpp"
#include "threepp/geometries/TorusKnotGeometry.hpp"
#include "threepp/geometries/IcosahedronGeometry.hpp"

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <iostream>
#include <random>

using namespace threepp;
constexpr float pi = 3.14159265359f;

struct Exhibit {
    std::shared_ptr<Scene> scene = Scene::create();
    std::function<void(float)> update = [](float) {};
    Vector3 eye, target;
};

std::shared_ptr<MeshStandardMaterial> surface(unsigned color, float metal = 0, float rough = .65f) {
    auto m = MeshStandardMaterial::create();
    m->color = Color(color);
    m->metalness = metal;
    m->roughness = rough;
    return m;
}

std::shared_ptr<Mesh> mesh(Exhibit& e, const std::shared_ptr<BufferGeometry>& g,
                           const std::shared_ptr<Material>& m, Vector3 p = {}) {
    auto o = Mesh::create(g, m);
    o->position.copy(p);
    o->castShadow = o->receiveShadow = true;
    e.scene->add(o);
    return o;
}

void sunlight(Exhibit& e, Color color, float intensity, Vector3 position) {
    e.scene->add(HemisphereLight::create(0xcadfff, 0x3e3932, .75f));
    auto sun = DirectionalLight::create(color, intensity);
    sun->position.copy(position);
    sun->castShadow = true;
    sun->shadow->mapSize.set(2048, 2048);
    auto c = sun->shadow->camera->as<OrthographicCamera>();
    c->left = c->bottom = -24;
    c->right = c->top = 24;
    c->nearPlane = 1;
    c->farPlane = 110;
    sun->shadow->bias = -.0004f;
    e.scene->add(sun);
}

Exhibit kinetic(const std::shared_ptr<Texture>& env) {
    Exhibit e;
    e.eye.set(13, 9, 17); e.target.set(-4, 2.3f, 0);
    e.scene->background = Color(0x080e19);
    e.scene->fog = FogExp2(Color(0x080e19), .014f);
    e.scene->environment = env;
    e.scene->environmentIntensity = .95f;
    sunlight(e, Color(0xffdfb1), 2.7f, {8, 18, 9});
    mesh(e, CylinderGeometry::create(7, 7.2f, .6f, 96), surface(0x101d2c, .65f, .26f), {0, -.3f, 0});
    auto floor = mesh(e, PlaneGeometry::create(200, 200), surface(0x0d1420, .3f, .5f), {0, -.62f, 0});
    floor->rotation.x = -pi / 2;
    std::vector<std::shared_ptr<Mesh>> rings;
    const unsigned palette[] = {0xf1bd75, 0x67d1d1, 0xe4edf5};
    for (int i = 0; i < 3; ++i) {
        auto ring = mesh(e, TorusGeometry::create(2.1f + i * .65f, .065f, 16, 160),
                         surface(palette[i], .9f, .16f), {0, 3.3f, 0});
        rings.push_back(ring);
    }
    auto core = mesh(e, TorusKnotGeometry::create(.85f, .27f, 180, 28), surface(0xf5cb87, .96f, .12f), {0, 3.3f, 0});
    auto bars = InstancedMesh::create(BoxGeometry::create(.16f, 1, .16f), surface(0x79bdc8, .75f, .26f), 192);
    bars->instanceMatrix()->setUsage(DrawUsage::Dynamic);
    bars->castShadow = bars->receiveShadow = true;
    e.scene->add(bars);
    auto accent = MeshStandardMaterial::create();
    accent->color = Color(0x1a6874); accent->emissive = Color(0x50c8de); accent->emissiveIntensity = 2.4f;
    auto edge = mesh(e, TorusGeometry::create(6.8f, .025f, 8, 192), accent, {0, .035f, 0});
    edge->rotation.x = pi / 2;
    e.update = [rings, core, bars](float t) {
        for (int i = 0; i < 3; ++i) {
            rings[i]->rotation.set(t * (.12f + .07f * i), t * .16f + i, .4f + i * .7f);
        }
        core->rotation.set(.2f * t, .32f * t, 0);
        Object3D transform;
        for (int i = 0; i < 192; ++i) {
            const float a = i * 2 * pi / 192;
            const float h = .55f + 1.5f * std::pow(.5f + .5f * std::sin(3 * a - t * 1.1f), 2.f);
            transform.position.set(5.1f * std::cos(a), h / 2, 5.1f * std::sin(a));
            transform.rotation.y = -a;
            transform.scale.set(1, h, 1);
            transform.updateMatrix(); bars->setMatrixAt(i, *transform.matrix);
        }
        bars->instanceMatrix()->needsUpdate();
    };
    return e;
}

Exhibit coast() {
    Exhibit e;
    e.eye.set(28, 17, 34); e.target.set(-8, 1, 0);
    sunlight(e, Color(0xffc38b), 2.5f, {-20, 18, -35});
    auto fill = DirectionalLight::create(0xffe6c6, 1.4f);
    fill->position.set(20, 14, 25); e.scene->add(fill);
    auto sky = Sky::create(); sky->scale.setScalar(2000);
    auto& u = sky->materialAs<ShaderMaterial>()->uniforms;
    u.at("turbidity").value<float>() = 4;
    u.at("rayleigh").value<float>() = 2;
    u.at("sunPosition").value<Vector3>().set(-.6f, .12f, -.8f);
    e.scene->add(sky);
    constexpr int n = 128;
    std::vector<unsigned char> pixels(n * n * 4);
    for (int y = 0; y < n; ++y) for (int x = 0; x < n; ++x) {
        const float a = 2 * pi * x / n, b = 2 * pi * y / n;
        Vector3 normal(.32f * std::cos(a * 4 + b * 3), .26f * std::sin(b * 5 - a * 2), 1);
        normal.normalize();
        auto i = 4 * (y * n + x);
        pixels[i] = static_cast<unsigned char>((normal.x * .5f + .5f) * 255);
        pixels[i + 1] = static_cast<unsigned char>((normal.y * .5f + .5f) * 255);
        pixels[i + 2] = static_cast<unsigned char>((normal.z * .5f + .5f) * 255);
        pixels[i + 3] = 255;
    }
    auto normals = DataTexture::create(pixels, n, n);
    normals->wrapS = normals->wrapT = TextureWrapping::Repeat;
    normals->magFilter = normals->minFilter = Filter::Linear;
    Water::Options opt;
    opt.waterNormals = normals; opt.waterColor = 0x12636c; opt.sunColor = 0xffdab3;
    opt.sunDirection = Vector3(-.6f, .12f, -.8f).normalize();
    opt.distortionScale = 2.3f; opt.textureWidth = opt.textureHeight = 256;
    auto water = Water::create(PlaneGeometry::create(2000, 2000), opt);
    water->rotation.x = -pi / 2; e.scene->add(water);
    auto rock = surface(0x777f7c, .05f, .95f);
    std::mt19937 rng(13); std::uniform_real_distribution<float> unit(0, 1);
    for (int i = 0; i < 18; ++i) {
        const float a = 2 * pi * i / 18;
        auto r = mesh(e, IcosahedronGeometry::create(1.6f + unit(rng)), rock,
                      {8 * std::cos(a), -.5f, 5 * std::sin(a)});
        r->scale.set(1.5f, .8f, 1.2f); r->rotation.set(unit(rng), unit(rng), unit(rng));
    }
    mesh(e, CylinderGeometry::create(5.8f, 6.8f, 1.8f, 48), surface(0xa49b85), {0, .2f, 0});
    auto white = surface(0xeee6d3), red = surface(0xa54739), dark = surface(0x233b45, .45f, .3f);
    mesh(e, CylinderGeometry::create(1.05f, 1.5f, 7, 32), white, {1, 4.3f, 0});
    mesh(e, CylinderGeometry::create(1.2f, 1.3f, 1.1f, 32), red, {1, 5.8f, 0});
    mesh(e, CylinderGeometry::create(1.8f, 1.8f, .22f, 32), dark, {1, 7.7f, 0});
    for (int i = 0; i < 6; ++i) {
        const float a = i * pi / 3;
        mesh(e, CylinderGeometry::create(.055f, .055f, 1.3f, 8), dark,
             {1 + 1.05f * std::cos(a), 8.4f, 1.05f * std::sin(a)});
    }
    mesh(e, ConeGeometry::create(1.65f, 1, 32), red, {1, 9.55f, 0});
    auto lamp = surface(0xffda8b); lamp->emissive = Color(0xffc269); lamp->emissiveIntensity = 2.5f;
    mesh(e, SphereGeometry::create(.48f, 20, 16), lamp, {1, 8.5f, 0});
    auto lantern = PointLight::create(0xffc378, 3, 12); lantern->position.set(1, 8.5f, 0); e.scene->add(lantern);
    auto wood = surface(0x8a6650);
    mesh(e, BoxGeometry::create(2, .25f, 12), wood, {-3.5f, 1.2f, 8});
    for (float z : {3.f, 7.f, 12.f}) for (float x : {-4.25f, -2.75f})
        mesh(e, CylinderGeometry::create(.12f, .12f, 3, 8), wood, {x, .2f, z});
    auto boat = Group::create(); e.scene->add(boat);
    auto hull = Mesh::create(SphereGeometry::create(1, 24, 16), red);
    hull->scale.set(.85f, .45f, 2.2f); boat->add(hull);
    auto cabin = Mesh::create(BoxGeometry::create(1.1f, .9f, 1.2f), white);
    cabin->position.set(0, .55f, -.3f); boat->add(cabin);
    e.update = [water, boat](float t) {
        water->materialAs<ShaderMaterial>()->uniforms.at("time").setValue(t * .7f);
        boat->position.set(-.5f, .35f + std::sin(t * 1.3f) * .15f, 11);
        boat->rotation.set(.04f * std::sin(t), .25f, .07f * std::cos(t * 1.3f));
    };
    return e;
}

Exhibit woodland(const std::shared_ptr<Texture>& env) {
    Exhibit e;
    e.eye.set(17, 12, 20); e.target.set(-4, 2, 0);
    e.scene->background = Color(0xcbd7d2);
    e.scene->fog = FogExp2(Color(0xcbd7d2), .006f);
    e.scene->environment = env; e.scene->environmentIntensity = .35f;
    sunlight(e, Color(0xffe0ac), 3.2f, {-12, 24, 4});
    mesh(e, CylinderGeometry::create(8, 7.5f, 1.1f, 96), surface(0x353f3b), {0, -.7f, 0});
    mesh(e, CylinderGeometry::create(8.02f, 8.02f, .15f, 96), surface(0x728663), {0, -.08f, 0});
    auto ground = mesh(e, PlaneGeometry::create(200, 200), surface(0xb1bfb9), {0, -1.28f, 0});
    ground->rotation.x = -pi / 2;
    for (int i = 0; i < 7; ++i) {
        vegetation::TreeParams p; vegetation::applyPreset(i % 3, p); p.seed = 40 + i;
        p.attractorCount = 350;
        vegetation::TreeGenerator gen(p.seed); gen.buildSkeleton(p);
        auto bark = vegetation::makeBarkTextures(128, p.seed, p.barkColor, p.barkStyle);
        auto bm = surface(0xffffff); bm->map = bark.first; bm->normalMap = bark.second; bm->vertexColors = true;
        auto lm = surface(0xffffff, 0, .85f);
        lm->map = p.leafStyle == vegetation::LeafStyle::Frond
            ? vegetation::makeNeedleFrondTexture(128, p.seed, p.leafColor, p.leafAtlasCells)
            : vegetation::makeLeafClusterTexture(128, p.seed, p.leafColor, p.leafShape, 8, p.leafAtlasCells);
        lm->side = Side::Double; lm->alphaTest = vegetation::kLeafAlphaTest; lm->vertexColors = true;
        auto tree = Group::create();
        auto trunk = Mesh::create(gen.makeTrunkGeometry(p), bm), leaves = Mesh::create(gen.makeLeafGeometry(p), lm);
        trunk->castShadow = trunk->receiveShadow = leaves->castShadow = leaves->receiveShadow = true;
        tree->add(trunk); tree->add(leaves);
        const float a = .15f + i * pi / 6;
        tree->position.set(5.1f * std::cos(a), 0, -1.5f - 3.6f * std::sin(a));
        tree->scale.setScalar(.64f + .06f * (i % 3)); e.scene->add(tree);
    }
    auto stone = surface(0xc0b6a1), wood = surface(0x77503c), roof = surface(0x394f50, .3f, .4f);
    mesh(e, BoxGeometry::create(3.3f, .3f, 2.7f), stone, {0, .15f, 1.6f});
    mesh(e, BoxGeometry::create(2.9f, 1.7f, 2.3f), wood, {0, 1.15f, 1.6f});
    for (int s : {-1, 1}) {
        auto panel = mesh(e, BoxGeometry::create(2.05f, .16f, 3.05f), roof, {s * .76f, 2.25f, 1.6f});
        panel->rotation.z = -s * .5f;
    }
    auto glow = surface(0xffd397); glow->emissive = Color(0xffa84a); glow->emissiveIntensity = 1.3f;
    mesh(e, BoxGeometry::create(.72f, .65f, .035f), glow, {.65f, 1.3f, 2.77f});
    mesh(e, BoxGeometry::create(.6f, 1.25f, .04f), roof, {-.65f, .93f, 2.78f});
    for (int i = 0; i < 8; ++i)
        mesh(e, CylinderGeometry::create(.43f, .5f, .12f, 7), stone, {-.65f + .35f * std::sin(static_cast<float>(i)), .04f, 3.2f + i * .48f});
    auto motes = InstancedMesh::create(SphereGeometry::create(.035f, 6, 4), glow, 48); e.scene->add(motes);
    e.update = [motes](float t) {
        Object3D o;
        for (int i = 0; i < 48; ++i) {
            const float a = i * 2.39996f;
            o.position.set(std::cos(a + t * .06f) * (2 + i % 5), 1 + (i % 7) * .3f + std::sin(t + i) * .3f,
                           std::sin(a + t * .06f) * (2 + i % 5));
            o.updateMatrix(); motes->setMatrixAt(i, *o.matrix);
        }
        motes->instanceMatrix()->needsUpdate();
    };
    return e;
}

int main(int argc, char** argv) {
    try {
        int exhibit = 0, frame = 0, frames = 8;
        float t = 4;
        std::string shot;
        for (int i = 1; i < argc; ++i) {
            std::string a = argv[i];
            if (a == "--scene" && i + 1 < argc) exhibit = std::clamp(std::stoi(argv[++i]) - 1, 0, 2);
            else if (a == "--shot" && i + 1 < argc) shot = argv[++i];
            else if (a == "--time" && i + 1 < argc) t = std::stof(argv[++i]);
            else if (a == "--frames" && i + 1 < argc) frames = std::max(1, std::stoi(argv[++i]));
        }
        Canvas canvas(Canvas::Parameters().title("threepp | Engine Playground (30 fps)").size(960, 600).vsync(true).headless(!shot.empty()));
        GLRenderer renderer(canvas);
        renderer.checkShaderErrors = true;
        renderer.toneMapping = ToneMapping::ACESFilmic;
        renderer.shadowMap().enabled = false; renderer.shadowMap().type = ShadowMap::PFC;
        PMREMGenerator pmrem(renderer); RoomEnvironment room;
        auto env = pmrem.fromScene(room, .04f);
        std::vector<Exhibit> scenes;
        scenes.push_back(kinetic(env)); scenes.push_back(coast()); scenes.push_back(woodland(env));
        auto camera = PerspectiveCamera::create(47, canvas.aspect(), .1f, 3000);
        OrbitControls orbit(*camera, canvas); orbit.enableDamping = true; orbit.minDistance = 7; orbit.maxDistance = 85;
        orbit.maxPolarAngle = pi * .48f;
        bool paused = false, autoOrbit = false;
        auto resetCamera = [&] { camera->position.copy(scenes[exhibit].eye); orbit.target.copy(scenes[exhibit].target); orbit.update(); };
        resetCamera();
        std::unique_ptr<EffectComposer> composer;
        std::shared_ptr<UnrealBloomPass> bloom;
        auto rebuild = [&] {
            composer.reset();
            renderer.toneMappingExposure = exhibit == 1 ? .45f : 1.f;
            EffectComposer::Options options; options.samples = 0;
            composer = std::make_unique<EffectComposer>(renderer, options);
            composer->addPass(std::make_shared<RenderPass>(*scenes[exhibit].scene, *camera));
            bloom = std::make_shared<UnrealBloomPass>(Vector2(960, 600), .25f, .4f, 1.5f);
            bloom->enabled = false;
            composer->addPass(bloom); composer->addPass(std::make_shared<OutputPass>());
        };
        rebuild();
        auto change = [&](int index) { if (exhibit != index) { exhibit = index; resetCamera(); rebuild(); } };
        const char* names[] = {"01  /  ORBITAL FOUNDRY", "02  /  TIDAL OUTPOST", "03  /  LITTLE WOODLAND"};
        const char* descriptions[] = {
            "192 moving instances.\nPolished metal and reflections.\nAll geometry generated locally.",
            "Reflective animated water.\nSky and procedural wave normals.\nLighthouse and a bobbing boat.",
            "Seeded procedural trees.\nGenerated bark and leaf textures.\nA cabin and drifting fireflies."
        };
        ImguiFunctionalContext ui(canvas, [&] {
            ImGui::SetNextWindowPos(ImVec2(24, 24), ImGuiCond_Always);
            ImGui::SetNextWindowSize(ImVec2(296, 0));
            ImGui::Begin("Engine Playground", nullptr, ImGuiWindowFlags_NoResize | ImGuiWindowFlags_NoCollapse);
            ImGui::TextDisabled("THREEPP / OPENGL"); ImGui::Spacing();
            for (int i = 0; i < 3; ++i) if (ImGui::Selectable(names[i], exhibit == i, 0, ImVec2(0, 30))) change(i);
            ImGui::Separator(); ImGui::Spacing(); ImGui::TextUnformatted(descriptions[exhibit]); ImGui::Spacing();
            ImGui::Checkbox("Pause motion [Space]", &paused); ImGui::Checkbox("Slow camera orbit", &autoOrbit);
            ImGui::SliderFloat("Exposure", &renderer.toneMappingExposure, .35f, 1.8f, "%.2f");
            ImGui::TextDisabled("Conservative mode: effects reduced");
            if (ImGui::Button("Reset camera [R]", ImVec2(-1, 28))) resetCamera();
            ImGui::Spacing(); ImGui::TextDisabled("Drag: orbit  |  Wheel: zoom\nRight-drag: pan\n1 / 2 / 3: switch scene");
            ImGui::TextDisabled("%.0f fps", ImGui::GetIO().Framerate);
            ImGui::End();
        });
        ImGui::StyleColorsDark(); ImGui::GetStyle().WindowRounding = 8;
        ui.setFontScale(1.f);
        canvas.onKeyPressed([&](KeyEvent ev) {
            if (ImGui::GetIO().WantCaptureKeyboard) return;
            if (ev.key == Key::NUM_1) change(0);
            if (ev.key == Key::NUM_2) change(1);
            if (ev.key == Key::NUM_3) change(2);
            if (ev.key == Key::SPACE) paused = !paused;
            if (ev.key == Key::R) resetCamera();
            if (ev.key == Key::ESCAPE) canvas.close();
        });
        canvas.onWindowResize([&](WindowSize s) {
            camera->aspect = s.aspect(); camera->updateProjectionMatrix(); renderer.setSize(s);
            composer->setSize(s.width(), s.height());
        });
        Clock clock;
        canvas.animate([&] {
            FrameBudget frameBudget;
            float dt = shot.empty() ? std::min(clock.getDelta(), .05f) : 1.f / 60;
            if (!paused) t += dt;
            scenes[exhibit].update(t);
            orbit.autoRotate = autoOrbit; orbit.autoRotateSpeed = .35f;
            orbit.enabled = !ImGui::GetIO().WantCaptureMouse; orbit.update();
            composer->render(dt); ui.render();
            if (!shot.empty() && ++frame >= frames) {
                renderer.writeFramebuffer(shot);
                if (!std::filesystem::exists(shot)) throw std::runtime_error("Could not write capture");
                std::cout << "Captured scene " << exhibit + 1 << ": " << shot << '\n'; canvas.close();
            }
        });
        return 0;
    } catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
