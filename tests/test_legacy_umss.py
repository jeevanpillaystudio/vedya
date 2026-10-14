"""The stand-in runs the UMSS scripts from history and builds what Fusion built.

Milestone 1's STL files are the only files in the repository that Fusion exported from
the code with no manual step, so they check the stand-in itself: run unchanged, the
scripts that made two of them must give the same tile. These tests read git history,
and need a clone with every commit.
"""

import numpy as np
import pytest

from references import MEASURED_EXCESS, differences, milestone_1_stl
from stl_mesh import mesh_bounds, mesh_volume, read_stl
from tools.legacy import golden, history
from tools.legacy.adsk import fusion

pytestmark = pytest.mark.slow

MILESTONE_ENTRY = "src/v1/api-vedya-draw/APIDrawVedya.py"


@pytest.mark.parametrize(
    ("commit", "hole_radius"),
    [
        ("af36f97", 3.0),  # "converted the magnet hole stl files to mm"
        ("de4e698", 3.1),  # its only code change sets the hole radius to 0.31 cm
    ],
)
def test_the_stand_in_reproduces_milestone_1(commit: str, hole_radius: float) -> None:
    tile = golden.run(commit, MILESTONE_ENTRY, ("tile",))["tile"]
    triangles = read_stl(milestone_1_stl(hole_radius))
    low_excess, high_excess = MEASURED_EXCESS
    assert low_excess <= mesh_volume(triangles) - tile.volume <= high_excess
    low, high = mesh_bounds(triangles)
    np.testing.assert_allclose(low, tile.bbox_min, atol=1e-3)
    np.testing.assert_allclose(high, tile.bbox_max, atol=1e-3)


def test_a_failure_the_script_catches_still_fails_the_run(monkeypatch: pytest.MonkeyPatch) -> None:
    # HEAD's run() catches every exception and reports it only in a message box.
    def broken(*_: object) -> None:
        raise RuntimeError("the stand-in broke")

    monkeypatch.setattr(fusion.SketchCircles, "addByCenterRadius", broken)
    source = golden.SOURCES["umss"]
    with pytest.raises(RuntimeError, match="reported a failure:\nFailed:\nTraceback"):
        golden.run(source.commit, source.entry, source.parts)


def test_the_golden_is_what_heads_script_builds_on_the_stand_in() -> None:
    source = golden.SOURCES["umss"]
    committed = golden.read("umss")
    assert committed.commit == history.resolve(source.commit)
    assert committed.entry == source.entry
    rebuilt = golden.run(source.commit, source.entry, source.parts)
    assert list(rebuilt) == list(committed.parts)
    for name, fp in rebuilt.items():
        assert not differences(fp, committed.parts[name]), name
