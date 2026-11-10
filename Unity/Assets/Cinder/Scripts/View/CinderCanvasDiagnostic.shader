Shader "Hidden/Cinder/CanvasDiagnostic" {
 SubShader {Tags {"RenderType"="Opaque"} Cull Off ZWrite On
 Pass {CGPROGRAM
 #pragma vertex vert
 #pragma fragment frag
 #include "UnityCG.cginc"
 float4 vert(float4 vertex:POSITION):SV_POSITION{return UnityObjectToClipPos(vertex);}
 float4 frag():SV_Target{return float4(1,0,1,1);}
 ENDCG}
 } Fallback Off
}
