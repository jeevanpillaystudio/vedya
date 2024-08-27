from abc import abstractmethod

import adsk.fusion
from ..libs.component_utils import create_component
from ..libs.geometry_utils import create_sketch, extrude_profile_by_area


class Extrude:
    def __init__(self, height: float, parent_component: adsk.fusion.Component):
        self.height = height
        self.parent_component = parent_component
        self.body_component = self.create_component(
            name="extrude-component"
        )  # @TODO: change this to a better name

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
            extrude_height=self.height,
            name="draw-extrude",
            operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        )

    def create_component(self, name: str) -> adsk.fusion.Component:
        return create_component(self.parent_component, name)
