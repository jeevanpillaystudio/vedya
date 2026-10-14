"""What a design builds, and the numbers that pin it.

A `Model` is a design's named parts in the order it builds them. `aggregate` fuses them
into the one solid that is milled or printed whole. `fingerprint` reduces a shape to the
numbers the tests compare against the goldens.

Every length is in millimetres.
"""

import copy
import re
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

import build123d as bd
from build123d.topology import Shape

# OCP is compiled and ships no type stubs, so its names are invisible to the type checker.
from OCP.BRepBuilderAPI import BRepBuilderAPI_NurbsConvert  # pyright: ignore[reportAttributeAccessIssue]
from OCP.BRepGProp import BRepGProp  # pyright: ignore[reportAttributeAccessIssue]
from OCP.GProp import GProp_GProps  # pyright: ignore[reportAttributeAccessIssue]

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

    The parts are fused as copies. build123d cleans what a boolean makes, and the clean
    can rewrite edges the result shares with its operands, which leaves the operands
    unfit for another boolean; the model's parts stay as they were built.
    """
    first, *rest = (copy.deepcopy(part) for part in model.parts.values())
    fused = first + rest
    return fused if isinstance(fused, bd.Part) else bd.Part(fused.solids())


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
