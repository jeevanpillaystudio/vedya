"""The April 2024 toolpaths, read from their G-code, and a model seen from above.

Shire was milled in April 2024 with two toolpaths, `public/cnc-cuts/6mm-adaptive.tap` and
`3mm-adaptive.tap`, adaptive clearing with flat end mills of 6 and 3 mm, which CAM wrote
from that month's model. `read_toolpath` reads where such a program puts the tool's tip,
and `plan` what of a model stands at or above each of its heights, seen from above.
`tests/test_toolpaths.py` holds Shire to the toolpaths with them, and `tools/figures.py`
draws the surface the toolpaths cut.

- The toolpaths' z = 0 is the design's top, `TOP` up. Their X runs along the board's
  length, which is the design's y, and their Y across it, the design's x.
- The reader follows the tool wherever it goes: to each programmed point, and along each
  line and arc between them. It refuses any code it does not follow rather than skip it.
- A plan reads a model exactly. Every face of it must be level or upright everywhere, as
  a slab's are, and any other face is refused. So what of it stands above a height is,
  seen from above, the union of its upward faces at that height and higher, and changes
  only at those faces' heights; heights within 1e-6 mm of each other are taken as the
  highest of them. Each face is drawn as a polygon whose sides stray at most a chord
  from its edges.

Every length is in millimetres.
"""

import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import build123d as bd
import numpy as np
import numpy.typing as npt
import shapely

# OCP is compiled and ships no type stubs, so its names are invisible to the type checker.
from OCP.BRepAdaptor import (
    BRepAdaptor_Curve,  # pyright: ignore[reportAttributeAccessIssue]
    BRepAdaptor_Surface,  # pyright: ignore[reportAttributeAccessIssue]
)
from OCP.BRepTools import BRepTools_WireExplorer  # pyright: ignore[reportAttributeAccessIssue]
from OCP.GCPnts import GCPnts_TangentialDeflection  # pyright: ignore[reportAttributeAccessIssue]
from OCP.GeomAbs import GeomAbs_SurfaceType  # pyright: ignore[reportAttributeAccessIssue]
from OCP.TopAbs import TopAbs_Orientation  # pyright: ignore[reportAttributeAccessIssue]
from shapely.geometry.base import BaseGeometry

__all__ = [
    "CHORD",
    "CNC_CUTS",
    "STEP",
    "TOOL_RADII",
    "TOP",
    "Floats",
    "Plan",
    "Toolpath",
    "corners",
    "loops",
    "plan",
    "read_toolpath",
    "upward_faces",
]

type Floats = npt.NDArray[np.float64]

CNC_CUTS = Path(__file__).parent.parent / "public" / "cnc-cuts"
"""The toolpaths the piece was milled with."""

TOOL_RADII = {"6mm-adaptive.tap": 3.0, "3mm-adaptive.tap": 1.5}
"""Each toolpath's tool radius, as its header gives the diameter."""

TOP = 38.4
"""The design's top, where the toolpaths' z is 0."""

CHORD = 0.005
"""How far the sides of a face's polygon may stray from its edges."""

STEP = 0.25
"""The longest stretch of a move between two positions checked."""


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
