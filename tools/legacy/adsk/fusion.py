"""The `adsk.fusion` members Vedya's scripts call, on build123d, in centimetres.

A design is a tree of components. Each holds bodies, construction planes, sketches and
the features that make bodies. Every component sits at the identity transform, as the
scripts create them, so a plane's height is its height in the design.

Every feature extrudes a sketch drawn parallel to XY straight along z, so a body is a
stack of prisms, and its shape is a `prisms.Stack`. Its booleans are worked out in the
plane, band by band, where OpenCascade's booleans hold; `prisms` says why.

How the features behave is the stand-in's contract, set by what Fusion built for the
piece that was milled:

- A sketch's profiles are the closed regions its curves bound, each with its inner
  loops. A region's `areaProperties().area` is exact.
- A thin extrude's wall grows inside the profile on Side1, outside it on Side2, and
  astride it on Center, with sharp corners.
- A Cut or Intersect extrude reaches every body it overlaps in its top-level component:
  the component under the root that holds the feature's component, or is it, and every
  component nested in it. It never reaches another top-level component's bodies.
- A Join extrude reaches only the bodies it overlaps in its own component, and makes a
  new body there when it reaches none.
- A Cut or Intersect that reaches no body raises `RuntimeError(NO_TARGET)`, as Fusion's
  `add` does.
- A combine changes its target and, unless told to keep them, deletes its tools.

The reach is what the April 2024 toolpaths record. A seed-of-life layer's later pass
trims the earlier pass's slabs it overlaps, so a leaf's Intersect reached its sibling
leaves under the layer's component. The middle cut and the kailash cut, each made from a
top-level component of its own, reached nothing: the centre was not bored, nor the
kailash band cut. A Join keeps to its own component: the April script joins each leaf's
rings into one body. Had a ring joined a sibling leaf's body instead, the leaf's combine
would have had no tools, and the run would have stopped before the core and the torus,
which were milled.

Where a script reaches behaviour that record does not settle, the stand-in chooses as
Autodesk documents it, or as the scripts assume:

- A fitted spline is the cubic spline that interpolates its fit points in order, as
  OpenCascade's `GeomAPI_Interpolate` makes it with its own parameters. It is never
  periodic: a spline whose first and last points coincide is a closed curve with a start
  and an end, as `SketchFittedSpline.isClosed` describes, and it bounds a region, as the
  astroids in the milled piece show.
- A three-point rectangle's first side runs from the first point to the second. Its other
  side is as long as the third point lies from that side's line, towards the third point.
- An occurrence is named `<component name>:1`. The scripts place each component once.
- A copy-paste puts a copy of each body into the component whose features made it. A
  combine changes its target body wherever that body is.
- A split by a plane leaves two bodies in the split body's component, listed lower piece
  first, as the scripts' slicer assumes. Fusion leaves their order undefined.

Members Fusion's scripts can call are camelCase, as Fusion names them. snake_case members
are the stand-in's own, for the tools that read what a script built.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from enum import IntEnum

import build123d as bd

# OCP is compiled and ships no type stubs, so its names are invisible to the type checker.
from OCP.BRepAlgoAPI import BRepAlgoAPI_Splitter  # pyright: ignore[reportAttributeAccessIssue]
from OCP.collections import List_TopoDS_Shape  # pyright: ignore[reportAttributeAccessIssue]

from tools.legacy import prisms
from tools.legacy.adsk import core
from tools.legacy.prisms import Stack
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
    "CopyPasteBodies",
    "CopyPasteBody",
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
    "SketchFittedSpline",
    "SketchFittedSplines",
    "SketchLine",
    "SketchLineList",
    "SketchLines",
    "SketchPoint",
    "Sketches",
    "SplitBodyFeature",
    "SplitBodyFeatureInput",
    "SplitBodyFeatures",
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
    """One of Fusion's read-only collections: `count`, `item(index)`, `[index]`, iteration,
    `len`."""

    def __init__(self, items: Iterable[T] = ()) -> None:
        self._items: list[T] = list(items)

    @property
    def count(self) -> int:
        return len(self._items)

    def item(self, index: int) -> T:
        return self._items[index]

    def __getitem__(self, index: int) -> T:
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
    """A solid body in a component. `shape` is its stack of prisms, in centimetres."""

    def __init__(self, shape: Stack, component: Component, name: str) -> None:
        self.shape = shape
        self.name = name
        self.parentComponent = component
        self.isValid = True

    @property
    def boundingBox(self) -> core.BoundingBox3D:
        low, high = self.shape.bounds
        return core.BoundingBox3D(core.Point3D.create(*low), core.Point3D.create(*high))


class BRepBodies(_Collection[BRepBody]):
    pass


class Component:
    """A component: its bodies, the components inside it, and what makes its geometry."""

    def __init__(self, name: str, parent: Component | None = None) -> None:
        self.name = name
        self.parent = parent
        self._bodies: list[BRepBody] = []
        self._made = 0
        self.occurrences = Occurrences(self)
        self.xYConstructionPlane = ConstructionPlane("XY", 0.0)
        self.constructionPlanes = ConstructionPlanes()
        self.sketches = Sketches()
        self.features = Features(self)

    @property
    def bRepBodies(self) -> BRepBodies:
        return BRepBodies(self._bodies)

    def add_body(self, shape: Stack) -> BRepBody:
        """A new body of `shape` in this component."""
        self._made += 1
        body = BRepBody(shape, self, f"Body{self._made}")
        self._bodies.append(body)
        return body

    def remove_body(self, body: BRepBody) -> None:
        """Delete `body` from this component."""
        self._bodies.remove(body)
        body.isValid = False

    def all_bodies(self) -> list[BRepBody]:
        """Its own bodies, then those of the components nested in it, depth first."""
        bodies = list(self._bodies)
        for occurrence in self.occurrences:
            bodies.extend(occurrence.component.all_bodies())
        return bodies

    def top_level(self) -> Component:
        """The component under the root that holds this one, or is it; the root is its own."""
        component = self
        while component.parent is not None and component.parent.parent is not None:
            component = component.parent
        return component


class Occurrence:
    """A component placed in its parent. Every placement is the identity."""

    def __init__(self, component: Component) -> None:
        self.component = component

    @property
    def name(self) -> str:
        """`<component name>:1`, as Fusion names a component's first occurrence."""
        return f"{self.component.name}:1"


class Occurrences(_Collection[Occurrence]):
    def __init__(self, owner: Component) -> None:
        super().__init__()
        self._owner = owner

    def addNewComponent(self, transform: core.Matrix3D) -> Occurrence:
        occurrence = Occurrence(Component(f"Component{len(self._items) + 1}", self._owner))
        self._items.append(occurrence)
        return occurrence

    def itemByName(self, name: str) -> Occurrence | None:
        return next((item for item in self._items if item.name == name), None)


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
        self.sketchFittedSplines = SketchFittedSplines(self.edges)
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


class SketchFittedSpline:
    def __init__(self, fit_points: list[tuple[float, float]]) -> None:
        self.fit_points = fit_points


class SketchFittedSplines(_Collection[SketchFittedSpline]):
    def __init__(self, edges: list[bd.Edge]) -> None:
        super().__init__()
        self._edges = edges

    def add(self, fitPoints: core.ObjectCollection) -> SketchFittedSpline:
        """The spline through `fitPoints`, in order: never periodic, closed where its ends
        coincide."""
        points: list[tuple[float, float]] = []
        for point in fitPoints:
            if not isinstance(point, core.Point3D):
                raise TypeError(f"a spline's fit points are Point3D, not {type(point).__name__}")
            _on_the_sketch(point)
            points.append((point.x, point.y))
        if len(points) < 2:
            raise RuntimeError("a spline needs at least two fit points")
        self._edges.append(bd.Edge.make_spline([(x, y, 0.0) for x, y in points]))
        spline = SketchFittedSpline(points)
        self._items.append(spline)
        return spline


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
        return self._rectangle([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])

    def addThreePointRectangle(
        self, pointOne: core.Point3D, pointTwo: core.Point3D, pointThree: core.Point3D
    ) -> SketchLineList:
        """The rectangle with a side from `pointOne` to `pointTwo`, reaching as far from that
        side's line as `pointThree` lies, towards it."""
        for point in (pointOne, pointTwo, pointThree):
            _on_the_sketch(point)
        (x0, y0), (x1, y1) = (pointOne.x, pointOne.y), (pointTwo.x, pointTwo.y)
        side_x, side_y = x1 - x0, y1 - y0
        length_squared = side_x * side_x + side_y * side_y
        if length_squared == 0:
            raise RuntimeError("a rectangle's first two points must differ")
        # The third corner is the third point moved along the first side until it lies
        # square to the second point; a third point drawn at that corner stays where it is.
        along = ((pointThree.x - x1) * side_x + (pointThree.y - y1) * side_y) / length_squared
        x2, y2 = pointThree.x - along * side_x, pointThree.y - along * side_y
        if (x2, y2) == (x1, y1):
            raise RuntimeError("a rectangle's third point must lie off its first side")
        return self._rectangle([(x0, y0), (x1, y1), (x2, y2), (x0 + x2 - x1, y0 + y2 - y1)])

    def _rectangle(self, corners: list[tuple[float, float]]) -> SketchLineList:
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
        self._area: float | None = None

    def areaProperties(self) -> AreaProperties:
        if self._area is None:
            self._area = fingerprint(self.face).area
        return AreaProperties(self._area)


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
        tool = Stack.prism([region], extrudeInput.profile.z, distance)
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
        tool = prisms.union([body.shape for body in tools])
        match FeatureOperations(combineInput.operation):
            case FeatureOperations.JoinFeatureOperation:
                result = prisms.union([target.shape, tool])
            case FeatureOperations.CutFeatureOperation:
                result = prisms.cut(target.shape, tool)
            case FeatureOperations.IntersectFeatureOperation:
                result = prisms.common(target.shape, tool)
            case operation:
                raise NotImplementedError(f"the stand-in cannot combine with {operation.name}")
        if result.is_empty:
            raise RuntimeError("the combine leaves nothing of its target body")
        target.shape = result
        if not combineInput.isKeepToolBodies:
            for body in tools:
                body.parentComponent.remove_body(body)
        feature = CombineFeature([target])
        self._items.append(feature)
        return feature


class CopyPasteBody:
    def __init__(self, bodies: Iterable[BRepBody]) -> None:
        self.bodies = BRepBodies(bodies)


class CopyPasteBodies(_Collection[CopyPasteBody]):
    def __init__(self, component: Component) -> None:
        super().__init__()
        self._component = component

    def add(self, sourceBodies: BRepBody | core.ObjectCollection) -> CopyPasteBody:
        """A copy of each of `sourceBodies` in this collection's component."""
        sources = [sourceBodies] if isinstance(sourceBodies, BRepBody) else list(sourceBodies)
        copies: list[BRepBody] = []
        for body in sources:
            if not isinstance(body, BRepBody) or not body.isValid:
                raise RuntimeError("a copy-paste copies bodies that exist")
            # A stack never changes, so the copy can share it.
            copies.append(self._component.add_body(body.shape))
        if not copies:
            raise RuntimeError("a copy-paste needs at least one body")
        feature = CopyPasteBody(copies)
        self._items.append(feature)
        return feature


class SplitBodyFeatureInput:
    def __init__(
        self, splitBodies: BRepBody, splittingTool: ConstructionPlane, isSplittingToolExtended: bool
    ) -> None:
        self.splitBodies = splitBodies
        self.splittingTool = splittingTool
        self.isSplittingToolExtended = isSplittingToolExtended


class SplitBodyFeature:
    def __init__(self, bodies: Iterable[BRepBody]) -> None:
        self.bodies = BRepBodies(bodies)


class SplitBodyFeatures(_Collection[SplitBodyFeature]):
    def createInput(
        self,
        splitBodies: object,
        splittingTool: object,
        isSplittingToolExtended: bool,
    ) -> SplitBodyFeatureInput:
        if not isinstance(splitBodies, BRepBody) or not isinstance(
            splittingTool, ConstructionPlane
        ):
            raise NotImplementedError("the stand-in splits one body by a construction plane")
        return SplitBodyFeatureInput(splitBodies, splittingTool, isSplittingToolExtended)

    def add(self, splitBodyInput: SplitBodyFeatureInput) -> SplitBodyFeature:
        """Split the body at the plane's height: the lower piece, then the upper piece."""
        body, z = splitBodyInput.splitBodies, splitBodyInput.splittingTool.z
        lower, upper = prisms.split(body.shape, z)
        if lower.is_empty or upper.is_empty:
            raise RuntimeError("the splitting plane does not cross the body")
        component = body.parentComponent
        component.remove_body(body)
        feature = SplitBodyFeature([component.add_body(lower), component.add_body(upper)])
        self._items.append(feature)
        return feature


class Features:
    def __init__(self, component: Component) -> None:
        self.extrudeFeatures = ExtrudeFeatures(component)
        self.combineFeatures = CombineFeatures()
        self.copyPasteBodies = CopyPasteBodies(component)
        self.splitBodyFeatures = SplitBodyFeatures()


def _apply(component: Component, tool: Stack, operation: FeatureOperations) -> list[BRepBody]:
    """Apply an extruded `tool` made by a feature of `component`; the bodies it made or changed."""
    match operation:
        case FeatureOperations.NewBodyFeatureOperation:
            return [component.add_body(tool)]
        case FeatureOperations.NewComponentFeatureOperation:
            raise NotImplementedError("the stand-in cannot extrude into a new component")
        case _:
            pass
    if operation is FeatureOperations.JoinFeatureOperation:
        reached = [body for body in component.bRepBodies if _overlaps(body.shape, tool)]
        if not reached:
            return [component.add_body(tool)]
        first, *rest = reached
        first.shape = prisms.union([first.shape, tool, *(body.shape for body in rest)])
        for body in rest:
            body.parentComponent.remove_body(body)
        return [first]
    reached = [body for body in component.top_level().all_bodies() if _overlaps(body.shape, tool)]
    if not reached:
        raise RuntimeError(NO_TARGET)
    for body in reached:
        if operation is FeatureOperations.CutFeatureOperation:
            left = prisms.cut(body.shape, tool)
        else:
            left = prisms.common(body.shape, tool)
        if not left.is_empty:
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


def _overlaps(body: Stack, tool: Stack) -> bool:
    """Whether `body` and `tool` share volume; stacks that only touch do not."""
    (a_low, a_high), (b_low, b_high) = body.bounds, tool.bounds
    if any(a_high[i] < b_low[i] or b_high[i] < a_low[i] for i in range(3)):
        return False
    return not prisms.common(body, tool).is_empty


def _on_the_sketch(point: core.Point3D) -> None:
    if point.z != 0:
        raise NotImplementedError("the stand-in draws only in the sketch's own plane, at z = 0")
