import math
import adsk.core, adsk.fusion, adsk.cam, traceback
from .core.shapes import (
    calculate_three_point_rectangle_area,
    draw_astroid,
    draw_astroid_stroke,
    calculate_astroid_area,
    draw_circle,
    calculate_circle_area,
    calculate_rectangle_area,
    draw_rectangle,
    draw_rotated_rectangle,
    create_seed,
    draw_tesseract_projection,
)
from .core.utils import (
    DepthRepeat,
    combine_body,
    copy_body,
    create_array_random_unique_multiples,
    create_offset_plane,
    create_sketch,
    extrude_profile_by_area,
    component_exist,
    create_component,
    extrude_single_profile_by_area,
    extrude_thin_one,
    log,
    move_body,
    scale_body,
    timer,
    depth_repeat_iterator,
)
import random
from .core.context import DesignContext
from .core.types import DesignType, FabricationType
from .core.math.measurement import Measurement


@timer
def run(context):
    log(f"DEBUG: Start run function")
    ui = None
    try:
        # Create context runner
        context = DesignContext(
            app_context=adsk.core.Application.get(),
            design_type=DesignType.DIRECT,
            seed=create_seed(),
            fabrication_type=FabricationType.CNC_MILL,
        )

        # Get needed values
        ui = context.ui
        root_component = context.root_component

        # Running
        log(f"DEBUG: Start generation of the design")

    except Exception as e:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))

        log(f"ERROR: {e}")


def create_component_name(name: str):
    return f"{FabricationType.get_name(FabricationType.CNC_MILL).lower()}-{name}"
