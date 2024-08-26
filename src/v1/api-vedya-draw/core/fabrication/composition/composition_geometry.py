# @NOTE assuming all elements are on xYConstructionPlane
from typing import List

from utils.lib import log

from ...geometry.geometry import OwnableGeometry
from ...geometry.action.create.extrude import Extrude
from ...geometry.action.modify.index import Modifier

import adsk.fusion, adsk.core


class CompositionGeometry(OwnableGeometry, Extrude, Modifiers):
    # body
    modifiers: List[Modifier] = []

    def __init__(
        self,
        children: OwnableGeometry,
        count_x: int = 1,
        count_y: int = 1,
    ):
        # init
        OwnableGeometry.__init__(self, children=children, parent=None)

        # @NOTE: this is a placeholder for the array modifier
        self.count_x = count_x
        self.count_y = count_y

    """
    @params component: adsk.fusion.Component - the component to run the
    geometry calculations on
    @returns None
    """

    def run(self, component: adsk.fusion.Component) -> None:
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
                    Extrude.run(component)
                    Modifiers.run(component)

    def calculate_area(self) -> float:
        return sum([element.calculate_area() for element in self.children])
