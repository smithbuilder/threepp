# Authored Mercer evening profile

November 11, 2026, Pacific Time. Source: `Unity/Assets/Cinder/Scripts/Editor/CinderSunsetBake.cs`. This is an original authored approximately 6pm profile, not an astronomical day/night system.

The existing licensed photographic HDR supplies cloud structure after its old sun/halo is removed by the frozen native extractor. The new profile uses a blue/lavender upper sky, rose/peach horizon and cloud tint, a low warm sun and a muted lower hemisphere. The original daylight source and all daylight-generated resources remain intact. No new media service, paid asset or runtime generation is used.

Run `CinderSunsetBake.Run()` after the existing daylight bake. It writes `Cinder/sunset-sky`, `Cinder/sunset-reflection`, `Cinder/sunset-ambient-sh` and `Cinder/sunset-lighting` resources. The recipe receipt includes exact palette/shape parameters, source/code/image hashes, original sun extraction, the shared sun direction/colour/intensity, sampled sun energy, SH calibration and cardinal reflection comparisons.

Visible sky and true-mirror mip0 contain the authored sun disc. Rough reflection mips and diffuse SH use the same disc-free authored sky. Discrete solid-angle weighting normalizes the visible disc's integrated RGB energy to the recorded analytic irradiance. Sun irradiance is 2.4 with linear RGB (1,0.62,0.35); Unity's calibrated intensity is 2.4/pi. Environment strength remains 0.65. The native hemisphere component remains unchanged at linear hex colours times 0.24/pi. Material factors and tone/exposure are outside this worker's scope and remain untouched.

The diffuse bake retains 4,096 uniform sphere samples, a unit-white-furnace check across 70 directions and the native hemisphere calibration. SH is an L2 low-frequency approximation. The profile must be judged in fresh actual player captures; source completion and calibration are not visual acceptance. Streetlight behavior is integrated separately by the host/material owner.

The r27 refinement adds a separately recorded calibrated constant cool city-bounce SH term (linear RGB0.075/0.11/0.16) after independent r26 feedback found shaded walls/cabins too plum-dark. This is an authored indirect fill, not extra sun energy or a reflection/exposure retune; calibration remains checked. Lamp scalar intensity is reduced48 to28 and the sunset garage camera moves off the strong mirror-sun angle to preserve the lace. Original daylight is unchanged.
