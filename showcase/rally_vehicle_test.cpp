// CPU-only checks against the actual rendered model and particle simulation.
#include "RallyBuggy.hpp"
#include "RallyDust.hpp"
#include "RallyCamera.hpp"
#include "RallyDynamics.hpp"
#include "RallyTrails.hpp"
#include "RallySafari.hpp"
#include "RallyClearance.hpp"
#include "threepp/math/Triangle.hpp"
#include <filesystem>
#include <iostream>
#include <stdexcept>
#include <regex>
#include "threepp/renderers/shaders/ShaderChunk.hpp"
using namespace threepp;

void require(bool condition,const std::string& message){if(!condition)throw std::runtime_error(message);}
int main(){try{
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
    auto safari=rally::makeSafari(std::filesystem::path(__FILE__).parent_path()/"assets");auto safariTriangles=rally::bodyTriangles(safari);const auto& sd=safari.dimensions;
    require(sd.halfTrack<buggy.dimensions.halfTrack&&sd.tyreRadius<buggy.dimensions.tyreRadius,"Safari proportions did not reach actual chassis");
    int safariPoses=0;
    for(int wheel=0;wheel<4;++wheel)for(int t=0;t<=76;++t)for(int a=0;a<=(wheel<2?40:0);++a){
        float travel=sd.droop+(sd.bump-sd.droop)*t/76.f,steer=wheel<2?-.4f+.8f*a/40.f:0;
        auto hit=rally::bodyTyreIntersection(safariTriangles,wheel,travel,steer,sd,.020f);
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
