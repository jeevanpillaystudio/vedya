import math
from core.geometry.composition_geometry import CompositionGeometry


class Circle(CompositionGeometry):
    # body
    radius: float
    thickness: float

    def __init__(
        self,
        thickness: float,
        radius: float,
        parent: CompositionGeometry = None,
        center_x: float = 0.0,
        center_y: float = 0.0,
    ):
        CompositionGeometry.__init__(
            self,
            parent=parent,
            children=None,
            center_x=center_x,
            center_y=center_y,
            thickness=thickness,
        )

        # body
        self.radius = radius

    # def draw(self, sketch: adsk.fusion.Sketch) -> adsk.fusion.SketchCircle:
    #     # Draw the base circle
    #     return sketch.sketchCurves.sketchCircles.addByCenterRadius(
    #         adsk.core.Point3D.create(self.center_x, self.center_y, 0), self.radius
    #     )

    def calculate_area(self) -> float:
        return math.pi * self.radius**2

    def __str__(self):
        return (
            f"Circle(radius={self.radius}, center=({self.center_x}, {self.center_y}))"
        )
