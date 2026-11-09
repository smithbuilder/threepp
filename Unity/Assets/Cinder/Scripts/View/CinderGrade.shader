Shader "Cinder/Grade" {
 Properties {_MainTex("Source",2D)="white"{}}
 SubShader {Cull Off ZWrite Off ZTest Always Pass {
 CGPROGRAM
 #pragma vertex vert_img
 #pragma fragment frag
 #include "UnityCG.cginc"
 sampler2D _MainTex;float4 _MainTex_TexelSize;
 float3 tone(float2 uv){float3 c=tex2D(_MainTex,uv).rgb*.98;return saturate((c*(2.51*c+.03))/(c*(2.43*c+.59)+.14));}
 fixed4 frag(v2f_img i):SV_Target {float2 px=abs(_MainTex_TexelSize.xy);float3 m=tone(i.uv),nw=tone(i.uv+px*float2(-1,-1)),ne=tone(i.uv+px*float2(1,-1)),sw=tone(i.uv+px*float2(-1,1)),se=tone(i.uv+px*float2(1,1));float3 weights=float3(.299,.587,.114);float lm=dot(m,weights),lnw=dot(nw,weights),lne=dot(ne,weights),lsw=dot(sw,weights),lse=dot(se,weights);float lo=min(lm,min(min(lnw,lne),min(lsw,lse))),hi=max(lm,max(max(lnw,lne),max(lsw,lse)));if(hi-lo<max(.025,hi*.125))return float4(m,1);float2 direction=float2(-((lnw+lne)-(lsw+lse)),(lnw+lsw)-(lne+lse));float reduce=max((lnw+lne+lsw+lse)*.03125,.0078125);direction=clamp(direction/(min(abs(direction.x),abs(direction.y))+reduce),-8,8)*px;float3 a=.5*(tone(i.uv+direction*(-.1666667))+tone(i.uv+direction*.1666667));float3 b=a*.5+.25*(tone(i.uv-direction*.5)+tone(i.uv+direction*.5));float lb=dot(b,weights);return float4(lb<lo||lb>hi?a:b,1);}
 ENDCG
 }} Fallback Off
}
