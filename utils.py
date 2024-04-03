import random
import adsk.core, adsk.fusion
import datetime
import os

FP_TOLERANCE = 1e-2 # 0.01 Precision for floating point comparison

def create_offset_plane(rootComp, offset):
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
    offsetValue = adsk.core.ValueInput.createByReal(offset)
    planeInput.setByOffset(xyPlane, offsetValue)
    offsetPlane = planes.add(planeInput)
    return offsetPlane

def create_sketch(rootComp, name, offset=0):
    """
    Creates a sketch on the specified plane.

    Parameters:
    - rootComp: The root component to which the sketch is added.
    - sketchName: The name of the sketch.

    Returns:
    - The created sketch.
    """
    sketches = rootComp.sketches
    sketch = sketches.add(create_offset_plane(rootComp, offset))
    sketch.name = name
    return sketch

def extrude_profile_by_area(component: adsk.fusion.Component, profiles: list[adsk.fusion.Profile], area: float, depth, name, operation: adsk.fusion.FeatureOperations=adsk.fusion.FeatureOperations.NewBodyFeatureOperation):
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
    extrudes = component.features.extrudeFeatures
    for profile in profiles:
        if abs(profile.areaProperties().area - area) < FP_TOLERANCE:
            extInput = extrudes.createInput(profile, operation=operation)
            extInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(depth))
            extrude = extrudes.add(extInput)
            body = extrude.bodies.item(0)
            body.name = name
            return body
    raise ValueError('Failed to find the profile for extrusion')

def extrude_thin_one(component: adsk.fusion.Component, profile: adsk.fusion.Profile, depth, name, strokeWeight: int, operation: adsk.fusion.FeatureOperations=adsk.fusion.FeatureOperations.NewBodyFeatureOperation):
    """
    Creates a thin extrusion based on the specified depth for the given profile.
    
    Parameters:
    - rootComp: The root component to which the extrusion is added.
    - profiles: The profiles to thin extrude.
    - depth: The depth of the extrusion.
    - bodyName: The name of the body created by the extrusion.
    
    Returns:
    - The body created by the extrusion based on the specified depth.
    """
    extrudes = component.features.extrudeFeatures
    extrudeInput = extrudes.createInput(profile, operation=operation)
    extrudeInput.setThinExtrude(adsk.fusion.ThinExtrudeWallLocation.Side1, adsk.core.ValueInput.createByReal(strokeWeight))
    extrudeInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(depth))
    extrude = extrudes.add(extrudeInput)
    body = extrude.bodies.item(0)
    body.name = name
    return body

def create_component(root_component: adsk.fusion.Component, name) -> adsk.fusion.Component:
    # Create a new component
    newComp = root_component.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    newComp.component.name = name
    return newComp.component

def component_exist(root_component: adsk.fusion.Component, name) -> bool:
    return root_component.occurrences.itemByName(name + ":1") is not None

def log(value):
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"{timestamp} INFO: {str(value)}\n"
        
        # Write the log message to the a file
        with open("/Users/jeevanpillay/Library/Application Support/Autodesk/Autodesk Fusion 360/API/Scripts/APIDrawVedya/logfile.txt", "a") as file:
            file.write(log_message)
        
        print("Values written to logfile.txt successfully.")
    except Exception as e:
        print("An error occurred while writing to logfile.txt:", str(e))
        
# Redefine the function to generate unique values without using numpy
def create_array_random_unique_multiples(size: int, multiple: int = 8, min_multiple: int = 1, max_multiple: int = 10):
    values = set()
    while len(values) < size:
        # Generate a unique value that is a multiple of 8, increasing range for uniqueness
        value = multiple * random.randint(min_multiple, max_multiple)
        values.add(value)
    return sorted(list(values))