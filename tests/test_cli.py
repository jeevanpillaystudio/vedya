"""The `vedya` command, run as a user runs it."""

import logging
import math
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import build123d as bd
import pytest
from typer.testing import CliRunner

from stl_mesh import is_closed, mesh_volume, read_3mf, read_stl
from tools.legacy import golden
from vedya.cli import _apply_settings, app
from vedya.designs.umss import PART_NAMES as UMSS_PARTS
from vedya.designs.umss import UmssParams
from vedya.designs.umss import build as build_umss
from vedya.export import LINEAR_TOLERANCE
from vedya.model import aggregate, fingerprint

runner = CliRunner()


@pytest.mark.parametrize("name", ["umss", "shire"])
def test_list_names_each_design(name: str) -> None:
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0, result.output
    assert any(line.startswith(f"{name}\t") for line in result.stdout.splitlines())


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
        (["build", "umss", "--slice", "3.2"], "must be written HEIGHT:COUNT"),
        (["build", "umss", "--slice", "thin:2"], "must be written HEIGHT:COUNT"),
        (["build", "umss", "--slice", "3.2:0"], "the count at least 1"),
        (["build", "umss", "--slice", "-1:3"], "the height must be positive"),
    ],
)
def test_build_reports_a_mistake_in_one_line(tmp_path: Path, args: list[str], message: str) -> None:
    result = runner.invoke(app, [*args, "--out", str(tmp_path / "out")])
    assert result.exit_code == 1
    assert result.stderr.startswith("error: ")
    assert message in result.stderr
    assert len(result.stderr.splitlines()) == 1
    assert not (tmp_path / "out").exists()


def test_build_writes_only_the_parts_when_asked(tmp_path: Path) -> None:
    result = runner.invoke(
        app, ["build", "umss", "--parts", "--format", "step", "--out", str(tmp_path)]
    )
    assert result.exit_code == 0, result.output
    assert sorted(path.name for path in tmp_path.iterdir()) == ["umss-magnet-base.step"]


def test_build_slices_the_aggregate_and_skips_an_empty_layer(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    # The magnet base, from -2.5 to -1 mm, and the base ring, from -0.5 to 0, leave the
    # layer from -1 to -0.5 empty; the tile stands from 0 to 3.
    args = ["build", "umss", "--set", "parts=tile,magnet-base,base-ring"]
    options = ["--aggregate", "--slice", "0.5:12", "--format", "3mf", "--out", str(tmp_path)]
    with caplog.at_level(logging.WARNING, logger="vedya"):
        result = runner.invoke(app, [*args, *options])
    assert result.exit_code == 0, result.output
    layers = [f"umss-slice-{i:02d}.3mf" for i in range(11) if i != 3]
    assert sorted(path.name for path in tmp_path.iterdir()) == sorted(["umss.3mf", *layers])
    assert "layer 3 holds nothing" in caplog.text
    meshes = [read_3mf(tmp_path / name) for name in layers]
    assert all(is_closed(mesh.corners) for mesh in meshes)
    # Each mesh lies within the tolerance of its solid's faces: the union's, and on each
    # side of the 10 cuts at most the tile.
    exact = fingerprint(aggregate(build_umss(UmssParams(parts=UMSS_PARTS))))
    total = sum(mesh_volume(mesh.triangles) for mesh in meshes)
    assert abs(total - exact.volume) <= LINEAR_TOLERANCE * (exact.area + 2 * 10 * 32.0 * 32.0)
    whole = mesh_volume(read_3mf(tmp_path / "umss.3mf").triangles)
    assert abs(whole - exact.volume) <= LINEAR_TOLERANCE * exact.area


@pytest.mark.slow
def test_build_shire_into_twelve_layers_writes_thirteen_files(tmp_path: Path) -> None:
    args = ["build", "shire", "--aggregate", "--slice", "3.2:12", "--format", "stl"]
    result = runner.invoke(app, [*args, "--out", str(tmp_path)])
    assert result.exit_code == 0, result.output
    layers = [f"shire-slice-{i:02d}.stl" for i in range(12)]
    assert sorted(path.name for path in tmp_path.iterdir()) == sorted(["shire.stl", *layers])
    whole = read_stl(tmp_path / "shire.stl")
    total = sum(mesh_volume(read_stl(tmp_path / name)) for name in layers)
    # The layers' solids hold the whole's volume, and each mesh lies within the tolerance
    # of its solid's faces: the whole's, and on each side of the 11 cuts at most the board.
    golden_area = golden.read("shire").aggregate.area  # pyright: ignore[reportOptionalMemberAccess]
    faces = 2 * golden_area + 2 * 11 * 640.0 * 960.0
    assert abs(total - mesh_volume(whole)) <= LINEAR_TOLERANCE * faces


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


WITHOUT_THE_EXTRAS = """
import importlib.abc
import sys

EXTRAS = {"cv2", "noise", "plotly"}


class Missing(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name.partition(".")[0] in EXTRAS:
            raise ModuleNotFoundError(f"No module named {name!r}", name=name)
        return None


sys.meta_path.insert(0, Missing())

import vedya
import vedya.cli
import vedya.designs
import vedya.export
import vedya.geometry
import vedya.mapping
import vedya.model
import vedya.patterns
from typer.testing import CliRunner

assert vedya.designs.load_designs()
runner = CliRunner()
result = runner.invoke(vedya.cli.app, ["map", "sphere", "--out", "points.csv"])
assert result.exit_code == 0, result.output
for args in (
    ["stencil", "image.png", "--out", "stencil.png"],
    ["flowfield", "--out", "field.npy"],
    ["map", "cylinder", "--out", "points.csv", "--figure", "figure.html"],
):
    result = runner.invoke(vedya.cli.app, args)
    assert result.exit_code == 1, result.output
    print(result.stderr, end="")
assert not EXTRAS & {name.partition(".")[0] for name in sys.modules}
"""


def test_the_core_and_its_commands_work_without_the_extras(tmp_path: Path) -> None:
    # A fresh interpreter, isolated from the environment and the working folder, in which
    # OpenCV, plotly and noise cannot be imported.
    result = subprocess.run(
        [sys.executable, "-I", "-c", WITHOUT_THE_EXTRAS],
        capture_output=True,
        check=False,
        cwd=tmp_path,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "error: vedya.render needs the render extra, which brings cv2: install it with "
        "`uv sync --extra render` or `pip install 'vedya[render]'`",
        "error: vedya.flowfield needs the examples extra, which brings noise: install it with "
        "`uv sync --extra examples` or `pip install 'vedya[examples]'`",
        "error: vedya.render needs the render extra, which brings cv2: install it with "
        "`uv sync --extra render` or `pip install 'vedya[render]'`",
    ]
    assert sorted(path.name for path in tmp_path.iterdir()) == ["points.csv"]
