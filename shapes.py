import math
import adsk.fusion
import os
import hashlib
import random
import time

def create_astroid_points(n, numPoints, scaleX, scaleY):
    points = adsk.core.ObjectCollection.create()
    for i in range(numPoints + 1):
        angle = i * 2 * math.pi / numPoints
        x = pow(abs(math.cos(angle)), 2/n) * math.copysign(1, math.cos(angle)) * scaleX
        y = pow(abs(math.sin(angle)), 2/n) * math.copysign(1, math.sin(angle)) * scaleY
        points.add(adsk.core.Point3D.create(x, y, 0))
    return points  

def draw_astroid(sketch, n, numPoints, scaleX, scaleY):
    sketch.sketchCurves.sketchFittedSplines.add(create_astroid_points(n, numPoints, scaleX, scaleY))
    
def draw_astroid_stroke(sketch, n, numPoints, scaleX, scaleY, strokeWeight):
    sketch.sketchCurves.sketchFittedSplines.add(create_astroid_points(n, numPoints, scaleX, scaleY))
    sketch.sketchCurves.sketchFittedSplines.add(create_astroid_points(n, numPoints, scaleX - strokeWeight, scaleY - strokeWeight)) 
    

def draw_circle(sketch, radius, center_x=0.0, center_y=0.0):
    circles = sketch.sketchCurves.sketchCircles
    circle = circles.addByCenterRadius(adsk.core.Point3D.create(center_x, center_y, 0), radius)
    return circle
    
def draw_rectangle(sketch: adsk.fusion.Sketch, length, width):
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(adsk.core.Point3D.create(-length / 2, width / 2, 0), adsk.core.Point3D.create(length / 2, -width / 2, 0))   
    
def draw_rotated_rectangle(sketch, width, height):
    sketch.sketchCurves.sketchLines.addThreePointRectangle(adsk.core.Point3D.create(-width, 0, 0), adsk.core.Point3D.create(0, height, 0), adsk.core.Point3D.create(width, 0, 0))
    
def calculate_astroid_area(scaleX):
    """
    Calculate the area of an astroid shape.

    Parameters:
    scaleX (float): The scale factor of the astroid shape.

    Returns:
    float: The area of the astroid shape.
    """
    return (3 / 8) * math.pi * scaleX ** 2

def calculate_rectangle_area(width, height):
    """
    Calculate the area of a rectangle.

    Args:
        width (float): The width of the rectangle.
        height (float): The height of the rectangle.

    Returns:
        float: The area of the rectangle.
    """
    return width * height


def calculate_circle_area(radius):
    """
    Calculate the area of a circle.

    Parameters:
    radius (float): The radius of the circle.

    Returns:
    float: The area of the circle.
    """
    return math.pi * radius ** 2

def calculate_three_point_rectangle_area(width, height):
    """
    Calculate the area of a rectangle given the width and height using the three-point formula.

    Args:
        width (float): The width of the rectangle.
        height (float): The height of the rectangle.

    Returns:
        float: The area of the rectangle.
    """
    return math.sqrt(width ** 2 + height ** 2) * math.sqrt(width ** 2 + height ** 2)

def create_seed():
    """
    Generates a unique seed value based on the current time, process ID, and a random number.

    Returns:
        str: A unique seed value.
    """
    base_string = str(time.time()) + str(os.getpid()) + str(random.random())
    hash_object = hashlib.sha256(base_string.encode())
    hex_dig = hash_object.hexdigest()
    return hex_dig[:64]

def create_power_series_multiples(n):
    """
    Generate the first n multiples of 1, 2, 4, 8, 16...
    
    Args:
        n (int): The number of multiples to generate.
        
    Returns:
        list: A list of the first n multiples.
    """
    # Base multiplier
    multiplier = 1
    
    # List to hold the multiples
    multiples = []
    
    # Generate multiples
    for _ in range(n):
        multiples.append(multiplier)
        multiplier *= 2  # Update the multiplier for the next iteration
    
    return multiples