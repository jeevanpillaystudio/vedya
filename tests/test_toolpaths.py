"""Shire is never above where the toolpaths it was milled from put the tool.

The piece was milled in April 2024 with two toolpaths, `public/cnc-cuts/6mm-adaptive.tap`
and `3mm-adaptive.tap`, adaptive clearing with flat end mills of 6 and 3 mm, which CAM
wrote from that month's model. Wherever the tool went, the model was not: under the
tool's flat end, a disc of its radius at its tip, no point of the model stands higher
than the tip.

- The toolpaths' z = 0 is the design's top, 38.4 mm up. Their X runs along the board's
  length, which is the design's y, and their Y across it, the design's x.
- The model is read as a height map: over the centre of each cell of a 0.5 mm grid, its
  highest point, from its horizontal faces meshed to 0.01 mm. The model is the union of
  its parts, so its height map is the highest of theirs.
- The border is left out. The toolpaths cut where a wall inside the board's edge would
  stand, so the milled piece had none; ADR 0003 records the open question.
- A tip may sit 0.15 mm into the model: the stock CAM left on floors, and the mesh.
- The tool is checked wherever it goes: at each programmed point, and along each line
  and arc between them every quarter millimetre.

Every length is in millimetres.
"""

import copy
import math
import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import build123d as bd
import numpy as np
import numpy.typing as npt
import pytest

# OCP is compiled and ships no type stubs, so its names are invisible to the type checker.
from OCP.BRep import BRep_Tool  # pyright: ignore[reportAttributeAccessIssue]
from OCP.BRepMesh import BRepMesh_IncrementalMesh  # pyright: ignore[reportAttributeAccessIssue]
from OCP.TopLoc import TopLoc_Location  # pyright: ignore[reportAttributeAccessIssue]

from vedya.export import ANGULAR_TOLERANCE, LINEAR_TOLERANCE
from vedya.geometry import circle, rectangle, slab
from vedya.model import Model

type Floats = npt.NDArray[np.float64]
type Centres = npt.NDArray[np.floating[Any]]
type Indices = npt.NDArray[np.intp]

CNC_CUTS = Path(__file__).parent.parent / "public" / "cnc-cuts"
"""The toolpaths the piece was milled with."""

TOOL_RADII = {"6mm-adaptive.tap": 3.0, "3mm-adaptive.tap": 1.5}
"""Each toolpath's tool radius, as its header gives the diameter."""

TOP = 38.4
"""The design's top, where the toolpaths' z is 0."""

ALLOWANCE = 0.15
"""How far a tip may sit into the model: stock left on floors, and the mesh."""

CELL = 0.5
"""The height map's cell."""

STEP = 0.25
"""The longest stretch of a move between two positions checked."""

LEFT_OUT = ("border",)
"""The parts the milled piece did not have."""


# Reading G-code.

_WORD = re.compile(r"([A-Z])\s*([-+]?(?:\d+\.?\d*|\.\d+))")
_COMMENT = re.compile(r"\([^)]*\)")
_TOOL = re.compile(r"\bD=(\d+\.?\d*)\s+CR=(\d+\.?\d*)\b.*FLAT END MILL")

_PLANES = {17: (0, 1, 2), 18: (2, 0, 1), 19: (1, 2, 0)}
"""For G17, G18 and G19, an arc's first and second axes and the axis normal to them, as
indices of x, y and z. Each triple is right-handed: an arc turns counter-clockwise from
its first axis towards its second (G3), or clockwise (G2), seen from the normal's tip."""

_MOTIONS = (0, 1, 2, 3)


@dataclass(frozen=True)
class Toolpath:
    """A toolpath read from G-code.

    Attributes:
        diameter: The flat end mill's diameter, from the header.
        moves: The moves the program makes.
        positions: Where the tool's tip goes, in the toolpath's own x, y and z: the end of
            every move, and points along it no more than a step apart.
    """

    diameter: float
    moves: int
    positions: Floats


def read_toolpath(text: str, step: float) -> Toolpath:
    """The toolpath that the G-code `text` programs, sampled every `step` along its moves.

    The code is Fusion 360's: absolute coordinates (G90) with arc centres relative to the
    arc's start (G91.1), arcs in any of the three planes and helical along the third, and
    G28 returns to the machine's home, after which the axes it names are unknown until
    set again. Raises `ValueError` for a word the reader does not follow.
    """
    found = _TOOL.search(text)
    if found is None:
        raise ValueError("the program names no flat end mill and its diameter")
    if float(found.group(2)) != 0:
        raise ValueError("the reader takes flat end mills only")
    position = [math.nan] * 3
    motion, plane, centre_relative = 0, 17, True
    moves = 0
    pieces: list[Floats] = []
    for raw in text.splitlines():
        words = [(letter, float(value)) for letter, value in _WORD.findall(_COMMENT.sub("", raw))]
        codes = [value for letter, value in words if letter == "G"]
        axes = {letter: value for letter, value in words if letter in "XYZ"}
        if 28 in codes:
            for letter in axes:
                position["XYZ".index(letter)] = math.nan
            continue
        for code in codes:
            if code in _MOTIONS:
                motion = int(code)
            elif code in _PLANES:
                plane = int(code)
            elif code == 91:
                raise ValueError(f"incremental moves are not read: {raw!r}")
            elif code in (90.1, 91.1):
                centre_relative = code == 91.1
        if not axes:
            continue
        start = np.array(position)
        end = start.copy()
        for letter, value in axes.items():
            end["XYZ".index(letter)] = value
        moves += 1
        position = [float(v) for v in end]
        if np.isnan(end).any():
            continue
        if np.isnan(start).any():
            pieces.append(end[np.newaxis, :])
        elif motion in (2, 3):
            offsets = [dict(words).get(letter, 0.0) for letter in "IJK"]
            pieces.append(_arc(start, end, offsets, centre_relative, plane, motion == 3, step))
        else:
            count = max(1, math.ceil(float(np.linalg.norm(end - start)) / step))
            fractions = np.arange(1, count + 1)[:, np.newaxis] / count
            pieces.append(start + (end - start) * fractions)
    if not pieces:
        raise ValueError("the program never puts the tool anywhere")
    return Toolpath(float(found.group(1)), moves, np.concatenate(pieces))


def _arc(
    start: Floats,
    end: Floats,
    offsets: Sequence[float],
    relative: bool,
    plane: int,
    counter_clockwise: bool,
    step: float,
) -> Floats:
    """Points every `step` or less along an arc from `start` to `end`, helical along the
    plane's normal, ending at `end`."""
    first, second, normal = _PLANES[plane]
    centre = start.copy() if relative else np.zeros(3)
    centre[first] += offsets[first]
    centre[second] += offsets[second]
    radius = math.hypot(start[first] - centre[first], start[second] - centre[second])
    end_radius = math.hypot(end[first] - centre[first], end[second] - centre[second])
    if abs(radius - end_radius) > 0.01:
        raise ValueError(f"an arc starts {radius} from its centre and ends {end_radius}")
    begin = math.atan2(start[second] - centre[second], start[first] - centre[first])
    finish = math.atan2(end[second] - centre[second], end[first] - centre[first])
    sweep = (
        (finish - begin) % (2 * math.pi)
        if counter_clockwise
        else -((begin - finish) % (2 * math.pi))
    )
    if sweep == 0:
        sweep = 2 * math.pi if counter_clockwise else -2 * math.pi  # a whole circle
    # A helix is no longer than its turn about the axis and its rise along it together.
    length = math.hypot(abs(sweep) * max(radius, end_radius), end[normal] - start[normal])
    count = max(1, math.ceil(length / step))
    fractions = np.arange(1, count + 1) / count
    angles = begin + sweep * fractions
    radii = radius + (end_radius - radius) * fractions
    points = np.empty((count, 3))
    points[:, first] = centre[first] + radii * np.cos(angles)
    points[:, second] = centre[second] + radii * np.sin(angles)
    points[:, normal] = start[normal] + (end[normal] - start[normal]) * fractions
    points[-1] = end
    return points


# The model's height map.


@dataclass(frozen=True)
class HeightMap:
    """The highest point of some solids over each cell of a grid in the XY plane.

    Attributes:
        low: The grid's low corner. Cell (row, column) is centred at
            low + (column + ½, row + ½) · cell.
        cell: The side of a cell.
        heights: The highest point over each cell's centre, by row and column; -inf where
            there is none.
        owners: The index in `names` of the solid that highest point is on; -1 for none.
        names: The solids' names.
    """

    low: tuple[float, float]
    cell: float
    heights: Floats
    owners: Indices
    names: tuple[str, ...]

    def centres(self, rows: Indices, columns: Indices) -> tuple[Centres, Centres]:
        """The x and y of the centres of the cells at `rows` and `columns`."""
        x0, y0 = self.low
        return x0 + (columns + 0.5) * self.cell, y0 + (rows + 0.5) * self.cell


def height_map(solids: Sequence[bd.Part], names: Sequence[str], cell: float) -> HeightMap:
    """The height map of `solids`, named `names`, on a grid of `cell`.

    Every face of a solid must be horizontal or vertical, as a slab's are: the height of
    a solid over a point is that of its highest horizontal face there.
    """
    flats = [_horizontal_triangles(solid) for solid in solids]
    corners = np.concatenate([triangles.reshape(-1, 3) for triangles in flats])
    x0 = math.floor(corners[:, 0].min() / cell) * cell
    y0 = math.floor(corners[:, 1].min() / cell) * cell
    columns = math.ceil((corners[:, 0].max() - x0) / cell)
    rows = math.ceil((corners[:, 1].max() - y0) / cell)
    heights = np.full((rows, columns), -np.inf)
    owners = np.full((rows, columns), -1, dtype=np.intp)
    for index, triangles in enumerate(flats):
        levels = np.round(triangles[:, 0, 2], 6)
        for level in np.unique(levels):
            these = triangles[levels == level]
            z = float(these[:, :, 2].max())
            covered = _covered(these[:, :, :2], (x0, y0), cell, (rows, columns))
            higher = covered & (heights < z)
            heights[higher] = z
            owners[higher] = index
    return HeightMap((x0, y0), cell, heights, owners, tuple(names))


def _horizontal_triangles(solid: bd.Part) -> Floats:
    """The triangles of `solid`'s horizontal faces, meshed to `LINEAR_TOLERANCE`, as
    (triangle, corner, xyz)."""
    # Mesh a copy, so the model's own shapes carry no mesh. build123d's own `tessellate`
    # takes its tolerance relative to each edge's length, too coarse for large circles.
    copied = copy.deepcopy(solid)
    BRepMesh_IncrementalMesh(copied.wrapped, LINEAR_TOLERANCE, False, ANGULAR_TOLERANCE, True)
    found: list[Floats] = []
    for face in copied.faces():
        upward = face.normal_at().Z
        if face.geom_type == bd.GeomType.PLANE and abs(abs(upward) - 1) < 1e-9:
            location = TopLoc_Location()
            mesh = BRep_Tool.Triangulation_s(face.wrapped, location)
            moved = location.Transformation()
            corners = np.array(
                [
                    (point.X(), point.Y(), point.Z())
                    for point in (
                        mesh.Node(i).Transformed(moved) for i in range(1, mesh.NbNodes() + 1)
                    )
                ]
            )
            order = np.array([mesh.Triangle(i).Get() for i in range(1, mesh.NbTriangles() + 1)])
            found.append(corners[order - 1])
        elif abs(upward) > 1e-9:
            raise ValueError(f"a {face.geom_type.name} face neither horizontal nor vertical")
    return np.concatenate(found)


def _covered(
    triangles: Floats, low: tuple[float, float], cell: float, shape: tuple[int, int]
) -> npt.NDArray[np.bool_]:
    """Which cells of the grid have their centres in any of `triangles`, given in XY.

    Each triangle is cut along each row of centres it spans; the span it covers on that
    row is counted into a running sum along the row.
    """
    x0, y0 = low
    rows, columns = shape
    ys = triangles[:, :, 1]
    first = np.ceil((ys.min(axis=1) - y0) / cell - 0.5 - 1e-9).astype(np.intp)
    last = np.floor((ys.max(axis=1) - y0) / cell - 0.5 + 1e-9).astype(np.intp)
    spans = np.maximum(last - first + 1, 0)
    which = np.repeat(np.arange(len(triangles)), spans)
    row = np.repeat(first, spans) + (
        np.arange(spans.sum()) - np.repeat(np.cumsum(spans) - spans, spans)
    )
    y = y0 + (row + 0.5) * cell
    corners = triangles[which]
    low_x = np.full(len(which), np.inf)
    high_x = np.full(len(which), -np.inf)
    for k in range(3):
        a, b = corners[:, k], corners[:, (k + 1) % 3]
        crosses = (y - a[:, 1]) * (y - b[:, 1]) <= 0
        level = a[:, 1] == b[:, 1]
        with np.errstate(divide="ignore", invalid="ignore"):
            x = np.where(
                level, a[:, 0], a[:, 0] + (y - a[:, 1]) * (b[:, 0] - a[:, 0]) / (b[:, 1] - a[:, 1])
            )
        other = np.where(level, b[:, 0], x)
        low_x = np.where(crosses, np.minimum(low_x, np.minimum(x, other)), low_x)
        high_x = np.where(crosses, np.maximum(high_x, np.maximum(x, other)), high_x)
    begin = np.ceil((low_x - x0) / cell - 0.5 - 1e-9)
    end = np.floor((high_x - x0) / cell - 0.5 + 1e-9)
    keep = np.isfinite(begin) & (end >= begin) & (row >= 0) & (row < rows)
    begin = np.clip(begin[keep], 0, columns).astype(np.intp)
    end = np.clip(end[keep], -1, columns - 1).astype(np.intp)
    row = row[keep]
    counts = np.zeros((rows, columns + 1), dtype=np.int32)
    np.add.at(counts, (row, begin), 1)
    np.add.at(counts, (row, end + 1), -1)
    return np.cumsum(counts, axis=1)[:, :columns] > 0


def highest_under(
    heights: HeightMap, points: Floats, radius: float, chunk: int = 10_000
) -> tuple[Floats, Indices, Indices]:
    """For each of `points` in XY, the highest point of the map whose cell's centre lies
    within `radius` of it, and that cell's row and column."""
    x0, y0 = heights.low
    rows, columns = heights.heights.shape
    reach = math.ceil(radius / heights.cell) + 1
    offsets = np.arange(-reach, reach + 1)
    d_row, d_column = (grid.ravel() for grid in np.meshgrid(offsets, offsets, indexing="ij"))
    highest = np.empty(len(points))
    at_row = np.empty(len(points), dtype=np.intp)
    at_column = np.empty(len(points), dtype=np.intp)
    for begin in range(0, len(points), chunk):
        part = points[begin : begin + chunk]
        base_row = np.floor((part[:, 1] - y0) / heights.cell - 0.5).astype(np.intp)
        base_column = np.floor((part[:, 0] - x0) / heights.cell - 0.5).astype(np.intp)
        row = base_row[:, np.newaxis] + d_row
        column = base_column[:, np.newaxis] + d_column
        x, y = heights.centres(row, column)
        under = (x - part[:, :1]) ** 2 + (y - part[:, 1:2]) ** 2 <= radius**2
        under &= (row >= 0) & (row < rows) & (column >= 0) & (column < columns)
        found = np.where(
            under,
            heights.heights[np.clip(row, 0, rows - 1), np.clip(column, 0, columns - 1)],
            -np.inf,
        )
        best = found.argmax(axis=1)
        picked = np.arange(len(part))
        highest[begin : begin + chunk] = found[picked, best]
        at_row[begin : begin + chunk] = row[picked, best]
        at_column[begin : begin + chunk] = column[picked, best]
    return highest, at_row, at_column


# The reader and the height map, on what can be worked out by hand.

PROGRAM = """(T9 D=4. CR=0. - ZMIN=-2. - FLAT END MILL)
G90 G94 G91.1 G40 G49 G17
G21
G28 G91 Z0.
G90
G0 X0. Y0.
G43 Z5. H9
G1 Z-1. F100.
X2.
G3 X4. Y2. I0. J2.
G2 X6. Y4. Z-2. I2. J0.
G18 G3 X5. Z-1. I0. K1.
G0 Z5.
G28 G91 Z0.
G90
G0 X10.
"""


def test_the_reader_reads_the_tool_and_every_move() -> None:
    path = read_toolpath(PROGRAM, STEP)
    assert path.diameter == 4.0
    # G0 X Y, G43 Z, G1 Z, X, G3, G2, G18 G3, G0 Z, and the last G0 X; not the G28s.
    assert path.moves == 9
    first, last = path.positions[0], path.positions[-1]
    # Before the tool's height is set it is nowhere; after the G28 too.
    assert tuple(first) == (0.0, 0.0, 5.0)
    assert tuple(last) == (5.0, 4.0, 5.0)
    gaps = np.linalg.norm(np.diff(path.positions, axis=0), axis=1)
    assert gaps.max() <= STEP + 1e-9


def test_arcs_turn_the_way_their_code_says() -> None:
    p = read_toolpath(PROGRAM, STEP).positions
    # G3 from (2, 0) about (2, 2) to (4, 2), at z -1: a quarter turn counter-clockwise,
    # through the lower right.
    g3 = p[(p[:, 2] == -1.0) & (p[:, 0] > 2.0) & (p[:, 1] < 2.0)]
    assert len(g3) > 2
    assert np.hypot(g3[:, 0] - 2, g3[:, 1] - 2) == pytest.approx(2.0, abs=1e-9)
    # G2 from (4, 2) about (6, 2) to (6, 4), down to z -2: a quarter turn clockwise,
    # through the upper left, its height falling with the angle.
    g2 = p[(p[:, 2] < -1.0) & (p[:, 2] > -2.0) & (p[:, 1] > 2.0) & (p[:, 1] < 4.0)]
    assert len(g2) > 2
    assert np.hypot(g2[:, 0] - 6, g2[:, 1] - 2) == pytest.approx(2.0, abs=1e-9)
    assert (g2[:, 0] <= 6.0).all()
    turned = np.arctan2(g2[:, 1] - 2, g2[:, 0] - 6)
    assert -g2[:, 2] - 1 == pytest.approx(1 - (turned - math.pi / 2) / (math.pi / 2), abs=1e-9)
    # G18 G3 from x 6, z -2 about x 6, z -1 to x 5, z -1: a quarter turn in the XZ plane,
    # leading out backwards and up, as the 6 mm toolpath's one such arc does.
    g18 = p[(p[:, 1] == 4.0) & (p[:, 2] > -2.0) & (p[:, 2] < -1.0)]
    assert len(g18) > 2
    assert np.hypot(g18[:, 0] - 6, g18[:, 2] + 1) == pytest.approx(1.0, abs=1e-9)
    assert (g18[:, 0] < 6.0).all()


def test_the_reader_refuses_what_it_does_not_follow() -> None:
    with pytest.raises(ValueError, match="no flat end mill"):
        read_toolpath("G0 X0. Y0. Z0.", STEP)
    with pytest.raises(ValueError, match="incremental"):
        read_toolpath(PROGRAM.replace("G0 X10.", "G91 G0 X10."), STEP)


def test_the_height_map_holds_the_highest_face_over_each_cell() -> None:
    board = slab(rectangle(20.0, 10.0), 0.0, 2.0)
    post = slab(circle(2.0, at=(5.0, 0.0)), 1.0, 4.0)
    heights = height_map([board, post], ("board", "post"), CELL)
    assert heights.low == (-10.0, -5.0)
    assert heights.heights.shape == (20, 40)
    covered = np.isfinite(heights.heights)
    assert covered.all()
    # The post's top covers cells centred within its circle, about π · 2² / 0.5² of them.
    on_post = heights.heights == 5.0
    x, y = heights.centres(*np.nonzero(on_post))
    assert ((x - 5.0) ** 2 + y**2 <= 4.0).all()
    assert on_post.sum() == pytest.approx(math.pi * 4.0 / CELL**2, rel=0.1)
    assert (heights.owners[on_post] == 1).all()
    assert (heights.heights[~on_post] == 2.0).all()


def test_the_highest_point_under_a_disc_reaches_its_edge_and_no_further() -> None:
    floor = slab(rectangle(10.0, 10.0), 0.0, 3.0)
    wall = slab(bd.Pos(4.0, 0.0) * rectangle(2.0, 10.0), 3.0, 2.0)
    heights = height_map([floor, wall], ("floor", "wall"), CELL)
    # The wall stands from x = 3 to 5; the nearest cell centres are at x = 3.25.
    tool = np.array([[0.25, 0.25], [0.24, 0.25]])
    highest, _, _ = highest_under(heights, tool, 3.0)
    assert list(highest) == [5.0, 3.0]


# The toolpaths against the model.


@pytest.fixture(scope="module")
def milled(shire: Model) -> HeightMap:
    names = [name for name in shire.parts if name not in LEFT_OUT]
    return height_map([shire.parts[name] for name in names], names, CELL)


def inside_edge(
    heights: HeightMap, points: Floats, radius: float, levels: Floats, chunk: int = 10_000
) -> Floats:
    """For each of `points` in XY, how far inside the edge of a disc of `radius` about it
    the map stands higher than the point's level in `levels`; -inf where it does not."""
    x0, y0 = heights.low
    rows, columns = heights.heights.shape
    reach = math.ceil(radius / heights.cell) + 1
    offsets = np.arange(-reach, reach + 1)
    d_row, d_column = (grid.ravel() for grid in np.meshgrid(offsets, offsets, indexing="ij"))
    found = np.empty(len(points))
    for begin in range(0, len(points), chunk):
        part = points[begin : begin + chunk]
        row = np.floor((part[:, 1] - y0) / heights.cell - 0.5).astype(np.intp)[:, np.newaxis]
        column = np.floor((part[:, 0] - x0) / heights.cell - 0.5).astype(np.intp)[:, np.newaxis]
        row, column = row + d_row, column + d_column
        x, y = heights.centres(row, column)
        distance = np.hypot(x - part[:, :1], y - part[:, 1:2])
        valid = (row >= 0) & (row < rows) & (column >= 0) & (column < columns)
        above = heights.heights[np.clip(row, 0, rows - 1), np.clip(column, 0, columns - 1)]
        higher = valid & (distance <= radius) & (above > levels[begin : begin + chunk, np.newaxis])
        found[begin : begin + chunk] = radius - np.where(higher, distance, np.inf).min(axis=1)
    return found


@dataclass(frozen=True)
class Gouge:
    """Where a tool position cuts into the model, in the design's coordinates.

    Attributes:
        x: The tool's centre, along the board's width.
        y: The tool's centre, along the board's length.
        tip: The tool's tip, from the design's top.
        model: The model's highest point under the tool, from the design's top.
        inside: How far inside the tool's edge the model stands above the allowance.
        part: The part that highest point is on.
    """

    x: float
    y: float
    tip: float
    model: float
    inside: float
    part: str

    def __str__(self) -> str:
        return (
            f"  x {self.x:9.3f}  y {self.y:9.3f}  (toolpath X {self.y:9.3f} Y {self.x:9.3f})  "
            f"tip {self.tip:8.3f}  model {self.model:8.3f}  overlap {self.model - self.tip:7.3f}  "
            f"{self.inside:6.3f} inside the edge  on {self.part}"
        )


def describe(
    by_overlap: Sequence[Gouge], by_inside: Sequence[Gouge], count: int, of: int, parts: str
) -> str:
    return "\n".join(
        [
            f"{count} of {of} positions cut more than {ALLOWANCE} mm into the model ({parts}).",
            "In the design's coordinates, with z from its top, the deepest:",
            *map(str, by_overlap),
            "and those furthest inside the tool's edge:",
            *map(str, by_inside),
        ]
    )


@pytest.mark.slow
@pytest.mark.parametrize(("name", "radius"), TOOL_RADII.items())
def test_no_tool_position_cuts_into_the_model(milled: HeightMap, name: str, radius: float) -> None:
    path = read_toolpath((CNC_CUTS / name).read_text(encoding="ascii"), STEP)
    assert path.diameter == 2 * radius
    cutting = path.positions[path.positions[:, 2] < 0]
    # The design's x is the toolpath's Y, and its y the toolpath's X.
    design = cutting[:, [1, 0]]
    highest, rows, columns = highest_under(milled, design, radius)
    overlap = (highest - TOP) - cutting[:, 2]
    bad = np.nonzero(overlap > ALLOWANCE)[0]
    if not len(bad):
        return
    owners = milled.owners[rows[bad], columns[bad]]
    inside = inside_edge(milled, design[bad], radius, cutting[bad, 2] + TOP + ALLOWANCE)

    def gouge(k: int) -> Gouge:
        i = bad[k]
        return Gouge(
            x=float(design[i, 0]),
            y=float(design[i, 1]),
            tip=float(cutting[i, 2]),
            model=float(highest[i] - TOP),
            inside=float(inside[k]),
            part=milled.names[owners[k]],
        )

    parts = Counter(milled.names[owner] for owner in owners)
    pytest.fail(
        describe(
            [gouge(k) for k in np.argsort(-overlap[bad], kind="stable")[:8]],
            [gouge(k) for k in np.argsort(-inside, kind="stable")[:8]],
            len(bad),
            len(cutting),
            ", ".join(f"{part} {n}" for part, n in parts.most_common()),
        )
    )
