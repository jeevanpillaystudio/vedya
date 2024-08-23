import adsk.core, adsk.fusion
from ...component_utils import intersect_bodies, copy_body, create_component
from ....design.shire.lib import aggregate_all_bodies, create_component_name
from ....utils.lib import log

FABRICATION_NAME = "aggregator"


def start_aggregator(
    component: adsk.fusion.Component,
):
    log(f"INFO: starting start_aggregator: {component.name}")

    # create a new component for the aggregator
    aggregator_component = create_component(
        component, create_component_name(FABRICATION_NAME)
    )

    # run the aggregator
    body = run_aggregator(
        root_component=component, target_component=aggregator_component
    )

    # rename
    body.name = f"{FABRICATION_NAME}-body-root"


def run_aggregator(
    root_component: adsk.fusion.Component,
    target_component: adsk.fusion.Component,
) -> adsk.fusion.BRepBody:
    log(
        f"INFO: starting run_aggregator: root_component: {root_component.name}, target_component: {target_component.name}"
    )

    # Gather all bodies from the root component and its subcomponents
    all_bodies = aggregate_all_bodies(root_component)

    # Combine the rest of the bodies with the main body
    tool_bodies = adsk.core.ObjectCollection.create()
    for i in range(all_bodies.count):
        body_copy = copy_body(root_component, all_bodies.item(i), "body-" + str(i))
        tool_bodies.add(body_copy)

    # Perform the combination
    first_body = tool_bodies.item(0)
    tool_bodies.removeByIndex(0)
    intersect_bodies(
        target_component,
        first_body,
        tool_bodies,
        adsk.fusion.FeatureOperations.JoinFeatureOperation,
    )

    log(
        f"INFO: completed run_aggregator: root_component: {root_component.name}, target_component: {target_component.name}"
    )

    return first_body
