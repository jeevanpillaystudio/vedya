"""The stand-in for Fusion's API keeps the contract `tools/legacy/adsk/fusion.py` states.

Every length here is in centimetres, as the stand-in takes them.
"""

import math
import sys

import pytest

from tools.legacy import adsk
from tools.legacy.adsk import core, fusion
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
    return sum(fingerprint(body.shape).volume for body in owner.bRepBodies)


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
    fp = fingerprint(feature.bodies.item(0).shape)
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
    fp = fingerprint(feature.bodies.item(0).shape)
    assert fp.volume == pytest.approx(math.pi * (outer**2 - inner**2), rel=1e-12)
    assert fp.bbox_max == pytest.approx((outer, outer, 1.0), abs=1e-9)


def test_a_thin_wall_keeps_a_rectangles_corners_sharp(root: fusion.Component) -> None:
    drawn = sketch(root)
    corners = core.Point3D.create(-1.0, -0.5, 0.0), core.Point3D.create(1.0, 0.5, 0.0)
    drawn.sketchCurves.sketchLines.addTwoPointRectangle(*corners)
    feature = extrude(root, drawn.profiles.item(0), 1.0, wall=(Side.Side1, 0.1))
    fp = fingerprint(feature.bodies.item(0).shape)
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
    assert sorted(fingerprint(body.shape).volume for body in own.bRepBodies) == pytest.approx(
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
    assert len(root.bRepBodies.item(0).shape.solids()) == 1


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
