import math
import adsk.core, adsk.fusion

from .index import ModifiableGeometry


class Circle(ModifiableGeometry):
    def __init__(
        self,
        thickness: float,
        radius: float,
        center_x: float = 0.0,
        center_y: float = 0.0,
        plane_offset: float = 0,
    ):
        super().__init__(thickness, plane_offset)
        self.radius = radius
        self.center_x = center_x
        self.center_y = center_y

    def draw(self):
        # Draw the base circle
        self._draw_circle(self.sketch)

        # Apply modifiers
        # self.apply_modifiers(sketch)

    def _draw_circle(self, sketch: adsk.fusion.Sketch) -> adsk.fusion.SketchCircle:
        return sketch.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(self.center_x, self.center_y, 0), self.radius
        )

    def calculate_area(self) -> float:
        return math.pi * self.radius**2

    def __str__(self):
        return (
            f"Circle(radius={self.radius}, center=({self.center_x}, {self.center_y}))"
        )

    def xyBound(self) -> adsk.core.Point3D:
        return adsk.core.Point3D.create(self.radius, self.radius, 0)
