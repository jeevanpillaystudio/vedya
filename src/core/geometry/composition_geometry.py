# @NOTE assuming all elements are on xYConstructionPlane
from abc import abstractmethod
import math
from typing import List
import uuid
import adsk.fusion, adsk.core

from .libs.component_utils import create_component
from .modifiers.boolean import Boolean
from .modifiers.extrude import Extrude
from .ownable_geometry import OwnableGeometry
from ..utils import log

class ArrayType:
    SINGLE_AXIS = 1
    DOUBLE_AXIS = 2
    RADIAL = 3
    
class CompositionGeometry(OwnableGeometry):
    # body
    boolean: List[Boolean]
    component: adsk.fusion.Component

    def __init__(
        self,
        extrude: Extrude,
        boolean: List[Boolean] = None,
        array_type: ArrayType = ArrayType.SINGLE_AXIS,
        center_x: float = 0.0,
        center_y: float = 0.0,
        x_count: int = 1,
        y_count: int = 1,
    ):
        # init
        OwnableGeometry.__init__(self, center_x=center_x, center_y=center_y)

        # to be removed
        self.boolean = boolean
        self.extrude = extrude
        self.array_type = array_type
        self.x_count = x_count
        self.y_count = y_count
        self.component = None
        
    def setup(self, component: adsk.fusion.Component):
        self.component = create_component(
            component, f"composition-component-{uuid.uuid4()}"
        )

    @abstractmethod
    def draw(self, sketch: adsk.fusion.Sketch) -> None:
        pass

    def run(self) -> adsk.fusion.BRepBodies:
        initial_center_x = self.center_x
        initial_center_y = self.center_y
        
        bodies = None
        
        if self.array_type == ArrayType.DOUBLE_AXIS or self.array_type == ArrayType.SINGLE_AXIS:
            for x in range(self.x_count):
                for y in range(self.y_count):
                    self.center_x = x * self.xy_bound() + initial_center_x
                    self.center_y = y * self.xy_bound() + initial_center_y
                    bodies = self.extrude.run(
                        draw_func=lambda sketch: self.draw(sketch), component=self.component
                    )

                    # run boolean operation
                    if self.boolean is not None:
                        for boolean in self.boolean:
                            for geometry in boolean.geometries:
                                geometry.setup(self.component)
                                geometry.center_x = self.center_x
                                geometry.center_y = self.center_y
                                child_bodies =geometry.run()
                                boolean.run(self.component, bodies, child_bodies)
                                
        elif self.array_type == ArrayType.RADIAL:
            for index in range(self.x_count):
                pos = math.pi * 2 / self.x_count * index
                self.center_x = math.cos(pos) * self.xy_bound() + initial_center_x
                self.center_y = math.sin(pos) * self.xy_bound() + initial_center_y
                bodies = self.extrude.run(
                    draw_func=lambda sketch: self.draw(sketch), component=self.component
                )

               # run boolean operation
                if self.boolean is not None:
                    for boolean in self.boolean:
                        for geometry in boolean.geometries:
                            geometry.setup(self.component)
                            geometry.center_x = self.center_x
                            geometry.center_y = self.center_y
                            child_bodies = geometry.run()
                            boolean.run(self.component, bodies, child_bodies)

        return bodies

    def calculate_area(self) -> float:
        return sum([element.calculate_area() for element in self.children])
    
    @abstractmethod
    def xy_bound(self) -> float:
        pass

