import math
import adsk.core
import adsk.fusion
from .index import Geometry


class Rectangle(Geometry):
    def __init__(self, length: float, width: float, rotation: float = 0):
        self.length = length
        self.width = width
        self.rotation = rotation

    def draw(self, sketch: adsk.fusion.Sketch):
        if self.rotation == 0:
            draw_rectangle(sketch, self.length, self.width)
        else:
            draw_rotated_rectangle(sketch, self.length, self.width, self.rotation)

    def calculate_area(self):
        return self.length * self.width


def draw_rectangle(sketch: adsk.fusion.Sketch, length, width):
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(-length / 2, width / 2, 0),
        adsk.core.Point3D.create(length / 2, -width / 2, 0),
    )


def draw_rotated_rectangle(sketch, width, height):
    sketch.sketchCurves.sketchLines.addThreePointRectangle(
        adsk.core.Point3D.create(-width, 0, 0),
        adsk.core.Point3D.create(0, height, 0),
        adsk.core.Point3D.create(width, 0, 0),
    )


def calculate_rectangle_area(width, length):
    return width * length


def calculate_three_point_rectangle_area(width, height):
    return math.sqrt(width**2 + height**2) * math.sqrt(width**2 + height**2)
