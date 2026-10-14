"""Every solid the command line writes is clean: valid, and every edge on its curve.

That is each part and the aggregate of every registered design. Each is checked as
OpenCascade checks a solid, and no face, edge or vertex of it may be looser than
`references.CLEAN`.
"""

import build123d as bd
import pytest

from references import CLEAN, largest_tolerance
from vedya.designs import load_designs
from vedya.designs.umss import PART_NAMES as UMSS_PARTS
from vedya.designs.umss import UmssParams
from vedya.designs.umss import build as build_umss
from vedya.model import Model, aggregate

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
