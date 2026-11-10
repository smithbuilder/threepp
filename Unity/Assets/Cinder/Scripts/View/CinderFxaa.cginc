// Display-space FXAA from this repository's three.js r186 / NVIDIA implementation.
// Original: include/threepp/postprocessing/shaders/FXAAShader.hpp.
// HLSL translation only; native thresholds, edge search and subpixel blend retained.
#define EDGE_STEP_COUNT 6
#define EDGE_GUESS 8.0
#define EDGE_STEPS 1.0, 1.5, 2.0, 2.0, 2.0, 4.0
static const float edgeSteps[EDGE_STEP_COUNT] = { EDGE_STEPS };

const float _ContrastThreshold = 0.0312;
const float _RelativeThreshold = 0.063;
const float _SubpixelBlending = 1.0;

float4 Sample( sampler2D sourceTexture, float2 uv ) {
    return tex2Dlod( sourceTexture, float4(uv,0,0) );
}

float SampleLuminance( sampler2D sourceTexture, float2 uv ) {
    return dot( Sample( sourceTexture, uv ).rgb, float3( 0.3, 0.59, 0.11 ) );
}

float SampleLuminance( sampler2D sourceTexture, float2 texSize, float2 uv, float uOffset, float vOffset ) {
    uv += texSize * float2( uOffset, vOffset );
    return SampleLuminance( sourceTexture, uv );
}

struct LuminanceData {
    float m, n, e, s, w;
    float ne, nw, se, sw;
    float highest, lowest, contrast;
};

LuminanceData SampleLuminanceNeighborhood( sampler2D sourceTexture, float2 texSize, float2 uv ) {
    LuminanceData l=(LuminanceData)0;
    l.m = SampleLuminance( sourceTexture, uv );
    l.n = SampleLuminance( sourceTexture, texSize, uv,  0.0,  1.0 );
    l.e = SampleLuminance( sourceTexture, texSize, uv,  1.0,  0.0 );
    l.s = SampleLuminance( sourceTexture, texSize, uv,  0.0, -1.0 );
    l.w = SampleLuminance( sourceTexture, texSize, uv, -1.0,  0.0 );

    l.ne = SampleLuminance( sourceTexture, texSize, uv,  1.0,  1.0 );
    l.nw = SampleLuminance( sourceTexture, texSize, uv, -1.0,  1.0 );
    l.se = SampleLuminance( sourceTexture, texSize, uv,  1.0, -1.0 );
    l.sw = SampleLuminance( sourceTexture, texSize, uv, -1.0, -1.0 );

    l.highest = max( max( max( max( l.n, l.e ), l.s ), l.w ), l.m );
    l.lowest = min( min( min( min( l.n, l.e ), l.s ), l.w ), l.m );
    l.contrast = l.highest - l.lowest;
    return l;
}

bool ShouldSkipPixel( LuminanceData l ) {
    float threshold = max( _ContrastThreshold, _RelativeThreshold * l.highest );
    return l.contrast < threshold;
}

float DeterminePixelBlendFactor( LuminanceData l ) {
    float f = 2.0 * ( l.n + l.e + l.s + l.w );
    f += l.ne + l.nw + l.se + l.sw;
    f *= 1.0 / 12.0;
    f = abs( f - l.m );
    f = clamp( f / l.contrast, 0.0, 1.0 );

    float blendFactor = smoothstep( 0.0, 1.0, f );
    return blendFactor * blendFactor * _SubpixelBlending;
}

struct EdgeData {
    bool isHorizontal;
    float pixelStep;
    float oppositeLuminance, gradient;
};

EdgeData DetermineEdge( float2 texSize, LuminanceData l ) {
    EdgeData e=(EdgeData)0;
    float horizontal =
        abs( l.n + l.s - 2.0 * l.m ) * 2.0 +
        abs( l.ne + l.se - 2.0 * l.e ) +
        abs( l.nw + l.sw - 2.0 * l.w );
    float vertical =
        abs( l.e + l.w - 2.0 * l.m ) * 2.0 +
        abs( l.ne + l.nw - 2.0 * l.n ) +
        abs( l.se + l.sw - 2.0 * l.s );
    e.isHorizontal = horizontal >= vertical;

    float pLuminance = e.isHorizontal ? l.n : l.e;
    float nLuminance = e.isHorizontal ? l.s : l.w;
    float pGradient = abs( pLuminance - l.m );
    float nGradient = abs( nLuminance - l.m );

    e.pixelStep = e.isHorizontal ? texSize.y : texSize.x;

    if ( pGradient < nGradient ) {
        e.pixelStep = -e.pixelStep;
        e.oppositeLuminance = nLuminance;
        e.gradient = nGradient;
    } else {
        e.oppositeLuminance = pLuminance;
        e.gradient = pGradient;
    }

    return e;
}

float DetermineEdgeBlendFactor( sampler2D sourceTexture, float2 texSize, LuminanceData l, EdgeData e, float2 uv ) {
    float2 uvEdge = uv;
    float2 edgeStep=float2(0,0);
    if ( e.isHorizontal ) {
        uvEdge.y += e.pixelStep * 0.5;
        edgeStep = float2( texSize.x, 0.0 );
    } else {
        uvEdge.x += e.pixelStep * 0.5;
        edgeStep = float2( 0.0, texSize.y );
    }

    float edgeLuminance = ( l.m + e.oppositeLuminance ) * 0.5;
    float gradientThreshold = e.gradient * 0.25;

    float2 puv = uvEdge + edgeStep * edgeSteps[0];
    float pLuminanceDelta = SampleLuminance( sourceTexture, puv ) - edgeLuminance;
    bool pAtEnd = abs( pLuminanceDelta ) >= gradientThreshold;

    for ( int pIndex = 1; pIndex < EDGE_STEP_COUNT && !pAtEnd; pIndex++ ) {
        puv += edgeStep * edgeSteps[pIndex];
        pLuminanceDelta = SampleLuminance( sourceTexture, puv ) - edgeLuminance;
        pAtEnd = abs( pLuminanceDelta ) >= gradientThreshold;
    }

    if ( !pAtEnd ) {
        puv += edgeStep * EDGE_GUESS;
    }

    float2 nuv = uvEdge - edgeStep * edgeSteps[0];
    float nLuminanceDelta = SampleLuminance( sourceTexture, nuv ) - edgeLuminance;
    bool nAtEnd = abs( nLuminanceDelta ) >= gradientThreshold;

    for ( int nIndex = 1; nIndex < EDGE_STEP_COUNT && !nAtEnd; nIndex++ ) {
        nuv -= edgeStep * edgeSteps[nIndex];
        nLuminanceDelta = SampleLuminance( sourceTexture, nuv ) - edgeLuminance;
        nAtEnd = abs( nLuminanceDelta ) >= gradientThreshold;
    }

    if ( !nAtEnd ) {
        nuv -= edgeStep * EDGE_GUESS;
    }

    float pDistance=0, nDistance=0;
    if ( e.isHorizontal ) {
        pDistance = puv.x - uv.x;
        nDistance = uv.x - nuv.x;
    } else {
        pDistance = puv.y - uv.y;
        nDistance = uv.y - nuv.y;
    }

    float shortestDistance=0;
    bool deltaSign=false;
    if ( pDistance <= nDistance ) {
        shortestDistance = pDistance;
        deltaSign = pLuminanceDelta >= 0.0;
    } else {
        shortestDistance = nDistance;
        deltaSign = nLuminanceDelta >= 0.0;
    }

    if ( deltaSign == ( l.m - edgeLuminance >= 0.0 ) ) {
        return 0.0;
    }

    return 0.5 - shortestDistance / ( pDistance + nDistance );
}

float4 ApplyFXAA( sampler2D sourceTexture, float2 texSize, float2 uv ) {
    LuminanceData luminance = SampleLuminanceNeighborhood( sourceTexture, texSize, uv );
    if ( ShouldSkipPixel( luminance ) ) {
        return Sample( sourceTexture, uv );
    }

    float pixelBlend = DeterminePixelBlendFactor( luminance );
    EdgeData edge = DetermineEdge( texSize, luminance );
    float edgeBlend = DetermineEdgeBlendFactor( sourceTexture, texSize, luminance, edge, uv );
    float finalBlend = max( pixelBlend, edgeBlend );

    if ( edge.isHorizontal ) {
        uv.y += edge.pixelStep * finalBlend;
    } else {
        uv.x += edge.pixelStep * finalBlend;
    }

    return Sample( sourceTexture, uv );
}

