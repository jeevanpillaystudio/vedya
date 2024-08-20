import adsk.core, adsk.fusion
from ...core.types import FabricationType
from ...core.component_utils import (
    component_exist,
    create_component,
)
from ...core.geometry.rectangle import calculate_rectangle_area, draw_rectangle
from ...core.geometry_utils import (
    create_sketch,
    extrude_profile_by_area,
    extrude_thin_one,
)
from .config import AppConfig, BackgroundConfig


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


def create_border(root_comp):
    if not component_exist(root_comp, create_component_name("border")):
        layer_offset = AppConfig.LayerDepth * 2
        border_comp = create_component(
            component=root_comp, name=create_component_name("border")
        )
        extrude_height = AppConfig.LayerDepth * 6
        sketch = create_sketch(border_comp, "border", offset=layer_offset)
        draw_rectangle(
            sketch=sketch, length=AppConfig.MaxLength, width=AppConfig.MaxWidth
        )
        extrude_thin_one(
            component=border_comp,
            profile=sketch.profiles[0],
            extrudeHeight=extrude_height,
            strokeWeight=AppConfig.BorderWidth,
            name="border",
            operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        )


def create_component_name(name: str):
    return f"{FabricationType.get_name(FabricationType.CNC_MILL).lower()}-{name}"
