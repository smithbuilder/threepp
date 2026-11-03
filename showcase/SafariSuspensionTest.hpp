#pragma once
#include "RallyClearance.hpp"
#include "threepp/math/Triangle.hpp"
#include <iostream>
#include <unordered_map>

namespace safari_test {
inline std::vector<threepp::Vector3> samples(threepp::BufferGeometry& geometry){
    using namespace threepp;auto* p=geometry.getAttribute<float>("position");auto* index=geometry.getIndex();std::vector<Vector3> result;
    const unsigned count=index?index->count():p->count();auto vertex=[&](unsigned j){const auto k=index?index->getX(j):j;return Vector3(p->getX(k),p->getY(k),p->getZ(k));};
    for(unsigned i=0;i+2<count;i+=3){const auto a=vertex(i),b=vertex(i+1),c=vertex(i+2);const int n=std::max(1,static_cast<int>(std::ceil(std::max({a.distanceTo(b),b.distanceTo(c),c.distanceTo(a)})/.02f)));
        for(int u=0;u<=n;++u)for(int v=0;v<=n-u;++v)result.push_back(a.clone().addScaledVector(b.clone().sub(a),u/static_cast<float>(n)).addScaledVector(c.clone().sub(a),v/static_cast<float>(n)));}
    return result;
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
    for(auto* mesh:safari.suspension.fixedMeshes)if(mesh->name.starts_with("front.frame")||mesh->name=="rear.frame.safari-shock-tower"||mesh->name=="safari.upper-clevis"){
        for(const auto& local:samples(*mesh->geometry())){auto world=local.clone().applyMatrix4(*mesh->matrixWorld);std::string name;float clearance=skin.nearSkin(world,name);if(clearance<minSkin){minSkin=clearance;skinFailure="Safari front tower/clevis intersects actual body: "+name;}}}
    check(minSkin>=.019f,skinFailure+"; minimum actual rubber gap="+std::to_string(minRubber)+"; spherical articulation="+std::to_string(maxBearingAngle));
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
