import math


from ..modifiers.extrude import Extrude
from ..modifiers.boolean import Boolean
from ..composition_geometry import CompositionGeometry
import adsk.fusion, adsk.core


class Circle(CompositionGeometry):
    # body
    radius: float

    def __init__(
        self,
        extrude: Extrude,
        radius: float,
        center_x: float = 0.0,
        center_y: float = 0.0,
        parent: CompositionGeometry = None,
        boolean: Boolean = None,
    ):
        CompositionGeometry.__init__(
            self,
            extrude=extrude,
            parent=parent,
            children=None,
            center_x=center_x,
            center_y=center_y,
            boolean=boolean,
        )

        # body
        self.radius = radius

    def draw(self, sketch: adsk.fusion.Sketch) -> adsk.fusion.SketchCircle:
        # Draw the base circle
        return sketch.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(self.center_x, self.center_y, 0), self.radius
        )

    def calculate_area(self) -> float:
        return math.pi * self.radius**2

    def __str__(self):
        return (
            f"Circle(radius={self.radius}, center=({self.center_x}, {self.center_y}))"
        )

    def xy_bound(self) -> float:
        return self.radius