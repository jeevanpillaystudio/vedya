# 0002: Pin each ported design by running the 2024 script on a stand-in for Fusion

Status: accepted, October 2026.

## Context

No commit of the Fusion 360 code had a test. What it built depends on Fusion behaviours that Autodesk leaves open or documents differently from what happened (ADR 0003). Fusion cannot run in CI: it needs a licence and a window. A port checked against numbers written down from a reading of the code would pin the reading, not the code.

## Decision

The ported designs are pinned by the old code itself.

- `tools/legacy/adsk/` is a stand-in for Fusion's `adsk` package: the forty or so members the 2024 scripts call, built on build123d, in centimetres. Its contract, the Fusion behaviour it reproduces, is written at the top of `tools/legacy/adsk/fusion.py` and held by `tests/test_stand_in.py`.
- `tools/legacy/history.py` writes a commit's files to a temporary folder with `git show`. `tools/legacy/golden.py` imports the script from there, unchanged, with the stand-in installed as `adsk`, and calls its `run()` as Fusion did. It joins the bodies under each top-level component, scales them to millimetres, and writes their fingerprints to `tests/golden/<design>.json`, with the commit, the entry point and the build123d version. A golden is keyed by build order, because some scripts name components with random suffixes.
- UMSS's golden comes from `08f31da` (`src/APIDrawVedya.py`), and Shire's from `a36cc3c` (`src/v1/api-vedya-draw/APIDrawVedya.py`), with its aggregate.
- The fast tests compare each built part with its golden to a relative 1e-6 in volume and area, and to 0.001 mm in bounding box and centroid.

The stand-in holds every body as a stack of prisms along z (`tools/legacy/prisms.py`). Every feature the scripts use extrudes a sketch drawn parallel to XY straight along z, so every body they make is such a stack, and a boolean on stacks is the same boolean on their sections, band by band, in the plane. OpenCascade's booleans in the plane hold where its booleans on solids do not. On the 39 bodies of `a36cc3c`'s Shire, a fuse of the solids gave a solid 2 to 9% short of their union, or an invalid one, as the order and options varied, and the intersection of two overlapping solids came out empty. In the plane, Shire's parts agree with the solids the new design builds to 3e-8, and the aggregate with the union of the parts to 1e-14.

Four checks keep the stand-in honest, in `make slow`:
- Run unchanged, the milestone-1 scripts at `af36f97` and `de4e698` give the tiles whose STL files Fusion exported, with hole radii 3.0 and 3.1 mm: the files' volumes sit 0.085 to 0.098 mm³ above the exact solid's, as tessellation leaves them, and their bounding boxes agree to 0.001 mm.
- The April script (`57f2b02`) and the August one (`a36cc3c`) build the same parts and the same aggregate.
- Each of Shire's twelve area picks matches exactly one region.
- Each new Shire part, and the new aggregate, differs from the stand-in's by less than 1e-6 of its volume: the volume in one and not the other. Two routes built independently agree, which two errors that cancel in a fingerprint cannot fake.

Turned down:
- Expected numbers written by hand from a reading of the code: they pin the reading.
- Running Fusion: it cannot run in CI.
- Keeping the old files in the tree: git history already holds them, and the tags `fusion/milled`, `fusion/shire-last` and `fusion/head` mark them.

## Consequences

- The slow tests read git history, so they need a clone with every commit: CI's slow job checks out with `fetch-depth: 0`, and a shallow clone needs `git fetch --unshallow`.
- A golden is regenerated with `make golden` only when the stand-in changes, and the change is explained in the commit. A design test that fails against its golden means the design changed, and is never fixed by regenerating.
- The stand-in can model only prismatic features. A script with fillets, lofts or tilted sketches would need a different stand-in.
- New designs have no Fusion script. Their pin is their own tests; the stand-in serves only the ported designs.

## What would change it

- A Fusion run of the 2024 scripts, or a recovered Fusion document of Shire, that disagrees with the stand-in's contract. The contract would be corrected from it, and the goldens regenerated with that reason.
- The ported designs being retired, which would leave the stand-in nothing to pin.
