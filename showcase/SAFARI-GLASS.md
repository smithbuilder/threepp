# Safari thin glass

`RallyThinGlass.hpp` opts named Safari materials into a thin dielectric
approximation: smoky panes, clear lamp covers, rear optical covers and the
two inner clear prism interfaces. Other
materials retain their shader branch and blend state. Standard glTF alpha
settings remain in the asset as a fallback for other viewers.

The rally composer already renders scene geometry into linear HalfFloat
targets before its tone-mapping OutputPass. The glass uses the existing PBR
specular lobe, which already contains Fresnel, without multiplying it again
by alpha. Custom `One / OneMinusSrcAlpha` blending combines that reflection
with the opaque scene behind the pane. No new render target, pass, texture,
screen-space transmission or refraction sampling is introduced.

For normal/view cosine `c`, the Schlick approximation is
`F=.04+.96*(1-c)^5`, and background transmission is `(1-F)*T`.
The stored alpha is `1-(1-F)*T`. Bulk `T=.96` gives normal background
transmission `.9216` for lamp covers; smoky panes use bulk `.90`.
Inner headlamp/rear prism interfaces use bulk1.0, so the outer surface owns
the glass slab's absorption once. At normal incidence the first-order
two-interface reflection is `.076864`, with background `.884736` and the
remaining `.0384` absorbed. The source reflection at either interface is not
attenuated by the standard alpha-blend opacity a second time.
Fog contribution is weighted by source alpha to avoid adding a second bright
fog layer over an already-fogged background.

Material defines participate in the renderer's program key. Shader insertion
is guarded by the existing PBR/fog anchors and occurs once in this single-threaded
game setup. The engine library's source files are not modified. Cover depth
tests remain enabled; transparent panes do not write depth or cast opaque
depth-map shadows. Body panes and inner prism interfaces remain viewable from
both sides: exterior observers see the back-facing internal interfaces.
Outer optical covers are front-sided. Window roughness is `.18`; continuous
surface normals avoid the previous separate centre-fan reflection seam.

CPU checks cover normal/grazing limits, ideal bounded energy, fog compositing
and ordinary-paint isolation. An independent source review found no blocking
GLSL/cache/blend issue. Supervised960x600 native captures compiled and rendered
the shader successfully, starting with session20261103-021042-110 and the
subsequent front/side/rear/detail views. This establishes native execution;
the whole-car visual gate remains a separate assessment.

This is thin, non-refracting glass with scalar absorption. Rear chamber tint
is authored in its inner materials. It does not model spectral filtering,
multiple internal optical bounces or volumetric lens focusing.
