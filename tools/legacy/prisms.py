"""Solids that are stacks of prisms along z, and booleans on them worked out in the plane.

Every body the stand-in makes is a stack: each feature extrudes a sketch drawn parallel
to XY straight along z, and a union, cut or intersection of stacks is a stack. A `Stack`
holds its bands. Within a band, from one height to the next, its section is one region:
flat faces that do not overlap. A boolean on stacks is the same boolean on their regions,
band by band, and a stack's fingerprint follows from its bands without making a solid.

OpenCascade's booleans on faces in a plane hold where its booleans on solids, and its
gluing of prisms back into one solid, do not. On the 39 bodies of a36cc3c's Shire, a
fuse of the solids gives a solid 2 to 9% short of their union, or an invalid one, as
the order and options vary, and the intersection of two that overlap comes out empty.
Fusing two equal prisms of the core's section, one on the other, loses 1e-4 of their
volume where an astroid's cusps cross a diamond's wall. Worked in the plane, Shire's
parts agree with the solids the new design builds to 3e-8, and the aggregate with the
union of the parts to 1e-14.

A stack never changes. Lengths are in its own unit.
"""

import itertools
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from functools import cached_property
from typing import Any

import build123d as bd
from build123d.topology import Shape
from build123d.topology.shape_core import downcast
from OCP.BRepAdaptor import BRepAdaptor_Curve  # pyright: ignore[reportAttributeAccessIssue]

# OCP is compiled and ships no type stubs, so its names are invisible to the type checker.
from OCP.BRepAlgoAPI import (
    BRepAlgoAPI_Common,  # pyright: ignore[reportAttributeAccessIssue]
    BRepAlgoAPI_Cut,  # pyright: ignore[reportAttributeAccessIssue]
    BRepAlgoAPI_Fuse,  # pyright: ignore[reportAttributeAccessIssue]
)
from OCP.BRepBuilderAPI import BRepBuilderAPI_Copy  # pyright: ignore[reportAttributeAccessIssue]
from OCP.collections import List_TopoDS_Shape  # pyright: ignore[reportAttributeAccessIssue]
from OCP.GCPnts import GCPnts_AbscissaPoint  # pyright: ignore[reportAttributeAccessIssue]
from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain  # pyright: ignore[reportAttributeAccessIssue]

from vedya.model import Fingerprint, fingerprint

__all__ = ["Band", "Stack", "common", "cut", "split", "union"]

_LEVEL = 1e-7
"""Heights closer than this are one; OpenCascade's own precision."""

_FLAT = 1e-9
"""How far a horizontal face's normal may lean from the z axis."""

_LENGTH_ERROR = 1e-10
"""The largest relative error a curve's length may have."""

type Vec3 = tuple[float, float, float]


@dataclass(frozen=True)
class Band:
    """A slice of a stack: from `low` up to `high`, its section is `region`, a set of faces
    in the plane z = 0, each facing up, no two overlapping."""

    low: float
    high: float
    region: tuple[bd.Face, ...]


@dataclass(frozen=True)
class Stack:
    """A solid made of prisms along z: its bands, lowest first, none empty, none
    overlapping another."""

    bands: tuple[Band, ...] = ()

    @staticmethod
    def prism(region: Iterable[bd.Face], z: float, height: float) -> "Stack":
        """`region`, faces in the plane z = 0, extruded from `z` by `height`, which may
        be negative to extrude downwards."""
        low, high = sorted((z, z + height))
        if not high - low > _LEVEL:
            raise ValueError("a prism needs a height")
        faces = tuple(_facing_up(face) for face in region)
        return Stack((Band(low, high, faces),) if faces else ())

    @staticmethod
    def of_solid(part: bd.Part) -> "Stack":
        """The stack `part` is, read from its sections between its horizontal faces.

        `part` must be a stack of prisms along z, as everything Vedya builds is.
        """
        levels = _levels(
            face.center().Z
            for face in part.faces()
            if face.geom_type == bd.GeomType.PLANE and abs(face.normal_at().Z) > 1 - _FLAT
        )
        bands: list[Band] = []
        for low, high in itertools.pairwise(levels):
            middle = (low + high) / 2
            region = _section(part, middle)
            if region:
                drop = bd.Location((0.0, 0.0, -middle))
                bands.append(Band(low, high, tuple(face.moved(drop) for face in region)))
        return Stack(tuple(bands))

    @property
    def is_empty(self) -> bool:
        return not self.bands

    def region_at(self, z: float) -> tuple[bd.Face, ...]:
        """The section at height `z`, which must not be a band's end."""
        for band in self.bands:
            if band.low < z < band.high:
                return band.region
        return ()

    def scaled(self, factor: float) -> "Stack":
        """This stack scaled by `factor` about the origin."""
        if not factor > 0:
            raise ValueError(f"a stack is scaled by a positive factor, not {factor!r}")
        return Stack(
            tuple(
                Band(
                    band.low * factor,
                    band.high * factor,
                    tuple(face.scale(factor, about=(0.0, 0.0, 0.0)) for face in band.region),
                )
                for band in self.bands
            )
        )

    @cached_property
    def bounds(self) -> tuple[Vec3, Vec3]:
        """The low and high corners of the box aligned with the axes that holds the stack."""
        if not self.bands:
            raise ValueError("an empty stack has no bounds")
        flat = bd.Compound([face for band in self.bands for face in band.region]).bounding_box()
        return (
            (flat.min.X, flat.min.Y, self.bands[0].low),
            (flat.max.X, flat.max.Y, self.bands[-1].high),
        )

    def fingerprint(self) -> Fingerprint:
        """The fingerprint of the solid this stack is, worked out from its bands.

        The volume and centroid sum each band's region's area and centroid through its
        height. The area is the walls, each region's perimeter times its height, and the
        flat faces: at each height where bands meet, the part of the region below or above
        that the other does not cover, and the lowest and highest regions whole.
        """
        if not self.bands:
            raise ValueError("cannot fingerprint an empty stack")
        volume = walls = 0.0
        moment = [0.0, 0.0, 0.0]
        for band in self.bands:
            height = band.high - band.low
            for face in band.region:
                flat = fingerprint(face)
                volume += flat.area * height
                moment[0] += flat.centroid[0] * flat.area * height
                moment[1] += flat.centroid[1] * flat.area * height
                moment[2] += (band.low + band.high) / 2 * flat.area * height
                walls += sum(_length(edge) for edge in face.edges()) * height
        flats = _area(self.bands[0].region) + _area(self.bands[-1].region)
        for below, above in itertools.pairwise(self.bands):
            if above.low - below.high > _LEVEL:
                flats += _area(below.region) + _area(above.region)
            else:
                flats += _area(_cut_of([below.region, above.region]))
                flats += _area(_cut_of([above.region, below.region]))
        low, high = self.bounds
        return Fingerprint(
            volume=volume,
            area=walls + flats,
            bbox_min=low,
            bbox_max=high,
            centroid=(moment[0] / volume, moment[1] / volume, moment[2] / volume),
        )


def union(stacks: Sequence[Stack]) -> Stack:
    """Everything that is in any of `stacks`."""
    return _by_bands(stacks, _union_of)


def cut(stack: Stack, tool: Stack) -> Stack:
    """What is in `stack` and not in `tool`."""
    return _by_bands([stack, tool], _cut_of)


def common(stack: Stack, tool: Stack) -> Stack:
    """What is in both `stack` and `tool`."""
    return _by_bands([stack, tool], _common_of)


def split(stack: Stack, z: float) -> tuple[Stack, Stack]:
    """What of `stack` lies below the height `z`, and what lies above it."""
    lower: list[Band] = []
    upper: list[Band] = []
    for band in stack.bands:
        if band.high - z <= _LEVEL:
            lower.append(band)
        elif z - band.low <= _LEVEL:
            upper.append(band)
        else:
            lower.append(Band(band.low, z, band.region))
            upper.append(Band(z, band.high, band.region))
    return Stack(tuple(lower)), Stack(tuple(upper))


type _Regions = list[tuple[bd.Face, ...]]
"""Each operand's region in one band."""


def _union_of(regions: _Regions) -> tuple[bd.Face, ...]:
    present = [region for region in regions if region]
    if len(present) <= 1:
        return present[0] if present else ()
    first, *rest = present
    return _planar(BRepAlgoAPI_Fuse, first, [face for region in rest for face in region])


def _cut_of(regions: _Regions) -> tuple[bd.Face, ...]:
    shape, tool = regions
    if not shape or not tool:
        return shape
    return _planar(BRepAlgoAPI_Cut, shape, tool)


def _common_of(regions: _Regions) -> tuple[bd.Face, ...]:
    shape, tool = regions
    if not shape or not tool:
        return ()
    return _planar(BRepAlgoAPI_Common, shape, tool)


def _by_bands(stacks: Sequence[Stack], combine: Callable[[_Regions], tuple[bd.Face, ...]]) -> Stack:
    """The stack whose region in each band is `combine` of the operands' regions there."""
    heights = (
        height for stack in stacks for band in stack.bands for height in (band.low, band.high)
    )
    levels = _levels(heights)
    bands: list[Band] = []
    for low, high in itertools.pairwise(levels):
        region = combine([stack.region_at((low + high) / 2) for stack in stacks])
        if region:
            bands.append(Band(low, high, region))
    return Stack(tuple(bands))


def _levels(heights: Iterable[float]) -> list[float]:
    """`heights`, lowest first, with those closer than `_LEVEL` taken as one."""
    levels: list[float] = []
    for height in sorted(heights):
        if not levels or height - levels[-1] > _LEVEL:
            levels.append(height)
    return levels


def _area(region: Iterable[bd.Face]) -> float:
    return sum(fingerprint(face).area for face in region)


def _length(edge: bd.Edge) -> float:
    return GCPnts_AbscissaPoint.Length_s(BRepAdaptor_Curve(edge.wrapped), _LENGTH_ERROR)


def _section(part: bd.Part, z: float) -> tuple[bd.Face, ...]:
    """The faces where the plane at height `z` cuts `part`, facing up."""
    box = part.bounding_box()
    if not box.min.Z < z < box.max.Z:
        return ()
    margin = 1.0 + max(box.size.X, box.size.Y)
    low_x, low_y = box.min.X - margin, box.min.Y - margin
    high_x, high_y = box.max.X + margin, box.max.Y + margin
    sheet = bd.Face(
        bd.Wire.make_polygon(
            [(low_x, low_y, z), (high_x, low_y, z), (high_x, high_y, z), (low_x, high_y, z)],
            close=True,
        )
    )
    return tuple(_facing_up(face) for face in _faces(_run(BRepAlgoAPI_Common, [part], [sheet])))


def _planar(
    builder: Callable[[], object], shapes: Sequence[bd.Face], tools: Sequence[bd.Face]
) -> tuple[bd.Face, ...]:
    """A boolean on two sets of faces in one plane, each region of the result one face."""
    result = _run(builder, shapes, tools)
    # The merge works on a copy, so that no edge the result shares with its operands is
    # rewritten in place.
    unify = ShapeUpgrade_UnifySameDomain(BRepBuilderAPI_Copy(result).Shape(), True, True, False)
    unify.AllowInternalEdges(False)
    unify.Build()
    return tuple(_facing_up(face) for face in _faces(unify.Shape()))


def _run(
    builder: Callable[[], object], shapes: Sequence[Shape[Any]], tools: Sequence[Shape[Any]]
) -> object:
    """The OpenCascade shape `builder` makes of `shapes` with `tools`, leaving them as
    they were."""
    arguments, others = List_TopoDS_Shape(), List_TopoDS_Shape()
    for shape in shapes:
        arguments.Append(shape.wrapped)
    for tool in tools:
        others.Append(tool.wrapped)
    operation = builder()
    operation.SetArguments(arguments)  # pyright: ignore[reportAttributeAccessIssue]
    operation.SetTools(others)  # pyright: ignore[reportAttributeAccessIssue]
    operation.SetNonDestructive(True)  # pyright: ignore[reportAttributeAccessIssue]
    operation.SetRunParallel(True)  # pyright: ignore[reportAttributeAccessIssue]
    operation.Build()  # pyright: ignore[reportAttributeAccessIssue]
    if not operation.IsDone():  # pyright: ignore[reportAttributeAccessIssue]
        raise RuntimeError(f"OpenCascade could not complete a {type(operation).__name__}")
    return operation.Shape()  # pyright: ignore[reportAttributeAccessIssue]


def _faces(topods: object) -> list[bd.Face]:
    return bd.Compound(topods).faces()  # pyright: ignore[reportArgumentType]


def _facing_up(face: bd.Face) -> bd.Face:
    if face.normal_at().Z > 0:
        return face
    return bd.Face(downcast(face.wrapped.Reversed()))  # pyright: ignore[reportArgumentType]
