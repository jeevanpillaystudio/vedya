"""Writing a shape to a file, in the format its suffix names.

STEP keeps the exact geometry, in millimetres. STL and 3MF are triangle meshes, in
millimetres: no point of one lies further than `LINEAR_TOLERANCE` from the exact surface,
and no two neighbouring triangles of a curved face turn by more than `ANGULAR_TOLERANCE`.
A 3MF file holds the shape as one object whose triangles share their corners, so that
its mesh is closed and every side between two corners is crossed by two triangles, as a
slicer for printing expects.
"""

import math
from collections.abc import Callable
from pathlib import Path
from typing import Any

import build123d as bd
import numpy as np
import numpy.typing as npt
from build123d.topology import Shape

# lib3mf, which build123d writes 3MF with, ships no type stubs.
from lib3mf import Lib3MF  # pyright: ignore[reportMissingTypeStubs]

# OCP is compiled and ships no type stubs, so its names are invisible to the type checker.
from OCP.BRep import BRep_Tool  # pyright: ignore[reportAttributeAccessIssue]
from OCP.BRepMesh import BRepMesh_IncrementalMesh  # pyright: ignore[reportAttributeAccessIssue]
from OCP.StlAPI import StlAPI_Writer  # pyright: ignore[reportAttributeAccessIssue]
from OCP.TopAbs import TopAbs_Orientation  # pyright: ignore[reportAttributeAccessIssue]
from OCP.TopLoc import TopLoc_Location  # pyright: ignore[reportAttributeAccessIssue]

__all__ = ["ANGULAR_TOLERANCE", "LINEAR_TOLERANCE", "SUFFIXES", "export"]

LINEAR_TOLERANCE = 0.01
"""The furthest, in mm, a mesh may lie from the exact surface."""

ANGULAR_TOLERANCE = 0.1
"""The largest angle, in radians, between neighbouring triangles of a curved face."""


def _write_step(shape: Shape[Any], path: Path) -> bool:
    return bd.export_step(shape, path)


def _mesh_absolute(shape: Shape[Any]) -> None:
    # build123d meshes with a tolerance relative to each edge's size, which lets a 640 mm
    # circle stray 0.8 mm, and its 3MF writer meshes a copy so. Mesh to an absolute
    # tolerance instead; OpenCascade keeps the mesh on the shape for the writers.
    BRepMesh_IncrementalMesh(shape.wrapped, LINEAR_TOLERANCE, False, ANGULAR_TOLERANCE, True)


def _write_stl(shape: Shape[Any], path: Path) -> bool:
    _mesh_absolute(shape)
    writer = StlAPI_Writer()
    writer.ASCIIMode = False
    return writer.Write(shape.wrapped, str(path))


type _Points = npt.NDArray[np.float32]
type _Triangles = npt.NDArray[np.uint32]


def _triangles(shape: Shape[Any]) -> tuple[_Points, _Triangles]:
    """`shape` meshed: its distinct corners, and each triangle as three of them, in the
    order that faces out of the solid.

    Each face is meshed on its own, and the faces that meet at an edge put their corners
    at the same points along it. The points are kept to single precision, as 3MF keeps
    them, and points equal there are one corner.
    """
    _mesh_absolute(shape)
    points: list[tuple[float, float, float]] = []
    corners: list[tuple[int, int, int]] = []
    for face in shape.faces():
        location = TopLoc_Location()
        mesh = BRep_Tool.Triangulation_s(face.wrapped, location)
        if mesh is None:
            raise RuntimeError("OpenCascade could not mesh a face of the shape")
        move = location.Transformation()
        first = len(points)
        for i in range(1, mesh.NbNodes() + 1):
            point = mesh.Node(i).Transformed(move)
            points.append((point.X(), point.Y(), point.Z()))
        # A face turned inside out by its solid lists its triangles the other way round.
        reverse = face.wrapped.Orientation() == TopAbs_Orientation.TopAbs_REVERSED
        for i in range(1, mesh.NbTriangles() + 1):
            triangle = mesh.Triangle(i)
            a, b, c = (first + triangle.Value(k) - 1 for k in (1, 2, 3))
            corners.append((a, c, b) if reverse else (a, b, c))
    distinct, index = np.unique(np.asarray(points, dtype=np.float32), axis=0, return_inverse=True)
    triangles = index.reshape(-1)[np.asarray(corners, dtype=np.intp)]
    # A triangle two of whose corners became one has no area, and is left out.
    a, b, c = triangles.T
    kept = triangles[(a != b) & (b != c) & (c != a)]
    return distinct, kept.astype(np.uint32)


type _Side = tuple[int, int]
"""A side of a triangle, from one corner to the next in the triangle's order."""


def _separated(points: _Points, triangles: _Triangles) -> tuple[_Points, _Triangles]:
    """The mesh, with every side between two corners crossed by two triangles.

    Where two pieces of a solid touch along an edge, as Shire's layers do where one
    ends and another starts across the same circle, four faces of the solid meet there,
    and four triangles at each side along it; a slicer for printing wants two. Around
    such a side, each triangle is paired with the one across the solid beside it, and
    each pair is split at a point of its own in the middle of the side. The pieces then
    meet only at the sides' ends, and the mesh encloses what it did.
    """
    size = len(points)
    froms = triangles.reshape(-1).astype(np.int64)
    tos = triangles[:, [1, 2, 0]].reshape(-1).astype(np.int64)
    sides, uses = np.unique(froms * size + tos, return_counts=True)
    crowded = sorted(
        {
            (min(start, end), max(start, end))
            for start, end in (divmod(side, size) for side in sides[uses > 1].tolist())
        }
    )
    if not crowded:
        return points, triangles
    touched = list({corner for side in crowded for corner in side})
    across: dict[_Side, list[int]] = {}
    for row in np.nonzero(np.isin(triangles, touched).any(axis=1))[0].tolist():
        a, b, c = (int(corner) for corner in triangles[row])
        for side in ((a, b), (b, c), (c, a)):
            across.setdefault(side, []).append(row)
    middles: dict[tuple[int, _Side], int] = {}
    added: list[npt.NDArray[np.float64]] = []
    for start, end in crowded:
        for row, other in _pairs(points, triangles, (start, end), across):
            middles[(row, (start, end))] = middles[(other, (end, start))] = size + len(added)
            added.append((points[start].astype(np.float64) + points[end]) / 2)
    split = sorted({row for row, _ in middles})
    pieces: list[tuple[int, int, int]] = []
    for row in split:
        a, b, c = (int(corner) for corner in triangles[row])
        outline: list[int] = []
        for side in ((a, b), (b, c), (c, a)):
            outline.append(side[0])
            if (row, side) in middles:
                outline.append(middles[(row, side)])
        # A fan from a middle point: every point it reaches lies off the side it is on.
        first = next(i for i, corner in enumerate(outline) if corner >= size)
        outline = outline[first:] + outline[:first]
        pieces.extend((outline[0], outline[i], outline[i + 1]) for i in range(1, len(outline) - 1))
    kept = np.delete(triangles, split, axis=0)
    return (
        np.concatenate([points, np.asarray(added, dtype=np.float32).reshape(-1, 3)]),
        np.concatenate([kept, np.asarray(pieces, dtype=np.uint32).reshape(-1, 3)]),
    )


def _pairs(
    points: _Points, triangles: _Triangles, side: _Side, across: dict[_Side, list[int]]
) -> list[tuple[int, int]]:
    """Each triangle that crosses `side` forwards, with the one that crosses it back on
    the other face of the solid between them.

    Turning about the side, a triangle that crosses it forwards faces out the way of the
    turn, with the solid behind it, and one that crosses it back faces out against the
    turn, with the solid ahead of it. So each that crosses back is paired with the next
    triangle on, which must cross forwards.
    """
    start, end = side
    origin = points[start].astype(np.float64)
    axis = points[end].astype(np.float64) - origin
    axis /= np.linalg.norm(axis)
    first = np.cross(axis, (1.0, 0.0, 0.0))
    if np.linalg.norm(first) < 0.5:
        first = np.cross(axis, (0.0, 1.0, 0.0))
    first /= np.linalg.norm(first)
    second = np.cross(axis, first)
    forwards, backwards = across.get((start, end), []), across.get((end, start), [])
    wings: list[tuple[float, bool, int]] = []
    for forward, rows in ((True, forwards), (False, backwards)):
        for row in rows:
            far = next(int(corner) for corner in triangles[row] if corner not in side)
            wing = points[far].astype(np.float64) - origin
            wings.append((math.atan2(wing @ second, wing @ first), forward, row))
    wings.sort()
    pairs = [
        (wings[(i + 1) % len(wings)][2], row)
        for i, (_, forward, row) in enumerate(wings)
        if not forward and wings[(i + 1) % len(wings)][1]
    ]
    if len(forwards) != len(backwards) or len(pairs) != len(forwards):
        raise RuntimeError("the triangles that meet at a side of the mesh do not pair")
    return pairs


def _write_3mf(shape: Shape[Any], path: Path) -> bool:
    points, triangles = _separated(*_triangles(shape))
    mesher = bd.Mesher(unit=bd.Unit.MM)
    model = mesher.model
    if model is None:
        raise RuntimeError("lib3mf made no model to write")
    mesh = model.AddMeshObject()
    mesh.SetName(path.stem)
    mesh.SetGeometry(
        (Lib3MF.Position * len(points)).from_buffer_copy(np.ascontiguousarray(points)),
        (Lib3MF.Triangle * len(triangles)).from_buffer_copy(np.ascontiguousarray(triangles)),
    )
    if not mesh.IsManifoldAndOriented():
        raise RuntimeError(f"the mesh for {path.name!r} is not closed")
    model.AddBuildItem(mesh, mesher.wrapper.GetIdentityTransform())
    # Mesher's own `write` reads the format from a suffix in lower case only.
    model.QueryWriter("3mf").WriteToFile(str(path))
    return True


_WRITERS: dict[str, Callable[[Shape[Any], Path], bool]] = {
    ".3mf": _write_3mf,
    ".step": _write_step,
    ".stl": _write_stl,
    ".stp": _write_step,
}

SUFFIXES: tuple[str, ...] = tuple(sorted(_WRITERS))
"""The file suffixes `export` can write."""


def export(shape: Shape[Any], path: Path | str) -> None:
    """Write `shape` to `path`, in the format the suffix of `path` names.

    Raises `ValueError` for an empty shape or a suffix not in `SUFFIXES`, and `OSError`
    when the file cannot be written.
    """
    path = Path(path)
    writer = _WRITERS.get(path.suffix.lower())
    if writer is None:
        raise ValueError(
            f"cannot write {path.name!r}: the supported suffixes are {', '.join(SUFFIXES)}"
        )
    if not shape or not shape.faces():
        raise ValueError(f"cannot write {path.name!r}: the shape is empty")
    if not path.parent.is_dir():
        raise FileNotFoundError(f"no such folder: {path.parent}")
    if not writer(shape, path):
        raise OSError(f"could not write {path}")
