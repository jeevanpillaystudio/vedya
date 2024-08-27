# @NOTE assuming all elements are on xYConstructionPlane
from typing import List
import adsk.fusion, adsk.core

from .libs.component_utils import create_component
from .modifiers.boolean import Boolean
from .modifiers.extrude import Extrude
from ..utils import log
from .ownable_geometry import OwnableGeometry


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
    ):
        OwnableGeometry.__init__(
            self, children=children, parent=parent, center_x=center_x, center_y=center_y
        )
        Extrude.__init__(self, height=thickness)

        # to be removed
        self.boolean = boolean

    """
    @params component: adsk.fusion.Component - the component to run the
    geometry calculations on
    @returns None
    """

    # def run(self, component: adsk.fusion.Component) -> None:
    def run(self, component: adsk.fusion.Component) -> adsk.fusion.BRepBodies:
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
        bodies = Extrude.run(self, component)
        log(f"DEBUG: Created bodies {len(bodies)}")

        # Iterate every child of Boolean and draw it
        # if self.boolean is not None:
        #     tool_bodies = adsk.core.ObjectCollection.create()
        #     for i, geometry in enumerate(self.boolean.geometries):
        #         geometry_component = create_component(component, f"geometry-{i}")
        #         child_bodies: adsk.fusion.BRepBodies = geometry.run(geometry_component)
        #         log(f"DEBUG: Created child bodies {len(child_bodies)}")
        #         # for body in child_bodies:
        #         #     tool_bodies.add(body)
        #         # log(f"DEBUG: Created child bodies {len(child_bodies)}")
        #     # log(f"DEBUG: Created bodies {len(tool_bodies)}")

        return bodies

    def calculate_area(self) -> float:
        return sum([element.calculate_area() for element in self.children])
