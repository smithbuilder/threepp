Shader "Cinder/Grade" {
 Properties {_MainTex("Source",2D)="white"{}}
 SubShader {Cull Off ZWrite Off ZTest Always Pass {
 CGPROGRAM
 #pragma vertex vert_img
 #pragma fragment frag
 #include "UnityCG.cginc"
 sampler2D _MainTex;
 fixed4 frag(v2f_img i):SV_Target {float3 c=tex2D(_MainTex,i.uv).rgb*.98;float3 mapped=(c*(2.51*c+.03))/(c*(2.43*c+.59)+.14);return float4(saturate(mapped),1);}
 ENDCG
 }} Fallback Off
}
