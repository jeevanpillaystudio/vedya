"""A stand-in for Autodesk's `adsk` package, on build123d, to run Vedya's Fusion 360 scripts.

It has only the members the scripts call, and every length is in centimetres, as in
Fusion's API. `adsk.fusion` describes how its features behave.

    with adsk.installed():
        design = adsk.new_document()
        ...                           # import a script and call its run(context)

camelCase members are Fusion's; snake_case members are the stand-in's own.
"""

import sys
from collections.abc import Generator
from contextlib import contextmanager

from tools.legacy.adsk import cam, core, fusion

__all__ = ["cam", "core", "fusion", "installed", "new_document"]


@contextmanager
def installed() -> Generator[None, None, None]:
    """Make the stand-in the `adsk` package that `import adsk.core` finds, while the block
    runs; whatever was there before is put back after."""
    modules = {
        "adsk": sys.modules[__name__],
        "adsk.cam": cam,
        "adsk.core": core,
        "adsk.fusion": fusion,
    }
    saved = {name: sys.modules.get(name) for name in modules}
    sys.modules.update(modules)
    try:
        yield
    finally:
        for name, module in saved.items():
            if module is None:
                del sys.modules[name]
            else:
                sys.modules[name] = module


def new_document() -> fusion.Design:
    """Open an empty design as the application's active document, and return it."""
    design = fusion.Design()
    core.Application.get().open_product(design)
    return design
