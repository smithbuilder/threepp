#pragma once
#include "PlaygroundTerrain.hpp"
#include "PlaygroundVehicles.hpp"
#include "PlaygroundArcade.hpp"
#include <btBulletDynamicsCommon.h>
#include <BulletDynamics/Vehicle/btRaycastVehicle.h>
#include <memory>
#include <string>

namespace playground {
inline btVector3 bt(const Vector3& v){return {v.x,v.y,v.z};}
inline Vector3 vec(const btVector3& v){return {float(v.x()),float(v.y()),float(v.z())};}
// A finite tyre footprint improves contact on crests and steep gradients. Each
// ray samples the lower tyre arc; Bullet still owns spring, tyre and body forces.
// Only static terrain is queried. This is not a rigid or deformable tyre solver.
class FootprintRaycaster:public btVehicleRaycaster {
    btDynamicsWorld& world;btRigidBody& body;const Tune& tune;
public:
    float steering=0;int corner=0;
    std::array<float,4> requestedLength{};
    FootprintRaycaster(btDynamicsWorld& w,btRigidBody& b,const Tune& t):world(w),body(b),tune(t){}
    void* castRay(const btVector3& from,const btVector3& to,btVehicleRaycasterResult& result)override{
        const int i=corner++%4;const auto& d=tune.dims;auto dir=(to-from).normalized();
        auto basis=body.getWorldTransform().getBasis()*btMatrix3x3(btQuaternion({0,1,0},rally::steeringAngle(i,steering,d)));
        bool found=false;btScalar closest=1;const btCollisionObject* object=nullptr;
        for(int row=-1;row<=1;++row)for(int arc=-3;arc<=3;++arc){float a=arc*.24f;
            auto offset=basis*btVector3(row*d.tyreHalfWidth*.70f,-d.tyreRadius*std::cos(a),d.tyreRadius*std::sin(a));
            auto start=from+offset-dir*d.tyreRadius,end=to+offset-dir*d.tyreRadius;
            btCollisionWorld::ClosestRayResultCallback ray(start,end);ray.m_collisionFilterGroup=2;ray.m_collisionFilterMask=1;
            world.rayTest(start,end,ray);
            if(ray.hasHit()&&ray.m_closestHitFraction<closest){closest=ray.m_closestHitFraction;result.m_hitPointInWorld=ray.m_hitPointWorld;
                result.m_hitNormalInWorld=ray.m_hitNormalWorld.normalized();object=ray.m_collisionObject;found=true;}
        }
        requestedLength[i]=found?float(closest*(to-from).length()-d.tyreRadius):1000.f;
        if(found)result.m_distFraction=closest;
        return const_cast<btCollisionObject*>(object);
    }
};
// Iterative static/dynamic tyre friction at the actual patch. The stock brake
// divides a single impulse between all wheels; on a slope that never fully
// resolves the coupled pitch/translation error. Accumulated impulses here stay
// inside ONE Coulomb circle per tyre, even across the solver iterations.
class CrawlVehicle:public btRaycastVehicle {
public:
    using btRaycastVehicle::btRaycastVehicle;
    FootprintRaycaster* footprint=nullptr;
    std::array<float,4> stopLoad{};
    void updateFriction(btScalar dt)override{
        std::array<btVector3,4> forward,side,relative;
        std::array<btScalar,4> longitudinal{},lateral{},limit{},drive{},brake{};
        auto& body=*getRigidBody();
        // Unilateral bump-stop contacts carry impact load after spring travel
        // runs out. Accumulated impulses include finite chassis inertia; tyres
        // cannot disappear into the road while the rendered stroke is clamped.
        stopLoad.fill(0);std::array<float,4> stopImpulse{};
        if(footprint)for(int pass=0;pass<16;++pass)for(int i=0;i<4;++i){auto& w=getWheelInfo(i);if(!w.m_raycastInfo.m_isInContact)continue;
            float minimum=w.getSuspensionRestLength()-w.m_maxSuspensionTravelCm*.01f;
            float penetration=minimum-footprint->requestedLength[i];if(penetration<-.002f)continue;
            auto point=w.m_raycastInfo.m_contactPointWS,normal=w.m_raycastInfo.m_contactNormalWS,lever=point-body.getCenterOfMassPosition();
            float target=std::max(0.f,penetration-.001f)*.15f/dt;
            float impulse=std::max(0.f,stopImpulse[i]+(target-body.getVelocityInLocalPoint(lever).dot(normal))/body.computeImpulseDenominator(point,normal));
            body.applyImpulse(normal*(impulse-stopImpulse[i]),lever);stopImpulse[i]=impulse;stopLoad[i]=impulse/dt;
        }
        for(int i=0;i<4;++i){auto& w=getWheelInfo(i);if(!w.m_raycastInfo.m_isInContact)continue;
            const auto n=w.m_raycastInfo.m_contactNormalWS;auto axle=-w.m_worldTransform.getBasis().getColumn(0);
            auto tangent=axle-n*axle.dot(n);if(tangent.length2()<1e-8f)continue;
            side[i]=tangent.normalized();forward[i]=n.cross(side[i]).normalized();
            relative[i]=w.m_raycastInfo.m_contactPointWS-body.getCenterOfMassPosition();
            limit[i]=(btMin(w.m_wheelsSuspensionForce,w.m_maxSuspensionForce)+stopLoad[i])*dt*w.m_frictionSlip;
            drive[i]=w.m_engineForce*dt;brake[i]=w.m_brake;
        }
        for(int pass=0;pass<12;++pass)for(int i=0;i<4;++i){if(limit[i]<=0)continue;auto p=body.getCenterOfMassPosition()+relative[i];
            auto velocity=body.getVelocityInLocalPoint(relative[i]);
            float lon=btClamped(longitudinal[i]-velocity.dot(forward[i])/body.computeImpulseDenominator(p,forward[i]),drive[i]-brake[i],drive[i]+brake[i]);
            float lat=lateral[i]-velocity.dot(side[i])/body.computeImpulseDenominator(p,side[i]);
            float length=std::sqrt(lon*lon+lat*lat);if(length>limit[i]){lon*=limit[i]/length;lat*=limit[i]/length;}
            body.applyImpulse(forward[i]*(lon-longitudinal[i])+side[i]*(lat-lateral[i]),relative[i]);longitudinal[i]=lon;lateral[i]=lat;
        }
    }
};
// Bullet's stock action runs the vehicle AFTER integrating its pose. On a
// braked grade that leaves one gravity step of creep in every displayed pose.
// Resolve tyre/suspension impulses after gravity and contacts, BEFORE pose
// integration, so parking and very slow crawling don't have that phase error.
class VehicleWorld:public btDiscreteDynamicsWorld {
public:
    using btDiscreteDynamicsWorld::btDiscreteDynamicsWorld;
    btRaycastVehicle* activeVehicle=nullptr;
    void solveConstraints(btContactSolverInfo& info)override{
        btDiscreteDynamicsWorld::solveConstraints(info);
        if(activeVehicle)activeVehicle->updateVehicle(info.m_timeStep);
    }
};
class Simulation {
    btDefaultCollisionConfiguration config;
    btCollisionDispatcher dispatcher{&config};
    btDbvtBroadphase broadphase;
    btSequentialImpulseConstraintSolver solver;
    VehicleWorld world{&dispatcher,&broadphase,&solver,&config};
    btTriangleMesh triangles;
    std::unique_ptr<btBvhTriangleMeshShape> groundShape;
    std::unique_ptr<btRigidBody> ground;
    std::vector<std::unique_ptr<btBoxShape>> sceneryShapes;
    std::vector<std::unique_ptr<btRigidBody>> sceneryBodies;
    std::unique_ptr<btConvexHullShape> hull;
    std::unique_ptr<btCompoundShape> chassisShape;
    std::unique_ptr<btRigidBody> chassis;
    std::unique_ptr<FootprintRaycaster> raycaster;
    std::unique_ptr<CrawlVehicle> vehicle;
public:
    static constexpr float fixedStep=1.f/240;
    const Terrain& terrain;
    Tune tune=tunes[0];
    int selected=0;
    float steer=0,time=0;
    float throttle=0,brake=0;
    bool reverse=false;
    ArcadeBoost boost;
    Vector3 windVelocity,aerodynamicForce;
    bool windGusts=false;
    std::array<float,4> travel{},load{},spin{};
    std::array<bool,4> grounded{};
    std::array<rally::WheelContact,4> contacts{};
    explicit Simulation(const Terrain& t):terrain(t){
        world.setGravity({0,-9.81f,0});world.getSolverInfo().m_numIterations=16;
        for(size_t i=0;i<t.indices.size();i+=3)triangles.addTriangle(bt(t.vertex(t.indices[i])),bt(t.vertex(t.indices[i+1])),bt(t.vertex(t.indices[i+2])),false);
        groundShape=std::make_unique<btBvhTriangleMeshShape>(&triangles,true);
        btRigidBody::btRigidBodyConstructionInfo ci(0,nullptr,groundShape.get());ground=std::make_unique<btRigidBody>(ci);ground->setFriction(1);
        world.addRigidBody(ground.get(),1,2);
        for(const auto& b:windFrame){auto shape=std::make_unique<btBoxShape>(btVector3(b[3],b[4],b[5]));btRigidBody::btRigidBodyConstructionInfo info(0,nullptr,shape.get());
            auto body=std::make_unique<btRigidBody>(info);btTransform tr;tr.setIdentity();tr.setOrigin({b[0],b[1],b[2]});body->setWorldTransform(tr);world.addRigidBody(body.get(),1,2);
            sceneryShapes.push_back(std::move(shape));sceneryBodies.push_back(std::move(body));}
        select(0,stations[0]);
    }
    ~Simulation(){clear();for(auto& b:sceneryBodies)world.removeRigidBody(b.get());world.removeRigidBody(ground.get());}
    void clear(){world.activeVehicle=nullptr;vehicle.reset();raycaster.reset();if(chassis)world.removeRigidBody(chassis.get());chassis.reset();chassisShape.reset();hull.reset();}
    Vector3 cg()const{return {0,tune.cgY,tune.cgZ};}
    Vector3 origin()const{return vec(chassis->getWorldTransform().getOrigin()-chassis->getWorldTransform().getBasis()*bt(cg()));}
    threepp::Quaternion rotation()const{auto q=chassis->getWorldTransform().getRotation();return threepp::Quaternion(q.x(),q.y(),q.z(),q.w());}
    Vector3 velocity()const{return vec(chassis->getLinearVelocity());}
    Vector3 angularVelocity()const{return vec(chassis->getAngularVelocity());}
    Vector3 centerOfMass()const{return vec(chassis->getWorldTransform().getOrigin());}
    Vector3 airVelocity()const{return windVelocity.clone().multiplyScalar(windGusts?1+.32f*std::sin(time*2.1f)+.12f*std::sin(time*5.3f):1);}
    void setGrip(float grip){tune.grip=grip;for(int i=0;i<4;++i)vehicle->getWheelInfo(i).m_frictionSlip=grip;}
    float rayHeight(float x,float z)const{btCollisionWorld::ClosestRayResultCallback ray({x,40,z},{x,-20,z});ray.m_collisionFilterGroup=2;ray.m_collisionFilterMask=1;world.rayTest(ray.m_rayFromWorld,ray.m_rayToWorld,ray);return ray.hasHit()?ray.m_hitPointWorld.y():-1000;}
    float speed()const{return float(chassis->getLinearVelocity().dot(chassis->getWorldTransform().getBasis().getColumn(2)));}
    void select(int n,const Station& station){
        clear();selected=std::clamp(n,0,static_cast<int>(tunes.size())-1);tune=tunes[selected];steer=time=throttle=brake=0;reverse=false;
        // Hull bottom follows the lowest substantial chassis, excluding tyres.
        const float bottom=tune.hullBottom;
        const float centerY=bottom+tune.height*.5f,end=tune.length*.5f,flat=tune.dims.halfWheelbase*.82f;
        // Raised nose/tail represent bumper approach and departure angles. A
        // flat box extended under the nose acted as an invisible plough before
        // the front tyres could climb the ramp, especially on the Baja truck.
        const std::array<std::pair<float,float>,6> outline{{{-end,bottom+tune.tailRise},{-flat,bottom},{flat,bottom},{end,bottom+tune.noseRise},{end,bottom+tune.height},{-end,bottom+tune.height}}};
        hull=std::make_unique<btConvexHullShape>();for(float side:{-1.f,1.f})for(auto [z,y]:outline)hull->addPoint({side*tune.width*.5f,y-centerY,z},false);
        hull->recalcLocalAabb();hull->setMargin(.025f);
        chassisShape=std::make_unique<btCompoundShape>();btTransform local;local.setIdentity();
        local.setOrigin({0,bottom+tune.height*.5f-tune.cgY,-tune.cgZ});chassisShape->addChildShape(local,hull.get());
        // The collision hull excludes roof, engine ends and wheels. Its box
        // inertia badly understates their rotational mass and made takeoffs
        // pitch violently. Use full-vehicle SI estimates independent of that
        // simplified collision envelope (X pitch / Y yaw / Z roll).
        btVector3 inertia(tune.pitchInertia,tune.yawInertia,tune.rollInertia);
        btRigidBody::btRigidBodyConstructionInfo ci(tune.mass,nullptr,chassisShape.get(),inertia);chassis=std::make_unique<btRigidBody>(ci);
        chassis->setDamping(.008f,.015f);chassis->setFriction(.65f);chassis->setRestitution(.02f);chassis->setActivationState(DISABLE_DEACTIVATION);
        chassis->setCcdMotionThreshold(.4f);chassis->setCcdSweptSphereRadius(.15f);world.addRigidBody(chassis.get(),2,1);
        btRaycastVehicle::btVehicleTuning settings;
        raycaster=std::make_unique<FootprintRaycaster>(world,*chassis,tune);vehicle=std::make_unique<CrawlVehicle>(settings,chassis.get(),raycaster.get());
        vehicle->footprint=raycaster.get();
        vehicle->setCoordinateSystem(0,1,2);world.activeVehicle=vehicle.get();
        const auto& d=tune.dims;float mount=d.bump+.1f,rest=mount-d.droop;
        for(int i=0;i<4;++i){auto hub=tune.straightWheelPath?rally::wheelAnchor(i,d):rally::hubAtTravel(i,d.staticTravel,d);
            auto& w=vehicle->addWheel({hub.x,mount-tune.cgY,hub.z-tune.cgZ},{0,-1,0},{-1,0,0},rest,d.tyreRadius,settings,i<2);
            w.m_suspensionStiffness=(i<2?tune.frontRate:tune.rearRate)/tune.mass;
            w.m_wheelsDampingCompression=tune.compression/tune.mass;w.m_wheelsDampingRelaxation=tune.rebound/tune.mass;
            w.m_maxSuspensionTravelCm=(d.bump-d.droop)*100;w.m_maxSuspensionForce=tune.mass*9.81f*2;
            w.m_frictionSlip=tune.grip;w.m_rollInfluence=1; // Preserve physical contact-height roll torque.
        }
        reset(station);
    }
    void reset(const Station& station){
        btTransform tr;tr.setIdentity();tr.setRotation(btQuaternion({0,1,0},station.yaw));
        Vector3 p(station.x,0,station.z);auto sample=[&](float x,float z){return terrain.height(x,z);};
        auto road=rally::roadPose(p,station.yaw,sample,tune.dims);
        threepp::Quaternion q=rally::chassisOrientation(station.yaw,road.pitch,road.roll);tr.setRotation(btQuaternion(q.x,q.y,q.z,q.w));
        p.y=road.ride+.07f;tr.setOrigin(bt(p)+tr.getBasis()*bt(cg()));
        chassis->setWorldTransform(tr);chassis->setInterpolationWorldTransform(tr);chassis->setLinearVelocity({0,0,0});chassis->setAngularVelocity({0,0,0});chassis->clearForces();
        vehicle->resetSuspension();world.getBroadphase()->getOverlappingPairCache()->cleanProxyFromPairs(chassis->getBroadphaseHandle(),&dispatcher);
        steer=0;throttle=brake=0;boost={};spin.fill(0);time=0;sync();
    }
    void lift(float y){auto t=chassis->getWorldTransform();t.getOrigin().setY(t.getOrigin().y()+y);chassis->setWorldTransform(t);}
    void kick(const Vector3& v){chassis->setLinearVelocity(bt(v));}
    float tyrePenetration(int i){
        const auto& w=vehicle->getWheelInfo(i);auto from=chassis->getWorldTransform()*w.m_chassisConnectionPointCS;
        auto dir=chassis->getWorldTransform().getBasis()*w.m_wheelDirectionCS;
        raycaster->corner=i;raycaster->steering=steer;btVehicleRaycaster::btVehicleRaycasterResult result;
        if(!raycaster->castRay(from,from+dir*(w.getSuspensionRestLength()+w.m_wheelsRadius),result))return 0;
        return std::max(0.f,w.getSuspensionRestLength()-w.m_maxSuspensionTravelCm*.01f-raycaster->requestedLength[i]);
    }
    void tick(float gas,float stop,float turn,bool handbrake=false,bool requestBoost=false){
        throttle=std::clamp(gas,0.f,1.f);brake=std::clamp(stop,0.f,1.f);
        const float target=std::clamp(turn,-1.f,1.f)*.48f/(1+std::abs(speed())*.025f);
        steer+=std::clamp(target-steer,-1.1f*fixedStep,1.1f*fixedStep);
        const float boostFactor=boost.step(requestBoost,handbrake?0:contactCount(),throttle,brake,reverse,fixedStep);
        const float force=tune.driveForce*throttle*boostFactor*(reverse?-1.f:1.f)/(1+std::pow(std::abs(speed())/14.f,2));
        for(int i=0;i<4;++i){
            vehicle->setSteeringValue(i<2?rally::steeringAngle(i,steer,tune.dims):0,i);
            vehicle->applyEngineForce(force*.25f,i); // AWD and a bounded low-range drive force.
            // Bullet brake input is impulse (N*s), not force or torque.
            float drag=std::abs(speed())>.08f?tune.mass*9.81f*.014f*.25f:0;
            float braking=brake*tune.mass*9.81f*.45f+(handbrake&&i>1?tune.mass*9.81f*.5f:0)+drag;
            vehicle->setBrake(braking*fixedStep,i);
        }
        // Directional quadratic drag using RELATIVE air velocity. Apply at a
        // stated pressure-center estimate, so crosswinds can create roll/yaw
        // and tyre load transfer. This is a lumped aero model, not CFD.
        const auto basis=chassis->getWorldTransform().getBasis();
        auto local=basis.transpose()*(chassis->getLinearVelocity()-bt(airVelocity()));
        auto aeroLocal=btVector3(-.6125f*tune.lateralCdA*local.x()*btFabs(local.x()),-.6125f*tune.verticalCdA*local.y()*btFabs(local.y()),-.6125f*tune.frontalCdA*local.z()*btFabs(local.z()));
        auto worldForce=basis*aeroLocal;aerodynamicForce=vec(worldForce);chassis->applyForce(worldForce,basis*btVector3(0,tune.pressureY,tune.pressureZ));
        raycaster->corner=0;raycaster->steering=steer;
        world.stepSimulation(fixedStep,0,fixedStep);time+=fixedStep;sync();
    }
    void sync(){
        const auto inv=chassis->getWorldTransform().inverse();const auto& d=tune.dims;
        for(int i=0;i<4;++i){auto& w=vehicle->getWheelInfo(i);const bool contact=w.m_raycastInfo.m_isInContact;
            vehicle->updateWheelTransform(i,false);w.m_raycastInfo.m_isInContact=contact;
            auto p=inv*w.m_worldTransform.getOrigin()+bt(cg());travel[i]=p.y();load[i]=w.m_raycastInfo.m_isInContact?std::min(w.m_wheelsSuspensionForce,w.m_maxSuspensionForce)+vehicle->stopLoad[i]:0;
            grounded[i]=w.m_raycastInfo.m_isInContact;spin[i]=w.m_rotation;
            contacts[i].local=vec(p);contacts[i].world=vec(w.m_worldTransform.getOrigin());contacts[i].requested=travel[i];
            contacts[i].ground=vec(w.m_raycastInfo.m_contactPointWS);contacts[i].gap=contacts[i].world.y-d.tyreRadius-terrain.height(contacts[i].world.x,contacts[i].world.z);
        }
    }
    int contactCount()const{int n=0;for(bool c:grounded)n+=c;return n;}
};
}
