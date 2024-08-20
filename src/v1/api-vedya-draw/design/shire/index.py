"""
Functionality to generate the v1 of the Vedya design.

@NOTE
    The design is accompanied with a production of mandalic-looking slab of Huon Pine 
    wood sourced from Tasmania. The design is a result of a collaboration between Jeevan Pillay and
    Adam Brown, Gemma & team at Tasmania. This was a art installation prototype for the Shire festival
    held in Victoria, Melbourne over the dates 26th April to 28th April 2024.
    
    While the design has a "generative" design by nature; resulting in a unique design each time it is
    generated, we selected a single "seed" to generate the design for the art installation. The design
    was then fabricated using a CNC machine to produce the final product. The design was a 3D model
    that was then used to generate the G-code for the CNC machine.
"""

import adsk.core, adsk.fusion

from .lib import create_bg
from ...utils.lib import log


# def start_func(root_comp: adsk.fusion.Component):

#     log(f"DEBUG: Start execute function")
#     # create_bg(root_comp)


def start_func(root_comp: adsk.fusion.Component):
    """
    Function to generate the v1 of the Vedya design.

    @param root_comp: adsk.fusion.Component: The root component to generate the design.
    """
    log(f"DEBUG: Start execute function")
    create_bg(root_comp)
