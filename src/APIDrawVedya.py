import adsk.core, adsk.fusion, adsk.cam, traceback

from .core.utils import create_seed, log, timer
from .core.context import FusionDesignContext
from .core.types import DesignType, FabricationMode, FabricationType

# fabrication
# from .core.fabrication.slicer.index import start_slicer
# from .core.fabrication.aggregator.index import start_aggregator

# design
# from .design.shire.index import start_func
# from .design.parthenon.index import start_func
from .core.fabrication.design.umss.index import start_func


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
            fabrication_mode=FabricationMode.NORMAL,
        )

        # Get needed values
        ui = context.ui
        root_component = context.root_component

        # Running
        log(f"DEBUG: Start generation of the design")

        # Call the function to generate the design
        start_func(root_component)

        # # Call the function to slice the design
        # if context.fabrication_mode == FabricationMode.SLICER:
        #     context.set_design(DesignType.PARAMETRIC)
        #     start_slicer(
        #         component=root_component,
        #         sliced_layer_depth=1.28 / 4,
        #         sliced_layer_count=12,
        #     )
        # elif context.fabrication_mode == FabricationMode.AGGREGATOR:
        #     context.set_design(DesignType.PARAMETRIC)
        #     start_aggregator(
        #         component=root_component,
        #     )

        # End
        log(f"DEBUG: End generation of the design")

    except Exception as e:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))

        log(f"ERROR: {e}")
