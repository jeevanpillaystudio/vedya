"""The stencil, against the outputs the 2024 library left, and the point-cloud figure."""

import hashlib
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import pytest
from typer.testing import CliRunner

from tools.legacy import history
from vedya.cli import app
from vedya.render import COLOURS, Image, point_cloud_figure, read_image, stencil, write_image

runner = CliRunner()

STENCIL = Path(__file__).parent.parent / "public" / "stencil"
SOLDIER = STENCIL / "roman-soldier-cc.png"
"""The stencil's example input: a lithograph of a helmeted bust, 2481 by 3508 pixels."""

COMMITTED = STENCIL / "stencil_output.png"
"""The stencil output the 2024 library kept beside its input."""

STENCIL_SHA256 = "4d3b1840dec69f4ba3db9021b6f4b34a39dc10bf750ba6da37fcfb8d5347ce14"
"""The SHA-256 of the example's stencil: its pixels, row by row, a byte each."""

DRAFTED_AT = "e659e88"
"""The commit that added the committed stencil output, and the code that wrote the
stencil this port reproduces."""


def read_grey(path: Path) -> Image:
    """The image at `path`, as the levels it was saved with."""
    image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    assert image is not None, path
    return np.asarray(image, dtype=np.uint8)


def digest(image: Image) -> str:
    return hashlib.sha256(np.ascontiguousarray(image).tobytes()).hexdigest()


@pytest.fixture(scope="module")
def soldier() -> Image:
    return stencil(read_image(SOLDIER))


def test_the_stencil_of_the_example_against_the_committed_output(soldier: Image) -> None:
    """The stencil of `roman-soldier-cc.png` is not pixel-identical to the committed
    `stencil_output.png`.

    Measured with OpenCV 5.0.0: of its 8,703,348 pixels, 3508 rows of 2481, 7,746,606
    differ, and the largest difference is 255, black against white. The committed file is white
    on black, and the stencil black on white.

    The committed file is a draft. It is exactly the inverted Gaussian adaptive threshold
    of the grey image over 11 pixels with an offset of 2, with no outlines and no last
    inversion, as the next test checks. The code committed beside it, at `e659e88`, takes
    5 pixels and an offset of 12, adds the outlines, inverts, and wrote its output to the
    repository's root, not beside the input; that file, deleted in `c175195`, is this
    stencil pixel for pixel, as the slow test below checks.

    So this test holds the difference to what was measured, and the stencil to the hash
    of its pixels.
    """
    assert soldier.shape == (3508, 2481)
    assert soldier.dtype == np.uint8
    assert set(np.unique(soldier).tolist()) == {0, 255}
    committed = read_grey(COMMITTED)
    assert int(np.count_nonzero(soldier != committed)) == 7_746_606
    assert int(np.abs(soldier.astype(np.int16) - committed).max()) == 255
    assert digest(soldier) == STENCIL_SHA256


def test_the_committed_output_is_a_draft_of_the_threshold_alone() -> None:
    grey = cv2.cvtColor(read_image(SOLDIER), cv2.COLOR_BGR2GRAY)
    threshold = cv2.adaptiveThreshold(
        grey, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, blockSize=11, C=2
    )
    np.testing.assert_array_equal(read_grey(COMMITTED), cv2.bitwise_not(threshold))


@pytest.mark.slow
def test_the_stencil_is_what_the_2024_code_wrote(tmp_path: Path, soldier: Image) -> None:
    history.materialise(DRAFTED_AT, ["stencil_output.png"], tmp_path)
    np.testing.assert_array_equal(soldier, read_grey(tmp_path / "stencil_output.png"))


def square_on_white() -> Image:
    """A white image 64 pixels square, with a black square 20 pixels a side in the middle."""
    image = np.full((64, 64), 255, dtype=np.uint8)
    image[22:42, 22:42] = 0
    return image


def test_a_stencil_marks_outlines_black_on_white() -> None:
    marked = stencil(square_on_white())
    assert set(np.unique(marked).tolist()) == {0, 255}
    # Away from the square's edge, inside it and out, nothing is marked.
    assert (marked[:16, :] == 255).all()
    assert (marked[28:36, 28:36] == 255).all()
    # Along its edge, every row and column of it is marked.
    assert (marked[22:42, 18:26] == 0).any(axis=1).all()
    assert (marked[18:26, 22:42] == 0).any(axis=0).all()


def test_a_grey_image_and_its_colour_copy_give_one_stencil() -> None:
    grey = np.asarray(cv2.GaussianBlur(square_on_white(), (9, 9), 0), dtype=np.uint8)
    colour = np.stack([grey, grey, grey], axis=-1)
    np.testing.assert_array_equal(stencil(grey), stencil(colour))


def test_the_values_the_2024_code_fixed_are_defaults_that_can_change() -> None:
    image = square_on_white()
    assert (stencil(image) == stencil(image, blur=5, edges=(100, 180), block_size=5)).all()
    assert (stencil(image, block_size=3) != stencil(image, block_size=15)).any()


@pytest.mark.parametrize(
    ("image", "options", "message"),
    [
        (np.zeros((4, 4), np.float64), {}, "8-bit grey or blue-green-red"),
        (np.zeros((4, 4, 4), np.uint8), {}, "8-bit grey or blue-green-red"),
        (np.zeros((4, 4), np.uint8), {"blur": 4}, "blur must be an odd number"),
        (np.zeros((4, 4), np.uint8), {"block_size": 1}, "block_size must be an odd number"),
        (np.zeros((4, 4), np.uint8), {"block_size": 6}, "block_size must be an odd number"),
    ],
)
def test_an_impossible_stencil_is_refused(
    image: Image, options: dict[str, Any], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        stencil(image, **options)


def test_images_are_read_in_colour_and_written_by_suffix(tmp_path: Path) -> None:
    grey = square_on_white()
    write_image(grey, tmp_path / "square.png")
    read = read_image(tmp_path / "square.png")
    assert read.shape == (64, 64, 3)
    np.testing.assert_array_equal(read[..., 1], grey)
    with pytest.raises(FileNotFoundError, match="no such file"):
        read_image(tmp_path / "missing.png")
    (tmp_path / "words.png").write_text("not an image", encoding="utf-8")
    with pytest.raises(ValueError, match=r"cannot read 'words\.png' as an image"):
        read_image(tmp_path / "words.png")
    with pytest.raises(ValueError, match="no writer"):
        write_image(grey, tmp_path / "square.stl")
    with pytest.raises(FileNotFoundError, match="no such folder"):
        write_image(grey, tmp_path / "missing" / "square.png")


def test_the_command_writes_the_examples_stencil(tmp_path: Path) -> None:
    out = tmp_path / "out" / "stencil.png"
    result = runner.invoke(app, ["stencil", str(SOLDIER), "--out", str(out)])
    assert result.exit_code == 0, result.output
    assert result.stdout.splitlines() == [str(out)]
    assert digest(read_grey(out)) == STENCIL_SHA256


def test_the_command_reports_a_missing_image_in_one_line(tmp_path: Path) -> None:
    out = tmp_path / "out" / "stencil.png"
    result = runner.invoke(app, ["stencil", str(tmp_path / "none.png"), "--out", str(out)])
    assert result.exit_code == 1
    assert result.stderr.startswith("error: no such file: ")
    assert len(result.stderr.splitlines()) == 1
    assert not out.parent.exists()


def test_the_figure_shows_each_cloud_in_its_own_colour() -> None:
    clouds = {"Rectangle": np.zeros((5, 3)), "Circle": np.ones((2, 3)), "Third": np.ones((1, 3))}
    figure = point_cloud_figure(clouds, radius=2.0, z_range=(0.0, 4.0), title="Points")
    # plotly's objects are untyped; read them as a dictionary, and the points from the
    # traces, which the dictionary holds encoded.
    drawn: dict[str, Any] = figure.to_dict()
    traces = drawn["data"]
    assert [trace["type"] for trace in traces] == ["scatter3d"] * 3
    assert [trace["name"] for trace in traces] == ["Rectangle", "Circle", "Third"]
    assert [trace["marker"]["color"] for trace in traces] == list(COLOURS[:3])
    assert {trace["mode"] for trace in traces} == {"markers"}
    shown: Any = figure.data
    for trace, cloud in zip(shown, clouds.values(), strict=True):
        np.testing.assert_array_equal(np.stack([trace.x, trace.y, trace.z], axis=-1), cloud)
    scene = drawn["layout"]["scene"]
    assert scene["xaxis"]["range"] == scene["yaxis"]["range"] == [-3.0, 3.0]
    assert scene["zaxis"]["range"] == [0.0, 4.0]
    assert scene["aspectmode"] == "manual"
    assert drawn["layout"]["title"]["text"] == "Points"


def test_a_cloud_must_be_points_in_space() -> None:
    with pytest.raises(ValueError, match="cloud 'flat' must be rows of"):
        point_cloud_figure({"flat": np.zeros((3, 2))}, radius=1.0, z_range=(0.0, 1.0))


@pytest.mark.parametrize(
    ("surface", "title", "z_range"),
    [
        ("cylinder", "Cylinder with Filled Circle", "[0.0,4.0]"),
        # The 2024 code's note for a sphere: one unit past the radius each way.
        ("sphere", "Sphere with Filled Circle", "[-2.0,2.0]"),
    ],
)
def test_the_map_command_writes_the_figure(
    tmp_path: Path, surface: str, title: str, z_range: str
) -> None:
    out, page = tmp_path / "points.csv", tmp_path / "figure" / "points.html"
    result = runner.invoke(app, ["map", surface, "--out", str(out), "--figure", str(page)])
    assert result.exit_code == 0, result.output
    assert result.stdout.splitlines() == [str(out), str(page)]
    html = page.read_text(encoding="utf-8").replace(" ", "")
    assert title.replace(" ", "") in html
    assert '"name":"Rectangle"' in html
    assert '"name":"Circle"' in html
    assert f'"zaxis":{{"range":{z_range}}}' in html
