Shader "Cinder/Canvas" {
 Properties {
  _Color("Authored fabric colour",Color)=(.16,.1647,.17255,1)
  _MainTex("Fabric base",2D)="white"{}
  _Metallic("Metal",Range(0,1))=0
  _Glossiness("Smoothness",Range(0,1))=.03
  _Cull("Native double-sided rule",Float)=0
  _Clearcoat("Lacquer compatibility",Range(0,1))=0
  _CoatRoughness("Lacquer roughness compatibility",Range(0,1))=0
 }
 SubShader {
  Tags {"RenderType"="Opaque" "Queue"="Geometry"}
  Cull Off
  CGPROGRAM
  #pragma surface surf EveningStandard fullforwardshadows addshadow
  #pragma target 3.0
  #include "CinderEveningLighting.cginc"
  sampler2D _MainTex;
  fixed4 _Color;
  half _Metallic,_Glossiness;
  struct Input {float2 uv_MainTex;float3 worldPos;float facing:VFACE;};
  void surf(Input IN,inout SurfaceOutputEveningStandard o){
   o.WorldPosition=IN.worldPos;o.LampVisibility0=1;o.LampVisibility1=1;
   fixed4 fabric=tex2D(_MainTex,IN.uv_MainTex)*_Color;
   o.Albedo=fabric.rgb;o.Alpha=fabric.a;
   o.Normal=float3(0,0,IN.facing>=0?1:-1);
   o.Metallic=_Metallic;o.Smoothness=_Glossiness;o.Occlusion=1;
  }
  ENDCG
 }
 FallBack Off
}
