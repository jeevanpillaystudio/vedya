"""UMSS, a magnetic tile for the Universal Modular Storage System.

The tile is a fork of https://www.printables.com/model/947943, in 32 mm squares, with a
pocket for a cylindrical magnet 6 mm across and 3 mm high. `UmssParams.parts` chooses
what is built:

- `magnet-base`, the default: the solid disc the Fusion 360 script built last.
- `tile`: the square tile with a through hole for the magnet. Milestone 1 printed it
  with hole radii from 3.0 to 3.5 mm.
- `base-ring`: the 1 mm wall that encloses the magnet base, outside its circle.
"""

from collections.abc import Callable
from dataclasses import dataclass

import build123d as bd

from vedya.designs import Design
from vedya.geometry import Align, circle, rectangle, slab, stroke
from vedya.model import Model

__all__ = ["PART_NAMES", "UmssParams", "build", "design"]


@dataclass(frozen=True)
class UmssParams:
    """A UMSS magnetic tile: which parts to build, and their sizes in mm.

    Attributes:
        tile: The tile's length (x), width (y) and thickness; it stands on z = 0.
        hole_radius: The radius of the magnet hole through the tile's centre.
        magnet_base: The magnet base disc's radius, height, and the z of its underside.
        base_ring: The base ring's inner radius, height, wall thickness, and the z of its
            underside.
        parts: The parts to build, from `PART_NAMES`.
    """

    tile: tuple[float, float, float] = (32.0, 32.0, 3.0)
    hole_radius: float = 3.1
    magnet_base: tuple[float, float, float] = (3.1, 1.5, -2.5)
    base_ring: tuple[float, float, float, float] = (3.1, 0.5, 1.0, -0.5)
    parts: tuple[str, ...] = ("magnet-base",)


def _tile(params: UmssParams) -> bd.Part:
    length, width, thickness = params.tile
    if not params.hole_radius < min(length, width) / 2:
        raise ValueError(
            f"a hole of radius {params.hole_radius:g} mm does not fit in a "
            f"{length:g} by {width:g} mm tile"
        )
    return slab(rectangle(length, width) - circle(params.hole_radius), 0.0, thickness)


def _magnet_base(params: UmssParams) -> bd.Part:
    radius, height, z = params.magnet_base
    return slab(circle(radius), z, height)


def _base_ring(params: UmssParams) -> bd.Part:
    radius, height, wall, z = params.base_ring
    return slab(stroke(circle(radius), wall, Align.OUTSIDE), z, height)


_BUILDERS: dict[str, Callable[[UmssParams], bd.Part]] = {
    "tile": _tile,
    "magnet-base": _magnet_base,
    "base-ring": _base_ring,
}

PART_NAMES: tuple[str, ...] = tuple(_BUILDERS)
"""The parts UMSS can build, in the order it builds them."""


def build(params: UmssParams) -> Model:
    """The parts `params.parts` names, built in the order of `PART_NAMES`."""
    unknown = sorted(set(params.parts) - set(PART_NAMES))
    if unknown:
        raise ValueError(
            f"UMSS has no part {', '.join(map(repr, unknown))}; "
            f"its parts are {', '.join(PART_NAMES)}"
        )
    if not params.parts:
        raise ValueError(f"choose at least one UMSS part from {', '.join(PART_NAMES)}")
    return Model({name: _BUILDERS[name](params) for name in PART_NAMES if name in params.parts})


design = Design(name="umss", params=UmssParams, build=build)
