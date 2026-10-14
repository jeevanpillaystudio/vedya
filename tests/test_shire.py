"""Shire builds what the Fusion 360 script built at a36cc3c, part by part."""

import math

import pytest

from references import differences
from tools.legacy import golden
from vedya.designs.shire import PART_NAMES, ShireParams, build
from vedya.model import Model, fingerprint


@pytest.fixture(scope="module")
def model() -> Model:
    return build(ShireParams())


def test_the_parts_are_built_in_the_scripts_order(model: Model) -> None:
    expected = golden.read("shire")
    assert list(model.parts) == list(PART_NAMES)
    # Every part built is one of the script's, in the order the script built them.
    order = list(expected.parts)
    assert [order.index(name) for name in model.parts] == sorted(
        order.index(name) for name in model.parts
    )


@pytest.mark.parametrize("name", PART_NAMES)
def test_each_part_matches_the_golden_from_the_fusion_script(model: Model, name: str) -> None:
    expected = golden.read("shire").parts[name]
    assert not differences(fingerprint(model.parts[name]), expected)


def test_the_bg_is_the_board_two_layers_deep(model: Model) -> None:
    fp = fingerprint(model.parts["bg"])
    assert fp.volume == pytest.approx(640.0 * 960.0 * 9.6, rel=1e-12)
    assert fp.bbox_min == pytest.approx((-320.0, -480.0, 0.0), abs=1e-9)
    assert fp.bbox_max == pytest.approx((320.0, 480.0, 9.6), abs=1e-9)


def test_the_border_stands_inside_the_board_on_the_bg(model: Model) -> None:
    fp = fingerprint(model.parts["border"])
    inside = 640.0 * 960.0 - (640.0 - 2 * 19.2) * (960.0 - 2 * 19.2)
    assert fp.volume == pytest.approx(inside * 28.8, rel=1e-12)
    assert fp.bbox_min == pytest.approx((-320.0, -480.0, 9.6), abs=1e-9)
    assert fp.bbox_max == pytest.approx((320.0, 480.0, 38.4), abs=1e-9)


def test_the_middle_ring_is_a_wall_outside_the_hole(model: Model) -> None:
    fp = fingerprint(model.parts["middle-ring"])
    assert fp.volume == pytest.approx(math.pi * (64.8**2 - 57.6**2) * 28.8, rel=1e-12)
    assert fp.bbox_min == pytest.approx((-64.8, -64.8, 4.8), abs=1e-9)
    assert fp.bbox_max == pytest.approx((64.8, 64.8, 33.6), abs=1e-9)


@pytest.mark.parametrize(
    ("params", "message"),
    [
        (ShireParams(layer=0.0), "height must be positive"),
        (ShireParams(border_width=400.0), "cannot be offset"),
        (ShireParams(astroids=(294.4, 7.0)), "radius must be positive"),
    ],
)
def test_impossible_parameters_are_refused(params: ShireParams, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        build(params)
