import math
import adsk.core, adsk.fusion, adsk.cam, traceback
from .shapes import draw_astroid_filled, draw_astroid_stroke, calculate_astroid_area, draw_circle, calculate_circle_area, calculate_rectangle_area, draw_rectangle, draw_rotated_rectangle, calculate_three_point_rectangle_area
from .utils import create_offset_plane, create_sketch, extrude_profile_by_area

EXTRUDE = True

# structurally
# 1 layer; each having 4 sub-layers
# 1 sub-layer == 0.32cm
# 1 layer == 1.28cm
# total layers = 4
# total depth = 5.12cm
# base = 6.4cm - 5.12cm = 1.28cm

def run(context):
    ui = None
    try:
        # Get the application and root component
        app = adsk.core.Application.get()
        ui  = app.userInterface
        design = app.activeProduct

        # Get the root component of the active design
        rootComp: adsk.fusion.Component = design.rootComponent
        hole_radius = 16.0
        
        # Layer 0
        # drawBackgroundRectangle(rootComp=rootComp, bg_length=128, bg_width=128, bg_depth=1.28, hole_radius=hole_radius, name='bg-rect')
        drawCircle(rootComp, 16.0, 1.28, 'circle', 1.28)
        # drawBorderAroundRectangle(rootComp, 200, 200, 6, 2)
        
        # Layer 1
        # drawZenoRectangles(rootComp=rootComp, layer_offset=1.28, strokeWeight=1.28, depth=1.28)
        # drawZenoCircles(rootComp=rootComp, layer_offset=1.28, strokeWeight=0.64, depth=1.28)
        # drawRotatedSquare(rootComp=rootComp, width=64.0, layer_offset=1.28, depth=1.28)
        # drawRotatedSquare(rootComp=rootComp, width=32.0 + 16.0, layer_offset=1.28, depth=1.28)
        # drawRotatedSquare(rootComp=rootComp, width=32.0, layer_offset=1.28, depth=1.28)
        
        # drawBorderedCircle(rootComp=rootComp, radius=64.0, depth=1.28, name='outer-circle', offset=1.28, strokeWeight=1.28)
        # drawOuterAstroid(rootComp=rootComp, depth=1.28, n=2/3, numPoints=128, scaleX=64, scaleY=64, name='outer-superellipse', hole_radius=hole_radius, layer_offset=1.28, strokeWeight=2.56)
        # drawOuterAstroid(rootComp=rootComp, depth=1.28, n=2/3, numPoints=128, scaleX=32.0, scaleY=32.0, name='outer-superellipse', hole_radius=hole_radius, layer_offset=1.28, strokeWeight=2.56)
        
        # drawInnerSuperellipse(rootComp=rootComp, depth=1.28, n=4/10, numPoints=128, scaleX=64.0, scaleY=64.0, name='inner-superellipse', offset=1.28, hole_radius=hole_radius)
        create_seed_of_life(rootComp=rootComp, radius=16.0, layer_depth=0.0, radius_diff=0.0, strokeWeight=0.16, extrudeHeight=1.28, n=2, layer_offset=1.28, fp_tolerance=26)
        # create_seed_of_life(rootComp=rootComp, diameter=32.0, layer_depth=0.0, radius_diff=0.0, strokeWeight=0.64, extrudeHeight=1.28, n=2, layer_offset=1.28, fp_tolerance=14)
        
        # # Depth == 2
        # drawBorderedCircle(rootComp=rootComp, radius=32, depth=1, name='inner-circle', offset=2, width=1)
        
        # # Depth == 3
        # drawBorderedCircle(rootComp, 50, 1, 'circle', 3, 1)
        # drawBorderedCircle(rootComp, 50 - 2, 1, 'circle', 3, 1 / 2)
        # create_inverted_triangle(rootComp, 75, n=1, layer_depth=0.5, extrudeHeight=0.5, layer_offset=3.0)

        # # Depth == 4
        # drawInnerSuperellipseWithCenterHole(rootComp, 1, 4 / 10, 100, 100, 100, 'inner-superellipse', 4, 10)

        # # Depth == 5
        # # drawCircle(rootComp, 15, 1, 'circle', 5)
        # drawBorderedCircle(rootComp, 25, 1, 'circle', 5, 1 / 2)
        # drawBorderedCircle(rootComp, 15, 1, 'circle', 5, 1 / 2)
        # drawBorderedCircle(rootComp, 10, 1, 'circle', 5, 1 / 2)
        # create_seed_of_life(rootComp=rootComp, diameter=24.5, layer_depth=0.0, radius_diff=0.0, strokeWeight=0.5, extrudeHeight=1.0, n=2, layer_offset=5.0)
        # # create_seed_of_life(rootComp=rootComp, diameter=22, layer_depth=0.0, radius_diff=0.0, strokeWeight=0.5, extrudeHeight=0.5, n=2, layer_offset=5.0)
        
        # # Depth == 6
        # drawBorderedCircle(rootComp, 10, 1, 'circle', 6, 1 / 2)
        
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def drawRotatedSquare(rootComp, width=64.0, layer_offset=1.28, depth=1.28, strokeWeight=1.28):
    sketch = create_sketch(rootComp, '60-rectangle', offset=layer_offset)
    draw_rotated_rectangle(sketch, width, width)
    draw_rotated_rectangle(sketch, width - strokeWeight, width - strokeWeight)
    extrude_profile_by_area(rootComp, sketch.profiles, calculate_three_point_rectangle_area(width, width) - calculate_three_point_rectangle_area(width - strokeWeight, width - strokeWeight), depth, '60-rectangle')

def drawZenoRectangles(rootComp: adsk.fusion.Component, layer_offset=0.0, strokeWeight=0.0, depth=0.5):
    sketch = create_sketch(rootComp, 'zeno-rectangles', offset=layer_offset)
    for i in range(2):
        # based on power series of 1/2
        val = (2 ** (i + 6))
        length = width = val
        
        # Draw the rectangle (only border)
        draw_rectangle(sketch, length, width)
        draw_rectangle(sketch, length - strokeWeight, width - strokeWeight)
        
        # Extrude the rectangle
        extrude_profile_by_area(rootComp, sketch.profiles, calculate_rectangle_area(length, width) - calculate_rectangle_area(length - strokeWeight, width - strokeWeight), depth, 'zeno-rectangle-' + str(i + 1))

def drawZenoCircles(rootComp: adsk.fusion.Component, layer_offset=0.0, strokeWeight=0.0, depth=0.5):
    sketch = create_sketch(rootComp, 'zeno-circles', offset=layer_offset)
    for i in range(2):
        # based on power series of 1/2
        val = (2 ** (i + 5))
        radius = val / 2
        
        # Draw the circle (only border)
        draw_circle(sketch, radius)
        draw_circle(sketch, radius - strokeWeight)
        
        # Extrude the circle
        extrude_profile_by_area(rootComp, sketch.profiles, calculate_circle_area(radius) - calculate_circle_area(radius - strokeWeight), depth, 'zeno-circle-' + str(i + 1))


def drawBackgroundRectangle(rootComp: adsk.fusion.Component, bg_length, bg_width, bg_depth, hole_radius, name):
    sketch = create_sketch(rootComp, name, offset=0.0)
    draw_rectangle(sketch, bg_length, bg_width)
    extrude_profile_by_area(rootComp, sketch.profiles, calculate_rectangle_area(bg_length, bg_width), bg_depth, name) 
    
def drawOuterAstroid(rootComp, depth, n, numPoints, scaleX, scaleY, name, hole_radius, layer_offset=0.0, strokeWeight = 0.0):
    sketch = create_sketch(rootComp, name, layer_offset)
    if strokeWeight > 0:
        draw_astroid_filled(sketch, n, numPoints, scaleX, scaleY)
        draw_astroid_stroke(sketch, n, numPoints, scaleX, scaleY, strokeWeight)
        extrude_profile_by_area(rootComp, sketch.profiles, calculate_astroid_area(scaleX) - calculate_astroid_area(scaleX - strokeWeight), depth, name)
    else:
        draw_astroid_filled(sketch, n, numPoints, scaleX, scaleY)
        extrude_profile_by_area(rootComp, sketch.profiles, calculate_astroid_area(scaleX), depth, name)
 
def drawInnerSuperellipse(rootComp, depth, n, numPoints, scaleX, scaleY, name, offset, hole_radius):
    sketch = create_sketch(rootComp, name, offset)
    draw_astroid_filled(sketch, n, numPoints, scaleX, scaleY)
    
    if EXTRUDE:
        # Iterate and extrude each profile
        for profile in sketch.profiles:
            area = profile.areaProperties().area
            extrudeInput = rootComp.features.extrudeFeatures.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            extrudeInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(depth))
            rootComp.features.extrudeFeatures.add(extrudeInput)

def drawBorderedCircle(rootComp, radius, depth, name, offset, strokeWeight):
    # Create an offset plane from the xyPlane
    xyPlane = rootComp.xYConstructionPlane
    planes = rootComp.constructionPlanes
    planeInput = planes.createInput()
    offsetValue = adsk.core.ValueInput.createByReal(offset)
    planeInput.setByOffset(xyPlane, offsetValue)
    offsetPlane = planes.add(planeInput)
    
    # Create a new sketch on the offset plane
    sketches = rootComp.sketches   
    sketch = sketches.add(offsetPlane)
    sketch.name = name    
    
    # Create a circle with the specified radius
    center = adsk.core.Point3D.create(0, 0, 0)
    sketch.sketchCurves.sketchCircles.addByCenterRadius(center, radius)

    # Create another circle with a smaller radius
    center = adsk.core.Point3D.create(0, 0, 0)
    sketch.sketchCurves.sketchCircles.addByCenterRadius(center, radius - strokeWeight)
   
    # Extrude
    if EXTRUDE:
        # Iterate each Profile & Find Profile with the Area = extract area for the circle - hole (use params above)
        searchArea = math.pi * radius ** 2 - math.pi * (radius - strokeWeight) ** 2
        profile = extrude_profile_by_area(rootComp, sketch.profiles, searchArea, depth, name)    
        if profile is None:
            raise ValueError('Failed to find the profile for extrusion')
    
def drawCircle(rootComp, radius, depth, name, offset):
    # Create an offset plane from the xyPlane
    xyPlane = rootComp.xYConstructionPlane
    planes = rootComp.constructionPlanes
    planeInput = planes.createInput()
    offsetValue = adsk.core.ValueInput.createByReal(offset)
    planeInput.setByOffset(xyPlane, offsetValue)
    offsetPlane = planes.add(planeInput)
    
    # Create a new sketch on the offset plane
    sketches = rootComp.sketches   
    sketch = sketches.add(offsetPlane)
    sketch.name = name    
    
    # Create a circle with the specified radius
    center = adsk.core.Point3D.create(0, 0, 0)
    sketch.sketchCurves.sketchCircles.addByCenterRadius(center, radius)
    
    # Extrude if needed
    if EXTRUDE:
        extrudes = rootComp.features.extrudeFeatures
        profile = sketch.profiles.item(0)  # Assuming Fusion 360 recognizes the single composite profile
        extrudeInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        extrudeInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(depth))
        extrudes.add(extrudeInput)
 

def drawBorderAroundRectangle(rootComp, originalWidth, originalHeight, borderDepth, borderWidth):
    # Create a new sketch on the xy plane
    sketches = rootComp.sketches
    xyPlane = rootComp.xYConstructionPlane
    sketch = sketches.add(xyPlane)
    sketch.name = 'bg-border'
    
    # Define the corner points for the border rectangles
    # Calculations account for original rectangle size plus the border on each side
    extendedWidth = originalWidth + 2 * borderWidth
    extendedHeight = originalHeight + 2 * borderWidth
    
    # Top Border Rectangle
    topBorderTopLeft = adsk.core.Point3D.create(-extendedWidth / 2, originalHeight / 2 + borderWidth, 0)
    topBorderBottomRight = adsk.core.Point3D.create(extendedWidth / 2, originalHeight / 2, 0)
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(topBorderTopLeft, topBorderBottomRight)
    
    # Bottom Border Rectangle
    bottomBorderTopLeft = adsk.core.Point3D.create(-extendedWidth / 2, -originalHeight / 2 - borderWidth, 0)
    bottomBorderBottomRight = adsk.core.Point3D.create(extendedWidth / 2, -originalHeight / 2, 0)
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(bottomBorderTopLeft, bottomBorderBottomRight)
    
    # Left Border Rectangle
    leftBorderTopLeft = adsk.core.Point3D.create(-originalWidth / 2 - borderWidth, originalHeight / 2, 0)
    leftBorderBottomRight = adsk.core.Point3D.create(-originalWidth / 2, -originalHeight / 2, 0)
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(leftBorderTopLeft, leftBorderBottomRight)
    
    # Right Border Rectangle
    rightBorderTopLeft = adsk.core.Point3D.create(originalWidth / 2, originalHeight / 2, 0)
    rightBorderBottomRight = adsk.core.Point3D.create(originalWidth / 2 + borderWidth, -originalHeight / 2, 0)
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(rightBorderTopLeft, rightBorderBottomRight)
    
    # Extrusion of border rectangles could follow here, similar to how the bg-rect was extruded
    # Assuming you'd extrude these borders with the same or different depth as needed
    # Extrude if needed
    # Extrude if needed
    if EXTRUDE:
        # Extrude each border rectangle individually
        extrudes = rootComp.features.extrudeFeatures
        largestArea = 0
        # First, find the largest profile area to identify the inner profile to skip
        for profile in sketch.profiles:
            area = profile.areaProperties().area
            if area > largestArea:
                largestArea = area
        
        # Now, extrude only the profiles that are not the largest (assuming borders have smaller area)
        for profile in sketch.profiles:
            area = profile.areaProperties().area
            if area < largestArea:
                # This profile is not the inner profile, so extrude it
                extrudeInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                distance = adsk.core.ValueInput.createByReal(borderDepth)  # Depth of the extrusion for each border
                extrudeInput.setDistanceExtent(False, distance)
                extrudes.add(extrudeInput)



def create_seed_of_life(rootComp: adsk.fusion.Component, radius=8.0, layer_depth=0.1, layer_offset=0.0, radius_diff=0.1, strokeWeight=0.05, extrudeHeight=0.1, n=3, fp_tolerance=0.1):
    try:
        sketches = rootComp.sketches
        extrudes = rootComp.features.extrudeFeatures
                
        # angle multiplier
        angle_mult = 30

        # Main code to create the Seed of Life and extrude
        for i in range(n):  # Creating 3 layers
            sketch = create_sketch(rootComp, 'seed-of-life-' + str(i + 1), layer_offset + layer_depth * i)
            create_seed_of_life_pattern(sketch, radius - i * (radius_diff * 2), 0, 0, angle_mult * i)
            
            # Thin Extrude the Seed of Life 
            for profile in sketch.profiles:
                # Thin Extrude
                extrudeInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.JoinFeatureOperation)
                
                # Set the extrude to be a thin extrusion with a specified thickness.
                extrudeInput.setThinExtrude(adsk.fusion.ThinExtrudeWallLocation.Side1, adsk.core.ValueInput.createByReal(strokeWeight))
                
                # Extrude Height
                extrudeInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(extrudeHeight))
                
                # Create the extrusion.
                extrudes.add(extrudeInput)

    except:
        raise Exception('Failed:\n{}'.format(traceback.format_exc()))

def create_inverted_triangle(rootComp, side_length, center_x=0, center_y=0, n=3, layer_depth=0.1, extrudeHeight=0.1, layer_offset=0.0):
    """
    Creates inverted triangles with two options: fill-based or stroke-based.
    For stroke-based, it draws smaller triangles inside the larger triangles and extrudes the space between them.
    
    Parameters:
    - rootComp: The root component in which the sketches are to be created.
    - side_length: The length of the side of the triangles.
    - center_x, center_y: The center position of the composite shape.
    - n: The number of layers to create.
    - layer_depth: The depth between each layer.
    - type: The type of triangles to create ('fill' or 'stroke').
    """
    sketches = rootComp.sketches
    extrudes = rootComp.features.extrudeFeatures
    
    def create_triangles(sketch, side_length, center_x, center_y, type):
        # Base triangle height
        height = (math.sqrt(3) / 2) * side_length
        # Define vertices for both triangles
        vertices_up = [
            (center_x, center_y + 2 * height / 3),  # Top vertex of upward triangle
            (center_x - side_length / 2, center_y - height / 3),  # Bottom left vertex
            (center_x + side_length / 2, center_y - height / 3)   # Bottom right vertex
        ]
        
        vertices_down = [
            (center_x, center_y - 2 * height / 3),  # Bottom vertex of downward triangle
            (center_x - side_length / 2, center_y + height / 3),  # Top left vertex
            (center_x + side_length / 2, center_y + height / 3)   # Top right vertex
        ]

        def add_line(start_point, end_point):
            sketch.sketchCurves.sketchLines.addByTwoPoints(
                adsk.core.Point3D.create(*start_point), 
                adsk.core.Point3D.create(*end_point)
            )

        def draw_triangle(vertices, shrink_factor=0):
            if shrink_factor:
                center = (center_x, center_y)
                shrinked_vertices = [
                    (v[0] + (center[0] - v[0]) * shrink_factor, v[1] + (center[1] - v[1]) * shrink_factor)
                    for v in vertices
                ]
                for i in range(len(shrinked_vertices)):
                    start_point = shrinked_vertices[i]
                    end_point = shrinked_vertices[(i + 1) % len(shrinked_vertices)]
                    add_line(start_point, end_point)
            else:
                for i in range(len(vertices)):
                    start_point = vertices[i]
                    end_point = vertices[(i + 1) % len(vertices)]
                    add_line(start_point, end_point)

        # Draw outer triangles
        draw_triangle(vertices_up)
        draw_triangle(vertices_down)

        if type == 'stroke':
            # Draw inner triangles for the stroke effect
            draw_triangle(vertices_up, shrink_factor=0.1)
            draw_triangle(vertices_down, shrink_factor=0.1)
        
        # Extrude the space between the outer and inner triangles if 'stroke', else extrude the whole profile for 'fill'
        if type == 'stroke':
            for profile in sketch.profiles:
                if profile.areaProperties().area > 170:  # Adjust this threshold based on your design needs
                    continue
                extrudeInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                extrudeInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(extrudeHeight))  # Set extrusion depth
                extrudes.add(extrudeInput)
        elif type == 'fill':
            for profile in sketch.profiles:
                extrudeInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                extrudeInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(extrudeHeight))
                extrudes.add(extrudeInput)
    
    
    # Create Base
    offsetPlane = create_offset_plane(rootComp, layer_offset)
    sketch = sketches.add(offsetPlane)
    sketch.name = 'base'
    create_triangles(sketch, side_length, center_x, center_y, 'fill')
    
    # Create layers
    offsetPlane = create_offset_plane(rootComp, layer_offset + layer_depth)
    sketch = sketches.add(offsetPlane)
    sketch.name = 'layer-1'
    create_triangles(sketch, side_length, center_x, center_y, 'stroke')
    
# Function to create a circle in a sketch
def create_circle(sketch, radius, center_x, center_y):
    circles = sketch.sketchCurves.sketchCircles
    circle = circles.addByCenterRadius(adsk.core.Point3D.create(center_x, center_y, 0), radius)
    return circle

# Function to create the Seed of Life pattern
def create_seed_of_life_pattern(sketch, radius, center_x=0, center_y=0, angle_offset=0):
    # Create the center circle
    create_circle(sketch, radius, center_x, center_y)
    
    # Create the surrounding circles
    for i in range(6):
        # use angle offset
        angle = math.radians(i * 60 + angle_offset)
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        create_circle(sketch, radius, x, y)