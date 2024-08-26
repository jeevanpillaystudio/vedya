from typing import List
import adsk.core
import adsk.fusion
from core.fabrication.composition.composition_geometry import CompositionGeometry
from core.geometry.action.modify.index import Modifier


class Rectangle(CompositionGeometry):
    def __init__(
        self,
        thickness: float,
        length: float,
        width: float,
        center_x: float = 0,
        center_y: float = 0,
        plane_offset: float = 0,
        modifiers: List[Modifier] = None,
    ):
        super().__init__(
            thickness=thickness,
            plane_offset=plane_offset,
            modifiers=modifiers,
            center_x=center_x,
            center_y=center_y,
        )
        self.length = length
        self.width = width

    def draw(self, sketch: adsk.fusion.Sketch) -> adsk.fusion.SketchLineList:
        return sketch.sketchCurves.sketchLines.addTwoPointRectangle(
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
