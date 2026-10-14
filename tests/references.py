"""The outside references the designs are held to, and how closely they must match.

- The goldens in `tests/golden/`, which the stand-in wrote by running the original Fusion
  360 scripts (`make golden`). A fingerprint matches its golden to a relative 1e-6 in
  volume and area, and to 1e-3 mm in its bounding box and centroid.
- Milestone 1's STL files, which Fusion exported from the 2024 code with no manual step.
- How clean a solid written for fabrication must be: valid, and no edge looser than
  `CLEAN`.
"""

import math
from pathlib import Path
from typing import Any

from build123d.topology import Shape

# OCP is compiled and ships no type stubs, so its names are invisible to the type checker.
from OCP.BRep import BRep_Tool  # pyright: ignore[reportAttributeAccessIssue]

from vedya.model import Fingerprint

MILESTONE_1 = Path(__file__).parent.parent / "src" / "public" / "f360-milestone-1"
"""Milestone 1's STL files: the tile with a magnet hole, one file per hole radius."""

MEASURED_EXCESS = (0.0845, 0.0985)
"""How far, in mm³, milestone 1's STL volumes sit above the exact solid's.

Fusion meshed the hole as a polygon inside its circle, so each file holds slightly more
than the solid. Across the six files the excess measured +0.085 to +0.098 mm³, to three
decimals; the band allows half a unit of the last decimal each way.
"""

RELATIVE = 1e-6
"""How far a volume or an area may stray from its golden, relative to it."""

LENGTH = 1e-3
"""How far, in mm, a bounding box's corner or a centroid may stray from its golden."""

CLEAN = 1e-3
"""The loosest, in mm, that an edge, vertex or face of a solid written for fabrication
may be: how far it may lie from the curve or surface it stands for. OpenCascade leaves
exact ones at 1e-7; a 3D fuse of overlapping slabs left Shire's core at 0.39."""


def largest_tolerance(shape: Shape[Any]) -> float:
    """The loosest tolerance, in mm, of any face, edge or vertex of `shape`."""
    return max(
        BRep_Tool.Tolerance_s(item.wrapped)
        for items in (shape.faces(), shape.edges(), shape.vertices())
        for item in items
    )


def milestone_1_stl(hole_radius: float) -> Path:
    """Milestone 1's STL file for the tile with a hole of `hole_radius` mm."""
    # The files are named by the code's centimetre radius: 0.30 cm is a 3.0 mm hole.
    return MILESTONE_1 / f"tile-magnet-hole-radius-{hole_radius / 10:.2f}mm.stl"


def differences(actual: Fingerprint, expected: Fingerprint) -> list[str]:
    """How `actual` strays from the golden `expected` beyond the tolerances; empty if not."""
    found: list[str] = []
    for name, got, want in (
        ("volume", actual.volume, expected.volume),
        ("area", actual.area, expected.area),
    ):
        if not math.isclose(got, want, rel_tol=RELATIVE):
            found.append(f"{name} {got!r}, golden {want!r}")
    for name, got_point, want_point in (
        ("bbox_min", actual.bbox_min, expected.bbox_min),
        ("bbox_max", actual.bbox_max, expected.bbox_max),
        ("centroid", actual.centroid, expected.centroid),
    ):
        if any(abs(g - w) > LENGTH for g, w in zip(got_point, want_point, strict=True)):
            found.append(f"{name} {got_point!r}, golden {want_point!r}")
    return found
