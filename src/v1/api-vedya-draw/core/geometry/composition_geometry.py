# @NOTE assuming all elements are on xYConstructionPlane
from abc import abstractmethod
from typing import List
import adsk.fusion, adsk.core

from .modifiers.boolean import Boolean
from .modifiers.extrude import Extrude, Fillet
from .ownable_geometry import OwnableGeometry
from ..utils import log
        
class CompositionGeometry(OwnableGeometry):
    # body
    boolean: List[Boolean]  

    def __init__(
        self,
        extrude: Extrude,
        fillet: Fillet,
        parent: OwnableGeometry,
        children: List[OwnableGeometry],
        boolean: List[Boolean] = None,
        center_x: float = 0.0,
        center_y: float = 0.0,
    ):
        # init
        OwnableGeometry.__init__(
            self, children=children, parent=parent, center_x=center_x, center_y=center_y
        )

        # to be removed
        self.boolean = boolean
        self.extrude = extrude
        self.fillet = fillet
        
    def setup(self, component: adsk.fusion.Component):
        self.extrude.setup(component)
        self.fillet.setup(component)

    @abstractmethod
    def draw(self, sketch: adsk.fusion.Sketch) -> None:
        pass

    def run(self) -> adsk.fusion.BRepBody:
        initial_center_x = self.center_x
        initial_center_y = self.center_y

        for x in range(self.extrude.x_count):
            for y in range(self.extrude.y_count):
                self.center_x = x * self.xy_bound() + initial_center_x
                self.center_y = y * self.xy_bound() + initial_center_y
                body = self.extrude.run(draw_func=lambda sketch: self.draw(sketch))
                log(f"DEBUG: Created body {body.name}")

                # run boolean operation
                if self.boolean is not None:
                    for boolean in self.boolean:
                        for geometry in boolean.geometries:
                            geometry.setup(self.body_component)
                        geometry.center_x = self.center_x
                        geometry.center_y = self.center_y
                        child_bodies = geometry.run()
                        boolean.run(self.body_component, body, child_bodies)
                        
                self.extrude.fillet(body)

        # return the bodies
        return body

    def calculate_area(self) -> float:
        return sum([element.calculate_area() for element in self.children])

    @abstractmethod
    def xy_bound(self) -> float:
        pass