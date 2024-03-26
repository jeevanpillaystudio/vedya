import math
import adsk.fusion

def create_astroid_points(n, numPoints, scaleX, scaleY):
    points = adsk.core.ObjectCollection.create()
    for i in range(numPoints + 1):
        angle = i * 2 * math.pi / numPoints
        x = pow(abs(math.cos(angle)), 2/n) * math.copysign(1, math.cos(angle)) * scaleX
        y = pow(abs(math.sin(angle)), 2/n) * math.copysign(1, math.sin(angle)) * scaleY
        points.add(adsk.core.Point3D.create(x, y, 0))
    return points  

def draw_astroid_filled(sketch, n, numPoints, scaleX, scaleY):
    sketch.sketchCurves.sketchFittedSplines.add(create_astroid_points(n, numPoints, scaleX, scaleY))
    
def draw_astroid_stroke(sketch, n, numPoints, scaleX, scaleY, strokeWeight):
    sketch.sketchCurves.sketchFittedSplines.add(create_astroid_points(n, numPoints, scaleX, scaleY))
    sketch.sketchCurves.sketchFittedSplines.add(create_astroid_points(n, numPoints, scaleX - strokeWeight, scaleY - strokeWeight)) 
    
def calculate_astroid_area(scaleX):
    return (3 / 8) * math.pi * scaleX ** 2 

def draw_circle(sketch, radius):
    sketch.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), radius)
    
def calculate_circle_area(radius):
    return math.pi * radius ** 2

def draw_rectangle(sketch, length, width):
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(adsk.core.Point3D.create(-length / 2, width / 2, 0), adsk.core.Point3D.create(length / 2, -width / 2, 0))   
    
def calculate_rectangle_area(width, height):
    return width * height

def draw_rotated_rectangle(sketch, width, height):
    sketch.sketchCurves.sketchLines.addThreePointRectangle(adsk.core.Point3D.create(-width, 0, 0), adsk.core.Point3D.create(0, height, 0), adsk.core.Point3D.create(width, 0, 0))

def calculate_three_point_rectangle_area(width, height):
    return math.sqrt(width ** 2 + height ** 2) * math.sqrt(width ** 2 + height ** 2)