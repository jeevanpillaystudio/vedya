"""What a design builds, and the numbers that pin it.

A `Model` is a design's named parts in the order it builds them. `union` joins solids
into one, as a design joins the slabs of a part; `aggregate` joins a model's parts into
the one solid that is milled or printed whole, and `slice_layers` cuts a solid into the
layers it is laser cut or printed in. `fingerprint` reduces a shape to the numbers the
tests compare against the goldens.

Every length is in millimetres.
"""

import copy
import itertools
import math
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

import build123d as bd
from build123d.topology import Shape
from build123d.topology.shape_core import downcast

# OCP is compiled and ships no type stubs, so its names are invisible to the type checker.
from OCP.BRep import BRep_Tool  # pyright: ignore[reportAttributeAccessIssue]
from OCP.BRepAdaptor import BRepAdaptor_Surface  # pyright: ignore[reportAttributeAccessIssue]
from OCP.BRepAlgoAPI import (
    BRepAlgoAPI_Common,  # pyright: ignore[reportAttributeAccessIssue]
    BRepAlgoAPI_Cut,  # pyright: ignore[reportAttributeAccessIssue]
    BRepAlgoAPI_Fuse,  # pyright: ignore[reportAttributeAccessIssue]
)
from OCP.BRepBuilderAPI import (
    BRepBuilderAPI_Copy,  # pyright: ignore[reportAttributeAccessIssue]
    BRepBuilderAPI_NurbsConvert,  # pyright: ignore[reportAttributeAccessIssue]
)
from OCP.BRepGProp import BRepGProp  # pyright: ignore[reportAttributeAccessIssue]
from OCP.collections import List_TopoDS_Shape  # pyright: ignore[reportAttributeAccessIssue]
from OCP.GeomAbs import GeomAbs_SurfaceType  # pyright: ignore[reportAttributeAccessIssue]
from OCP.GProp import GProp_GProps  # pyright: ignore[reportAttributeAccessIssue]
from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain  # pyright: ignore[reportAttributeAccessIssue]

__all__ = ["Fingerprint", "Model", "aggregate", "fingerprint", "slice_layers", "union"]

type Vec3 = tuple[float, float, float]

_PART_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")

# The largest relative error each face's adaptive integration may make.
_INTEGRATION_ERROR = 1e-9

_ANALYTIC = frozenset(
    {
        bd.GeomType.PLANE,
        bd.GeomType.CYLINDER,
        bd.GeomType.CONE,
        bd.GeomType.SPHERE,
        bd.GeomType.TORUS,
    }
)


@dataclass(frozen=True)
class Model:
    """A design's parts by name, in the order the design builds them.

    Part names are lowercase words joined by hyphens, such as `magnet-base`, because they
    become file names.

    Which parts a model holds, and under which names, is fixed once it is built. The parts
    themselves are build123d shapes, which can be changed in place; nothing here stops
    that, so code that reads a model leaves its parts as they are.
    """

    parts: Mapping[str, bd.Part]

    def __post_init__(self) -> None:
        if not self.parts:
            raise ValueError("a model needs at least one part")
        for name in self.parts:
            if not _PART_NAME.fullmatch(name):
                raise ValueError(f"part name {name!r} must be lowercase words joined by hyphens")
        # A read-only copy of the mapping: no part can be added, removed or renamed. The
        # parts are not copied, and stay as changeable as build123d makes them.
        object.__setattr__(self, "parts", MappingProxyType(dict(self.parts)))


def union(parts: Iterable[bd.Part]) -> bd.Part:
    """`parts` joined into one part: every point that lies in any of them.

    Where every part is a stack of slabs along z, as every part built from `slab` is, the
    parts are joined band by band. The heights of their level faces cut z into bands; in
    each band the parts' sections are joined in the plane, and the bands' slabs, which
    meet only at their level faces, are then fused. Other parts are fused as solids.

    The bands keep OpenCascade's 3D fuse from meeting one part inside another. Where a
    thin wedge of one part, such as an astroid's cusp, lies inside another part whose
    level face crosses it, the 3D fuse can keep the wedge's faces inside the result: the
    solid stays valid, but encloses the wedge twice, and its volume and area come out
    too large (Shire's core and layer-1 by 35 mm³), or the fuse drops a piece. Where the
    wall of one astroid meets the level face of a wider one, the 3D fuse approximates the
    curve they share and loosens its edges to 0.39 mm. Joined in the plane, where
    OpenCascade's booleans hold, no part meets another in 3D, and every edge stays on
    the curve it was drawn with.

    The union of one part is a copy of it. The parts are never changed. Raises
    `ValueError` when there are no parts.
    """
    solids = list(parts)
    if not solids:
        raise ValueError("a union needs at least one part")
    if len(solids) == 1:
        return copy.deepcopy(solids[0])
    if all(_is_stack(part) for part in solids):
        return _join_by_bands(solids)
    # build123d cleans what a boolean makes, and the clean can rewrite edges the result
    # shares with its operands, so the parts are fused as copies.
    first, *rest = (copy.deepcopy(part) for part in solids)
    return _as_part(first + rest)


def aggregate(model: Model) -> bd.Part:
    """Every part of `model` joined into one, as Fusion's aggregator joined every body:
    their `union`. A model of one part aggregates to a copy of it."""
    return union(model.parts.values())


def slice_layers(part: bd.Part, layer_height: float, max_count: int) -> list[bd.Part]:
    """`part` cut into layers `layer_height` high from the bottom up, then what is left.

    The cuts are level planes at `layer_height`, twice it, and so on above the bottom of
    `part`, at most `max_count` of them and none at or above its top. Each layer is what
    lies between a cut and the one below it, or the bottom, and the last element is what
    lies above the last cut. A 10 mm box cut at 3.2 mm gives three layers and 0.4 mm
    left; a part a whole number of layers high gives that many, the last as what is left.
    A layer with nothing in it is an empty `Part`. Together the layers hold `part`.

    This is the Fusion 360 slicer's cut, with each piece chosen by its height. A stack of
    slabs along z, as `union` makes, is cut band by band: each layer is swept from the
    sections of the bands it holds, so no plane meets the part in 3D. Other parts are
    cut by OpenCascade's boolean with a box.

    Raises `ValueError` for an empty part, a height that is not positive, or a count
    below one. The part is never changed.
    """
    if not layer_height > 0:
        raise ValueError(f"layer_height must be positive, not {layer_height!r}")
    if max_count < 1:
        raise ValueError(f"max_count must be at least 1, not {max_count!r}")
    if not part.solids():
        raise ValueError("cannot slice an empty part")
    bands = _bands(part) if _is_stack(part) else []
    if bands:
        bottom, top = bands[0][0], bands[-1][1]
    else:
        box = part.bounding_box()
        bottom, top = box.min.Z, box.max.Z
    count = min(max_count, math.floor((top - bottom + _LEVEL) / layer_height))
    cuts = [bottom + layer_height * (i + 1) for i in range(count)]
    cuts = [cut for cut in cuts if cut < top - _LEVEL]
    if bands:
        # A cut at a band's edge is taken there, so that no layer keeps a sliver of the
        # band beyond it.
        edges = _merged(edge for band in bands for edge in band[:2])
        cuts = [_snapped(cut, edges) for cut in cuts]
    spans = list(itertools.pairwise([bottom, *cuts, top]))
    if bands:
        return [_stacked(_clipped(bands, low, high)) for low, high in spans]
    return [
        _between(part, low, high, open_below=i == 0, open_above=i == len(spans) - 1)
        for i, (low, high) in enumerate(spans)
    ]


_LEVEL = 1e-7
"""Heights closer than this, in mm, are one: OpenCascade's own precision."""

_UPRIGHT = 1e-9
"""How far an upright face's direction may lean from the z axis, or a level face's
normal; as a sine or cosine."""


def _is_stack(part: bd.Part) -> bool:
    """Whether every face of `part` is a level plane, or upright: a plane, cylinder or
    extrusion along z. A solid bounded so is a stack of prisms along z."""
    for face in part.faces():
        surface = BRepAdaptor_Surface(face.wrapped)
        match surface.GetType():
            case GeomAbs_SurfaceType.GeomAbs_Plane:
                z = abs(surface.Plane().Axis().Direction().Z())
                if not (z < _UPRIGHT or z > 1 - _UPRIGHT):
                    return False
            case GeomAbs_SurfaceType.GeomAbs_Cylinder:
                if abs(surface.Cylinder().Axis().Direction().Z()) < 1 - _UPRIGHT:
                    return False
            case GeomAbs_SurfaceType.GeomAbs_SurfaceOfExtrusion:
                if abs(surface.Direction().Z()) < 1 - _UPRIGHT:
                    return False
            case _:
                return False
    return True


def _merged(heights: Iterable[float]) -> list[float]:
    """`heights`, lowest first, with those closer than `_LEVEL` taken as one."""
    levels: list[float] = []
    for height in sorted(heights):
        if not levels or height - levels[-1] > _LEVEL:
            levels.append(height)
    return levels


def _snapped(height: float, levels: Sequence[float]) -> float:
    """`height`, or the level in `levels` that lies within `_LEVEL` of it."""
    nearest = min(levels, key=lambda level: abs(level - height))
    return nearest if abs(nearest - height) <= _LEVEL else height


def _join_by_bands(parts: Sequence[bd.Part]) -> bd.Part:
    """The union of `parts`, each a stack of prisms along z, built band by band."""
    stacks = [_bands(part) for part in parts]
    levels = _merged(edge for stack in stacks for band in stack for edge in band[:2])
    joined: list[_Band] = []
    for low, high in itertools.pairwise(levels):
        middle = (low + high) / 2
        faces = [
            face
            for stack in stacks
            for below, above, region in stack
            if below < middle < above
            for face in region
        ]
        if faces:
            joined.append((low, high, _in_plane(BRepAlgoAPI_Fuse(), faces[:1], faces[1:])))
    return _stacked(joined)


type _Band = tuple[float, float, list[bd.Face]]
"""From one height up to another, a part's section there: faces in the plane z = 0."""


def _stacked(bands: Sequence[_Band]) -> bd.Part:
    """The solid each band's section sweeps from its lower height to its upper; an empty
    part if there are no bands."""
    slabs = [
        bd.Pos(0.0, 0.0, low)
        * bd.extrude(bd.Sketch(region), amount=high - low, dir=(0.0, 0.0, 1.0))
        for low, high, region in bands
    ]
    if not slabs:
        return bd.Part()
    first, *rest = slabs
    # The slabs meet only where their level faces coincide, the case OpenCascade's glue
    # is for.
    return _as_part(first.fuse(*rest, glue=True) if rest else first)


def _clipped(bands: Sequence[_Band], low: float, high: float) -> list[_Band]:
    """The parts of `bands` between the heights `low` and `high`.

    Each section is copied, since one band may be swept into two layers and a boolean
    on one may rewrite the edges it shares with the other."""
    return [
        (max(below, low), min(above, high), [copy.deepcopy(face) for face in region])
        for below, above, region in bands
        if min(above, high) - max(below, low) > _LEVEL
    ]


def _between(part: bd.Part, low: float, high: float, open_below: bool, open_above: bool) -> bd.Part:
    """What of `part` lies between the heights `low` and `high`, by a boolean with a box.

    Where the span is open below or above, the box reaches `_SHEET` beyond it there, so
    that a bounding box a hair too tight trims nothing."""
    box = part.bounding_box()
    below = low - _SHEET if open_below else low
    above = high + _SHEET if open_above else high
    cutter = bd.Pos(box.center().X, box.center().Y, below) * bd.Box(
        box.size.X + 2 * _SHEET, box.size.Y + 2 * _SHEET, above - below, align=_ON_FLOOR
    )
    made = _boolean(BRepAlgoAPI_Common(), [part.wrapped], [cutter.wrapped])
    return bd.Part(bd.Compound(made).solids())  # pyright: ignore[reportArgumentType]


_ON_FLOOR = (bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)
"""A box centred in x and y, standing on its base."""

_EXACT = 1e-6
"""The widest tolerance, in mm, of an edge that lies on its curves: OpenCascade leaves
exact edges at its precision, 1e-7, or a hair above it."""

_SHEET = 1.0
"""How far, in mm, a plane that cuts a section reaches beyond the part."""


def _bands(part: bd.Part) -> list[_Band]:
    """`part`, a stack of prisms along z, as its bands, lowest first.

    The sections come from the part's level faces where every edge of them is exact,
    since those faces keep the curves the part's regions were drawn with. Going up, at
    each level the section loses the faces that face up there, the tops of what ends, and
    gains those that face down, the bottoms of what starts.

    A 3D boolean can leave a level face only approximate. Where the wall of one astroid
    meets the level face of a wider one, as when Shire's core was fused in 3D, OpenCascade
    approximates the curve they share, misses the cusps' tips, and widens the edges'
    tolerance to cover it, to 0.39 mm. `union` makes no such part, but one made elsewhere
    is cut instead by a plane through the middle of each band.
    The plane meets the walls, which a boolean keeps as they were drawn; it misses about
    2e-7 of the section at a cusp, where the wall's curve turns back on itself.
    """
    ups: dict[float, list[bd.Face]] = {}
    downs: dict[float, list[bd.Face]] = {}
    for face in part.faces():
        surface = BRepAdaptor_Surface(face.wrapped)
        if surface.GetType() != GeomAbs_SurfaceType.GeomAbs_Plane:
            continue
        axis = surface.Plane().Axis()
        if abs(axis.Direction().Z()) < 1 - _UPRIGHT:
            continue
        z = axis.Location().Z()
        (ups if face.normal_at().Z > 0 else downs).setdefault(z, []).append(face)
    levels = _merged([*ups, *downs])
    level_faces = [face for found in (*ups.values(), *downs.values()) for face in found]
    if any(BRep_Tool.Tolerance_s(e.wrapped) > _EXACT for f in level_faces for e in f.edges()):
        return _cut(part, levels)

    def at(faces: dict[float, list[bd.Face]], level: float) -> list[bd.Face]:
        return [
            _flat(face, z)
            for z, found in faces.items()
            if abs(z - level) <= _LEVEL
            for face in found
        ]

    bands: list[_Band] = []
    region: list[bd.Face] = []
    for level, above in itertools.pairwise(levels):
        ending, starting = at(ups, level), at(downs, level)
        if region and ending:
            region = _in_plane(BRepAlgoAPI_Cut(), region, ending)
        if starting:
            shapes, tools = (region, starting) if region else (starting[:1], starting[1:])
            region = _in_plane(BRepAlgoAPI_Fuse(), shapes, tools)
        if region:
            bands.append((level, above, region))
    return bands


def _cut(part: bd.Part, levels: Sequence[float]) -> list[_Band]:
    """The bands of `part` between `levels`, each section cut by a plane through the
    band's middle."""
    box = part.bounding_box()
    sheet = bd.Face.make_rect(box.size.X + 2 * _SHEET, box.size.Y + 2 * _SHEET)
    bands: list[_Band] = []
    for low, high in itertools.pairwise(levels):
        middle = (low + high) / 2
        plane = bd.Pos(box.center().X, box.center().Y, middle) * sheet
        section = _boolean(BRepAlgoAPI_Common(), [part.wrapped], [plane.wrapped])
        faces = bd.Compound(section).faces()  # pyright: ignore[reportArgumentType]
        if faces:
            bands.append((low, high, [_flat(face, middle) for face in faces]))
    return bands


def _in_plane(operation: Any, shapes: Sequence[bd.Face], tools: Sequence[bd.Face]) -> list[bd.Face]:
    """A boolean on faces in the plane z = 0, each region of the result one face, facing
    up. The faces are left as they were."""
    if not tools:
        return list(shapes)
    made = _boolean(
        operation, [shape.wrapped for shape in shapes], [tool.wrapped for tool in tools]
    )
    # The merge works on a copy, so that no edge the result shares with its operands is
    # rewritten in place.
    unify = ShapeUpgrade_UnifySameDomain(BRepBuilderAPI_Copy(made).Shape(), True, True, False)
    unify.AllowInternalEdges(False)
    unify.Build()
    faces = bd.Compound(unify.Shape()).faces()  # pyright: ignore[reportArgumentType]
    return [_flat(face, 0.0) for face in faces]


def _boolean(operation: Any, shapes: Iterable[Any], tools: Iterable[Any]) -> Any:
    """What `operation` makes of `shapes` and `tools`, which it leaves as they were."""
    arguments, others = List_TopoDS_Shape(), List_TopoDS_Shape()
    for shape in shapes:
        arguments.Append(shape)
    for tool in tools:
        others.Append(tool)
    operation.SetArguments(arguments)
    operation.SetTools(others)
    operation.SetNonDestructive(True)
    operation.SetRunParallel(True)
    operation.Build()
    if not operation.IsDone():
        raise RuntimeError(f"OpenCascade could not complete a {type(operation).__name__}")
    return operation.Shape()


def _flat(face: bd.Face, z: float) -> bd.Face:
    """`face`, which lies at height `z`, moved to the plane z = 0 and facing up."""
    if z:
        face = face.moved(bd.Location((0.0, 0.0, -z)))
    if face.normal_at().Z > 0:
        return face
    return bd.Face(downcast(face.wrapped.Reversed()))  # pyright: ignore[reportArgumentType]


def _as_part(shape: Shape[Any]) -> bd.Part:
    return shape if isinstance(shape, bd.Part) else bd.Part(shape.solids())


@dataclass(frozen=True)
class Fingerprint:
    """The numbers that identify a shape.

    Attributes:
        volume: The enclosed volume, in mm³; 0 for a shape with no closed shell.
        area: The total area of the shape's faces, in mm².
        bbox_min: The low corner of the tightest axis-aligned bounding box.
        bbox_max: The high corner of that box.
        centroid: The centre of the volume, or of the area for a shape with no volume.
    """

    volume: float
    area: float
    bbox_min: Vec3
    bbox_max: Vec3
    centroid: Vec3


def fingerprint(shape: Shape[Any]) -> Fingerprint:
    """The volume, area, bounding box and centroid of `shape`, to a relative 1e-8 or better.

    The integrals are chosen for faces bounded or swept by splines, such as an astroid's:

    - build123d's `area` integrates at a fixed order, which misreads the area of a flat
      face bounded by a spline by 12%.
    - OpenCascade's adaptive Gauss rule fails on the wall a spline sweeps, so volume and
      centroid use its Gauss-Kronrod rule, which converges there.
    - Areas of faces that are not planes, cylinders, cones, spheres or tori are taken on
      their NURBS form, where the adaptive rule converges. Analytic faces are integrated
      as they are, since their NURBS form loses precision.
    """
    if not shape or not shape.faces():
        raise ValueError("cannot fingerprint an empty shape")
    volume = GProp_GProps()
    BRepGProp.VolumePropertiesGK_s(
        shape.wrapped, volume, _INTEGRATION_ERROR, OnlyClosed=True, IsUseSpan=True, CGFlag=True
    )
    surface = GProp_GProps()
    for face in shape.faces():
        exact = face.geom_type in _ANALYTIC
        topods = face.wrapped if exact else BRepBuilderAPI_NurbsConvert(face.wrapped, True).Shape()
        # With a tolerance, OpenCascade replaces what a framework holds instead of adding to it.
        one = GProp_GProps()
        BRepGProp.SurfaceProperties_s(topods, one, _INTEGRATION_ERROR)
        surface.Add(one)
    centre = (volume if volume.Mass() > 0 else surface).CentreOfMass()
    box = shape.bounding_box()
    return Fingerprint(
        volume=volume.Mass(),
        area=surface.Mass(),
        bbox_min=(box.min.X, box.min.Y, box.min.Z),
        bbox_max=(box.max.X, box.max.Y, box.max.Z),
        centroid=(centre.X(), centre.Y(), centre.Z()),
    )
