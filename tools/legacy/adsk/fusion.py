"""The `adsk.fusion` members Vedya's scripts call, on build123d, in centimetres.

A design is a tree of components. Each holds bodies, construction planes, sketches and
the features that make bodies. Every component sits at the identity transform, as the
scripts create them, so a plane's height is its height in the design.

How the features behave is the stand-in's contract, set by what Fusion built for the
piece that was milled:

- A sketch's profiles are the closed regions its curves bound, each with its inner
  loops. A region's `areaProperties().area` is exact.
- A thin extrude's wall grows inside the profile on Side1, outside it on Side2, and
  astride it on Center, with sharp corners.
- A Cut, Intersect or Join extrude reaches the bodies it overlaps in its own component
  and the components inside it. It never reaches a sibling's or a parent's bodies.
- A Cut or Intersect that reaches no body raises `RuntimeError(NO_TARGET)`, as Fusion's
  `add` does. A Join that reaches none makes a new body.
- A combine changes its target and, unless told to keep them, deletes its tools.

Members Fusion's scripts can call are camelCase, as Fusion names them. snake_case members
are the stand-in's own, for the tools that read what a script built.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from enum import IntEnum
from typing import Any

import build123d as bd
from build123d.topology import Shape

# OCP is compiled and ships no type stubs, so its names are invisible to the type checker.
from OCP.BRepAlgoAPI import BRepAlgoAPI_Splitter  # pyright: ignore[reportAttributeAccessIssue]
from OCP.collections import List_TopoDS_Shape  # pyright: ignore[reportAttributeAccessIssue]

from tools.legacy.adsk import core
from vedya.model import fingerprint

__all__ = [
    "NO_TARGET",
    "AreaProperties",
    "BRepBodies",
    "BRepBody",
    "CombineFeature",
    "CombineFeatureInput",
    "CombineFeatures",
    "Component",
    "ConstructionPlane",
    "ConstructionPlaneInput",
    "ConstructionPlanes",
    "Design",
    "DesignTypes",
    "ExtrudeFeature",
    "ExtrudeFeatureInput",
    "ExtrudeFeatures",
    "FeatureOperations",
    "Features",
    "Occurrence",
    "Occurrences",
    "Profile",
    "Profiles",
    "Sketch",
    "SketchCircle",
    "SketchCircles",
    "SketchCurves",
    "SketchLine",
    "SketchLineList",
    "SketchLines",
    "SketchPoint",
    "Sketches",
    "ThinExtrudeWallLocation",
]

NO_TARGET = "No target body found to cut or intersect!"
"""The message of Fusion's error when a Cut or Intersect reaches no body."""


class DesignTypes(IntEnum):
    DirectDesignType = 0
    ParametricDesignType = 1


class FeatureOperations(IntEnum):
    JoinFeatureOperation = 0
    CutFeatureOperation = 1
    IntersectFeatureOperation = 2
    NewBodyFeatureOperation = 3
    NewComponentFeatureOperation = 4


class ThinExtrudeWallLocation(IntEnum):
    Side1 = 0
    Side2 = 1
    Center = 2


class _Collection[T]:
    """One of Fusion's read-only collections: `count`, `item(index)`, iteration, `len`."""

    def __init__(self, items: Iterable[T] = ()) -> None:
        self._items: list[T] = list(items)

    @property
    def count(self) -> int:
        return len(self._items)

    def item(self, index: int) -> T:
        return self._items[index]

    def __iter__(self) -> Iterator[T]:
        return iter(list(self._items))

    def __len__(self) -> int:
        return len(self._items)


class Design(core.Product):
    """A document's design: its type and its root component."""

    def __init__(self) -> None:
        self.designType = DesignTypes.ParametricDesignType
        self._root = Component("root")

    @property
    def rootComponent(self) -> Component:
        return self._root


class BRepBody:
    """A solid body in a component. `shape` holds its solids, in centimetres."""

    def __init__(self, shape: bd.Part, component: Component, name: str) -> None:
        self.shape = shape
        self.name = name
        self.parentComponent = component
        self.isValid = True


class BRepBodies(_Collection[BRepBody]):
    pass


class Component:
    """A component: its bodies, the components inside it, and what makes its geometry."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._bodies: list[BRepBody] = []
        self._made = 0
        self.occurrences = Occurrences()
        self.xYConstructionPlane = ConstructionPlane("XY", 0.0)
        self.constructionPlanes = ConstructionPlanes()
        self.sketches = Sketches()
        self.features = Features(self)

    @property
    def bRepBodies(self) -> BRepBodies:
        return BRepBodies(self._bodies)

    def add_body(self, shape: bd.Part) -> BRepBody:
        """A new body of `shape` in this component."""
        self._made += 1
        body = BRepBody(shape, self, f"Body{self._made}")
        self._bodies.append(body)
        return body

    def remove_body(self, body: BRepBody) -> None:
        """Delete `body` from this component."""
        self._bodies.remove(body)
        body.isValid = False

    def reach(self) -> list[BRepBody]:
        """The bodies a feature of this component can reach: its own, then those of the
        components inside it, depth first."""
        bodies = list(self._bodies)
        for occurrence in self.occurrences:
            bodies.extend(occurrence.component.reach())
        return bodies


class Occurrence:
    """A component placed in its parent. Every placement is the identity."""

    def __init__(self, component: Component) -> None:
        self.component = component


class Occurrences(_Collection[Occurrence]):
    def addNewComponent(self, transform: core.Matrix3D) -> Occurrence:
        occurrence = Occurrence(Component(f"Component{len(self._items) + 1}"))
        self._items.append(occurrence)
        return occurrence


class ConstructionPlane:
    """A plane parallel to XY, `z` centimetres up."""

    def __init__(self, name: str, z: float) -> None:
        self.name = name
        self.z = z


class ConstructionPlaneInput:
    def __init__(self) -> None:
        self.z: float | None = None

    def setByOffset(self, planarEntity: ConstructionPlane, offset: core.ValueInput) -> bool:
        self.z = planarEntity.z + offset.realValue
        return True


class ConstructionPlanes(_Collection[ConstructionPlane]):
    def createInput(self) -> ConstructionPlaneInput:
        return ConstructionPlaneInput()

    def add(self, planeInput: ConstructionPlaneInput) -> ConstructionPlane:
        if planeInput.z is None:
            raise RuntimeError("the construction plane input was never defined")
        plane = ConstructionPlane(f"Plane{len(self._items) + 1}", planeInput.z)
        self._items.append(plane)
        return plane


class Sketch:
    """Curves drawn on a plane `z` centimetres up, and the closed regions they bound."""

    def __init__(self, z: float) -> None:
        self.name = ""
        self.z = z
        self.sketchCurves = SketchCurves()
        self._profiles = Profiles()
        self._profiled = 0

    @property
    def profiles(self) -> Profiles:
        edges = self.sketchCurves.edges
        if self._profiled != len(edges):
            self._profiles = Profiles(Profile(face, self.z) for face in _regions(edges))
            self._profiled = len(edges)
        return self._profiles


class Sketches(_Collection[Sketch]):
    def add(self, planarEntity: ConstructionPlane) -> Sketch:
        sketch = Sketch(planarEntity.z)
        self._items.append(sketch)
        return sketch


class SketchPoint:
    """A point on a sketch. The scripts name it in an annotation and never make one."""


class SketchCurves:
    def __init__(self) -> None:
        self.edges: list[bd.Edge] = []
        self.sketchCircles = SketchCircles(self.edges)
        self.sketchLines = SketchLines(self.edges)


class SketchCircle:
    def __init__(self, centre: core.Point3D, radius: float) -> None:
        self.centre = centre
        self.radius = radius


class SketchCircles(_Collection[SketchCircle]):
    def __init__(self, edges: list[bd.Edge]) -> None:
        super().__init__()
        self._edges = edges

    def addByCenterRadius(self, centerPoint: core.Point3D, radius: float) -> SketchCircle:
        _on_the_sketch(centerPoint)
        if not radius > 0:
            raise RuntimeError(f"a circle needs a positive radius, not {radius!r}")
        self._edges.append(
            bd.Edge.make_circle(radius, bd.Plane(origin=(centerPoint.x, centerPoint.y, 0.0)))
        )
        circle = SketchCircle(centerPoint, radius)
        self._items.append(circle)
        return circle


class SketchLine:
    def __init__(self, start: tuple[float, float], end: tuple[float, float]) -> None:
        self.start = start
        self.end = end


class SketchLineList(_Collection[SketchLine]):
    pass


class SketchLines(_Collection[SketchLine]):
    def __init__(self, edges: list[bd.Edge]) -> None:
        super().__init__()
        self._edges = edges

    def addTwoPointRectangle(
        self, pointOne: core.Point3D, pointTwo: core.Point3D
    ) -> SketchLineList:
        _on_the_sketch(pointOne)
        _on_the_sketch(pointTwo)
        (x0, y0), (x1, y1) = (pointOne.x, pointOne.y), (pointTwo.x, pointTwo.y)
        if x0 == x1 or y0 == y1:
            raise RuntimeError("a rectangle's two corners must differ in x and in y")
        corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        lines = [SketchLine(corners[i], corners[(i + 1) % 4]) for i in range(4)]
        for line in lines:
            self._edges.append(bd.Edge.make_line((*line.start, 0.0), (*line.end, 0.0)))
        self._items.extend(lines)
        return SketchLineList(lines)


class AreaProperties:
    def __init__(self, area: float) -> None:
        self.area = area


class Profile:
    """A closed region of a sketch: `face` in the sketch's plane, which is `z` up."""

    def __init__(self, face: bd.Face, z: float) -> None:
        self.face = face
        self.z = z

    def areaProperties(self) -> AreaProperties:
        return AreaProperties(fingerprint(self.face).area)


class Profiles(_Collection[Profile]):
    pass


class ExtrudeFeatureInput:
    def __init__(self, profile: Profile, operation: FeatureOperations) -> None:
        self.profile = profile
        self.operation = operation
        self.distance: float | None = None
        self.wall: tuple[ThinExtrudeWallLocation, float] | None = None

    def setDistanceExtent(self, isSymmetric: bool, distance: core.ValueInput) -> bool:
        if isSymmetric:
            raise NotImplementedError("the stand-in extrudes to one side of the sketch only")
        self.distance = distance.realValue
        return True

    def setThinExtrude(
        self,
        thinExtrudeWallLocationOne: ThinExtrudeWallLocation,
        thinExtrudeWallThicknessOne: core.ValueInput,
    ) -> bool:
        self.wall = (
            ThinExtrudeWallLocation(thinExtrudeWallLocationOne),
            thinExtrudeWallThicknessOne.realValue,
        )
        return True


class ExtrudeFeature:
    def __init__(self, bodies: Iterable[BRepBody]) -> None:
        self.bodies = BRepBodies(bodies)


class ExtrudeFeatures(_Collection[ExtrudeFeature]):
    def __init__(self, component: Component) -> None:
        super().__init__()
        self._component = component

    def createInput(self, profile: object, operation: FeatureOperations) -> ExtrudeFeatureInput:
        if not isinstance(profile, Profile):
            raise NotImplementedError("the stand-in extrudes one profile at a time")
        return ExtrudeFeatureInput(profile, FeatureOperations(operation))

    def add(self, extrudeInput: ExtrudeFeatureInput) -> ExtrudeFeature:
        distance = extrudeInput.distance
        if distance is None or distance == 0:
            raise RuntimeError("the extrude has no distance")
        region = extrudeInput.profile.face
        if extrudeInput.wall is not None:
            region = _thin_wall(region, *extrudeInput.wall)
        placed = region.moved(bd.Location((0.0, 0.0, extrudeInput.profile.z)))
        tool = bd.Part([bd.Solid.extrude(placed, bd.Vector(0.0, 0.0, distance))])
        feature = ExtrudeFeature(_apply(self._component, tool, extrudeInput.operation))
        self._items.append(feature)
        return feature


class CombineFeatureInput:
    def __init__(self, targetBody: BRepBody, toolBodies: core.ObjectCollection) -> None:
        self.targetBody = targetBody
        self.toolBodies = toolBodies
        self.operation = FeatureOperations.JoinFeatureOperation
        self.isKeepToolBodies = False
        self.isNewComponent = False


class CombineFeature:
    def __init__(self, bodies: Iterable[BRepBody]) -> None:
        self.bodies = BRepBodies(bodies)


class CombineFeatures(_Collection[CombineFeature]):
    def createInput(
        self, targetBody: BRepBody, toolBodies: core.ObjectCollection
    ) -> CombineFeatureInput:
        return CombineFeatureInput(targetBody, toolBodies)

    def add(self, combineInput: CombineFeatureInput) -> CombineFeature:
        if combineInput.isNewComponent:
            raise NotImplementedError("the stand-in combines into the target's component only")
        target = combineInput.targetBody
        tools: list[BRepBody] = []
        for item in combineInput.toolBodies:
            if not isinstance(item, BRepBody):
                raise TypeError(f"a combine's tools are bodies, not {type(item).__name__}")
            tools.append(item)
        if not tools:
            raise RuntimeError("a combine needs at least one tool body")
        if target in tools:
            raise RuntimeError("a combine's target cannot also be its tool")
        if not all(body.isValid for body in (target, *tools)):
            raise RuntimeError("a combine was given a body that no longer exists")
        tool = _union(body.shape for body in tools)
        match FeatureOperations(combineInput.operation):
            case FeatureOperations.JoinFeatureOperation:
                result = target.shape + tool
            case FeatureOperations.CutFeatureOperation:
                result = target.shape - tool
            case FeatureOperations.IntersectFeatureOperation:
                result = target.shape & tool
            case operation:
                raise NotImplementedError(f"the stand-in cannot combine with {operation.name}")
        if not result.solids():
            raise RuntimeError("the combine leaves nothing of its target body")
        target.shape = _part(result)
        if not combineInput.isKeepToolBodies:
            for body in tools:
                body.parentComponent.remove_body(body)
        feature = CombineFeature([target])
        self._items.append(feature)
        return feature


class Features:
    def __init__(self, component: Component) -> None:
        self.extrudeFeatures = ExtrudeFeatures(component)
        self.combineFeatures = CombineFeatures()


def _apply(component: Component, tool: bd.Part, operation: FeatureOperations) -> list[BRepBody]:
    """Apply an extruded `tool` made by a feature of `component`; the bodies it made or changed."""
    match operation:
        case FeatureOperations.NewBodyFeatureOperation:
            return [component.add_body(tool)]
        case FeatureOperations.NewComponentFeatureOperation:
            raise NotImplementedError("the stand-in cannot extrude into a new component")
        case _:
            pass
    reached = [body for body in component.reach() if _overlaps(body.shape, tool)]
    if operation is FeatureOperations.JoinFeatureOperation:
        if not reached:
            return [component.add_body(tool)]
        if len({id(body.parentComponent) for body in reached}) > 1:
            raise NotImplementedError("the stand-in cannot join bodies of different components")
        first, *rest = reached
        first.shape = _union([first.shape, tool, *(body.shape for body in rest)])
        for body in rest:
            body.parentComponent.remove_body(body)
        return [first]
    if not reached:
        raise RuntimeError(NO_TARGET)
    for body in reached:
        if operation is FeatureOperations.CutFeatureOperation:
            left = _part(body.shape - tool)
        else:
            left = _part(body.shape & tool)
        if left.solids():
            body.shape = left
        else:
            body.parentComponent.remove_body(body)
    return [body for body in reached if body.isValid]


def _regions(edges: list[bd.Edge]) -> list[bd.Face]:
    """The closed regions `edges` bound on the XY plane, each with its inner loops.

    A face larger than the edges is split by every edge; the pieces that do not touch its
    border are the regions. They are ordered by their low corner, then their area.
    """
    if not edges:
        return []
    box = bd.Compound(edges).bounding_box()
    margin = max(box.size.X, box.size.Y, 1.0)
    low_x, low_y = box.min.X - margin, box.min.Y - margin
    high_x, high_y = box.max.X + margin, box.max.Y + margin
    sheet = bd.Face(
        bd.Wire.make_polygon(
            [(low_x, low_y), (high_x, low_y), (high_x, high_y), (low_x, high_y)], close=True
        )
    )
    arguments, tools = List_TopoDS_Shape(), List_TopoDS_Shape()
    arguments.Append(sheet.wrapped)
    for edge in edges:
        tools.Append(edge.wrapped)
    splitter = BRepAlgoAPI_Splitter()
    splitter.SetArguments(arguments)
    splitter.SetTools(tools)
    splitter.Build()
    if not splitter.IsDone():
        raise RuntimeError("the sketch's curves could not be split into regions")
    # Every curve lies `margin` inside the sheet's border, so the one piece that reaches
    # halfway there is the piece outside every curve.
    reach = margin / 2

    def enclosed(face: bd.Face) -> bool:
        piece = face.bounding_box()
        return (
            box.min.X - reach < piece.min.X
            and box.min.Y - reach < piece.min.Y
            and box.max.X + reach > piece.max.X
            and box.max.Y + reach > piece.max.Y
        )

    regions = [face for face in bd.Compound(splitter.Shape()).faces() if enclosed(face)]
    return sorted(regions, key=_region_order)


def _region_order(face: bd.Face) -> tuple[float, float, float]:
    box = face.bounding_box()
    return (round(box.min.X, 9), round(box.min.Y, 9), round(face.area, 9))


def _thin_wall(face: bd.Face, side: ThinExtrudeWallLocation, thickness: float) -> bd.Face:
    """The band of `thickness` along `face`'s outline, on `side` of it."""
    if face.inner_wires():
        raise NotImplementedError("the stand-in cannot thin-extrude a profile with holes")
    if not thickness > 0:
        raise RuntimeError(f"a thin wall needs a positive thickness, not {thickness!r}")
    outline = face.outer_wire()
    match side:
        case ThinExtrudeWallLocation.Side1:
            outer, inner = outline, _offset(outline, -thickness)
        case ThinExtrudeWallLocation.Side2:
            outer, inner = _offset(outline, thickness), outline
        case ThinExtrudeWallLocation.Center:
            outer, inner = _offset(outline, thickness / 2), _offset(outline, -thickness / 2)
    return bd.Face(outer, [inner])


def _offset(wire: bd.Wire, distance: float) -> bd.Wire:
    """`wire` moved `distance` outwards, or inwards where negative, keeping sharp corners."""
    try:
        moved = wire.offset_2d(distance, kind=bd.Kind.INTERSECTION)
    except RuntimeError as error:
        raise RuntimeError(f"a thin wall of {abs(distance):g} cm closes the profile up") from error
    return moved if isinstance(moved, bd.Wire) else bd.Wire([moved])


def _overlaps(body: bd.Part, tool: bd.Part) -> bool:
    """Whether `body` and `tool` share volume; solids that only touch do not."""
    a, b = body.bounding_box(), tool.bounding_box()
    if (
        a.max.X < b.min.X
        or b.max.X < a.min.X
        or a.max.Y < b.min.Y
        or b.max.Y < a.min.Y
        or a.max.Z < b.min.Z
        or b.max.Z < a.min.Z
    ):
        return False
    return bool((body & tool).solids())


def _union(shapes: Iterable[bd.Part]) -> bd.Part:
    first, *rest = shapes
    return _part(first + rest) if rest else first


def _part(shape: Shape[Any]) -> bd.Part:
    """`shape` as a `Part`; build123d types its boolean operators loosely."""
    return shape if isinstance(shape, bd.Part) else bd.Part(shape.solids())


def _on_the_sketch(point: core.Point3D) -> None:
    if point.z != 0:
        raise NotImplementedError("the stand-in draws only in the sketch's own plane, at z = 0")
