import math

from ..aggregator.index import run_aggregator
from ...geometry_utils import create_offset_plane
from ...component_utils import create_component
from ....design.shire.lib import create_component_name
from ....utils import log, timer
import adsk.core, adsk.fusion

FABRICATION_NAME = "slicer"


def start_slicer(
    component: adsk.fusion.Component,
    sliced_layer_depth: float,
    sliced_layer_count: float,
):
    log(f"INFO: starting start_slicer: {component.name}")

    # Create a new component for the slicing operation
    slicer_comp = create_component(component, create_component_name(FABRICATION_NAME))

    # run the aggregator
    body = run_aggregator(root_component=component, target_component=slicer_comp)

    # rename
    body.name = f"{FABRICATION_NAME}-body-root"

    # slice the body
    slice_body(slicer_comp, body, sliced_layer_depth, sliced_layer_count)

    log(f"INFO: completed start_slicer: {component.name}")


@timer
def slice_body(
    slicer_component: adsk.fusion.Component,
    body: adsk.fusion.BRepBody,
    sliced_layer_depth: float,
    sliced_layer_count: float,
):
    log(
        f"slice_body: body: {body.name}, sliced_layer_depth: {sliced_layer_depth}, sliced_layer_count: {sliced_layer_count}"
    )

    # Get the bounding box of the body
    bounding_box = body.boundingBox
    min_point = bounding_box.minPoint
    max_point = bounding_box.maxPoint

    # Calculate the dimensions
    height = max_point.z - min_point.z

    # Calculate the number of slices and the height of each slice
    slice_height = sliced_layer_depth
    slice_count = int(min(sliced_layer_count, math.floor(height / slice_height)))

    # Log the details (assumed log function exists or use print instead)
    log(
        f"slice_body: height: {height}, slice_count: {slice_count}, slice_height: {slice_height}"
    )

    # Iterate to create each slice
    for i in range(slice_count):
        # Calculate the offset for the current plane
        offset = min_point.z + ((i + 1) * slice_height)

        # Create an offset plane at the calculated position
        offset_plane = create_offset_plane(
            slicer_component, offset, name=f"plane-slice-{i}"
        )

        # log
        log(f"slice_body: offset_plane: {offset_plane.name}, offset: {offset}")

        # Split the body using the created plane

        split_body_features = slicer_component.features.splitBodyFeatures
        split_body_input = split_body_features.createInput(body, offset_plane, True)
        newBodies = split_body_features.add(split_body_input).bodies

        # Get the new body
        slice_body = newBodies.item(0)
        slice_body.name = f"{FABRICATION_NAME}-body-{i}"

        # replace the original body with the new body
        body = newBodies.item(1)
        body.name = f"{FABRICATION_NAME}-body-remaining"
