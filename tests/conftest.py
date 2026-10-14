"""Fixtures shared across test files.

Shire takes about 12 seconds to build, and its aggregate about 7 more, so each design is
built once per session for every test that reads it. No test changes them: a
fingerprint, a section, a slice and an aggregate leave their shapes as they were.
"""

import build123d as bd
import pytest

from vedya.designs import load_designs
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
