import math
from typing import List

from ..modifiers.extrude import Extrude
from ..modifiers.boolean import Boolean
from ..composition_geometry import ArrayType, CompositionGeometry
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
        x_count: int = 1,
        y_count: int = 1,
        boolean: List[Boolean] = None,
        array_type: ArrayType = ArrayType.SINGLE_AXIS,
    ):
        CompositionGeometry.__init__(
            self,
            extrude=extrude,
            center_x=center_x,
            center_y=center_y,
            boolean=boolean,
            array_type=array_type,
            x_count=x_count,
            y_count=y_count,
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
