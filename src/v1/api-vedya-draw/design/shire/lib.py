from core.component_utils import (
    component_exist,
    create_component,
    create_component_name,
)
from core.geometry.rectangle import calculate_rectangle_area, draw_rectangle
from core.geometry_utils import create_sketch, extrude_profile_by_area
import adsk.core, adsk.fusion
from design.shire.config import BackgroundConfig


def create_bg(root_comp: adsk.fusion.Component):
    if not component_exist(root_comp, create_component_name("bg")):
        core_structural_comp = create_component(
            component=root_comp, name=create_component_name("bg")
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
