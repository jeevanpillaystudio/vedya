"""Shire is never above where the toolpaths it was milled from put the tool.

The piece was milled in April 2024 with two toolpaths, `public/cnc-cuts/6mm-adaptive.tap`
and `3mm-adaptive.tap`, adaptive clearing with flat end mills of 6 and 3 mm, which CAM
wrote from that month's model. Wherever the tool went, the model was not: under the
tool's flat end, a disc of its radius at its tip, no point of the model stands higher
than the tip.

- The toolpaths' z = 0 is the design's top, 38.4 mm up. Their X runs along the board's
  length, which is the design's y, and their Y across it, the design's x.
- The model is read exactly, in plan. Every face of it is level or upright everywhere,
  as a slab's are, and any other face is refused. So what of it stands above a height
  is, seen from above, the union of its upward faces at that height and higher, and
  changes only at those faces' heights; heights within 1e-6 mm of each other are taken
  as the highest of them. Each face is drawn as a polygon whose sides stray at most
  0.005 mm from its edges, which is the check's resolution; a slow test holds every
  edge of the model to it. The model is the union of its parts, so its plan is the
  union of theirs.
- The border is left out. The toolpaths cut where a wall inside the board's edge would
  stand, so the milled piece had none; ADR 0003 records the open question.
- A tip may sit 0.15 mm into the model: the stock CAM left on floors.
- A tool position is checked against what stands more than 0.15 mm above its tip: the
  horizontal distance from the tool's centre to that region. It fails only where the
  distance is less than the tool's radius less 0.1 mm, where the model stands more than
  0.1 mm inside the edge of the tool's circle. CAM brings the tool to a wall within its
  own cutting tolerance; the deepest graze is 0.070 mm, with the 3 mm tool. The 0.1 mm
  stays an order of magnitude below 1.2 mm, the shallowest step of a seed-of-life
  layer, the smallest error this test exists to catch.
- The tool is checked wherever it goes: at each programmed point, and along each line
  and arc between them, no two points more than a quarter millimetre apart. The reader
  refuses any code it does not follow rather than skip it.

Every length is in millimetres.
"""

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
import shapely

# OCP is compiled and ships no type stubs, so its names are invisible to the type checker.
from OCP.BRepAdaptor import (
    BRepAdaptor_Curve,  # pyright: ignore[reportAttributeAccessIssue]
    BRepAdaptor_Surface,  # pyright: ignore[reportAttributeAccessIssue]
)
from OCP.BRepTools import BRepTools_WireExplorer  # pyright: ignore[reportAttributeAccessIssue]
from OCP.GCPnts import GCPnts_TangentialDeflection  # pyright: ignore[reportAttributeAccessIssue]
from OCP.GeomAbs import (
    GeomAbs_CurveType,  # pyright: ignore[reportAttributeAccessIssue]
    GeomAbs_SurfaceType,  # pyright: ignore[reportAttributeAccessIssue]
)
from OCP.TopAbs import TopAbs_Orientation  # pyright: ignore[reportAttributeAccessIssue]
from shapely.geometry.base import BaseGeometry

from vedya.geometry import astroid, circle, rectangle, slab
from vedya.model import Model

type Floats = npt.NDArray[np.float64]

CNC_CUTS = Path(__file__).parent.parent / "public" / "cnc-cuts"
"""The toolpaths the piece was milled with."""

TOOL_RADII = {"6mm-adaptive.tap": 3.0, "3mm-adaptive.tap": 1.5}
"""Each toolpath's tool radius, as its header gives the diameter."""

TOP = 38.4
"""The design's top, where the toolpaths' z is 0."""

ALLOWANCE = 0.15
"""How far a tip may sit into the model: stock left on floors."""

SIDEWAYS = 0.1
"""How far the model may reach inside the edge of the tool's circle: CAM's tolerance on
walls."""

CHORD = 0.005
"""How far the sides of a face's polygon may stray from its edges."""

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

_SETTINGS = frozenset({21, 40, 43, 49, 54, 90, 94})
"""G codes that change nothing the reader tracks: millimetres (G21), no cutter radius
offset (G40), the tool's length offset on and off (G43, G49), the first work offset
(G54), absolute moves (G90), and feed per minute (G94). The toolpaths give the tip's
position in the work offset's coordinates, after the length offset."""

_HOME = frozenset({28, 91})
"""The G codes of a return home, `G28 G91 Z0.`: through the named axes' zero, taken as
incremental, to the machine's home."""

_MACHINE = frozenset({3, 5, 6, 8, 9, 30})
"""M codes that move nothing: the spindle on and off, the tool change, coolant on and
off, and the program's end."""

_LETTERS = frozenset("GMXYZIJKFSTH")
"""The words the reader follows: the codes, the axes and an arc's centre, and the feed,
spindle speed, tool and length offset number, which change no position."""


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
    arc's start (G91.1) or absolute (G90.1), arcs given by their centre (I, J, K) in any
    of the three planes and helical along the third, and G28 returns to the machine's
    home, after which the axes it names are unknown until set again. Raises `ValueError`
    for any word, G code or M code the reader does not follow, an arc given by its
    radius (R), and an arc block that names no end, rather than skip it.
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
        line = _COMMENT.sub("", raw)
        if _WORD.sub("", line).strip() not in ("", "%"):
            raise ValueError(f"the reader cannot read {raw!r}")
        words = [(letter, float(value)) for letter, value in _WORD.findall(line)]
        letters = {letter for letter, _ in words}
        if unknown := letters - _LETTERS:
            raise ValueError(f"the reader does not follow {sorted(unknown)} words: {raw!r}")
        codes = [value for letter, value in words if letter == "G"]
        axes = {letter: value for letter, value in words if letter in "XYZ"}
        for code in (value for letter, value in words if letter == "M"):
            if code not in _MACHINE:
                raise ValueError(f"the reader does not follow M{code:g}: {raw!r}")
        if 28 in codes:
            if not set(codes) <= _HOME or letters & set("IJK"):
                raise ValueError(f"the reader follows a return home alone: {raw!r}")
            for letter in axes:
                position["XYZ".index(letter)] = math.nan
            continue
        for code in codes:
            if code in _MOTIONS:
                motion = int(code)
            elif code in _PLANES:
                plane = int(code)
            elif code in (90.1, 91.1):
                centre_relative = code == 91.1
            elif code == 91:
                raise ValueError(f"incremental moves are not read: {raw!r}")
            elif code not in _SETTINGS:
                raise ValueError(f"the reader does not follow G{code:g}: {raw!r}")
        centred = letters & set("IJK")
        if centred and motion not in (2, 3):
            raise ValueError(f"an arc's centre in a block that is no arc: {raw!r}")
        if not axes:
            if centred:
                raise ValueError(f"an arc block that names no end is not read: {raw!r}")
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
    """Points no more than `step` apart along an arc from `start` to `end`, helical along
    the plane's normal, ending at `end`.

    An arc whose end lies more than 0.01 mm nearer its centre or further from it than its
    start raises `ValueError`; within that, the radius changes evenly along the arc.
    """
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
    # Between neighbouring points the arc turns, widens and rises by equal shares of its
    # sweep, change of radius and rise. Their chord is no longer than those three shares
    # together, the turn taken at the larger radius, so this bounds every gap by `step`.
    length = math.sqrt(
        (abs(sweep) * max(radius, end_radius)) ** 2
        + (end_radius - radius) ** 2
        + (end[normal] - start[normal]) ** 2
    )
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


# The model in plan.


@dataclass(frozen=True)
class Plan:
    """What of some solids stands at or above each of their tops, seen from above.

    Attributes:
        tops: The heights of the solids' upward faces, lowest first.
        above: For each of `tops`, the region in XY over which some solid stands at that
            height or higher: the union of the upward faces there and higher up.
        faces: For each of `tops`, the upward faces there, joined by the name of the
            solid they are on.
    """

    tops: Floats
    above: tuple[BaseGeometry, ...]
    faces: tuple[dict[str, BaseGeometry], ...]

    def first_above(self, levels: Floats) -> npt.NDArray[np.intp]:
        """For each of `levels`, the index of the lowest top higher than it; the number
        of tops where none is."""
        return np.searchsorted(self.tops, levels, side="right")


def plan(solids: Sequence[bd.Part], names: Sequence[str], chord: float) -> Plan:
    """The plan of `solids`, named `names`, each face drawn to `chord`.

    Every face of a solid must be level or upright everywhere, as a slab's are (see
    `upward_faces`). Then a solid stands over a point up to its highest upward face there,
    so its upward faces alone say what stands where. Tops that agree within `_SAME` are
    one top, at the highest of them, so that no face is taken as lower than it is.
    """
    found = sorted(
        (
            (height, name, _polygon(face, chord))
            for name, solid in zip(names, solids, strict=True)
            for height, face in upward_faces(solid, name)
        ),
        key=lambda each: each[0],
    )
    by_top: dict[float, dict[str, list[shapely.Polygon]]] = {}
    group: list[tuple[float, str, shapely.Polygon]] = []
    for here in [*found, None]:
        if group and (here is None or here[0] - group[-1][0] > _SAME):
            top = group[-1][0]
            for _, name, polygon in group:
                by_top.setdefault(top, {}).setdefault(name, []).append(polygon)
            group = []
        if here is not None:
            group.append(here)
    tops = sorted(by_top)
    faces = tuple(
        {name: shapely.union_all(polygons) for name, polygons in by_top[top].items()}
        for top in tops
    )
    above: list[BaseGeometry] = []
    standing: BaseGeometry = shapely.Polygon()
    for here in reversed(faces):
        standing = shapely.union_all([standing, *here.values()])
        above.append(standing)
    above.reverse()
    # Prepared, a region answers distances through an index of its sides.
    shapely.prepare(above)
    return Plan(np.array(tops), tuple(above), faces)


_SAME = 1e-6
"""Tops closer than this, in mm, are one."""

_LEVEL = 1e-9
"""How far a level face's normal may lean from the z axis, or an upright face's axis or
direction; as the sine or cosine of the angle."""


def upward_faces(solid: bd.Part, name: str) -> list[tuple[float, bd.Face]]:
    """The faces of `solid` that face up, with their heights.

    A face facing up is a plane whose normal, after the face's orientation, is +z. Every
    other face must be a plane facing down, or upright everywhere: a plane whose normal is
    level, or a cylinder or a surface of extrusion whose axis or direction is the z axis.
    Any other face raises `ValueError`, naming `name` and the face.
    """
    found: list[tuple[float, bd.Face]] = []
    for index, face in enumerate(solid.faces()):
        surface = BRepAdaptor_Surface(face.wrapped)
        kind = surface.GetType()
        if kind == GeomAbs_SurfaceType.GeomAbs_Plane:
            frame = surface.Plane().Position()
            up = frame.Direction().Z()
            # The plane's normal is its frame's x direction across its y direction, its
            # main direction in a right-handed frame; a reversed face turns it over.
            if not frame.Direct():
                up = -up
            if face.wrapped.Orientation() == TopAbs_Orientation.TopAbs_REVERSED:
                up = -up
            if abs(up - 1) <= _LEVEL:
                found.append((frame.Location().Z(), face))
                continue
            if abs(up + 1) <= _LEVEL or abs(up) <= _LEVEL:
                continue
        elif kind == GeomAbs_SurfaceType.GeomAbs_Cylinder:
            if abs(abs(surface.Cylinder().Axis().Direction().Z()) - 1) <= _LEVEL:
                continue
        elif kind == GeomAbs_SurfaceType.GeomAbs_SurfaceOfExtrusion:
            if abs(abs(surface.Direction().Z()) - 1) <= _LEVEL:
                continue
        at = face.center()
        raise ValueError(
            f"{name}: face {index}, a {kind.name.removeprefix('GeomAbs_')} about "
            f"({at.X:.3f}, {at.Y:.3f}, {at.Z:.3f}), is neither level nor upright"
        )
    return found


def _polygon(face: bd.Face, chord: float) -> shapely.Polygon:
    """`face`, which is level, as a polygon in XY whose sides stray at most `chord` from
    its edges."""
    outer, *inner = (_ring(edges, chord) for edges in loops(face))
    polygon = shapely.Polygon(outer, inner)
    if not polygon.is_valid:
        raise ValueError(f"a face drew as an invalid polygon: {shapely.is_valid_reason(polygon)}")
    return polygon


_TURN = 0.1
"""The furthest, in radians, a face's edge may turn between neighbouring corners."""


def loops(face: bd.Face) -> list[list[Any]]:
    """The edges of each loop of `face`, outer first, each loop in its order round."""
    found: list[list[Any]] = []
    for wire in [face.outer_wire(), *face.inner_wires()]:
        edges: list[Any] = []
        explorer = BRepTools_WireExplorer(wire.wrapped, face.wrapped)
        while explorer.More():
            edges.append(explorer.Current())
            explorer.Next()
        found.append(edges)
    return found


def corners(edge: Any, chord: float) -> tuple[Floats, Floats]:
    """Points along `edge`, from its first parameter to its last, such that the chords
    between neighbours stray at most `chord` from it: their parameters, and their x and y.

    The sampling is OpenCascade's mesher's, which also bounds how far the curve turns
    between neighbouring points, so that it follows an astroid round its cusps; its
    sampling by deflection alone cuts their tips by up to 0.34 mm. It is asked for half
    the chord, since its bound is approximate: asked for 0.005 mm, it strays up to
    0.0055 mm on Shire's splines.
    """
    curve = BRepAdaptor_Curve(edge)
    points = GCPnts_TangentialDeflection(curve, _TURN, chord / 2, 2, 1e-9, 1e-7)
    count = points.NbPoints()
    parameters = np.array([points.Parameter(i) for i in range(1, count + 1)])
    xy = np.array([(points.Value(i).X(), points.Value(i).Y()) for i in range(1, count + 1)])
    return parameters, xy


def _ring(edges: Sequence[Any], chord: float) -> list[tuple[float, float]]:
    """The corners of a polygon along `edges`, a loop in its order round."""
    ring: list[tuple[float, float]] = []
    for edge in edges:
        _, xy = corners(edge, chord)
        along = [(float(x), float(y)) for x, y in xy]
        if edge.Orientation() == TopAbs_Orientation.TopAbs_REVERSED:
            along.reverse()
        ring.extend(along[:-1])  # the next edge starts where this one ends
    return ring


def stray(edge: Any, chord: float, spacing: float) -> tuple[float, float, float]:
    """How far the curve of `edge` strays from the chords between its `corners`.

    The curve is sampled no more than `spacing` apart, and each sample measured to the
    chord between the corners either side of it. Every chord's points then lie as near
    the curve too: as the curve runs from one corner to the next, it passes over each
    point of their chord, no further from it than from the chord's line. Returns the
    furthest sample, the widest gap between neighbouring samples, and how far the
    curve's own formula, where it is a line's or a circle's, misses OpenCascade's points
    at the corners.
    """
    curve = BRepAdaptor_Curve(edge)
    parameters, xy = corners(edge, chord)
    if not np.all(np.diff(parameters) > 0):
        raise ValueError("an edge's corners do not run from its first parameter to its last")
    misses = float(np.abs(_along(curve, parameters) - xy).max())
    sides = len(parameters) - 1
    counts = np.maximum(1, np.ceil(np.hypot(*np.diff(xy, axis=0).T) / spacing).astype(np.intp))
    while True:
        # Each side's samples run from the corner at its start up to the next one, and
        # the last corner closes the edge.
        side = np.repeat(np.arange(sides), counts)
        starts = np.cumsum(counts) - counts
        share = (np.arange(len(side)) - starts[side]) / counts[side]
        along = np.append(
            parameters[side] + (parameters[side + 1] - parameters[side]) * share,
            parameters[-1],
        )
        points = _along(curve, along)
        gaps = np.hypot(*np.diff(points, axis=0).T)
        widest = np.maximum.reduceat(gaps, starts)
        if (widest <= spacing).all():
            break
        counts = np.where(widest > spacing, counts * 2, counts)
    side = np.append(side, sides - 1)
    a, b = xy[side], xy[side + 1]
    ab = b - a
    t = np.clip(np.einsum("ij,ij->i", points - a, ab) / np.einsum("ij,ij->i", ab, ab), 0, 1)
    distance = np.hypot(*(points - (a + t[:, np.newaxis] * ab)).T)
    return float(distance.max()), float(gaps.max()), misses


def _along(curve: Any, parameters: Floats) -> Floats:
    """The x and y of `curve` at `parameters`. A line's and a circle's are worked out from
    their definitions, as OpenCascade gives them, at once; any other curve's point by
    point, by OpenCascade."""
    match curve.GetType():
        case GeomAbs_CurveType.GeomAbs_Line:
            line = curve.Line()
            origin, direction = line.Location(), line.Direction()
            return np.column_stack(
                [
                    origin.X() + parameters * direction.X(),
                    origin.Y() + parameters * direction.Y(),
                ]
            )
        case GeomAbs_CurveType.GeomAbs_Circle:
            circle_ = curve.Circle()
            centre, radius = circle_.Location(), circle_.Radius()
            x, y = circle_.XAxis().Direction(), circle_.YAxis().Direction()
            cos, sin = np.cos(parameters), np.sin(parameters)
            return np.column_stack(
                [
                    centre.X() + radius * (cos * x.X() + sin * y.X()),
                    centre.Y() + radius * (cos * x.Y() + sin * y.Y()),
                ]
            )
        case _:
            return np.array([(curve.Value(u).X(), curve.Value(u).Y()) for u in parameters])


def distance_above(plan: Plan, points: Floats, levels: Floats, reach: float) -> Floats:
    """For each of `points` in XY, the horizontal distance from it to what stands higher
    than its level in `levels`; inf where that is further than `reach`, or nothing is."""
    found = np.full(len(points), np.inf)
    first = plan.first_above(levels)
    for k in np.unique(first[first < len(plan.tops)]):
        which = np.nonzero(first == k)[0]
        region = plan.above[k]
        near = which[shapely.dwithin(region, shapely.points(points[which]), reach)]
        found[near] = shapely.distance(region, shapely.points(points[near]))
    return found


def inside_edge(plan: Plan, points: Floats, tips: Floats, radius: float) -> Floats:
    """For each tool position, its centre at `points` in XY and its tip at `tips` in z,
    how far inside the edge of its circle the model stands more than `ALLOWANCE` above
    the tip: `radius` less the distance to it; -inf where nothing stands within the
    circle."""
    return radius - distance_above(plan, points, tips + ALLOWANCE, radius)


# The reader and the plan, on what can be worked out by hand.

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


@pytest.mark.parametrize(
    ("line", "message"),
    [
        ("G91 G0 X10.", "incremental"),
        ("G41 G1 X10.", "does not follow G41"),
        ("G20", "does not follow G20"),
        ("M98", "does not follow M98"),
        ("G1 X10. P2", r"does not follow \['P'\] words"),
        ("G2 X6. Y4. R2.", r"does not follow \['R'\] words"),
        ("G2 I1. J0.", "names no end"),
        ("G1 X10. I1.", "no arc"),
        ("G28 G0 X0.", "return home alone"),
        ("G2 X7. Y4. I2. J0.", "ends"),
        ("X10. #1=2", "cannot read"),
    ],
)
def test_the_reader_refuses_what_it_does_not_follow(line: str, message: str) -> None:
    with pytest.raises(ValueError, match="no flat end mill"):
        read_toolpath("G0 X0. Y0. Z0.", STEP)
    # Each line in place of the program's last move, after it has cut at (5, 4, -1).
    with pytest.raises(ValueError, match=message):
        read_toolpath(PROGRAM.replace("G0 Z5.\n", f"{line}\n", 1), STEP)


def test_an_arcs_points_stay_a_step_apart_as_its_radius_changes() -> None:
    # A clockwise arc a step long at 1000 mm, its radius growing by 0.01 mm: the chord
    # between its ends is longer than a step, so it is sampled twice.
    radius, grown = 1000.0, 1000.01
    turn = (STEP - 1e-7) / grown
    start = np.array([0.0, 0.0, 0.0])
    end = np.array([radius - grown * math.cos(turn), grown * math.sin(turn), 0.0])
    points = _arc(start, end, [radius, 0.0, 0.0], True, 17, False, STEP)
    assert np.linalg.norm(end - start) > STEP
    gaps = np.linalg.norm(np.diff(np.vstack([start, points]), axis=0), axis=1)
    assert len(points) == 2
    assert gaps.max() <= STEP


def test_the_plan_holds_what_stands_above_each_top() -> None:
    board = slab(rectangle(20.0, 10.0), 0.0, 2.0)
    post = slab(circle(2.0, at=(5.0, 0.0)), 1.0, 4.0)
    seen = plan([board, post], ("board", "post"), CHORD)
    assert list(seen.tops) == [2.0, 5.0]
    # At the board's top, the post stands inside the board.
    assert seen.above[0].area == pytest.approx(200.0, rel=1e-12)
    assert set(seen.faces[0]) == {"board"}
    assert set(seen.faces[1]) == {"post"}
    # The post's top is a polygon inside its circle, its corners on it, short of it by
    # no more than the chord along its edge.
    top = seen.above[1]
    corners = shapely.get_coordinates(top)
    assert np.hypot(corners[:, 0] - 5.0, corners[:, 1]) == pytest.approx(2.0, abs=1e-9)
    assert 4 * math.pi - 2 * math.pi * 2.0 * CHORD <= top.area <= 4 * math.pi
    levels = np.array([1.0, 2.0, 4.99, 5.0])
    assert list(seen.first_above(levels)) == [0, 1, 1, 2]


def test_the_plan_follows_an_astroid_round_its_cusps() -> None:
    star = slab(astroid(185.6), 0.0, 1.0)
    seen = plan([star], ("star",), CHORD)
    (top,) = (face for face in star.faces() if face.center().Z > 0.5)
    sides = seen.above[0].boundary
    for edge in top.edges():
        curve = BRepAdaptor_Curve(edge.wrapped)
        along = np.linspace(curve.FirstParameter(), curve.LastParameter(), 20_001)
        points = np.array([(curve.Value(u).X(), curve.Value(u).Y()) for u in along])
        assert shapely.distance(sides, shapely.points(points)).max() <= CHORD
    # Each cusp's tip is a corner of the polygon.
    corners = shapely.get_coordinates(sides)
    for tip in ((185.6, 0.0), (0.0, 185.6), (-185.6, 0.0), (0.0, -185.6)):
        assert np.hypot(*(corners - tip).T).min() <= CHORD


@pytest.mark.parametrize(
    ("solid", "kind"),
    [
        (bd.Sphere(1.0), "Sphere"),
        (bd.Rot(0.0, 10.0, 0.0) * bd.Box(1.0, 1.0, 1.0), "Plane"),
        (bd.Rot(90.0, 0.0, 0.0) * bd.Cylinder(1.0, 2.0), "Cylinder"),
    ],
)
def test_a_face_neither_level_nor_upright_is_refused_by_name(solid: bd.Part, kind: str) -> None:
    with pytest.raises(ValueError, match=rf"odd: face \d+, a {kind} about .* neither level"):
        plan([slab(rectangle(4.0, 4.0), 0.0, 1.0), solid], ("board", "odd"), CHORD)


def test_tops_that_agree_within_a_micron_are_one_at_the_highest() -> None:
    low = slab(rectangle(4.0, 4.0), 0.0, 2.0)
    high = slab(rectangle(2.0, 2.0), 0.0, 2.0 + 5e-7)
    seen = plan([low, high], ("low", "high"), CHORD)
    assert list(seen.tops) == [2.0 + 5e-7]
    assert set(seen.faces[0]) == {"low", "high"}
    # A level between the two heights still has both faces above it.
    assert list(seen.first_above(np.array([2.0 + 2e-7]))) == [0]


def test_a_wall_between_the_old_grid_centres_is_seen() -> None:
    floor = slab(rectangle(10.0, 10.0), 0.0, 3.0)
    wall = slab(bd.Pos(4.0, 0.0) * rectangle(2.0, 10.0), 3.0, 2.0)
    seen = plan([floor, wall], ("floor", "wall"), CHORD)
    # The wall stands from x = 3 to 5. A tool of radius 3 at x = 0.25, its tip on the
    # floor, reaches 0.25 mm into it, between the centres at 3.25 of the 0.5 mm grid the
    # check once read. At x = 0.05 it grazes the wall by 0.05 mm, which is allowed.
    centres = np.array([[0.25, 0.25], [0.05, 0.25], [4.0, 0.0], [0.25, 0.25]])
    tips = np.array([3.0, 3.0, 3.0, 4.9])
    inside = inside_edge(seen, centres, tips, 3.0)
    assert inside[:3] == pytest.approx([0.25, 0.05, 3.0], abs=1e-9)
    # A tip within the allowance of the wall's top sees nothing above it.
    assert inside[3] == -np.inf
    assert list(inside > SIDEWAYS) == [True, False, True, False]


# The toolpaths against the model.


@pytest.fixture(scope="module")
def milled(shire: Model) -> Plan:
    names = [name for name in shire.parts if name not in LEFT_OUT]
    return plan([shire.parts[name] for name in names], names, CHORD)


SPACING = 0.002
"""The widest gap between samples of an edge's curve, when the plan's polygons are
checked against it."""


@pytest.mark.slow
def test_every_polygon_stays_within_the_chord_of_its_edges(shire: Model) -> None:
    # Every edge of every upward face of every part the toolpaths are checked against. The
    # curve between two samples lies within their gap of one of them, so the samples'
    # furthest stray and the widest gap bound how far the curve strays. Measured: 0.0025
    # mm at most, on the core's splines and Shire's circles.
    worst, widest, misses, edges = 0.0, 0.0, 0.0, 0
    for name, solid in shire.parts.items():
        if name in LEFT_OUT:
            continue
        for _, face in upward_faces(solid, name):
            for edge in (edge for loop in loops(face) for edge in loop):
                furthest, gap, missed = stray(edge, CHORD, SPACING)
                worst, widest = max(worst, furthest), max(widest, gap)
                misses, edges = max(misses, missed), edges + 1
    print(f"{edges} edges: the polygons stray at most {worst:.5f} mm from them")
    assert edges > 0
    assert misses <= 1e-9
    assert widest <= SPACING
    assert worst + widest <= CHORD


def highest_within(plan: Plan, points: Floats, reach: float) -> tuple[Floats, list[str]]:
    """For each of `points` in XY, the highest top of the plan whose region comes within
    `reach` of it, and the solid whose face at that top lies nearest; -inf and "" where
    none does."""
    heights = np.full(len(points), -np.inf)
    owners = [""] * len(points)
    left = np.arange(len(points))
    for k in reversed(range(len(plan.tops))):
        hit = shapely.dwithin(plan.above[k], shapely.points(points[left]), reach)
        found, left = left[hit], left[~hit]
        if len(found):
            # Nothing higher comes within reach, so what does lies in the faces at this top.
            heights[found] = plan.tops[k]
            names = list(plan.faces[k])
            distances = np.stack(
                [
                    shapely.distance(plan.faces[k][name], shapely.points(points[found]))
                    for name in names
                ]
            )
            for i, nearest in zip(found, distances.argmin(axis=0), strict=True):
                owners[i] = names[nearest]
    return heights, owners


@dataclass(frozen=True)
class Gouge:
    """Where a tool position cuts into the model, in the design's coordinates.

    Attributes:
        x: The tool's centre, along the board's width.
        y: The tool's centre, along the board's length.
        tip: The tool's tip, from the design's top.
        model: The highest top of the model within the tool's radius less `SIDEWAYS` of
            its centre, from the design's top.
        inside: How far inside the tool's edge the model stands more than `ALLOWANCE`
            above the tip: the radius less the distance to it.
        part: The part whose face at that highest top lies nearest the tool's centre.
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
            f"{count} of {of} positions have the model more than {SIDEWAYS} mm inside the "
            f"tool's edge, more than {ALLOWANCE} mm above its tip ({parts}).",
            "In the design's coordinates, with z from its top, the deepest:",
            *map(str, by_overlap),
            "and those furthest inside the tool's edge:",
            *map(str, by_inside),
        ]
    )


@pytest.mark.slow
@pytest.mark.parametrize(("name", "radius"), TOOL_RADII.items())
def test_no_tool_position_cuts_into_the_model(milled: Plan, name: str, radius: float) -> None:
    path = read_toolpath((CNC_CUTS / name).read_text(encoding="ascii"), STEP)
    assert path.diameter == 2 * radius
    gaps = np.linalg.norm(np.diff(path.positions, axis=0), axis=1)
    assert gaps.max() <= STEP + 1e-9
    cutting = path.positions[path.positions[:, 2] < 0]
    # The design's x is the toolpath's Y, and its y the toolpath's X. The toolpath's z is
    # measured from the design's top, which stands `TOP` above its floor.
    design = cutting[:, [1, 0]]
    tips = cutting[:, 2] + TOP
    inside = inside_edge(milled, design, tips, radius)
    bad = np.nonzero(inside > SIDEWAYS)[0]
    if not len(bad):
        return
    model, owners = highest_within(milled, design[bad], radius - SIDEWAYS)
    overlap = model - tips[bad]

    def gouge(k: int) -> Gouge:
        i = bad[k]
        return Gouge(
            x=float(design[i, 0]),
            y=float(design[i, 1]),
            tip=float(cutting[i, 2]),
            model=float(model[k] - TOP),
            inside=float(inside[i]),
            part=owners[k],
        )

    parts = Counter(owners)
    pytest.fail(
        describe(
            [gouge(k) for k in np.argsort(-overlap, kind="stable")[:8]],
            [gouge(k) for k in np.argsort(-inside[bad], kind="stable")[:8]],
            len(bad),
            len(cutting),
            ", ".join(f"{part} {n}" for part, n in parts.most_common()),
        )
    )
