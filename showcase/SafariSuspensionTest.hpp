#pragma once
#include "RallyClearance.hpp"
#include "threepp/math/Triangle.hpp"
#include <iostream>
#include <unordered_map>

namespace safari_test {
inline std::vector<threepp::Vector3> samples(threepp::BufferGeometry& geometry,float spacing=.02f){
    using namespace threepp;auto* p=geometry.getAttribute<float>("position");auto* index=geometry.getIndex();std::vector<Vector3> result;
    const unsigned count=index?index->count():p->count();auto vertex=[&](unsigned j){const auto k=index?index->getX(j):j;return Vector3(p->getX(k),p->getY(k),p->getZ(k));};
    for(unsigned i=0;i+2<count;i+=3){const auto a=vertex(i),b=vertex(i+1),c=vertex(i+2);const int n=std::max(1,static_cast<int>(std::ceil(std::max({a.distanceTo(b),b.distanceTo(c),c.distanceTo(a)})/spacing)));
        for(int u=0;u<=n;++u)for(int v=0;v<=n-u;++v)result.push_back(a.clone().addScaledVector(b.clone().sub(a),u/static_cast<float>(n)).addScaledVector(c.clone().sub(a),v/static_cast<float>(n)));}
    return result;
}
inline float segmentDistance(const threepp::Vector3& a,const threepp::Vector3& b,const threepp::Vector3& c,const threepp::Vector3& d){
    auto u=b.clone().sub(a),v=d.clone().sub(c),r=a.clone().sub(c);const float uu=u.lengthSq(),vv=v.lengthSq(),vr=v.dot(r);float s=0,t=0;
    if(uu<1e-12f){if(vv>1e-12f)t=std::clamp(vr/vv,0.f,1.f);}
    else {const float ur=u.dot(r);if(vv<1e-12f)s=std::clamp(-ur/uu,0.f,1.f);
        else {const float uv=u.dot(v),den=uu*vv-uv*uv;if(den>1e-12f)s=std::clamp((uv*vr-ur*vv)/den,0.f,1.f);t=(uv*s+vr)/vv;
            if(t<0){t=0;s=std::clamp(-ur/uu,0.f,1.f);}else if(t>1){t=1;s=std::clamp((uv-ur)/uu,0.f,1.f);}}}
    return a.clone().addScaledVector(u,s).distanceTo(c.clone().addScaledVector(v,t));
}
// Exact triangle/segment distance, then subtract the fixed tube's OUTER radius.
// The resulting capsule includes finite tube caps conservatively; sampling
// only vertices would miss a support piercing the middle of a spring-seat cap.
inline float triangleSegmentDistance(const threepp::Vector3& a,const threepp::Vector3& b,const threepp::Vector3& c,const threepp::Vector3& from,const threepp::Vector3& to){
    using namespace threepp;auto n=b.clone().sub(a).cross(c.clone().sub(a)),d=to.clone().sub(from);const float den=n.dot(d);
    if(std::abs(den)>1e-12f){const float t=n.dot(a.clone().sub(from))/den;if(t>=0&&t<=1&&Triangle::containsPoint(from.clone().addScaledVector(d,t),a,b,c))return 0;}
    float distance=std::min({segmentDistance(from,to,a,b),segmentDistance(from,to,b,c),segmentDistance(from,to,c,a)});
    if(n.lengthSq()>1e-12f){Triangle tri(a,b,c);Vector3 p;tri.closestPointToPoint(from,p);distance=std::min(distance,p.distanceTo(from));tri.closestPointToPoint(to,p);distance=std::min(distance,p.distanceTo(to));}
    return distance;
}
struct SupportGapWitness {size_t support=0;unsigned triangle=0;threepp::Vector3 a,b,c;};
inline float supportGap(threepp::Mesh& mesh,const threepp::Matrix4& bodyInverse,const std::vector<rally::SuspensionSupport>& supports,int wheel,SupportGapWitness* witness=nullptr){
    using namespace threepp;auto geometry=mesh.geometry();auto* p=geometry->getAttribute<float>("position");auto* index=geometry->getIndex();auto transform=bodyInverse;transform.multiply(*mesh.matrixWorld);
    const unsigned count=index?index->count():p->count();auto vertex=[&](unsigned j){const auto k=index?index->getX(j):j;return Vector3(p->getX(k),p->getY(k),p->getZ(k)).applyMatrix4(transform);};float gap=.10f;
    for(unsigned i=0;i+2<count;i+=3){const auto a=vertex(i),b=vertex(i+1),c=vertex(i+2);Box3 triangleBox;triangleBox.setFromPoints(std::vector<Vector3>{a,b,c});
        for(size_t j=0;j<supports.size();++j){const auto& support=supports[j];if(support.wheel!=wheel)continue;Box3 box;box.setFromPoints(std::vector<Vector3>{support.from,support.to});box.expandByScalar(support.radius+std::max(0.f,gap));
            if(box.intersectsBox(triangleBox)){const float candidate=triangleSegmentDistance(a,b,c,support.from,support.to)-support.radius;if(candidate<gap){gap=candidate;if(witness)*witness={j,i/3,a,b,c};}}}}
    return gap;
}
inline void towerSweep(rally::Buggy& safari){
    using namespace threepp;auto check=[](bool ok,const std::string& message){if(!ok)throw std::runtime_error(message);};auto& rig=safari.suspension;const auto dims=safari.dimensions;
    check(rig.rearTowerSupports.size()==18&&!rig.rearTowerGussets.empty(),"Safari rear tower lost its braced chassis/clevis load path");
    float minSeat=.10f,minCoil=.10f,minEye=.10f,minOther=.10f,minAxle=.10f,minAll=.10f,oldMinimum=.10f,firstCorrectedAxle=.10f;std::string failure;int originalHitPoses=0;std::array<rally::WheelContact,4> wheels;
    struct ComponentMinimum {std::string name;float gap=.10f,travel=0;int wheel=-1;SupportGapWitness witness;};std::vector<ComponentMinimum> components;
    const auto& shock=rig.shocks[3];Quaternion clevis;clevis.setFromUnitVectors(Vector3(0,0,1),shock.nominalPinAxis);
    const auto oldLug=Vector3(-.04f,-.02f,.05f).applyQuaternion(clevis).add(shock.top);
    const std::vector<rally::SuspensionSupport> originalForward{{{.60f,.38f,-1.05f},oldLug,.0275f,3}};
    const std::vector<rally::SuspensionSupport> firstCorrectedDiagonal{{{.53f,.38f,-1.06f},{.54f,.60f,-1.39f},.0225f,3}};
    for(int t=0;t<=220;++t){const float travel=dims.droop+(dims.bump-dims.droop)*t/220.f;
        for(int i=0;i<4;++i)wheels[i].local=rally::hubAtTravel(i,i<2?dims.staticTravel:(i==2?dims.droop+dims.bump-travel:travel),dims);
        rally::updateSuspension(rig,wheels,0);safari.car->updateMatrixWorld(true);auto inverse=*safari.body->matrixWorld;inverse.invert();
        const float oldGap=supportGap(*rig.shocks[3].upperSeat,inverse,originalForward,3);oldMinimum=std::min(oldMinimum,oldGap);if(oldGap<0)++originalHitPoses;
        firstCorrectedAxle=std::min(firstCorrectedAxle,supportGap(*rig.axles[1],inverse,firstCorrectedDiagonal,3));
        for(int i=2;i<4;++i){auto& s=rig.shocks[i];std::vector<std::pair<Mesh*,std::string>> moving;
            // Construction-path identity is retained in every label, so a
            // diagnostic never turns an anonymous mesh into "other hardware".
            const std::array<const char*,16> assemblyNames{{"barrel","upper-neck","lower-neck","shaft","coil","upper-seat","lower-seat","upper-eye","lower-eye","reservoir","reservoir-upper-cap","reservoir-lower-cap","fluid-passage","preload-upper","preload-middle","preload-lower"}};
            check(s.assembly->children.size()==assemblyNames.size(),"Safari damper assembly changed; update explicit component diagnostic labels");
            for(size_t j=0;j<s.assembly->children.size();++j){auto* mesh=dynamic_cast<Mesh*>(s.assembly->children[j]);check(mesh!=nullptr,"Safari damper diagnostic expected a direct mesh child");moving.emplace_back(mesh,std::string(assemblyNames[j])+"[assembly."+std::to_string(j)+"]");}
            for(size_t j=0;j<s.lowerClevis->children.size();++j){auto* mesh=dynamic_cast<Mesh*>(s.lowerClevis->children[j]);check(mesh!=nullptr,"Safari lower clevis diagnostic expected a mesh child");moving.emplace_back(mesh,(j<2?"lower-clevis-ear":"lower-spherical-bearing")+std::string("[clevis.")+std::to_string(j)+"]");}
            moving.insert(moving.end(),{{s.lowerPin.get(),"lower-pin"},{s.bridge.get(),"lower-saddle-bridge"},{rig.uprights[i].get(),"upright"},{rig.lowerJoints[i].get(),"lower-joint"},{rig.upperJoints[i].get(),"upper-joint"},{rig.axles[i-2].get(),"drive-axle"}});
            for(size_t j=0;j<s.saddleBraces.size();++j)moving.emplace_back(s.saddleBraces[j].get(),"lower-saddle-brace."+std::to_string(j));int armIndex=0;for(const auto& arm:rig.arms)if(arm.wheel==i)moving.emplace_back(arm.mesh.get(),"trailing-arm."+std::to_string(armIndex++));
            // Only the fixed top pin/bearing/clevis mating surfaces are absent
            // from this moving list. The WHOLE moving eye, neck, upper seat,
            // spring and reservoir remain checked, without a mount-radius mask.
            for(const auto& [mesh,label]:moving){SupportGapWitness witness;const float gap=supportGap(*mesh,inverse,rig.rearTowerSupports,i,&witness);const char* part="other-hardware";
                if(mesh==s.upperSeat.get()){minSeat=std::min(minSeat,gap);part="upper-seat";}else if(mesh==s.spring.get()){minCoil=std::min(minCoil,gap);part="coil";}else if(mesh==s.upperEye.get()){minEye=std::min(minEye,gap);part="upper-eye";}else minOther=std::min(minOther,gap);
                if(mesh==rig.axles[i-2].get())minAxle=std::min(minAxle,gap);
                auto found=std::find_if(components.begin(),components.end(),[&](const auto& value){return value.name==label;});if(found==components.end()){components.push_back({label});found=components.end()-1;}
                if(gap<found->gap)*found={label,gap,wheels[i].local.y,i,witness};
                if(gap<minAll){minAll=gap;failure="Safari moving "+label+" ("+part+") intersects fixed rear tower: wheel="+std::to_string(i)+" travel="+std::to_string(wheels[i].local.y)+" support="+std::to_string(witness.support)+" triangle="+std::to_string(witness.triangle)+" capsule gap="+std::to_string(gap);}}
        }
    }
    check(originalHitPoses==221,"Rear-tower regression failed to reject original forward tube/upper-seat collision at every travel pose");
    // Actual fishplate surfaces are sampled at <=2 mm edge spacing. Requiring
    // 3 mm INSIDE the capsule union covers the intervening surface too; the
    // conservative tube test therefore covers every added junction plate.
    float gussetCover=1;auto inverse=*safari.body->matrixWorld;inverse.invert();
    for(auto* mesh:rig.rearTowerGussets){auto transform=inverse;transform.multiply(*mesh->matrixWorld);for(const auto& local:samples(*mesh->geometry(),.002f)){auto p=local.clone().applyMatrix4(transform);float cover=1;
            for(const auto& support:rig.rearTowerSupports)cover=std::min(cover,segmentDistance(p,p,support.from,support.to)-support.radius);gussetCover=std::min(gussetCover,-cover);check(cover<=-.003f,"Safari tower gusset escapes the swept capsule clearance envelope");}}
    std::cout<<"Safari rear tower 221-pose triangle/capsule sweep: upper-seat="<<minSeat<<"m coil="<<minCoil<<"m upper-eye="<<minEye<<"m drive-axle="<<minAxle<<"m other-hardware="<<minOther<<"m overall="<<minAll<<"m; original upper-seat hits="<<originalHitPoses<<"/221 gap="<<oldMinimum<<"m; first-corrected straight-diagonal axle="<<firstCorrectedAxle<<"m; gusset containment margin="<<gussetCover<<"m.\n";
    for(const auto& component:components){std::cout<<"  Tower component "<<component.name<<" gap="<<(component.wheel<0?">=":"")<<component.gap<<"m";
        if(component.wheel>=0){const auto& w=component.witness;const auto& support=rig.rearTowerSupports[w.support];auto centre=w.a.clone().add(w.b).add(w.c).multiplyScalar(1.f/3);
            std::cout<<" wheel="<<component.wheel<<" travel="<<component.travel<<" support="<<w.support<<" from="<<support.from.x<<","<<support.from.y<<","<<support.from.z<<" to="<<support.to.x<<","<<support.to.y<<","<<support.to.z<<" triangle="<<w.triangle<<" triangleCentre="<<centre.x<<","<<centre.y<<","<<centre.z;}
        std::cout<<"\n";}
    check(minAll>=.004f,failure);check(minSeat>=.010f&&minCoil>=.010f,"Safari rear tower leaves insufficient running room for the full upper-seat/coil sweep");
    check(firstCorrectedAxle<.005f,"Drive-axle regression no longer detects the first-corrected diagonal's known tight running room");
    check(minAxle>=.015f,"Safari rotating drive axle has less than 15 mm full-travel tower running room: "+std::to_string(minAxle));
}
struct SkinIndex {
    std::vector<rally::BodyTriangle> triangles;std::unordered_map<std::int64_t,std::vector<unsigned>> cells;
    static std::int64_t key(int x,int y,int z){return (static_cast<std::int64_t>(x+256)<<20)|(static_cast<std::int64_t>(y+256)<<10)|(z+256);}
    explicit SkinIndex(const std::vector<rally::BodyTriangle>& source){
        for(const auto& face:source)if(face.name.starts_with("body.")||face.name.starts_with("cabin.")||face.name.starts_with("interior."))triangles.push_back(face);
        for(unsigned i=0;i<triangles.size();++i){auto box=triangles[i].bounds;box.expandByScalar(.025f);auto lo=box.min(),hi=box.max();
            for(int x=static_cast<int>(std::floor(lo.x/.125f));x<=static_cast<int>(std::floor(hi.x/.125f));++x)for(int y=static_cast<int>(std::floor(lo.y/.125f));y<=static_cast<int>(std::floor(hi.y/.125f));++y)for(int z=static_cast<int>(std::floor(lo.z/.125f));z<=static_cast<int>(std::floor(hi.z/.125f));++z)cells[key(x,y,z)].push_back(i);}
    }
    float nearSkin(const threepp::Vector3& p,std::string& name,threepp::Vector3* nearest=nullptr)const{
        using namespace threepp;float distance=.025f;const auto found=cells.find(key(static_cast<int>(std::floor(p.x/.125f)),static_cast<int>(std::floor(p.y/.125f)),static_cast<int>(std::floor(p.z/.125f))));
        if(found!=cells.end())for(auto i:found->second){const auto& face=triangles[i];if(face.bounds.distanceToPoint(p)>distance)continue;Vector3 closest;Triangle(face.a,face.b,face.c).closestPointToPoint(p,closest);float d=p.distanceTo(closest);if(d<distance){distance=d;name=face.name;if(nearest)nearest->copy(closest);}}
        return distance;
    }
};
// Distance to the ACTUAL revolved rubber cross-section, preserving the empty
// rim interior. A filled tyre cylinder would reject legitimate inboard joints.
inline float rubberDistance(float axial,float radial,const std::vector<threepp::Vector2>& polygon){
    using namespace threepp;Vector2 p(axial,radial);float best=10;bool inside=false;
    for(size_t i=0;i+1<polygon.size();++i){const auto& a=polygon[i];const auto& b=polygon[i+1];auto d=b.clone().sub(a);float length=d.lengthSq();if(length<1e-12f)continue;
        float t=std::clamp(p.clone().sub(a).dot(d)/length,0.f,1.f);best=std::min(best,p.distanceTo(a.clone().addScaledVector(d,t)));
        if((a.y>radial)!=(b.y>radial))if(axial<a.x+(b.x-a.x)*(radial-a.y)/(b.y-a.y))inside=!inside;
    }return inside?-best:best;
}
inline void run(rally::Buggy& safari,const std::vector<rally::BodyTriangle>& source){
    using namespace threepp;using rally::SuspensionProfile;auto check=[](bool ok,const std::string& text){if(!ok)throw std::runtime_error(text);};const auto dims=safari.dimensions;
    check(safari.suspension.profile==SuspensionProfile::Safari,"Safari has no explicit suspension profile");
    SkinIndex skin(source);auto* tyreMesh=dynamic_cast<Mesh*>(safari.rolls[0]->children.front());auto* lathe=dynamic_cast<LatheGeometry*>(tyreMesh->geometry().get());check(lathe!=nullptr,"Actual rubber profile unavailable");
    std::vector<Vector2> rubber;for(const auto& p:lathe->parameters.points)rubber.emplace_back(p.y*dims.tyreHalfWidth/rally::buggyDimensions.tyreHalfWidth,p.x*dims.tyreRadius/rally::buggyDimensions.tyreRadius);
    float minSkin=.025f,minRubber=1,maxBearingAngle=0;std::string skinFailure;std::array<float,4> shortest,longest;shortest.fill(10);longest.fill(0);std::array<rally::WheelContact,4> wheels;
    std::unordered_map<BufferGeometry*,std::vector<Vector3>> fixedSamples;
    for(int t=0;t<=76;++t){float travel=dims.droop+(dims.bump-dims.droop)*t/76.f;
        for(int i=0;i<4;++i)wheels[i].local=rally::hubAtTravel(i,travel,dims);rally::updateSuspension(safari.suspension,wheels,0);safari.car->updateMatrixWorld(true);
        for(auto& shock:safari.suspension.shocks){const int i=shock.wheel;shortest[i]=std::min(shortest[i],shock.length);longest[i]=std::max(longest[i],shock.length);
            const float extension=shock.length-shock.shaftStart;check(extension>.08f&&extension+.05f<shock.barrelLength-.08f,"Safari damper cannot contain its piston/shaft through full stroke");
            check(shock.length-.10f-.012f-shock.shaftStart>.02f,"Safari lower spring seat bottoms on the barrel/seal");
            check((shock.length-shock.springStart-.10f)/rally::coilTurns>2*rally::wireRadius+.01f,"Safari spring reaches coil bind");
            check(shock.barrel->scale.y==1,"Safari fixed barrel stretches");
            auto foot=rally::coiloverFoot(i,wheels[i].local,dims,shock.lowerInboard);check(shock.lowerPin->position.distanceTo(foot)<.000001f,"Safari lower pin detaches from actual arm pickup");
            auto eyeAxis=Vector3(0,0,1).applyQuaternion(shock.assembly->quaternion);auto upperPin=Vector3(0,1,0).applyQuaternion(shock.topPin->quaternion);auto lowerPin=Vector3(0,1,0).applyQuaternion(shock.lowerPin->quaternion);
            const float angle=std::max(eyeAxis.angleTo(upperPin),eyeAxis.angleTo(lowerPin));maxBearingAngle=std::max(maxBearingAngle,angle);check(angle<(i<2?.0005f:.26f),"Safari pin exceeds spherical-bearing articulation");
            check(i>1||(shock.top.y==.94f&&shock.top.z==dims.halfWheelbase),"Safari front top returned above the actual bonnet");
            std::vector<Mesh*> moving;shock.assembly->traverseType<Mesh>([&](Mesh& m){moving.push_back(&m);});shock.lowerClevis->traverseType<Mesh>([&](Mesh& m){moving.push_back(&m);});moving.push_back(shock.lowerPin.get());moving.push_back(shock.topPin.get());
            for(auto* mesh:moving){auto* g=mesh->geometry().get();auto& points=fixedSamples[g];if(points.empty()||g==shock.spring->geometry().get())points=samples(*g);
                for(const auto& local:points){auto world=local.clone().applyMatrix4(*mesh->matrixWorld);std::string name;Vector3 nearest;float clearance=skin.nearSkin(world,name,&nearest);
                    if(clearance<minSkin){minSkin=clearance;skinFailure="Safari moving coilover intersects body/tower clearance: "+name+" wheel="+std::to_string(i)+" travel="+std::to_string(travel)+" point="+std::to_string(world.x)+","+std::to_string(world.y)+","+std::to_string(world.z)+" distance="+std::to_string(clearance)+" nearest="+std::to_string(nearest.x)+","+std::to_string(nearest.y)+","+std::to_string(nearest.z);}
                    for(int a=0;a<=(i<2?40:0);++a){float steer=i<2?-.4f+.8f*a/40.f:0;float angle=-rally::steeringAngle(i,steer,dims),c=std::cos(angle),s=std::sin(angle);auto p=world.clone().sub(wheels[i].local);float axial=c*p.x+s*p.z;
                        if(std::abs(axial)>dims.tyreHalfWidth+minRubber)continue;float radial=std::hypot(p.y,-s*p.x+c*p.z);float gap=rubberDistance(axial,radial,rubber);minRubber=std::min(minRubber,gap);
                        check(gap>.02f,"Safari coilover/clevis rubs actual tyre rubber through steering/travel: wheel="+std::to_string(i)+" gap="+std::to_string(gap));}
                }
            }
        }
    }
    check(shortest[0]>.67f&&longest[0]<.81f&&longest[0]-shortest[0]>.13f,"Safari front usable stroke/range lost");
    check(shortest[2]>.87f&&longest[2]<1.03f&&longest[2]-shortest[2]>.15f,"Safari rear usable stroke/range lost");
    for(auto* mesh:safari.suspension.fixedMeshes)if(mesh->name.starts_with("front.frame")||mesh->name.starts_with("rear.frame.safari-shock-tower")||mesh->name=="safari.upper-clevis"){
        for(const auto& local:samples(*mesh->geometry())){auto world=local.clone().applyMatrix4(*mesh->matrixWorld);std::string name;float clearance=skin.nearSkin(world,name);if(clearance<minSkin){minSkin=clearance;skinFailure="Safari front tower/clevis intersects actual body: "+name;}}}
    check(minSkin>=.019f,skinFailure+"; minimum actual rubber gap="+std::to_string(minRubber)+"; spherical articulation="+std::to_string(maxBearingAngle));
    towerSweep(safari);
    // Legacy/default construction and articulation remain identical, including
    // actual positions, geometry vertices and original shock top/barrel/shaft.
    auto a=Group::create(),b=Group::create();auto legacy=rally::addSuspension(*a),explicitLegacy=rally::addSuspension(*b,rally::buggyDimensions,SuspensionProfile::Legacy);
    check(legacy.profile==SuspensionProfile::Legacy&&legacy.fixedMeshes.size()==34&&legacy.arms.size()==12&&legacy.steering.size()==2,"Accepted Legacy rig topology/default profile changed");
    std::vector<Mesh*> defaultMeshes,explicitMeshes;a->traverseType<Mesh>([&](Mesh& m){defaultMeshes.push_back(&m);});b->traverseType<Mesh>([&](Mesh& m){explicitMeshes.push_back(&m);});check(defaultMeshes.size()==explicitMeshes.size(),"Default Legacy mesh count differs");
    for(int t=0;t<=52;++t){for(int i=0;i<4;++i)wheels[i].local=rally::hubAtTravel(i,rally::droop+.01f*t);rally::updateSuspension(legacy,wheels,.4f);rally::updateSuspension(explicitLegacy,wheels,.4f);
        for(int i=0;i<4;++i){const auto& p=legacy.shocks[i];const auto& q=explicitLegacy.shocks[i];const Vector3 originalTop((i%2?1.f:-1.f)*.80f,1.14f,(i<2?1.35f:-1.35f)+(i<2?-.22f:.15f));check(p.top.equals(originalTop)&&p.top.equals(q.top)&&p.length==q.length&&p.barrel->position.y==.20f&&p.barrelLength==.31f&&p.shaftStart==.35f&&p.springStart==.06f,"Default open-buggy shock pickups/lengths changed");}
        for(size_t i=0;i<defaultMeshes.size();++i){const auto& p=*defaultMeshes[i];const auto& q=*explicitMeshes[i];check(p.position.equals(q.position)&&p.scale.equals(q.scale)&&p.quaternion.equals(q.quaternion)&&p.geometry()->getAttribute<float>("position")->array()==q.geometry()->getAttribute<float>("position")->array(),"Default and explicit Legacy mesh articulation differ");}}
    std::cout<<"PASS: Safari full suspension sweep: body/tower room>="<<minSkin<<"m, actual tyre rubber gap="<<minRubber<<"m, front stroke="<<longest[0]-shortest[0]<<"m, rear stroke="<<longest[2]-shortest[2]<<"m, max spherical articulation="<<maxBearingAngle<<"rad; fixed barrels, rod insertion, coil bind, arm/pin attachment and Legacy geometry pass.\n";
}
}
