Shader "Cinder/ShopGlass" {
 Properties {_Color("Interior tint",Color)=(.2,.29,.33,1)}
 SubShader {Tags {"RenderType"="Opaque"} Cull Off Pass {
 CGPROGRAM
 #pragma vertex vert
 #pragma fragment frag
 #pragma target 3.0
 #include "UnityCG.cginc"
 struct a {float4 vertex:POSITION;float3 normal:NORMAL;};struct v {float4 pos:SV_POSITION;float3 normal:TEXCOORD0;float3 world:TEXCOORD1;};fixed4 _Color;
 v vert(a i){v o;o.pos=UnityObjectToClipPos(i.vertex);o.world=mul(unity_ObjectToWorld,i.vertex).xyz;o.normal=UnityObjectToWorldNormal(i.normal);return o;}
 fixed4 frag(v i):SV_Target {float3 view=normalize(_WorldSpaceCameraPos-i.world),n=normalize(i.normal);n=faceforward(n,-view,n);half4 sample=UNITY_SAMPLE_TEXCUBE_LOD(unity_SpecCube0,reflect(-view,n),1.5);float3 environment=min(DecodeHDR(sample,unity_SpecCube0_HDR),float3(2,2,2));float fresnel=.16+.62*pow(1-saturate(dot(n,view)),5);return float4(lerp(_Color.rgb*.22,environment*.4,fresnel),1);}
 ENDCG
 }} FallBack Off
}
