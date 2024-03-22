import math
import adsk.core, adsk.fusion, adsk.cam, traceback

EXTRUDE = True
FP_TOLERANCE = 1e-2 # 0.01 Precision for floating point comparison

def run(context):
    ui = None
    try:
        # Get the application and root component
        app = adsk.core.Application.get()
        ui  = app.userInterface
        design = app.activeProduct

        # Get the root component of the active design
        rootComp: adsk.fusion.Component = design.rootComponent
        hole_radius = 10
        
        # Depth == 0
        drawBackgroundRectangeWithCenterHole(rootComp, 200, 200, 2, hole_radius, 'bg-rect')
        drawBorderAroundRectangle(rootComp, 200, 200, 6, 2)
        
        # Depth == 1
        drawBorderedCircle(rootComp, 100, 1, 'circle', 2, 1)
        drawOuterAsteroidWithCenterHole(rootComp, 1, 2/3, 100, 100, 100, 'outer-superellipse', 1, 10)
        
        # Depth == 2
        drawCircle(rootComp, 50, 1, 'circle', 2)
        
        # Depth == 3
        drawBorderedCircle(rootComp, 50, 1, 'circle', 3, 1)
        drawBorderedCircle(rootComp, 50 - 2, 1, 'circle', 3, 1 / 2)
        drawInnerSuperellipseWithCenterHole(rootComp, 1, 4 / 10, 100, 100, 100, 'inner-superellipse', 3, 10)
        create_inverted_triangle(rootComp, 75, n=1, layer_depth=0.5, extrudeHeight=0.5, layer_offset=3.0)

        # Depth == 4
        drawInnerSuperellipseWithCenterHole(rootComp, 1, 4 / 10, 100, 100, 100, 'inner-superellipse', 4, 10)

        # Depth == 5
        # drawCircle(rootComp, 15, 1, 'circle', 5)
        drawBorderedCircle(rootComp, 25, 1, 'circle', 5, 1 / 2)
        drawBorderedCircle(rootComp, 15, 1, 'circle', 5, 1 / 2)
        drawBorderedCircle(rootComp, 10, 1, 'circle', 5, 1 / 2)
        create_seed_of_life(rootComp=rootComp, diameter=24.5, layer_depth=0.0, radius_diff=0.0, strokeWeight=0.5, extrudeHeight=1.0, n=2, layer_offset=5.0)
        # create_seed_of_life(rootComp=rootComp, diameter=22, layer_depth=0.0, radius_diff=0.0, strokeWeight=0.5, extrudeHeight=0.5, n=2, layer_offset=5.0)
        
        # Depth == 6
        drawBorderedCircle(rootComp, 10, 1, 'circle', 6, 1 / 2)
        
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
            
            
def drawBackgroundRectangeWithCenterHole(rootComp: adsk.fusion.Component, bg_length, bg_width, bg_depth, hole_radius, name):
    # Create a new sketch on the xy plane
    sketches = rootComp.sketches
    xyPlane = rootComp.xYConstructionPlane
    sketch = sketches.add(xyPlane)
    sketch.name = name
    
    # Draw the rectangle
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(adsk.core.Point3D.create(-bg_length / 2, bg_width / 2, 0), adsk.core.Point3D.create(bg_length / 2, -bg_width / 2, 0))
    
    # Create a circle in the middle with the specified radius
    sketch.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), hole_radius)
    
    # Extrude the rectangle
    if EXTRUDE:
        # Iterate each Profile & Find Profile with the Area = extract area calc for the rectangle - hole (use params above)
        searchArea = bg_length * bg_width - math.pi * hole_radius ** 2
        profile = extrudeProfileByArea(rootComp, sketch.profiles, searchArea, bg_depth, name)    
        if profile is None:
            raise ValueError('Failed to find the profile for extrusion')
    
def drawOuterAsteroidWithCenterHole(rootComp, depth, n, numPoints, scaleX, scaleY, name, offset, hole_radius):
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
    
    # Superellipse parameters
    points = adsk.core.ObjectCollection.create()

    for i in range(numPoints + 1):
        angle = i * 2 * math.pi / numPoints
        x = pow(abs(math.cos(angle)), 2/n) * math.copysign(1, math.cos(angle)) * scaleX
        y = pow(abs(math.sin(angle)), 2/n) * math.copysign(1, math.sin(angle)) * scaleY
        # Add point to the collection
        points.add(adsk.core.Point3D.create(x, y, 0))

    # Create a spline through the calculated points
    sketch.sketchCurves.sketchFittedSplines.add(points)

    # Add a circle in the middle with a radius of 10cm
    sketch.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), hole_radius)
    
    # Extrude
    if EXTRUDE:
        # Iterate each Profile & Find Profile with the Area = extract area calc for the superellipse - hole (use params above)
        searchArea = (3 / 8) * math.pi * (scaleX ** 2) - math.pi * 10 ** 2
        profile = extrudeProfileByArea(rootComp, sketch.profiles, searchArea, depth, name)    
        if profile is None:
            raise ValueError('Failed to find the profile for extrusion')
      
        
def drawInnerSuperellipseWithCenterHole(rootComp, depth, n, numPoints, scaleX, scaleY, name, offset, hole_radius):
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
    
    # Superellipse parameters
    points = adsk.core.ObjectCollection.create()

    for i in range(numPoints + 1):
        angle = i * 2 * math.pi / numPoints
        x = pow(abs(math.cos(angle)), 2/n) * math.copysign(1, math.cos(angle)) * scaleX
        y = pow(abs(math.sin(angle)), 2/n) * math.copysign(1, math.sin(angle)) * scaleY
        # Add point to the collection
        points.add(adsk.core.Point3D.create(x, y, 0))

    # Create a spline through the calculated points
    sketch.sketchCurves.sketchFittedSplines.add(points)

    # Add a circle in the middle with a radius of 10cm
    sketch.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), hole_radius)
    
    # Extrude
    if EXTRUDE:
        extrudes = rootComp.features.extrudeFeatures
        profile = sketch.profiles.item(0)  # Assuming Fusion 360 recognizes the single composite profile
        extrudeInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        extrudeInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(depth))
        extrudes.add(extrudeInput)

def drawBorderedCircle(rootComp, radius, depth, name, offset, width):
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
    sketch.sketchCurves.sketchCircles.addByCenterRadius(center, radius - width)
   
    # Extrude
    if EXTRUDE:
        # Iterate each Profile & Find Profile with the Area = extract area for the circle - hole (use params above)
        searchArea = math.pi * radius ** 2 - math.pi * (radius - width) ** 2
        profile = extrudeProfileByArea(rootComp, sketch.profiles, searchArea, depth, name)    
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

    # Add a circle in the middle with a radius of 10cm
    center = adsk.core.Point3D.create(0, 0, 0)
    sketch.sketchCurves.sketchCircles.addByCenterRadius(center, 10) 
    
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

def createOffsetPlane(rootComp, planeOffset):
    """
    Creates an offset plane from the XY plane based on the specified offset.

    Parameters:
    - rootComp: The root component to which the plane is added.
    - offset: The offset distance from the XY plane.

    Returns:
    - The created offset construction plane.
    """
    xyPlane = rootComp.xYConstructionPlane
    planes = rootComp.constructionPlanes
    planeInput = planes.createInput()
    offsetValue = adsk.core.ValueInput.createByReal(planeOffset)
    planeInput.setByOffset(xyPlane, offsetValue)
    offsetPlane = planes.add(planeInput)
    return offsetPlane

def extrudeProfileByArea(rootComp: adsk.fusion.Component, profiles: list[adsk.fusion.Profile], area: float, depth, bodyName):
    """
    Creates an extrusion based on the specified area and depth for the given profiles.
    
    Parameters:
    - rootComp: The root component to which the extrusion is added.
    - profiles: The collection of profiles to search for the specified area.
    - area: The area to search for in the profiles.
    - depth: The depth of the extrusion.
    - bodyName: The name of the body created by the extrusion.
    
    Returns:
    - The body created by the extrusion based on the specified area and depth.
    """
    for profile in profiles:
        if abs(profile.areaProperties().area - area) < FP_TOLERANCE:
            extrudes = rootComp.features.extrudeFeatures
            extInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            extInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(depth))
            extrude = extrudes.add(extInput)
            body = extrude.bodies.item(0)
            body.name = bodyName
            return body
    return None

def create_seed_of_life(rootComp: adsk.fusion.Component, diameter=10.0, layer_depth=0.1, layer_offset=0.0, radius_diff=0.1, strokeWeight=0.05, extrudeHeight=0.1, n=3):
    try:
        sketches = rootComp.sketches
        extrudes = rootComp.features.extrudeFeatures
        
        # Function to create a circle in a sketch
        def create_circle(sketch, radius, center_x, center_y):
            circles = sketch.sketchCurves.sketchCircles
            circle = circles.addByCenterRadius(adsk.core.Point3D.create(center_x, center_y, 0), radius)
            return circle

        # Function to create the Seed of Life pattern
        def create_seed_of_life_pattern(sketch, diameter, center_x=0, center_y=0, angle_offset=0):
            # Calculate the radius
            radius = diameter / 2
            # Create the center circle
            create_circle(sketch, radius, center_x, center_y)
            create_circle(sketch, radius - strokeWeight, center_x, center_y)
            
            # Create the surrounding circles
            for i in range(6):
                # use angle offset
                angle = math.radians(i * 60 + angle_offset)
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                create_circle(sketch, radius, x, y)
                create_circle(sketch, radius - strokeWeight, x, y)

        
        # Main code to create the Seed of Life and extrude
        for i in range(n):  # Creating 3 layers
            # create offset plane
            offsetPlane = createOffsetPlane(rootComp, layer_offset + layer_depth * i)
            xyPlane = rootComp.xYConstructionPlane
            sketch = sketches.add(offsetPlane)
            sketch.name = 'seed-of-life- ' + str(i + 1)
            
            create_seed_of_life_pattern(sketch, diameter - i * (radius_diff * 2), 0, 0, 30 * i)
            for i in range(sketch.profiles.count):
                profile = sketch.profiles.item(i)
                # Check if the profile is less than some area
                if profile.areaProperties().area > 15:
                    continue
                
                # Extrude the profile
                extrudes = rootComp.features.extrudeFeatures
                extrudeInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                extrudeInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(extrudeHeight))
                extrude = extrudes.add(extrudeInput)


            # sketch
            sketch = sketches.add(offsetPlane)
            sketch.name = 'large-circle-enclosed-' + str(i + 1)
            
            create_circle(sketch, diameter + strokeWeight, 0, 0)
            create_circle(sketch, diameter, 0, 0)
            
            # Extrude the large circle
            extrudeInput = extrudes.createInput(sketch.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            extrudeInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(extrudeHeight))
            extrude = extrudes.add(extrudeInput)
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
    offsetPlane = createOffsetPlane(rootComp, layer_offset)
    sketch = sketches.add(offsetPlane)
    sketch.name = 'base'
    create_triangles(sketch, side_length, center_x, center_y, 'fill')
    
    # Create layers
    offsetPlane = createOffsetPlane(rootComp, layer_offset + layer_depth)
    sketch = sketches.add(offsetPlane)
    sketch.name = 'layer-1'
    create_triangles(sketch, side_length, center_x, center_y, 'stroke')
      