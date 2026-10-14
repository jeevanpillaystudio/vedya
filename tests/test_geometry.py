"""The primitives against closed-form areas and volumes, and the identities strokes obey."""

import math
from collections.abc import Callable

import build123d as bd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from vedya.geometry import Align, Region, circle, diamond, rectangle, slab, stroke
from vedya.model import fingerprint

REL = 1e-9

sizes = st.floats(min_value=1.0, max_value=500.0)
fractions = st.floats(min_value=0.01, max_value=0.9)
examples = settings(max_examples=25, deadline=None)


def area(region: Region) -> float:
    return fingerprint(region).area


def test_circle_is_a_disc_at_its_centre() -> None:
    disc = circle(2.5, at=(10.0, -4.0))
    assert area(disc) == pytest.approx(math.pi * 2.5**2, rel=REL)
    assert fingerprint(disc).centroid == pytest.approx((10.0, -4.0, 0.0), abs=1e-9)


def test_rectangle_is_centred_on_the_origin() -> None:
    box = rectangle(640.0, 960.0).bounding_box()
    assert (box.min.X, box.min.Y, box.max.X, box.max.Y) == (-320.0, -480.0, 320.0, 480.0)
    assert area(rectangle(640.0, 960.0)) == pytest.approx(640.0 * 960.0, rel=REL)


def test_diamond_has_its_vertices_on_the_axes() -> None:
    vertices = {(round(v.X, 9), round(v.Y, 9)) for v in diamond(310.0).vertices()}
    assert vertices == {(310.0, 0.0), (0.0, 310.0), (-310.0, 0.0), (0.0, -310.0)}
    assert area(diamond(310.0)) == pytest.approx(2 * 310.0**2, rel=REL)


@pytest.mark.parametrize(
    "make",
    [
        lambda: circle(0.0),
        lambda: rectangle(-1.0, 2.0),
        lambda: rectangle(1.0, 0.0),
        lambda: diamond(0.0),
        lambda: stroke(circle(1.0), 0.0, Align.OUTSIDE),
        lambda: slab(circle(1.0), 0.0, 0.0),
    ],
)
def test_sizes_must_be_positive(make: Callable[[], object]) -> None:
    with pytest.raises(ValueError, match="must be positive"):
        make()


@examples
@given(radius=sizes, fraction=fractions)
def test_circle_strokes(radius: float, fraction: float) -> None:
    width = fraction * radius
    disc = circle(radius)
    assert area(stroke(disc, width, Align.INSIDE)) == pytest.approx(
        math.pi * (radius**2 - (radius - width) ** 2), rel=REL
    )
    assert area(stroke(disc, width, Align.OUTSIDE)) == pytest.approx(
        math.pi * ((radius + width) ** 2 - radius**2), rel=REL
    )
    assert area(stroke(disc, width, Align.CENTER)) == pytest.approx(
        2 * math.pi * radius * width, rel=REL
    )


@examples
@given(length=sizes, width_y=sizes, fraction=fractions)
def test_rectangle_strokes_keep_sharp_corners(
    length: float, width_y: float, fraction: float
) -> None:
    w = fraction * min(length, width_y) / 2
    shape = rectangle(length, width_y)
    outside = stroke(shape, w, Align.OUTSIDE)
    assert area(outside) == pytest.approx(
        (length + 2 * w) * (width_y + 2 * w) - length * width_y, rel=REL
    )
    size = outside.bounding_box().size
    assert pytest.approx(length + 2 * w, rel=REL) == size.X
    assert pytest.approx(width_y + 2 * w, rel=REL) == size.Y
    assert area(stroke(shape, w, Align.INSIDE)) == pytest.approx(
        length * width_y - (length - 2 * w) * (width_y - 2 * w), rel=REL
    )
    assert area(stroke(shape, w, Align.CENTER)) == pytest.approx(
        2 * w * (length + width_y), rel=REL
    )


@examples
@given(half_diagonal=sizes, fraction=fractions)
def test_diamond_strokes_keep_sharp_corners(half_diagonal: float, fraction: float) -> None:
    w = fraction * half_diagonal / math.sqrt(2)  # the inscribed circle's radius bounds w
    inner = half_diagonal - w * math.sqrt(2)
    outer = half_diagonal + w * math.sqrt(2)
    shape = diamond(half_diagonal)
    assert area(stroke(shape, w, Align.INSIDE)) == pytest.approx(
        2 * (half_diagonal**2 - inner**2), rel=REL
    )
    assert area(stroke(shape, w, Align.OUTSIDE)) == pytest.approx(
        2 * (outer**2 - half_diagonal**2), rel=REL
    )


shapes = st.one_of(
    st.builds(circle, sizes),
    st.builds(rectangle, sizes, sizes),
    st.builds(diamond, sizes),
)


@examples
@given(shape=shapes, fraction=st.floats(min_value=0.01, max_value=0.45))
def test_stroke_sides_partition_the_centred_stroke(shape: bd.Sketch, fraction: float) -> None:
    box = shape.bounding_box().size
    w = fraction * min(box.X, box.Y) / 2 / math.sqrt(2)
    inside = stroke(shape, w, Align.INSIDE)
    outside = stroke(shape, w, Align.OUTSIDE)
    # A centred stroke of 2w is the inside and outside strokes of w, side by side.
    assert area(stroke(shape, 2 * w, Align.CENTER)) == pytest.approx(
        area(inside) + area(outside), rel=REL
    )
    # The inside stroke lies within the shape, and the outside stroke beyond it.
    assert area(inside & shape) == pytest.approx(area(inside), rel=REL)
    assert area(outside - shape) == pytest.approx(area(outside), rel=REL)


@pytest.mark.parametrize(
    ("shape", "width", "align"),
    [
        (circle(3.0), 3.5, Align.INSIDE),
        (circle(3.0), 7.0, Align.CENTER),
        (diamond(10.0), 8.0, Align.INSIDE),  # its inscribed circle's radius is 7.07
    ],
)
def test_a_stroke_wider_than_the_shape_allows_is_refused(
    shape: bd.Sketch, width: float, align: Align
) -> None:
    with pytest.raises(ValueError, match="cannot be offset"):
        stroke(shape, width, align)


def test_stroke_takes_a_union_of_separate_regions() -> None:
    pair = circle(1.0) + circle(1.0, at=(5.0, 0.0))
    assert area(stroke(pair, 0.2, Align.OUTSIDE)) == pytest.approx(
        2 * math.pi * (1.2**2 - 1.0), rel=REL
    )


@examples
@given(radius=sizes, z=st.floats(min_value=-100.0, max_value=100.0), height=sizes)
def test_slab_sweeps_the_region_from_z_up(radius: float, z: float, height: float) -> None:
    solid = fingerprint(slab(circle(radius), z, height))
    assert solid.volume == pytest.approx(math.pi * radius**2 * height, rel=REL)
    assert solid.bbox_min[2] == pytest.approx(z, abs=1e-9)
    assert solid.bbox_max[2] == pytest.approx(z + height, abs=1e-9)
    assert solid.centroid == pytest.approx((0.0, 0.0, z + height / 2), abs=1e-6)


def test_slab_of_a_region_with_a_hole() -> None:
    tile = slab(rectangle(32.0, 32.0) - circle(3.0), 0.0, 3.0)
    assert fingerprint(tile).volume == pytest.approx((32.0**2 - math.pi * 9.0) * 3.0, rel=REL)


@pytest.mark.parametrize(
    "region", [circle(1.0) - circle(2.0), circle(1.0).wire()], ids=["nothing left", "a wire"]
)
def test_an_empty_region_is_refused(region: Region) -> None:
    with pytest.raises(ValueError, match="empty region"):
        slab(region, 0.0, 1.0)
    with pytest.raises(ValueError, match="empty region"):
        stroke(region, 0.1, Align.INSIDE)


def test_a_region_is_flat() -> None:
    with pytest.raises(TypeError, match="flat"):
        slab(bd.Box(1.0, 1.0, 1.0), 0.0, 1.0)
