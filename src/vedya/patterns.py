"""Patterns built from the primitives: depth steps, the seed of life, and the torus of rings.

A depth step is one slab of a stack that gives a pattern relief: each step stands on the
one below it, and its stroke grows or shrinks with height. The seed of life is a ring
and six rings of the same size around it, each through its centre. The torus of rings is
a ring and a circle of smaller rings that meet at its centre.

Every length is in millimetres.
"""

import math
from dataclasses import dataclass
from enum import Enum

import build123d as bd

from vedya import geometry
from vedya.geometry import Align

__all__ = ["DepthStep", "Growth", "depth_steps", "seed_of_life", "torus_rings"]

_PETALS = 6
"""The rings around the seed of life's centre ring."""


class Growth(Enum):
    """How a stack's strokes change from its lowest step to its highest.

    `THICKER_UPWARD` is the Fusion 360 script's `Decrement`, the one Shire uses: step i of
    n has the stroke times i + 1. `THINNER_UPWARD`, its `Increment`, has it times n - i.
    """

    THICKER_UPWARD = "thicker-upward"
    THINNER_UPWARD = "thinner-upward"


@dataclass(frozen=True)
class DepthStep:
    """One step of a stack: a slab from `z` up `height`, drawn with a stroke of `stroke`."""

    z: float
    height: float
    stroke: float


def depth_steps(
    count: int,
    start: float,
    total_height: float,
    stroke: float,
    growth: Growth = Growth.THICKER_UPWARD,
) -> list[DepthStep]:
    """`count` steps of equal height that stack from `start` up to `start + total_height`.

    Step i's stroke is `stroke` times i + 1, or times `count` - i, as `growth` says.
    """
    if count < 1:
        raise ValueError(f"a stack needs at least one step, not {count!r}")
    for name, value in (("total_height", total_height), ("stroke", stroke)):
        if not value > 0:
            raise ValueError(f"{name} must be positive, not {value!r}")
    height = total_height / count
    return [
        DepthStep(
            z=start + height * i,
            height=height,
            stroke=stroke * (i + 1 if growth is Growth.THICKER_UPWARD else count - i),
        )
        for i in range(count)
    ]


def seed_of_life(
    radius: float,
    stroke: float,
    centre: Align = Align.INSIDE,
    petals: Align = Align.CENTER,
) -> bd.Sketch:
    """A ring along the circle of `radius` at the origin, and six petals: rings along
    circles of the same radius, centred `radius` from the origin at 60° steps from the x
    axis, so that each passes through the origin and the centres of its neighbours.

    Every ring is a stroke of `stroke`, the centre ring's on the side `centre` names and
    the petals' on the side `petals` names. The defaults are the Fusion 360 script's mix:
    its centre circle took the thin wall's default side, inside, and Shire asked for the
    petals' walls to be centred on their circles.
    """
    rings = [geometry.stroke(geometry.circle(radius), stroke, centre)]
    for i in range(_PETALS):
        # The angle is written as the Fusion 360 script wrote it.
        angle = math.radians(i * 60)
        at = (radius * math.cos(angle), radius * math.sin(angle))
        rings.append(geometry.stroke(geometry.circle(radius, at=at), stroke, petals))
    first, *rest = rings
    return bd.Sketch((first + rest).faces())


def torus_rings(radius: float, count: int, stroke: float) -> bd.Sketch:
    """A ring along the circle of `radius`, and `count` rings along circles half as large.

    Each smaller circle is centred `radius / 2` from the origin, at `360° / count` steps
    from the x axis, so it passes through the origin and touches the large circle from
    inside. Every ring is a stroke of `stroke` inside its circle.
    """
    if count < 1:
        raise ValueError(f"a torus needs at least one inner ring, not {count!r}")
    half = radius / 2
    rings = [geometry.stroke(geometry.circle(radius), stroke, Align.INSIDE)]
    for i in range(count):
        # The angle is written as the Fusion 360 script wrote it.
        angle = math.radians(i * (360 / count))
        centre = (half * math.cos(angle), half * math.sin(angle))
        rings.append(geometry.stroke(geometry.circle(half, at=centre), stroke, Align.INSIDE))
    first, *rest = rings
    return bd.Sketch((first + rest).faces())
