import adsk.core, adsk.fusion

FP_TOLERANCE = 1e-2  # 0.1 Precision for floating point comparison


def create_offset_plane(
    component: adsk.fusion.Component,
    offset: float,
    name: str = "",
    plane: adsk.fusion.ConstructionPlane = None,
) -> adsk.fusion.ConstructionPlane:
    if plane is None:
        plane = component.xYConstructionPlane
    planes = component.constructionPlanes
    planeInput = planes.createInput()
    offsetValue = adsk.core.ValueInput.createByReal(offset)
    planeInput.setByOffset(plane, offsetValue)
    offsetPlane = planes.add(planeInput)
    if name:
        offsetPlane.name = name
    return offsetPlane


def create_sketch(
    component: adsk.fusion.Component,
    name: str,
    offset: float = 0.0,
    plane: adsk.fusion.ConstructionPlane = None,
) -> adsk.fusion.Sketch:
    sketches = component.sketches
    sketch = sketches.add(create_offset_plane(component, offset, plane=plane))
    sketch.name = name
    return sketch


def extrude_profile_by_area(
    component: adsk.fusion.Component,
    profiles: list[adsk.fusion.Profile],
    area: float,
    extrude_height: float,
    name: str,
    operation: adsk.fusion.FeatureOperations = adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    fp_tolerance: float = FP_TOLERANCE,
) -> adsk.core.ObjectCollection:
    bodies = adsk.core.ObjectCollection.create()
    extrudes = component.features.extrudeFeatures
    for profile in profiles:
        if (
            abs(profile.areaProperties().area - area) < fp_tolerance
            or abs(profile.areaProperties().area - area) == 0.0
        ):
            extInput = extrudes.createInput(profile, operation=operation)
            extInput.setDistanceExtent(
                False, adsk.core.ValueInput.createByReal(extrude_height)
            )
            extrude = extrudes.add(extInput)
            body = extrude.bodies.item(0)
            body.name = name
            bodies.add(body)
    if bodies.count > 0:
        return bodies
    raise ValueError("Failed to find the profile for extrusion")


def extrude_single_profile_by_area(
    component: adsk.fusion.Component,
    profiles: list[adsk.fusion.Profile],
    area: float,
    extrude_height: float,
    name: str,
    operation: adsk.fusion.FeatureOperations = adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    fp_tolerance: float = FP_TOLERANCE,
) -> adsk.fusion.BRepBody:
    extrudes = component.features.extrudeFeatures
    for profile in profiles:
        if abs(profile.areaProperties().area - area) < fp_tolerance:
            extInput = extrudes.createInput(profile, operation=operation)
            extInput.setDistanceExtent(
                False, adsk.core.ValueInput.createByReal(extrude_height)
            )
            extrude = extrudes.add(extInput)
            body = extrude.bodies.item(0)
            body.name = name
            return body
    raise ValueError("Failed to find the profile for extrusion")


def extrude_thin_one(
    component: adsk.fusion.Component,
    profile: adsk.fusion.Profile,
    extrudeHeight: float,
    name: str,
    strokeWeight: int,
    operation: adsk.fusion.FeatureOperations = adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    side: adsk.fusion.ThinExtrudeWallLocation = adsk.fusion.ThinExtrudeWallLocation.Side1,
    start_from: adsk.fusion.BRepBody = None,
):
    extrudes = component.features.extrudeFeatures
    extrudeInput = extrudes.createInput(profile, operation=operation)

    if start_from is not None:
        mm0 = adsk.core.ValueInput.createByString("0 mm")
        start_from_extent = adsk.fusion.FromEntityStartDefinition.create(
            start_from, mm0
        )
        extrudeInput.startExtent = start_from_extent

    extrudeInput.setThinExtrude(side, adsk.core.ValueInput.createByReal(strokeWeight))
    extrudeInput.setDistanceExtent(
        False, adsk.core.ValueInput.createByReal(extrudeHeight)
    )
    extrude = extrudes.add(extrudeInput)
    body = extrude.bodies.item(0)
    body.name = name
    return body
