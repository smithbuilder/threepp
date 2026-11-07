#include "CatrinaRig.hpp"
#include "FrameBudget.hpp"
#include "threepp/threepp.hpp"
#include "threepp/renderers/gl/PMREMGenerator.hpp"
#include "threepp/extras/environments/RoomEnvironment.hpp"
#include "threepp/postprocessing/postprocessing.hpp"
#include <algorithm>
#include <filesystem>
#include <iostream>
#include <stdexcept>

using namespace threepp;
// Reference-review bench. Same bounded graphics profile as the driving build.
int main(int argc,char** argv){try{
    std::string shot,audit;int frames=1,view=0,pose=1;
    for(int i=1;i<argc;++i){
        const std::string a=argv[i];auto next=[&](){if(i+1>=argc)throw std::runtime_error("Missing review argument");return std::string(argv[++i]);};
        if(a=="--shot")shot=next();else if(a=="--frames")frames=std::clamp(std::stoi(next()),1,900);
        else if(a=="--view")view=std::clamp(std::stoi(next()),0,6);
        else if(a=="--scene")pose=std::clamp(std::stoi(next()),1,3);
        else if(a=="--physics-audit")audit=next();else throw std::runtime_error("Unknown review argument: "+a);
    }
    if(!std::getenv("THREEPP_EVALUATION_MODE"))throw std::runtime_error("Use Run-Evaluation.ps1");
    rally::CatrinaRig bench(std::filesystem::absolute(argv[0]).parent_path()/"catrina-assets/la-catrina.glb");
    if(!audit.empty()){bench.audit(audit);return 0;}
    if(shot.empty())throw std::runtime_error("Review bench requires a bounded still capture");
    const bool frontCorner=pose==3&&view==6,rearLinks=pose==2&&view==6;
    const bool service=(pose==3&&(view==4||view==5))||frontCorner||rearLinks;
    const bool legacyStudio=pose==3&&view==2;
    // Unscored same-camera control for diagnosing trunk shadow artefacts.
    const bool shadowControl=pose==2&&view==0;
    const bool contrastControl=(pose==2&&view==1)||(pose==3&&view==3);
    bench.trunkOpen=pose==2&&view!=4;bench.hoodOpen=pose==3&&!service&&view!=1&&!legacyStudio;
    if(contrastControl)bench.trunkOpen=bench.hoodOpen=false;
    bench.present(service?Vector3(0,.4f,0):Vector3(),Quaternion(),service?std::array<float,4>{-.1109f,-.1109f,-.1109f,-.1109f}:std::array<float,4>{.2891f,.2891f,.2891f,.2891f},0,{});
    if(service)bench.car->traverseType<Mesh>([](Mesh& m){
        for(const char* prefix:{"body.","cab.","trim.","interior."})if(m.name.starts_with(prefix))m.visible=false;
        if(m.parent&&m.parent->name=="body"&&(m.name.starts_with("front.")||m.name.starts_with("rear.")))m.visible=false;
    });
    if(frontCorner)bench.spin[0]->visible=false;
    if(rearLinks){bench.spin[2]->visible=false;bench.spin[3]->visible=false;}
    Canvas canvas(Canvas::Parameters().title("La Catrina | reference review").size(960,600).vsync(true).headless(true));
    GLRenderer renderer(canvas);renderer.checkShaderErrors=true;renderer.toneMapping=ToneMapping::ACESFilmic;renderer.toneMappingExposure=.88f;
    renderer.shadowMap().enabled=!shadowControl;renderer.shadowMap().type=ShadowMap::PFC;
    auto scene=Scene::create();scene->background=Color(0xe1d3c6);scene->fog=FogExp2(Color(0xe1d3c6),.012f);
    PMREMGenerator pmrem(renderer);Scene studio;studio.background=Color(.16f,.18f,.20f);
    auto card=[&](float w,float h,Vector3 p,float radiance){
        auto m=MeshBasicMaterial::create();m->color.setRGB(radiance,radiance,radiance);m->side=Side::Double;
        auto plane=Mesh::create(PlaneGeometry::create(w,h),m);plane->position.copy(p);plane->lookAt(Vector3());studio.add(plane);
    };
    card(1.1f,5.5f,{-1.4f,4.f,0},3.5f);card(5.5f,1.1f,{-3.5f,1.9f,.1f},3.5f);
    card(4.f,1.6f,{3.f,1.6f,4.f},2.5f);card(.45f,2.4f,{3.f,2.6f,-3.5f},2.8f);
    card(20.f,20.f,{.01f,-1.f,0},.30f);
    // Fixed-model comparison retained in scene3/view2. The room probe adds
    // actual reflected shapes to chrome while all scene lights remain fixed.
    if(legacyStudio)scene->environment=pmrem.fromScene(studio,.045f);
    else {RoomEnvironment room;scene->environment=pmrem.fromScene(room,.045f);}
    // Balanced diffuse illumination preserves candy/gold separation. The
    // unscored control retains the lower-probe comparison at identical views.
    scene->environmentIntensity=contrastControl?.25f:.45f;
    scene->add(HemisphereLight::create(0xd9e9ff,0x76654a,.16f));
    auto key=DirectionalLight::create(0xffeddb,1.7f);key->position.set(-4,8,6);key->castShadow=!shadowControl;
    auto fill=DirectionalLight::create(0xdbe8ff,.3f);fill->position.set(5,3,-4);scene->add(fill);
    key->shadow->mapSize.set(512,512);key->shadow->bias=-.00012f;key->shadow->normalBias=.003f;key->shadow->radius=2;
    auto sc=key->shadow->camera->as<OrthographicCamera>();sc->left=sc->bottom=-3;sc->right=sc->top=3;sc->nearPlane=.1f;sc->farPlane=25;sc->updateProjectionMatrix();scene->add(key);
    auto fm=MeshStandardMaterial::create();fm->color=Color(0xd5c3b3);fm->roughness=.96f;
    fm->envMapIntensity=.40f;
    auto floor=Mesh::create(PlaneGeometry::create(200,200),fm);floor->rotation.x=-1.570796327f;floor->receiveShadow=true;scene->add(floor);scene->add(bench.car);
    if(service){auto sm=MeshStandardMaterial::create();sm->color=Color(0x9b3b2c);sm->roughness=.65f;
        for(float x:{-.33f,.33f})for(float z:{-.6f,.6f}){auto stem=Mesh::create(BoxGeometry::create(.045f,.67f,.045f),sm);stem->position.set(x,.335f,z);scene->add(stem);auto base=Mesh::create(BoxGeometry::create(.22f,.025f,.22f),sm);base->position.set(x,.0125f,z);scene->add(base);auto saddle=Mesh::create(BoxGeometry::create(.12f,.04f,.12f),sm);saddle->position.set(x,.67f,z);scene->add(saddle);}}
    const std::array<Vector3,7> eyes{{{-4.5f,2.1f,5.8f},{-7.8f,1.35f,0},{4.5f,2.1f,-5.8f},{-.001f,9.7f,0},{-1.8f,1.15f,4.5f},{-1.85f,1.25f,-4.4f},{-2.4f,1.65f,.5f}}};
    const std::array<Vector3,7> targets{{{0,.67f,0},{0,.67f,0},{0,.67f,0},{0,0,0},{-.35f,.67f,1.90f},{0,.65f,-1.85f},{0,.89f,.05f}}};
    auto camera=PerspectiveCamera::create(view==3?39.f:(view>=4?40.f:31.f),canvas.aspect(),.05f,220);
    camera->position.copy(eyes[view]);if(view==3)camera->up.set(0,0,-1);camera->lookAt(targets[view]);camera->updateProjectionMatrix();
    if(contrastControl&&view==1){camera->position.copy(eyes[0]);camera->lookAt(targets[0]);}
    if(pose==2&&(view==5||shadowControl)){camera->fov=40;camera->position.set(-2.2f,3.2f,-4.3f);camera->lookAt(Vector3(0,.54f,-1.96f));camera->updateProjectionMatrix();}
    if(pose==2&&view==2){camera->position.set(4.5f,3.6f,-5.8f);camera->lookAt(Vector3(0,.68f,-.35f));}
    if(pose==3&&view==0){camera->position.set(-4.5f,3.6f,5.8f);camera->lookAt(Vector3(0,.68f,.35f));}
    if(service){camera->position.set(-2.6f,1.65f,view==4?3.5f:-3.5f);camera->lookAt(Vector3(0,.66f,view==4?1.25f:-1.25f));}
    if(frontCorner){camera->fov=43;camera->position.set(-2.10f,1.10f,2.60f);camera->lookAt(Vector3(-.35f,.78f,1.5113f));camera->updateProjectionMatrix();}
    if(rearLinks){camera->fov=45;camera->position.set(-1.5f,.65f,-2.9f);camera->lookAt(Vector3(-.20f,.50f,-1.30f));camera->updateProjectionMatrix();}
    if(pose==3&&view==1){camera->position.set(7.8f,1.35f,0);camera->lookAt(Vector3(0,.67f,0));}
    if(pose==2&&view==4){camera->position.set(-2.05f,.55f,1.90f);camera->lookAt(Vector3(-.765f,.31f,1.5113f));}
    EffectComposer::Options options;options.samples=0;EffectComposer composer(renderer,options);
    composer.addPass(std::make_shared<RenderPass>(*scene,*camera));composer.addPass(std::make_shared<OutputPass>());composer.addPass(std::make_shared<FXAAPass>());
    int frame=0;canvas.animate([&]{FrameBudget budget;composer.render(1.f/30);if(++frame>=frames){renderer.writeFramebuffer(shot);if(!std::filesystem::exists(shot))throw std::runtime_error("Missing review image");canvas.close();}});
    std::cout<<"La Catrina reference review completed: view "<<view<<", 960x600\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
