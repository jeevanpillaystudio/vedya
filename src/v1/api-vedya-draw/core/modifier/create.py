import adsk.fusion

from ..geometry_utils import create_sketch, extrude_profile_by_area
from ..geometry.index import Geometry
from .index import Modifier


class Create(Modifier):
    def __init__(self, geometry: Geometry, extrude_height: float):
        self.geometry = geometry
        self.extrude_height = extrude_height

    def apply(self, component: adsk.fusion.Component):
        sketch = create_sketch(component, "draw-geometry")
        self.geometry.draw(sketch)
        extrude_profile_by_area(
            component=component,
            profiles=sketch.profiles,
            area=self.geometry.calculate_area(),
            extrude_height=self.extrude_height,
            name="draw-extrude",
            operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        )

    def calculate_area(self):
        return self.geometry.calculate_area()
