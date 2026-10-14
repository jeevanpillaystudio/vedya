"""The goldens: what the original Fusion 360 scripts built, run on the stand-in.

    make golden                              # rewrite every file in tests/golden/
    uv run python -m tools.legacy.golden umss

`run` writes a script's files at a commit to a temporary folder, imports its entry point
with the stand-in as `adsk`, and calls `run(context)` as Fusion did. It then fuses the
bodies under each top-level component, in the order the script made the components,
scales them from Fusion's centimetres to millimetres, and fingerprints each.

The scripts name components with random suffixes, so a golden is keyed by build order:
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
from typing import Any
from unittest import mock

import build123d as bd

from tools.legacy import adsk, history
from tools.legacy.adsk import core, fusion
from vedya.model import Fingerprint, fingerprint

__all__ = ["GOLDEN_DIR", "MM_PER_CM", "SOURCES", "Golden", "Source", "read", "run", "solids"]

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
        parts: The part name of each top-level component, in the order the script makes
            them.
    """

    design: str
    commit: str
    entry: str
    parts: tuple[str, ...]


SOURCES: dict[str, Source] = {
    source.design: source
    for source in (
        # HEAD's script builds only UMSS's magnet base, in one component.
        Source("umss", "08f31da", "src/APIDrawVedya.py", ("magnet-base",)),
    )
}
"""Every design with a golden, by name."""


@dataclass(frozen=True)
class Golden:
    """A golden as read from its file.

    Attributes:
        design: The design's name.
        commit: The full hash of the commit whose script was run.
        entry: The script's entry point at that commit.
        build123d: The version of build123d the stand-in ran on.
        parts: Each part's fingerprint, in millimetres, in build order.
    """

    design: str
    commit: str
    entry: str
    build123d: str
    parts: dict[str, Fingerprint]


def solids(commit: str, entry: str) -> list[bd.Part]:
    """What the script `entry` at `commit` builds: the union of the bodies under each
    top-level component, in millimetres, in the order the script made the components.

    Raises `RuntimeError` when the script reports a failure, and `ValueError` when it
    leaves a component with no bodies or bodies outside every component.
    """
    full = history.resolve(commit)
    folder = PurePosixPath(entry).parent
    scripts = [path for path in history.files(full, folder.as_posix()) if path.endswith(".py")]
    with tempfile.TemporaryDirectory(prefix="vedya-legacy-") as temp:
        root = history.materialise(full, scripts, Path(temp))
        design = _run_script(root.joinpath(*folder.parts), PurePosixPath(entry).stem, full)
        return [_in_mm(_union(bodies)) for bodies in _top_level_bodies(design.rootComponent)]


def run(commit: str, entry: str, parts: Sequence[str]) -> dict[str, Fingerprint]:
    """The fingerprint of each top-level component the script builds, named by `parts`."""
    built = solids(commit, entry)
    if len(built) != len(parts):
        raise ValueError(
            f"{entry} at {commit} built {len(built)} top-level components, "
            f"but {len(parts)} part names were given"
        )
    return {name: fingerprint(shape) for name, shape in zip(parts, built, strict=True)}


def write(source: Source, parts: dict[str, Fingerprint]) -> Path:
    """Write `parts` as the golden of `source.design`, and return the file's path."""
    data = {
        "design": source.design,
        "source": {"commit": history.resolve(source.commit), "entry": source.entry},
        "build123d": version("build123d"),
        "units": "mm",
        "parts": {name: _encode(fp) for name, fp in parts.items()},
    }
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
    )


def _run_script(folder: Path, module: str, commit: str) -> fusion.Design:
    """Import `module` from `folder` as a package's entry point, run it as Fusion would, and
    return the design it built."""
    package = f"_vedya_legacy_{commit}"
    spec = importlib.machinery.ModuleSpec(package, None, is_package=True)
    spec.submodule_search_locations = [str(folder)]
    output = io.StringIO()
    with (
        adsk.installed(),
        _imported_as(package, importlib.util.module_from_spec(spec)),
        _random_state_kept(),
        _writes_refused(),
        redirect_stdout(output),
    ):
        design = adsk.new_document()
        script = importlib.import_module(f"{package}.{module}")
        script.run(None)
        messages = core.Application.get().userInterface.messages
    if output.getvalue():
        log.debug("the script printed:\n%s", output.getvalue())
    if messages:
        raise RuntimeError("the script reported a failure:\n" + "\n".join(messages))
    return design


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


def _top_level_bodies(root: fusion.Component) -> list[list[fusion.BRepBody]]:
    """The bodies under each of `root`'s components, in the order they were made."""
    if root.bRepBodies.count:
        raise ValueError("the script left bodies in the root component, outside every part")
    groups: list[list[fusion.BRepBody]] = []
    for occurrence in root.occurrences:
        bodies = occurrence.component.reach()
        if not bodies:
            raise ValueError(f"component {occurrence.component.name!r} holds no bodies")
        groups.append(bodies)
    if not groups:
        raise ValueError("the script built nothing")
    return groups


def _union(bodies: list[fusion.BRepBody]) -> bd.Part:
    first, *rest = (body.shape for body in bodies)
    if not rest:
        return first
    fused = first + rest
    return fused if isinstance(fused, bd.Part) else bd.Part(fused.solids())


def _in_mm(part: bd.Part) -> bd.Part:
    return part.scale(MM_PER_CM, about=(0.0, 0.0, 0.0))


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
        path = write(source, run(source.commit, source.entry, source.parts))
        log.info(
            "wrote %s from %s at %s",
            path.relative_to(history.REPOSITORY),
            source.entry,
            source.commit,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
