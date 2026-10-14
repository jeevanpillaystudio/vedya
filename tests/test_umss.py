"""UMSS builds what the Fusion 360 script built, and milestone 1 matches its STL files."""

import math

import numpy as np
import pytest

from references import MEASURED_EXCESS, differences, milestone_1_stl
from stl_mesh import mesh_bounds, mesh_volume, read_stl
from tools.legacy import golden
from vedya.designs.umss import UmssParams, build
from vedya.model import fingerprint


def test_the_default_matches_the_golden_from_the_fusion_script() -> None:
    expected = golden.read("umss")
    model = build(UmssParams())
    assert list(model.parts) == list(expected.parts)
    for name, part in model.parts.items():
        assert not differences(fingerprint(part), expected.parts[name]), name


def test_the_default_is_the_magnet_base_disc() -> None:
    model = build(UmssParams())
    assert list(model.parts) == ["magnet-base"]
    fp = fingerprint(model.parts["magnet-base"])
    assert fp.volume == pytest.approx(math.pi * 3.1**2 * 1.5, rel=1e-9)
    assert fp.bbox_min == pytest.approx((-3.1, -3.1, -2.5), abs=1e-9)
    assert fp.bbox_max == pytest.approx((3.1, 3.1, -1.0), abs=1e-9)
    assert fp.centroid == pytest.approx((0.0, 0.0, -1.75), abs=1e-9)


def test_the_tile_has_a_centred_through_hole() -> None:
    fp = fingerprint(build(UmssParams(parts=("tile",), hole_radius=3.0)).parts["tile"])
    assert fp.volume == pytest.approx((32.0 * 32.0 - math.pi * 3.0**2) * 3.0, rel=1e-9)
    assert fp.bbox_min == pytest.approx((-16.0, -16.0, 0.0), abs=1e-9)
    assert fp.bbox_max == pytest.approx((16.0, 16.0, 3.0), abs=1e-9)


def test_the_base_ring_is_a_wall_outside_the_magnet_base() -> None:
    fp = fingerprint(build(UmssParams(parts=("base-ring",))).parts["base-ring"])
    assert fp.volume == pytest.approx(math.pi * (4.1**2 - 3.1**2) * 0.5, rel=1e-9)
    assert fp.bbox_min == pytest.approx((-4.1, -4.1, -0.5), abs=1e-9)
    assert fp.bbox_max == pytest.approx((4.1, 4.1, 0.0), abs=1e-9)


def test_parts_are_built_in_their_own_order() -> None:
    model = build(UmssParams(parts=("base-ring", "tile", "magnet-base")))
    assert list(model.parts) == ["tile", "magnet-base", "base-ring"]


@pytest.mark.parametrize(
    ("params", "message"),
    [
        (UmssParams(parts=("lid",)), "no part 'lid'"),
        (UmssParams(parts=()), "at least one"),
        (UmssParams(parts=("tile",), hole_radius=16.0), "does not fit"),
    ],
)
def test_impossible_parameters_are_refused(params: UmssParams, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        build(params)


@pytest.mark.parametrize("hole_radius", [3.0, 3.1, 3.2, 3.3, 3.4, 3.5])
def test_milestone_1_tile_matches_fusions_stl(hole_radius: float) -> None:
    tile = build(UmssParams(parts=("tile",), hole_radius=hole_radius)).parts["tile"]
    exact = fingerprint(tile)
    triangles = read_stl(milestone_1_stl(hole_radius))
    low_excess, high_excess = MEASURED_EXCESS
    assert low_excess <= mesh_volume(triangles) - exact.volume <= high_excess
    low, high = mesh_bounds(triangles)
    np.testing.assert_allclose(low, exact.bbox_min, atol=1e-3)
    np.testing.assert_allclose(high, exact.bbox_max, atol=1e-3)
