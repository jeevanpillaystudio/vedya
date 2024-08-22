import math
import adsk.core, adsk.fusion

from .index import ModifiableGeometry


class Circle(ModifiableGeometry):
    def __init__(
        self,
        extrude_height: float,
        radius: float,
        center_x: float = 0.0,
        center_y: float = 0.0,
    ):
        super().__init__(extrude_height)
        self.radius = radius
        self.center_x = center_x
        self.center_y = center_y

    def draw(self, sketch: adsk.fusion.Sketch):
        # Draw the base circle
        profile = self._draw_circle(sketch)

        # Apply modifiers
        # self.apply_modifiers(sketch)

        return profile

    def _draw_circle(self, sketch: adsk.fusion.Sketch) -> adsk.fusion.SketchCircle:
        circle = sketch.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(self.center_x, self.center_y, 0), self.radius
        )
        return sketch.profiles.item(sketch.profiles.count - 1)

    def calculate_area(self) -> float:
        return math.pi * self.radius**2

    def __str__(self):
        return (
            f"Circle(radius={self.radius}, center=({self.center_x}, {self.center_y}))"
        )


def calculate_circle_area(radius):
    return math.pi * radius**2
