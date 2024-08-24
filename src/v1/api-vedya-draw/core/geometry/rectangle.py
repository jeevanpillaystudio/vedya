import math
from typing import List
import adsk.core
import adsk.fusion
from ..modifier.index import Modifier
from .index import ModifiableGeometry


class Rectangle(ModifiableGeometry):
    def __init__(
        self,
        thickness: float,
        length: float,
        width: float,
        center_x: float = 0,
        center_y: float = 0,
        plane_offset: float = 0,
        modifiers: Modifier = None,
    ):
        super().__init__(thickness, plane_offset, modifiers, center_x, center_y)
        self.length = length
        self.width = width

    def draw(self) -> adsk.fusion.SketchLineList:
        # @TODO should be two seperate geometries; Rectangle and RotatedRectangle
        if self.sketch is None:
            raise ValueError("Sketch is not initialized")

        return self.sketch.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(
                -self.length / 2 + self.center_x, self.width / 2 + self.center_y, 0
            ),
            adsk.core.Point3D.create(
                self.length / 2 + self.center_x, -self.width / 2 + self.center_y, 0
            ),
        )

    def calculate_area(self):
        return self.length * self.width

    def __str__(self):
        return f"Rectangle(length={self.length}, width={self.width}, center_x={self.center_x}, center_y={self.center_y})"

    def xyBound(self):
        return adsk.core.Point3D.create(self.length, self.width, 0)
