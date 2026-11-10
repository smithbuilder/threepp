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
 sampler2D _MainTex,_BumpMap,_RoughnessMap;fixed4 _Color;half3 _EmissionColor;half _Metallic,_Glossiness,_Roughness,_HasRoughnessMap,_BumpScale,_Cutoff;
 struct Input {float2 uv_MainTex;fixed4 color:COLOR;};
 void vert(inout appdata_full v,out Input o){UNITY_INITIALIZE_OUTPUT(Input,o);o.color=v.color;}
 void surf(Input IN,inout SurfaceOutputStandard o){fixed4 c=tex2D(_MainTex,IN.uv_MainTex)*_Color;
 #ifdef CINDER_CUTOUT
 clip(c.a-_Cutoff);
 #endif
 o.Albedo=c.rgb*IN.color.rgb;o.Alpha=c.a;o.Metallic=_Metallic;o.Smoothness=_HasRoughnessMap>.5?1-saturate(_Roughness*tex2D(_RoughnessMap,IN.uv_MainTex).g):_Glossiness;
 #ifdef _NORMALMAP
 o.Normal=UnpackScaleNormal(tex2D(_BumpMap,IN.uv_MainTex),_BumpScale);
 #endif
 o.Occlusion=1;o.Emission=_EmissionColor;}
 ENDCG
 } FallBack "Standard"
}
