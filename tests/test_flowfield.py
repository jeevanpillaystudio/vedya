"""The flow field: its shape, its unit vectors, the noise beneath it, and agreement with
the 2024 library it ports."""

import math
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt
import pytest

# noise is compiled, and ships no type stubs.
from noise import pnoise2  # pyright: ignore[reportMissingTypeStubs]
from typer.testing import CliRunner

from tools.legacy import golden
from vedya.cli import app
from vedya.flowfield import EXTENT, flow_field

runner = CliRunner()

PNOISE = 0.07723968476057053
"""`pnoise2(0.1, 0.2)` with the 2024 example's octaves, persistence, lacunarity, repeats and
base, as noise 1.2.2 gave it on Python 3.12 and 3.14 on an Apple-silicon Mac."""


type Field = npt.NDArray[np.float64]


@pytest.fixture(scope="module")
def field() -> Field:
    return flow_field()


def test_the_noise_is_the_noise_the_2024_library_drew() -> None:
    value = pnoise2(
        0.1, 0.2, octaves=6, persistence=0.5, lacunarity=2.0, repeatx=150, repeaty=150, base=0
    )
    assert value == PNOISE


def test_the_example_field_is_150_by_150_unit_vectors(field: Field) -> None:
    assert field.shape == (150, 150, 2)
    assert field.dtype == np.float64
    np.testing.assert_allclose(np.hypot(field[..., 0], field[..., 1]), 1.0, rtol=0, atol=1e-15)
    # The noise is 0 at the origin, so the first vector points along x.
    np.testing.assert_array_equal(field[0, 0], [1.0, 0.0])


def angle_at(x: float, y: float) -> float:
    """2π times the example's noise at (x, y) on the grid."""
    noise = pnoise2(
        x * 0.1, y * 0.1, octaves=6, persistence=0.5, lacunarity=2.0, repeatx=150, repeaty=150
    )
    return 2 * math.pi * noise


@pytest.mark.parametrize(("row", "column"), [(90, 120), (40, 7), (149, 75)])
def test_each_vector_turns_by_the_noise_at_its_point(field: Field, row: int, column: int) -> None:
    # Rows go up in y and columns across in x, from 0 to EXTENT.
    steps = np.linspace(0, EXTENT, 150)
    x, y = float(steps[column]), float(steps[row])
    angle = angle_at(x, y)
    np.testing.assert_allclose(field[row, column], [math.cos(angle), math.sin(angle)], atol=1e-15)
    # The noise differs with x and y swapped, so a field with them swapped would fail.
    assert abs(angle_at(y, x) - angle) > 1e-3


def test_the_grid_takes_its_size_across_then_up() -> None:
    assert flow_field(width=3, height=2).shape == (2, 3, 2)
    assert flow_field(width=1, height=1).shape == (1, 1, 2)


@pytest.mark.parametrize(
    ("options", "message"),
    [
        ({"width": 0}, "the grid needs a point"),
        ({"height": -1}, "the grid needs a point"),
        ({"octaves": 0}, "octaves must be at least 1"),
        ({"scale": 0.0}, "scale must be positive"),
        ({"persistence": math.nan}, "persistence must be positive"),
        ({"lacunarity": -2.0}, "lacunarity must be positive"),
    ],
)
def test_an_impossible_field_is_refused(options: dict[str, Any], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        flow_field(**options)


def test_the_command_writes_the_example_field(tmp_path: Path, field: Field) -> None:
    out = tmp_path / "out" / "field.npy"
    result = runner.invoke(app, ["flowfield", "--out", str(out)])
    assert result.exit_code == 0, result.output
    assert result.stdout.splitlines() == [str(out)]
    np.testing.assert_array_equal(np.load(out), field)


def test_the_command_takes_other_values(tmp_path: Path) -> None:
    out = tmp_path / "field.npy"
    options = ["--width", "20", "--height", "10", "--octaves", "2", "--scale", "0.5"]
    result = runner.invoke(app, ["flowfield", *options, "--out", str(out)])
    assert result.exit_code == 0, result.output
    np.testing.assert_array_equal(
        np.load(out), flow_field(width=20, height=10, octaves=2, scale=0.5)
    )


@pytest.mark.parametrize(
    ("name", "args", "message"),
    [
        ("field.txt", [], "error: --out 'field.txt': the flow field is written as .npy\n"),
        ("field.npy", ["--octaves", "0"], "error: octaves must be at least 1, not 0\n"),
    ],
)
def test_the_command_reports_a_mistake_in_one_line(
    tmp_path: Path, name: str, args: list[str], message: str
) -> None:
    out = tmp_path / "out" / name
    result = runner.invoke(app, ["flowfield", *args, "--out", str(out)])
    assert result.exit_code == 1
    assert result.stderr == message
    assert not out.parent.exists()


@pytest.mark.slow
def test_the_field_is_the_2024_librarys_to_the_bit(field: Field) -> None:
    with golden.scripts("08f31da", "src/lib/src/examples") as load:
        old = load("flow_field_visual").generate_2d_flowfield(150, 150, 0.1, 6, 0.5, 2.0)
    np.testing.assert_array_equal(field, old)
