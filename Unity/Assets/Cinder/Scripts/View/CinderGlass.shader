Shader "Cinder/Glass" {
 Properties {_Color("Tint",Color)=(.6,.7,.7,.12) _Glossiness("Smoothness",Range(0,1))=.93 _MainTex("Base",2D)="white"{} _Metallic("Metal",Range(0,1))=0 _BumpMap("Normal",2D)="bump"{} _BumpScale("Normal strength",Float)=1}
 SubShader {Tags {"Queue"="Transparent" "RenderType"="Transparent"} Cull Off ZWrite Off Blend SrcAlpha OneMinusSrcAlpha
 Pass { CGPROGRAM
 #pragma vertex vert
 #pragma fragment frag
 #pragma target 3.0
 #include "UnityCG.cginc"
 struct appdata {float4 vertex:POSITION;float3 normal:NORMAL;float2 uv:TEXCOORD0;};
 struct v2f {float4 pos:SV_POSITION;float3 world:TEXCOORD0;float3 normal:TEXCOORD1;float2 uv:TEXCOORD2;};
 fixed4 _Color;half _Glossiness;sampler2D _MainTex;
 v2f vert(appdata v){v2f o;o.pos=UnityObjectToClipPos(v.vertex);o.world=mul(unity_ObjectToWorld,v.vertex).xyz;o.normal=UnityObjectToWorldNormal(v.normal);o.uv=v.uv;return o;}
 fixed4 frag(v2f i):SV_Target {float3 n=normalize(i.normal),v=normalize(_WorldSpaceCameraPos-i.world);n=faceforward(n,-v,n);float3 reflection=reflect(-v,n);half4 sample=UNITY_SAMPLE_TEXCUBE_LOD(unity_SpecCube0,reflection,(1-_Glossiness)*6);float3 environment=min(DecodeHDR(sample,unity_SpecCube0_HDR),float3(2,2,2));float fresnel=pow(1-saturate(dot(n,v)),5);fixed4 tint=tex2D(_MainTex,i.uv)*_Color;return float4(lerp(tint.rgb,environment,.22+.35*fresnel),tint.a);}
 ENDCG }
 } FallBack Off
}
