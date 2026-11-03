# Safari cockpit finish and fit

`RallySafariCockpitFinish.hpp` decorates only the Safari cockpit, immediately
after its creation and before collecting fixed meshes. It preserves steering
and instrument animation parents, the eye, stock housing/face positions and
dashboard dimensions. It adds calibrated dial print, tapered needles/collets,
smooth bezels, leather grain, drilled/dished wheel spokes, fixings and trim.
Shared texture images are reused with local mesh UVs; their repeat settings
are not mutated. The original buggy still uses the stock cockpit.

The compiled validator checks27 meshes and2,878 net detail triangles, closed
physical meshes, finite unit normals, animation endpoints and bounded detail.
Bezel chord inflation is0.795626mm; dashboard face relief is1.8mm. Instrument
and steering details remain inside their reviewed principal envelopes.

`scripts/audit-safari-cockpit.py` checks the actual serialized body against
refined rim triangles and conservative circumscribed detail volumes. It checks
every body triangle against those volumes, including contained/boundary
corners: surface distance alone missed an entirely enclosed triangle in an
independent negative test. Exact source pins also bind placement helpers outside
the main builder. Changed helper/transforms or finish geometry require review.
Complete-header pins normalize only line endings so LF and CRLF checkouts
agree. Independent mutation controls still reject all non-EOL source edits;
the fresh actual-body audit repeats the same geometry and containment results.

The final combined body82795FE6 passes the independent full audit, with no
intersection or contained body corner. Minimum clearance is23.72715mm at the
left gauge/windscreen. See ignored review evidence under
`build/safari-cockpit-finish-review/COMBINED-REVIEW-82795fe6.md`.

The same body has closed EPDM window seals: measured14mm at both screens and
10mm at side panes, with exact paint/glass contacts. Their dedicated material
is matte rubber, rather than the previous coated-steel assignment. This fixes
the old chart-metric distortion that shrank some nominal6mm side seals below
2mm. Painted outer frames and the body loft are unchanged.

Run `Build-Playground.ps1 -Action Test` for CPU validation and
`scripts/prepare-safari-body.ps1` for the complete raw/AO body preparation gates.
Native appearance is separately scored; small gauge print remains a minor
readability limit in the approved960x600 profile.
