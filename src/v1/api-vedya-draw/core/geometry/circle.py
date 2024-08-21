import math
import adsk.core
from .index import Geometry


class Circle(Geometry):
    def __init__(self, radius: float):
        self.radius = radius

    def draw(self, sketch: adsk.fusion.Sketch):
        sketch.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0), self.radius
        )

    def calculate_area(self):
        return math.pi * self.radius**2


def draw_circle(sketch, radius, center_x=0.0, center_y=0.0):
    circles = sketch.sketchCurves.sketchCircles
    circle = circles.addByCenterRadius(
        adsk.core.Point3D.create(center_x, center_y, 0), radius
    )
    return circle


def calculate_circle_area(radius):
    return math.pi * radius**2
