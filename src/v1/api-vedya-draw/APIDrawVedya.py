import adsk.core, adsk.fusion, adsk.cam, traceback
from .utils.lib import (
    log,
    timer,
    create_seed,
)
from .core.context import FusionDesignContext
from .core.types import DesignType, FabricationType

from .design.shire.index import start_func


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

        # Call the function to generate the design
        start_func(root_component)

        # End
        log(f"DEBUG: End generation of the design")

    except Exception as e:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))

        log(f"ERROR: {e}")
