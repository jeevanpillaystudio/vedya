import adsk.core


def draw_circle(sketch, radius, center_x=0.0, center_y=0.0):
    circles = sketch.sketchCurves.sketchCircles
    circle = circles.addByCenterRadius(
        adsk.core.Point3D.create(center_x, center_y, 0), radius
    )
    return circle


def calculate_circle_area(radius):
    return math.pi * radius**2
