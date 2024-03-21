import math
import adsk.core, adsk.fusion, adsk.cam, traceback

EXTRUDE = True

BG_DEPTH = 2
BG_LENGTH = 200
BG_WIDTH = 200

HOLE_RADIUS = 20

OUTER_SUPERELLIPSE_DEPTH = 1
INNER_SUPERELLIPSE_DEPTH = 1

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
        # drawBorderedCircle(rootComp, 100, 1, 'circle', BG_DEPTH)
        
        # # Draw an astroid with a hole in the center
        # drawOuterAsteroidWithCenterHole(rootComp, OUTER_SUPERELLIPSE_DEPTH, 2/3, 100, 100, 100, 'outer-superellipse', BG_DEPTH)
        # # Draw a circle with a hole in the center with radius 50
        # drawCircle(rootComp, 50, 1, 'circle', OUTER_SUPERELLIPSE_DEPTH + BG_DEPTH)
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
    # Calculate corner points
    topLeft = adsk.core.Point3D.create(-BG_LENGTH / 2, BG_WIDTH / 2, 0)
    bottomRight = adsk.core.Point3D.create(BG_LENGTH / 2, -BG_WIDTH / 2, 0)
    
    # Draw the rectangle
    lines = sketch.sketchCurves.sketchLines
    rectLines = lines.addTwoPointRectangle(topLeft, bottomRight)
    
    # Extrude the rectangle
    prof = sketch.profiles.item(0)
    extrudes = rootComp.features.extrudeFeatures
    extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(bg_depth))
    extrude = extrudes.add(extInput)
    body = extrude.bodies.item(0)
    
    # Create a new sketch for the hole
    sketchHole = sketches.add(xyPlane)
    sketch.name = 'hole'
    sketchHole.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), hole_radius)
    
    # Extrude cut the hole
    holeProf = sketchHole.profiles.item(0)
    cutInput = extrudes.createInput(holeProf, adsk.fusion.FeatureOperations.CutFeatureOperation)
    cutInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(bg_depth))
    extrude = extrudes.add(cutInput)
    body = extrude.bodies.item(0)
    # cutInput.targetBody = body  # Make sure 'body' references the correct extruded body.
    # extrudes.add(cutInput)
    
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
    spline = sketch.sketchCurves.sketchFittedSplines.add(points)

    # Add a circle in the middle with a radius of 10cm
    center = adsk.core.Point3D.create(0, 0, 0)
    sketch.sketchCurves.sketchCircles.addByCenterRadius(center, 10)
    
   # Calculate the radius of the inscribed circle for the outer superellipse (astroid)
    # Adjusted for the astroid scaled to fit within scaleX by scaleY area
    # The radius calculation is done based on the normalized astroid's inscribed circle radius 
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
    
    # Extrude if needed
    if EXTRUDE:
        extrudes = rootComp.features.extrudeFeatures
        profile = sketch.profiles.item(0)  # Assuming Fusion 360 recognizes the single composite profile
        extrudeInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        extrudeInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(depth))
        extrudes.add(extrudeInput)

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
