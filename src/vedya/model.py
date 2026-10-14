"""What a design builds, and the numbers that pin it.

A `Model` is a design's named parts in the order it builds them. `aggregate` fuses them
into the one solid that is milled or printed whole. `fingerprint` reduces a shape to the
numbers the tests compare against the goldens.

Every length is in millimetres.
"""

import copy
import itertools
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

__all__ = ["Fingerprint", "Model", "aggregate", "fingerprint"]

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
    """

    parts: Mapping[str, bd.Part]

    def __post_init__(self) -> None:
        if not self.parts:
            raise ValueError("a model needs at least one part")
        for name in self.parts:
            if not _PART_NAME.fullmatch(name):
                raise ValueError(f"part name {name!r} must be lowercase words joined by hyphens")
        # A read-only copy, so a model cannot change after it is built.
        object.__setattr__(self, "parts", MappingProxyType(dict(self.parts)))


def aggregate(model: Model) -> bd.Part:
    """Every part of `model` fused into one, as Fusion's aggregator joined every body.

    Where every part is a stack of slabs along z, as every part a design builds from
    `slab` is, the parts are joined band by band. The heights of their level faces cut z
    into bands; in each band the parts' sections are joined in the plane, and the bands'
    slabs, which meet only at their level faces, are then fused. Other parts are fused
    as solids.

    The bands keep OpenCascade's 3D fuse from meeting one part inside another. Where a
    thin wedge of one part, such as an astroid's cusp, lies inside another part whose
    level face crosses it, the 3D fuse can keep the wedge's faces inside the result: the
    solid stays valid, but encloses the wedge twice, and its volume and area come out
    too large (Shire's core and layer-1 by 35 mm³), or the fuse drops a piece. Joined in
    the plane, where OpenCascade's booleans hold, no part meets another in 3D.

    A model of one part aggregates to a copy of it. The parts are never changed.
    """
    parts = list(model.parts.values())
    if len(parts) == 1:
        return copy.deepcopy(parts[0])
    if all(_is_stack(part) for part in parts):
        return _join_by_bands(parts)
    # build123d cleans what a boolean makes, and the clean can rewrite edges the result
    # shares with its operands, so the parts are fused as copies.
    first, *rest = (copy.deepcopy(part) for part in parts)
    return _as_part(first + rest)


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


def _join_by_bands(parts: Sequence[bd.Part]) -> bd.Part:
    """The union of `parts`, each a stack of prisms along z, built band by band."""
    stacks = [_bands(part) for part in parts]
    levels = _merged(edge for stack in stacks for band in stack for edge in band[:2])
    slabs: list[bd.Part] = []
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
            region = bd.Sketch(_in_plane(BRepAlgoAPI_Fuse(), faces[:1], faces[1:]))
            rise = bd.extrude(region, amount=high - low, dir=(0.0, 0.0, 1.0))
            slabs.append(bd.Pos(0.0, 0.0, low) * rise)
    first, *rest = slabs
    # The slabs meet only where their level faces coincide, the case OpenCascade's glue
    # is for.
    return _as_part(first.fuse(*rest, glue=True) if rest else first)


type _Band = tuple[float, float, list[bd.Face]]
"""From one height up to another, a part's section there: faces in the plane z = 0."""

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
    meets the level face of a wider one, as in Shire's core, OpenCascade approximates the
    curve they share, misses the cusps' tips, and widens the edges' tolerance to cover it,
    to 0.39 mm. Such a part is cut instead by a plane through the middle of each band.
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
