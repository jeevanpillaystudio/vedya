"""Fixtures shared across test files.

Shire takes about 20 seconds to build, and its aggregate about 10 more, so each is built
once per session for every test that reads it. No test changes them: a fingerprint, a
section and an aggregate leave their shapes as they were.
"""

import build123d as bd
import pytest

from vedya.designs.shire import ShireParams, build
from vedya.model import Model, aggregate


@pytest.fixture(scope="session")
def shire() -> Model:
    """Shire as its default parameters build it."""
    return build(ShireParams())


@pytest.fixture(scope="session")
def shire_aggregate(shire: Model) -> bd.Part:
    """Every part of Shire fused into one."""
    return aggregate(shire)
