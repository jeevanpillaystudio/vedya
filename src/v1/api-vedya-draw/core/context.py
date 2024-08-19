import adsk.core
import random
from .types import FabricationType, DesignType
from ..utils.lib import log


class DesignContext:
    def __init__(
        self,
        app_context: adsk.core.Application,
        design_type: adsk.fusion.DesignTypes,
        seed: int,
        fabrication_type: FabricationType,
    ):
        # Set the context
        self._app_context = app_context

        # Set the fabrication type
        self.fabrication_type = fabrication_type

        # Set the design type
        self._design = self._app_context.activeProduct
        self._design.designType = design_type

        log(
            f"DEBUG: DesignContext: design_type:{self._design.designType}, fabrication_type:{FabricationType.get_name(self.fabrication_type)}, seed:{seed}"
        )

        # Post-set
        self.validate_design_mode()
        self.set_seed(seed)

    def set_seed(self, seed: int):
        random.seed(seed)

    def validate_design_mode(self):
        if self._design.designType != DesignType.DIRECT:
            raise Exception(
                "It is not supported in the current workspace. Please switch to the DIRECT-DESIGN workspace and try again."
            )

    @property
    def ui(self) -> adsk.core.UserInterface:
        return self._app_context.userInterface

    @property
    def root_component(self) -> adsk.fusion.Component:
        return self._design.rootComponent
