"""Shire is never above where the toolpaths it was milled from put the tool.

The piece was milled in April 2024 with two toolpaths, `public/cnc-cuts/6mm-adaptive.tap`
and `3mm-adaptive.tap`, adaptive clearing with flat end mills of 6 and 3 mm, which CAM
wrote from that month's model. Wherever the tool went, the model was not: under the
tool's flat end, a disc of its radius at its tip, no point of the model stands higher
than the tip.

- The toolpaths' z = 0 is the design's top, 38.4 mm up. Their X runs along the board's
  length, which is the design's y, and their Y across it, the design's x.
- The model is read exactly, in plan. It is a stack of flat slabs, so what of it stands
  above a height is, seen from above, the union of its upward faces at that height and
  higher, and changes only at those faces' heights. Each face is drawn as a polygon
  whose sides stray at most 0.005 mm from its edges, which is the check's resolution.
  The model is the union of its parts, so its plan is the union of theirs.
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
  and arc between them every quarter millimetre.

Every length is in millimetres.
"""

import math
import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import build123d as bd
import numpy as np
import numpy.typing as npt
import pytest
import shapely

# OCP is compiled and ships no type stubs, so its names are invisible to the type checker.
from OCP.BRepAdaptor import BRepAdaptor_Curve  # pyright: ignore[reportAttributeAccessIssue]
from OCP.BRepTools import BRepTools_WireExplorer  # pyright: ignore[reportAttributeAccessIssue]
from OCP.GCPnts import GCPnts_TangentialDeflection  # pyright: ignore[reportAttributeAccessIssue]
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

    Every face of a solid must be horizontal or vertical, as a slab's are: a solid stands
    over a point up to its highest upward face there.
    """
    by_top: dict[float, dict[str, list[shapely.Polygon]]] = {}
    for name, solid in zip(names, solids, strict=True):
        for face in solid.faces():
            upward = face.normal_at().Z
            if face.geom_type == bd.GeomType.PLANE and abs(upward - 1) < 1e-9:
                top = round(face.center().Z, 6)
                by_top.setdefault(top, {}).setdefault(name, []).append(_polygon(face, chord))
            elif abs(upward) > 1e-9 and abs(upward + 1) > 1e-9:
                raise ValueError(f"a {face.geom_type.name} face neither horizontal nor vertical")
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


def _polygon(face: bd.Face, chord: float) -> shapely.Polygon:
    """`face`, which is level, as a polygon in XY whose sides stray at most `chord` from
    its edges."""
    polygon = shapely.Polygon(
        _ring(face.outer_wire(), face, chord),
        [_ring(wire, face, chord) for wire in face.inner_wires()],
    )
    if not polygon.is_valid:
        raise ValueError(f"a face drew as an invalid polygon: {shapely.is_valid_reason(polygon)}")
    return polygon


_TURN = 0.1
"""The furthest, in radians, a face's edge may turn between neighbouring corners."""


def _ring(wire: bd.Wire, face: bd.Face, chord: float) -> list[tuple[float, float]]:
    """The corners of a polygon along `wire`, a loop of `face`, in the loop's order."""
    corners: list[tuple[float, float]] = []
    explorer = BRepTools_WireExplorer(wire.wrapped, face.wrapped)
    while explorer.More():
        edge = explorer.Current()
        curve = BRepAdaptor_Curve(edge)
        # OpenCascade's mesher's sampling, which also bounds how far the curve turns
        # between neighbouring points, so that it follows an astroid round its cusps; its
        # sampling by deflection alone cuts their tips by up to 0.34 mm. It is asked for
        # half the chord, since its bound is approximate: asked for 0.005 mm, it strays
        # up to 0.0055 mm on Shire's splines; asked for half, 0.0025 mm.
        points = GCPnts_TangentialDeflection(curve, _TURN, chord / 2, 2, 1e-9, 1e-7)
        along = [
            (points.Value(i).X(), points.Value(i).Y()) for i in range(1, points.NbPoints() + 1)
        ]
        if edge.Orientation() == TopAbs_Orientation.TopAbs_REVERSED:
            along.reverse()
        corners.extend(along[:-1])  # the next edge starts where this one ends
        explorer.Next()
    return corners


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


def test_the_reader_refuses_what_it_does_not_follow() -> None:
    with pytest.raises(ValueError, match="no flat end mill"):
        read_toolpath("G0 X0. Y0. Z0.", STEP)
    with pytest.raises(ValueError, match="incremental"):
        read_toolpath(PROGRAM.replace("G0 X10.", "G91 G0 X10."), STEP)


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
    cutting = path.positions[path.positions[:, 2] < 0]
    # The design's x is the toolpath's Y, and its y the toolpath's X; its z is the
    # toolpath's above the design's floor.
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
