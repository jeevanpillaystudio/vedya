"""Maps between the plane and a cylinder or a sphere, and samplers of the plane.

A point on the plane is a row (x, y), and a point in space a row (x, y, z); a map takes an
array of such rows and returns one row for each.

- A cylinder of `radius` stands on the XY plane around the z axis. The plane wraps around
  it: x goes once around in `length`, from the +x axis towards +y, and y is the height.
- A sphere of `radius` is centred on the origin. The rectangle `length` by `height` wraps
  over it: x is the longitude, once around in `length`, and y the angle from the +z pole,
  from 0 at y = 0 to π at y = `height`.

The samplers give the points that the maps carry: the cell centres of a rectangle, and
rings of points that fill a disc. The arithmetic is the 2024 library's
(`src/lib/src/coord_transform/` at the tag `fusion/head`), operation for operation, so each
map gives its values to the last bit.
"""

import math

import numpy as np
import numpy.typing as npt

__all__ = [
    "Points",
    "circle_samples",
    "from_cylinder",
    "from_sphere",
    "rectangle_samples",
    "to_cylinder",
    "to_sphere",
]

type Points = npt.NDArray[np.float64]
"""An array of points, one per row: (x, y) on the plane, (x, y, z) in space."""


def to_cylinder(points: npt.ArrayLike, length: float, radius: float) -> Points:
    """Each plane point (x, y) wrapped onto the cylinder of `radius`, as (x, y, z).

    x turns into the angle 2πx / `length` around the z axis, and y is the height.
    """
    _require_positive(length=length, radius=radius)
    x, y = _columns(points, 2)
    theta = 2 * np.pi * x / length
    return np.stack([radius * np.cos(theta), radius * np.sin(theta), y], axis=-1)


def from_cylinder(points: npt.ArrayLike, length: float) -> Points:
    """Each point (x, y, z) on a cylinder about the z axis unwrapped to the plane, as (x, y).

    The angle about the axis becomes x, between -`length`/2 and `length`/2, and z becomes
    y; how far a point lies from the axis is dropped. A plane point carried onto the
    cylinder and back keeps its y, and its x less a whole number of turns of `length`.
    """
    _require_positive(length=length)
    x, y, z = _columns(points, 3)
    theta = np.arctan2(y, x)
    return np.stack([length * theta / (2 * np.pi), z], axis=-1)


def to_sphere(points: npt.ArrayLike, length: float, height: float, radius: float) -> Points:
    """Each plane point (x, y) wrapped onto the sphere of `radius`, as (x, y, z).

    x turns into the longitude 2πx / `length`, and y into the angle πy / `height` from the
    +z pole.
    """
    _require_positive(length=length, height=height, radius=radius)
    x, y = _columns(points, 2)
    theta = 2 * np.pi * x / length
    phi = np.pi * y / height
    return np.stack(
        [
            radius * np.sin(phi) * np.cos(theta),
            radius * np.sin(phi) * np.sin(theta),
            radius * np.cos(phi),
        ],
        axis=-1,
    )


def from_sphere(points: npt.ArrayLike, length: float, height: float, radius: float) -> Points:
    """Each point (x, y, z) on the sphere of `radius` unwrapped to the plane, as (x, y).

    The longitude becomes x, between -`length`/2 and `length`/2, and the angle from the +z
    pole becomes y, from 0 to `height`. At a pole, where the longitude is not defined, x is
    0. A point further from the plane z = 0 than `radius` has no angle, and gives NaN.
    """
    _require_positive(length=length, height=height, radius=radius)
    x, y, z = _columns(points, 3)
    phi = np.arccos(z / radius)
    theta = np.arctan2(y, x)
    return np.stack([length * theta / (2 * np.pi), height * phi / np.pi], axis=-1)


def rectangle_samples(length: float, height: float, resolution: float) -> Points:
    """The centres of the square cells, `resolution` on a side, that tile the rectangle
    from (0, 0) to (`length`, `height`), as (x, y) rows, column by column.

    There are int(`length` / `resolution`) columns of int(`height` / `resolution`) cells:
    a part cell at the far edge is left out, and so is a whole one that the quotient's
    rounding falls just short of, as 0.3 / 0.1 does.
    """
    _require_positive(length=length, height=height, resolution=resolution)
    columns = np.arange(int(length / resolution)) * resolution + resolution / 2
    rows = np.arange(int(height / resolution)) * resolution + resolution / 2
    x, y = np.meshgrid(columns, rows, indexing="ij")
    return np.stack([x.ravel(), y.ravel()], axis=-1, dtype=np.float64)


def circle_samples(
    radius: float, resolution: float, centre: tuple[float, float] = (0.0, 0.0)
) -> Points:
    """Rings of points that fill the disc of `radius` about `centre`, as (x, y) rows,
    ring by ring from the centre out.

    There are int(2 · `radius` / `resolution`) rings, `resolution` / 2 apart from the centre
    out, and each holds int(2π · `radius` / `resolution`) points at equal angles from the
    +x direction. The first ring has no radius, so its points all lie at the centre, and
    the last falls short of the disc's edge by less than `resolution` / 2.
    """
    _require_positive(radius=radius, resolution=resolution)
    rings = np.arange(int(2 * radius / resolution))
    steps = int(2 * np.pi * radius / resolution)
    r = radius * (rings * resolution / (2 * radius))
    theta = 2 * np.pi * np.arange(steps) / steps
    r_grid, theta_grid = np.meshgrid(r, theta, indexing="ij")
    cx, cy = centre
    x = r_grid * np.cos(theta_grid)
    y = cy + r_grid * np.sin(theta_grid)
    return np.stack([(cx + x).ravel(), y.ravel()], axis=-1, dtype=np.float64)


def _columns(points: npt.ArrayLike, width: int) -> list[npt.NDArray[np.float64]]:
    """The columns of `points`, an array whose last axis has `width` entries."""
    array = np.asarray(points, dtype=np.float64)
    if array.ndim == 0 or array.shape[-1] != width:
        raise ValueError(
            f"expected points with {width} coordinates each, not an array of shape {array.shape}"
        )
    return [array[..., i] for i in range(width)]


def _require_positive(**values: float) -> None:
    for name, value in values.items():
        if not (value > 0 and math.isfinite(value)):
            raise ValueError(f"{name} must be positive, not {value!r}")
