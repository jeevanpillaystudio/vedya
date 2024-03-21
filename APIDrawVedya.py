import math
import adsk.core, adsk.fusion, adsk.cam, traceback

EXTRUDE = True

BG_DEPTH = 2
BG_LENGTH = 200
BG_WIDTH = 200

HOLE_RADIUS = 20

OUTER_SUPERELLIPSE_DEPTH = 1
INNER_SUPERELLIPSE_DEPTH = 1
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
        
        # Draw a rectangle with a hole in the center
        drawBackgroundRectangeWithCenterHole(rootComp)
        # drawBorderAroundRectangle(rootComp, 200, 200, 8)
        drawBorderedCircle(rootComp, 100, 1, 'circle', BG_DEPTH)
        
        # Draw an astroid with a hole in the center
        drawOuterAsteroidWithCenterHole(rootComp, OUTER_SUPERELLIPSE_DEPTH, 2/3, 100, 100, 100, 'outer-superellipse', BG_DEPTH)
        # Draw a circle with a hole in the center with radius 50
        drawCircle(rootComp, 50, 1, 'circle', OUTER_SUPERELLIPSE_DEPTH + BG_DEPTH)
        # drawBorderedCircle(rootComp, 50, 1, 'circle', OUTER_SUPERELLIPSE_DEPTH + BG_DEPTH + 1)
        # drawBorderedCircle(rootComp, 50-2, 1, 'circle', OUTER_SUPERELLIPSE_DEPTH + BG_DEPTH + 1)

        # # Create a smaller superellipse
        # drawInnerSuperellipseWithCenterHole(rootComp, INNER_SUPERELLIPSE_DEPTH, 4 / 10, 100, 100, 100, 'inner-superellipse', OUTER_SUPERELLIPSE_DEPTH + BG_DEPTH)
        # drawInnerSuperellipseWithCenterHole(rootComp, INNER_SUPERELLIPSE_DEPTH, 4 / 10, 100, 100, 100, 'inner-superellipse', OUTER_SUPERELLIPSE_DEPTH + BG_DEPTH + 1)

        # # Create a circle on the xy plane
        # drawCircle(rootComp, 25, 1, 'circle', OUTER_SUPERELLIPSE_DEPTH + INNER_SUPERELLIPSE_DEPTH + BG_DEPTH + 1)
        # drawBorderedCircle(rootComp, 25, 1, 'circle', OUTER_SUPERELLIPSE_DEPTH + INNER_SUPERELLIPSE_DEPTH + BG_DEPTH + 2)
        
        # drawCircle(rootComp, 15, 1, 'circle', OUTER_SUPERELLIPSE_DEPTH + INNER_SUPERELLIPSE_DEPTH + BG_DEPTH + 2)
        # drawBorderedCircle(rootComp, 15, 1, 'circle', OUTER_SUPERELLIPSE_DEPTH + INNER_SUPERELLIPSE_DEPTH + BG_DEPTH + 2)
        
        # drawBorderedCircle(rootComp, 10, 1, 'circle', OUTER_SUPERELLIPSE_DEPTH + INNER_SUPERELLIPSE_DEPTH + BG_DEPTH + 3)
        
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
            
            
def drawBackgroundRectangeWithCenterHole(rootComp: adsk.fusion.Component):
    # Parameters
    name = 'bg-rect'
    bg_length = BG_LENGTH  # Length of the rectangle
    bg_width = BG_WIDTH  # Width of the rectangle
    bg_depth = BG_DEPTH  # Depth of the extruded rectangle
    hole_radius = 10  # Diameter of the hole
    
    # Create a new sketch on the xy plane
    sketches = rootComp.sketches
    xyPlane = rootComp.xYConstructionPlane
    sketch = sketches.add(xyPlane)
    sketch.name = name
    
    # Draw the rectangle
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(adsk.core.Point3D.create(-BG_LENGTH / 2, BG_WIDTH / 2, 0), adsk.core.Point3D.create(BG_LENGTH / 2, -BG_WIDTH / 2, 0))
    
    # Create a circle in the middle with the specified radius
    sketch.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), hole_radius)
    
    # Extrude the rectangle
    if EXTRUDE:
        # Iterate each Profile & Find Profile with the Area = extract area calc for the rectangle - hole (use params above)
        searchArea = bg_length * bg_width - math.pi * hole_radius ** 2
        profile = extrudeProfileByArea(rootComp, sketch.profiles, searchArea, bg_depth, name)    
        if profile is None:
            raise ValueError('Failed to find the profile for extrusion')
    
def drawOuterAsteroidWithCenterHole(rootComp, depth, n, numPoints, scaleX, scaleY, name, offset):
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
    sketch.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), 10)
    
    # Extrude
    if EXTRUDE:
        # Iterate each Profile & Find Profile with the Area = extract area calc for the superellipse - hole (use params above)
        searchArea = (3 / 8) * math.pi * (scaleX ** 2) - math.pi * 10 ** 2
        profile = extrudeProfileByArea(rootComp, sketch.profiles, searchArea, depth, name)    
        if profile is None:
            raise ValueError('Failed to find the profile for extrusion')
      
        
def drawInnerSuperellipseWithCenterHole(rootComp, depth, n, numPoints, scaleX, scaleY, name, offset):
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
    spline = sketch.sketchCurves.sketchFittedSplines.add(points)

    # Add a circle in the middle with a radius of 10cm
    center = adsk.core.Point3D.create(0, 0, 0)
    sketch.sketchCurves.sketchCircles.addByCenterRadius(center, 10)
    
    # # Calculate the radius of the inscribed circle for the outer superellipse (astroid)
    # # Adjusted for the astroid scaled to fit within scaleX by scaleY area
    # # The radius calculation is done based on the normalized astroid's inscribed circle radius 
    # inscribedCircleRadius = 50  # Calculated radius of the inscribed circle scaled to fit the astroid
    # # Add a circle in the middle with the calculated radius
    # center = adsk.core.Point3D.create(0, 0, 0)
    # sketch.sketchCurves.sketchCircles.addByCenterRadius(center, inscribedCircleRadius)
    
    # Extrude if needed
    if EXTRUDE:
        extrudes = rootComp.features.extrudeFeatures
        profile = sketch.profiles.item(0)  # Assuming Fusion 360 recognizes the single composite profile
        extrudeInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        extrudeInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(depth))
        extrudes.add(extrudeInput)

def drawBorderedCircle(rootComp, radius, depth, name, offset):
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
    sketch.sketchCurves.sketchCircles.addByCenterRadius(center, radius - 1)
   
    # # Add a circle in the middle with a radius of 10cm
    # center = adsk.core.Point3D.create(0, 0, 0)
    # sketch.sketchCurves.sketchCircles.addByCenterRadius(center, 10) 
    
    # Extrude
    if EXTRUDE:
        # Iterate each Profile & Find Profile with the Area = extract area for the circle - hole (use params above)
        searchArea = math.pi * radius ** 2 - math.pi * (radius - 1) ** 2
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
 

def drawBorderAroundRectangle(rootComp, originalWidth, originalHeight, borderDepth):
    # Constants
    borderWidth = BG_DEPTH  # The width of the border is equal to the specified depth for visual consistency
    
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