"""Round trips: what export writes holds the solid it was given."""

from pathlib import Path

import build123d as bd
import numpy as np
import pytest

from stl_mesh import mesh_bounds, mesh_volume, read_stl
from vedya.export import LINEAR_TOLERANCE, SUFFIXES, export
from vedya.geometry import circle, rectangle, slab
from vedya.model import fingerprint

TILE = slab(rectangle(32.0, 32.0) - circle(3.1), 0.0, 3.0)
DISC = slab(circle(640.0), -2.5, 1.5)


def test_stl_of_a_box_is_exact(tmp_path: Path) -> None:
    solid = bd.Box(32.0, 32.0, 3.0)
    export(solid, tmp_path / "box.stl")
    triangles = read_stl(tmp_path / "box.stl")
    assert mesh_volume(triangles) == pytest.approx(fingerprint(solid).volume, rel=1e-7)


@pytest.mark.parametrize("solid", [TILE, DISC], ids=["tile", "disc"])
def test_stl_lies_within_the_linear_tolerance(tmp_path: Path, solid: bd.Part) -> None:
    export(solid, tmp_path / "solid.stl")
    triangles = read_stl(tmp_path / "solid.stl")
    exact = fingerprint(solid)
    # Every mesh point lies within the tolerance of the surface, so the volume between
    # them is at most the tolerance times the surface's area.
    assert abs(mesh_volume(triangles) - exact.volume) <= LINEAR_TOLERANCE * exact.area
    low, high = mesh_bounds(triangles)
    np.testing.assert_allclose(low, exact.bbox_min, atol=LINEAR_TOLERANCE)
    np.testing.assert_allclose(high, exact.bbox_max, atol=LINEAR_TOLERANCE)


@pytest.mark.parametrize("suffix", [".step", ".stp", ".STEP"])
def test_step_keeps_the_exact_solid(tmp_path: Path, suffix: str) -> None:
    path = tmp_path / f"tile{suffix}"
    export(TILE, path)
    exact, loaded = fingerprint(TILE), fingerprint(bd.import_step(path))
    assert loaded.volume == pytest.approx(exact.volume, rel=1e-9)
    assert loaded.area == pytest.approx(exact.area, rel=1e-9)
    assert loaded.bbox_min == pytest.approx(exact.bbox_min, abs=1e-6)
    assert loaded.bbox_max == pytest.approx(exact.bbox_max, abs=1e-6)


def test_an_unknown_suffix_names_the_supported_ones(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match=", ".join(SUFFIXES)):
        export(TILE, tmp_path / "tile.obj")


def test_a_missing_folder_is_reported(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="no such folder"):
        export(TILE, tmp_path / "missing" / "tile.stl")


def test_an_empty_shape_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="empty"):
        export(bd.Part(), tmp_path / "nothing.step")
