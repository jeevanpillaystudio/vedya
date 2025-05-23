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
    
@TODO
    - [ ] create an "array" modifier; r.e this makes iterating over a grid of elements easier
    - [ ] create a "texture" modifier; r.e this implements things such as torus & seed of life
"""

PROJECT_NAME = "shire"

import adsk.core, adsk.fusion

from .lib import (
    create_bg,
    create_border,
    create_component_core,
    create_component_outer_diagonal_steps,
    create_component_seed_of_life_layer_0,
    create_component_seed_of_life_layer_1,
    create_component_seed_of_life_layer_2,
    create_intersect_only_in_bounds,
    create_kailash_terrain_cut,
    create_middle_cut,
    create_torus_astroid,
)
from ...utils import log


def start_func(root_comp: adsk.fusion.Component):
    """
    Function to generate the v1 of the Vedya design.

    @param root_comp: adsk.fusion.Component: The root component to generate the design.
    """
    # start
    log(f"DEBUG: Start execute function for {PROJECT_NAME}")

    # create the background
    log(f"INFO: create_bg function")
    create_bg(root_comp)

    # create the border
    log(f"INFO: create_border function")
    create_border(root_comp)

    # create seed of life layer 0 component
    log(f"INFO: create_seed_of_life_layer_0 function")
    create_component_seed_of_life_layer_0(root_comp)

    # create seed of life layer 2 component
    log(f"INFO: create_seed_of_life_layer_2 function")
    create_component_seed_of_life_layer_2(root_comp)

    # create seed of life layer 1 component
    log(f"INFO: create_seed_of_life_layer_1 function")
    create_component_seed_of_life_layer_1(root_comp)

    # create component core
    log(f"INFO: create_core function")
    create_component_core(root_comp)

    # create torus astroid
    log(f"INFO: create_torus_astroid function")
    create_torus_astroid(root_comp)

    # middle cut
    log(f"INFO: create_middle_cut function")
    create_middle_cut(root_comp)

    # kailash terrain
    # @TODO right now, there is no TERRAIN to cut as the AREA is hardcoded in config, and probably set to a different SCALE_FACTOR than the rest of the design
    log(f"INFO: create_kailash_terrain_cut function")
    create_kailash_terrain_cut(root_comp)

    # outer diagonal steps
    # log(f"INFO: create_component_outer_diagonal_steps function")
    # create_component_outer_diagonal_steps(root_comp)

    # intersect only in bounds
    log(f"INFO: Intersecting only in bounds")
    create_intersect_only_in_bounds(root_comp)

    # end
    log(f"DEBUG: End execute function for {PROJECT_NAME}")
