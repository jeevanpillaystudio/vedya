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
from ....geometry.modifiers.fillet import Fillet
from ....geometry.modifiers.extrude import FullExtrude, ThinExtrude
from ....geometry.modifiers.boolean import Difference, Union
from ....geometry.shapes.circle import Circle
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

# dimensions
# 1. tile
TILE_LENGTH = 30.0
TILE_WIDTH = 30.0
TILE_THICKNESS = 3.0

# 2. magnet
MAGNET_HOLE_RADIUS = 3.0  # 6mm / 2
MAGNET_BASE_THICKNESS = 3.0

# 3. magnet enclosure
MAGNET_ENCLOSURE_RADIUS = 3.0  # 8mm / 2
MAGNET_ENCLOSURE_THICKNESS = 1.0

# 3. fillet
FILLET_RADIUS = 1.5


def start_func(root_comp: adsk.fusion.Component):
    """
    Function to generate the Parthenon from Greece

    @param root_comp: adsk.fusion.Component: The root component to generate the design.
    """
    # start
    log(f"DEBUG: Start execute function for {PROJECT_NAME}")

    composition = Composition(root_comp=root_comp, plane_offset=0.0)
    # composition.add_geometry(
    #     Circle(
    #         radius=MAGNET_HOLE_RADIUS,
    #         extrude=ThinExtrude(
    #             thickness=MAGNET_BASE_THICKNESS / 2,
    #             plane_offset=-1.5,
    #             x_count=1,
    #             y_count=1,
    #             stroke_weight=1.0,
    #             side=adsk.fusion.ThinExtrudeWallLocation.Side2,
    #         ),
    #         # fillet=Fillet(radius=FILLET_RADIUS),
    #         boolean=[
    #             Union(
    #                 Rectangle(
    #                     extrude=FullExtrude(
    #                         thickness=TILE_THICKNESS,
    #                         plane_offset=0.0,
    #                         x_count=1,
    #                         y_count=1,
    #                     ),
    #                     fillet=Fillet(radius=FILLET_RADIUS),
    #                     length=TILE_LENGTH,
    #                     width=TILE_WIDTH,
    #                     boolean=[
    #                         Difference(
    #                             Circle(
    #                                 extrude=FullExtrude(
    #                                     thickness=MAGNET_BASE_THICKNESS,
    #                                     plane_offset=0.0,
    #                                     x_count=1,
    #                                     y_count=1,
    #                                 ),
    #                                 radius=MAGNET_HOLE_RADIUS,
    #                             )
    #                         )
    #                     ],
    #                 ),
    #                 Circle(
    #                     extrude=FullExtrude(
    #                         thickness=MAGNET_ENCLOSURE_THICKNESS,
    #                         plane_offset=-1.5,
    #                         x_count=1,
    #                         y_count=1,
    #                     ),
    #                     radius=MAGNET_ENCLOSURE_RADIUS,
    #                 ),
    #             )
    #         ],
    #     )
    # )

    composition.add_geometry(
        Rectangle(
            extrude=FullExtrude(
                thickness=TILE_THICKNESS,
                plane_offset=0.0,
                x_count=1,
                y_count=1,
            ),
            fillet=Fillet(radius=FILLET_RADIUS),
            length=TILE_LENGTH,
            width=TILE_WIDTH,
            boolean=[
                Difference(
                    Circle(
                        extrude=FullExtrude(
                            thickness=MAGNET_BASE_THICKNESS,
                            plane_offset=0.0,
                            x_count=1,
                            y_count=1,
                        ),
                        fillet=Fillet(radius=FILLET_RADIUS),
                        radius=MAGNET_HOLE_RADIUS,
                    )
                ),
                Union(
                    Circle(
                        radius=MAGNET_HOLE_RADIUS,
                        extrude=ThinExtrude(
                            thickness=MAGNET_BASE_THICKNESS / 2,
                            plane_offset=-1.5,
                            x_count=1,
                            y_count=1,
                            stroke_weight=1.0,
                            side=adsk.fusion.ThinExtrudeWallLocation.Side2,
                        ),
                    )
                ),
                Union(
                    Circle(
                        extrude=FullExtrude(
                            thickness=MAGNET_ENCLOSURE_THICKNESS,
                            plane_offset=-1.5,
                            x_count=1,
                            y_count=1,
                        ),
                        radius=MAGNET_ENCLOSURE_RADIUS,
                    ),
                ),
            ],
        )
    )

    log(str(composition))

    # # create composition
    composition.create()
