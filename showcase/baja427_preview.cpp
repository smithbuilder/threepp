// Isolated asset test bench. No changes to the accepted rally vehicles.
#include "FrameBudget.hpp"
#include "threepp/threepp.hpp"
#include "threepp/loaders/GLTFLoader.hpp"
#include "threepp/extras/environments/RoomEnvironment.hpp"
#include "threepp/extras/imgui/ImguiContext.hpp"
#include "threepp/renderers/gl/PMREMGenerator.hpp"
#include "threepp/postprocessing/postprocessing.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>

using namespace threepp;
constexpr float pi = 3.14159265359f;

struct BajaBench {
    Object3D& model;
    std::array<Object3D*,4> steer{}, roll{};
    Object3D* tailgate{};
    std::vector<std::pair<MaterialWithEmissive*,float>> lamps;
    float steering=0, spin=0, tail=0;
    bool lights=true, spares=true;

    explicit BajaBench(Object3D& root):model(root) {
        const std::array<std::string,4> names{"FL","FR","RL","RR"};
        for(int i=0;i<4;++i){
            steer[i]=model.getObjectByName("wheel."+names[i]+".steer");
            roll[i]=model.getObjectByName("wheel."+names[i]+".roll");
            if(!steer[i]||!roll[i])throw std::runtime_error("Missing wheel pivots: "+names[i]);
        }
        tailgate=model.getObjectByName("tailgate.hinge");
        model.traverseType<Mesh>([&](Mesh& mesh){
            mesh.castShadow=mesh.receiveShadow=true;
            for(const auto& material:mesh.materials()){
                if(material->transparent){material->depthWrite=false;mesh.castShadow=false;}
                if(auto* e=dynamic_cast<MaterialWithEmissive*>(material.get());e&&e->emissive.getHex()!=0){
                    if(std::none_of(lamps.begin(),lamps.end(),[&](const auto& p){return p.first==e;}))lamps.emplace_back(e,e->emissiveIntensity);
                }
            }
        });
    }
    void update(){
        for(int i=0;i<4;++i){
            // Tyres turn about their local X axle; steering is a separate Y pivot.
            if(i<2)steer[i]->rotation.y=steering;
            roll[i]->rotation.x=spin;
        }
        if(tailgate)tailgate->rotation.x=-tail*1.45f;
        for(auto& [lamp,intensity]:lamps)lamp->emissiveIntensity=lights?intensity:0;
        for(const char* name:{"spare.L.steer","spare.R.steer","cargo.spare_tiedowns"})if(auto* spare=model.getObjectByName(name))spare->visible=spares;
    }
    void audit(const std::filesystem::path& directory){
        std::filesystem::create_directories(directory);
        Box3 bounds;bounds.setFromObject(model);Vector3 size;bounds.getSize(size);
        if(size.x<2||size.x>3||size.y<1.5f||size.y>2.8f||size.z<4.8f||size.z>5.8f)throw std::runtime_error("Truck scale outside expected metre range");
        unsigned meshes=0,triangles=0;
        model.traverseType<Mesh>([&](Mesh& mesh){
            ++meshes;auto* p=mesh.geometry()->getAttribute<float>("position");
            if(!p)throw std::runtime_error("Missing positions: "+mesh.name);
            for(unsigned j=0;j<p->count();++j)if(!std::isfinite(p->getX(j))||!std::isfinite(p->getY(j))||!std::isfinite(p->getZ(j)))throw std::runtime_error("Non-finite model geometry");
            const auto* index=mesh.geometry()->getIndex();triangles+=(index?index->count():p->count())/3;
        });
        if(!tailgate||lamps.empty()||!model.getObjectByName("rear_axle"))throw std::runtime_error("Missing tailgate, axle or emissive lamps");
        for(const char* name:{"spare.L.steer","spare.R.steer","cargo.spare_tiedowns"})if(!model.getObjectByName(name))throw std::runtime_error(std::string("Missing removable cargo: ")+name);
        std::array<Vector3,4> before;
        model.updateMatrixWorld(true);
        for(int i=0;i<4;++i){
            roll[i]->getWorldPosition(before[i]);
            const Vector3 expected(i%2?1.025f:-1.025f,.4f,i<2?1.59f:-1.59f);
            if(before[i].distanceTo(expected)>1e-5f)throw std::runtime_error("Unexpected wheel placement");
            Box3 wheel;wheel.setFromObject(*roll[i]);Vector3 diameter;wheel.getSize(diameter);
            if(diameter.x<.3f||diameter.x>.45f||diameter.y<.93f||diameter.y>.96f||diameter.z<.93f||diameter.z>.96f)throw std::runtime_error("Tyre dimensions or axle orientation incorrect");
        }
        steering=.35f;spin=1.1f;tail=1;lights=false;update();model.updateMatrixWorld(true);
        for(int i=0;i<4;++i){Vector3 after;roll[i]->getWorldPosition(after);if(after.distanceTo(before[i])>1e-5f)throw std::runtime_error("Wheel roll/steer changed hub centre");}
        for(const auto& [lamp,_]:lamps)if(lamp->emissiveIntensity!=0)throw std::runtime_error("Lamp toggle failed");
        if(std::abs(tailgate->rotation.x+1.45f)>1e-5f)throw std::runtime_error("Tailgate pose failed");
        spares=false;update();for(const char* name:{"spare.L.steer","spare.R.steer","cargo.spare_tiedowns"})if(model.getObjectByName(name)->visible)throw std::runtime_error("Removable cargo toggle failed");
        spares=true;
        steering=spin=tail=0;lights=true;update();
        std::ofstream out(directory/"baja-asset-audit.json");
        out<<"{\n  \"result\":\"PASS\",\n  \"scope\":\"native loader, metre bounds, finite vertices, fixed wheel pivots, tailgate pivot and lamp toggle\",\n  \"meshes\":"<<meshes<<",\n  \"triangles\":"<<triangles<<",\n  \"size\":["<<size.x<<','<<size.y<<','<<size.z<<"]\n}\n";
        if(!out)throw std::runtime_error("Cannot write asset audit");
        std::cout<<"PASS: Baja native asset audit, "<<meshes<<" meshes / "<<triangles<<" triangles\n";
    }
};

int main(int argc,char** argv){
    try{
        std::string shot,auditDir,inspection="default";int frames=1,view=0,pose=1;
        for(int i=1;i<argc;++i){
            const std::string a=argv[i];
            if(a=="--shot"&&i+1<argc)shot=argv[++i];
            else if(a=="--frames"&&i+1<argc)frames=std::clamp(std::stoi(argv[++i]),1,900);
            else if(a=="--view"&&i+1<argc)view=std::clamp(std::stoi(argv[++i]),0,3);
            else if(a=="--scene"&&i+1<argc)pose=std::clamp(std::stoi(argv[++i]),1,3);
            else if(a=="--physics-audit"&&i+1<argc)auditDir=argv[++i];
            else if(a=="--inspect"&&i+1<argc)inspection=argv[++i];
        }
        const auto assetPath=std::filesystem::absolute(argv[0]).parent_path()/"baja427-assets/baja-427.glb";
        auto asset=GLTFLoader{}.load(assetPath);
        if(!asset||!asset->scene)throw std::runtime_error("Cannot load "+assetPath.string());
        BajaBench bench(*asset->scene);
        if(!auditDir.empty()){
            if(!std::getenv("THREEPP_EVALUATION_MODE"))throw std::runtime_error("Asset audit requires its supervisor");
            bench.audit(auditDir);return 0; // No Canvas, renderer, or audio context.
        }
        if(pose==2){bench.steering=.35f;bench.tail=1;bench.lights=false;}
        if(pose==3){bench.spares=false;bench.tail=1;}
        if(inspection!="default"&&(shot.empty()||!std::getenv("THREEPP_EVALUATION_MODE")))throw std::runtime_error("Mechanical inspection is supervised capture only");
        Canvas canvas(Canvas::Parameters().title("Baja 427 | vehicle test bench").size(960,600).vsync(true).headless(!shot.empty()));
        GLRenderer renderer(canvas);renderer.checkShaderErrors=true;
        renderer.toneMapping=ToneMapping::ACESFilmic;renderer.toneMappingExposure=.85f;
        renderer.shadowMap().enabled=true;renderer.shadowMap().type=ShadowMap::PFC;
        auto scene=Scene::create();scene->background=Color(0x25292b);scene->fog=FogExp2(Color(0x25292b),.035f);
        PMREMGenerator pmrem(renderer);RoomEnvironment room;
        scene->environment=pmrem.fromScene(room,.045f);scene->environmentIntensity=.65f;
        scene->add(HemisphereLight::create(0xd9e9ff,0x76654a,.4f));
        auto key=DirectionalLight::create(0xffedcf,2.8f);key->position.set(-4,8,6);key->castShadow=true;
        key->shadow->mapSize.set(512,512);key->shadow->bias=-.00012f;key->shadow->normalBias=.012f;
        auto shadowCamera=key->shadow->camera->as<OrthographicCamera>();
        shadowCamera->left=shadowCamera->bottom=-4;shadowCamera->right=shadowCamera->top=4;
        shadowCamera->nearPlane=.1f;shadowCamera->farPlane=25;shadowCamera->updateProjectionMatrix();
        scene->add(key);
        auto floorMat=MeshStandardMaterial::create();floorMat->color=Color(0x555a59);floorMat->roughness=.96f;
        auto floor=Mesh::create(PlaneGeometry::create(200,200),floorMat);floor->rotation.x=-pi*.5f;floor->receiveShadow=true;scene->add(floor);
        asset->scene->position.y=.07f;scene->add(asset->scene);
        auto camera=PerspectiveCamera::create(42,canvas.aspect(),.05f,220);
        OrbitControls orbit(*camera,canvas);orbit.enableDamping=true;orbit.minDistance=3;orbit.maxDistance=16;orbit.maxPolarAngle=pi*.49f;
        auto cameraView=[&](int v){
            const std::array<Vector3,4> eyes{Vector3(-4.4f,2.8f,5.6f),Vector3(-6.6f,2.25f,0),Vector3(4.4f,2.8f,-5.8f),Vector3(-3.8f,5.1f,-4.7f)};
            camera->position.copy(eyes[v]);orbit.target.set(0,1,0);orbit.update();
        };cameraView(view);
        if(inspection!="default"){
            Vector3 eye,target;bool cutaway=false;
            if(inspection=="hitch"){eye={1.0f,.45f,-4.3f};target={0,.48f,-2.30f};}
            else if(inspection=="front"){eye={-2.0f,.65f,2.75f};target={-.62f,.64f,1.59f};cutaway=true;}
            else if(inspection=="rear"){eye={-2.1f,.55f,-2.8f};target={-.55f,.65f,-1.55f};cutaway=true;}
            else if(inspection=="underside"){eye={-2.6f,-3.3f,-3.6f};target={0,.52f,0};floor->visible=false;orbit.maxPolarAngle=pi*.99f;}
            else throw std::runtime_error("Unknown Baja mechanical view");
            if(cutaway){bench.spares=false;asset->scene->traverseType<Mesh>([](Mesh& m){for(const char* prefix:{"body.","cab.","cargo.","livery.","door.","hood.","mirror.","bed.","tailgate.","interior.","flare."})if(m.name.starts_with(prefix))m.visible=false;if(m.name.starts_with("rear.")&&(m.name.find("emission")!=std::string::npos||m.name.find("recess_black")!=std::string::npos||m.name.find("vermilion")!=std::string::npos))m.visible=false;});bench.steer[inspection=="front"?0:2]->visible=false;}
            camera->position.copy(eye);orbit.target.copy(target);orbit.update();camera->fov=inspection=="underside"?45:40;camera->updateProjectionMatrix();
        }
        EffectComposer::Options options;options.samples=0;EffectComposer composer(renderer,options);
        composer.addPass(std::make_shared<RenderPass>(*scene,*camera));composer.addPass(std::make_shared<OutputPass>());
        bool spin=pose==2,autoOrbit=false,showControls=true;
        ImguiFunctionalContext ui(canvas,[&]{
            if(!shot.empty()&&inspection!="default"){
                auto* d=ImGui::GetBackgroundDrawList();const std::string label="BAJA 427 / "+inspection+" INSPECTION";
                d->AddText(ImGui::GetFont(),20,ImVec2(18,18),IM_COL32(245,241,225,255),label.c_str());
                const char* note=inspection=="front"||inspection=="rear"?"SERVICE CUTAWAY: BODY, CARGO AND NEAR WHEEL HIDDEN":inspection=="underside"?"FLOOR HIDDEN / COMPLETE VEHICLE":"COMPLETE VEHICLE / FRAME-MOUNTED RECEIVER";
                d->AddText(ImVec2(18,44),IM_COL32(245,241,225,255),note);return;
            }
            ImGui::SetNextWindowPos(ImVec2(16,16),ImGuiCond_Always);
            ImGui::SetNextWindowBgAlpha(.87f);
            ImGui::Begin("Baja 427",nullptr,ImGuiWindowFlags_AlwaysAutoResize|ImGuiWindowFlags_NoCollapse);
            ImGui::TextUnformatted("BAJA 427 / FIRST VEHICLE CANDIDATE");
            ImGui::TextDisabled("Original model from your reference");
            if(showControls){
                ImGui::SliderAngle("Steering",&bench.steering,-25,25);
                ImGui::Checkbox("Roll wheels",&spin);ImGui::SameLine();ImGui::Checkbox("Orbit",&autoOrbit);
                ImGui::SliderFloat("Tailgate",&bench.tail,0,1,"%.2f");
                ImGui::Checkbox("Lights",&bench.lights);ImGui::SameLine();ImGui::Checkbox("Bed spares",&bench.spares);
                for(int v=0;v<4;++v){if(v)ImGui::SameLine();const char* labels[]={"Front","Side","Rear","Bed"};if(ImGui::Button(labels[v]))cameraView(v);}
                ImGui::TextDisabled("Drag to orbit | scroll to zoom | H hides controls");
                ImGui::TextDisabled("Asset bench. Driving and suspension physics pending.");
            }
            ImGui::End();
        });
        ImGui::StyleColorsDark();ImGui::GetStyle().WindowRounding=5;
        canvas.onKeyPressed([&](KeyEvent e){
            if(e.key==Key::ESCAPE)canvas.close();
            if(ImGui::GetIO().WantCaptureKeyboard)return;
            if(e.key==Key::H)showControls=!showControls;
            if(e.key==Key::SPACE)spin=!spin;
            if(e.key==Key::L)bench.lights=!bench.lights;
            if(e.key==Key::T)bench.tail=bench.tail>.5f?0:1;
            if(e.key==Key::R)cameraView(view);
        });
        canvas.onWindowResize([&](WindowSize s){camera->aspect=s.aspect();camera->updateProjectionMatrix();renderer.setSize(s);composer.setSize(s.width(),s.height());});
        Clock clock;int frame=0;
        canvas.animate([&]{
            FrameBudget budget;
            const float dt=shot.empty()?std::min(clock.getDelta(),.05f):1.f/30;
            if(spin)bench.spin+=dt*3;
            bench.update();orbit.autoRotate=autoOrbit;orbit.autoRotateSpeed=.35f;
            orbit.enabled=shot.empty()&&!ImGui::GetIO().WantCaptureMouse;orbit.update();
            composer.render(dt);
            if(shot.empty()||inspection!="default")ui.render();
            if(!shot.empty()&&++frame>=frames){renderer.writeFramebuffer(shot);if(!std::filesystem::exists(shot))throw std::runtime_error("Capture missing");canvas.close();}
        });
        std::cout<<"Baja 427 test bench exited cleanly\n";return 0;
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
