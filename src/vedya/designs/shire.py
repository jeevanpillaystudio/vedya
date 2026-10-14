"""Shire, the relief milled in Huon pine for the Shire festival in April 2024.

The board is 640 by 960 mm. Everything on it is a whole number of layers, 4.8 mm, or a
fraction of one, up to 38.4 mm. Its parts, in the order the Fusion 360 script built them:

- `bg`: the board, two layers thick.
- `border`: a wall six layers high along the board's edge, inside it, standing on the bg.
- `layer-0`: a seed-of-life layer in the circle of 360 mm around the outer diamond, from
  four layers up. The circle is wider than the board, so the layer overhangs the board's
  long sides, from 320 to 360 mm out, as the script built it.
- `layer-2`: a seed-of-life layer on the board outside that circle, from four layers up
  to the top.
- `layer-1`: a seed-of-life layer between the outer and middle diamonds, from two layers
  up.
- `core`: the board outside the outer diamond, the walls inside the middle and inner
  diamonds, and four astroids stacked at the centre.
- `torus`: the top astroid less a torus of rings, in two steps whose rings thicken
  upwards, with a wall along the astroid's edge.
- `middle-ring`: a wall outside the circle at the centre, which stands through the core.

A seed-of-life layer is a region, its mask, carved by seeds of life in two passes whose
steps differ; where they overlap, the later pass's steps hold (see `seed_layer`).

A diamond is a square turned 45°, given by its half-diagonal. An astroid is given by the
distance from its centre to a cusp.
"""

import copy
from collections.abc import Callable, Sequence
from dataclasses import dataclass

import build123d as bd

from vedya.designs import Design
from vedya.geometry import Align, Region, astroid, circle, diamond, rectangle, slab, stroke
from vedya.model import Model
from vedya.patterns import depth_steps, seed_of_life, torus_rings

__all__ = ["PART_NAMES", "SeedPass", "ShireParams", "build", "design", "seed_layer"]

_TORUS_STEPS = 2
"""The torus is carved in two steps, one half-layer each."""

_SEED_CIRCLE = 360.0
"""The radius of the circle between the two outer seed-of-life layers: layer-0 lies
inside it, and layer-2 outside it. The script wrote it as a literal in both layers."""

_LAYER_2_LEEWAY = 160.0
"""How much longer than the circle's diameter the script drew layer-2's rectangle, which
the board then trims."""


@dataclass(frozen=True)
class SeedPass:
    """One pass of a seed-of-life layer: seeds of `radius`, drawn `steps` times up `height`,
    with the stroke growing by `stroke` at each step."""

    radius: float
    stroke: float
    height: float
    steps: int


@dataclass(frozen=True)
class ShireParams:
    """Shire, the relief milled in Huon pine in 2024: its sizes in mm.

    Attributes:
        layer: The depth of one layer; the parts start and end at whole layers, and a
            seed-of-life pass divides its layers into equal steps.
        board: The board's length (x) and width (y).
        border_width: The thickness of the border wall.
        diamonds: The half-diagonals of the outer, middle and inner diamonds.
        wall: The thickness of the diamonds' walls, of the step from each astroid to the
            one on it, of the torus's edge wall, and of the middle ring.
        astroids: The radii of the outer and inner astroids, each the lower of a pair; the
            inner pair's top astroid holds the torus.
        torus: The torus's radius, its number of inner rings, and the stroke of its lowest
            step's rings.
        hole_radius: The radius of the circle the middle ring stands outside.
        layer_0: The passes of the seed-of-life layer in the circle around the outer diamond.
        layer_2: The passes of the seed-of-life layer outside that circle.
        layer_1: The passes of the seed-of-life layer between the outer and middle diamonds.
    """

    layer: float = 4.8
    board: tuple[float, float] = (640.0, 960.0)
    border_width: float = 19.2
    diamonds: tuple[float, float, float] = (310.0, 240.0, 160.0)
    wall: float = 7.2
    astroids: tuple[float, float] = (294.4, 185.6)
    torus: tuple[float, int, float] = (192.0, 16, 3.2)
    hole_radius: float = 57.6
    layer_0: tuple[SeedPass, ...] = (SeedPass(200, 9.6, 9.6, 4), SeedPass(640, 28.8, 4.8, 4))
    layer_2: tuple[SeedPass, ...] = (SeedPass(440, 9.6, 19.2, 6), SeedPass(720, 9.6, 9.6, 4))
    layer_1: tuple[SeedPass, ...] = (SeedPass(280, 19.2, 19.2, 6), SeedPass(160, 9.6, 9.6, 4))


# Each part makes its regions afresh where it uses them: a region combined twice may be
# left unfit for the second boolean by the first (see `vedya.geometry`).


def _board(params: ShireParams) -> bd.Sketch:
    return rectangle(*params.board)


def _bg(params: ShireParams) -> bd.Part:
    return slab(_board(params), 0.0, 2 * params.layer)


def _border(params: ShireParams) -> bd.Part:
    layer = params.layer
    return slab(stroke(_board(params), params.border_width, Align.INSIDE), 2 * layer, 6 * layer)


def seed_layer(mask: Region, start: float, passes: Sequence[SeedPass]) -> bd.Part:
    """The mask carved by seeds of life, in passes that each rise from `start`.

    A pass is a stack of `steps` slabs, one on another, up its `height`. Each slab is the
    mask less a seed of life of the pass's radius, drawn with a stroke that grows by the
    pass's `stroke` at each step up (`depth_steps`). The seed's centre ring is stroked
    inside its circle and its petals astride theirs, as the Fusion 360 script drew them.

    The slabs are laid in order, pass after pass and each pass from the bottom up, and
    each one cuts back every slab laid before it that it overlaps in height to the
    heights the two share. The passes all rise from `start`, so a later pass's slabs
    trim the earlier passes' to their own steps, and above the later pass's top the
    earlier passes stand alone. The layer is the union of what is left. That is how the
    piece was milled: in Fusion, each step's intersect with the mask reached every body
    in the layer.
    """
    if not passes:
        raise ValueError("a seed-of-life layer needs at least one pass")
    laid: list[_Slab] = []
    for seed in passes:
        for step in depth_steps(seed.steps, start, seed.height, seed.stroke):
            low, high = step.z, step.z + step.height
            laid = [earlier.trimmed(low, high) for earlier in laid]
            # The mask is copied for each slab, as a region combined once may be left unfit
            # for another boolean (see `vedya.geometry`).
            region = copy.deepcopy(mask) - seed_of_life(
                seed.radius, step.stroke, centre=Align.INSIDE, petals=Align.CENTER
            )
            laid.append(_Slab(low, high, region))
    return _fuse([slab(each.region, each.low, each.high - each.low) for each in laid])


_LEVEL = 1e-9
"""Heights closer than this, in mm, are one: steps that only meet do not overlap."""


@dataclass(frozen=True)
class _Slab:
    """A region to be swept from `low` up to `high`."""

    low: float
    high: float
    region: Region

    def trimmed(self, low: float, high: float) -> "_Slab":
        """This slab cut back to the heights it shares with `low` to `high`, if it shares
        any; otherwise this slab."""
        shared_low, shared_high = max(self.low, low), min(self.high, high)
        if shared_high - shared_low <= _LEVEL:
            return self
        return _Slab(shared_low, shared_high, self.region)


def _layer_0(params: ShireParams) -> bd.Part:
    outer = params.diamonds[0]
    return seed_layer(circle(_SEED_CIRCLE) - diamond(outer), 4 * params.layer, params.layer_0)


def _layer_2(params: ShireParams) -> bd.Part:
    _, width = params.board
    beyond = rectangle(2 * _SEED_CIRCLE + _LAYER_2_LEEWAY, width) - circle(_SEED_CIRCLE)
    # The script cut away what lay outside the board once the layer was built; trimming
    # its mask gives the same.
    return seed_layer(beyond & _board(params), 4 * params.layer, params.layer_2)


def _layer_1(params: ShireParams) -> bd.Part:
    outer, middle, _ = params.diamonds
    return seed_layer(diamond(outer) - diamond(middle), 2 * params.layer, params.layer_1)


def _core(params: ShireParams) -> bd.Part:
    layer, wall = params.layer, params.wall
    outer, middle, inner = params.diamonds
    low, high = params.astroids
    return _fuse(
        [
            slab(_board(params) - diamond(outer), 2 * layer, 2 * layer),
            slab(stroke(diamond(middle), wall, Align.INSIDE), 2.5 * layer, 3 * layer),
            slab(astroid(low), 2.5 * layer, layer),
            slab(astroid(low - wall), 3 * layer, 2 * layer),
            slab(stroke(diamond(inner), wall, Align.INSIDE), 5 * layer, 2 * layer),
            slab(astroid(high), 5 * layer, layer),
            slab(astroid(high - wall), 6 * layer, layer),
        ]
    )


def _torus(params: ShireParams) -> bd.Part:
    layer, wall = params.layer, params.wall
    radius, count, base_stroke = params.torus
    top = params.astroids[1] - wall
    return _fuse(
        [
            slab(
                (astroid(top) - torus_rings(radius, count, step.stroke))
                + (astroid(top) - astroid(top - wall)),
                step.z,
                step.height,
            )
            for step in depth_steps(_TORUS_STEPS, 6 * layer, layer, base_stroke)
        ]
    )


def _middle_ring(params: ShireParams) -> bd.Part:
    layer = params.layer
    return slab(stroke(circle(params.hole_radius), params.wall, Align.OUTSIDE), layer, 6 * layer)


_BUILDERS: dict[str, Callable[[ShireParams], bd.Part]] = {
    "bg": _bg,
    "border": _border,
    "layer-0": _layer_0,
    "layer-2": _layer_2,
    "layer-1": _layer_1,
    "core": _core,
    "torus": _torus,
    "middle-ring": _middle_ring,
}

PART_NAMES: tuple[str, ...] = tuple(_BUILDERS)
"""The parts `build` makes, in the order it makes them."""


def build(params: ShireParams) -> Model:
    """Every part in `PART_NAMES`, in that order."""
    return Model({name: make(params) for name, make in _BUILDERS.items()})


def _fuse(solids: list[bd.Part]) -> bd.Part:
    first, *rest = solids
    fused = first + rest
    return fused if isinstance(fused, bd.Part) else bd.Part(fused.solids())


design = Design(name="shire", params=ShireParams, build=build)
