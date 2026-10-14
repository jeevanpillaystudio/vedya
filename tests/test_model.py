"""Models, the union and aggregate of parts, layers sliced from a part, and the
fingerprint of a known solid."""

import itertools
import math

import build123d as bd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# OCP is compiled and ships no type stubs, so its names are invisible to the type checker.
from OCP.BRep import BRep_Tool  # pyright: ignore[reportAttributeAccessIssue]

from references import CLEAN, largest_tolerance
from vedya.geometry import Align, Region, astroid, circle, rectangle, slab, stroke
from vedya.model import Model, aggregate, fingerprint, slice_layers, union


def box(x: float, y: float, z: float, at: tuple[float, float, float] = (0.0, 0.0, 0.0)) -> bd.Part:
    """A box of the given size whose low corner is at `at`."""
    return bd.Pos(*at) * bd.Box(x, y, z, align=bd.Align.MIN)


def test_fingerprint_of_a_known_box() -> None:
    fp = fingerprint(box(10.0, 20.0, 30.0, at=(1.0, 2.0, 3.0)))
    assert fp.volume == pytest.approx(10.0 * 20.0 * 30.0, rel=1e-12)
    assert fp.area == pytest.approx(2 * (10.0 * 20.0 + 20.0 * 30.0 + 10.0 * 30.0), rel=1e-12)
    assert fp.bbox_min == (1.0, 2.0, 3.0)
    assert fp.bbox_max == (11.0, 22.0, 33.0)
    assert fp.centroid == pytest.approx((6.0, 12.0, 18.0), abs=1e-12)


def test_fingerprint_of_a_cylinder() -> None:
    fp = fingerprint(slab(circle(3.1), -2.5, 1.5))
    assert fp.volume == pytest.approx(math.pi * 3.1**2 * 1.5, rel=1e-12)
    assert fp.area == pytest.approx(2 * math.pi * 3.1**2 + 2 * math.pi * 3.1 * 1.5, rel=1e-12)
    assert fp.centroid == pytest.approx((0.0, 0.0, -1.75), abs=1e-12)


def test_a_flat_shape_has_no_volume_and_takes_its_area_centroid() -> None:
    fp = fingerprint(circle(1.0, at=(4.0, 0.0)) + circle(1.0, at=(-2.0, 0.0)))
    assert fp.volume == 0.0
    assert fp.area == pytest.approx(2 * math.pi, rel=1e-12)
    assert fp.centroid == pytest.approx((1.0, 0.0, 0.0), abs=1e-12)


def test_fingerprint_refuses_an_empty_shape() -> None:
    with pytest.raises(ValueError, match="empty"):
        fingerprint(bd.Part())


def test_model_keeps_its_parts_in_build_order() -> None:
    model = Model({"top": box(1, 1, 1), "base": box(1, 1, 1), "middle-ring": box(1, 1, 1)})
    assert list(model.parts) == ["top", "base", "middle-ring"]


def test_which_parts_a_model_holds_is_fixed_once_built() -> None:
    parts = {"base": box(1, 1, 1)}
    model = Model(parts)
    parts["late"] = box(1, 1, 1)
    assert list(model.parts) == ["base"]
    with pytest.raises(TypeError):
        model.parts["late"] = box(1, 1, 1)  # pyright: ignore[reportIndexIssue]


@pytest.mark.parametrize("name", ["", "Base", "middle ring", "layer_0", "-edge", "a/b"])
def test_part_names_are_lowercase_words_joined_by_hyphens(name: str) -> None:
    with pytest.raises(ValueError, match="part name"):
        Model({name: box(1, 1, 1)})


def test_model_needs_a_part() -> None:
    with pytest.raises(ValueError, match="at least one part"):
        Model({})


def test_aggregate_fuses_overlapping_parts() -> None:
    model = Model({"a": box(2, 2, 2), "b": box(2, 2, 2, at=(1.0, 0.0, 0.0))})
    union = aggregate(model)
    assert fingerprint(union).volume == pytest.approx(12.0, rel=1e-12)
    assert len(union.solids()) == 1


def test_aggregate_keeps_separate_parts_apart() -> None:
    model = Model({"a": box(1, 1, 1), "b": box(1, 1, 1, at=(5.0, 0.0, 0.0))})
    union = aggregate(model)
    assert isinstance(union, bd.Part)
    assert fingerprint(union).volume == pytest.approx(2.0, rel=1e-12)
    assert len(union.solids()) == 2


def test_aggregate_of_one_part_is_that_part() -> None:
    part = box(1, 2, 3)
    assert fingerprint(aggregate(Model({"only": part}))) == fingerprint(part)


def test_aggregate_leaves_the_parts_as_they_were_built() -> None:
    # A fuse of these keeps edges of both, which the clean after it may then rewrite.
    model = Model(
        {
            "board": slab(rectangle(10.0, 10.0), 0.0, 1.0),
            "ring": slab(stroke(circle(3.0), 1.0, Align.OUTSIDE), 1.0, 2.0),
        }
    )
    before = {name: fingerprint(part) for name, part in model.parts.items()}
    union = aggregate(model)
    assert fingerprint(union).volume == pytest.approx(100.0 + 2 * math.pi * 7.0, rel=1e-9)
    for name, part in model.parts.items():
        assert fingerprint(part) == before[name]
        assert not any(
            mine.wrapped.IsSame(theirs.wrapped)  # pyright: ignore[reportOptionalMemberAccess]
            for mine in part.edges()
            for theirs in union.edges()
        ), f"the union shares edges with {name}"
    assert fingerprint(aggregate(model)) == fingerprint(union)


def area(region: Region) -> float:
    faces = region.faces()
    return fingerprint(bd.Sketch(faces)).area if faces else 0.0


def test_aggregate_joins_a_cusp_that_lies_inside_another_part() -> None:
    # An astroid's cusps reach into a ring whose slab starts and ends within the
    # astroid's height. OpenCascade's 3D fuse of these two comes out 2.2 mm³ short.
    star = slab(astroid(287.2), 14.4, 9.6)
    ring = slab(circle(300.0) - circle(280.0), 19.2, 3.2)
    union = aggregate(Model({"star": star, "ring": ring}))
    shared = area(astroid(287.2) & (circle(300.0) - circle(280.0)))
    assert shared > 0
    expected = area(astroid(287.2)) * 9.6 + (area(circle(300.0) - circle(280.0)) - shared) * 3.2
    assert union.is_valid
    assert len(union.solids()) == 1
    assert fingerprint(union).volume == pytest.approx(expected, rel=1e-9)


def test_aggregate_joins_a_cusp_inside_a_stepped_part() -> None:
    # The same with the ring in two steps of different widths, one part as a layer is.
    # OpenCascade's 3D fuse of these drops a quarter of a million mm³.
    star = slab(astroid(287.2), 14.4, 9.6)
    lower, upper = circle(300.0) - circle(280.0), circle(300.0) - circle(282.0)
    steps = slab(lower, 16.8, 2.4) + slab(upper, 19.2, 3.2)
    stepped = steps if isinstance(steps, bd.Part) else bd.Part(steps.solids())
    union = aggregate(Model({"star": star, "steps": stepped}))
    disc = area(astroid(287.2))
    expected = (
        disc * 9.6
        + (area(lower) - area(astroid(287.2) & lower)) * 2.4
        + (area(upper) - area(astroid(287.2) & upper)) * 3.2
    )
    assert union.is_valid
    assert len(union.solids()) == 1
    assert fingerprint(union).volume == pytest.approx(expected, rel=1e-9)


def test_aggregate_joins_a_part_a_3d_fuse_left_approximate() -> None:
    # Fused in 3D, two astroids in steps, as Shire's core stacks them, share a curve that
    # OpenCascade approximates, leaving its edges 0.4 mm loose. Such a part is cut into
    # sections by planes, which miss about 2e-7 of an astroid's section at its cusps.
    steps = slab(astroid(300.0), 0.0, 4.0) + slab(astroid(290.0), 2.0, 4.0)
    stepped = steps if isinstance(steps, bd.Part) else bd.Part(steps.solids())
    assert max(BRep_Tool.Tolerance_s(edge.wrapped) for edge in stepped.edges()) > 0.1
    base = slab(rectangle(700.0, 700.0), -2.0, 2.0)
    union = aggregate(Model({"steps": stepped, "base": base}))
    expected = area(astroid(300.0)) * 4.0 + area(astroid(290.0)) * 2.0 + 700.0**2 * 2.0
    assert union.is_valid
    assert len(union.solids()) == 1
    assert fingerprint(union).volume == pytest.approx(expected, rel=1e-6)


def test_aggregate_fuses_parts_that_are_not_slabs_as_solids() -> None:
    ball = bd.Pos(0.0, 0.0, 1.0) * bd.Sphere(1.0)
    model = Model({"ball": ball, "base": box(4, 4, 1, at=(-2.0, -2.0, -0.5))})
    union = aggregate(model)
    # The ball's lower half-centimetre, a cap of height 0.5, lies in the base.
    cap = math.pi * 0.5**2 * (3 * 1.0 - 0.5) / 3
    assert fingerprint(union).volume == pytest.approx(4 / 3 * math.pi + 16.0 - cap, rel=1e-9)
    assert len(union.solids()) == 1


def test_a_union_needs_a_part() -> None:
    with pytest.raises(ValueError, match="at least one part"):
        union([])


def test_union_keeps_the_curves_a_3d_fuse_loosens() -> None:
    # The two astroids in steps whose 3D fuse leaves edges 0.4 mm loose, above.
    steps = union([slab(astroid(300.0), 0.0, 4.0), slab(astroid(290.0), 2.0, 4.0)])
    assert steps.is_valid
    assert largest_tolerance(steps) < 1e-6
    expected = area(astroid(300.0)) * 4.0 + area(astroid(290.0)) * 2.0
    assert fingerprint(steps).volume == pytest.approx(expected, rel=1e-9)


def test_union_leaves_its_parts_as_they_were() -> None:
    parts = [slab(rectangle(10.0, 10.0), 0.0, 1.0), slab(circle(3.0), 0.5, 2.0)]
    before = [fingerprint(part) for part in parts]
    union(parts)
    assert [fingerprint(part) for part in parts] == before


def heights(layers: list[bd.Part]) -> list[float]:
    """Each layer's lowest and highest z, layer after layer."""
    boxes = [layer.bounding_box() for layer in layers]
    return [z for box in boxes for z in (box.min.Z, box.max.Z)]


def flat(spans: list[tuple[float, float]]) -> list[float]:
    return [z for span in spans for z in span]


def test_a_10_mm_box_at_3_2_mm_is_three_layers_and_what_is_left() -> None:
    part = box(5.0, 4.0, 10.0, at=(0.0, 0.0, 1.0))
    layers = slice_layers(part, 3.2, 12)
    assert heights(layers) == pytest.approx(
        flat([(1.0, 4.2), (4.2, 7.4), (7.4, 10.6), (10.6, 11.0)]), abs=1e-9
    )
    assert [fingerprint(layer).volume for layer in layers] == pytest.approx(
        [64.0, 64.0, 64.0, 8.0], rel=1e-9
    )


def test_a_part_a_whole_number_of_layers_high_leaves_its_top_layer_last() -> None:
    layers = slice_layers(box(1.0, 1.0, 9.6), 3.2, 12)
    assert heights(layers) == pytest.approx(flat([(0.0, 3.2), (3.2, 6.4), (6.4, 9.6)]), abs=1e-9)


def test_the_count_limits_the_cuts_and_the_rest_is_left_whole() -> None:
    layers = slice_layers(box(1.0, 1.0, 10.0), 3.2, 2)
    assert heights(layers) == pytest.approx(flat([(0.0, 3.2), (3.2, 6.4), (6.4, 10.0)]), abs=1e-9)


def test_a_layer_higher_than_the_part_leaves_it_whole() -> None:
    (only,) = slice_layers(box(1.0, 2.0, 3.0), 5.0, 12)
    assert heights([only]) == pytest.approx([0.0, 3.0], abs=1e-9)
    assert fingerprint(only).volume == pytest.approx(6.0, rel=1e-12)


def test_layers_of_stacked_slabs_are_cut_band_by_band() -> None:
    # A disc on a board, cut through both; each layer holds what lies at its heights.
    part = union([slab(rectangle(10.0, 10.0), 0.0, 2.0), slab(circle(3.0), 2.0, 2.0)])
    layers = slice_layers(part, 1.5, 12)
    assert heights(layers) == pytest.approx(flat([(0.0, 1.5), (1.5, 3.0), (3.0, 4.0)]), abs=1e-9)
    disc = math.pi * 3.0**2
    expected = [150.0, 50.0 + disc, disc]
    assert [fingerprint(layer).volume for layer in layers] == pytest.approx(expected, rel=1e-9)
    for layer in layers:
        assert layer.is_valid
        assert largest_tolerance(layer) <= CLEAN


def test_a_layer_with_nothing_in_it_is_empty() -> None:
    part = union([slab(circle(1.0), 0.0, 1.0), slab(circle(1.0), 2.0, 1.0)])
    layers = slice_layers(part, 1.0, 12)
    assert [bool(layer.solids()) for layer in layers] == [True, False, True]


def test_a_part_that_is_not_a_stack_is_cut_by_a_boolean() -> None:
    ball = bd.Sphere(2.0)
    layers = slice_layers(ball, 1.0, 12)
    assert heights(layers) == pytest.approx(
        flat([(-2.0, -1.0), (-1.0, 0.0), (0.0, 1.0), (1.0, 2.0)]), abs=1e-6
    )
    # A cap of height h of a sphere of radius r holds πh²(3r - h)/3.
    cap, half = math.pi * 1.0 * (6.0 - 1.0) / 3, 2 / 3 * math.pi * 2.0**3
    expected = [cap, half - cap, half - cap, cap]
    # build123d's volume integrates a sphere's faces exactly, where the fingerprint's
    # adaptive rule takes seconds over them.
    assert [layer.volume for layer in layers] == pytest.approx(expected, rel=1e-12)
    for layer in layers:
        assert layer.is_valid


@pytest.mark.parametrize(
    ("height", "count", "message"),
    [(0.0, 12, "layer_height must be positive"), (3.2, 0, "max_count must be at least 1")],
)
def test_slicing_refuses_impossible_layers(height: float, count: int, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        slice_layers(box(1.0, 1.0, 1.0), height, count)


def test_slicing_refuses_an_empty_part() -> None:
    with pytest.raises(ValueError, match="empty"):
        slice_layers(bd.Part(), 1.0, 1)


@settings(max_examples=25, deadline=None)
@given(
    total=st.floats(min_value=0.5, max_value=40.0),
    layer=st.floats(min_value=0.3, max_value=8.0),
    count=st.integers(min_value=1, max_value=12),
)
def test_layers_stack_up_and_hold_the_whole(total: float, layer: float, count: int) -> None:
    part = box(2.0, 3.0, total)
    layers = slice_layers(part, layer, count)
    zs = heights(layers)
    spans = list(zip(zs[::2], zs[1::2], strict=True))
    assert spans[0][0] == pytest.approx(0.0, abs=1e-9)
    assert spans[-1][1] == pytest.approx(total, abs=1e-9)
    for (_, top), (bottom, _) in itertools.pairwise(spans):
        assert top == pytest.approx(bottom, abs=1e-9)
    # Every layer but the last is one layer high, and there are no more than `count` cuts.
    assert all(high - low == pytest.approx(layer, abs=1e-9) for low, high in spans[:-1])
    assert len(layers) - 1 <= count
    assert spans[-1][1] - spans[-1][0] <= layer + 1e-9 or len(layers) - 1 == count
    total_volume = sum(fingerprint(each).volume for each in layers)
    assert total_volume == pytest.approx(6.0 * total, rel=1e-9)
