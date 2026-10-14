"""Reading the mesh files export writes, binary STL and 3MF, for tests that check meshes
against exact solids. The 3MF reader is the standard library's zip and XML, so that it
does not share the writer's library."""

import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree

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


_RELATIONSHIPS = "{http://schemas.openxmlformats.org/package/2006/relationships}"
_MODEL_RELATIONSHIP = "http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"
_CORE = "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"


@dataclass(frozen=True)
class Mesh3mf:
    """What a 3MF file builds: its unit, its corners, and its triangles as three corners
    each, every object's placed as the build places it."""

    unit: str
    points: NDArray[np.float64]
    corners: NDArray[np.intp]

    @property
    def triangles(self) -> NDArray[np.float64]:
        """The triangles as an (n, 3, 3) array of their corners' positions."""
        return self.points[self.corners]


def read_3mf(path: Path) -> Mesh3mf:
    """The mesh the 3MF file at `path` builds: each build item's object, transformed."""
    with zipfile.ZipFile(path) as package:
        relationships = ElementTree.fromstring(package.read("_rels/.rels"))
        targets = [
            found.attrib["Target"]
            for found in relationships.iter(f"{_RELATIONSHIPS}Relationship")
            if found.attrib["Type"] == _MODEL_RELATIONSHIP
        ]
        if len(targets) != 1:
            raise ValueError(f"{path} names {len(targets)} 3D models, not one")
        model = ElementTree.fromstring(package.read(targets[0].lstrip("/")))
    objects = {found.attrib["id"]: found for found in model.iter(f"{_CORE}object")}
    points: list[NDArray[np.float64]] = []
    corners: list[NDArray[np.intp]] = []
    count = 0
    for item in model.iter(f"{_CORE}item"):
        mesh = objects[item.attrib["objectid"]].find(f"{_CORE}mesh")
        if mesh is None:
            raise ValueError(f"{path}: object {item.attrib['objectid']} has no mesh")
        placed = np.array(
            [[float(v.attrib[axis]) for axis in "xyz"] for v in mesh.iter(f"{_CORE}vertex")]
        )
        if "transform" in item.attrib:
            # Twelve numbers: a 3 by 3 matrix, row by row, that a row vector multiplies,
            # then the translation.
            values = np.array([float(value) for value in item.attrib["transform"].split()])
            placed = placed @ values[:9].reshape(3, 3) + values[9:]
        points.append(placed)
        corners.append(
            np.array(
                [
                    [int(t.attrib[k]) for k in ("v1", "v2", "v3")]
                    for t in mesh.iter(f"{_CORE}triangle")
                ],
                dtype=np.intp,
            )
            + count
        )
        count += len(placed)
    return Mesh3mf(
        unit=model.attrib.get("unit", "millimeter"),
        points=np.concatenate(points),
        corners=np.concatenate(corners),
    )


def is_closed(corners: NDArray[np.intp]) -> bool:
    """Whether the triangles, as three corners each, close up consistently: every edge
    between two corners is crossed once each way, by two triangles."""
    starts = corners.reshape(-1).astype(np.int64)
    ends = np.roll(corners, -1, axis=1).reshape(-1).astype(np.int64)
    size = int(corners.max()) + 1
    forward, backward = np.sort(starts * size + ends), np.sort(ends * size + starts)
    # No edge is crossed twice the same way, and each is crossed the other way as often.
    return not np.any(forward[1:] == forward[:-1]) and np.array_equal(forward, backward)


def mesh_volume(triangles: NDArray[np.float64]) -> float:
    """The volume a closed, outward-facing triangle mesh encloses, by the divergence theorem."""
    a, b, c = triangles[:, 0], triangles[:, 1], triangles[:, 2]
    return float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0)


def mesh_bounds(triangles: NDArray[np.float64]) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """The low and high corners of the mesh's axis-aligned bounding box."""
    points = triangles.reshape(-1, 3)
    return points.min(axis=0), points.max(axis=0)
