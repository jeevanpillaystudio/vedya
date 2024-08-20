import adsk.core, adsk.fusion


def create_component(
    component: adsk.fusion.Component, name: str
) -> adsk.fusion.Component:
    newComp = component.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    newComp.component.name = name
    return newComp.component


def is_component_exist(component: adsk.fusion.Component, name: str) -> bool:
    return component.occurrences.itemByName(name + ":1") is not None


def move_body(
    root_component: adsk.fusion.Component,
    body: adsk.fusion.BRepBody,
    x: float,
    y: float,
):
    bodies = adsk.core.ObjectCollection.create()
    bodies.add(body)
    vector = adsk.core.Vector3D.create(x, y, 0)
    transform = adsk.core.Matrix3D.create()
    transform.translation = vector
    move_feature = root_component.features.moveFeatures
    move_feature_input = move_feature.createInput2(bodies)
    move_feature_input.defineAsFreeMove(transform)
    move_feature.add(move_feature_input)


def scale_body(
    root_component: adsk.fusion.Component,
    body: adsk.fusion.BRepBody,
    scale_x: float = 1,
    scale_y: float = 1,
    scale_z: float = 1,
    sketch_pt: adsk.fusion.SketchPoint = None,
):
    bodies = adsk.core.ObjectCollection.create()
    bodies.add(body)
    scale_factor = adsk.core.ValueInput.createByReal(1)
    scale_feature = root_component.features.scaleFeatures
    scale_feature_input = scale_feature.createInput(bodies, sketch_pt, scale_factor)
    xScale = adsk.core.ValueInput.createByReal(scale_x)
    yScale = adsk.core.ValueInput.createByReal(scale_y)
    zScale = adsk.core.ValueInput.createByReal(scale_z)
    scale_feature_input.setToNonUniform(xScale, yScale, zScale)
    scale = scale_feature.add(scale_feature_input)
    return scale


def combine_body(
    root_component: adsk.fusion.Component,
    target_body: adsk.fusion.BRepBody,
    tool_bodies: adsk.core.ObjectCollection,
    operation=adsk.fusion.FeatureOperations.CutFeatureOperation,
):
    combine_feature = root_component.features.combineFeatures
    combine_feature_input = root_component.features.combineFeatures.createInput(
        target_body, tool_bodies
    )
    combine_feature_input.operation = operation
    combine_feature_input.isKeepToolBodies = False
    combine_feature_input.isNewComponent = False
    combine_feature.add(combine_feature_input)


def copy_body(root_component, body, name) -> adsk.fusion.BRepBody:
    copied_body = root_component.features.copyPasteBodies.add(body)
    real_body = copied_body.bodies.item(0)
    real_body.name = name
    return real_body
