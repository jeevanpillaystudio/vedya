import math
import adsk.core, adsk.fusion, adsk.cam, traceback

EXTRUDE = True

BG_DEPTH = 2
BG_LENGTH = 200
BG_WIDTH = 200

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
        rootComp = design.rootComponent
        
        # Draw a rectangle with a hole in the center
        drawBackgroundRectangeWithCenterHole(rootComp)
        # drawBorderAroundRectangle(rootComp, 200, 200, 4)
        
        # Draw an astroid with a hole in the center
        outerSuperellipseRadius = 100  # This is a simplification; adjust based on your specific requirements
        drawSuperellipseWithCenterHole(rootComp, OUTER_SUPERELLIPSE_DEPTH, 2/3, 100, 100, 100, 'outer-superellipse', BG_DEPTH)
        drawInscribedCircleInSuperellipse(rootComp,'outer-superellipse', BG_DEPTH)

        # Create a smaller superellipse
        # drawSuperellipseWithCenterHole(rootComp, INNER_SUPERELLIPSE_DEPTH, 1/2, 100, 100, 100, 'inner-superellipse', OUTER_SUPERELLIPSE_DEPTH + BG_DEPTH)

        
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
            
            
def drawBackgroundRectangeWithCenterHole(rootComp):
    name = 'bg-rect'
    
    # Create a new sketch on the xy plane
    sketches = rootComp.sketches
    xyPlane = rootComp.xYConstructionPlane
    sketch = sketches.add(xyPlane)
    sketch.name = name
    
    # Calculate corner points
    topLeft = adsk.core.Point3D.create(-BG_LENGTH / 2, BG_WIDTH / 2, 0)
    bottomRight = adsk.core.Point3D.create(BG_LENGTH / 2, -BG_WIDTH / 2, 0)
    
    # Draw the rectangle
    lines = sketch.sketchCurves.sketchLines
    rectLines = lines.addTwoPointRectangle(topLeft, bottomRight)
    
    # Hole parameters
    holeRadius = 10  # Radius of the hole in cm
    center = adsk.core.Point3D.create(0, 0, 0)  # Center of the hole
    
    # Draw the center hole
    circles = sketch.sketchCurves.sketchCircles
    hole = circles.addByCenterRadius(center, holeRadius)
    
    # Extrude the sketch
    if not EXTRUDE:
        return
    
    # Get the profile defined by the rectangle and the hole
    # Identify the correct profile for extrusion
    targetProfile = None
    maxArea = 0
    for profile in sketch.profiles:
        area = profile.areaProperties().area
        if area > maxArea:
            maxArea = area
            targetProfile = profile

    if targetProfile is not None:
        # Extrude the target profile
        extrudes = rootComp.features.extrudeFeatures
        extInput = extrudes.createInput(targetProfile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        distance = adsk.core.ValueInput.createByReal(BG_DEPTH)  # Extrude depth in cm
        extInput.setDistanceExtent(False, distance)
        extrudes.add(extInput)
    
# Function adjusted to accept an offset for the plane
def drawSuperellipseWithCenterHole(rootComp, depth, n, numPoints, scaleX, scaleY, name, offset):
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
    
    # Extrude if needed
    if EXTRUDE:
        # Identify the correct profile for extrusion
        targetProfile = None
        maxArea = 0
        for profile in sketch.profiles:
            area = profile.areaProperties().area
            if area > maxArea:
                maxArea = area
                targetProfile = profile

        if targetProfile is not None:
            # Extrude the target profile
            extrudes = rootComp.features.extrudeFeatures
            extInput = extrudes.createInput(targetProfile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            distance = adsk.core.ValueInput.createByReal(depth)  # Extrude depth in cm
            extInput.setDistanceExtent(False, distance)
            extrudes.add(extInput)

# Assuming the offsetPlane has already been defined for your superellipse layer
def drawInscribedCircleInSuperellipse(rootComp, name, offset):
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
    sketch.name = name + '-inscribed-circle' 
    
    # Calculate the radius of the inscribed circle for the outer superellipse (astroid)
    # Adjusted for the astroid scaled to fit within scaleX by scaleY area
    # The radius calculation is done based on the normalized astroid's inscribed circle radius
    inscribedCircleRadius = 50  # Calculated radius of the inscribed circle scaled to fit the astroid

    # Add a circle in the middle with the calculated radius
    center = adsk.core.Point3D.create(0, 0, 0)
    sketch.sketchCurves.sketchCircles.addByCenterRadius(center, inscribedCircleRadius)
    


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
