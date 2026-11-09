Shader "Cinder/Body" {
 Properties { _Color("Colour",Color)=(1,1,1,1) _MainTex("Base",2D)="white"{} _Metallic("Metal",Range(0,1))=0 _Glossiness("Smoothness",Range(0,1))=.5 _MetallicGlossMap("Metal/Smooth",2D)="white"{} _BumpMap("Normal",2D)="bump"{} _BumpScale("Normal strength",Range(0,2))=1 _Cutoff("Cutoff",Range(0,1))=.5 _Cull("Cull",Float)=2 _Clearcoat("Lacquer",Range(0,1))=0 _CoatRoughness("Lacquer roughness",Range(0,1))=.06 _EmissionColor("Emission",Color)=(0,0,0,0) }
 SubShader { Tags {"RenderType"="Opaque"} LOD 250 Cull [_Cull]
 CGPROGRAM
 #pragma surface surf Cinder fullforwardshadows vertex:vert
 #pragma target 3.0
 #pragma shader_feature_local CINDER_CUTOUT
 #pragma shader_feature_local _METALLICGLOSSMAP
 #pragma shader_feature_local _NORMALMAP
 #include "UnityCG.cginc"
 #include "UnityStandardUtils.cginc"
 #include "UnityPBSLighting.cginc"
 half _Clearcoat,_CoatRoughness;
 half4 LightingCinder(SurfaceOutputStandard s,half3 viewDir,UnityGI gi){half4 result=LightingStandard(s,viewDir,gi);if(_Clearcoat>.001){Unity_GlossyEnvironmentData g;g.roughness=_CoatRoughness;g.reflUVW=reflect(-viewDir,s.Normal);UnityIndirect coat;coat.diffuse=0;coat.specular=Unity_GlossyEnvironment(UNITY_PASS_TEXCUBE(unity_SpecCube0),unity_SpecCube0_HDR,g);half4 top=UNITY_BRDF_PBS(half3(0,0,0),half3(.04,.04,.04),.96,1-_CoatRoughness,s.Normal,viewDir,gi.light,coat);half f=.04+.96*Pow5(1-saturate(dot(s.Normal,viewDir)));result.rgb=result.rgb*(1-_Clearcoat*f)+top.rgb*_Clearcoat;}return result;}
 void LightingCinder_GI(SurfaceOutputStandard s,UnityGIInput data,inout UnityGI gi){LightingStandard_GI(s,data,gi);}
 sampler2D _MainTex,_MetallicGlossMap,_BumpMap;fixed4 _Color,_EmissionColor;half _Metallic,_Glossiness,_Cutoff,_BumpScale;
 struct Input {float2 uv_MainTex;fixed4 color:COLOR;};
 void vert(inout appdata_full v,out Input o){UNITY_INITIALIZE_OUTPUT(Input,o);o.color=v.color;}
 void surf(Input IN,inout SurfaceOutputStandard o){fixed4 c=tex2D(_MainTex,IN.uv_MainTex)*_Color; o.Albedo=c.rgb*IN.color.rgb;o.Alpha=c.a;
 #ifdef CINDER_CUTOUT
 clip(c.a-_Cutoff);
 #endif
 o.Metallic=_Metallic;o.Smoothness=_Glossiness;
 #ifdef _METALLICGLOSSMAP
 half4 mr=tex2D(_MetallicGlossMap,IN.uv_MainTex);o.Metallic=mr.r;o.Smoothness=mr.a;
 #endif
 #ifdef _NORMALMAP
 o.Normal=UnpackScaleNormal(tex2D(_BumpMap,IN.uv_MainTex),_BumpScale);
 #endif
 o.Emission=_EmissionColor.rgb; }
 ENDCG
 } FallBack "Standard"
}
