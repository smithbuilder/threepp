Shader "Cinder/Body" {
 Properties { _Color("Colour",Color)=(1,1,1,1) _MainTex("Base",2D)="white"{} _Metallic("Metal",Range(0,1))=0 _Glossiness("Smoothness",Range(0,1))=.5 _MetallicGlossMap("Metal/Smooth",2D)="white"{} _BumpMap("Normal",2D)="bump"{} _BumpScale("Normal strength",Range(0,2))=1 _Cutoff("Cutoff",Range(0,1))=.5 _Cull("Cull",Float)=2 _Clearcoat("Lacquer",Range(0,1))=0 _CoatRoughness("Lacquer roughness",Range(0,1))=.06 _EmissionColor("Emission",Color)=(0,0,0,0) }
 SubShader { Tags {"RenderType"="Opaque"} LOD 250 Cull [_Cull]
 CGPROGRAM
 #pragma surface surf Cinder fullforwardshadows vertex:vert addshadow
 #pragma target 3.0
 #pragma shader_feature_local CINDER_CUTOUT
 #pragma shader_feature_local _METALLICGLOSSMAP
 #pragma shader_feature_local _NORMALMAP
 #include "UnityCG.cginc"
 #include "UnityStandardUtils.cginc"
 #include "UnityPBSLighting.cginc"
 half _Clearcoat,_CoatRoughness;float _CinderMaterialDiagnostic;
 struct SurfaceOutputCinder {fixed3 Albedo;float3 Normal;half3 Emission;half Metallic;half Smoothness;half Occlusion;fixed Alpha;float3 CoatNormal;float3 WorldPosition;};
 SurfaceOutputStandard BaseSurface(SurfaceOutputCinder s){SurfaceOutputStandard b=(SurfaceOutputStandard)0;b.Albedo=s.Albedo;b.Normal=normalize(s.Normal);b.Emission=s.Emission;b.Metallic=s.Metallic;b.Smoothness=s.Smoothness;b.Occlusion=s.Occlusion;b.Alpha=s.Alpha;return b;}
 // Screen-space normal variance filters subpixel highlights without changing the
 // donor roughness on broad, stable surfaces. The clear layer uses the smooth
 // authored shell normal, independently of the base paint's flake normal map.
 half FilterSmoothness(half smoothness,float3 n){float3 dx=ddx(n),dy=ddy(n);float variance=min(.12,.5*(dot(dx,dx)+dot(dy,dy)));half roughness=1-smoothness;return 1-sqrt(saturate(roughness*roughness+variance));}
 half4 LightingCinder(SurfaceOutputCinder s,half3 viewDir,UnityGI gi){SurfaceOutputStandard b=BaseSurface(s);b.Smoothness=FilterSmoothness(b.Smoothness,b.Normal);half4 result=LightingStandard(b,viewDir,gi);if(_Clearcoat>.001){float3 n=normalize(s.CoatNormal);half smoothness=FilterSmoothness(1-_CoatRoughness,n);Unity_GlossyEnvironmentData g=(Unity_GlossyEnvironmentData)0;g.roughness=1-smoothness;g.reflUVW=reflect(-viewDir,n);
 #if UNITY_SPECCUBE_BOX_PROJECTION
 g.reflUVW=BoxProjectedCubemapDirection(g.reflUVW,s.WorldPosition,unity_SpecCube0_ProbePosition,unity_SpecCube0_BoxMin,unity_SpecCube0_BoxMax);
 #endif
 UnityIndirect coat=(UnityIndirect)0;coat.diffuse=0;coat.specular=Unity_GlossyEnvironment(UNITY_PASS_TEXCUBE(unity_SpecCube0),unity_SpecCube0_HDR,g);
 // Capture-only controls expose the actual GPU lookup before tone mapping.
 if(_CinderMaterialDiagnostic==1)return half4(g.reflUVW*.5+.5,1);
 if(_CinderMaterialDiagnostic==2)return half4(n*.5+.5,1);
 if(_CinderMaterialDiagnostic==3)return half4(DecodeHDR(UNITY_SAMPLE_TEXCUBE_LOD(unity_SpecCube0,g.reflUVW,0),unity_SpecCube0_HDR),1);
 if(_CinderMaterialDiagnostic==4)return half4(coat.specular,1);
 if(_CinderMaterialDiagnostic==5)return half4(unity_SpecCube0_HDR.x,unity_SpecCube0_HDR.y,unity_SpecCube0_HDR.w,1);
 if(_CinderMaterialDiagnostic==7)return half4(_LightColor0.rgb,1);
 if(_CinderMaterialDiagnostic==6){UnityLight dark=(UnityLight)0;dark.color=0;dark.dir=gi.light.dir;coat.specular=1;return UNITY_BRDF_PBS(half3(0,0,0),half3(.04,.04,.04),.96,smoothness,n,viewDir,dark,coat);}
 half4 top=UNITY_BRDF_PBS(half3(0,0,0),half3(.04,.04,.04),.96,smoothness,n,viewDir,gi.light,coat);half f=.04+.96*Pow5(1-saturate(dot(n,viewDir)));result.rgb=result.rgb*(1-_Clearcoat*f)+top.rgb*_Clearcoat;}return result;}
 void LightingCinder_GI(SurfaceOutputCinder s,UnityGIInput data,inout UnityGI gi){SurfaceOutputStandard b=BaseSurface(s);b.Smoothness=FilterSmoothness(b.Smoothness,b.Normal);LightingStandard_GI(b,data,gi);}
 sampler2D _MainTex,_MetallicGlossMap,_BumpMap;fixed4 _Color,_EmissionColor;half _Metallic,_Glossiness,_Cutoff,_BumpScale;
 struct Input {float2 uv_MainTex;fixed4 color:COLOR;float3 worldNormal;float3 worldPos;INTERNAL_DATA};
 void vert(inout appdata_full v,out Input o){UNITY_INITIALIZE_OUTPUT(Input,o);o.color=v.color;}
 void surf(Input IN,inout SurfaceOutputCinder o){fixed4 c=tex2D(_MainTex,IN.uv_MainTex)*_Color; o.Albedo=c.rgb*IN.color.rgb;o.Alpha=c.a;o.Occlusion=1;
 // Always declare the tangent-space normal output. Surface-shader variants
 // without a normal map still need the tangent frame for the world-space coat.
 o.Normal=float3(0,0,1);o.CoatNormal=WorldNormalVector(IN,float3(0,0,1));o.WorldPosition=IN.worldPos;
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
