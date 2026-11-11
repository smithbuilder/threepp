Shader "Cinder/Grade" {
 Properties {_MainTex("Source",2D)="white"{}}
 CGINCLUDE
 #include "UnityCG.cginc"
 sampler2D _MainTex,_BloomTex,_NearBloom;
 float4 _MainTex_TexelSize;float _BloomStrength,_DitherStrength;
 // Uniform scalar extraction and radiance cap preserve each source's hue.
 // Suppress ordinary lit surfaces; soft knee admits HDR glints without popping.
 float3 Bright(float3 c){c=max(0,c);float peak=max(c.r,max(c.g,c.b));float knee=clamp(peak-1.2+.6,0,1.2);knee=knee*knee/(2.4+.00001);float weight=max(peak-1.2,knee)/max(peak,.00001);return c*weight*min(1,16/max(peak,.00001));}
 float3 Tent(float2 uv){float2 d=abs(_MainTex_TexelSize.xy);float3 c=tex2D(_MainTex,uv).rgb*4;
 c+=(tex2D(_MainTex,uv+float2(d.x,0)).rgb+tex2D(_MainTex,uv-float2(d.x,0)).rgb+tex2D(_MainTex,uv+float2(0,d.y)).rgb+tex2D(_MainTex,uv-float2(0,d.y)).rgb)*2;
 c+=tex2D(_MainTex,uv+d).rgb+tex2D(_MainTex,uv-d).rgb+tex2D(_MainTex,uv+float2(d.x,-d.y)).rgb+tex2D(_MainTex,uv+float2(-d.x,d.y)).rgb;return c/16;}
 ENDCG
 SubShader {Cull Off ZWrite Off ZTest Always
 Pass {
 CGPROGRAM
 #pragma vertex vert_img
 #pragma fragment grade
 #pragma target 3.0
 float3 NativeTone(float3 c){c=max(0,c)*(.98/.6);c=mul(float3x3(.59719,.35458,.04823,.076,.90834,.01566,.0284,.13383,.83777),c);c=(c*(c+.0245786)-.000090537)/(c*(.983729*c+.4329510)+.238081);return saturate(mul(float3x3(1.60475,-.53108,-.07367,-.10208,1.10813,-.00605,-.00327,-.07276,1.07602),c));}
 float4 grade(v2f_img i):SV_Target {return float4(LinearToGammaSpace(NativeTone(tex2D(_MainTex,i.uv).rgb+tex2D(_BloomTex,i.uv).rgb*_BloomStrength)),1);}
 ENDCG
 }
 Pass {
 CGPROGRAM
 #pragma vertex vert_img
 #pragma fragment filtered
 #pragma target 3.0
 #include "CinderFxaa.cginc"
 float4 filtered(v2f_img i):SV_Target {float3 display=ApplyFXAA(_MainTex,abs(_MainTex_TexelSize.xy),i.uv).rgb;
 // Two independent static hashes give zero-mean triangular noise, bounded to
 // half one display byte. Screen-anchored noise avoids temporal grain/shimmer.
 float2 p=floor(i.pos.xy);float a=frac(52.9829189*frac(dot(p,float2(.06711056,.00583715))));float b=frac(52.9829189*frac(dot(p+float2(17,59),float2(.06711056,.00583715))));
 display=saturate(display+(a+b-1)*_DitherStrength);return float4(GammaToLinearSpace(display),1);}
 ENDCG
 }
 Pass {
 CGPROGRAM
 #pragma vertex vert_img
 #pragma fragment prefilter
 #pragma target 3.0
 float4 prefilter(v2f_img i):SV_Target {float2 d=abs(_MainTex_TexelSize.xy)*.5;return float4((Bright(tex2D(_MainTex,i.uv+d).rgb)+Bright(tex2D(_MainTex,i.uv-d).rgb)+Bright(tex2D(_MainTex,i.uv+float2(d.x,-d.y)).rgb)+Bright(tex2D(_MainTex,i.uv+float2(-d.x,d.y)).rgb))*.25,1);}
 ENDCG
 }
 Pass {
 CGPROGRAM
 #pragma vertex vert_img
 #pragma fragment downsample
 #pragma target 3.0
 float4 downsample(v2f_img i):SV_Target {return float4(Tent(i.uv),1);}
 ENDCG
 }
 Pass {
 CGPROGRAM
 #pragma vertex vert_img
 #pragma fragment upsample
 #pragma target 3.0
 float4 upsample(v2f_img i):SV_Target {return float4(lerp(tex2D(_NearBloom,i.uv).rgb,Tent(i.uv),.65),1);}
 ENDCG
 }
 } Fallback Off
}
