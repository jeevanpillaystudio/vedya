"""The stencil of an image, and a 3D figure of clouds of points.

This module needs the `render` extra, which brings OpenCV and plotly:
`uv sync --extra render`, or `pip install 'vedya[render]'`. The rest of the package
imports without it.
"""

from collections.abc import Mapping
from itertools import cycle
from pathlib import Path

import numpy as np
import numpy.typing as npt

try:
    import cv2
    import plotly.graph_objects as go
except ModuleNotFoundError as error:
    raise ModuleNotFoundError(
        f"vedya.render needs the render extra, which brings {error.name}: install it with "
        "`uv sync --extra render` or `pip install 'vedya[render]'`",
        name=error.name,
    ) from error

__all__ = ["COLOURS", "Image", "point_cloud_figure", "read_image", "stencil", "write_image"]

type Image = npt.NDArray[np.uint8]
"""An 8-bit image, as OpenCV holds one: rows of pixels, each a grey level or blue, green
and red levels."""

COLOURS = ("red", "blue", "green", "orange", "purple")
"""The colours `point_cloud_figure` gives its clouds, in order, round again after the
last."""


def read_image(path: Path | str) -> Image:
    """The image at `path`, as blue, green and red levels, whatever channels it has.

    A grey image is given three equal channels, and an alpha channel is dropped, as
    OpenCV reads in colour. Raises `FileNotFoundError` for a missing file, and
    `ValueError` for one OpenCV cannot read as an image.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"no such file: {path}")
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"cannot read {path.name!r} as an image")
    return np.asarray(image, dtype=np.uint8)


def write_image(image: Image, path: Path | str) -> None:
    """Write `image` to `path`, in the format its suffix names, such as `.png`.

    Raises `FileNotFoundError` for a missing folder, `ValueError` for a suffix OpenCV
    has no writer for, and `OSError` when the file cannot be written.
    """
    path = Path(path)
    if not path.parent.is_dir():
        raise FileNotFoundError(f"no such folder: {path.parent}")
    try:
        written = cv2.imwrite(str(path), image)
    except cv2.error as error:
        raise ValueError(f"cannot write {path.name!r}: OpenCV has no writer for it") from error
    if not written:
        raise OSError(f"could not write {path}")


def stencil(
    image: Image,
    *,
    blur: int = 5,
    edges: tuple[float, float] = (100.0, 180.0),
    block_size: int = 5,
    offset: float = 12.0,
) -> Image:
    """The stencil of `image`: its dark strokes and its outlines in black, on white.

    The steps are the 2024 library's (`render_2d_stencil`), whose values are the
    defaults:
    - The image is turned grey.
    - The strokes: each pixel at least `offset` levels darker than the Gaussian-weighted
      mean of the square of `block_size` pixels a side around it.
    - The outlines: the edges Canny finds, with hysteresis thresholds `edges`, in the
      grey image blurred by a Gaussian `blur` pixels square, thickened by a pixel each way.
      Each outermost outline is drawn on the strokes as a line one pixel wide.
    - Strokes and outlines are black, and everything else white.

    `image` is grey, as rows of levels, or colour, as rows of blue, green and red
    levels. Returns a grey image of the same height and width, every pixel 0 or 255.
    Raises `ValueError` for an image of another form, and for an even or too small
    `blur` or `block_size`.
    """
    # OpenCV reads an array row by row, so a view that skips through memory is copied.
    pixels = np.ascontiguousarray(image)
    if pixels.dtype != np.uint8 or not (
        pixels.ndim == 2 or (pixels.ndim == 3 and pixels.shape[2] == 3)
    ):
        raise ValueError(
            "expected an 8-bit grey or blue-green-red image, "
            f"not an array of {pixels.dtype} of shape {pixels.shape}"
        )
    if blur < 1 or blur % 2 == 0:
        raise ValueError(f"blur must be an odd number of pixels, not {blur!r}")
    if block_size < 3 or block_size % 2 == 0:
        raise ValueError(f"block_size must be an odd number of pixels from 3, not {block_size!r}")
    grey = pixels if pixels.ndim == 2 else cv2.cvtColor(pixels, cv2.COLOR_BGR2GRAY)

    blurred = cv2.GaussianBlur(grey, (blur, blur), 0)
    low, high = edges
    outlines = cv2.Canny(blurred, threshold1=low, threshold2=high)
    outlines = cv2.dilate(outlines, np.ones((3, 3), np.uint8), iterations=1)

    light = cv2.adaptiveThreshold(
        grey,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=block_size,
        C=offset,
    )
    marks = cv2.bitwise_not(light)
    contours, _ = cv2.findContours(outlines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(marks, contours, -1, (255, 255, 255), 1)
    return np.asarray(cv2.bitwise_not(marks), dtype=np.uint8)


def point_cloud_figure(
    clouds: Mapping[str, npt.ArrayLike],
    *,
    radius: float,
    z_range: tuple[float, float],
    title: str = "",
) -> go.Figure:
    """A 3D figure of each cloud of (x, y, z) points, as dots named by its key.

    The clouds take the colours of `COLOURS` in order. The view spans one unit past
    `radius` each way in x and y, and `z_range` in z, at equal scales, as the 2024
    library's `render_3d_plot` drew a cylinder's points.
    """
    figure = go.Figure()
    for (name, points), colour in zip(clouds.items(), cycle(COLOURS), strict=False):
        array = np.asarray(points, dtype=np.float64)
        if array.ndim != 2 or array.shape[1] != 3:
            raise ValueError(f"cloud {name!r} must be rows of (x, y, z), not shape {array.shape}")
        figure.add_trace(
            go.Scatter3d(
                x=array[:, 0],
                y=array[:, 1],
                z=array[:, 2],
                mode="markers",
                marker={"size": 3, "color": colour},
                name=name,
            )
        )
    span = [-radius - 1, radius + 1]
    figure.update_layout(
        scene={
            "xaxis": {"range": span},
            "yaxis": {"range": span},
            "zaxis": {"range": list(z_range)},
            "aspectmode": "manual",
            "aspectratio": {"x": 1, "y": 1, "z": 1},
        },
        title=title,
    )
    return figure
