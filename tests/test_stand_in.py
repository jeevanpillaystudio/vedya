"""The stand-in for Fusion's API keeps the contract `tools/legacy/adsk/fusion.py` states.

Every length here is in centimetres, as the stand-in takes them.
"""

import math
import sys

import build123d as bd
import pytest

from tools.legacy import adsk
from tools.legacy.adsk import core, fusion
from vedya.geometry import astroid
from vedya.model import fingerprint

Op = fusion.FeatureOperations
Side = fusion.ThinExtrudeWallLocation


def component(parent: fusion.Component, name: str) -> fusion.Component:
    made = parent.occurrences.addNewComponent(core.Matrix3D.create()).component
    made.name = name
    return made


def sketch(owner: fusion.Component, z: float = 0.0) -> fusion.Sketch:
    planes = owner.constructionPlanes
    plane_input = planes.createInput()
    plane_input.setByOffset(owner.xYConstructionPlane, core.ValueInput.createByReal(z))
    return owner.sketches.add(planes.add(plane_input))


def circle(
    owner: fusion.Component, radius: float, at: tuple[float, float] = (0.0, 0.0), z: float = 0.0
) -> fusion.Profile:
    drawn = sketch(owner, z)
    drawn.sketchCurves.sketchCircles.addByCenterRadius(core.Point3D.create(*at, 0.0), radius)
    (profile,) = drawn.profiles
    return profile


def extrude(
    owner: fusion.Component,
    profile: fusion.Profile,
    height: float,
    operation: fusion.FeatureOperations = Op.NewBodyFeatureOperation,
    wall: tuple[fusion.ThinExtrudeWallLocation, float] | None = None,
) -> fusion.ExtrudeFeature:
    features = owner.features.extrudeFeatures
    extrude_input = features.createInput(profile, operation)
    extrude_input.setDistanceExtent(False, core.ValueInput.createByReal(height))
    if wall is not None:
        extrude_input.setThinExtrude(wall[0], core.ValueInput.createByReal(wall[1]))
    return features.add(extrude_input)


def disc(
    owner: fusion.Component, radius: float = 1.0, at: tuple[float, float] = (0.0, 0.0)
) -> None:
    """A body in `owner`: a disc of `radius` at `at`, from z 0 to 1."""
    extrude(owner, circle(owner, radius, at), 1.0)


def volume(owner: fusion.Component) -> float:
    return sum(body.shape.fingerprint().volume for body in owner.bRepBodies)


@pytest.fixture
def root() -> fusion.Component:
    return adsk.new_document().rootComponent


def test_profiles_are_the_closed_regions_with_their_inner_loops(root: fusion.Component) -> None:
    drawn = sketch(root)
    corners = core.Point3D.create(-1.6, -1.6, 0.0), core.Point3D.create(1.6, 1.6, 0.0)
    drawn.sketchCurves.sketchLines.addTwoPointRectangle(*corners)
    drawn.sketchCurves.sketchCircles.addByCenterRadius(core.Point3D.create(), 0.31)
    hole = math.pi * 0.31**2
    by_area = sorted(drawn.profiles, key=lambda profile: profile.areaProperties().area)
    assert [p.areaProperties().area for p in by_area] == pytest.approx(
        [hole, 3.2**2 - hole], rel=1e-12
    )
    assert [len(p.face.inner_wires()) for p in by_area] == [0, 1]


def test_overlapping_circles_bound_three_regions(root: fusion.Component) -> None:
    drawn = sketch(root)
    for x in (0.0, 1.0):
        drawn.sketchCurves.sketchCircles.addByCenterRadius(core.Point3D.create(x, 0.0, 0.0), 1.0)
    lens = 2 * math.acos(0.5) - 0.5 * math.sqrt(3)  # two unit circles a radius apart
    areas = sorted(p.areaProperties().area for p in drawn.profiles)
    assert areas == pytest.approx([lens, math.pi - lens, math.pi - lens], rel=1e-9)


def test_a_new_body_rises_from_its_sketch_plane(root: fusion.Component) -> None:
    feature = extrude(root, circle(root, 0.31, z=-0.25), 0.15)
    fp = feature.bodies.item(0).shape.fingerprint()
    assert fp.volume == pytest.approx(math.pi * 0.31**2 * 0.15, rel=1e-12)
    assert fp.bbox_min == pytest.approx((-0.31, -0.31, -0.25), abs=1e-12)
    assert fp.bbox_max == pytest.approx((0.31, 0.31, -0.1), abs=1e-12)


@pytest.mark.parametrize(
    ("side", "inner", "outer"),
    [(Side.Side1, 0.8, 1.0), (Side.Side2, 1.0, 1.2), (Side.Center, 0.9, 1.1)],
)
def test_a_thin_wall_grows_inside_on_side1_and_outside_on_side2(
    root: fusion.Component, side: fusion.ThinExtrudeWallLocation, inner: float, outer: float
) -> None:
    feature = extrude(root, circle(root, 1.0), 1.0, wall=(side, 0.2))
    fp = feature.bodies.item(0).shape.fingerprint()
    assert fp.volume == pytest.approx(math.pi * (outer**2 - inner**2), rel=1e-12)
    assert fp.bbox_max == pytest.approx((outer, outer, 1.0), abs=1e-9)


def test_a_thin_wall_keeps_a_rectangles_corners_sharp(root: fusion.Component) -> None:
    drawn = sketch(root)
    corners = core.Point3D.create(-1.0, -0.5, 0.0), core.Point3D.create(1.0, 0.5, 0.0)
    drawn.sketchCurves.sketchLines.addTwoPointRectangle(*corners)
    feature = extrude(root, drawn.profiles.item(0), 1.0, wall=(Side.Side1, 0.1))
    fp = feature.bodies.item(0).shape.fingerprint()
    assert fp.volume == pytest.approx(2.0 * 1.0 - 1.8 * 0.8, rel=1e-12)


def test_a_cut_reaches_its_component_and_those_inside_it(root: fusion.Component) -> None:
    parent = component(root, "parent")
    own = component(parent, "own")
    nested = component(own, "nested")
    sibling = component(parent, "sibling")
    for holder in (parent, own, nested, sibling):
        disc(holder)
    extrude(own, circle(own, 0.5), 1.0, Op.CutFeatureOperation)
    whole, cut = math.pi, math.pi * (1.0 - 0.25)
    assert [volume(c) for c in (parent, own, nested, sibling)] == pytest.approx(
        [whole, cut, cut, whole], rel=1e-12
    )


def test_an_intersect_leaves_a_body_it_misses_whole(root: fusion.Component) -> None:
    own = component(root, "own")
    disc(own)
    disc(own, at=(5.0, 0.0))
    sibling = component(root, "sibling")
    disc(sibling)
    extrude(own, circle(own, 0.5), 1.0, Op.IntersectFeatureOperation)
    assert sorted(body.shape.fingerprint().volume for body in own.bRepBodies) == pytest.approx(
        [math.pi * 0.25, math.pi], rel=1e-12
    )
    assert volume(sibling) == pytest.approx(math.pi, rel=1e-12)


@pytest.mark.parametrize("operation", [Op.CutFeatureOperation, Op.IntersectFeatureOperation])
def test_a_cut_or_intersect_that_reaches_nothing_raises(
    root: fusion.Component, operation: fusion.FeatureOperations
) -> None:
    disc(component(root, "sibling"))
    empty = component(root, "empty")
    with pytest.raises(RuntimeError) as raised:
        extrude(empty, circle(empty, 0.5), 1.0, operation)
    assert str(raised.value) == "No target body found to cut or intersect!"


def test_a_join_that_reaches_nothing_makes_a_new_body(root: fusion.Component) -> None:
    sibling = component(root, "sibling")
    disc(sibling)
    empty = component(root, "empty")
    extrude(empty, circle(empty, 0.5), 1.0, Op.JoinFeatureOperation)
    assert empty.bRepBodies.count == 1
    assert volume(empty) == pytest.approx(math.pi * 0.25, rel=1e-12)
    assert volume(sibling) == pytest.approx(math.pi, rel=1e-12)


def test_a_join_merges_what_it_reaches_into_one_body(root: fusion.Component) -> None:
    disc(root)
    disc(root, at=(2.5, 0.0))  # half a centimetre apart; the join bridges them
    extrude(root, circle(root, 0.5, at=(1.25, 0.0)), 1.0, Op.JoinFeatureOperation)
    assert root.bRepBodies.count == 1
    # One band, whose section is one face: the three discs are one solid.
    (band,) = root.bRepBodies.item(0).shape.bands
    assert len(band.region) == 1


def test_a_combine_changes_its_target_and_deletes_its_tools(root: fusion.Component) -> None:
    disc(root)
    inner = component(root, "inner")
    extrude(inner, circle(inner, 0.5), 1.0)
    target, tool = root.bRepBodies.item(0), inner.bRepBodies.item(0)
    tools = core.ObjectCollection.create()
    tools.add(tool)
    combine_input = root.features.combineFeatures.createInput(target, tools)
    combine_input.operation = Op.CutFeatureOperation
    combine_input.isKeepToolBodies = False
    root.features.combineFeatures.add(combine_input)
    assert volume(root) == pytest.approx(math.pi * 0.75, rel=1e-12)
    assert inner.bRepBodies.count == 0
    assert not tool.isValid


def test_a_message_box_is_recorded() -> None:
    adsk.new_document()
    ui = core.Application.get().userInterface
    ui.messageBox("Failed:\nTraceback")
    assert ui.messages == ["Failed:\nTraceback"]
    adsk.new_document()
    assert core.Application.get().userInterface.messages == []


def test_installed_is_the_adsk_package_only_while_the_block_runs() -> None:
    assert "adsk" not in sys.modules
    with adsk.installed():
        import adsk.fusion as installed_fusion  # pyright: ignore[reportMissingImports]

        assert installed_fusion is fusion
    assert "adsk" not in sys.modules
    assert "adsk.fusion" not in sys.modules


def test_a_three_point_rectangle_drawn_as_the_scripts_draw_it_is_a_diamond(
    root: fusion.Component,
) -> None:
    drawn = sketch(root)
    w = 3.1
    points = (
        core.Point3D.create(-w, 0, 0),
        core.Point3D.create(0, w, 0),
        core.Point3D.create(w, 0),
    )
    lines = drawn.sketchCurves.sketchLines.addThreePointRectangle(*points)
    assert {line.start for line in lines} == {(-w, 0.0), (0.0, w), (w, 0.0), (0.0, -w)}
    (profile,) = drawn.profiles
    assert profile.areaProperties().area == pytest.approx(2 * w**2, rel=1e-12)


@pytest.mark.parametrize(
    ("third", "low_y", "high_y"), [((5.0, 1.0), 0.0, 1.0), ((-3.0, -1.0), -1.0, 0.0)]
)
def test_a_three_point_rectangle_is_as_tall_as_the_third_point_lies_from_its_first_side(
    root: fusion.Component, third: tuple[float, float], low_y: float, high_y: float
) -> None:
    drawn = sketch(root)
    first, second = core.Point3D.create(0, 0, 0), core.Point3D.create(2, 0, 0)
    drawn.sketchCurves.sketchLines.addThreePointRectangle(
        first, second, core.Point3D.create(*third, 0.0)
    )
    (profile,) = drawn.profiles
    box = profile.face.bounding_box()
    corners = (box.min.X, box.min.Y, box.max.X, box.max.Y)
    assert corners == pytest.approx((0, low_y, 2, high_y))


def test_a_three_point_rectangle_needs_a_third_point_off_its_first_side(
    root: fusion.Component,
) -> None:
    on_the_side = (
        core.Point3D.create(0, 0, 0),
        core.Point3D.create(2, 0, 0),
        core.Point3D.create(5),
    )
    with pytest.raises(RuntimeError, match="off its first side"):
        sketch(root).sketchCurves.sketchLines.addThreePointRectangle(*on_the_side)


def fit_points(radius: float, count: int) -> core.ObjectCollection:
    """`count` + 1 points around a circle of `radius`, the last where the first is."""
    points = core.ObjectCollection.create()
    for i in range(count + 1):
        angle = 2 * math.pi * i / count
        points.add(core.Point3D.create(radius * math.cos(angle), radius * math.sin(angle), 0.0))
    return points


def test_a_fitted_spline_whose_ends_meet_bounds_a_region(root: fusion.Component) -> None:
    drawn = sketch(root)
    drawn.sketchCurves.sketchFittedSplines.add(fit_points(1.0, 64))
    (profile,) = drawn.profiles
    assert profile.areaProperties().area == pytest.approx(math.pi, rel=1e-6)
    (outline,) = profile.face.edges()
    for point in fit_points(1.0, 64):
        assert isinstance(point, core.Point3D)
        assert outline.distance_to(bd.Vector(point.x, point.y, 0.0)) < 1e-12


def test_the_stand_in_fits_an_astroid_as_vedya_does(root: fusion.Component) -> None:
    # The points a36cc3c's draw_astroid fits, in centimetres, with N = 2/3.
    radius, points = 29.44, core.ObjectCollection.create()
    for i in range(129):
        angle = i * 2 * math.pi / 128
        x = pow(abs(math.cos(angle)), 2 / (2 / 3)) * math.copysign(1, math.cos(angle)) * radius
        y = pow(abs(math.sin(angle)), 2 / (2 / 3)) * math.copysign(1, math.sin(angle)) * radius
        points.add(core.Point3D.create(x, y, 0))
    drawn = sketch(root)
    drawn.sketchCurves.sketchFittedSplines.add(points)
    (profile,) = drawn.profiles
    in_mm = fingerprint(astroid(radius * 10)).area
    assert profile.areaProperties().area * 100 == pytest.approx(in_mm, rel=1e-12)


def test_profiles_and_collections_are_indexed(root: fusion.Component) -> None:
    profile = circle(root, 1.0)
    assert profile.face is not None
    drawn = sketch(root)
    drawn.sketchCurves.sketchCircles.addByCenterRadius(core.Point3D.create(), 1.0)
    assert drawn.profiles[0] is drawn.profiles.item(0)
    items = core.ObjectCollection.create()
    for item in ("a", "b", "c"):
        items.add(item)
    items.removeByIndex(0)
    assert (items.count, items[0], items.item(1)) == (2, "b", "c")


def test_an_occurrence_is_named_after_its_component(root: fusion.Component) -> None:
    occurrence = root.occurrences.addNewComponent(core.Matrix3D.create())
    occurrence.component.name = "cnc_mill-bg"
    assert root.occurrences.itemByName("cnc_mill-bg:1") is occurrence
    assert root.occurrences.itemByName("cnc_mill-bg") is None
    occurrence.component.name = "renamed"
    assert root.occurrences.itemByName("renamed:1") is occurrence


def test_a_copy_paste_copies_into_the_component_that_made_it(root: fusion.Component) -> None:
    inner = component(root, "inner")
    disc(inner)
    original = inner.bRepBodies.item(0)
    copied = root.features.copyPasteBodies.add(original).bodies.item(0)
    assert copied.parentComponent is root
    assert inner.bRepBodies.count == 1
    # The copy is a body of its own: cutting the original leaves it whole.
    extrude(inner, circle(inner, 0.5), 1.0, Op.CutFeatureOperation)
    assert copied.shape.fingerprint().volume == pytest.approx(math.pi, rel=1e-12)
    assert volume(inner) == pytest.approx(math.pi * 0.75, rel=1e-12)


def test_a_combine_reaches_its_target_in_another_component(root: fusion.Component) -> None:
    # As a36cc3c's aggregator: copies in the root, joined by a combine of another component.
    disc(root)
    disc(root, at=(1.5, 0.0))
    aggregator = component(root, "aggregator")
    target, tool = root.bRepBodies.item(0), root.bRepBodies.item(1)
    tools = core.ObjectCollection.create()
    tools.add(tool)
    aggregator.features.combineFeatures.add(
        aggregator.features.combineFeatures.createInput(target, tools)
    )
    assert root.bRepBodies.count == 1
    assert aggregator.bRepBodies.count == 0
    lens = 2 * math.acos(0.75) - 1.5 * math.sqrt(1 - 0.75**2)  # two unit discs 1.5 apart
    assert volume(root) == pytest.approx(2 * math.pi - lens, rel=1e-9)


def test_a_split_lists_the_lower_piece_first(root: fusion.Component) -> None:
    disc(root)
    body = root.bRepBodies.item(0)
    assert (body.boundingBox.minPoint.z, body.boundingBox.maxPoint.z) == (0.0, 1.0)
    planes = root.constructionPlanes
    plane_input = planes.createInput()
    plane_input.setByOffset(root.xYConstructionPlane, core.ValueInput.createByReal(0.25))
    splits = root.features.splitBodyFeatures
    lower, upper = splits.add(splits.createInput(body, planes.add(plane_input), True)).bodies
    assert lower.shape.fingerprint().volume == pytest.approx(math.pi * 0.25, rel=1e-12)
    assert upper.shape.fingerprint().volume == pytest.approx(math.pi * 0.75, rel=1e-12)
    assert not body.isValid
    assert [b.name for b in root.bRepBodies] == [lower.name, upper.name]


def test_a_split_by_a_plane_that_misses_the_body_raises(root: fusion.Component) -> None:
    disc(root)
    planes = root.constructionPlanes
    plane_input = planes.createInput()
    plane_input.setByOffset(root.xYConstructionPlane, core.ValueInput.createByReal(2.0))
    splits = root.features.splitBodyFeatures
    with pytest.raises(RuntimeError, match="does not cross"):
        splits.add(splits.createInput(root.bRepBodies.item(0), planes.add(plane_input), True))
