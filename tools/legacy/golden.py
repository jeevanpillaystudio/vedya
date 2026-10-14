"""The goldens: what the original Fusion 360 scripts built, run on the stand-in.

    make golden                              # rewrite every file in tests/golden/
    uv run python -m tools.legacy.golden umss

`run` writes a script's files at a commit to a temporary folder, imports its entry point
with the stand-in as `adsk`, and calls `run(context)` as Fusion did. It then joins the
bodies under each top-level component, in the order the script made the components,
scales them from Fusion's centimetres to millimetres, and fingerprints each. A script that
joins its whole design into one body, as the aggregator at a36cc3c does, leaves that body
in the root component; it is fingerprinted as the design's aggregate.

Some scripts name components with random suffixes, so a golden is keyed by build order:
each design's `Source` gives the part name of each top-level component in turn.
"""

import argparse
import builtins
import importlib
import importlib.machinery
import importlib.util
import io
import json
import logging
import random
import sys
import tempfile
from collections.abc import Callable, Generator, Sequence
from contextlib import contextmanager, redirect_stdout
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path, PurePosixPath
from types import ModuleType
from typing import Any
from unittest import mock

from tools.legacy import adsk, history, prisms
from tools.legacy.adsk import core, fusion
from tools.legacy.prisms import Stack
from vedya.model import Fingerprint

__all__ = [
    "GOLDEN_DIR",
    "MM_PER_CM",
    "SOURCES",
    "Built",
    "Golden",
    "Source",
    "read",
    "run",
    "scripts",
    "stacks",
]

log = logging.getLogger("tools.legacy.golden")

GOLDEN_DIR = history.REPOSITORY / "tests" / "golden"
"""Where the goldens are written, one JSON file per design."""

MM_PER_CM = 10.0
"""Fusion's API measures in centimetres, and the goldens in millimetres."""


@dataclass(frozen=True)
class Source:
    """Where a design's golden comes from.

    Attributes:
        design: The design's name, and its golden's file name in `GOLDEN_DIR`.
        commit: The commit whose script is run.
        entry: The script's entry point at that commit, from the repository's root.
        parts: The part name of each top-level component that holds bodies, in the order
            the script makes them.
        aggregate: Whether the script joins its whole design into the root component.
    """

    design: str
    commit: str
    entry: str
    parts: tuple[str, ...]
    aggregate: bool = False


SOURCES: dict[str, Source] = {
    source.design: source
    for source in (
        # HEAD's script builds only UMSS's magnet base, in one component.
        Source("umss", "08f31da", "src/APIDrawVedya.py", ("magnet-base",)),
        # The last Shire that imports builds eight components, then its aggregator joins a
        # copy of every body in the root, in a ninth component that is left with no body.
        # Its kailash cut and in-bounds intersect raise a TypeError, which the script
        # catches, before they make a component.
        Source(
            "shire",
            "a36cc3c",
            "src/v1/api-vedya-draw/APIDrawVedya.py",
            ("bg", "border", "layer-0", "layer-2", "layer-1", "core", "torus", "middle-ring"),
            aggregate=True,
        ),
    )
}
"""Every design with a golden, by name."""


@dataclass(frozen=True)
class Built[T]:
    """What a script built: each part, and the whole design where the script joined it.

    Attributes:
        parts: Each part, by name, in build order.
        aggregate: The one body the script joined its whole design into, or None.
    """

    parts: dict[str, T]
    aggregate: T | None = None


@dataclass(frozen=True)
class Golden:
    """A golden as read from its file.

    Attributes:
        design: The design's name.
        commit: The full hash of the commit whose script was run.
        entry: The script's entry point at that commit.
        build123d: The version of build123d the stand-in ran on.
        parts: Each part's fingerprint, in millimetres, in build order.
        aggregate: The fingerprint of the body the script joined its design into, or None.
    """

    design: str
    commit: str
    entry: str
    build123d: str
    parts: dict[str, Fingerprint]
    aggregate: Fingerprint | None


def stacks(commit: str, entry: str, parts: Sequence[str], aggregate: bool = False) -> Built[Stack]:
    """What the script `entry` at `commit` builds, in millimetres: the union of the bodies
    under each top-level component that holds any, named by `parts` in the order the
    script made the components, and, if `aggregate`, the body it leaves in the root.

    Raises `RuntimeError` when the script reports a failure, and `ValueError` when what it
    built does not have the parts given, or leaves bodies in the root unless `aggregate`.
    """
    full = history.resolve(commit)
    folder = PurePosixPath(entry).parent.as_posix()
    output = io.StringIO()
    with (
        scripts(full, folder) as load,
        _random_state_kept(),
        _writes_refused(),
        redirect_stdout(output),
    ):
        design = adsk.new_document()
        load(PurePosixPath(entry).stem).run(None)
        messages = core.Application.get().userInterface.messages
    if output.getvalue():
        log.debug("the script printed:\n%s", output.getvalue())
    if messages:
        raise RuntimeError("the script reported a failure:\n" + "\n".join(messages))
    groups, own = _bodies(design.rootComponent)
    if len(groups) != len(parts):
        raise ValueError(
            f"{entry} at {commit} built {len(groups)} top-level components with bodies, "
            f"but {len(parts)} part names were given"
        )
    if own and not aggregate:
        raise ValueError("the script left bodies in the root component, outside every part")
    if aggregate and not own:
        raise ValueError("the script left no body in the root component to be its aggregate")
    return Built(
        parts={name: _in_mm(_union(bodies)) for name, bodies in zip(parts, groups, strict=True)},
        aggregate=_in_mm(_union(own)) if own else None,
    )


def run(
    commit: str, entry: str, parts: Sequence[str], aggregate: bool = False
) -> Built[Fingerprint]:
    """The fingerprints of what `stacks` gives for the same arguments."""
    built = stacks(commit, entry, parts, aggregate)
    return Built(
        parts={name: stack.fingerprint() for name, stack in built.parts.items()},
        aggregate=None if built.aggregate is None else built.aggregate.fingerprint(),
    )


@contextmanager
def scripts(commit: str, folder: str) -> Generator[Callable[[str], ModuleType], None, None]:
    """While the block runs, the Python files under `folder` at `commit` import as one
    package, with the stand-in as `adsk`.

    Yields a function that imports a module of the package by its dotted name within
    `folder`, such as `core.geometry.astroid`. Every module is forgotten after the block.
    """
    full = history.resolve(commit)
    files = [path for path in history.files(full, folder) if path.endswith(".py")]
    package = f"_vedya_legacy_{full}"
    with tempfile.TemporaryDirectory(prefix="vedya-legacy-") as temp:
        root = history.materialise(full, files, Path(temp))
        spec = importlib.machinery.ModuleSpec(package, None, is_package=True)
        spec.submodule_search_locations = [str(root.joinpath(*PurePosixPath(folder).parts))]
        with adsk.installed(), _imported_as(package, importlib.util.module_from_spec(spec)):
            yield lambda name: importlib.import_module(f"{package}.{name}")


def write(source: Source, built: Built[Fingerprint]) -> Path:
    """Write `built` as the golden of `source.design`, and return the file's path."""
    data: dict[str, object] = {
        "design": source.design,
        "source": {"commit": history.resolve(source.commit), "entry": source.entry},
        "build123d": version("build123d"),
        "units": "mm",
        "parts": {name: _encode(fp) for name, fp in built.parts.items()},
    }
    if built.aggregate is not None:
        data["aggregate"] = _encode(built.aggregate)
    path = GOLDEN_DIR / f"{source.design}.json"
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")
    return path


def read(design: str) -> Golden:
    """The golden of `design`, from `GOLDEN_DIR`."""
    data = json.loads((GOLDEN_DIR / f"{design}.json").read_text(encoding="utf-8"))
    if data["units"] != "mm":
        raise ValueError(f"the {design} golden is in {data['units']}, not mm")
    return Golden(
        design=data["design"],
        commit=data["source"]["commit"],
        entry=data["source"]["entry"],
        build123d=data["build123d"],
        parts={name: _decode(values) for name, values in data["parts"].items()},
        aggregate=_decode(data["aggregate"]) if "aggregate" in data else None,
    )


@contextmanager
def _imported_as(package: str, module: Any) -> Generator[None, None, None]:
    """Register `module` as `package` while the block runs, and forget it and every module
    imported under it after."""
    sys.modules[package] = module
    try:
        yield
    finally:
        for name in [name for name in sys.modules if name.partition(".")[0] == package]:
            del sys.modules[name]


@contextmanager
def _random_state_kept() -> Generator[None, None, None]:
    """Put back the random generator's state after the block; the scripts reseed it."""
    state = random.getstate()
    try:
        yield
    finally:
        random.setstate(state)


@contextmanager
def _writes_refused() -> Generator[None, None, None]:
    """Refuse every file the block opens for writing.

    The scripts append a log to a fixed path on the author's machine. They catch the
    refusal themselves, so a run writes no file.
    """
    real_open: Callable[..., Any] = builtins.open

    def read_only(file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
        if any(flag in mode for flag in "wax+"):
            raise PermissionError(f"the stand-in does not let the script write {file}")
        return real_open(file, mode, *args, **kwargs)

    with mock.patch("builtins.open", read_only):
        yield


def _bodies(
    root: fusion.Component,
) -> tuple[list[list[fusion.BRepBody]], list[fusion.BRepBody]]:
    """The bodies under each of `root`'s components that holds any, in the order they were
    made, and the bodies in `root` itself.

    A component with no bodies is not a part: the aggregator at a36cc3c makes one to hold
    its combine feature, and the joined body stays in the root, where its copies were made.
    """
    groups = [
        bodies for occurrence in root.occurrences if (bodies := occurrence.component.all_bodies())
    ]
    if not groups:
        raise ValueError("the script built nothing")
    return groups, list(root.bRepBodies)


def _union(bodies: list[fusion.BRepBody]) -> Stack:
    return prisms.union([body.shape for body in bodies])


def _in_mm(stack: Stack) -> Stack:
    return stack.scaled(MM_PER_CM)


# A golden keeps what the stand-in measures reliably: volumes and areas to ten significant
# figures (the integrals are good to 1e-9), lengths to the nearest nanometre.
_FIGURES = 10
_LENGTH_DIGITS = 6


def _significant(value: float) -> float:
    return float(f"{value:.{_FIGURES}g}") + 0.0


def _length(value: float) -> float:
    return round(value, _LENGTH_DIGITS) + 0.0


def _encode(fp: Fingerprint) -> dict[str, object]:
    return {
        "volume": _significant(fp.volume),
        "area": _significant(fp.area),
        "bbox_min": [_length(v) for v in fp.bbox_min],
        "bbox_max": [_length(v) for v in fp.bbox_max],
        "centroid": [_length(v) for v in fp.centroid],
    }


def _decode(values: dict[str, Any]) -> Fingerprint:
    def vec(key: str) -> tuple[float, float, float]:
        x, y, z = (float(v) for v in values[key])
        return (x, y, z)

    return Fingerprint(
        volume=float(values["volume"]),
        area=float(values["area"]),
        bbox_min=vec("bbox_min"),
        bbox_max=vec("bbox_max"),
        centroid=vec("centroid"),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Rewrite the goldens of the designs named in `argv`, or of every design."""
    parser = argparse.ArgumentParser(
        prog="python -m tools.legacy.golden",
        description="Run the original Fusion 360 scripts on the stand-in and rewrite "
        "tests/golden/<design>.json.",
    )
    parser.add_argument("designs", nargs="*", help=f"from {', '.join(SOURCES)}; default all")
    parser.add_argument("-v", "--verbose", action="store_true", help="show what scripts print")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(message)s")
    names: list[str] = list(args.designs) or list(SOURCES)
    unknown = [name for name in names if name not in SOURCES]
    if unknown:
        parser.error(f"no golden for {', '.join(unknown)}; the designs are {', '.join(SOURCES)}")
    for name in names:
        source = SOURCES[name]
        built = run(source.commit, source.entry, source.parts, source.aggregate)
        path = write(source, built)
        log.info(
            "wrote %s from %s at %s",
            path.relative_to(history.REPOSITORY),
            source.entry,
            source.commit,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
