# Vedya

A generative design system for geometric patterns and modular parts, built for fabrication (CNC milling, 3D printing, laser cutting). Each design is Python over build123d, an open-source CAD library. The first designs, Shire and UMSS, are ports of a 2024 Fusion 360 script and are held to what it built. Every length is in millimetres.

Read `CONTEXT.md` for the domain words and `docs/adr/` for the decisions before changing geometry, the stand-in or the goldens.

## Build and check

- `uv sync --all-extras` installs everything, the extras included; `make sync` does the same from the lock file exactly.
- `make check` runs ruff, ruff format, pyright in strict mode and the fast tests. Run it before every commit. `make format` fixes what ruff can.
- `make slow` runs the slow tests: the 2024 scripts on the stand-in, the milestone-1 STLs, April against August, the new Shire against the stand-in, the toolpaths, and the 2024 library. Run it when a change touches geometry, a design, `tools/legacy/` or `tests/golden/`. It reads old commits, so it needs full history (`git fetch --unshallow` in a shallow clone).
- `uv run vedya build <design> --out out/` and `make designs` write files into `out/`, which git ignores.
- CI runs the lint job, the fast tests on Linux, macOS and Windows, and the slow tests. All must pass before a merge.

## Goldens

- `tests/golden/<design>.json` holds the fingerprint of each part of a ported design, and of the aggregate where the old script made one: what the 2024 Fusion 360 script built. `tools/legacy/golden.py` runs that script unchanged, from git history, on the stand-in in `tools/legacy/adsk/`. `SOURCES` in `golden.py` names each design's commit and entry point: UMSS from `08f31da`, Shire from `a36cc3c`.
- The fast tests hold every part to its golden: a relative 1e-6 in volume and area, and 0.001 mm in bounding box and centroid (`tests/references.py`). A tolerance changes only with a measured explanation of the difference.
- Regenerate with `make golden` only when the stand-in changes, and say in the commit why the numbers moved. Never regenerate to make a failing test pass: a design that no longer matches its golden has changed its geometry. When nothing in `tools/legacy/` changed, `make golden && git diff --exit-code tests/golden/` must print nothing.
- The stand-in's contract, the Fusion behaviour it reproduces, is at the top of `tools/legacy/adsk/fusion.py`; ADR 0002 says why the pin works this way, and ADR 0003 what it pins.
- The Fusion code lives only in history, at the tags `fusion/milled` (`57f2b02`), `fusion/shire-last` (`a36cc3c`) and `fusion/head` (`08f31da`). `tools/legacy/history.py` reads it by commit. Do not copy it back into the tree.

## Adding a design

A design is one module in `src/vedya/designs/`: a frozen dataclass of parameters with millimetre defaults, a `build(params) -> Model`, and `design = Design(name, params, build)`, registered under `[project.entry-points."vedya.designs"]` in `pyproject.toml`. Build regions with 2D booleans on the primitives in `vedya.geometry` and `vedya.patterns`, and join slabs with `vedya.model.union`. A new design has no golden; its tests pin it.

## Agent skills

### Issue tracker

Issues live in this repository's GitHub Issues, through the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

The five default labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `CONTEXT.md` and `docs/adr/` at the repository root. See `docs/agents/domain.md`.
