from typing import List
from core.geometry.composition_geometry import CompositionGeometry
from core.geometry.modifiers.extrude import Extrude
import adsk.fusion, adsk.core


class Rectangle(CompositionGeometry, Extrude):
    # body
    length: float
    width: float
    thickness: float

    def __init__(
        self,
        thickness: float,
        length: float,
        width: float,
        parent: CompositionGeometry = None,
        center_x: float = 0,
        center_y: float = 0,
    ):
        CompositionGeometry.__init__(
            self,
            parent=parent,
            children=None,
            center_x=center_x,
            center_y=center_y,
        )

        # body
        self.length = length
        self.width = width

        # to be removed
        self.thickness = thickness

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
        return f"Rectangle(length={self.length}, width={self.width}, center_x={self.center_x}, center_y={self.center_y}), plane_offset={self.plane_offset}"
