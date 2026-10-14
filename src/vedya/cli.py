"""The `vedya` command: list the designs, and build one into files.

    vedya list
    vedya build umss --out out/
    vedya build umss --set parts=tile --set hole_radius=3.0 --format step --out out/m1

`build` writes each part as `<design>-<part>.<format>` and the fused design as
`<design>.<format>`. A `--set name=value` overrides one parameter: a number, a word, or
a comma-separated list of them for a tuple field.
"""

import dataclasses
import logging
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, get_args, get_origin, get_type_hints

import typer

from vedya.designs import Design, load_designs
from vedya.export import SUFFIXES, export
from vedya.model import aggregate

if TYPE_CHECKING:
    from _typeshed import DataclassInstance

__all__ = ["app"]

log = logging.getLogger("vedya")

app = typer.Typer(no_args_is_help=True, add_completion=False)


@app.callback()
def main(
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Report each step.")] = False,
) -> None:
    """Build Vedya's designs into files for fabrication. Every length is in millimetres."""
    logging.basicConfig(
        level=logging.INFO if verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )


@app.command("list")
def list_designs() -> None:
    """Name every design that can be built, with what it is."""
    for name, design in load_designs().items():
        doc = (design.params.__doc__ or "").strip()
        typer.echo(f"{name}\t{doc.splitlines()[0] if doc else ''}")


@app.command()
def build(
    design: Annotated[str, typer.Argument(help="The design to build, as `vedya list` names it.")],
    out: Annotated[Path, typer.Option(help="The folder to write into; made if missing.")],
    formats: Annotated[
        str, typer.Option("--format", help="Comma-separated formats to write.")
    ] = "stl,step",
    settings: Annotated[
        list[str] | None,
        typer.Option("--set", help="Override a parameter, as name=value. Repeatable."),
    ] = None,
) -> None:
    """Build DESIGN and write its parts and their union into OUT."""
    try:
        written = _build(design, out, formats, settings or [])
    except Exception as error:
        log.info("%s failed", design, exc_info=True)
        typer.echo(f"error: {error}", err=True)
        raise typer.Exit(1) from error
    for path in written:
        typer.echo(path)


def _build(name: str, out: Path, formats: str, settings: Sequence[str]) -> list[Path]:
    designs = load_designs()
    if name not in designs:
        raise ValueError(f"no design named {name!r}; the designs are {', '.join(designs)}")
    chosen: Design[Any] = designs[name]
    suffixes = _suffixes(formats)
    params = _apply_settings(chosen.params(), settings)
    log.info("building %s with %s", name, params)
    model = chosen.build(params)
    shapes = {f"{name}-{part}": shape for part, shape in model.parts.items()}
    shapes[name] = aggregate(model)
    out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for stem, shape in shapes.items():
        for suffix in suffixes:
            path = out / f"{stem}{suffix}"
            log.info("writing %s", path)
            export(shape, path)
            written.append(path)
    return written


def _suffixes(formats: str) -> list[str]:
    """The file suffixes for a comma-separated list of formats, such as `stl,step`."""
    known = ", ".join(suffix.lstrip(".") for suffix in SUFFIXES)
    names = [item.strip().lower().lstrip(".") for item in formats.split(",") if item.strip()]
    if not names:
        raise ValueError(f"choose at least one format from {known}")
    unknown = [name for name in names if f".{name}" not in SUFFIXES]
    if unknown:
        raise ValueError(f"cannot write {', '.join(unknown)}; the formats are {known}")
    return list(dict.fromkeys(f".{name}" for name in names))


def _apply_settings[P: DataclassInstance](params: P, settings: Sequence[str]) -> P:
    """`params` with each `name=value` in `settings` applied, typed as the field is typed.

    Raises `ValueError` for a setting without `=`, a name the parameters lack, a value
    that does not parse, and a field whose type is not a number, a word, or a tuple of
    those.
    """
    hints = get_type_hints(type(params))
    names = [field.name for field in dataclasses.fields(params)]
    changes: dict[str, object] = {}
    for setting in settings:
        name, equals, text = setting.partition("=")
        name = name.strip()
        if not equals:
            raise ValueError(f"--set {setting!r} must be written name=value")
        if name not in names:
            raise ValueError(
                f"--set {name}: {type(params).__name__} has no such parameter; "
                f"it has {', '.join(names)}"
            )
        try:
            changes[name] = _parse(text, hints[name])
        except ValueError as error:
            raise ValueError(f"--set {name}: {error}") from error
    return dataclasses.replace(params, **changes)


def _parse_bool(text: str) -> bool:
    match text.strip().lower():
        case "true" | "yes" | "1":
            return True
        case "false" | "no" | "0":
            return False
        case _:
            raise ValueError(f"{text!r} is not true or false")


_SCALARS: dict[object, Callable[[str], object]] = {
    bool: _parse_bool,
    float: float,
    int: int,
    str: str.strip,
}


def _parse(text: str, annotation: object) -> object:
    """`text` as a value of the type `annotation`: a scalar, or a tuple of scalars."""
    if annotation in _SCALARS:
        return _SCALARS[annotation](text)
    args: tuple[object, ...] = get_args(annotation)
    if get_origin(annotation) is tuple and args:
        items = text.split(",")
        if len(args) == 2 and args[1] is Ellipsis:
            kinds = [args[0]] * len(items)
        elif len(items) == len(args):
            kinds = list(args)
        else:
            raise ValueError(f"expected {len(args)} comma-separated values, not {len(items)}")
        if all(kind in _SCALARS for kind in kinds):
            return tuple(_SCALARS[kind](item) for kind, item in zip(kinds, items, strict=True))
    raise ValueError(
        "only numbers, words and comma-separated lists of them can be set here, "
        f"not {getattr(annotation, '__name__', annotation)}"
    )
