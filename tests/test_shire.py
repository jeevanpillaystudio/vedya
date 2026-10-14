"""Shire builds what the Fusion 360 script built at a36cc3c, part by part and as a whole."""

import math

import build123d as bd
import pytest

from references import differences
from tools.legacy import golden
from vedya.designs.shire import PART_NAMES, SeedPass, ShireParams, build, seed_layer
from vedya.geometry import Region, circle
from vedya.model import Model, fingerprint
from vedya.patterns import seed_of_life


def test_every_part_of_the_script_is_built_in_its_order(shire: Model) -> None:
    assert list(shire.parts) == list(PART_NAMES) == list(golden.read("shire").parts)


@pytest.mark.parametrize("name", PART_NAMES)
def test_each_part_matches_the_golden_from_the_fusion_script(shire: Model, name: str) -> None:
    expected = golden.read("shire").parts[name]
    assert not differences(fingerprint(shire.parts[name]), expected)


def test_the_aggregate_is_the_aggregators_one_body(shire_aggregate: bd.Part) -> None:
    expected = golden.read("shire").aggregate
    assert expected is not None
    assert shire_aggregate.is_valid
    assert len(shire_aggregate.solids()) == 1
    assert not differences(fingerprint(shire_aggregate), expected)


def test_the_bg_is_the_board_two_layers_deep(shire: Model) -> None:
    fp = fingerprint(shire.parts["bg"])
    assert fp.volume == pytest.approx(640.0 * 960.0 * 9.6, rel=1e-12)
    assert fp.bbox_min == pytest.approx((-320.0, -480.0, 0.0), abs=1e-9)
    assert fp.bbox_max == pytest.approx((320.0, 480.0, 9.6), abs=1e-9)


def test_the_border_stands_inside_the_board_on_the_bg(shire: Model) -> None:
    fp = fingerprint(shire.parts["border"])
    inside = 640.0 * 960.0 - (640.0 - 2 * 19.2) * (960.0 - 2 * 19.2)
    assert fp.volume == pytest.approx(inside * 28.8, rel=1e-12)
    assert fp.bbox_min == pytest.approx((-320.0, -480.0, 9.6), abs=1e-9)
    assert fp.bbox_max == pytest.approx((320.0, 480.0, 38.4), abs=1e-9)


def test_the_middle_ring_is_a_wall_outside_the_hole(shire: Model) -> None:
    fp = fingerprint(shire.parts["middle-ring"])
    assert fp.volume == pytest.approx(math.pi * (64.8**2 - 57.6**2) * 28.8, rel=1e-12)
    assert fp.bbox_min == pytest.approx((-64.8, -64.8, 4.8), abs=1e-9)
    assert fp.bbox_max == pytest.approx((64.8, 64.8, 33.6), abs=1e-9)


def corners(part: bd.Part) -> tuple[float, ...]:
    box = part.bounding_box()
    return (box.min.X, box.min.Y, box.min.Z, box.max.X, box.max.Y, box.max.Z)


def test_layer_0_overhangs_the_long_sides_of_the_board(shire: Model) -> None:
    # Its circle of 360 mm is wider than the board's 640 mm, and nothing trims it.
    assert corners(shire.parts["layer-0"]) == pytest.approx(
        (-360.0, -360.0, 19.2, 360.0, 360.0, 28.8), abs=1e-6
    )


def test_layer_2_is_trimmed_to_the_board_and_reaches_the_top(shire: Model) -> None:
    assert corners(shire.parts["layer-2"]) == pytest.approx(
        (-320.0, -480.0, 19.2, 320.0, 480.0, 38.4), abs=1e-6
    )


def test_layer_1_lies_between_the_outer_and_middle_diamonds(shire: Model) -> None:
    layer = shire.parts["layer-1"]
    assert corners(layer) == pytest.approx((-310.0, -310.0, 9.6, 310.0, 310.0, 28.8), abs=1e-6)
    # No point of it is inside the middle diamond, |x| + |y| < 240.
    inside = bd.Pos(0, 0, 9.6) * bd.extrude(
        bd.Polygon((239, 0), (0, 239), (-239, 0), (0, -239), align=None), amount=19.2
    )
    assert not (layer & inside).solids()


# Each is refused by the first part that uses it, before the slow parts are built. An
# astroid too small for its wall is refused by `astroid` itself (test_geometry), and only
# after the three layers, so it is not built here again.
def test_a_later_step_cuts_back_an_earlier_slab_to_its_own_heights() -> None:
    # The earlier pass's slabs stand from 0 to 1, 1 to 2 and 2 to 3 mm; the later pass's
    # one step from 0 to 1.5 mm. The first earlier slab lies within the step and stays
    # whole, the second straddles its top and keeps only 1 to 1.5 mm, and the third lies
    # wholly above it and stays whole: nothing stands from 1.5 to 2 mm.
    earlier, later = SeedPass(20.0, 1.0, 3.0, 3), SeedPass(30.0, 1.0, 1.5, 1)
    layer = seed_layer(circle(60.0), 0.0, (earlier, later))

    def carved(radius: float, stroke: float) -> Region:
        return circle(60.0) - seed_of_life(radius, stroke)

    def area(*regions: Region) -> float:
        """The area of the union of `regions`."""
        first, *rest = regions
        return fingerprint(bd.Sketch((first + rest).faces())).area

    expected = (
        area(carved(20.0, 1.0), carved(30.0, 1.0)) * 1.0
        + area(carved(20.0, 2.0), carved(30.0, 1.0)) * 0.5
        + area(carved(20.0, 3.0)) * 1.0
    )
    assert fingerprint(layer).volume == pytest.approx(expected, rel=1e-9)
    top = layer.bounding_box().max.Z
    assert top == pytest.approx(3.0, abs=1e-9)


@pytest.mark.parametrize(
    ("params", "message"),
    [
        (ShireParams(layer=0.0), "height must be positive"),
        (ShireParams(border_width=400.0), "cannot be offset"),
        (ShireParams(layer_0=()), "at least one pass"),
        (ShireParams(layer_0=(SeedPass(200, 450, 9.6, 4),)), "cannot be offset"),
        (ShireParams(layer_0=(SeedPass(200, 9.6, 9.6, 0),)), "at least one step"),
    ],
)
def test_impossible_parameters_are_refused(params: ShireParams, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        build(params)
