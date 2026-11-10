Shader "Cinder/CityFoliage" {
 Properties {
  _Color("Leaf colour",Color)=(1,1,1,1) _MainTex("Cutout leaves",2D)="white"{}
  _Metallic("Metal",Range(0,1))=0 _Glossiness("Smoothness",Range(0,1))=.07
  _Roughness("Roughness factor",Range(0,1))=.93 _RoughnessMap("Roughness data",2D)="white"{}
  _HasRoughnessMap("Use roughness map",Float)=0 _BumpMap("Normal",2D)="bump"{}
  _BumpScale("Normal strength",Float)=1 _EmissionColor("Emission",Color)=(0,0,0,0)
  _Cutoff("Cutoff",Range(0,1))=.36 _Cull("Cull",Float)=0
 }
 SubShader {Tags {"RenderType"="TransparentCutout" "Queue"="AlphaTest"} Cull Off
 CGPROGRAM
 #pragma surface surf Standard fullforwardshadows vertex:vert alphatest:_Cutoff addshadow
 #pragma target 3.0
 sampler2D _MainTex;fixed4 _Color;half _Glossiness;
 struct Input {float2 uv_MainTex;fixed4 color:COLOR;float facing:VFACE;};
 void vert(inout appdata_full v,out Input o){UNITY_INITIALIZE_OUTPUT(Input,o);o.color=v.color;}
 void surf(Input IN,inout SurfaceOutputStandard o){fixed4 c=tex2D(_MainTex,IN.uv_MainTex)*_Color;o.Albedo=c.rgb*IN.color.rgb;o.Alpha=c.a;o.Normal=float3(0,0,IN.facing>=0?1:-1);o.Metallic=0;o.Smoothness=_Glossiness;o.Occlusion=1;}
 ENDCG
 } FallBack "Transparent/Cutout/Diffuse"
}
