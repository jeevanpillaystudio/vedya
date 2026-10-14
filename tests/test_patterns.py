"""Depth steps keep the Fusion 360 script's arithmetic; the seed of life and the torus of
rings are where they should be."""

import itertools
import math

import build123d as bd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from vedya.geometry import Align, Region, circle, stroke
from vedya.model import fingerprint
from vedya.patterns import DepthStep, Growth, depth_steps, seed_of_life, torus_rings

examples = settings(max_examples=50, deadline=None)

counts = st.integers(min_value=1, max_value=12)
heights = st.floats(min_value=0.1, max_value=100.0)
starts = st.floats(min_value=-100.0, max_value=100.0)


@examples
@given(count=counts, start=starts, total=heights, base=heights)
def test_steps_stack_evenly_from_the_start(
    count: int, start: float, total: float, base: float
) -> None:
    steps = depth_steps(count, start, total, base)
    assert len(steps) == count
    assert steps[0].z == start
    for i, step in enumerate(steps):
        assert step.height == pytest.approx(total / count, rel=1e-12)
        assert step.z == pytest.approx(start + total / count * i, rel=1e-12, abs=1e-12)
    for below, above in itertools.pairwise(steps):
        assert above.z == pytest.approx(below.z + below.height, rel=1e-12, abs=1e-12)
    top = steps[-1]
    assert top.z + top.height == pytest.approx(start + total, rel=1e-12, abs=1e-12)


@examples
@given(count=counts, base=heights)
def test_strokes_grow_or_shrink_upwards(count: int, base: float) -> None:
    thicker = depth_steps(count, 0.0, 1.0, base)
    thinner = depth_steps(count, 0.0, 1.0, base, Growth.THINNER_UPWARD)
    # The script's Decrement: step i of n has the stroke times i + 1; Increment, n - i.
    assert [step.stroke for step in thicker] == [base * (i + 1) for i in range(count)]
    assert [step.stroke for step in thinner] == [base * (count - i) for i in range(count)]


def test_the_torus_steps_of_shire() -> None:
    # a36cc3c's torus: depth_repeat_iterator(2, 2.88, 0.24, 0.32, Decrement), in cm.
    assert depth_steps(2, 28.8, 4.8, 3.2) == [
        DepthStep(z=28.8, height=2.4, stroke=3.2),
        DepthStep(z=31.2, height=2.4, stroke=6.4),
    ]


@pytest.mark.parametrize(
    ("count", "total", "base", "message"),
    [
        (0, 1.0, 1.0, "at least one step"),
        (2, 0.0, 1.0, "total_height must be positive"),
        (2, 1.0, -1.0, "stroke must be positive"),
    ],
)
def test_impossible_steps_are_refused(count: int, total: float, base: float, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        depth_steps(count, 0.0, total, base)


def area(region: Region) -> float:
    """The area of `region`'s faces; 0 for a region with none."""
    faces = region.faces()
    return fingerprint(bd.Sketch(faces)).area if faces else 0.0


SEEDS = [
    (20.0, 2.0, Align.INSIDE, Align.CENTER),
    (200.0, 9.6, Align.INSIDE, Align.CENTER),  # Shire's layer-0, lowest step
    (10.0, 1.0, Align.OUTSIDE, Align.INSIDE),
]


@pytest.mark.parametrize(("radius", "width", "centre", "petals"), SEEDS)
def test_a_seed_of_life_is_the_union_of_its_seven_stroked_circles(
    radius: float, width: float, centre: Align, petals: Align
) -> None:
    seed = seed_of_life(radius, width, centre=centre, petals=petals)
    rings = [stroke(circle(radius), width, centre)]
    for k in range(6):
        at = (radius * math.cos(k * math.pi / 3), radius * math.sin(k * math.pi / 3))
        rings.append(stroke(circle(radius, at=at), width, petals))
    # Fused in the other order, from the last petal back to the centre.
    last, *others = reversed(rings)
    union = last + others
    assert area(seed) == pytest.approx(area(union), rel=1e-9)
    assert area(seed - union) < 1e-9 * area(seed)
    assert area(union - seed) < 1e-9 * area(seed)
    # The rings overlap where the petals cross, so the union is less than their sum.
    assert area(seed) < sum(area(ring) for ring in rings)


@pytest.mark.parametrize(("radius", "width", "centre", "petals"), SEEDS)
def test_a_seed_of_life_turned_a_sixth_or_mirrored_is_itself(
    radius: float, width: float, centre: Align, petals: Align
) -> None:
    seed = seed_of_life(radius, width, centre=centre, petals=petals)
    for moved in (bd.Rot(0, 0, 60) * seed, seed.mirror(bd.Plane.XZ), seed.mirror(bd.Plane.YZ)):
        assert area(moved - seed) < 1e-9 * area(seed)
        assert area(seed - moved) < 1e-9 * area(seed)


def test_a_seed_of_life_reaches_as_far_as_its_petals_strokes() -> None:
    radius, width = 200.0, 9.6
    box = seed_of_life(radius, width).bounding_box()
    # The petals on the x axis are centred radius out; those at 60° rise sin 60° · radius.
    reach_x = 2 * radius + width / 2
    reach_y = math.sqrt(3) / 2 * radius + radius + width / 2
    reached = (box.min.X, box.min.Y, box.max.X, box.max.Y)
    assert reached == pytest.approx((-reach_x, -reach_y, reach_x, reach_y), abs=1e-6)


def test_by_default_the_centre_ring_is_inside_and_the_petals_astride() -> None:
    default = seed_of_life(50.0, 4.0)
    explicit = seed_of_life(50.0, 4.0, centre=Align.INSIDE, petals=Align.CENTER)
    assert area(default - explicit) == 0.0
    assert area(explicit - default) == 0.0
    # The centre ring's outer edge is its circle, which the petals' strokes cross.
    centre_ring = stroke(circle(50.0), 4.0, Align.INSIDE)
    assert area(centre_ring - default) == 0.0


@pytest.mark.parametrize(
    ("radius", "width", "message"),
    [(0.0, 1.0, "radius must be positive"), (10.0, 0.0, "width must be positive")],
)
def test_impossible_seeds_are_refused(radius: float, width: float, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        seed_of_life(radius, width)


def test_a_stroke_wider_than_the_seed_allows_is_refused() -> None:
    with pytest.raises(ValueError, match="cannot be offset"):
        seed_of_life(10.0, 25.0)


def angle_of(face: bd.Face) -> float:
    """The direction of `face`'s centroid from the origin, in degrees from the x axis."""
    x, y, _ = fingerprint(face).centroid
    return math.degrees(math.atan2(y, x)) % 360


@pytest.mark.parametrize(("radius", "count", "width"), [(192.0, 16, 3.2), (100.0, 8, 2.0)])
def test_the_inner_rings_are_count_circles_of_half_the_radius(
    radius: float, count: int, width: float
) -> None:
    rings = torus_rings(radius, count, width)
    # Each inner ring crosses the circle of half the radius twice, where its midline,
    # radius / 2 - width / 2 from a centre radius / 2 out, meets it.
    crossings = stroke(circle(radius / 2), 0.5, Align.CENTER)
    arcs = (rings & crossings).faces()
    middle = radius / 2 - width / 2
    turn = math.degrees(math.acos(1 - 2 * middle**2 / radius**2))
    expected = sorted(
        (360 / count * i + side * turn) % 360 for i in range(count) for side in (1, -1)
    )
    assert len(arcs) == 2 * count
    assert sorted(angle_of(arc) for arc in arcs) == pytest.approx(expected, abs=0.05)


@pytest.mark.parametrize(("radius", "count", "width"), [(192.0, 16, 3.2), (100.0, 8, 2.0)])
def test_the_inner_rings_touch_the_outer_ring_and_meet_at_the_centre(
    radius: float, count: int, width: float
) -> None:
    rings = torus_rings(radius, count, width)
    assert not (rings - circle(radius)).faces()
    # Inside the outer ring, the inner rings reach it along each axis, where four of
    # them touch the outer circle.
    inner = bd.Compound((rings & circle(radius - width)).faces()).bounding_box()
    reach = radius - width
    corners = (inner.min.X, inner.min.Y, inner.max.X, inner.max.Y)
    assert corners == pytest.approx((-reach, -reach, reach, reach), abs=1e-6)
    assert not (circle(width / 4) - rings).faces()


def test_the_first_inner_ring_lies_along_the_x_axis() -> None:
    rings = torus_rings(100.0, 1, 2.0)
    expected = stroke(circle(100.0), 2.0, Align.INSIDE) + stroke(
        circle(50.0, at=(50.0, 0.0)), 2.0, Align.INSIDE
    )
    assert not (rings - expected).faces()
    assert not (expected - rings).faces()


@pytest.mark.parametrize(
    ("radius", "count", "width", "error", "message"),
    [
        (100.0, 0, 2.0, ValueError, "at least one inner ring"),
        (100.0, 4, 60.0, ValueError, "cannot be offset"),
    ],
)
def test_impossible_tori_are_refused(
    radius: float, count: int, width: float, error: type[Exception], message: str
) -> None:
    with pytest.raises(error, match=message):
        torus_rings(radius, count, width)
