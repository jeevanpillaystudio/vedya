import adsk.core, adsk.fusion
from ...core.types import FabricationType
from ...core.component_utils import (
    component_exist,
    create_component,
)
from ...core.geometry.rectangle import calculate_rectangle_area, draw_rectangle
from ...core.geometry_utils import create_sketch, extrude_profile_by_area
from .config import BackgroundConfig


def create_bg(component: adsk.fusion.Component):
    if not component_exist(component=component, name=create_component_name("bg")):
        core_structural_comp = create_component(
            component=component, name=create_component_name("bg")
        )
        sketch = create_sketch(core_structural_comp, "bg-rect", offset=0.0)
        draw_rectangle(
            sketch=sketch,
            length=BackgroundConfig.MaxLength,
            width=BackgroundConfig.MaxWidth,
        )
        extrude_profile_by_area(
            component=core_structural_comp,
            profiles=sketch.profiles,
            area=calculate_rectangle_area(
                BackgroundConfig.MaxLength, BackgroundConfig.MaxWidth
            ),
            extrude_height=BackgroundConfig.ExtrudeHeight,
            name="bg-rect",
        )


def create_component_name(name: str):
    return f"{FabricationType.get_name(FabricationType.CNC_MILL).lower()}-{name}"
