from ..modifiers.boolean import Boolean
from ..composition_geometry import CompositionGeometry
import adsk.fusion, adsk.core


class Rectangle(CompositionGeometry):
    # body
    length: float
    width: float

    def __init__(
        self,
        thickness: float,
        length: float,
        width: float,
        boolean: Boolean = None,
        parent: CompositionGeometry = None,
        center_x: float = 0,
        center_y: float = 0,
        plane_offset: float = 0.0,
    ):
        CompositionGeometry.__init__(
            self,
            parent=parent,
            children=None,
            center_x=center_x,
            center_y=center_y,
            thickness=thickness,
            boolean=boolean,
            plane_offset=plane_offset,
        )

        # body
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
        return f"Rectangle(length={self.length}, width={self.width}, center_x={self.center_x}, center_y={self.center_y}), plane_offset={self.plane_offset}"
