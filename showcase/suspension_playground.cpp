#include "FrameBudget.hpp"
#include "PlaygroundAudit.hpp"
#include "RallySafari.hpp"
#include "RallyBaja.hpp"
#include "RallyLighting.hpp"
#include "threepp/extras/environments/RoomEnvironment.hpp"
#include "threepp/extras/imgui/ImguiContext.hpp"
#include "threepp/postprocessing/postprocessing.hpp"
#include <iomanip>
#include <sstream>

using namespace threepp;
int main(int argc,char** argv){try{
    std::string shot,sequence,auditDir,telemetry;int frames=90,warmup=0,view=0,station=0,selected=0;bool automatic=false,arcadeBoost=false,cutaway=false;float playbackScale=1;
    for(int i=1;i<argc;++i){std::string a=argv[i];auto next=[&](){if(i+1>=argc)throw std::runtime_error("Missing argument");return std::string(argv[++i]);};
        if(a=="--shot")shot=next();else if(a=="--sequence")sequence=next();else if(a=="--physics-audit")auditDir=next();else if(a=="--telemetry")telemetry=next();
        else if(a=="--frames")frames=std::clamp(std::stoi(next()),1,900);else if(a=="--warmup")warmup=std::clamp(std::stoi(next()),0,900);
        else if(a=="--scene")station=std::clamp(std::stoi(next())-1,0,static_cast<int>(playground::stations.size())-1);else if(a=="--view")view=std::clamp(std::stoi(next()),0,6);
        else if(a=="--arcade-boost")arcadeBoost=true;else if(a=="--suspension-cutaway")cutaway=true;
        else if(a=="--playback-scale"){playbackScale=std::stof(next());if(playbackScale!=.5f&&playbackScale!=1)throw std::runtime_error("Playback scale must be 0.5 or 1");}
        else if(a=="--vehicle")selected=playground::vehicleIndex(next());else if(a=="--autodrive")automatic=true;
        else throw std::runtime_error("Unknown playground argument: "+a);
    }
    playground::Terrain terrain;
    if(!auditDir.empty()){playground::audit(terrain,auditDir);return 0;} // CPU only, before Canvas or model loading.
    playground::Simulation simulation(terrain);simulation.select(selected,playground::stations[station]);
    auto assets=std::filesystem::absolute(argv[0]).parent_path()/"playground-assets";
    const bool capture=!shot.empty()||!sequence.empty();
    if((cutaway||playbackScale!=1)&&(!capture||!std::getenv("THREEPP_EVALUATION_MODE")))throw std::runtime_error("Diagnostic playback/cutaway requires supervised capture");
    if(cutaway&&(simulation.tune.visualRig!=playground::VisualRig::Baja||(view!=4&&view!=5)))throw std::runtime_error("Cutaway requires a Baja suspension camera");
    Canvas canvas(Canvas::Parameters().title("Off-road playground | Suspension lab").size(960,600).vsync(true).headless(capture));
    GLRenderer renderer(canvas);renderer.checkShaderErrors=true;renderer.toneMapping=ToneMapping::ACESFilmic;renderer.toneMappingExposure=.9f;
    renderer.shadowMap().enabled=true;renderer.shadowMap().type=ShadowMap::PFC;
    auto scene=Scene::create();scene->background=Color(0xaebdc3);scene->fog=FogExp2(Color(0xaebdc3),.0045f);scene->add(rally::daylightSky());
    PMREMGenerator pmrem(renderer);RoomEnvironment room;scene->environment=pmrem.fromScene(room,.045f);scene->environmentIntensity=.5f;
    scene->add(HemisphereLight::create(0xd9edff,0x75634d,1.1f));
    auto sun=DirectionalLight::create(0xffedcf,2.8f);sun->castShadow=true;sun->shadow->mapSize.set(512,512);sun->shadow->bias=-.00015f;sun->shadow->normalBias=.018f;
    auto sc=sun->shadow->camera->as<OrthographicCamera>();sc->left=sc->bottom=-9;sc->right=sc->top=9;sc->nearPlane=.1f;sc->farPlane=55;sc->updateProjectionMatrix();
    auto sunTarget=Group::create();sun->setTarget(*sunTarget);scene->add(sun);scene->add(sunTarget);
    auto geometry=BufferGeometry::create();geometry->setAttribute("position",FloatBufferAttribute::create(terrain.vertices,3));geometry->setIndex(terrain.indices);geometry->computeVertexNormals();
    std::vector<float> colors,uv;colors.reserve(terrain.vertices.size());
    for(size_t i=0;i<terrain.vertices.size();i+=3){float x=terrain.vertices[i],z=terrain.vertices[i+2];
        float distance=100;for(int lane=1;lane<6;++lane)distance=std::min(distance,std::abs(x-playground::Terrain::trailCenter(lane,z)));
        float dirt=(1-playground::smooth(2,4.5f,distance))*playground::window(-18,-5,106,118,z);
        dirt=std::max(dirt,(1-playground::smooth(2,4.5f,std::abs(x+50)))*playground::window(87,94,181,192,z));
        if(x>16&&x<34&&z>130&&z<144)dirt=.85f;
        Color green(0x666a43),brown(0xa79574);green.lerp(brown,dirt);float noise=.91f+.07f*std::sin(x*5.7f+z*8.1f)*std::sin(z*3.9f-x*7.3f);
        colors.insert(colors.end(),{green.r*noise,green.g*noise,green.b*noise});uv.insert(uv.end(),{x*.3f,z*.3f});}
    geometry->setAttribute("color",FloatBufferAttribute::create(colors,3));geometry->setAttribute("uv",FloatBufferAttribute::create(uv,2));
    auto groundMat=MeshStandardMaterial::create();groundMat->vertexColors=true;groundMat->roughness=.97f;
    TextureLoader textureLoader;
    auto texture=[&](const char* name,bool color){auto t=textureLoader.load(assets/name);t->wrapS=t->wrapT=TextureWrapping::Repeat;if(color)t->colorSpace=ColorSpace::sRGB;return t;};
    groundMat->map=texture("gravel-basecolor.jpg",true);groundMat->normalMap=texture("gravel-normal.jpg",false);groundMat->normalScale.set(.45f,.45f);groundMat->roughnessMap=texture("gravel-roughness.jpg",false);
    auto land=Mesh::create(geometry,groundMat);land->receiveShadow=true;scene->add(land);
    auto gantryMat=MeshStandardMaterial::create();gantryMat->color=Color(0x62777b);gantryMat->metalness=.5f;gantryMat->roughness=.55f;
    for(const auto& b:playground::windFrame){auto beam=Mesh::create(BoxGeometry::create(b[3]*2,b[4]*2,b[5]*2),gantryMat);beam->position.set(b[0],b[1],b[2]);beam->castShadow=beam->receiveShadow=true;scene->add(beam);}
    auto windVisuals=Group::create();std::vector<std::shared_ptr<ArrowHelper>> windArrows;
    for(int i=0;i<15;++i){auto a=ArrowHelper::create(Vector3(1,0,0),Vector3(),1.7f,0xe3c55e,.32f,.14f);windVisuals->add(a);windArrows.push_back(a);}scene->add(windVisuals);
    // Only the selected model is resident. A growing vehicle catalogue must
    // not require loading every GLB and texture before entering the world.
    std::unique_ptr<rally::Buggy> activeCar;std::unique_ptr<rally::BajaRace> activeBaja;
    std::shared_ptr<Group> activeRoot;int presented=-1;bool cutawayApplied=false;
    std::vector<std::pair<Material*,float>> cabinGlazing;
    auto camera=PerspectiveCamera::create(48,canvas.aspect(),.05f,450);
    EffectComposer::Options options;options.samples=0;EffectComposer composer(renderer,options);
    composer.addPass(std::make_shared<RenderPass>(*scene,*camera));composer.addPass(std::make_shared<OutputPass>());composer.addPass(std::make_shared<FXAAPass>());
    bool paused=false,slow=false,diagnostics=true,freeCamera=false,showControls=!capture,holdBrakes=playground::stations[station].kind==playground::TrialKind::Wind,gusts=false;
    float windSpeed=holdBrakes?20.f:0.f;int windDirection=0;
    float targetSpeed=playground::stations[station].defaultSpeed;double accumulator=0;int frame=0;float simulated=0;
    Vector3 cameraPos;bool cameraReady=false;OrbitControls orbit(*camera,canvas);orbit.enabled=false;orbit.maxDistance=55;orbit.minDistance=2;
    auto respawn=[&](){simulation.select(selected,playground::stations[station]);targetSpeed=playground::stations[station].defaultSpeed;holdBrakes=playground::stations[station].kind==playground::TrialKind::Wind;windSpeed=holdBrakes?20.f:0.f;accumulator=0;cameraReady=false;};
    auto drawText=[&](const char* text){ImGui::TextUnformatted(text);};
    ImguiFunctionalContext ui(canvas,[&]{
        ImGui::SetNextWindowPos(ImVec2(18,15),ImGuiCond_Always);ImGui::SetNextWindowBgAlpha(.70f);
        ImGui::Begin("Off-road playground",nullptr,ImGuiWindowFlags_AlwaysAutoResize|ImGuiWindowFlags_NoTitleBar|ImGuiWindowFlags_NoCollapse);
        drawText("OFF-ROAD / SUSPENSION PLAYGROUND");
        if(!showControls){
            const char* names[]={"Chase","Side / jump","Front","Overview","Front suspension","Rear suspension","Driver's eye"};
            ImGui::Text("%s  /  %s",simulation.tune.name,names[view]);
            ImGui::Text("%.0f km/h  |  %d tyres supporting  |  %s",simulation.velocity().length()*3.6f,simulation.contactCount(),playbackScale==.5f?"HALF SPEED":"REAL TIME");
            if(cutaway)ImGui::TextColored(ImVec4(1,.8f,.38f,1),"SERVICE CUTAWAY / body, cargo, near wheel hidden");
            if(arcadeBoost)ImGui::TextColored(ImVec4(1,.8f,.38f,1),"BOOST %s  |  charge %.0f%%",simulation.boost.active?"ACTIVE":simulation.contactCount()==0?"AIRBORNE / OFF":"READY",simulation.boost.charge*100);
            if(capture){ImGui::TextDisabled("Coupled physics / audio rebuilt for film");
                if(view==4||view==5){ImGui::Separator();for(int i=0;i<4;++i){if(i)ImGui::SameLine();ImGui::Text("%s %3.0fmm",std::array<const char*,4>{"FL","FR","RL","RR"}[i],1000*(simulation.travel[i]-simulation.tune.dims.droop));}}}
            else ImGui::TextDisabled("H shows controls");ImGui::End();return;}
        std::array<const char*,playground::tunes.size()> names;for(size_t i=0;i<names.size();++i)names[i]=playground::tunes[i].name;
        ImGui::SetNextItemWidth(180);if(ImGui::Combo("Vehicle",&selected,names.data(),static_cast<int>(names.size())))respawn();
        std::array<const char*,playground::stations.size()> stationNames;for(size_t i=0;i<stationNames.size();++i)stationNames[i]=playground::stations[i].name;
        ImGui::SetNextItemWidth(180);if(ImGui::Combo("Trail",&station,stationNames.data(),static_cast<int>(stationNames.size())))respawn();
        ImGui::TextDisabled("%s",playground::stations[station].description);
        if(ImGui::Button(paused?"Resume":"Pause"))paused=!paused;ImGui::SameLine();if(ImGui::Button("Reset (R)"))respawn();ImGui::SameLine();ImGui::Checkbox("1/4 speed",&slow);
        if(ImGui::Checkbox("Trail assist",&automatic)&&automatic)simulation.reverse=false;ImGui::SameLine();ImGui::Checkbox("Wheel readings",&diagnostics);
        ImGui::Checkbox("Arcade boost (hold B)",&arcadeBoost);if(arcadeBoost)ImGui::ProgressBar(simulation.boost.charge,ImVec2(180,10),"boost charge");
        if(automatic){ImGui::SetNextItemWidth(150);ImGui::SliderFloat(station==6?"Approach speed":"Crawl speed",&targetSpeed,.5f,station==6?14.f:6.f,"%.1f m/s");}
        if(station==7){ImGui::SetNextItemWidth(150);ImGui::SliderFloat("Wind speed",&windSpeed,0,35,"%.1f m/s");
            const char* directions[]={"Crosswind","Headwind","Tailwind"};ImGui::SetNextItemWidth(150);ImGui::Combo("Airflow",&windDirection,directions,3);
            ImGui::Checkbox("Gusts",&gusts);ImGui::SameLine();ImGui::Checkbox("Hold brakes",&holdBrakes);
            ImGui::Text("Aero force: %.0f N  /  air: %.1f m/s",simulation.aerodynamicForce.length(),simulation.airVelocity().length());ImGui::TextDisabled("Estimated drag and pressure centre. No CFD.");}
        ImGui::Text("%.1f km/h   %s   %d tyres supporting",simulation.speed()*3.6f,simulation.reverse?"REVERSE":"LOW RANGE",simulation.contactCount());
        const char* views[]={"Chase","Low side","Front","Overview","Front suspension","Rear suspension","Driver's eye"};ImGui::SetNextItemWidth(150);ImGui::Combo("Camera (C)",&view,views,7);
        ImGui::TextDisabled("W throttle / S brake / A D steer / Space handbrake");ImGui::TextDisabled("G reverse / P pause / O orbit / H hide / Esc exit");
        if(diagnostics){ImGui::Separator();drawText("FL     FR     RL     RR     (compression / load)");
            for(int i=0;i<4;++i){if(i)ImGui::SameLine();ImGui::BeginGroup();float compression=(simulation.travel[i]-simulation.tune.dims.droop)/(simulation.tune.dims.bump-simulation.tune.dims.droop);
                ImGui::PushID(i);ImGui::ProgressBar(compression,ImVec2(68,9),"");ImGui::Text("%3.0f mm",1000*(simulation.travel[i]-simulation.tune.dims.droop));ImGui::Text("%.1f kN",simulation.load[i]*.001f);ImGui::PopID();ImGui::EndGroup();}
            ImGui::TextDisabled("Unloaded tyres lose grip. R resets after a rollover.");}
        ImGui::End();
    });
    ImGui::StyleColorsDark();ImGui::GetStyle().WindowRounding=5;
    canvas.onKeyPressed([&](KeyEvent e){if(e.key==Key::ESCAPE)canvas.close();if(ImGui::GetIO().WantCaptureKeyboard)return;
        if(e.key==Key::R)respawn();if(e.key==Key::P)paused=!paused;if(e.key==Key::C){view=(view+1)%7;cameraReady=false;}
        if(e.key==Key::G){simulation.reverse=!simulation.reverse;automatic=false;}if(e.key==Key::H){showControls=!showControls;cameraReady=false;}
        if(e.key==Key::O){freeCamera=!freeCamera;orbit.target.copy(simulation.origin()).add(Vector3(0,1,0));} });
    canvas.onWindowResize([&](WindowSize s){camera->aspect=s.aspect();camera->updateProjectionMatrix();renderer.setSize(s);composer.setSize(s.width(),s.height());});
    std::ofstream csv;if(!telemetry.empty()){csv.open(telemetry+".csv");csv<<std::setprecision(9)<<"frame,t,x,y,z,speed,contacts,flTravel,frTravel,rlTravel,rrTravel,flLoad,frLoad,rlLoad,rrLoad,qx,qy,qz,qw,windX,windZ,aeroFx,aeroFy,aeroFz,throttle,brake,boostActive,boostCharge,cameraX,cameraY,cameraZ,view,playbackScale\n";}
    if(!sequence.empty())std::filesystem::create_directories(sequence);Clock clock;int discarded=0;
    canvas.animate([&]{FrameBudget budget;float dt=capture?1.f/30:std::min(clock.getDelta(),.10f);
        simulation.windVelocity=station==7?Vector3(windDirection==0?windSpeed:0,0,windDirection==1?-windSpeed:windDirection==2?windSpeed:0):Vector3();simulation.windGusts=gusts;
        if(!paused){accumulator+=dt*(slow?.25:playbackScale);int steps=0;
            while(accumulator+1e-9>=playground::Simulation::fixedStep&&steps<24){float gas=canvas.isKeyDown(Key::W)?1.f:0,brake=canvas.isKeyDown(Key::S)?1.f:0;
                float turn=rally::steerInput(canvas.isKeyDown(Key::A),canvas.isKeyDown(Key::D));
                const bool boostRequest=arcadeBoost&&(canvas.isKeyDown(Key::B)||(automatic&&station==6&&simulation.origin().z>=103&&simulation.origin().z<110));
                if(automatic){auto p=simulation.origin(),f=Vector3(0,0,1).applyQuaternion(simulation.rotation());float yaw=std::atan2(f.x,f.z),error=(boostRequest?14.f:targetSpeed)-simulation.speed();
                    float demand=error*.55f+simulation.tune.mass*9.81f*f.y/simulation.tune.driveForce;
                    gas=std::clamp(demand,0.f,1.f);brake=std::clamp(-demand*simulation.tune.driveForce/(simulation.tune.mass*9.81f*1.8f),0.f,1.f);
                    turn=std::clamp((playground::Terrain::trailCenter(station,p.z)-p.x)*.22f-yaw*1.5f,-1.f,1.f);}
                if(automatic&&simulation.origin().z>playground::stations[station].endZ){gas=0;brake=1;}
                if(holdBrakes)brake=1;
                simulation.tick(gas,brake,turn,canvas.isKeyDown(Key::SPACE),boostRequest);accumulator-=playground::Simulation::fixedStep;simulated+=playground::Simulation::fixedStep;++steps;}
            if(accumulator>.1){accumulator=0;++discarded;}
        }
        const auto p=simulation.origin();const auto q=simulation.rotation();
        auto rig=simulation.tune.visualRig;
        if(presented!=selected){if(activeRoot)scene->remove(*activeRoot);activeRoot.reset();activeCar.reset();activeBaja.reset();
            if(rig==playground::VisualRig::Safari)activeCar=std::make_unique<rally::Buggy>(rally::makeSafari(assets,simulation.tune.dims));
            else if(rig==playground::VisualRig::OriginalBuggy)activeCar=std::make_unique<rally::Buggy>(rally::makeBuggy());
            else if(rig==playground::VisualRig::Baja)activeBaja=std::make_unique<rally::BajaRace>(assets/"baja-427.glb");
            else throw std::runtime_error("Vehicle has no visual adapter");
            activeRoot=activeCar?activeCar->car:activeBaja->car;scene->add(activeRoot);presented=selected;cutawayApplied=false;cabinGlazing.clear();
            if(activeBaja)activeRoot->traverseType<Mesh>([&](Mesh& m){for(const auto& material:m.materials())if(material->name.find("smoked_glazing")!=std::string::npos&&std::none_of(cabinGlazing.begin(),cabinGlazing.end(),[&](const auto& entry){return entry.first==material.get();}))cabinGlazing.emplace_back(material.get(),material->opacity);});}
        for(auto [material,opacity]:cabinGlazing)material->opacity=view==6?.12f:opacity;
        if(cutaway&&activeBaja&&!cutawayApplied){cutawayApplied=true;activeRoot->traverseType<Mesh>([](Mesh& m){for(const char* prefix:{"body.","cab.","cargo.","livery.","door.","hood.","mirror.","bed.","tailgate.","interior.","flare."})if(m.name.starts_with(prefix))m.visible=false;if(m.name.starts_with("rear.")&&(m.name.find("emission")!=std::string::npos||m.name.find("recess_black")!=std::string::npos||m.name.find("vermilion")!=std::string::npos))m.visible=false;});for(const char* name:{"spare.L.steer","spare.R.steer"})activeBaja->required(name)->visible=false;activeBaja->steer[view==4?0:2]->visible=false;}
        if(activeCar){auto& car=*activeCar;car.car->position.copy(p);car.car->quaternion.copy(q);car.body->rotation.set(0,0,0);
            auto contacts=simulation.contacts;
            for(int i=0;i<4;++i){
                // Suspension geometry follows the authored arm arc. The physics
                // uses a straight strut approximation; the small lateral arc is visual.
                contacts[i].local=rally::hubAtTravel(i,simulation.travel[i],simulation.tune.dims);
                car.pivots[i]->position.copy(contacts[i].local);car.pivots[i]->rotation.y=rally::steeringAngle(i,simulation.steer,simulation.tune.dims);car.rolls[i]->rotation.x=simulation.spin[i];}
            rally::updateSuspension(car.suspension,contacts,simulation.steer);
        }else if(rig==playground::VisualRig::Baja){
            // Use the current modular mechanical rig only as a presentation
            // adapter. The shared six-DOF world remains authoritative.
            activeBaja->present(p,q,simulation.travel,simulation.steer,simulation.spin[0],[&](float x,float z){return terrain.height(x,z);});
            for(int i=0;i<4;++i){activeBaja->roll[i]->rotation.x=simulation.spin[i];activeBaja->rotor[i]->rotation.x=simulation.spin[i];}
        }
        sunTarget->position.copy(p);sun->position.copy(p).add(Vector3(-15,25,10));
        windVisuals->visible=station==7&&windSpeed>.1f;
        if(windVisuals->visible){auto dir=simulation.airVelocity().normalize();auto side=Vector3(-dir.z,0,dir.x);
            for(int i=0;i<15;++i){auto& arrow=windArrows[i];float phase=std::fmod(simulation.time*windSpeed*.22f+(i/3)*4.f,20.f)-10;
                arrow->position.set(25,.8f+(i%3)*.8f,137);arrow->position.addScaledVector(dir,phase).addScaledVector(side,((i/3)%3-1)*2.5f);arrow->setDirection(dir);}}
        camera->nearPlane=.05f;camera->fov=48;
        if(view>=4&&!freeCamera){
            orbit.enabled=false;
            Vector3 eye,target;
            if(view==4){eye={-3.1f,.82f,3.15f};target={-.56f,.57f,1.56f};camera->fov=43;}
            if(view==5){eye={-3.15f,.74f,-2.8f};target={-.45f,.54f,-1.57f};camera->fov=43;}
            if(view==6){eye={-.47f,1.55f,.13f};target={-.47f,1.48f,9};camera->nearPlane=.025f;camera->fov=78;}
            camera->position.copy(eye.applyQuaternion(q).add(p));camera->up.copy(Vector3(0,1,0).applyQuaternion(q));camera->lookAt(target.applyQuaternion(q).add(p));
            if(view!=6)camera->position.y=std::max(camera->position.y,terrain.height(camera->position.x,camera->position.z)+.12f);
        }else if(freeCamera&&!capture){orbit.enabled=!ImGui::GetIO().WantCaptureMouse;orbit.update();}
        else{orbit.enabled=false;auto f=Vector3(0,0,1).applyQuaternion(q);f.y=0;f.normalize();auto right=Vector3(f.z,0,-f.x);
            Vector3 desired=p.clone();if(view==0)desired.addScaledVector(f,-8.5f).addScaledVector(right,-3.8f).add(Vector3(0,3.8f,0));
            if(view==1)desired.addScaledVector(right,-6.4f).addScaledVector(f,1.5f).add(Vector3(0,1.5f,0));
            if(view==2)desired.addScaledVector(f,8.5f).addScaledVector(right,-3).add(Vector3(0,2.2f,0));
            if(view==3)desired.add(Vector3(-14,18,-19));
            desired.y=std::max(desired.y,terrain.height(desired.x,desired.z)+.65f);
            if(!cameraReady){cameraPos=desired;cameraReady=true;}else cameraPos.lerp(desired,1-std::exp(-5*dt));
            camera->position.copy(cameraPos);camera->up.set(0,1,0);camera->lookAt(p.clone().add(Vector3(0,.85f,0)));}
        const auto size=canvas.size();if(showControls&&!freeCamera)camera->setViewOffset(size.width(),size.height(),-145,0,size.width(),size.height());else camera->clearViewOffset();
        camera->updateProjectionMatrix();
        composer.render(dt);ui.render();
        if(csv){csv<<frame<<','<<simulated<<','<<p.x<<','<<p.y<<','<<p.z<<','<<simulation.speed()<<','<<simulation.contactCount();for(float t:simulation.travel)csv<<','<<t;for(float l:simulation.load)csv<<','<<l;
            csv<<','<<q.x<<','<<q.y<<','<<q.z<<','<<q.w<<','<<simulation.airVelocity().x<<','<<simulation.airVelocity().z<<','<<simulation.aerodynamicForce.x<<','<<simulation.aerodynamicForce.y<<','<<simulation.aerodynamicForce.z<<','<<simulation.throttle<<','<<simulation.brake<<','<<simulation.boost.active<<','<<simulation.boost.charge<<','<<camera->position.x<<','<<camera->position.y<<','<<camera->position.z<<','<<view<<','<<playbackScale<<'\n';}
        if(!sequence.empty()&&frame>=warmup){std::ostringstream file;file<<sequence<<"/frame_"<<std::setw(5)<<std::setfill('0')<<frame-warmup<<".png";renderer.writeFramebuffer(file.str());}
        if(capture&&++frame>=frames+warmup){if(!shot.empty())renderer.writeFramebuffer(shot);canvas.close();}
    });
    if(!telemetry.empty()){std::ofstream out(telemetry);out<<"{\"vehicle\":\""<<simulation.tune.name<<"\",\"station\":\""<<playground::stations[station].name<<"\",\"solver\":\"Bullet 3.25 raycast\",\"physicsHz\":240,\"simulatedSeconds\":"<<simulated<<",\"discardedBacklogs\":"<<discarded<<"}\n";}
    std::cout<<"Off-road playground exited cleanly\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
