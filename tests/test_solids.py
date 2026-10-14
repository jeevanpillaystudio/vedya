"""Every solid the command line writes is clean: valid, and every edge on its curve.

That is each part and the aggregate of every registered design, and the layers the
aggregate is sliced into. Each is checked as OpenCascade checks a solid, and no face,
edge or vertex of it may be looser than `references.CLEAN`.
"""

import build123d as bd
import pytest

from references import CLEAN, RELATIVE, largest_tolerance
from vedya.designs import load_designs
from vedya.designs.umss import PART_NAMES as UMSS_PARTS
from vedya.designs.umss import UmssParams
from vedya.designs.umss import build as build_umss
from vedya.model import Model, aggregate, fingerprint, slice_layers

DESIGNS = list(load_designs())


def assert_clean(shape: bd.Part, label: str) -> None:
    assert shape.solids(), f"{label} is empty"
    assert shape.is_valid, f"{label} is not a valid solid"
    assert largest_tolerance(shape) <= CLEAN, f"{label}: tolerance {largest_tolerance(shape)}"


@pytest.mark.parametrize("design", DESIGNS)
def test_each_part_of_every_design_is_clean(models: dict[str, Model], design: str) -> None:
    for name, part in models[design].parts.items():
        assert_clean(part, f"{design} {name}")


@pytest.mark.parametrize("design", DESIGNS)
def test_the_aggregate_of_every_design_is_clean(
    aggregates: dict[str, bd.Part], design: str
) -> None:
    assert_clean(aggregates[design], f"{design} aggregate")


def test_every_umss_part_and_their_aggregate_are_clean() -> None:
    model = build_umss(UmssParams(parts=UMSS_PARTS))
    for name, part in model.parts.items():
        assert_clean(part, name)
    assert_clean(aggregate(model), "aggregate")


@pytest.fixture(scope="module")
def shire_layers(shire_aggregate: bd.Part) -> list[bd.Part]:
    """Shire's aggregate in layers of 3.2 mm, at most 12 cuts, as `vedya build shire
    --slice 3.2:12` writes it."""
    return slice_layers(shire_aggregate, 3.2, 12)


def test_shires_layers_are_clean(shire_layers: list[bd.Part]) -> None:
    # The board is 38.4 mm high, twelve layers, so the twelfth cut would fall at its top.
    assert len(shire_layers) == 12
    for i, layer in enumerate(shire_layers):
        assert_clean(layer, f"layer {i}")
        box = layer.bounding_box()
        span = (box.min.Z, box.max.Z)
        assert span == pytest.approx((3.2 * i, 3.2 * (i + 1)), abs=1e-6)


@pytest.mark.slow
def test_shires_layers_hold_the_aggregate(
    shire_layers: list[bd.Part], shire_aggregate: bd.Part
) -> None:
    total = sum(fingerprint(layer).volume for layer in shire_layers)
    assert total == pytest.approx(fingerprint(shire_aggregate).volume, rel=RELATIVE / 100)
