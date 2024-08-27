"""
Funcitonality to generate a custom fork of Universal Modular Storage System (UMSS) based on
dimensions of 128mm x 128mm tiles.

@source https://www.printables.com/model/947943-umss-universal-modular-storage-system

@NOTE
    The UMSS is a modular storage system that is designed to be printed on a 3D printer.
    The original design is based on dimensions of 128mm x 128mm tiles. 
    
    The tiles are magnetised using CA007 (6x3mm) and CA008 (8x3mm) cylindrical magnets to
    allow for easy assembly and disassembly. Each tile comes as a female/male pair where
    the female tile (base) serves as the base and the male tile serves as the "lid". 
    
    This file focuses on the generation of the base tile (also the female). The design
    is based on a grid of 32x32 tiles.
@TODO
    - [ ] Vertical Stress-Load Analysis for CA007 and CA008
    - [ ] Generate the male tile (also the female) for testing
    - [ ] Tiles should be interlocked with each other using backets
"""

PROJECT_NAME = "UMSS"

import adsk.core, adsk.fusion
from ....geometry.shapes.rectangle import Rectangle

# from core.geometry.index import Composition
from ....geometry.composition import Composition

# from core.geometry.shapes.rectangle import Rectangle

# from core.geometry.composition_geometry import CompositionGeometry
# from core.fabrication.composition.index import Composition
# from core.geometry.action.modify.boolean import Difference, Union
# from core.geometry.circle import Circle
# from ...core.geometry.rectangle import Rectangle

# modifier
# from ...core.modifier.boolean import Difference, Union
# from ...core.modifier.array import Array

# geometry
from ....utils import log

MAGNET_BASE_THICKNESS = 1.5
MAGNET_HOLE_RADIUS = 2.9  # 5.8mm / 2; r.e we measured 5.8mm on the diameter


def start_func(root_comp: adsk.fusion.Component):
    """
    Function to generate the Parthenon from Greece

    @param root_comp: adsk.fusion.Component: The root component to generate the design.
    """
    # start
    log(f"DEBUG: Start execute function for {PROJECT_NAME}")

    composition = Composition(root_comp=root_comp, plane_offset=2.0)
    # composition.add_geometry(
    # Rectangle(
    #     length=32.0,
    #     width=32.0,
    #     thickness=3.0,
    #     center_x=0.0,
    #     center_y=0.0,
    # )
    # )

    # # create composition
    # composition.create(root_comp)
