"""Models, the aggregate of their parts, and the fingerprint of a known solid."""

import math

import build123d as bd
import pytest

from vedya.geometry import circle, slab
from vedya.model import Model, aggregate, fingerprint


def box(x: float, y: float, z: float, at: tuple[float, float, float] = (0.0, 0.0, 0.0)) -> bd.Part:
    """A box of the given size whose low corner is at `at`."""
    return bd.Pos(*at) * bd.Box(x, y, z, align=bd.Align.MIN)


def test_fingerprint_of_a_known_box() -> None:
    fp = fingerprint(box(10.0, 20.0, 30.0, at=(1.0, 2.0, 3.0)))
    assert fp.volume == pytest.approx(10.0 * 20.0 * 30.0, rel=1e-12)
    assert fp.area == pytest.approx(2 * (10.0 * 20.0 + 20.0 * 30.0 + 10.0 * 30.0), rel=1e-12)
    assert fp.bbox_min == (1.0, 2.0, 3.0)
    assert fp.bbox_max == (11.0, 22.0, 33.0)
    assert fp.centroid == pytest.approx((6.0, 12.0, 18.0), abs=1e-12)


def test_fingerprint_of_a_cylinder() -> None:
    fp = fingerprint(slab(circle(3.1), -2.5, 1.5))
    assert fp.volume == pytest.approx(math.pi * 3.1**2 * 1.5, rel=1e-12)
    assert fp.area == pytest.approx(2 * math.pi * 3.1**2 + 2 * math.pi * 3.1 * 1.5, rel=1e-12)
    assert fp.centroid == pytest.approx((0.0, 0.0, -1.75), abs=1e-12)


def test_a_flat_shape_has_no_volume_and_takes_its_area_centroid() -> None:
    fp = fingerprint(circle(1.0, at=(4.0, 0.0)) + circle(1.0, at=(-2.0, 0.0)))
    assert fp.volume == 0.0
    assert fp.area == pytest.approx(2 * math.pi, rel=1e-12)
    assert fp.centroid == pytest.approx((1.0, 0.0, 0.0), abs=1e-12)


def test_fingerprint_refuses_an_empty_shape() -> None:
    with pytest.raises(ValueError, match="empty"):
        fingerprint(bd.Part())


def test_model_keeps_its_parts_in_build_order() -> None:
    model = Model({"top": box(1, 1, 1), "base": box(1, 1, 1), "middle-ring": box(1, 1, 1)})
    assert list(model.parts) == ["top", "base", "middle-ring"]


def test_model_cannot_change_once_built() -> None:
    parts = {"base": box(1, 1, 1)}
    model = Model(parts)
    parts["late"] = box(1, 1, 1)
    assert list(model.parts) == ["base"]
    with pytest.raises(TypeError):
        model.parts["late"] = box(1, 1, 1)  # pyright: ignore[reportIndexIssue]


@pytest.mark.parametrize("name", ["", "Base", "middle ring", "layer_0", "-edge", "a/b"])
def test_part_names_are_lowercase_words_joined_by_hyphens(name: str) -> None:
    with pytest.raises(ValueError, match="part name"):
        Model({name: box(1, 1, 1)})


def test_model_needs_a_part() -> None:
    with pytest.raises(ValueError, match="at least one part"):
        Model({})


def test_aggregate_fuses_overlapping_parts() -> None:
    model = Model({"a": box(2, 2, 2), "b": box(2, 2, 2, at=(1.0, 0.0, 0.0))})
    union = aggregate(model)
    assert fingerprint(union).volume == pytest.approx(12.0, rel=1e-12)
    assert len(union.solids()) == 1


def test_aggregate_keeps_separate_parts_apart() -> None:
    model = Model({"a": box(1, 1, 1), "b": box(1, 1, 1, at=(5.0, 0.0, 0.0))})
    union = aggregate(model)
    assert isinstance(union, bd.Part)
    assert fingerprint(union).volume == pytest.approx(2.0, rel=1e-12)
    assert len(union.solids()) == 2


def test_aggregate_of_one_part_is_that_part() -> None:
    part = box(1, 2, 3)
    assert fingerprint(aggregate(Model({"only": part}))) == fingerprint(part)
