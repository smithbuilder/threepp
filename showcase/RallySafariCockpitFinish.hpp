#pragma once
#include "RallyCockpit.hpp"
#include "threepp/extras/core/Shape.hpp"
#include "threepp/geometries/ExtrudeGeometry.hpp"
#include <map>
#include <stdexcept>
#include <tuple>

namespace rally {
namespace safari_cockpit_detail {

inline void require(bool ok,const std::string& reason){
    if(!ok)throw std::runtime_error("Safari cockpit finish: "+reason);
}
inline bool near(float a,float b){return std::abs(a-b)<1e-6f;}
inline bool at(const Object3D& o,float x,float y,float z){
    return near(o.position.x,x)&&near(o.position.y,y)&&near(o.position.z,z)
        &&near(o.scale.x,1)&&near(o.scale.y,1)&&near(o.scale.z,1);
}
inline bool bounds(BufferGeometry& g,Vector3 min,Vector3 max){
    g.computeBoundingBox();return g.boundingBox&&g.boundingBox->min().distanceToSquared(min)<1e-12f
        &&g.boundingBox->max().distanceToSquared(max)<1e-12f;
}
struct Layout {
    Object3D* root;
    Object3D* rpm;
    Object3D* speed;
    Mesh* dash;
};
// Fail closed rather than finishing a different vehicle or silently breaking an
// animation parent. These are the original addCockpit(-.25,-.025) coordinates.
inline Layout layout(Cockpit& c,bool pristine){
    require(c.steering&&c.rpmNeedle&&c.speedNeedle,"missing animation handle");
    auto* rpm=c.rpmNeedle->parent;auto* speed=c.speedNeedle->parent;
    require(rpm&&speed&&rpm!=speed&&rpm->parent&&rpm->parent==speed->parent,"gauge parents changed");
    auto* root=rpm->parent;auto* column=c.steering->parent;
    require(column&&column->parent==root,"steering column parent changed");
    require(at(*root,0,-.25f,0)&&near(root->rotation.x,0)&&near(root->rotation.y,0)&&near(root->rotation.z,0),"Safari root placement changed");
    require(at(*rpm,-.51f,1.44f,.413f)&&at(*speed,-.29f,1.44f,.413f)
        &&near(rpm->rotation.y,pi)&&near(speed->rotation.y,pi)
        &&near(rpm->rotation.x,0)&&near(speed->rotation.x,0)
        &&near(rpm->rotation.z,0)&&near(speed->rotation.z,0),"gauge placement changed");
    require(at(*column,-.4f,1.28f,.25f)&&near(column->rotation.x,.28f)
        &&near(column->rotation.y,0)&&near(column->rotation.z,0),"steering column placement changed");
    require(at(*c.steering,0,0,0)&&at(*c.rpmNeedle,0,0,0)&&at(*c.speedNeedle,0,0,0),"animation pivot moved");
    require(root->children.size()>=5,"cockpit furniture missing");
    auto* dash=dynamic_cast<Mesh*>(root->children[0]);
    require(dash&&at(*dash,0,1.34f,.54f)&&dash->geometry()->type()=="BoxGeometry","dashboard topology changed");
    if(pristine){
        require(root->children.size()==5&&c.steering->children.size()==5,"cockpit already finished or topology changed");
        for(auto* dial:{rpm,speed}){
            require(dial->children.size()==15,"original gauge topology changed");
            const char* expected[]={"CylinderGeometry","CircleGeometry","TorusGeometry"};
            for(unsigned i=0;i<3;++i){auto* m=dynamic_cast<Mesh*>(dial->children[i]);
                require(m&&m->geometry()->type()==expected[i],"original gauge components changed");}
            auto* housing=dynamic_cast<Mesh*>(dial->children[0]);auto* face=dynamic_cast<Mesh*>(dial->children[1]);
            auto* rim=dynamic_cast<Mesh*>(dial->children[2]);
            require(at(*housing,0,0,-.03f)&&near(housing->rotation.x,pi/2)
                &&bounds(*housing->geometry(),{-.091f,-.025f,-.091f},{.091f,.025f,.091f})
                &&at(*face,0,0,0)&&bounds(*face->geometry(),{-.085f,-.085f,0},{.085f,.085f,0})
                &&at(*rim,0,0,0)&&bounds(*rim->geometry(),{-.093f,-.093f,-.006f*std::sin(pi/3)},{.093f,.093f,.006f*std::sin(pi/3)}),"original gauge geometry envelope changed");
            for(unsigned i=3;i<14;++i){auto* m=dynamic_cast<Mesh*>(dial->children[i]);
                require(m&&m->geometry()->type()=="BoxGeometry","original gauge ticks changed");}
        }
        require(rpm->children.back()==c.rpmNeedle.get()&&speed->children.back()==c.speedNeedle.get(),"needle binding changed");
        require(c.rpmNeedle->children.size()==1&&c.speedNeedle->children.size()==1,"needle geometry changed");
        for(auto* pointer:{c.rpmNeedle.get(),c.speedNeedle.get()}){
            auto* bar=dynamic_cast<Mesh*>(pointer->children[0]);
            require(bar&&bar->geometry()->type()=="BoxGeometry"&&at(*bar,0,.026f,.006f)
                &&bounds(*bar->geometry(),{-.003f,-.0295f,-.002f},{.003f,.0295f,.002f}),"original needle bar changed");
        }
        for(unsigned i=0;i<5;++i)require(dynamic_cast<Mesh*>(c.steering->children[i]),"original wheel topology changed");
    }
    return {root,rpm,speed,dash};
}
inline std::size_t triangles(const BufferGeometry& g){
    return (g.getIndex()?g.getIndex()->count():g.getAttribute<float>("position")->count())/3;
}
inline std::size_t triangles(Object3D& root){
    std::size_t n=0;root.traverseType<Mesh>([&](Mesh& m){n+=triangles(*m.geometry());});return n;
}
inline std::shared_ptr<Mesh> mesh(Object3D& root,const std::string& name,
        std::shared_ptr<BufferGeometry> g,std::shared_ptr<Material> m,bool closed=false){
    auto o=Mesh::create(std::move(g),std::move(m));o->name="safari.cockpit."+name;
    o->userData["safari.cockpit.closed"]=closed;root.add(o);return o;
}
inline auto basic(unsigned color){auto m=MeshBasicMaterial::create();m->color=Color(color);return m;}
inline void uvScale(BufferGeometry& g,float u,float v){
    auto* uv=g.getAttribute<float>("uv");if(!uv)return;
    for(unsigned i=0;i<uv->count();++i)uv->setXY(i,uv->getX(i)*u,uv->getY(i)*v);
}
inline auto cylinder(float radius,float depth,unsigned segments,float z){
    auto g=CylinderGeometry::create(radius,radius,depth,segments);
    g->rotateX(pi/2).translate(0,0,z);return g;
}

// All dial lettering, calibration and stitching are real, front-facing mesh
// marks. One batch per colour/parent; no canvas, atlas, texture or extra pass.
struct Ink {
    std::vector<float> p,n,uv;
    float front=1;
    explicit Ink(float front=1):front(front){}
    void triangle(Vector3 a,Vector3 b,Vector3 c){
        float area=(b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x);
        if(std::abs(area)<1e-13f)return;
        if(area*front<0)std::swap(b,c);
        for(const auto& v:{a,b,c}){p.insert(p.end(),{v.x,v.y,v.z});n.insert(n.end(),{0,0,front});uv.insert(uv.end(),{0,0});}
    }
    void quad(Vector3 a,Vector3 b,Vector3 c,Vector3 d){triangle(a,b,c);triangle(a,c,d);}
    void rect(float x,float y,float w,float h,float z,float a=0){
        auto point=[&](float dx,float dy){return Vector3(x+dx*std::cos(a)-dy*std::sin(a),y+dx*std::sin(a)+dy*std::cos(a),z);};
        quad(point(-w/2,-h/2),point(w/2,-h/2),point(w/2,h/2),point(-w/2,h/2));
    }
    void arc(float inner,float outer,float begin,float end,float z,unsigned segments){
        auto point=[&](float r,float a){return Vector3(r*std::sin(a),r*std::cos(a),z);};
        for(unsigned i=0;i<segments;++i){float a=begin+(end-begin)*i/segments,b=begin+(end-begin)*(i+1)/segments;
            quad(point(inner,a),point(outer,a),point(outer,b),point(inner,b));}
    }
    void text(const std::string& text,float size,float x,float y,float z){
        auto g=TextGeometry::create(text,TextGeometry::Options(FontLoader{}.defaultFont(),size,1));g->center();
        auto* v=g->getAttribute<float>("position");const auto* index=g->getIndex();
        auto point=[&](unsigned i){if(index)i=index->getX(i);return Vector3(x+front*v->getX(i),y+v->getY(i),z);};
        unsigned count=index?index->count():v->count();
        for(unsigned i=0;i<count;i+=3)triangle(point(i),point(i+1),point(i+2));
    }
    std::shared_ptr<BufferGeometry> geometry(){
        auto g=BufferGeometry::create();g->setAttribute("position",FloatBufferAttribute::create(p,3));
        g->setAttribute("normal",FloatBufferAttribute::create(n,3));g->setAttribute("uv",FloatBufferAttribute::create(uv,2));return g;
    }
};
inline auto merge(const std::vector<std::shared_ptr<BufferGeometry>>& parts){
    auto g=mergeBufferGeometries(parts);require(static_cast<bool>(g),"cannot batch geometry");return g;
}

inline void finishDial(Object3D& dial,Group& needle,const std::string& name,bool rpm,
        const std::shared_ptr<Material>& casing,const std::shared_ptr<Material>& face,
        const std::shared_ptr<Material>& alloy,const std::shared_ptr<Material>& ivory,
        const std::shared_ptr<Material>& red,const std::shared_ptr<Material>& dark){
    auto* housing=dynamic_cast<Mesh*>(dial.children[0]);auto* print=dynamic_cast<Mesh*>(dial.children[1]);
    auto* rim=dynamic_cast<Mesh*>(dial.children[2]);
    housing->setMaterial(casing);housing->name="safari.cockpit."+name+".housing";
    housing->userData["safari.cockpit.closed"]=true;
    print->setMaterial(face);print->name="safari.cockpit."+name+".face";
    // Same .087/.006 torus and six tube samples as stock. Only the azimuth
    // changes 24 -> 48: <= .093*(1-cos(pi/24)) = .796mm chord inflation.
    rim->setGeometry(TorusGeometry::create(.087f,.006f,6,48));rim->setMaterial(alloy);
    rim->name="safari.cockpit."+name+".bezel";rim->userData["safari.cockpit.closed"]=true;
    std::vector<Object3D*> oldTicks(dial.children.begin()+3,dial.children.begin()+14);
    for(auto* tick:oldTicks)dial.remove(*tick);
    Ink white,warning;
    int divisions=rpm?30:24; // 250 rpm / 5 km/h; matches updateCockpit exactly.
    for(int i=0;i<=divisions;++i){
        float fraction=static_cast<float>(i)/divisions,a=(-125+250*fraction)*pi/180;
        bool major=i%4==0;float length=major?.010f:.0048f;
        auto& ink=(rpm&&i>=26)?warning:white;float radius=.077f-length/2;
        ink.rect(std::sin(a)*radius,std::cos(a)*radius,major?.0019f:.00085f,length,.00085f,-a);
    }
    for(int i=0;i<=(rpm?7:6);++i){
        float value=rpm?static_cast<float>(i):i*20.f,max=rpm?7.5f:120.f;
        float a=(-125+250*value/max)*pi/180;
        auto& ink=(rpm&&i==7)?warning:white;
        ink.text(std::to_string(rpm?i:i*20),rpm?.0115f:.0102f,std::sin(a)*.052f,std::cos(a)*.052f,.0009f);
    }
    if(rpm){
        warning.arc(.078f,.080f,(-125+250*6.5f/7.5f)*pi/180,125*pi/180,.0009f,10);
        white.text("RPM",.0055f,0,-.019f,.0009f);
        white.text("x1000",.0053f,0,-.029f,.0009f);
    }else{
        white.text("km/h",.0065f,0,-.022f,.0009f);
        white.text("001107",.0052f,0,-.044f,.0009f);
        white.rect(0,-.051f,.035f,.00055f,.0009f);
    }
    mesh(dial,name+".calibration.ink",white.geometry(),ivory);
    if(!warning.p.empty())mesh(dial,name+".redline.ink",warning.geometry(),red);

    // Preserve the actual animated group and its original bar object. A tapered
    // counterweighted blade and its collet remain at/below the old z=.008 face.
    auto* bar=dynamic_cast<Mesh*>(needle.children[0]);require(bar,"needle bar is not a mesh");
    Shape blade;blade.moveTo(-.0026f,-.010f).lineTo(.0026f,-.010f)
        .lineTo(.0011f,.054f).lineTo(0,.056f).lineTo(-.0011f,.054f).lineTo(-.0026f,-.010f);
    ExtrudeGeometry::Options opt;opt.depth=.0022f;opt.steps=1;opt.curveSegments=1;opt.bevelEnabled=false;
    auto g=ExtrudeGeometry::create({blade},opt);g->translate(0,0,.0045f);
    bar->setGeometry(g);bar->position.set(0,0,0);bar->setMaterial(red);
    bar->name="safari.cockpit."+name+".needle";bar->userData["safari.cockpit.closed"]=true;
    mesh(needle,name+".collet",cylinder(.009f,.0028f,12,.0066f),alloy,true);
    mesh(needle,name+".collet_cap",cylinder(.0056f,.001f,8,.0075f),dark,true);
    needle.name="safari.cockpit."+name+".animation";
}
} // namespace safari_cockpit_detail

// Safari-only trim. Call immediately after addCockpit and BEFORE collecting
// fixedMeshes. Nothing here changes the eye, parents, transforms or update path.
inline void finishSafariCockpit(Cockpit& c){
    using namespace safari_cockpit_detail;
    auto l=layout(c,true);auto baseline=triangles(*l.root);
    auto leather=surfaceMaterial(0x151915,Surface::Rubber,.84f,0);leather->normalScale.setScalar(.075f);
    leather->name="safari.cockpit.leather";
    auto dashLeather=surfaceMaterial(0x1c211c,Surface::Rubber,.92f,0);dashLeather->normalScale.setScalar(.055f);
    dashLeather->name="safari.cockpit.dashboard_grain";
    auto alloy=surfaceMaterial(0x959c94,Surface::Metal,.40f,.82f);alloy->normalScale.setScalar(.04f);
    alloy->name="safari.cockpit.satin_alloy";
    auto casing=surfaceMaterial(0x20251f,Surface::Paint,.75f,.05f);casing->name="safari.cockpit.casing";
    auto dialFace=MeshStandardMaterial::create();dialFace->color=Color(0x101610);dialFace->roughness=.86f;
    auto dark=surfaceMaterial(0x151a15,Surface::Paint,.70f,.08f);
    auto ivory=basic(0xdedac4),red=basic(0xd65335),black=basic(0x0c100d),thread=basic(0x55594b);
    l.dash->setMaterial(dashLeather);l.dash->name="safari.cockpit.dashboard";
    l.dash->userData["safari.cockpit.closed"]=true;
    // Project this Safari-only box at eight tiles/metre: the cached 64-cycle
    // grain is ~2mm, rather than a 20mm pebble pattern. Texture.repeat is shared
    // and stays untouched. The geometry itself has the exact old box vertices.
    auto dashGeometry=BoxGeometry::create(1.30f,.14f,.18f);
    auto* dp=dashGeometry->getAttribute<float>("position");auto* dn=dashGeometry->getAttribute<float>("normal");
    auto* duv=dashGeometry->getAttribute<float>("uv");
    for(unsigned i=0;i<dp->count();++i){
        float nx=std::abs(dn->getX(i)),ny=std::abs(dn->getY(i)),nz=std::abs(dn->getZ(i));
        if(nz>=nx&&nz>=ny)duv->setXY(i,dp->getX(i)*8,dp->getY(i)*8);
        else if(ny>=nx)duv->setXY(i,dp->getX(i)*8,dp->getZ(i)*8);
        else duv->setXY(i,dp->getZ(i)*8,dp->getY(i)*8);
    }
    l.dash->setGeometry(dashGeometry);
    finishDial(*l.rpm,*c.rpmNeedle,"rpm",true,casing,dialFace,alloy,ivory,red,dark);
    finishDial(*l.speed,*c.speedNeedle,"speed",false,casing,dialFace,alloy,ivory,red,dark);

    auto* rim=dynamic_cast<Mesh*>(c.steering->children[0]);auto* hub=dynamic_cast<Mesh*>(c.steering->children[4]);
    auto wheelGeometry=TorusGeometry::create(.185f,.018f,12,48);uvScale(*wheelGeometry,8,1);
    rim->setGeometry(wheelGeometry);rim->setMaterial(leather);rim->name="safari.cockpit.wheel.rim";
    rim->userData["safari.cockpit.closed"]=true;
    std::vector<Object3D*> oldSpokes(c.steering->children.begin()+1,c.steering->children.begin()+4);
    for(auto* spoke:oldSpokes)c.steering->remove(*spoke);
    std::vector<std::shared_ptr<BufferGeometry>> spokes,hardware;
    for(int i=0;i<3;++i){
        Shape shape;shape.moveTo(-.015f,.030f).lineTo(.015f,.030f).lineTo(.021f,.174f)
            .lineTo(-.021f,.174f).lineTo(-.015f,.030f);
        for(float y:{.078f,.128f}){auto hole=std::make_shared<Path>();hole->absellipse(0,y,.0065f,.009f,0,2*pi,true);shape.holes.push_back(hole);}
        ExtrudeGeometry::Options opt;opt.depth=.0035f;opt.steps=1;opt.curveSegments=4;opt.bevelEnabled=false;
        auto g=ExtrudeGeometry::create({shape},opt);auto* p=g->getAttribute<float>("position");
        for(unsigned j=0;j<p->count();++j)p->setZ(j,p->getZ(j)-.020f+.023f*p->getY(j)/.174f);
        g->computeVertexNormals();g->rotateZ(pi+i*2*pi/3);spokes.push_back(g);
    }
    mesh(*c.steering,"wheel.drilled_spokes",merge(spokes),alloy,true);
    hub->setGeometry(CylinderGeometry::create(.044f,.044f,.042f,24));hub->position.z=.002f;
    hub->setMaterial(dark);hub->name="safari.cockpit.wheel.hub";hub->userData["safari.cockpit.closed"]=true;
    mesh(*c.steering,"wheel.horn_pad",cylinder(.0275f,.006f,16,-.0215f),leather,true);
    Ink wheelMarks(-1),stitches(-1);
    for(int i=0;i<6;++i){float a=i*pi/3,x=.035f*std::sin(a),y=.035f*std::cos(a);
        auto g=cylinder(.0033f,.005f,6,-.0215f);g->translate(x,y,0);hardware.push_back(g);
        wheelMarks.rect(x,y,.0035f,.00055f,-.0242f,a);
    }
    mesh(*c.steering,"wheel.fixings",merge(hardware),alloy,true);
    wheelMarks.text("C",.009f,0,0,-.0247f);
    mesh(*c.steering,"wheel.horn_and_fixing_marks.ink",wheelMarks.geometry(),black);
    // A fine seam follows the actual driver-facing crown. 0.2..0.3mm clearance
    // over the 12-sided tube surface, inside the old wheel cylinder.
    for(int i=0;i<48;++i){float a=i*2*pi/48;
        stitches.rect(.185f*std::sin(a),.185f*std::cos(a),.0027f,.00055f,-.0182f,-a);
    }
    mesh(*c.steering,"wheel.stitching.ink",stitches.geometry(),thread);
    c.steering->name="safari.cockpit.wheel.animation";

    // Existing box: x +/- .65, y 1.27..1.41, z .45.. .63. Every added
    // dashboard detail is inside that footprint; maximum face relief is 1.8mm.
    std::vector<std::shared_ptr<BufferGeometry>> dashMetal,dashDark;
    auto trim=BoxGeometry::create(1.242f,.004f,.0014f);trim->translate(0,1.323f,.4494f);dashMetal.push_back(trim);
    for(float x:{-.050f,.005f,.060f}){
        auto g=cylinder(.009f,.0013f,12,.44935f);g->translate(x,1.300f,0);dashMetal.push_back(g);
        auto cap=cylinder(.0064f,.0007f,12,.44855f);cap->translate(x,1.300f,0);dashDark.push_back(cap);
    }
    mesh(*l.root,"dashboard.satin_trim",merge(dashMetal),alloy,true);
    mesh(*l.root,"dashboard.switch_caps",merge(dashDark),dark,true);
    Ink dashInk(-1),dashFine(-1);
    // Recessed vent/speaker marks, plus the leather seam: no floating boxes.
    for(int row=0;row<5;++row)dashInk.rect(.295f,1.351f+row*.006f,.220f,.002f,.4489f);
    for(int i=0;i<3;++i)dashInk.rect(.220f+i*.075f,1.363f,.0015f,.029f,.4488f);
    dashFine.rect(0,1.390f,1.235f,.00065f,.4489f);
    dashFine.text("LIGHTS",.004f,-.050f,1.283f,.4486f);
    dashFine.text("WIPER",.004f,.005f,1.283f,.4486f);
    dashFine.text("FAN",.004f,.060f,1.283f,.4486f);
    mesh(*l.root,"dashboard.vents.ink",dashInk.geometry(),black);
    mesh(*l.root,"dashboard.seam_and_switch_labels.ink",dashFine.geometry(),thread);
    l.root->userData["safari.cockpit.baseline_triangles"]=baseline;
}

struct SafariCockpitFinishValidation {
    std::size_t meshes=0,triangles=0,supplementalTriangles=0,closedMeshes=0;
    // Original 24-gon gauge silhouette vs the new 48-gon, in metres. Tube
    // coordinates/depth, housing, face, root and needle front limit are fixed.
    float gaugeSilhouetteInflation=.093f*(1-std::cos(pi/24));
    float dashboardFaceRelief=0;
};

// CPU recipe for RallyVehicle_test:
//   Group body; auto c=addCockpit(body,-.25f,-.025f);
//   finishSafariCockpit(c); auto proof=validateSafariCockpitFinish(c);
// Checks all changed/new mesh vertices and normals, welded physical closure,
// finite triangle indices, principal envelopes and both live needle bindings.
// Animation poses are restored even when validation throws. No renderer needed.
inline SafariCockpitFinishValidation validateSafariCockpitFinish(Cockpit& c){
    using namespace safari_cockpit_detail;
    auto l=layout(c,false);SafariCockpitFinishValidation proof;
    require(l.root->userData.contains("safari.cockpit.baseline_triangles"),"finish was not applied");
    auto baseline=std::any_cast<std::size_t>(l.root->userData.at("safari.cockpit.baseline_triangles"));
    require(c.rpmNeedle->name=="safari.cockpit.rpm.animation"&&c.speedNeedle->name=="safari.cockpit.speed.animation"
        &&c.steering->name=="safari.cockpit.wheel.animation","animation handles no longer refer to finished meshes");
    struct Restore {
        Cockpit& c;float steering,rpm,speed;
        ~Restore(){c.steering->rotation.z=steering;c.rpmNeedle->rotation.z=rpm;c.speedNeedle->rotation.z=speed;}
    } restore{c,c.steering->rotation.z,c.rpmNeedle->rotation.z,c.speedNeedle->rotation.z};
    c.steering->rotation.z=0;c.rpmNeedle->rotation.z=0;c.speedNeedle->rotation.z=0;
    l.root->updateWorldMatrix(true,true);
    l.root->traverseType<Mesh>([&](Mesh& m){
        if(!m.name.starts_with("safari.cockpit."))return;
        ++proof.meshes;auto g=m.geometry();auto* p=g->getAttribute<float>("position");auto* n=g->getAttribute<float>("normal");
        require(p&&n&&p->count()==n->count(),m.name+" missing positions/normals");
        Object3D* domain=l.root;
        for(Object3D* ancestor=&m;ancestor;ancestor=ancestor->parent){
            if(ancestor==l.rpm||ancestor==l.speed||ancestor==c.steering.get()){domain=ancestor;break;}}
        Matrix4 transform=*domain->matrixWorld;transform.invert();transform.multiply(*m.matrixWorld);
        for(unsigned i=0;i<p->count();++i){
            auto v=Vector3(p->getX(i),p->getY(i),p->getZ(i));float length=Vector3(n->getX(i),n->getY(i),n->getZ(i)).length();
            require(std::isfinite(v.x)&&std::isfinite(v.y)&&std::isfinite(v.z)&&std::isfinite(length)&&std::abs(length-1)<.002f,m.name+" non-finite geometry or non-unit normal");
            v.applyMatrix4(transform);float r=std::hypot(v.x,v.y);
            if(domain==l.rpm||domain==l.speed)
                require(r<=.093001f&&v.z>=-.055001f&&v.z<=.008001f,m.name+" exceeds original gauge envelope");
            else if(domain==c.steering.get())
                require(r<=.203001f&&v.z>=-.025001f&&v.z<=.025001f,m.name+" exceeds original wheel envelope");
            else{
                require(std::abs(v.x)<=.650001f&&v.y>=1.269999f&&v.y<=1.410001f&&v.z>=.447999f&&v.z<=.630001f,m.name+" exceeds original dashboard plus 2mm face relief");
                proof.dashboardFaceRelief=std::max(proof.dashboardFaceRelief,.45f-v.z);
            }
        }
        const auto* index=g->getIndex();unsigned count=index?index->count():p->count();
        require(count%3==0,m.name+" incomplete triangles");
        using Vertex=std::tuple<long long,long long,long long>;
        using Edge=std::pair<Vertex,Vertex>;std::map<Edge,unsigned> edges;
        bool closed=m.userData.contains("safari.cockpit.closed")&&std::any_cast<bool>(m.userData.at("safari.cockpit.closed"));
        auto vertex=[&](unsigned i){if(index)i=index->getX(i);require(i<p->count(),m.name+" invalid triangle index");
            return Vector3(p->getX(i),p->getY(i),p->getZ(i));};
        auto key=[](const Vector3& v){return Vertex(std::llround(v.x*1e5),std::llround(v.y*1e5),std::llround(v.z*1e5));};
        for(unsigned i=0;i<count;i+=3){
            auto a=vertex(i),b=vertex(i+1),d=vertex(i+2);
            require(b.clone().sub(a).cross(d.clone().sub(a)).lengthSq()>1e-20f,m.name+" degenerate triangle");
            if(closed){Vertex v[]={key(a),key(b),key(d)};
                for(int e=0;e<3;++e){auto a=v[e],b=v[(e+1)%3];if(b<a)std::swap(a,b);++edges[{a,b}];}}
        }
        if(closed){for(const auto& [_,uses]:edges)require(uses==2,m.name+" physical mesh is not closed");++proof.closedMeshes;}
    });
    proof.triangles=triangles(*l.root);require(proof.triangles>=baseline,"unexpected triangle accounting");
    proof.supplementalTriangles=proof.triangles-baseline;
    require(proof.supplementalTriangles<=3000,"supplemental triangle budget exceeds 3000");
    require(proof.gaugeSilhouetteInflation<.0008f,"gauge silhouette exceeds 0.8mm guard");
    for(float fraction:{0.f,.5f,1.f}){
        updateCockpit(c,.31f,fraction*120.f/3.6f,fraction*7500.f);
        float angle=(125-250*fraction)*pi/180;
        require(near(c.rpmNeedle->rotation.z,angle)&&near(c.speedNeedle->rotation.z,angle)
            &&near(c.steering->rotation.z,-.31f*2.2f),"animation calibration/binding changed");
        require(c.rpmNeedle->getObjectByName<Mesh>("safari.cockpit.rpm.needle")
            &&c.speedNeedle->getObjectByName<Mesh>("safari.cockpit.speed.needle"),"animated blade detached");
    }
    return proof;
}
} // namespace rally
