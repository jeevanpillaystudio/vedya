import adsk.fusion

from ..geometry_utils import create_sketch, extrude_profile_by_area
from ..geometry.index import ModifiableGeometry
from .index import Modifier


class Extrude(Modifier):
    def __init__(self, extrude_height: float):
        self.extrude_height = extrude_height

    def apply(self, component: adsk.fusion.Component, geometry: ModifiableGeometry):
        # Create a new sketch
        sketch = create_sketch(component, "draw-geometry")

        # Draw the geometry and apply any previous modifiers
        profile = geometry.draw(sketch)
        profile = geometry.apply_modifiers(sketch, profile)

        # Perform the extrusion
        extrude_profile_by_area(
            component=component,
            profiles=[profile],
            area=geometry.calculate_area(),
            extrude_height=self.extrude_height,
            name="draw-extrude",
            operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        )

    def calculate_area(self, geometry: ModifiableGeometry):
        return geometry.calculate_area()
