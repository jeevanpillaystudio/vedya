from abc import abstractmethod

import adsk.fusion
from ..libs.geometry_utils import create_sketch, extrude_profile_by_area


class Extrude:
    def __init__(self, height: float):
        self.height = height

    @abstractmethod
    def draw(self, sketch: adsk.fusion.Sketch):
        pass

    def run(self, component: adsk.fusion.Component):
        # create the sketch
        self.sketch = create_sketch(
            component=component, name="extrude-sketch", offset=self.plane_offset
        )

        # draw the thing: re blah blah about maths goes in here, e.g points, etc
        self.draw(sketch=self.sketch)

        # extrude
        self.extrude(component=component)

    def extrude(self, component: adsk.fusion.Component):
        # extrude
        extrude_profile_by_area(
            component=component,
            profiles=self.sketch.profiles,
            area=self.calculate_area(),
            extrude_height=self.thickness,
            name="draw-extrude",
            operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        )
