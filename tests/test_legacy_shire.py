"""The stand-in runs Shire's scripts, and the new Shire agrees with what they build.

The golden comes from a36cc3c, the last Shire that imports, in August 2024. The piece was
milled from 57f2b02, in April, whose flat script builds the same parts in the same order
and stops before any aggregator; the union of its parts is August's aggregate.

These tests read git history, and need a clone with every commit.
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import PurePosixPath
from types import ModuleType, SimpleNamespace
from typing import Any

import build123d as bd
import pytest

from references import differences
from tools.legacy import adsk, golden, history, prisms
from tools.legacy.adsk import core, fusion
from tools.legacy.prisms import Stack
from vedya.designs.shire import PART_NAMES
from vedya.model import Model

pytestmark = pytest.mark.slow

SOURCE = golden.SOURCES["shire"]

APRIL = ("57f2b02", "src/api-vedya-draw/APIDrawVedya.py")
"""The commit the piece was milled from, and its script."""

XOR_RELATIVE = 1e-6
"""The largest volume, relative to a part's, that the new part and the script's may not
share."""


@pytest.fixture(scope="module")
def stand_in() -> golden.Built[Stack]:
    return golden.stacks(SOURCE.commit, SOURCE.entry, SOURCE.parts, SOURCE.aggregate)


@pytest.fixture(scope="module")
def april() -> golden.Built[Stack]:
    # April's kailash cut, made from a component of its own, reaches no body; the script
    # catches the error, and the component stays empty.
    commit, entry = APRIL
    return golden.stacks(commit, entry, SOURCE.parts)


def test_the_golden_is_what_the_august_script_builds(stand_in: golden.Built[Stack]) -> None:
    committed = golden.read("shire")
    assert committed.commit == history.resolve(SOURCE.commit)
    assert committed.entry == SOURCE.entry
    assert list(stand_in.parts) == list(committed.parts)
    for name, stack in stand_in.parts.items():
        assert not differences(stack.fingerprint(), committed.parts[name]), name
    assert stand_in.aggregate is not None
    assert committed.aggregate is not None
    assert not differences(stand_in.aggregate.fingerprint(), committed.aggregate)


def test_the_aggregator_joins_every_part(stand_in: golden.Built[Stack]) -> None:
    assert stand_in.aggregate is not None
    union = prisms.union(list(stand_in.parts.values()))
    assert not differences(union.fingerprint(), stand_in.aggregate.fingerprint())


def xor_volume(a: Stack, b: Stack) -> float:
    """The volume that is in one of `a` and `b` and not in the other."""
    pieces = (prisms.cut(a, b), prisms.cut(b, a))
    return sum(piece.fingerprint().volume for piece in pieces if not piece.is_empty)


@pytest.mark.parametrize("name", PART_NAMES)
def test_each_new_part_fills_the_space_the_scripts_did(
    stand_in: golden.Built[Stack], shire: Model, name: str
) -> None:
    old = stand_in.parts[name]
    new = Stack.of_solid(shire.parts[name])
    assert xor_volume(new, old) < XOR_RELATIVE * old.fingerprint().volume


def test_the_new_aggregate_fills_the_space_the_aggregators_body_did(
    stand_in: golden.Built[Stack], shire_aggregate: bd.Part
) -> None:
    assert stand_in.aggregate is not None
    old = stand_in.aggregate
    new = Stack.of_solid(shire_aggregate)
    assert xor_volume(new, old) < XOR_RELATIVE * old.fingerprint().volume


def test_the_xor_volume_sees_a_part_a_thousandth_too_large(
    stand_in: golden.Built[Stack], shire: Model
) -> None:
    old = stand_in.parts["middle-ring"]
    larger = Stack.of_solid(shire.parts["middle-ring"]).scaled(1.001)
    assert xor_volume(larger, old) > 1000 * XOR_RELATIVE * old.fingerprint().volume


def test_april_builds_what_august_does(
    april: golden.Built[Stack], stand_in: golden.Built[Stack]
) -> None:
    # April joins each seed of life's seven rings into one body where August keeps them
    # apart; a leaf's mask less their union is the same either way.
    assert april.aggregate is None
    assert list(april.parts) == list(stand_in.parts)
    for name, stack in april.parts.items():
        assert not differences(stack.fingerprint(), stand_in.parts[name].fingerprint()), name


def test_april_and_august_give_equal_aggregates(
    april: golden.Built[Stack], stand_in: golden.Built[Stack]
) -> None:
    assert stand_in.aggregate is not None
    august = stand_in.aggregate
    union = prisms.union(list(april.parts.values()))
    assert not differences(union.fingerprint(), august.fingerprint())
    assert xor_volume(union, august) < XOR_RELATIVE * august.fingerprint().volume


# The twelve picks of a region by its area in a Shire run: the curves each sketch holds,
# drawn by the script's own functions, the area it computes, and its tolerance. The
# circle of 36 cm and the 16 cm of leeway are literals in the script's layer functions.


type Draw = Callable[[Any, fusion.Sketch], object]
"""Draws curves on a sketch with the script's modules, `m`."""


@dataclass(frozen=True)
class Pick:
    draw: Draw
    area: Callable[[Any], float]
    tolerance: float | None = None
    """None for the script's `FP_TOLERANCE`."""


def _rectangle(length: Callable[[Any], float], width: Callable[[Any], float]) -> Draw:
    return lambda m, sketch: m.rectangle.draw_rectangle(sketch, length(m), width(m))


def _diamond(half: Callable[[Any], float]) -> Draw:
    return lambda m, sketch: m.rectangle.draw_rotated_rectangle(sketch, half(m), half(m))


def _astroid(radius: Callable[[Any], float]) -> Draw:
    def draw(m: Any, sketch: fusion.Sketch) -> None:
        n, points = m.config.AstroidConfig.N, m.config.AstroidConfig.NumPoints
        m.astroid.draw_astroid(sketch, n, points, radius(m), radius(m))

    return draw


def _all(*draws: Draw) -> Draw:
    return lambda m, sketch: [draw(m, sketch) for draw in draws]


def _length(m: Any) -> float:
    return m.config.AppConfig.MaxLength


def _width(m: Any) -> float:
    return m.config.AppConfig.MaxWidth


def _outer(m: Any) -> float:
    return m.config.DiagonalRectangleConfig.OuterDiagonalRectangleWidth


def _middle(m: Any) -> float:
    return m.config.DiagonalRectangleConfig.MiddleDiagonalRectangleWidth


def _big(m: Any) -> float:
    return m.config.AstroidConfig.OuterAstroidRadius


def _small(m: Any) -> float:
    return m.config.AstroidConfig.InnerAstroidRadius


def _wall(m: Any) -> float:
    return m.config.AppConfig.StrokeWeight


def _circle_area(m: Any, radius: float) -> float:
    return m.circle.calculate_circle_area(radius)


def _rectangle_area(m: Any, length: float, width: float) -> float:
    return m.rectangle.calculate_rectangle_area(length, width)


def _diamond_area(m: Any, half: float) -> float:
    return m.rectangle.calculate_three_point_rectangle_area(half, half)


def _astroid_area(m: Any, radius: float) -> float:
    return m.astroid.calculate_astroid_area(radius)


def _draw_circle(radius: Callable[[Any], float]) -> Draw:
    return lambda m, sketch: m.circle.draw_circle(sketch, radius(m))


PICKS: dict[str, Pick] = {
    "bg": Pick(
        _rectangle(
            lambda m: m.config.BackgroundConfig.MaxLength,
            lambda m: m.config.BackgroundConfig.MaxWidth,
        ),
        lambda m: _rectangle_area(
            m, m.config.BackgroundConfig.MaxLength, m.config.BackgroundConfig.MaxWidth
        ),
    ),
    "layer-0 mask": Pick(
        _all(_draw_circle(lambda _: 36.0), _diamond(_outer)),
        lambda m: _circle_area(m, 36.0) - _diamond_area(m, _outer(m)),
    ),
    "layer-2 mask": Pick(
        _all(_rectangle(lambda _: 36.0 * 2 + 16.0, _width), _draw_circle(lambda _: 36.0)),
        lambda m: _rectangle_area(m, 36.0 * 2 + 16.0, _width(m)) - _circle_area(m, 36.0),
    ),
    "layer-2 frame": Pick(
        _all(
            _rectangle(lambda m: _length(m) * 2, lambda m: _width(m) * 2),
            _rectangle(_length, _width),
        ),
        lambda m: (
            _rectangle_area(m, _length(m) * 2, _width(m) * 2)
            - _rectangle_area(m, _length(m), _width(m))
        ),
    ),
    "layer-1 band": Pick(
        _all(_rectangle(_length, _width), _diamond(_outer), _diamond(_middle)),
        lambda m: _diamond_area(m, _outer(m)) - _diamond_area(m, _middle(m)),
    ),
    "core base": Pick(
        _all(_rectangle(_length, _width), _diamond(_outer)),
        lambda m: _rectangle_area(m, _width(m), _length(m)) - _diamond_area(m, _outer(m)),
    ),
    "core astroid, outer": Pick(_astroid(_big), lambda m: _astroid_area(m, _big(m)), 1.0),
    "core astroid, outer step": Pick(
        _astroid(lambda m: _big(m) - _wall(m)),
        lambda m: _astroid_area(m, _big(m) - _wall(m)),
        1.0,
    ),
    "core astroid, inner": Pick(_astroid(_small), lambda m: _astroid_area(m, _small(m)), 1.0),
    "core and torus astroid, inner step": Pick(
        _astroid(lambda m: _small(m) - _wall(m)),
        lambda m: _astroid_area(m, _small(m) - _wall(m)),
        1.0,
    ),
    "torus bracing": Pick(
        lambda m, sketch: m.astroid.draw_astroid_stroke(
            sketch,
            m.config.AstroidConfig.N,
            m.config.AstroidConfig.NumPoints,
            _small(m) - _wall(m),
            _small(m) - _wall(m),
            thickness=_wall(m),
        ),
        lambda m: (
            _astroid_area(m, _small(m) - _wall(m))
            - _astroid_area(m, _small(m) - _wall(m) - _wall(m))
        ),
        1.0,
    ),
    "middle hole": Pick(
        _draw_circle(lambda m: m.config.AppConfig.HoleRadius),
        lambda m: _circle_area(m, m.config.AppConfig.HoleRadius),
    ),
}


@dataclass(frozen=True)
class Resolved:
    """What one pick found: the area it sought, and the areas of the regions within its
    tolerance, in cm²."""

    target: float
    matches: list[float]


@pytest.fixture(scope="module")
def resolved() -> dict[str, Resolved]:
    """Every pick, drawn and measured on the stand-in with the script's own modules."""
    folder = PurePosixPath(SOURCE.entry).parent.as_posix()
    found: dict[str, Resolved] = {}
    with golden.scripts(SOURCE.commit, folder) as load:
        modules: dict[str, ModuleType] = {
            "config": load("design.shire.config"),
            "circle": load("core.geometry.circle"),
            "rectangle": load("core.geometry.rectangle"),
            "astroid": load("core.geometry.astroid"),
        }
        default = load("core.geometry_utils").FP_TOLERANCE
        m = SimpleNamespace(**modules)
        for name, pick in PICKS.items():
            root = adsk.new_document().rootComponent
            planes = root.constructionPlanes
            plane_input = planes.createInput()
            plane_input.setByOffset(root.xYConstructionPlane, core.ValueInput.createByReal(0.0))
            sketch = root.sketches.add(planes.add(plane_input))
            pick.draw(m, sketch)
            target = pick.area(m)
            tolerance = default if pick.tolerance is None else pick.tolerance
            areas = [profile.areaProperties().area for profile in sketch.profiles]
            found[name] = Resolved(target, [a for a in areas if abs(a - target) < tolerance])
    return found


@pytest.mark.parametrize("name", PICKS)
def test_each_area_pick_resolves_to_one_region(resolved: dict[str, Resolved], name: str) -> None:
    pick = resolved[name]
    assert len(pick.matches) == 1, f"{name}: {pick.matches} for {pick.target}"
