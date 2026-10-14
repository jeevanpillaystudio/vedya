"""Planar regions, the strokes drawn around them, and the slabs extruded from them.

Every design is built from these few functions. A region is a set of faces on the XY
plane, combined with build123d's operators: `+` for union, `-` for difference and `&` for
intersection. A slab lifts a region into a solid of a given height at a given z.

Every length is in millimetres.
"""

from enum import Enum
from typing import Any

import build123d as bd
from build123d.topology import Shape

__all__ = ["Align", "Region", "circle", "diamond", "rectangle", "slab", "stroke"]

type Region = bd.Sketch | bd.Compound | bd.Wire
"""Faces on the XY plane, as build123d's operators type them.

`-` and `&` on sketches are typed to return a `Compound`, and `+` a `Compound | Wire`; at
run time a union of separate sketches is a bare `Compound`. A `Wire` has no faces, and is
refused as an empty region.
"""


class Align(Enum):
    """The side of an outline a stroke grows to.

    These are Fusion 360's thin-wall locations: `INSIDE` is Side1, `OUTSIDE` is Side2 and
    `CENTER` is Center.
    """

    INSIDE = "inside"
    OUTSIDE = "outside"
    CENTER = "center"


def circle(radius: float, at: tuple[float, float] = (0.0, 0.0)) -> bd.Sketch:
    """The disc of `radius` centred at `at`."""
    _require_positive("radius", radius)
    return bd.Pos(*at) * bd.Circle(radius)


def rectangle(length_x: float, width_y: float) -> bd.Sketch:
    """The rectangle `length_x` long in x and `width_y` wide in y, centred on the origin."""
    _require_positive("length_x", length_x)
    _require_positive("width_y", width_y)
    return bd.Rectangle(length_x, width_y)


def diamond(half_diagonal: float) -> bd.Sketch:
    """The square turned 45°, with its vertices at (±half_diagonal, 0) and (0, ±half_diagonal)."""
    _require_positive("half_diagonal", half_diagonal)
    s = half_diagonal
    return bd.Polygon((s, 0.0), (0.0, s), (-s, 0.0), (0.0, -s), align=None)


def stroke(shape: Region, width: float, align: Align) -> bd.Sketch:
    """The band of `width` along the outline of `shape`, on the side `align` names.

    - `INSIDE`: `shape` minus `shape` offset inwards by `width`.
    - `OUTSIDE`: `shape` offset outwards by `width`, minus `shape`.
    - `CENTER`: `shape` offset outwards by `width / 2`, minus `shape` offset inwards by
      `width / 2`.

    Offsets keep sharp corners: a stroked square is a square frame, not a rounded one.
    Raises `ValueError` when an inward offset would close the shape up, as a stroke wider
    than a circle's radius would.
    """
    _require_positive("width", width)
    region = _sketch(shape)
    if not region.faces():
        raise ValueError("cannot stroke an empty region")
    match align:
        case Align.INSIDE:
            return _sketch(region - _offset(region, -width))
        case Align.OUTSIDE:
            return _sketch(_offset(region, width) - region)
        case Align.CENTER:
            return _sketch(_offset(region, width / 2) - _offset(region, -width / 2))


def slab(region: Region, z: float, height: float) -> bd.Part:
    """The solid that `region` sweeps from `z` up to `z + height`."""
    _require_positive("height", height)
    flat = _sketch(region)
    if not flat.faces():
        raise ValueError("cannot make a slab from an empty region")
    return bd.Pos(0.0, 0.0, z) * bd.extrude(flat, amount=height, dir=(0.0, 0.0, 1.0))


def _offset(region: bd.Sketch, distance: float) -> bd.Sketch:
    """`region` grown by `distance`, or shrunk where `distance` is negative, with sharp corners."""
    try:
        moved = bd.offset(region, distance, kind=bd.Kind.INTERSECTION)
    except RuntimeError as error:
        # OpenCascade's 2D offset fails when an inward offset closes the outline up.
        raise ValueError(
            f"the shape cannot be offset by {distance:g} mm: a stroke that wide closes it up"
        ) from error
    if not moved.faces():
        raise ValueError(f"offsetting the shape by {distance:g} mm leaves nothing")
    return _sketch(moved)


def _sketch(shape: Shape[Any]) -> bd.Sketch:
    """`shape` as a `Sketch` of its faces. Raises `TypeError` for a shape with solids."""
    if shape.solids():
        raise TypeError("a region is flat, but this shape has solids")
    return shape if isinstance(shape, bd.Sketch) else bd.Sketch(shape.faces())


def _require_positive(name: str, value: float) -> None:
    if not value > 0:
        raise ValueError(f"{name} must be positive, not {value!r}")
