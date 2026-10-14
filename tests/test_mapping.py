"""The coordinate maps: values fixed by their geometry, round trips, the command's points,
and agreement with the 2024 library they port."""

import csv
import math
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from typer.testing import CliRunner

from tools.legacy import golden
from vedya.cli import app
from vedya.mapping import (
    Points,
    circle_samples,
    from_cylinder,
    from_sphere,
    rectangle_samples,
    to_cylinder,
    to_sphere,
)

runner = CliRunner()
examples = settings(max_examples=100, deadline=None)

lengths = st.floats(min_value=0.1, max_value=1000.0)
fractions = st.floats(min_value=-0.49, max_value=0.49)


def test_a_quarter_of_the_length_turns_a_quarter_round_the_cylinder() -> None:
    plane = [[0.0, 2.0], [2.5, 1.0], [5.0, 0.0], [7.5, 3.0]]
    np.testing.assert_allclose(
        to_cylinder(plane, length=10.0, radius=2.0),
        [[2.0, 0.0, 2.0], [0.0, 2.0, 1.0], [-2.0, 0.0, 0.0], [0.0, -2.0, 3.0]],
        atol=1e-15,
    )


def test_the_height_runs_from_pole_to_pole_of_the_sphere() -> None:
    plane = [[0.0, 0.0], [0.0, 2.0], [2.5, 2.0], [0.0, 4.0]]
    np.testing.assert_allclose(
        to_sphere(plane, length=10.0, height=4.0, radius=3.0),
        [[0.0, 0.0, 3.0], [3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, -3.0]],
        atol=1e-15,
    )


def test_unwrapping_takes_the_angle_between_minus_and_plus_half_a_turn() -> None:
    cylinder = [[0.0, 1.0, 5.0], [-1.0, 0.0, 2.0], [0.0, -3.0, 1.0]]
    np.testing.assert_allclose(
        from_cylinder(cylinder, length=10.0), [[2.5, 5.0], [5.0, 2.0], [-2.5, 1.0]], atol=1e-15
    )
    sphere = [[0.0, 0.0, 3.0], [3.0, 0.0, 0.0], [0.0, -3.0, 0.0], [0.0, 0.0, -3.0]]
    np.testing.assert_allclose(
        from_sphere(sphere, length=10.0, height=4.0, radius=3.0),
        [[0.0, 0.0], [0.0, 2.0], [-2.5, 2.0], [0.0, 4.0]],
        atol=1e-15,
    )


def test_a_map_keeps_the_shape_of_its_array_of_points() -> None:
    grid = np.zeros((4, 5, 2))
    assert to_cylinder(grid, 1.0, 1.0).shape == (4, 5, 3)
    assert to_sphere(grid, 1.0, 1.0, 1.0).shape == (4, 5, 3)
    assert from_cylinder(np.ones((4, 5, 3)), 1.0).shape == (4, 5, 2)
    assert to_cylinder([1.0, 2.0], 1.0, 1.0).shape == (3,)


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (lambda: to_cylinder([[0.0, 0.0, 0.0]], 1.0, 1.0), "2 coordinates each"),
        (lambda: from_sphere([[0.0, 0.0]], 1.0, 1.0, 1.0), "3 coordinates each"),
        (lambda: to_cylinder(1.0, 1.0, 1.0), "2 coordinates each"),
        (lambda: to_cylinder([[0.0, 0.0]], 0.0, 1.0), "length must be positive"),
        (lambda: to_sphere([[0.0, 0.0]], 1.0, -1.0, 1.0), "height must be positive"),
        (lambda: from_sphere([[0.0, 0.0, 0.0]], 1.0, 1.0, math.inf), "radius must be positive"),
        (lambda: rectangle_samples(1.0, 1.0, 0.0), "resolution must be positive"),
        (lambda: circle_samples(-1.0, 0.1), "radius must be positive"),
    ],
)
def test_impossible_maps_are_refused(call: Callable[[], object], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        call()


def test_the_rectangle_is_sampled_at_its_cell_centres_column_by_column() -> None:
    np.testing.assert_allclose(
        rectangle_samples(3.0, 2.0, 1.0),
        [[0.5, 0.5], [0.5, 1.5], [1.5, 0.5], [1.5, 1.5], [2.5, 0.5], [2.5, 1.5]],
    )
    # A part cell at the far edge is left out; so is a whole one when the quotient's
    # rounding falls short, as 0.3 / 0.1 = 2.9999999999999996 does.
    assert rectangle_samples(2.5, 1.0, 1.0).shape == (2, 2)
    assert rectangle_samples(0.3, 0.1, 0.1).shape == (2, 2)
    assert rectangle_samples(0.5, 1.0, 1.0).shape == (0, 2)


def test_the_disc_is_sampled_in_rings_from_its_centre() -> None:
    samples = circle_samples(1.0, 0.5, centre=(3.0, -1.0))
    # int(2 · 1 / 0.5) = 4 rings of int(2π / 0.5) = 12 points.
    assert samples.shape == (48, 2)
    offsets = (samples - [3.0, -1.0]).reshape(4, 12, 2)
    np.testing.assert_allclose(
        np.hypot(offsets[..., 0], offsets[..., 1]),
        np.repeat([[0.0], [0.25], [0.5], [0.75]], 12, axis=1),
        atol=1e-15,
    )
    angles = np.arctan2(offsets[1:, :, 1], offsets[1:, :, 0]) % (2 * math.pi)
    np.testing.assert_allclose(angles, np.tile(np.arange(12) * math.pi / 6, (3, 1)), atol=1e-14)


@examples
@given(length=lengths, fraction=fractions, y=st.floats(min_value=-1e3, max_value=1e3))
def test_a_point_wrapped_onto_the_cylinder_unwraps_to_itself(
    length: float, fraction: float, y: float
) -> None:
    point = [fraction * length, y]
    back = from_cylinder(to_cylinder(point, length, radius=2.0), length)
    assert back[0] == pytest.approx(point[0], abs=1e-12 * length)
    assert back[1] == y


@examples
@given(length=lengths, fraction=fractions, turns=st.integers(min_value=-5, max_value=5))
def test_whole_turns_round_the_cylinder_unwrap_to_nothing(
    length: float, fraction: float, turns: int
) -> None:
    point = [(fraction + turns) * length, 1.0]
    back = from_cylinder(to_cylinder(point, length, radius=1.0), length)
    assert back[0] == pytest.approx(fraction * length, abs=1e-11 * length)


@examples
@given(
    length=lengths,
    height=lengths,
    radius=lengths,
    across=fractions,
    up=st.floats(min_value=0.01, max_value=0.99),
)
def test_a_point_wrapped_onto_the_sphere_unwraps_to_itself(
    length: float, height: float, radius: float, across: float, up: float
) -> None:
    # Away from the poles, where the longitude is lost.
    point = [across * length, up * height]
    back = from_sphere(to_sphere(point, length, height, radius), length, height, radius)
    assert back[0] == pytest.approx(point[0], abs=1e-12 * length)
    assert back[1] == pytest.approx(point[1], abs=1e-12 * height)


@examples
@given(radius=lengths, angle=st.floats(min_value=-math.pi, max_value=math.pi), z=lengths)
def test_a_point_on_the_cylinder_wraps_back_to_itself(
    radius: float, angle: float, z: float
) -> None:
    point = [radius * math.cos(angle), radius * math.sin(angle), z]
    again = to_cylinder(from_cylinder(point, length=7.0), length=7.0, radius=radius)
    np.testing.assert_allclose(again, point, atol=1e-12 * max(radius, z))


def points_in(path: Path) -> dict[str, Points]:
    """The points of each shape in a CSV file `vedya map` wrote."""
    with path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.reader(file))
    assert rows[0] == ["shape", "x", "y", "z"]
    shapes: dict[str, list[list[float]]] = {}
    for shape, *coordinates in rows[1:]:
        shapes.setdefault(shape, []).append([float(value) for value in coordinates])
    return {shape: np.array(points) for shape, points in shapes.items()}


@pytest.mark.parametrize("surface", ["cylinder", "sphere"])
def test_the_command_maps_the_2024_rectangle_and_disc(tmp_path: Path, surface: str) -> None:
    out = tmp_path / "points" / f"{surface}.csv"
    result = runner.invoke(app, ["map", surface, "--out", str(out)])
    assert result.exit_code == 0, result.output
    assert result.stdout.splitlines() == [str(out)]
    shapes = points_in(out)
    assert {name: points.shape for name, points in shapes.items()} == {
        "rectangle": (4000, 3),
        "circle": (1240, 3),
    }
    # The 2024 command's values: a 10 by 4 rectangle at 0.1 on a radius of 1, and a disc
    # of radius 1 centred at height 2. The file holds every coordinate exactly.
    rectangle, circle = rectangle_samples(10.0, 4.0, 0.1), circle_samples(1.0, 0.1, (0.0, 2.0))
    if surface == "cylinder":
        expected = [to_cylinder(rectangle, 10.0, 1.0), to_cylinder(circle, 10.0, 1.0)]
    else:
        expected = [to_sphere(rectangle, 10.0, 4.0, 1.0), to_sphere(circle, 10.0, 4.0, 1.0)]
    np.testing.assert_array_equal(shapes["rectangle"], expected[0])
    np.testing.assert_array_equal(shapes["circle"], expected[1])


def test_the_command_takes_other_values(tmp_path: Path) -> None:
    out = tmp_path / "points.csv"
    options = ["--length", "6", "--height", "2", "--resolution", "0.5", "--circle-radius", "0.5"]
    result = runner.invoke(app, ["map", "cylinder", *options, "--out", str(out)])
    assert result.exit_code == 0, result.output
    shapes = points_in(out)
    assert shapes["rectangle"].shape == (12 * 4, 3)
    assert shapes["circle"].shape == (2 * 6, 3)


def test_the_command_reports_a_mistake_in_one_line(tmp_path: Path) -> None:
    out = tmp_path / "out" / "points.csv"
    result = runner.invoke(app, ["map", "cylinder", "--resolution", "0", "--out", str(out)])
    assert result.exit_code == 1
    assert result.stderr == "error: resolution must be positive, not 0.0\n"
    assert not out.parent.exists()


LIBRARY = ("08f31da", "src/lib/src/coord_transform/src")
"""The last commit with the 2024 library, and the folder of its coordinate maps."""


@pytest.mark.slow
@pytest.mark.parametrize(
    ("length", "height", "radius", "resolution", "circle_radius", "circle_height"),
    [(10.0, 4.0, 1.0, 0.1, 1.0, 2.0), (7.3, 2.9, 2.2, 0.13, 0.7, 1.1)],
    ids=["the command's values", "others"],
)
def test_the_maps_give_the_2024_librarys_values_to_the_bit(
    length: float,
    height: float,
    radius: float,
    resolution: float,
    circle_radius: float,
    circle_height: float,
) -> None:
    rectangle = rectangle_samples(length, height, resolution)
    circle = circle_samples(circle_radius, resolution, (0.0, circle_height))
    with golden.scripts(*LIBRARY) as load:
        cylinder, sphere = load("cylinder"), load("sphere")
        old_rectangle = cylinder.transform_rectangle_to_cylinder(length, height, radius, resolution)
        old_circle = cylinder.transform_circle_to_cylinder(
            length, radius, circle_radius, circle_height, resolution
        )
        np.testing.assert_array_equal(to_cylinder(rectangle, length, radius), old_rectangle)
        np.testing.assert_array_equal(to_cylinder(circle, length, radius), old_circle)
        x, y = cylinder.transform_cylinder_to_cartesian(*old_rectangle.T, length, radius)
        np.testing.assert_array_equal(from_cylinder(old_rectangle, length), np.stack([x, y], -1))

        old_rectangle = sphere.transform_rectangle_to_sphere(length, height, radius, resolution)
        old_circle = sphere.transform_circle_to_sphere(
            length, height, radius, circle_radius, circle_height, resolution
        )
        np.testing.assert_array_equal(to_sphere(rectangle, length, height, radius), old_rectangle)
        np.testing.assert_array_equal(to_sphere(circle, length, height, radius), old_circle)
        x, y = sphere.transform_sphere_to_cartesian(*old_rectangle.T, length, height, radius)
        np.testing.assert_array_equal(
            from_sphere(old_rectangle, length, height, radius), np.stack([x, y], -1)
        )
