"""The `vedya` command: build the designs into files, and run the library's other tools.

    vedya list
    vedya build umss --out out/
    vedya build umss --set parts=tile --set hole_radius=3.0 --format step --out out/m1
    vedya build shire --aggregate --slice 3.2:12 --format stl,3mf --out out/sliced
    vedya map cylinder --out out/cylinder.csv --figure out/cylinder.html
    vedya stencil public/stencil/roman-soldier-cc.png --out out/stencil.png
    vedya flowfield --out out/flowfield.npy

`build` writes what its options choose, in each format `--format` names:

- `--parts`: each part, as `<design>-<part>.<format>`.
- `--aggregate`: the parts joined into one, as `<design>.<format>`.
- `--slice H:N`: the parts joined into one and cut into layers H mm high from the
  bottom up, at most N cuts, as `<design>-slice-<i>.<format>` from 0 at the bottom; the
  last is what is left above the last cut.

With none of them it writes the parts and the aggregate. A `--set name=value` overrides
one parameter: a number, a word, or a comma-separated list of them for a tuple field.

`map`, `stencil` and `flowfield` are the 2024 library's commands, and the values that
library fixed are their defaults. `map` writes the points a rectangle and a disc give on
a cylinder or a sphere, as CSV, and with `--figure` as a 3D figure; `stencil` writes an
image's stencil; `flowfield` writes a Perlin flow field as a NumPy array. `stencil` and
`--figure` need the `render` extra, and `flowfield` the `examples` extra.

Every command makes the folder it writes into, and reports a failure in one line.
"""

import csv
import dataclasses
import logging
from collections.abc import Callable, Generator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, get_args, get_origin, get_type_hints

import build123d as bd
import numpy as np
import typer

from vedya.designs import Design, load_designs
from vedya.export import SUFFIXES, export
from vedya.mapping import (
    Points,
    circle_samples,
    rectangle_samples,
    to_cylinder,
    to_sphere,
)
from vedya.model import aggregate, slice_layers

if TYPE_CHECKING:
    from _typeshed import DataclassInstance

__all__ = ["Surface", "app"]

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
    parts: Annotated[bool, typer.Option("--parts", help="Write each part.")] = False,
    whole: Annotated[
        bool, typer.Option("--aggregate", help="Write the parts joined into one.")
    ] = False,
    layers: Annotated[
        str | None,
        typer.Option(
            "--slice",
            metavar="H:N",
            help="Write the parts joined into one and cut into layers H mm high, from the "
            "bottom up, at most N cuts; the last file is what is left above them.",
        ),
    ] = None,
    formats: Annotated[
        str, typer.Option("--format", help="Comma-separated formats to write: stl, step, 3mf.")
    ] = "stl,step",
    settings: Annotated[
        list[str] | None,
        typer.Option("--set", help="Override a parameter, as name=value. Repeatable."),
    ] = None,
) -> None:
    """Build DESIGN and write into OUT what the options choose: by default, its parts and
    their union."""
    with _reported(design):
        written = _build(design, out, formats, settings or [], _Outputs(parts, whole, layers))
    for path in written:
        typer.echo(path)


class Surface(StrEnum):
    """The surfaces `map` wraps the plane onto."""

    CYLINDER = "cylinder"
    SPHERE = "sphere"


@app.command("map")
def map_points(
    surface: Annotated[Surface, typer.Argument(help="The surface to wrap the plane onto.")],
    out: Annotated[
        Path, typer.Option(help="The CSV file to write, a point a row: shape, x, y, z.")
    ],
    figure: Annotated[
        Path | None,
        typer.Option(help="Also write the points as a 3D figure, in HTML. Needs the render extra."),
    ] = None,
    length: Annotated[
        float, typer.Option(help="The rectangle's length, which goes once around.")
    ] = 10.0,
    height: Annotated[
        float, typer.Option(help="The rectangle's height; on a sphere, from pole to pole.")
    ] = 4.0,
    radius: Annotated[float, typer.Option(help="The cylinder's or the sphere's radius.")] = 1.0,
    resolution: Annotated[
        float, typer.Option(help="The rectangle's cell size, and twice the disc's ring spacing.")
    ] = 0.1,
    circle_radius: Annotated[float, typer.Option(help="The disc's radius.")] = 1.0,
    circle_height: Annotated[
        float, typer.Option(help="The height of the disc's centre, which is at x = 0.")
    ] = 2.0,
) -> None:
    """Wrap a rectangle's cells and a disc's rings onto SURFACE, and write the points to OUT."""
    with _reported("map"):
        flat = {
            "rectangle": rectangle_samples(length, height, resolution),
            "circle": circle_samples(circle_radius, resolution, centre=(0.0, circle_height)),
        }
        if surface is Surface.CYLINDER:
            clouds = {name: to_cylinder(points, length, radius) for name, points in flat.items()}
            z_range = (0.0, height)
        else:
            clouds = {
                name: to_sphere(points, length, height, radius) for name, points in flat.items()
            }
            z_range = (-radius - 1, radius + 1)
        page: tuple[Path, str] | None = None
        if figure is not None:
            from vedya.render import point_cloud_figure

            drawing = point_cloud_figure(
                {name.capitalize(): points for name, points in clouds.items()},
                radius=radius,
                z_range=z_range,
                title=f"{surface.value.capitalize()} with Filled Circle",
            )
            # The page carries plotly's script, so it opens with no network.
            page = (figure, drawing.to_html(include_plotlyjs=True))
        out.parent.mkdir(parents=True, exist_ok=True)
        _write_points(clouds, out)
        if page is not None:
            path, html = page
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(html, encoding="utf-8")
    typer.echo(out)
    if figure is not None:
        typer.echo(figure)


@app.command("stencil")
def stencil_image(
    image: Annotated[Path, typer.Argument(help="The image to make a stencil of.")],
    out: Annotated[
        Path, typer.Option(help="The image file to write, in the format its suffix names.")
    ],
    blur: Annotated[
        int, typer.Option(help="The size, in pixels, of the blur before edges are found.")
    ] = 5,
    edges: Annotated[
        tuple[float, float],
        typer.Option(metavar="LOW HIGH", help="Canny's thresholds for the outlines."),
    ] = (100.0, 180.0),
    block_size: Annotated[
        int, typer.Option(help="The size, in pixels, of the patch a stroke is darker than.")
    ] = 5,
    offset: Annotated[
        float, typer.Option(help="How many levels darker than its patch a stroke is.")
    ] = 12.0,
) -> None:
    """Write the stencil of IMAGE to OUT, black on white. Needs the render extra."""
    with _reported("stencil"):
        from vedya import render

        result = render.stencil(
            render.read_image(image), blur=blur, edges=edges, block_size=block_size, offset=offset
        )
        out.parent.mkdir(parents=True, exist_ok=True)
        render.write_image(result, out)
    typer.echo(out)


@app.command("flowfield")
def flowfield_array(
    out: Annotated[Path, typer.Option(help="The NumPy file to write, named with .npy.")],
    width: Annotated[int, typer.Option(help="Points across the grid.")] = 150,
    height: Annotated[int, typer.Option(help="Points up the grid.")] = 150,
    scale: Annotated[float, typer.Option(help="How far the noise moves per unit of grid.")] = 0.1,
    octaves: Annotated[int, typer.Option(help="Layers of noise, each finer than the last.")] = 6,
    persistence: Annotated[
        float, typer.Option(help="Each layer's weight, relative to the one before.")
    ] = 0.5,
    lacunarity: Annotated[
        float, typer.Option(help="How much finer each layer is than the one before.")
    ] = 2.0,
) -> None:
    """Write a Perlin flow field of unit vectors to OUT. Needs the examples extra."""
    with _reported("flowfield"):
        if out.suffix.lower() != ".npy":
            raise ValueError(f"--out {out.name!r}: the flow field is written as .npy")
        from vedya.flowfield import flow_field

        field = flow_field(width, height, scale, octaves, persistence, lacunarity)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("wb") as file:
            np.save(file, field)
    typer.echo(out)


@contextmanager
def _reported(what: str) -> Generator[None]:
    """Report any exception from the block in one line and exit with status 1; `-v` logs
    its traceback."""
    try:
        yield
    except Exception as error:
        log.info("%s failed", what, exc_info=True)
        typer.echo(f"error: {error}", err=True)
        raise typer.Exit(1) from error


def _write_points(clouds: Mapping[str, Points], path: Path) -> None:
    """Write each cloud's points to `path` as CSV rows of shape, x, y, z, under a header,
    every coordinate as Python writes the float, which reads back the same."""
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["shape", "x", "y", "z"])
        for name, points in clouds.items():
            writer.writerows([name, *row] for row in points.tolist())


@dataclass(frozen=True)
class _Outputs:
    """What `build` writes: the parts, their union, and the union in layers, as
    `HEIGHT:COUNT`."""

    parts: bool
    whole: bool
    layers: str | None


def _build(
    name: str, out: Path, formats: str, settings: Sequence[str], outputs: _Outputs
) -> list[Path]:
    designs = load_designs()
    if name not in designs:
        raise ValueError(f"no design named {name!r}; the designs are {', '.join(designs)}")
    chosen: Design[Any] = designs[name]
    suffixes = _suffixes(formats)
    params = _apply_settings(chosen.params(), settings)
    layers = _layers(outputs.layers) if outputs.layers is not None else None
    parts, whole = outputs.parts, outputs.whole
    if not (parts or whole or layers):
        parts = whole = True
    log.info("building %s with %s", name, params)
    model = chosen.build(params)
    shapes: dict[str, bd.Part] = {}
    if parts:
        shapes.update({f"{name}-{part}": shape for part, shape in model.parts.items()})
    if whole or layers:
        union = aggregate(model)
        if whole:
            shapes[name] = union
        if layers:
            cut = slice_layers(union, *layers)
            digits = len(str(len(cut) - 1))
            for i, layer in enumerate(cut):
                if layer.solids():
                    shapes[f"{name}-slice-{i:0{digits}d}"] = layer
                else:
                    log.warning("%s: layer %d holds nothing, so no file is written", name, i)
    out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for stem, shape in shapes.items():
        for suffix in suffixes:
            path = out / f"{stem}{suffix}"
            log.info("writing %s", path)
            export(shape, path)
            written.append(path)
    return written


def _layers(text: str) -> tuple[float, int]:
    """The layer height and the most cuts, from `HEIGHT:COUNT`, such as `3.2:12`."""
    height, colon, count = text.partition(":")
    try:
        if not colon:
            raise ValueError
        layer_height, max_count = float(height), int(count)
    except ValueError:
        raise ValueError(f"--slice {text!r} must be written HEIGHT:COUNT, such as 3.2:12") from None
    if not layer_height > 0 or max_count < 1:
        raise ValueError(f"--slice {text!r}: the height must be positive and the count at least 1")
    return layer_height, max_count


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
