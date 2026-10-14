"""Fixtures shared across test files.

Shire takes about 12 seconds to build, and its aggregate about 7 more, so each design is
built once per session for every test that reads it. No test changes them: a
fingerprint, a section, a slice and an aggregate leave their shapes as they were.
"""

import build123d as bd
import pytest

from vedya.designs import load_designs
from vedya.designs.shire import ShireParams, _layer_0
from vedya.model import Model, aggregate


@pytest.fixture(scope="session")
def models() -> dict[str, Model]:
    """Every registered design, by name, as its default parameters build it."""
    return {name: design.build(design.params()) for name, design in load_designs().items()}


@pytest.fixture(scope="session")
def aggregates(models: dict[str, Model]) -> dict[str, bd.Part]:
    """Every registered design's parts joined into one, by the design's name."""
    return {name: aggregate(model) for name, model in models.items()}


@pytest.fixture(scope="session")
def shire(models: dict[str, Model]) -> Model:
    """Shire as its default parameters build it."""
    return models["shire"]


@pytest.fixture(scope="session")
def shire_aggregate(aggregates: dict[str, bd.Part]) -> bd.Part:
    """Every part of Shire joined into one."""
    return aggregates["shire"]


@pytest.fixture(scope="session")
def shire_unclipped(shire: Model) -> Model:
    """Shire as the 2024 script built it, `ShireParams(clip_to_board=False)`: its layer-0
    overhangs the board's long sides. This is what the goldens and the stand-in pin.

    `clip_to_board` changes only layer-0, so the other parts are the default build's, not
    built again. Were another part to change with it, the tests that hold this model to
    the goldens would fail.
    """
    layer_0 = _layer_0(ShireParams(clip_to_board=False))
    return Model(
        {name: layer_0 if name == "layer-0" else part for name, part in shire.parts.items()}
    )


@pytest.fixture(scope="session")
def shire_unclipped_aggregate(shire_unclipped: Model) -> bd.Part:
    """Every part of the 2024 Shire joined into one."""
    return aggregate(shire_unclipped)
