import math
import random
import adsk.core, adsk.fusion, adsk.cam, traceback

from .core.geometry.astroid import (
    draw_astroid,
    draw_astroid_stroke,
    create_astroid_points,
    calculate_astroid_area,
)

from .core.geometry.circle import (
    draw_circle,
    calculate_circle_area,
)

from .core.geometry.rectangle import (
    draw_rectangle,
    draw_rotated_rectangle,
    calculate_rectangle_area,
    calculate_three_point_rectangle_area,
)

from .core.geometry.tesseract import (
    draw_tesseract_projection,
)


from .core.geometry_utils import (
    create_offset_plane,
    create_sketch,
    extrude_profile_by_area,
    extrude_single_profile_by_area,
    extrude_thin_one,
)
from .core.component_utils import (
    combine_body,
    copy_body,
    create_component,
    component_exist,
    move_body,
    scale_body,
)
from .core.depth_utils import (
    DepthRepeat,
    depth_repeat_iterator,
)
from .utils.lib import (
    log,
    timer,
    create_array_random_unique_multiples,
    create_seed,
    create_power_series_multiples,
)

from .core.context import FusionDesignContext
from .core.types import DesignType, FabricationType
from .math.measurement import Measurement


@timer
def run(context):
    log(f"DEBUG: Start run function")
    ui = None
    try:
        # Create context runner
        context = FusionDesignContext(
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
