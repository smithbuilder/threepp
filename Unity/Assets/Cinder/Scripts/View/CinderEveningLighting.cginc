#ifndef CINDER_EVENING_LIGHTING
#define CINDER_EVENING_LIGHTING
#include "UnityPBSLighting.cginc"
float4 _CinderStreetLamps[8];
float4 _CinderLampColour,_CinderLampUp;
float _CinderLampsEnabled,_CinderLampScale;
// Fixed authored fixtures, evaluated in the existing forward base pass. This is
// direct PBR radiance, not a road decal or emissive wash. Static city visibility
// is baked per vertex; moving-car/bench occlusion is not shadow mapped.
half3 CinderPractical(half3 albedo,half metallic,half smoothness,float3 normal,float3 viewDir,float3 world,float4 visibility0,float4 visibility1){
 half3 result=0;
 #if !defined(UNITY_PASS_FORWARDADD) && !defined(UNITY_PASS_SHADOWCASTER) && !defined(UNITY_PASS_META)
 if(_CinderLampsEnabled>.5){
  half oneMinus;half3 specular;half3 diffuse=DiffuseAndSpecularFromMetallic(albedo,metallic,specular,oneMinus);
  UnityIndirect indirect=(UnityIndirect)0;
  [unroll]for(int k=0;k<8;k++){
   float3 ray=_CinderStreetLamps[k].xyz-world;float d2=dot(ray,ray);
   float scaleSquared=_CinderLampScale*_CinderLampScale;float rangeSquared=256*scaleSquared;
   if(d2<rangeSquared&&d2>.01*scaleSquared){
    float3 l=ray*rsqrt(d2);float cone=smoothstep(.56,.80,dot(l,_CinderLampUp.xyz));
    float edge=saturate(1-d2/rangeSquared);int channel=k%4;float visibility=k<4?visibility0[channel]:visibility1[channel];
    UnityLight lamp=(UnityLight)0;lamp.dir=l;lamp.color=_CinderLampColour.rgb*(_CinderStreetLamps[k].w*cone*edge*edge/max(d2,scaleSquared))*visibility;
    result+=UNITY_BRDF_PBS(diffuse,specular,oneMinus,smoothness,normalize(normal),normalize(viewDir),lamp,indirect).rgb;
   }
  }
 }
 #endif
 return result;
}
struct SurfaceOutputEveningStandard {fixed3 Albedo;float3 Normal;half3 Emission;half Metallic;half Smoothness;half Occlusion;fixed Alpha;float3 WorldPosition;float4 LampVisibility0;float4 LampVisibility1;};
SurfaceOutputStandard EveningBase(SurfaceOutputEveningStandard s){SurfaceOutputStandard b=(SurfaceOutputStandard)0;b.Albedo=s.Albedo;b.Normal=s.Normal;b.Emission=s.Emission;b.Metallic=s.Metallic;b.Smoothness=s.Smoothness;b.Occlusion=s.Occlusion;b.Alpha=s.Alpha;return b;}
half4 LightingEveningStandard(SurfaceOutputEveningStandard s,half3 viewDir,UnityGI gi){half4 c=LightingStandard(EveningBase(s),viewDir,gi);c.rgb+=CinderPractical(s.Albedo,s.Metallic,s.Smoothness,s.Normal,viewDir,s.WorldPosition,s.LampVisibility0,s.LampVisibility1);return c;}
void LightingEveningStandard_GI(SurfaceOutputEveningStandard s,UnityGIInput data,inout UnityGI gi){LightingStandard_GI(EveningBase(s),data,gi);}
#endif
