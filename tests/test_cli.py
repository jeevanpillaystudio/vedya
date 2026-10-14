"""The `vedya` command, run as a user runs it."""

import math
from dataclasses import dataclass
from pathlib import Path

import build123d as bd
import pytest
from typer.testing import CliRunner

from vedya.cli import _apply_settings, app
from vedya.model import fingerprint

runner = CliRunner()


def test_list_names_umss() -> None:
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0, result.output
    assert any(line.startswith("umss\t") for line in result.stdout.splitlines())


def test_build_writes_each_part_and_the_union(tmp_path: Path) -> None:
    result = runner.invoke(app, ["build", "umss", "--out", str(tmp_path / "out")])
    assert result.exit_code == 0, result.output
    expected = {
        f"{stem}.{suffix}" for stem in ("umss", "umss-magnet-base") for suffix in ("stl", "step")
    }
    assert {path.name for path in (tmp_path / "out").iterdir()} == expected
    assert sorted(Path(line).name for line in result.stdout.splitlines()) == sorted(expected)


def test_build_applies_typed_settings(tmp_path: Path) -> None:
    args = ["build", "umss", "--set", "parts=tile", "--set", "hole_radius=3.0"]
    result = runner.invoke(app, [*args, "--format", "step", "--out", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert sorted(path.name for path in tmp_path.iterdir()) == ["umss-tile.step", "umss.step"]
    tile = fingerprint(bd.import_step(tmp_path / "umss.step"))
    assert tile.volume == pytest.approx((32.0**2 - math.pi * 3.0**2) * 3.0, rel=1e-9)


@pytest.mark.parametrize(
    ("args", "message"),
    [
        (["build", "lid"], "no design named 'lid'"),
        (["build", "umss", "--set", "radius=3"], "--set radius: UmssParams has no such parameter"),
        (["build", "umss", "--set", "hole_radius=wide"], "--set hole_radius:"),
        (["build", "umss", "--set", "hole_radius"], "must be written name=value"),
        (["build", "umss", "--set", "tile=32,32"], "expected 3 comma-separated values"),
        (["build", "umss", "--set", "parts=lid"], "no part 'lid'"),
        (["build", "umss", "--format", "obj"], "cannot write obj"),
    ],
)
def test_build_reports_a_mistake_in_one_line(tmp_path: Path, args: list[str], message: str) -> None:
    result = runner.invoke(app, [*args, "--out", str(tmp_path / "out")])
    assert result.exit_code == 1
    assert result.stderr.startswith("error: ")
    assert message in result.stderr
    assert len(result.stderr.splitlines()) == 1
    assert not (tmp_path / "out").exists()


@dataclass(frozen=True)
class Pass:
    radius: float = 1.0


@dataclass(frozen=True)
class Nested:
    scale: float = 1.0
    count: int = 1
    mirrored: bool = False
    sizes: tuple[float, ...] = (1.0,)
    passes: tuple[Pass, ...] = (Pass(),)


def test_settings_are_typed_as_their_fields() -> None:
    settings = ["scale=2.5", "count=3", "mirrored=yes", "sizes=1, 2.5,4"]
    assert _apply_settings(Nested(), settings) == Nested(
        scale=2.5, count=3, mirrored=True, sizes=(1.0, 2.5, 4.0)
    )


def test_fields_that_are_not_numbers_or_words_are_refused() -> None:
    with pytest.raises(ValueError, match="--set passes: only numbers"):
        _apply_settings(Nested(), ["passes=2"])
