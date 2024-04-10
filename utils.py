import random
import adsk.core, adsk.fusion
import datetime
import os
import time

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

def extrude_profile_by_area(component: adsk.fusion.Component, profiles: list[adsk.fusion.Profile], area: float, depth, name, operation: adsk.fusion.FeatureOperations=adsk.fusion.FeatureOperations.NewBodyFeatureOperation) -> adsk.core.ObjectCollection:
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
    bodies = adsk.core.ObjectCollection.create()
    extrudes = component.features.extrudeFeatures
    for profile in profiles:
        if abs(profile.areaProperties().area - area) < FP_TOLERANCE:
            extInput = extrudes.createInput(profile, operation=operation)
            extInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(depth))
            extrude = extrudes.add(extInput)
            body = extrude.bodies.item(0)
            body.name = name
            bodies.add(body)
    if bodies.count > 0:
        return bodies
    raise ValueError('Failed to find the profile for extrusion')

def extrude_thin_one(component: adsk.fusion.Component, profile: adsk.fusion.Profile, extrudeHeight, name, strokeWeight: int, operation: adsk.fusion.FeatureOperations=adsk.fusion.FeatureOperations.NewBodyFeatureOperation, side: adsk.fusion.ThinExtrudeWallLocation=adsk.fusion.ThinExtrudeWallLocation.Side1):
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
    extrudeInput.setThinExtrude(side, adsk.core.ValueInput.createByReal(strokeWeight))
    extrudeInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(extrudeHeight))
    extrude = extrudes.add(extrudeInput)
    body = extrude.bodies.item(0)
    body.name = name
    return body

def create_component(root_component: adsk.fusion.Component, component_name) -> adsk.fusion.Component:
    # Create a new component
    newComp = root_component.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    newComp.component.name = component_name
    return newComp.component

def component_exist(root_component: adsk.fusion.Component, name) -> bool:
    return root_component.occurrences.itemByName(name + ":1") is not None

def log(value):
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"{timestamp} INFO: {str(value)}\n"
        
        # Write the log message to the a file
        with open("/Users/jeevanpillay/Documents - triangle/Developer/Repository/@jeevanpillaystudio/vedya/logfile.txt", "a") as file:
            file.write(log_message)
        
        print("Values written to logfile.txt successfully.")
    except Exception as e:
        print("An error occurred while writing to logfile.txt:", str(e))
        
# Redefine the function to generate unique values without using numpy
import random

def create_array_random_unique_multiples(size: int, multiple: int = 8, min_multiple: int = 1, max_multiple: int = 10):
    """
    Generate a list of random unique multiples of a given number.

    Args:
        size (int): The number of unique multiples to generate.
        multiple (int, optional): The base number to generate multiples of. Defaults to 8.
        min_multiple (int, optional): The minimum multiplier for generating multiples. Defaults to 1.
        max_multiple (int, optional): The maximum multiplier for generating multiples. Defaults to 10.

    Returns:
        list: A sorted list of unique multiples of the given number.
        e.g create_array_random_unique_multiples(5, 8, 1, 10) -> [8, 16, 24, 32, 40]
    """
    values = set()
    while len(values) < size:
        # Generate a unique value that is a multiple of the given number, increasing range for uniqueness
        value = multiple * random.randint(min_multiple, max_multiple)
        values.add(value)
    return sorted(list(values))

def timer(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        log(f"TIMER '{func.__name__}' took {end_time - start_time} seconds to run.")
        return result
    return wrapper

def scale_body(root_component: adsk.fusion.Component, body: adsk.fusion.BRepBody, scale_x: float = 1, scale_y: float = 1, scale_z: float = 1, sketch_pt: adsk.fusion.SketchPoint = None):
    # init
    bodies = adsk.core.ObjectCollection.create()
    bodies.add(body)
        
    # init values    
    scale_factor = adsk.core.ValueInput.createByReal(1) # @todo auto set to 1; doesn't have to be.
    
    # create the scale feature
    scale_feature = root_component.features.scaleFeatures
    scale_feature_input = scale_feature.createInput(bodies, sketch_pt, scale_factor)
    
    # set scale to be non-uniform
    xScale = adsk.core.ValueInput.createByReal(scale_x)
    yScale = adsk.core.ValueInput.createByReal(scale_y)
    zScale = adsk.core.ValueInput.createByReal(scale_z)
    scale_feature_input.setToNonUniform(xScale, yScale, zScale)
    
    # scale
    scale = scale_feature.add(scale_feature_input)
    
    return scale
    
def move_body(root_component: adsk.fusion.Component, x, y, body: adsk.fusion.BRepBody):
    # init
    bodies = adsk.core.ObjectCollection.create()
    bodies.add(body)
        
    # move body transforms
    vector = adsk.core.Vector3D.create(x, y, 0)
    transform = adsk.core.Matrix3D.create()
    transform.translation = vector
        
    # create the move feature
    move_feature = root_component.features.moveFeatures
    move_feature_input = move_feature.createInput2(bodies)
    move_feature_input.defineAsFreeMove(transform)
    move_feature.add(move_feature_input)

def copy_body(root_component, body, name) -> adsk.fusion.BRepBody:
    copied_body = root_component.features.copyPasteBodies.add(body)
    real_body = copied_body.bodies.item(0)
    real_body.name = name
    return real_body