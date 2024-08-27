# @NOTE assuming all elements are on xYConstructionPlane
from typing import List

from .modifiers.extrude import Extrude
from ..utils import log
from .ownable_geometry import OwnableGeometry


class CompositionGeometry(OwnableGeometry, Extrude):
    def __init__(
        self,
        parent: OwnableGeometry,
        children: List[OwnableGeometry],
        center_x: float = 0,
        center_y: float = 0,
    ):
        OwnableGeometry.__init__(self, children=children, parent=parent, center_x=center_x, center_y=center_y)
        Extrude.__init__(self, height=1.0)

    """
    @params component: adsk.fusion.Component - the component to run the
    geometry calculations on
    @returns None
    """
    # def run(self, component: adsk.fusion.Component) -> None:
    def run(self) -> None:
        # run array looper
        for geometry in self.children:
            for x in range(self.count_x):
                for y in range(self.count_y):
                    """
                    RUN ACTIONS
                    
                    @NOTE: this is where we run the extrude and modify actions
                    also, can extend to include other actions like cut, boolean, etc.
                    """
                    log(f"DEBUG: Running geometry {geometry}, x={x}, y={y}")
                    # Extrude.run(component)
                    # Modifiers.run(component)

    def calculate_area(self) -> float:
        return sum([element.calculate_area() for element in self.children])
