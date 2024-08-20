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

PROJECT_NAME = "parthenon"

import adsk.core, adsk.fusion
from ...utils.lib import log


def start_func(root_comp: adsk.fusion.Component):
    """
    Function to generate the Parthenon from Greece

    @param root_comp: adsk.fusion.Component: The root component to generate the design.
    """
    # start
    log(f"DEBUG: Start execute function for {PROJECT_NAME}")
