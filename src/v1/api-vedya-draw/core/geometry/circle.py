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

    def draw(self) -> adsk.fusion.SketchCircle:
        if self.sketch is None:
            raise ValueError("Sketch is not initialized")

        # Draw the base circle
        return self.sketch.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(self.center_x, self.center_y, 0), self.radius
        )

    @property
    def center_x(self):
        return self._center_x

    @center_x.setter
    def center_x(self, center_x: float):
        self._center_x = center_x

    @property
    def center_y(self):
        return self._center_y

    @center_y.setter
    def center_y(self, center_y: float):
        self._center_y = center_y

    def calculate_area(self) -> float:
        return math.pi * self.radius**2

    def __str__(self):
        return (
            f"Circle(radius={self.radius}, center=({self.center_x}, {self.center_y}))"
        )

    def xyBound(self) -> adsk.core.Point3D:
        return adsk.core.Point3D.create(self.radius, self.radius, 0)
