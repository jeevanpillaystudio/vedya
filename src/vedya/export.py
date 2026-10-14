"""Writing a shape to a file, in the format its suffix names.

STEP keeps the exact geometry, in millimetres. STL is a triangle mesh: no point of it
lies further than `LINEAR_TOLERANCE` from the exact surface, and no two neighbouring
triangles of a curved face turn by more than `ANGULAR_TOLERANCE`.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import build123d as bd
from build123d.topology import Shape

# OCP is compiled and ships no type stubs, so its names are invisible to the type checker.
from OCP.BRepMesh import BRepMesh_IncrementalMesh  # pyright: ignore[reportAttributeAccessIssue]
from OCP.StlAPI import StlAPI_Writer  # pyright: ignore[reportAttributeAccessIssue]

__all__ = ["ANGULAR_TOLERANCE", "LINEAR_TOLERANCE", "SUFFIXES", "export"]

LINEAR_TOLERANCE = 0.01
"""The furthest, in mm, a mesh may lie from the exact surface."""

ANGULAR_TOLERANCE = 0.1
"""The largest angle, in radians, between neighbouring triangles of a curved face."""


def _write_step(shape: Shape[Any], path: Path) -> bool:
    return bd.export_step(shape, path)


def _write_stl(shape: Shape[Any], path: Path) -> bool:
    # build123d's `export_stl` takes its tolerance relative to each edge's size, which
    # lets a 640 mm circle stray 0.8 mm. Mesh to an absolute tolerance instead.
    BRepMesh_IncrementalMesh(shape.wrapped, LINEAR_TOLERANCE, False, ANGULAR_TOLERANCE, True)
    writer = StlAPI_Writer()
    writer.ASCIIMode = False
    return writer.Write(shape.wrapped, str(path))


_WRITERS: dict[str, Callable[[Shape[Any], Path], bool]] = {
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
