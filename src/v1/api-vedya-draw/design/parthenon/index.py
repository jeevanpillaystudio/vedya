"""
Funcitonality to generate Partenon from Greece

@NOTE
    The purpose of this script is to generate a generative model of the Parthenon from Greece 
    using basic geometric shapes such as columns and walls. The primary goal is to generalize 
    the process of constructing the Parthenon by breaking down its elements into manageable 
    components.

    We plan to decompose certain elements in Blender 4.2 LTS, utilizing tools such as Boolean 
    and Array modifiers. The intention is to adopt a more structured and generative approach 
    to the modeling process.
    
    The script aims to create a digital model of the Parthenon, using a generative approach 
    that relies on basic shapes like columns and walls. The process will involve using 
    Blender 4.2 LTS, particularly leveraging Boolean and Array modifiers to break down and 
    organize the elements of the Parthenon. The goal is to make the modeling process more 
    systematic and adaptable, likely allowing for variations and explorations of the structure 
    through generative techniques.
"""

PROJECT_NAME = "PARTHENON"

import adsk.core, adsk.fusion
from ...core.modifier.boolean import Difference
from ...core.geometry.circle import Circle

# from ...core.modifier.boolean import Intersect

# from ...core.geometry.circle import Circle
from ...core.geometry.rectangle import Rectangle

# from ...core.modifier.extrude import Extrude

# from ...core.modifier.boolean import Intersect
# from ...core.modifier.extrude import Extrude
from ...design.shire.composition import Composition, CompositionLayer
from ...utils.lib import log

WIDTH = 64.0
LENGTH = 96.0
DEPTH_PER_LAYER = 0.48


def start_func(root_comp: adsk.fusion.Component):
    """
    Function to generate the Parthenon from Greece

    @param root_comp: adsk.fusion.Component: The root component to generate the design.
    """
    # start
    log(f"DEBUG: Start execute function for {PROJECT_NAME}")

    # create composition layer
    background_layer = CompositionLayer(
        [
            Rectangle(
                width=WIDTH, length=LENGTH, extrude_height=DEPTH_PER_LAYER
            ).add_modifier(
                Difference(Circle(radius=LENGTH / 2, extrude_height=DEPTH_PER_LAYER))
            )
            # Circle(radius=LENGTH / 2, extrude_height=DEPTH_PER_LAYER),
        ]
    )

    # create composition
    composition = Composition(
        [
            background_layer,
        ]
    )

    # create composition
    composition.draw(root_comp)
