from abc import abstractmethod
import uuid

import adsk.fusion
from ..libs.component_utils import create_component
from ..libs.geometry_utils import create_sketch, extrude_profile_by_area


class Extrude:
    def __init__(self, thickness: float, plane_offset: float):
        self.thickness = thickness
        self.plane_offset = plane_offset
        self.parent_component = None
        self.body_component = None
        
    def setup(self, parent_component: adsk.fusion.Component):
        self.parent_component = parent_component
        self.body_component = create_component(self.parent_component, f"extrude-component-{uuid.uuid4()}")

    @abstractmethod
    def draw(self, sketch: adsk.fusion.Sketch):
        pass

    def run(self) -> adsk.fusion.BRepBodies:
        # create the sketch
        self.sketch = create_sketch(
            component=self.body_component,
            name="extrude-sketch",
            offset=self.plane_offset,
        )

        # draw the thing: re blah blah about maths goes in here, e.g points, etc
        self.draw(sketch=self.sketch)

        # extrude
        return self.extrude()

    def extrude(self) -> adsk.fusion.BRepBodies:
        # extrude
        return extrude_profile_by_area(
            component=self.body_component,
            profiles=self.sketch.profiles,
            area=self.calculate_area(),
            extrude_height=self.thickness,
            name="draw-extrude",
            operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        )

    @property
    def plane_offset(self):
        return self._plane_offset

    @plane_offset.setter
    def plane_offset(self, plane_offset: float):
        self._plane_offset = plane_offset
