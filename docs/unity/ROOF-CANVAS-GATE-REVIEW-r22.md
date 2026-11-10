# Independent roof canvas gate diagnosis: r22

November 9, 2026, Pacific Time. Reviewer: migration_review. Read-only source and retained-report review; no player/editor launch and no implementation change.

## Measured failure

The retained `evidence/cinder-unity-r22/20261109-230045-521-Probe/runtime-batch-probe.json` has two unmutated canvas reads for each Nocturne detail tier. Both reads fail identically. All three cloth nodes and active original renderers are present, totaling 4,274 triangles. The hero cloth meshes share material instance 5278, named `nocturne.black_canvas`, with shader `Cinder/Body`.

On the Null graphics device the initial readbacks are `_Cull=0`, `HasProperty(_Cull)=false` and `shader.isSupported=false`. After deliberately writing `_Cull=2` and restoring the saved zero, `HasProperty` becomes true, while the value returns to zero and shader support remains false. Mesh participation and positions do not change. Mid and far exhibit the same pattern with their own material instances.

This localizes the first material-policy failure to Null-device property metadata, rather than missing geometry or a demonstrated serialized `_Cull=2`. The source hero canvas also independently serializes `_Cull=0` in `m_Floats` with no duplicate integer property. The failed packets remain failures under the original combined check; they must be retained.

## Proposed gate separation

**The proposed separation is justified by the measured environment limitation, subject to the conditions below. It does not approve canvas rendering.**

1. Only an actual `GraphicsDeviceType.Null` may omit graphics-dependent `HasProperty`/shader-support requirements. An unsupported D3D shader must fail.
2. Null structural checks must read the untouched material first: correct shader identity, finite `_Cull=0`, expected cloth-node coverage and positive active mesh/triangle participation. Negative mutation must detect `_Cull=2`, then restore and verify the original state. No preflight write may manufacture the initial pass.
3. A fresh D3D normal-render process using the same final executable must check every relevant actual cloth renderer before diagnostic mutation: supported expected shader, `HasProperty(_Cull)`, finite `_Cull=0`, enabled/active participation and `forceRenderingOff=false`. The three shipped detail tiers need graphics coverage if the conclusion covers all three.
4. Required graphics receipts must identify executable hash, graphics backend, tier, roof phase and per-renderer/material readbacks. Final packet acceptance must require these receipts, not merely print them as informational logs.
5. Names and delivery claims must distinguish headless structural/material-value checks from graphics material support and actual visible canvas. Positive world-space geometry and valid material properties alone do not establish rasterized visibility, correct normals, bounds/culling, silhouette or visual fidelity.

The reported missing deployed canvas in the actual graphics capture remains a separate unresolved rendering problem. Splitting the Null check does not resolve or waive that problem. Fresh graphics evidence and independent visual review are still required before the roof or final candidate can be accepted.

This reviewer authored the earlier `SurfaceShaderDiagnostics` helper and supplies no independent final shader-implementation approval here.
