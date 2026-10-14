# 0001: Build on build123d, in millimetres

Status: accepted, October 2026.

## Context

Vedya began, in 2024, as a script for Fusion 360's API. Nothing built a design without a Fusion licence and its window, and every output file was exported by hand. The script passed every length to Fusion as a bare number, which Fusion reads as centimetres; Fusion's STL export writes millimetres, so the files in `public/` are ten times the code's numbers. The script found the regions it extruded by comparing the areas of Fusion's sketch profiles with areas it computed.

The port needed a CAD kernel that runs from Python on Linux, macOS and Windows, with exact solids, 2D offsets, splines, booleans, and STEP, STL and 3MF export.

## Decision

- Vedya is built on [build123d](https://github.com/gumyr/build123d), on the OpenCascade kernel, used directly through its algebra API (`Sketch`, `Part` and their operators), with no wrapper of our own.
- Every length in the package is in millimetres. Values taken from the old code are multiplied by ten. Centimetres appear only in the stand-in (`tools/legacy/adsk/`), which runs the old code as written, and the goldens it writes are in millimetres (ADR 0002).
- A design constructs each region with 2D booleans, such as `circle(360) - diamond(310)`, and never picks a region by its area. Each of Shire's twelve area picks is one region that can be constructed this way.
- A thin wall becomes a stroke: the band between an outline and its 2D offset, with sharp corners, on the side `Align` names.

Turned down:
- CadQuery: the same kernel, under an older fluent API that types poorly.
- OpenSCAD: mesh CSG, with no exact solids and no STEP, and 2D offsets that cannot follow a spline exactly.
- FreeCAD scripting: brings in the whole application.
- OpenCascade's Python bindings (OCP) directly: what build123d already wraps, at many times the code.
- Keeping centimetres inside and scaling on export: a hidden unit in every function.

## Consequences

- `vedya build` runs anywhere build123d has wheels, and CI builds and checks every design on Linux, macOS and Windows.
- STEP, STL and 3MF files are in millimetres, which is what slicers, CAM and STEP viewers assume.
- Some of OpenCascade's 3D booleans are not reliable on these shapes. A 3D fuse of overlapping slabs enclosed thin wedges, such as an astroid's cusps, twice, so that Shire's core and layer-1 came out 35 mm³ too large, and it loosened edges of the core to 0.39 mm from their curves. So a part joins its slabs band by band, in the plane (`vedya.model.union`), and a design makes each region afresh for each use, because a boolean can leave its operands unfit for another. `tests/test_solids.py` holds every solid the command line writes to 0.001 mm.
- The goldens record the build123d version they were measured with.

## What would change it

- build123d stops being maintained, or has no wheels for a Python version Vedya supports.
- A design needs geometry that OpenCascade cannot build reliably, and another open kernel can.
