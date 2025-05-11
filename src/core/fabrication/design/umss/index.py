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
from ....geometry.composition_geometry import ArrayType
from ....geometry.modifiers.extrude import FullExtrude, ThinExtrude
from ....geometry.modifiers.boolean import Difference, Union
from ....geometry.shapes.circle import Circle
from ....geometry.shapes.rectangle import Rectangle
from ....geometry.composition import Composition


# geometry
from ....utils import log

# # fillets manufacture (upper/lower)
# # 1. 12.5 / 12.5
# # 2. 25 / 12.5


data = {
    "TILE_BASE": {
        "LENGTH": 3.20,
        "WIDTH": 3.20,
        "THICKNESS": 0.30,
        "PLANE_OFFSET": 0.0,
    },
    "MAGNET_HOLE": {"RADIUS": 0.31, "THICKNESS": 0.30, "PLANE_OFFSET": 0.0},
    "MAGNET_BASE": {
        "RADIUS": 0.31,
        "THICKNESS": 0.15,
        "PLANE_OFFSET": -0.25,
    },
    "MAGNET_BASE_RING": {
        "RADIUS": 0.31,
        "THICKNESS": 0.05,
        "STROKE_WEIGHT": 0.1,
        "PLANE_OFFSET": -0.05
    }
}


def start_func(root_comp: adsk.fusion.Component):
    """
    Function to generate the Parthenon from Greece

    @param root_comp: adsk.fusion.Component: The root component to generate the design.
    """
    # start
    log(f"DEBUG: Start execute function for {PROJECT_NAME}")

    TILE_DATA = data["TILE_BASE"]
    MAGNET_HOLE_DATA = data["MAGNET_HOLE"]
    MAGNET_BASE_DATA = data["MAGNET_BASE"]
    MAGNET_BASE_RING_DATA = data["MAGNET_BASE_RING"]

    composition = Composition(root_comp=root_comp, plane_offset=0.0)

    # top-level tile
    # composition.add_geometry(
    #     Rectangle(
    #         extrude=FullExtrude(
    #             thickness=TILE_DATA["THICKNESS"],
    #             plane_offset=TILE_DATA["PLANE_OFFSET"],
    #         ),
    #         array_type=ArrayType.SINGLE_AXIS,
    #         x_count=1,
    #         y_count=1,
    #         length=TILE_DATA["LENGTH"],
    #         width=TILE_DATA["WIDTH"],
    #         boolean=[
    #             Difference(
    #                 Circle(
    #                     extrude=FullExtrude(
    #                         thickness=MAGNET_HOLE_DATA["THICKNESS"],
    #                         plane_offset=MAGNET_HOLE_DATA["PLANE_OFFSET"],
    #                     ),
    #                     array_type=ArrayType.SINGLE_AXIS,
    #                     x_count=1,
    #                     y_count=1,
    #                     radius=MAGNET_HOLE_DATA["RADIUS"],
    #                 )
    #             ),
    #         ],
    #     )
    # )

    # # lower-level tile - magnet enclosure
    # composition.add_geometry(
    #     Circle(
    #         radius=MAGNET_BASE_RING_DATA["RADIUS"],
    #         extrude=ThinExtrude(
    #             thickness=MAGNET_BASE_RING_DATA["THICKNESS"],
    #             plane_offset=MAGNET_BASE_RING_DATA["PLANE_OFFSET"],
    #             stroke_weight=MAGNET_BASE_RING_DATA["STROKE_WEIGHT"],
    #             side=adsk.fusion.ThinExtrudeWallLocation.Side2,
    #         ),
    #         array_type=ArrayType.SINGLE_AXIS,
    #         x_count=1,
    #         y_count=1,
    #     #     boolean=[
    #     #         Union(
    #     #             Circle(
    #     #                 radius=MAGNET_BASE_DATA["RADIUS"],
    #     #                 extrude=FullExtrude(
    #     #                     thickness=MAGNET_BASE_DATA["THICKNESS"],
    #     #                     plane_offset=MAGNET_BASE_DATA["PLANE_OFFSET"],
    #     #                 ),
    #     #             ),
    #     #         ),
    #     #     ],
    #     )
    # )
    
    
    composition.add_geometry(
        Circle(
            radius=MAGNET_BASE_DATA["RADIUS"],
            extrude=FullExtrude(
                thickness=MAGNET_BASE_DATA["THICKNESS"],
                plane_offset=MAGNET_BASE_DATA["PLANE_OFFSET"],
            ),
        )
    )

    log(str(composition))

    # # create composition
    composition.create()
