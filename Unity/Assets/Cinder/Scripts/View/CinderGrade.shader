Shader "Cinder/Grade" {
 Properties {_MainTex("Source",2D)="white"{}}
 SubShader {Cull Off ZWrite Off ZTest Always
 Pass {
 CGPROGRAM
 #pragma vertex vert_img
 #pragma fragment grade
 #pragma target 3.0
 #include "UnityCG.cginc"
 sampler2D _MainTex;
 float3 NativeTone(float3 c){c=max(0,c)*(.98/.6);c=mul(float3x3(.59719,.35458,.04823,.076,.90834,.01566,.0284,.13383,.83777),c);c=(c*(c+.0245786)-.000090537)/(c*(.983729*c+.4329510)+.238081);return saturate(mul(float3x3(1.60475,-.53108,-.07367,-.10208,1.10813,-.00605,-.00327,-.07276,1.07602),c));}
 float4 grade(v2f_img i):SV_Target {return float4(LinearToGammaSpace(NativeTone(tex2D(_MainTex,i.uv).rgb)),1);}
 ENDCG
 }
 Pass {
 CGPROGRAM
 #pragma vertex vert_img
 #pragma fragment filtered
 #pragma target 3.0
 #include "UnityCG.cginc"
 sampler2D _MainTex;float4 _MainTex_TexelSize;
 #include "CinderFxaa.cginc"
 float4 filtered(v2f_img i):SV_Target {float3 display=ApplyFXAA(_MainTex,abs(_MainTex_TexelSize.xy),i.uv).rgb;return float4(GammaToLinearSpace(display),1);}
 ENDCG
 }
 } Fallback Off
}
