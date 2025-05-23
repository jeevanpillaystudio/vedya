from typing import List

from ..modifiers.extrude import Extrude
from ..modifiers.boolean import Boolean
from ..composition_geometry import ArrayType, CompositionGeometry
import adsk.fusion, adsk.core


class Rectangle(CompositionGeometry):
    # body
    length: float
    width: float

    def __init__(
        self,
        extrude: Extrude,
        length: float,
        width: float,
        center_x: float = 0,
        center_y: float = 0,
        boolean: List[Boolean] = None,
        array_type: ArrayType = ArrayType.SINGLE_AXIS,
        x_count: int = 1,
        y_count: int = 1,
    ):
        CompositionGeometry.__init__(
            self,
            extrude=extrude,
            array_type=array_type,
            x_count=x_count,
            y_count=y_count,
            center_x=center_x,
            center_y=center_y,
            boolean=boolean,
        )

        # body
        self.length = length
        self.width = width

    def draw(self, sketch: adsk.fusion.Sketch) -> adsk.fusion.SketchLineList:
        return sketch.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(
                self.center_x - self.length / 2, self.center_y - self.width / 2, 0
            ),
            adsk.core.Point3D.create(
                self.center_x + self.length / 2, self.center_y + self.width / 2, 0
            ),
        )

    def calculate_area(self):
        return self.length * self.width

    def __str__(self):
        return f"Rectangle(length={self.length}, width={self.width}, start_x={self.center_x}, start_y={self.center_y})"

    def xy_bound(self) -> float:
        return max(self.length, self.width)