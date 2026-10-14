"""The README's figures, drawn from the designs as the package builds them.

    make figures                              # uv run --group docs python -m tools.figures

Builds Shire and UMSS with `vedya` and writes every image the README shows into
`docs/images/`:

- `shire.png`: Shire's aggregate, written as STL and rendered in 3D, its heights doubled.
- `shire-and-the-milled-piece.jpg`: Shire's top, shaded, beside the photograph of the
  piece milled in April 2024, `public/final-piece.jpeg`.
- `shire-parts.png`: Shire's eight parts from above, each in its colour, with its top's
  height. Where two parts' tops are level, the part built later is drawn.
- `shire-against-the-toolpaths.png`: Shire's top, the surface the April 2024 toolpaths
  cut, and the difference. For each part, the script prints how many milled cells it
  holds, and the shares of them where the cut lies within 0.2 mm of the part's top, and
  more than 0.2 mm below it.
- `shire-slices.png`: the twelve 3.2 mm slices `vedya build shire --slice 3.2:12`
  writes, each from above.
- `umss.png`: UMSS's tile and its magnet base, moved down, in 3D.
- `flow-field.png`: `vedya.flowfield.flow_field` with its defaults.

The surfaces are read on a grid of 0.25 mm cells. A cell's height is the highest top
of Shire's plan (`tools.toolpaths.plan`) over the cell's centre, and the cell belongs to
the part whose face that is; where the faces of two parts lie at that top, to the part
built later. The surface the toolpaths cut is, at each cell, the lowest tip of either
tool whose centre passes within its radius less 0.3 mm of the cell, each tool position
taken at the centre of the cell it lies in and the reach rounded to whole cells. The 0.3
mm, a little more than a cell, keeps a cell the tool's circle only grazes, at the foot
of a wall, from reading as cut.

A second run writes the same files. matplotlib draws the same pixels each time, and is
kept from writing its version into the PNGs. The 3D views are VTK's offscreen OpenGL
renders. VTK's supersampling pass gives slightly different pixels from run to run, so
they are rendered with its default multisampling alone, at twice the size, and averaged
down (`SUPERSAMPLE`), which gives the same pixels each time on one machine. Another
machine's graphics driver may shade some of them differently.

Every length is in millimetres.
"""

import math
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import build123d as bd
import numpy as np
import numpy.typing as npt

# pyvista, matplotlib and Pillow are in the `docs` dependency group, which CI's type check
# does not install; there these imports are unresolved, and what they bring is untyped.
import pyvista as pv  # pyright: ignore[reportMissingImports]
import shapely
from matplotlib import colormaps  # pyright: ignore[reportMissingImports]
from matplotlib.colors import (  # pyright: ignore[reportMissingImports]
    LightSource,
    LinearSegmentedColormap,
    ListedColormap,
    to_rgb,
)
from matplotlib.figure import Figure  # pyright: ignore[reportMissingImports]
from matplotlib.lines import Line2D  # pyright: ignore[reportMissingImports]
from PIL import Image, ImageDraw  # pyright: ignore[reportMissingImports]
from shapely.geometry.base import BaseGeometry

from tools.toolpaths import CHORD, CNC_CUTS, STEP, TOOL_RADII, TOP, plan, read_toolpath
from vedya.designs import shire, umss
from vedya.export import export
from vedya.flowfield import EXTENT, flow_field
from vedya.model import Model, aggregate, slice_layers

__all__ = ["IMAGES", "main"]

REPOSITORY = Path(__file__).parent.parent

IMAGES = REPOSITORY / "docs" / "images"
"""Where the figures are written."""

PHOTOGRAPH = REPOSITORY / "public" / "final-piece.jpeg"
"""The piece milled in April 2024."""

type Raster = npt.NDArray[np.float32]
type Mask = npt.NDArray[np.bool_]
type Owners = npt.NDArray[np.int16]

PAPER = "#f7f4ef"
"""The figures' background."""

WOOD = "#d9b382"
"""The colour of the 3D renders, near the Huon pine's."""

WOOD_RAMP = ["#3b2414", "#7a4b27", "#b07a45", "#d9ac74", "#f2d7a8"]
"""The shaded reliefs' colours, from the board's bottom to its top."""

PART_COLOURS = {
    "bg": "#d8d2c4",
    "border": "#6b4f3a",
    "layer-0": "#4c8c7a",
    "layer-2": "#7aa6c2",
    "layer-1": "#c48a5a",
    "core": "#a65d57",
    "torus": "#e0b44c",
    "middle-ring": "#5a5a8c",
}
"""Each of Shire's parts' colour in `shire-parts.png`."""

RELIEF = 6.0
"""How much the shading exaggerates the reliefs' slopes."""

HEIGHTS = 2.0
"""How much the 3D view of Shire stretches its heights."""

WITHIN = 0.2
"""How near the model's top a milled cell is counted as cut to it."""

SHORT = 0.3
"""How much less than the tool's radius a tool centre must pass from a cell's centre to
count as cutting the cell."""

SLICE = (3.2, 12)
"""The slices' height and their most cuts, as `--slice 3.2:12` gives them."""

EXPLODE = 14.0
"""How far `umss.png` moves the magnet base down from where it is built."""


@dataclass(frozen=True)
class Grid:
    """Square cells over a rectangle of the XY plane, in rows from the north.

    Attributes:
        cell: The cells' side.
        west: The rectangle's least x.
        north: The rectangle's greatest y.
        rows: The cells down the rectangle.
        columns: The cells across it.
    """

    cell: float
    west: float
    north: float
    rows: int
    columns: int

    @property
    def extent(self) -> tuple[float, float, float, float]:
        """The rectangle as matplotlib's `imshow` takes it: west, east, south, north."""
        return (
            self.west,
            self.west + self.columns * self.cell,
            self.north - self.rows * self.cell,
            self.north,
        )

    def cells(self, x: npt.NDArray[np.float64], y: npt.NDArray[np.float64]) -> npt.NDArray[np.intp]:
        """The flat index of the cell each point lies in; -1 for a point off the grid."""
        row = np.floor((self.north - y) / self.cell).astype(np.intp)
        column = np.floor((x - self.west) / self.cell).astype(np.intp)
        on = (row >= 0) & (row < self.rows) & (column >= 0) & (column < self.columns)
        return np.where(on, row * self.columns + column, -1)

    def fill(self, region: BaseGeometry) -> Mask:
        """The cells whose centres lie in `region`.

        Pillow fills each polygon, and puts its outline up to a cell from where it lies.
        So every cell within two cells of the filled outline is then tested exactly.
        """
        mask = np.zeros((self.rows, self.columns), dtype=np.bool_)
        for polygon in shapely.get_parts(region):
            if not isinstance(polygon, shapely.Polygon) or polygon.is_empty:
                continue
            outer = self._pixels(polygon.exterior.coords)
            # A margin of three cells holds every cell Pillow may fill, and its neighbours.
            low = np.floor(outer.min(axis=0)).astype(np.intp) - 3
            high = np.ceil(outer.max(axis=0)).astype(np.intp) + 4
            left, top = max(0, int(low[0])), max(0, int(low[1]))
            right, bottom = min(self.columns, int(high[0])), min(self.rows, int(high[1]))
            if left >= right or top >= bottom:
                continue
            # Each polygon is drawn on its own, so that a hole in it clears no other.
            image = Image.new("L", (right - left, bottom - top), 0)
            draw = ImageDraw.Draw(image)
            corner = np.array([left, top])
            draw.polygon((outer - corner).ravel().tolist(), fill=1)
            for ring in polygon.interiors:
                draw.polygon((self._pixels(ring.coords) - corner).ravel().tolist(), fill=0)
            filled = np.asarray(image) > 0
            rows, columns = np.nonzero(_widened(_outline(filled), 2))
            filled[rows, columns] = shapely.contains_xy(
                polygon,
                self.west + (left + columns + 0.5) * self.cell,
                self.north - (top + rows + 0.5) * self.cell,
            )
            mask[top:bottom, left:right] |= filled
        return mask

    def _pixels(self, coords: Any) -> npt.NDArray[np.float64]:
        """Points in XY as image coordinates, in which a cell's centre is a whole number."""
        xy = np.asarray(coords, dtype=np.float64)[:, :2]
        return np.column_stack(
            [(xy[:, 0] - self.west) / self.cell - 0.5, (self.north - xy[:, 1]) / self.cell - 0.5]
        )


def _outline(mask: Mask) -> Mask:
    """The cells of `mask` beside a cell that differs from them, along a row or a column."""
    found = np.zeros_like(mask)
    across = mask[:, 1:] != mask[:, :-1]
    found[:, 1:] |= across
    found[:, :-1] |= across
    down = mask[1:, :] != mask[:-1, :]
    found[1:, :] |= down
    found[:-1, :] |= down
    return found


def _widened(mask: Mask, by: int) -> Mask:
    """`mask` and every cell within `by` cells of it, along rows, columns and diagonals."""
    found = mask.copy()
    for _ in range(by):
        grown = found.copy()
        grown[1:, :] |= found[:-1, :]
        grown[:-1, :] |= found[1:, :]
        found = grown.copy()
        found[:, 1:] |= grown[:, :-1]
        found[:, :-1] |= grown[:, 1:]
    return found


SHIRE_GRID = Grid(cell=0.25, west=-380.0, north=500.0, rows=4000, columns=3040)
"""Shire's board, 640 by 960 mm, and the 40 mm by which layer-0 overhangs its long
sides, with a margin."""

SLICE_GRID = Grid(cell=1.0, west=-380.0, north=500.0, rows=1000, columns=760)
"""The same rectangle, in cells of 1 mm."""


@dataclass(frozen=True)
class Surface:
    """Shire's top, cell by cell.

    Attributes:
        height: The height of the highest top over the cell's centre; 0 where nothing is.
        owner: The index in `names` of the part that top belongs to; -1 where nothing is.
        names: The parts, in the order the design builds them.
        tops: Each part's highest point.
    """

    height: Raster
    owner: Owners
    names: tuple[str, ...]
    tops: tuple[float, ...]


def surface(model: Model, grid: Grid) -> Surface:
    """`model`'s top on `grid`. Of the parts whose faces lie at the same top over a cell,
    the cell belongs to the one built last."""
    names = tuple(model.parts)
    seen = plan([model.parts[name] for name in names], names, CHORD)
    height = np.zeros((grid.rows, grid.columns), dtype=np.float32)
    owner = np.full((grid.rows, grid.columns), -1, dtype=np.int16)
    # The tops rise, so each face drawn lies on or above every face drawn before it.
    for top, faces in zip(seen.tops, seen.faces, strict=True):
        for index, name in enumerate(names):
            if name in faces:
                inside = grid.fill(faces[name])
                height[inside] = top
                owner[inside] = index
    tops = tuple(float(model.parts[name].bounding_box().max.Z) for name in names)
    return Surface(height, owner, names, tops)


def milled(grid: Grid) -> Raster:
    """The surface the April 2024 toolpaths cut, on `grid`: at each cell, the lowest tip of
    either tool whose centre passes within its radius less `SHORT` of the cell, taken to
    whole cells; infinite where none does."""
    lowest = np.full((grid.rows, grid.columns), np.inf, dtype=np.float32)
    for name, radius in TOOL_RADII.items():
        path = read_toolpath((CNC_CUTS / name).read_text(encoding="ascii"), STEP)
        cutting = path.positions[path.positions[:, 2] < 0]
        # The design's x is the toolpath's Y, and its y the toolpath's X; the toolpath's z
        # is measured down from the design's top.
        cells = grid.cells(cutting[:, 1], cutting[:, 0])
        tips = np.full(grid.rows * grid.columns, np.inf, dtype=np.float32)
        on = cells >= 0
        np.minimum.at(tips, cells[on], (cutting[on, 2] + TOP).astype(np.float32))
        reach = round((radius - SHORT) / grid.cell)
        lowest = np.minimum(lowest, lowest_within(tips.reshape(grid.rows, grid.columns), reach))
        print(f"  {name}: {len(cutting):,} tool positions below the top")
    return lowest


def lowest_within(values: Raster, reach: int) -> Raster:
    """For each cell, the least of `values` over the cells whose centres lie within `reach`
    cells of its centre."""
    rows, columns = values.shape
    padded = np.pad(values, reach, constant_values=np.inf)
    # The least within each width along a row, widened a cell at a time; each row of the
    # disc takes the width that reaches as far as the disc does there.
    across = padded[:, reach : reach + columns].copy()
    lowest = np.full_like(values, np.inf)
    for width in range(reach + 1):
        if width:
            np.minimum(across, padded[:, reach - width : reach - width + columns], out=across)
            np.minimum(across, padded[:, reach + width : reach + width + columns], out=across)
        for down in range(-reach, reach + 1):
            if math.isqrt(reach * reach - down * down) == width:
                np.minimum(lowest, across[reach + down : reach + down + rows], out=lowest)
    return lowest


@dataclass(frozen=True)
class Share:
    """How the cut surface lies against one part's top, over the milled cells it holds.

    Attributes:
        cells: The milled cells the part holds.
        within: How many of them the cut lies within `WITHIN` of the part's top at.
        below: How many it lies more than `WITHIN` below the part's top at.
    """

    cells: int
    within: int
    below: int


def shares(top: Surface, cut: Raster) -> dict[str, Share]:
    """For each part, how the cut surface lies against its top, over the cells it holds
    that the toolpaths cut."""
    reached = np.isfinite(cut) & (top.owner >= 0)
    difference = cut - top.height
    found: dict[str, Share] = {}
    for index, name in enumerate(top.names):
        held = difference[reached & (top.owner == index)]
        within = int(np.count_nonzero(np.abs(held) <= WITHIN))
        found[name] = Share(held.size, within, int(np.count_nonzero(held < -WITHIN)))
    return found


# Drawing.


def _relief(height: Raster) -> npt.NDArray[np.float64]:
    """`height` shaded as wood lit from the north-west, paper where it is 0."""
    ramp = LinearSegmentedColormap.from_list("wood", WOOD_RAMP)
    light = LightSource(azdeg=315, altdeg=35)
    cell = SHIRE_GRID.cell
    shaded = light.shade(
        height,
        cmap=ramp,
        vert_exag=RELIEF,
        dx=cell,
        dy=cell,
        blend_mode="soft",
        vmin=0.0,
        vmax=TOP,
    )
    rgb = np.asarray(shaded, dtype=np.float64)[..., :3]
    rgb[height <= 0] = to_rgb(PAPER)
    return rgb


def _figure(width: float, height: float) -> Any:
    """A figure `width` by `height` inches, on paper, laid out as its parts are added."""
    return Figure(figsize=(width, height), facecolor=PAPER, layout="constrained")


def _axes_in_mm(axes: Any) -> None:
    axes.set_xlabel("x (mm)")
    axes.set_ylabel("y (mm)")
    axes.set_facecolor(PAPER)


def _save_png(figure: Any, name: str, dpi: int) -> Path:
    path = IMAGES / name
    # Without the Software entry, the file depends on nothing but what is drawn.
    figure.savefig(path, dpi=dpi, facecolor=PAPER, metadata={"Software": None})
    return path


def draw_relief_and_photograph(top: Surface) -> Path:
    figure = _figure(12.0, 8.4)
    left, right = figure.subplots(1, 2, width_ratios=[0.76, 0.5625])
    left.imshow(_relief(top.height), extent=SHIRE_GRID.extent, interpolation="antialiased")
    left.set_title("Shire as vedya builds it, from above")
    _axes_in_mm(left)
    with Image.open(PHOTOGRAPH) as photograph:
        right.imshow(np.asarray(photograph.convert("RGB")))
    right.set_title("The piece milled in Huon pine, April 2024")
    right.axis("off")
    path = IMAGES / "shire-and-the-milled-piece.jpg"
    figure.savefig(path, dpi=100, facecolor=PAPER, pil_kwargs={"quality": 85, "optimize": True})
    return path


def draw_parts(top: Surface) -> Path:
    figure = _figure(8.0, 11.0)
    axes = figure.subplots()
    light = LightSource(azdeg=315, altdeg=35)
    cell = SHIRE_GRID.cell
    shade = np.asarray(
        light.hillshade(top.height, vert_exag=RELIEF, dx=cell, dy=cell), dtype=np.float64
    )
    image = np.empty((*top.height.shape, 3))
    image[:] = to_rgb(PAPER)
    for index, name in enumerate(top.names):
        held = top.owner == index
        colour = np.array(to_rgb(PART_COLOURS[name]))
        image[held] = colour * (0.55 + 0.45 * shade[held, np.newaxis])
    axes.imshow(image, extent=SHIRE_GRID.extent, interpolation="antialiased")
    _axes_in_mm(axes)
    handles = [
        Line2D(
            [],
            [],
            marker="s",
            linestyle="",
            markersize=12,
            color=PART_COLOURS[name],
            label=f"{name}, top {height:.1f} mm",
        )
        for name, height in zip(top.names, top.tops, strict=True)
    ]
    figure.legend(handles=handles, loc="outside lower center", ncols=2, frameon=False)
    axes.set_title("Shire's eight parts, from above")
    return _save_png(figure, "shire-parts.png", dpi=100)


def draw_against_the_toolpaths(top: Surface, cut: Raster) -> Path:
    figure = _figure(18.0, 8.0)
    model, milled_axes, difference_axes = figure.subplots(1, 3)
    model.imshow(_relief(top.height), extent=SHIRE_GRID.extent, interpolation="antialiased")
    model.set_title("The model's top")
    reached = np.isfinite(cut)
    milled_axes.imshow(
        _relief(np.where(reached, cut, 0.0).astype(np.float32)),
        extent=SHIRE_GRID.extent,
        interpolation="antialiased",
    )
    milled_axes.set_title("The surface the April 2024 toolpaths cut\n(paper where they never cut)")
    difference = np.where(reached & (top.owner >= 0), cut - top.height, np.nan)
    diverging = colormaps["RdBu_r"].copy()
    diverging.set_bad(PAPER)
    shown = difference_axes.imshow(
        difference,
        extent=SHIRE_GRID.extent,
        cmap=diverging,
        vmin=-10.0,
        vmax=10.0,
        interpolation="antialiased",
    )
    difference_axes.set_title(
        "The cut surface less the model's top (mm)\nblue: cut below it; red: left above it"
    )
    figure.colorbar(shown, ax=difference_axes, shrink=0.8)
    for axes in (model, milled_axes, difference_axes):
        _axes_in_mm(axes)
    return _save_png(figure, "shire-against-the-toolpaths.png", dpi=100)


def draw_slices(layers: Sequence[bd.Part]) -> Path:
    height, count = SLICE
    figure = _figure(18.0, 9.0)
    grid = figure.subplots(2, (len(layers) + 1) // 2)
    colours = ListedColormap([PAPER, "#8a5a33"])
    for index, (axes, layer) in enumerate(zip(grid.flat, layers, strict=True)):
        footprint = plan([layer], ["slice"], 0.05).above[0]
        axes.imshow(
            SLICE_GRID.fill(footprint),
            extent=SLICE_GRID.extent,
            cmap=colours,
            vmin=0,
            vmax=1,
            interpolation="antialiased",
        )
        low, high = height * index, height * (index + 1)
        axes.set_title(f"shire-slice-{index:02d}\n{low:.1f} to {high:.1f} mm", fontsize=11)
        axes.set_xticks([])
        axes.set_yticks([])
    figure.suptitle(
        f"vedya build shire --slice {height}:{count}: each slice from above", fontsize=13
    )
    return _save_png(figure, "shire-slices.png", dpi=100)


def draw_flow_field() -> Path:
    field = flow_field()
    rows, columns, _ = field.shape
    every = 5
    x = np.linspace(0.0, EXTENT, columns)[::every]
    y = np.linspace(0.0, EXTENT, rows)[::every]
    u, v = field[::every, ::every, 0], field[::every, ::every, 1]
    figure = _figure(8.0, 8.0)
    axes = figure.subplots()
    axes.quiver(
        x,
        y,
        u,
        v,
        np.arctan2(v, u),
        cmap="twilight",
        pivot="middle",
        angles="xy",
        scale_units="xy",
        scale=1 / (0.8 * EXTENT / (len(x) - 1)),
        width=0.004,
    )
    axes.set_aspect("equal")
    axes.set_facecolor(PAPER)
    axes.set_title(f"flow_field() with its defaults: {columns} by {rows} unit vectors, every fifth")
    return _save_png(figure, "flow-field.png", dpi=110)


SUPERSAMPLE = 2
"""How many times larger, across and down, a 3D view is rendered than it is written.
Pillow averages each square of pixels into one, which smooths the edges as VTK's
supersampling pass would, but gives the same pixels from one run to the next."""


def _render(
    meshes: Sequence[tuple[Any, str]],
    camera: Sequence[tuple[float, float, float]],
    size: tuple[int, int],
    name: str,
) -> Path:
    """Render `meshes`, each with its colour, from `camera`: its position, the point it
    looks at, and which way is up. The image is `size` pixels across and down."""
    width, height = size
    plotter = pv.Plotter(off_screen=True, window_size=[width * SUPERSAMPLE, height * SUPERSAMPLE])
    plotter.renderer.set_background(PAPER)
    for mesh, colour in meshes:
        plotter.add_mesh(
            mesh, color=colour, smooth_shading=False, specular=0.15, ambient=0.25, diffuse=0.8
        )
    plotter.enable_lightkit()
    plotter.camera_position = [tuple(each) for each in camera]
    pixels = plotter.screenshot(None, return_img=True)
    plotter.close()
    path = IMAGES / name
    image = Image.fromarray(np.asarray(pixels, dtype=np.uint8))
    image.resize(size, Image.Resampling.BOX).save(path, optimize=True)
    return path


def draw_shire(whole: bd.Part, folder: Path) -> Path:
    stl = folder / "shire.stl"
    export(whole, stl)
    mesh = pv.read(stl).scale([1.0, 1.0, HEIGHTS], inplace=False)
    camera = [(-620.0, -1300.0, 900.0), (20.0, -60.0, 0.0), (0.0, 0.0, 1.0)]
    return _render([(mesh, WOOD)], camera, (1600, 1100), "shire.png")


def draw_umss(model: Model, folder: Path) -> Path:
    meshes: list[tuple[Any, str]] = []
    for name, colour in (("tile", WOOD), ("magnet-base", "#5a7fa6")):
        stl = folder / f"umss-{name}.stl"
        export(model.parts[name], stl)
        mesh = pv.read(stl)
        if name == "magnet-base":
            mesh = mesh.translate((0.0, 0.0, -EXPLODE), inplace=False)
        meshes.append((mesh, colour))
    camera = [(-40.0, -54.0, 20.5), (0.0, 0.0, -5.5), (0.0, 0.0, 1.0)]
    return _render(meshes, camera, (1200, 800), "umss.png")


def _share(count: int, of: int) -> str:
    return f"{count:,} ({count / of:.1%})" if of else "none"


def main() -> None:
    IMAGES.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    print("building Shire and UMSS")
    model = shire.build(shire.ShireParams())
    tile = umss.build(umss.UmssParams(parts=("tile", "magnet-base")))
    print("reading Shire's top")
    top = surface(model, SHIRE_GRID)
    print("reading the toolpaths")
    cut = milled(SHIRE_GRID)
    print("the milled cells each part holds, and where the cut lies against the part's top:")
    within, below = f"within {WITHIN} mm", f"over {WITHIN} mm below"
    print(f"  {'part':12} {'cells':>9}  {within:>18}  {below:>18}")
    for name, share in shares(top, cut).items():
        print(
            f"  {name:12} {share.cells:>9,}  {_share(share.within, share.cells):>18}  "
            f"{_share(share.below, share.cells):>18}"
        )
    written.append(draw_relief_and_photograph(top))
    written.append(draw_parts(top))
    written.append(draw_against_the_toolpaths(top, cut))
    print("joining and slicing Shire")
    whole = aggregate(model)
    written.append(draw_slices(slice_layers(whole, *SLICE)))
    print("rendering")
    with tempfile.TemporaryDirectory() as folder:
        written.append(draw_shire(whole, Path(folder)))
        written.append(draw_umss(tile, Path(folder)))
    written.append(draw_flow_field())
    for path in written:
        print(f"wrote {path.relative_to(REPOSITORY)}, {path.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
