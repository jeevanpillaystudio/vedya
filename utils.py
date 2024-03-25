import adsk.core

EXTRUDE = True
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

def extrude_profile_by_area(rootComp: adsk.fusion.Component, profiles: list[adsk.fusion.Profile], area: float, depth, bodyName):
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
    if not EXTRUDE:
        return
    
    for profile in profiles:
        if abs(profile.areaProperties().area - area) < FP_TOLERANCE:
            extrudes = rootComp.features.extrudeFeatures
            extInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            extInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(depth))
            extrude = extrudes.add(extInput)
            body = extrude.bodies.item(0)
            body.name = bodyName
            return body
    raise ValueError('Failed to find the profile for extrusion')