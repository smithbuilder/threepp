Shader "Cinder/Foliage" {
 Properties {_Color("Leaf colour",Color)=(.35,.52,.28,1)}
 SubShader {Tags {"RenderType"="Opaque"} Cull Off Pass {
 CGPROGRAM
 #pragma vertex vert
 #pragma fragment frag
 #include "UnityCG.cginc"
 struct a {float4 vertex:POSITION;float3 normal:NORMAL;float4 color:COLOR;};
 struct v {float4 pos:SV_POSITION;float3 normal:TEXCOORD0;float4 color:COLOR;};
 fixed4 _Color;
 v vert(a i){v o;o.pos=UnityObjectToClipPos(i.vertex);o.normal=UnityObjectToWorldNormal(i.normal);o.color=i.color;return o;}
 fixed4 frag(v i):SV_Target {float light=.58+.42*abs(dot(normalize(i.normal),normalize(float3(-.525,.669,.525))));return float4(_Color.rgb*i.color.rgb*light,1);}
 ENDCG
 }} Fallback Off
}
