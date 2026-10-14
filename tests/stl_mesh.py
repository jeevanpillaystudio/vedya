"""Reading binary STL files, for tests that check meshes against exact solids."""

from pathlib import Path

import numpy as np
from numpy.typing import NDArray

_HEADER = 80
_TRIANGLE = np.dtype([("normal", "<f4", (3,)), ("vertices", "<f4", (3, 3)), ("attribute", "<u2")])


def read_stl(path: Path) -> NDArray[np.float64]:
    """The triangles of the binary STL file at `path`, as an (n, 3, 3) array in its units."""
    data = path.read_bytes()
    count = int.from_bytes(data[_HEADER : _HEADER + 4], "little")
    expected = _HEADER + 4 + count * _TRIANGLE.itemsize
    if len(data) != expected:
        raise ValueError(f"{path} is not a binary STL: {len(data)} bytes, expected {expected}")
    triangles = np.frombuffer(data, dtype=_TRIANGLE, count=count, offset=_HEADER + 4)
    return triangles["vertices"].astype(np.float64)


def mesh_volume(triangles: NDArray[np.float64]) -> float:
    """The volume a closed, outward-facing triangle mesh encloses, by the divergence theorem."""
    a, b, c = triangles[:, 0], triangles[:, 1], triangles[:, 2]
    return float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0)


def mesh_bounds(triangles: NDArray[np.float64]) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """The low and high corners of the mesh's axis-aligned bounding box."""
    points = triangles.reshape(-1, 3)
    return points.min(axis=0), points.max(axis=0)
