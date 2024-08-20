import adsk.core
import adsk.fusion


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
