import adsk.core, adsk.fusion
from ...utils import log

FP_TOLERANCE = 1e-2  # 0.1 Precision for floating point comparison


def create_offset_plane(
    component: adsk.fusion.Component,
    offset: float,
    name: str = "",
    plane: adsk.fusion.ConstructionPlane = None,
) -> adsk.fusion.ConstructionPlane:
    if plane is None:
        plane = component.xYConstructionPlane
    log(f"DEBUG: Creating offset plane with offset {offset}, plane {plane.name}")
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
