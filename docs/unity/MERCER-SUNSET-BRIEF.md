# Mercer: early evening light

November 11, 2026, Pacific. Oliver requested: "can you push the lighting quality of the city? make it like 6pm, not dark yet. street lights are starting to come on, nice sunset colors in the sky, better lighting all around."

The existing city keeps its geometry, shops, materials, cars and driving rules. This is a lighting profile refinement, not a new stop or racing mode. Aim for a visible sky/environment change: peach/coral near the low sun, rose/lavender across the horizon, cool blue above. Warm sun-facing planes and cool readable shade must preserve Catrina's magenta/lace, Luna's teal/ivory and Nocturne's blue-black/canvas.

## Asset and lighting decisions

The original licensed HDR supplies cloud structure after its old sun is removed. A new authored panorama, reflection cube and diffuse SH are baked offline from one profile. Visible/mirror0 sun and analytic directional light share one direction and energy policy; diffuse/rough reflection use the disc-free profile. Original daylight remains an explicit comparison control.

The city has afternoon shadows baked into its vertex colours. Separate cloned meshes replace only that static shade, preserving local AO/variation, geometry, normals, UV0 and shared materials. New five-ray low-sun shadows remain an approximate vertex bake over the existing adaptive ground. UV2/3 carry eight static building visibility weights for the existing lamp heads.

Eight existing streetlight fixtures gain HDR warm undersides and bounded cone/distance/normal-dependent direct PBR illumination in the existing base pass. This adds no Unity Light component, geometry, shadow map or ForwardAdd pass. Static building visibility is baked; dynamic car/bench/foliage occlusion is not fully shadow mapped. Do not claim otherwise. Source intensity and emitter HDR are authored to look like lights beginning to matter while ambient daylight still reveals the road. The sunset profile reduces bloom from0.10 to0.06 to limit thin-chrome/dark-cabin spill.

## Finite review route

Garage; same-pose car street views; low street vista toward sunset; opposite-facing street and cockpit; close existing fixture with lamp illumination off and emission left on; Catrina hop/three-wheel/drive, Luna lift, Nocturne roof. Focused capture-only lamp placement is recorded with its exact launch flag and initial state. Diagnostic captures cannot enter the normal delivery packet.

Independent evaluators judge actual player output, not the recipe. Check readable road between lamps, warm/cool facade separation, reflected sky and paint identity, matching sun/shadow direction, visible existing lamp fixtures with real local surface illumination, no global orange filter/night darkness, no broad bloom veil or sky seam, and bounded motion. Keep failed packets. The broader city's art-direction limitations remain separate from its lighting.

Existing caps remain: hidden/silent sequential960x600/30, no MSAA, one512shadow,2GiBprocessjob,300draws/700kactivegeometry. Measure new exact player against r25; do not infer GPU headroom or handheld1080p60 from capped PNG capture intervals. Pure simulation is unchanged. No sound/media is added.
