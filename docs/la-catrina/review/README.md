# La Catrina review evidence

Two independent reviewers compared the accepted model with the original sheet
and the same 16 native studio views. Their weighted scores were **8.020/10**
and **8.115/10**. The accepted GLB has SHA-256
`8444acaabf320f15fc3157342f4d23baa0b03b701d99af365608f48c4c16cb3e`.
[Acceptance record](accepted-model.json) · [Review A](round-11-a.md) · [Review B](round-11-b.md) · [Studio views and receipt](studio/) · [Original sheet](../references/La-Catrina-Master.jpg)

The mechanical review checked wheel, ram, coil and linkage travel over the
recorded poses. Its report includes intentional joint contacts and sampling
limits. The material notes identify the commercial component families and
the dimensions chosen specifically for this model.
[Mechanical review](round-11-mechanical.md) · [Rig measurements](rig-audit.json) · [Component and material references](../REAL-WORLD-BASIS.md)

The JSON and image files here preserve the original evaluation bytes. Paths
beginning with `build/` and absolute Windows paths in those records identify
the local sessions where the measurements were made. The 183-check physics
receipt came from the five-vehicle delivery build. The asset checks, enclosure
audit and package receipt each identify the accepted model.
[Asset audit](asset-audit.json) · [Enclosure audit](enclosure-audit.json) · [Physics comparison](physics-comparison.json) · [Native review](native-review.json) · [Package verification](delivery-receipt.json)

The `main` integration registers four vehicles. Both native targets compiled
and linked. A clean export of the proposed Git files regenerated the accepted
GLB byte for byte and passed 83 asset checks and the stored 243-pose wheel
clearance audit. The film preflight also passed after restoring its six local
clips. Fresh native execution requires signing the newly built executables.
[Main integration check](main-integration.json)

To rerun the historical independent mechanical check from the repository root,
place the two files from `mechanical-inputs/` at the original paths shown below.
The checker reads the retained poses and writes its new results under `build/`.
It requires Python, NumPy, SciPy and Pillow.

```powershell
$reviewInputs = 'docs/la-catrina/review/mechanical-inputs'
$reviewOutput = 'build/la-catrina/independent'
$poseOutput = 'build/sessions/20261106-101153-431/physics-audit'
New-Item -ItemType Directory -Force -Path $reviewOutput, $poseOutput | Out-Null
Copy-Item -LiteralPath "$reviewInputs/round-09-mechanical.json" -Destination $reviewOutput
Copy-Item -LiteralPath "$reviewInputs/catrina-rig-poses.csv" -Destination $poseOutput
python -B -X utf8 docs/la-catrina/review/round-11-mechanical-check.py
```
