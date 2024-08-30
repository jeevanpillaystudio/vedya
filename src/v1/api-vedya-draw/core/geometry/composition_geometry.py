# @NOTE assuming all elements are on xYConstructionPlane
from abc import abstractmethod
from typing import List
import adsk.fusion, adsk.core

from .modifiers.boolean import Boolean
from .modifiers.extrude import Extrude
from .ownable_geometry import OwnableGeometry
from ..utils import log
        
class CompositionGeometry(OwnableGeometry, Extrude):
    # body
    boolean: Boolean

    def __init__(
        self,
        parent: OwnableGeometry,
        children: List[OwnableGeometry],
        boolean: Boolean = None,
        center_x: float = 0.0,
        center_y: float = 0.0,
        thickness: float = 0.0,
        plane_offset: float = 0.0,
        count_x: int = 1,
        count_y: int = 1,
    ):
        OwnableGeometry.__init__(
            self, children=children, parent=parent, center_x=center_x, center_y=center_y
        )
        Extrude.__init__(self, thickness=thickness, plane_offset=plane_offset, x_count=count_x, y_count=count_y)

        # to be removed
        self.boolean = boolean

    # def run(self, component: adsk.fusion.Component) -> None:
    def run(self) -> adsk.fusion.BRepBodies:
        # # run array looper
        # for geometry in self.children:
        #     for x in range(self.count_x):
        #         for y in range(self.count_y):
        #             """
        #             RUN ACTIONS

        #             @NOTE: this is where we run the extrude and modify actions
        #             also, can extend to include other actions like cut, boolean, etc.
        #             """
        #             log(f"DEBUG: Running geometry {geometry}, x={x}, y={y}")
        #             Extrude.run(component)
        #             # Modifiers.run(component)
        initial_center_x = self.center_x
        initial_center_y = self.center_y

        for x in range(self.x_count):
            for y in range(self.y_count):
                self.center_x = x * self.xy_bound() + initial_center_x
                self.center_y = y * self.xy_bound() + initial_center_y
                bodies = Extrude.run(self)
                log(f"DEBUG: Created bodies {len(bodies)}")

                # run boolean operation
                if self.boolean is not None:
                    for geometry in self.boolean.geometries:
                        geometry.setup(self.body_component)
                        geometry.center_x = self.center_x
                        geometry.center_y = self.center_y
                        child_bodies = geometry.run()
                    self.boolean.run(self.body_component, bodies, child_bodies)

        # return the bodies
        return bodies

    def calculate_area(self) -> float:
        return sum([element.calculate_area() for element in self.children])

    @abstractmethod
    def xy_bound(self) -> float:
        pass