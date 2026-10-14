"""A flow field: a grid of unit vectors whose angles follow Perlin noise.

This module needs the `examples` extra, which brings `noise`, the Perlin noise the 2024
library drew with: `uv sync --extra examples`, or `pip install 'vedya[examples]'`. The
rest of the package imports without it.
"""

import math

import numpy as np
import numpy.typing as npt

try:
    # noise is compiled, and ships no type stubs.
    from noise import pnoise2  # pyright: ignore[reportMissingTypeStubs]
except ModuleNotFoundError as error:
    raise ModuleNotFoundError(
        f"vedya.flowfield needs the examples extra, which brings {error.name}: install it "
        "with `uv sync --extra examples` or `pip install 'vedya[examples]'`",
        name=error.name,
    ) from error

__all__ = ["EXTENT", "flow_field"]

EXTENT = 5.0
"""How far the grid runs across and up, from 0, in the noise's units before `scale`."""


def flow_field(
    width: int = 150,
    height: int = 150,
    scale: float = 0.1,
    octaves: int = 6,
    persistence: float = 0.5,
    lacunarity: float = 2.0,
) -> npt.NDArray[np.float64]:
    """The flow field on a grid `width` points across and `height` points up.

    Returns an array of shape (`height`, `width`, 2). At row i and column j it holds the
    unit vector (cos a, sin a), where a is 2π times the Perlin noise at
    (x_j · `scale`, y_i · `scale`); x_j and y_i run evenly from 0 to `EXTENT` across the
    columns and up the rows. The noise sums `octaves` layers, each `lacunarity` times
    finer than the last and weighted `persistence` times as much, and repeats every
    `width` units across and `height` up, with base 0. The defaults are the 2024 library's
    example's, and so is the arithmetic, so each vector equals that library's to the last
    bit.

    Raises `ValueError` for a grid without a point, fewer than one octave, or a scale,
    persistence or lacunarity that is not positive.
    """
    if width < 1 or height < 1:
        raise ValueError(f"the grid needs a point, not {width!r} across and {height!r} up")
    if octaves < 1:
        raise ValueError(f"octaves must be at least 1, not {octaves!r}")
    for name, value in (("scale", scale), ("persistence", persistence), ("lacunarity", lacunarity)):
        if not (value > 0 and math.isfinite(value)):
            raise ValueError(f"{name} must be positive, not {value!r}")
    x, y = np.meshgrid(np.linspace(0, EXTENT, width), np.linspace(0, EXTENT, height))
    noise = np.array(
        [
            [
                pnoise2(
                    x[i, j] * scale,
                    y[i, j] * scale,
                    octaves=octaves,
                    persistence=persistence,
                    lacunarity=lacunarity,
                    repeatx=width,
                    repeaty=height,
                    base=0,
                )
                for j in range(width)
            ]
            for i in range(height)
        ],
        dtype=np.float64,
    )
    angle = noise * 2 * np.pi
    return np.stack([np.cos(angle), np.sin(angle)], axis=-1)
