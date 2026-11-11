Shader "Cinder/City" {
 Properties {
  _Color("Linear source colour",Color)=(1,1,1,1) _MainTex("Albedo",2D)="white"{}
  _Metallic("Metal",Range(0,1))=0 _Glossiness("Smoothness",Range(0,1))=.1
  _Roughness("Roughness factor",Range(0,1))=.9 _RoughnessMap("Roughness data",2D)="white"{}
  _HasRoughnessMap("Use roughness map",Float)=0 _BumpMap("Normal",2D)="bump"{}
  _BumpScale("Normal strength",Float)=1 _EmissionColor("Emission",Color)=(0,0,0,0)
  _Cutoff("Cutoff",Range(0,1))=.36 _Cull("Cull",Float)=2
 }
 SubShader { Tags {"RenderType"="Opaque"} Cull [_Cull]
 CGPROGRAM
 #pragma surface surf Standard fullforwardshadows vertex:vert
 #pragma target 3.0
 #pragma shader_feature_local CINDER_CUTOUT
 #pragma shader_feature_local _NORMALMAP
 #include "UnityStandardUtils.cginc"
 float _CinderContactEnabled;float4x4 _CinderWorldToModule;float4 _CinderContacts[4],_CinderContactAxes[4];
 sampler2D _MainTex,_BumpMap,_RoughnessMap;fixed4 _Color;half3 _EmissionColor;half _Metallic,_Glossiness,_Roughness,_HasRoughnessMap,_BumpScale,_Cutoff;
 struct Input {float2 uv_MainTex;fixed4 color:COLOR;float3 worldPos;float3 worldNormal;INTERNAL_DATA};
 void vert(inout appdata_full v,out Input o){UNITY_INITIALIZE_OUTPUT(Input,o);o.color=v.color;}
 void surf(Input IN,inout SurfaceOutputStandard o){fixed4 c=tex2D(_MainTex,IN.uv_MainTex)*_Color;
 #ifdef CINDER_CUTOUT
 clip(c.a-_Cutoff);
 #endif
 o.Albedo=c.rgb*IN.color.rgb;o.Alpha=c.a;o.Metallic=_Metallic;o.Smoothness=_HasRoughnessMap>.5?1-saturate(_Roughness*tex2D(_RoughnessMap,IN.uv_MainTex).g):_Glossiness;o.Normal=float3(0,0,1);
 #ifdef _NORMALMAP
 o.Normal=UnpackScaleNormal(tex2D(_BumpMap,IN.uv_MainTex),_BumpScale);
 #endif
 o.Occlusion=1;
 if(_CinderContactEnabled>.5){
  float3 p=mul(_CinderWorldToModule,float4(IN.worldPos,1)).xyz;
  float up=saturate(normalize(mul((float3x3)_CinderWorldToModule,WorldNormalVector(IN,float3(0,0,1)))).y);
  float shade=0;
  [unroll]for(int k=0;k<4;k++){
   float3 d=p-_CinderContacts[k].xyz;float2 axis=_CinderContactAxes[k].xy;
   float2 q=float2(dot(d.xz,float2(axis.y,-axis.x)),dot(d.xz,axis))/max(_CinderContactAxes[k].zw,.001);
   float footprint=saturate(1-dot(q,q));footprint*=footprint;
   float height=1-smoothstep(.025,.09,abs(d.y));
   shade=max(shade,footprint*height*_CinderContacts[k].w);
  }
  // Standard's occlusion attenuates indirect light, leaving direct car shadows
  // and the frozen city vertex shade intact. Maximum indirect reduction is 45%.
  o.Occlusion=1-.45*shade*up;
 }
 o.Emission=_EmissionColor;}
 ENDCG
 } FallBack "Standard"
}
