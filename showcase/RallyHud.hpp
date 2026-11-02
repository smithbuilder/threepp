#pragma once
#include <imgui.h>
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <string>

namespace rally {
struct HudState {
    float width=960,height=600,speed=0,rpm=1050,time=0,best=0,progress=0,heading=0,x=0,z=0,nextDistance=0;
    int gear=1,next=1;
    bool inspection=false,scripted=false,finished=false,muted=true,menu=false;
};
inline std::string raceTime(float time) {
    char s[32];int ms=static_cast<int>(std::max(0.f,time)*1000);
    std::snprintf(s,sizeof(s),"%02d:%02d.%03d",ms/60000,(ms/1000)%60,ms%1000);return s;
}
// One restrained offset shadow keeps solid floating glyphs legible without
// outlining their interiors. No rectangular backing or scene veil is used.
inline void hudText(ImDrawList* d,ImFont* font,float x,float y,float size,ImU32 color,const std::string& value) {
    const ImU32 shadow=IM_COL32(7,13,11,205);
    d->AddText(font,size,ImVec2(x+.65f,y+1.2f),shadow,value.c_str());
    d->AddText(font,size,ImVec2(x,y),color,value.c_str());
}
inline void drawHud(const HudState& s,ImFont* font) {
    auto* d=ImGui::GetBackgroundDrawList();
    constexpr ImU32 ink=IM_COL32(246,244,233,255),quiet=IM_COL32(223,226,216,240),gold=IM_COL32(226,193,116,255),green=IM_COL32(187,213,190,255),edge=IM_COL32(9,18,15,150);
    auto text=[&](float x,float y,float size,ImU32 c,const std::string& v){hudText(d,font,x,y,size,c,v);};
    text(32,26,25,ink,"CINDER FOREST");text(32,55,14,quiet,s.inspection?"VEHICLE INSPECTION":"GRAVEL SPRINT  /  LAP 01 OF 01");
    if(s.scripted)text(s.width*.5f-102,15,13,quiet,s.inspection?"NATIVE ENGINE / INSPECTION COURT":"SCRIPTED GAMEPLAY / AUDIO REBUILT");
    if(s.menu)return;
    for(int i=0;i<8;++i){const bool done=s.finished||i<(s.next==0?7:s.next-1),active=!s.finished&&i==(s.next==0?7:s.next-1);float x=32+i*22.f;
        d->AddLine(ImVec2(x,82),ImVec2(x+15,82),edge,4);d->AddLine(ImVec2(x,82),ImVec2(x+15,82),done?green:active?gold:IM_COL32(232,236,222,95),2);}
    const float tx=s.width-200;text(tx,27,14,quiet,"LAP TIME");text(tx-2,46,36,ink,raceTime(s.time));
    text(tx,87,14,quiet,"BEST  "+(s.best>0?raceTime(s.best):std::string("--:--.---")));
    char distance[40];std::snprintf(distance,sizeof(distance),"%03.0f m",s.nextDistance);
    text(s.width*.5f-66,51,16,quiet,"NEXT CHECKPOINT");text(s.width*.5f-35,72,24,ink,distance);
    float px=s.width*.5f-96,py=s.height-30;
    d->AddLine(ImVec2(px,py),ImVec2(px+192,py),edge,4);d->AddLine(ImVec2(px,py),ImVec2(px+192,py),IM_COL32(240,241,230,105),1);
    d->AddLine(ImVec2(px,py),ImVec2(px+192*std::clamp(s.progress,0.f,1.f),py),gold,1.5f);
    text(px,py-21,13,quiet,"CHECKPOINT "+std::to_string(s.next==0?8:s.next)+" / 8");
    if(!s.scripted)text(px+123,py-21,13,quiet,s.muted?"M SOUND OFF":"M SOUND ON");
    const float cx=99,cy=s.height-89;
    auto point=[&](float x,float z){return ImVec2(cx+x*.55f,cy-z*.55f);};
    for(int i=0;i<100;++i){float a=i*6.2831853f/100,b=(i+1)*6.2831853f/100;
        auto p=point(64*std::sin(a)+8*std::sin(3*a),90*std::cos(a));auto q=point(64*std::sin(b)+8*std::sin(3*b),90*std::cos(b));
        d->AddLine(p,q,edge,4);d->AddLine(p,q,IM_COL32(233,235,220,230),1.5f);}
    for(int i=0;i<8;++i){float a=i*6.2831853f/8;auto p=point(64*std::sin(a)+8*std::sin(3*a),90*std::cos(a));d->AddCircleFilled(p,3.8f,edge);d->AddCircleFilled(p,2.2f,i==s.next?gold:quiet);}
    auto p=point(s.x,s.z);float fx=std::sin(s.heading),fy=-std::cos(s.heading);
    ImVec2 a(p.x+fx*8,p.y+fy*8),b(p.x-fx*4-fy*4,p.y-fy*4+fx*4),c(p.x-fx*4+fy*4,p.y-fy*4-fx*4);
    d->AddTriangleFilled(a,b,c,gold);d->AddTriangle(a,b,c,edge,1.2f);
    const float gx=s.width-119,gy=s.height-70,radius=66;
    for(int i=0;i<30;++i){float a=(140+260*i/29.f)*3.14159265f/180,r=radius+(i%5==0?3:0);
        const auto color=i/29.f<s.rpm/7500.f?(i>26?gold:ink):IM_COL32(237,239,226,100);
        auto p=ImVec2(gx+std::cos(a)*r,gy+std::sin(a)*r),q=ImVec2(gx+std::cos(a)*(r-6),gy+std::sin(a)*(r-6));
        d->AddLine(p,q,edge,3);d->AddLine(p,q,color,i%5==0?1.7f:1.f);}
    char speed[16],rpm[20];std::snprintf(speed,sizeof(speed),"%03.0f",std::abs(s.speed)*3.6f);std::snprintf(rpm,sizeof(rpm),"%04.0f RPM",s.rpm);
    text(gx-44,gy-49,53,ink,speed);text(gx-17,gy+1,13,quiet,"KM/H");text(gx-30,gy+23,13,quiet,rpm);
    text(gx+42,gy-29,28,ink,s.speed<-.5f?"R":std::to_string(s.gear));text(gx+35,gy+2,11,quiet,"GEAR");
}
}
