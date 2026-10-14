"""Stacks of prisms: their booleans and fingerprints agree with solids that OpenCascade
builds reliably, such as boxes and cylinders."""

import math

import build123d as bd
import pytest

from references import differences
from tools.legacy import prisms
from tools.legacy.prisms import Stack
from vedya.geometry import astroid, circle, rectangle, slab
from vedya.model import Fingerprint, fingerprint


def prism(region: bd.Sketch, z: float, height: float) -> Stack:
    return Stack.prism(region.faces(), z, height)


def box(x: float, y: float, z: float, at: tuple[float, float, float] = (0.0, 0.0, 0.0)) -> Stack:
    """A box `x` by `y` by `z` whose low corner is at `at`, as a stack."""
    low_x, low_y, low_z = at
    region = bd.Pos(low_x + x / 2, low_y + y / 2) * rectangle(x, y)
    return prism(region, low_z, z)


def solid_box(
    x: float, y: float, z: float, at: tuple[float, float, float] = (0.0, 0.0, 0.0)
) -> bd.Part:
    return bd.Pos(*at) * bd.Box(x, y, z, align=bd.Align.MIN)


def same(actual: Fingerprint, expected: Fingerprint) -> None:
    assert not differences(actual, expected)


@pytest.mark.parametrize(
    ("region", "z", "height"),
    [
        (rectangle(32.0, 32.0) - circle(3.1), 0.0, 3.0),
        (astroid(29.44), 1.2, 0.48),
        (circle(5.0), 2.0, -1.5),
    ],
    ids=["tile", "astroid", "downwards"],
)
def test_a_prism_has_the_fingerprint_of_its_solid(
    region: bd.Sketch, z: float, height: float
) -> None:
    low = min(z, z + height)
    same(prism(region, z, height).fingerprint(), fingerprint(slab(region, low, abs(height))))


def test_a_union_of_stacked_boxes_is_their_fuse() -> None:
    lower, upper = box(4, 4, 1), box(2, 2, 1, at=(1.0, 1.0, 1.0))
    union = prisms.union([lower, upper])
    assert len(union.bands) == 2
    same(union.fingerprint(), fingerprint(solid_box(4, 4, 1) + solid_box(2, 2, 1, at=(1, 1, 1))))


def test_a_union_of_overlapping_boxes_is_their_fuse() -> None:
    a, b = box(4, 4, 2), box(4, 4, 2, at=(2.0, 1.0, 1.0))
    expected = solid_box(4, 4, 2) + solid_box(4, 4, 2, at=(2, 1, 1))
    same(prisms.union([a, b]).fingerprint(), fingerprint(expected))


def test_a_cut_and_a_common_are_the_solids() -> None:
    disc = prism(circle(2.0), 0.0, 2.0)
    bar = box(10, 1, 1, at=(-5.0, -0.5, 0.5))
    solid_disc, solid_bar = slab(circle(2.0), 0.0, 2.0), solid_box(10, 1, 1, at=(-5, -0.5, 0.5))
    same(prisms.cut(disc, bar).fingerprint(), fingerprint(solid_disc - solid_bar))
    same(prisms.common(disc, bar).fingerprint(), fingerprint(solid_disc & solid_bar))


def test_stacks_that_only_touch_share_nothing() -> None:
    a, beside, above = box(1, 1, 1), box(1, 1, 1, at=(1.0, 0.0, 0.0)), box(1, 1, 1, at=(0, 0, 1))
    assert prisms.common(a, beside).is_empty
    assert prisms.common(a, above).is_empty
    # The face between two stacked boxes is inside their union.
    assert prisms.union([a, above]).fingerprint().area == pytest.approx(10.0, rel=1e-12)


def test_a_gap_between_bands_leaves_both_faces() -> None:
    union = prisms.union([box(1, 1, 1), box(1, 1, 1, at=(0.0, 0.0, 2.0))])
    fp = union.fingerprint()
    assert fp.volume == pytest.approx(2.0, rel=1e-12)
    assert fp.area == pytest.approx(12.0, rel=1e-12)
    assert fp.centroid == pytest.approx((0.5, 0.5, 1.5), abs=1e-12)


def test_a_split_keeps_the_lower_piece_below() -> None:
    lower, upper = prisms.split(box(2, 2, 4), 1.0)
    assert lower.fingerprint().volume == pytest.approx(4.0, rel=1e-12)
    assert upper.fingerprint().volume == pytest.approx(12.0, rel=1e-12)
    assert lower.bounds[1][2] == pytest.approx(1.0) == upper.bounds[0][2]
    below, nothing = prisms.split(box(2, 2, 4), 4.0)
    assert nothing.is_empty
    assert below.fingerprint().volume == pytest.approx(16.0, rel=1e-12)


def test_scaling_a_stack_scales_its_fingerprint() -> None:
    fp = prism(circle(1.0, at=(1.0, 2.0)), 1.0, 1.0).scaled(10.0).fingerprint()
    assert fp.volume == pytest.approx(math.pi * 100 * 10, rel=1e-12)
    assert fp.centroid == pytest.approx((10.0, 20.0, 15.0), abs=1e-9)
    assert fp.bbox_min == pytest.approx((0.0, 10.0, 10.0), abs=1e-9)


def test_a_solid_reads_back_as_its_stack() -> None:
    solid = slab(rectangle(4.0, 4.0), 0.0, 1.0) + slab(circle(1.0), 1.0, 2.0)
    assert isinstance(solid, bd.Part)
    stack = Stack.of_solid(solid)
    assert [(band.low, band.high) for band in stack.bands] == pytest.approx([(0, 1), (1, 3)])
    same(stack.fingerprint(), fingerprint(solid))


def test_an_empty_stack_has_no_fingerprint() -> None:
    empty = prisms.common(box(1, 1, 1), box(1, 1, 1, at=(5.0, 0.0, 0.0)))
    assert empty.is_empty
    with pytest.raises(ValueError, match="empty"):
        empty.fingerprint()
    with pytest.raises(ValueError, match="a height"):
        Stack.prism(circle(1.0).faces(), 0.0, 0.0)
