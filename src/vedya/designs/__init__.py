"""Designs, and how they are found.

A design is a frozen dataclass of parameters, whose defaults are in millimetres, and a
function from those parameters to a `Model`. A package makes one available by naming it
under the `vedya.designs` entry-point group; this package registers its own the same
way, in its `pyproject.toml`:

    [project.entry-points."vedya.designs"]
    umss = "vedya.designs.umss:design"
"""

from collections.abc import Callable
from dataclasses import dataclass
from importlib.metadata import entry_points
from typing import TYPE_CHECKING, Any

from vedya.model import Model

if TYPE_CHECKING:
    from _typeshed import DataclassInstance

__all__ = ["ENTRY_POINT_GROUP", "Design", "load_designs"]

ENTRY_POINT_GROUP = "vedya.designs"


@dataclass(frozen=True)
class Design[P: DataclassInstance]:
    """A named design: its parameter class, whose defaults build it as made, and its build.

    Attributes:
        name: The name the command line and the entry point use, such as `umss`.
        params: A frozen dataclass whose every field has a default.
        build: Builds the design's `Model` from an instance of `params`.
    """

    name: str
    params: type[P]
    build: Callable[[P], Model]


def load_designs() -> dict[str, Design[Any]]:
    """Every design registered under `ENTRY_POINT_GROUP`, by name, in name order.

    Raises `TypeError` for an entry point that does not load a `Design`, and `ValueError`
    when a design's name differs from its entry point's or two designs share a name.
    """
    designs: dict[str, Design[Any]] = {}
    for entry_point in sorted(entry_points(group=ENTRY_POINT_GROUP), key=lambda ep: ep.name):
        design = entry_point.load()
        if not isinstance(design, Design):
            raise TypeError(f"entry point {entry_point.value!r} does not load a vedya Design")
        if design.name != entry_point.name:
            raise ValueError(
                f"entry point {entry_point.name!r} loads a design named {design.name!r}"
            )
        if design.name in designs:
            raise ValueError(f"two designs are registered as {design.name!r}")
        designs[design.name] = design
    return designs
