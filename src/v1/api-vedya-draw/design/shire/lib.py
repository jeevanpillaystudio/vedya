import math
import adsk.core, adsk.fusion
from ...core.depth_utils import DepthEffect, DepthRepeat, depth_repeat_iterator
from ...core.geometry.circle import calculate_circle_area, draw_circle
from ...utils.lib import log, timer
from ...core.types import FabricationType
from ...core.component_utils import (
    combine_body,
    component_exist,
    create_component,
)
from ...core.geometry.rectangle import (
    calculate_rectangle_area,
    calculate_three_point_rectangle_area,
    draw_rectangle,
    draw_rotated_rectangle,
)
from ...core.geometry_utils import (
    create_sketch,
    extrude_profile_by_area,
    extrude_single_profile_by_area,
    extrude_thin_one,
)
from .config import SCALE_FACTOR, AppConfig, BackgroundConfig, DiagonalRectangleConfig


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


def create_component_seed_of_life_layer_0(root_comp: adsk.fusion.Component):
    if not component_exist(
        root_comp, create_component_name("layer-0-seed-of-life-x-1")
    ):
        # top level comp
        seed_of_life_comp = create_component(
            component=root_comp,
            name=create_component_name("layer-0-seed-of-life-x-1"),
        )

        # start layer offset
        start_layer_offset = AppConfig.LayerDepth * 4

        # iterate; the enumerator is an array of multiples of 8; e.g [32, 40, 48, 56, 64, 72, 80]
        # for (_, radius) in enumerate(create_array_random_unique_multiples(size=2, multiple=8 * SCALE_FACTOR, min_multiple=4, max_multiple=10)):
        # 32 64
        # 16 56
        # 16 56 64
        # 32 56
        # 16 20
        # 16 24
        # 16 32 v nice
        # 16 48, 16 72 more negative space
        # 16 56 crazy
        # 16 64 lots of cuts interesting
        # 20 56
        # 20 64 v nice. BIG potenially.
        # 24 56
        for _, values in enumerate(
            [
                [
                    20 * SCALE_FACTOR,
                    0.96 * SCALE_FACTOR,
                    AppConfig.LayerDepth * 2,
                    4,
                ],
                [
                    64 * SCALE_FACTOR,
                    2.88 * SCALE_FACTOR,
                    AppConfig.LayerDepth,
                    4,
                ],
            ]
        ):
            # init
            radius, stroke_weight, extrude_height, depth_repeat = (
                values[0],
                values[1],
                values[2],
                values[3],
            )

            log(
                f"INIT seed-of-life-layer-0: radius: {radius}, stroke-weight: {stroke_weight}, extrude-height: {extrude_height}, depth-repeat: {depth_repeat}"
            )

            # comp
            seed_of_life_layer_0_comp = create_component(
                component=seed_of_life_comp,
                name=create_component_name("seed-of-life-layer-0-" + str(radius)),
            )

            # extrude height
            extrude_height_per_layer = extrude_height / depth_repeat

            # draw from middle
            center_x = 0
            center_y = 0

            # stroke weight
            # stroke_weight = create_array_random_unique_multiples(size=1, multiple=0.48 * SCALE_FACTOR, min_multiple=1, max_multiple=6)[0]

            # cirlce
            circle_radius = 36.0 * SCALE_FACTOR

            # depth iterator
            for layer_offset, sw in depth_repeat_iterator(
                depth_repeat=depth_repeat,
                start_layer_offset=start_layer_offset,
                extrude_height=extrude_height_per_layer,
                stroke_weight=stroke_weight,
                direction=DepthRepeat.Decrement,
            ):
                seed_of_life_layer_0_inner_comp = create_component(
                    component=seed_of_life_layer_0_comp,
                    name=create_component_name(
                        "seed-of-inner-layer-" + str(layer_offset) + "-" + str(sw)
                    ),
                )
                log(
                    f"INIT seed-of-life-layer-0: depth-repeat 2, initial-radius: {radius}, extrude-height-per-layer: {extrude_height_per_layer}, stroke-weight: {sw}"
                )
                create_seed_of_life(
                    component=seed_of_life_layer_0_inner_comp,
                    center_x=center_x,
                    center_y=center_y,
                    radius=radius,
                    extrude_height=extrude_height_per_layer,
                    stroke_weight=sw,
                    layer_offset=layer_offset,
                    side=DepthEffect.Center,
                )

                sketch = create_sketch(
                    seed_of_life_layer_0_inner_comp,
                    "seed-of-life-intersect",
                    offset=layer_offset,
                )
                draw_circle(sketch=sketch, radius=circle_radius)
                draw_rotated_rectangle(
                    sketch=sketch,
                    width=DiagonalRectangleConfig.OuterDiagonalRectangleWidth,
                    height=DiagonalRectangleConfig.OuterDiagonalRectangleHeight,
                )
                extrude_single_profile_by_area(
                    component=seed_of_life_layer_0_inner_comp,
                    profiles=sketch.profiles,
                    area=calculate_circle_area(circle_radius)
                    - calculate_three_point_rectangle_area(
                        DiagonalRectangleConfig.OuterDiagonalRectangleWidth,
                        DiagonalRectangleConfig.OuterDiagonalRectangleHeight,
                    ),
                    extrude_height=extrude_height_per_layer,
                    name="seed-of-life-intersect",
                    operation=adsk.fusion.FeatureOperations.IntersectFeatureOperation,
                )

                # invert the joint body; re should always be in first occurance
                invert_bodies = adsk.core.ObjectCollection.create()
                for body in seed_of_life_layer_0_inner_comp.bRepBodies:
                    invert_bodies.add(body)
                sketch = create_sketch(
                    seed_of_life_layer_0_inner_comp,
                    "seed-of-life-inverse",
                    offset=layer_offset,
                )
                draw_circle(sketch=sketch, radius=circle_radius)
                draw_rotated_rectangle(
                    sketch=sketch,
                    width=DiagonalRectangleConfig.OuterDiagonalRectangleWidth,
                    height=DiagonalRectangleConfig.OuterDiagonalRectangleHeight,
                )
                invert_body = extrude_single_profile_by_area(
                    component=seed_of_life_layer_0_inner_comp,
                    profiles=sketch.profiles,
                    area=calculate_circle_area(circle_radius)
                    - calculate_three_point_rectangle_area(
                        DiagonalRectangleConfig.OuterDiagonalRectangleWidth,
                        DiagonalRectangleConfig.OuterDiagonalRectangleHeight,
                    ),
                    extrude_height=extrude_height_per_layer,
                    name="seed-of-life-inverse",
                    operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
                )
                combine_body(
                    seed_of_life_layer_0_inner_comp,
                    invert_body,
                    invert_bodies,
                    operation=adsk.fusion.FeatureOperations.CutFeatureOperation,
                )

        # only in bounds
        # sketch = create_sketch(seed_of_life_comp, 'seed-of-life-bound-intersect', offset=start_layer_offset)
        # extrude_height = AppConfig.LayerDepth * 2
        # draw_rectangle(sketch=sketch, length=AppConfig.MaxLength, width=AppConfig.MaxWidth)
        # extrude_single_profile_by_area(component=seed_of_life_comp, profiles=sketch.profiles, area=calculate_rectangle_area(AppConfig.MaxLength, AppConfig.MaxWidth), extrude_height=AppConfig.LayerDepth * 2, name='seed-of-life-bound-intersect', operation=adsk.fusion.FeatureOperations.IntersectFeatureOperation)


def create_component_seed_of_life_layer_2(root_comp: adsk.fusion.Component):
    if not component_exist(root_comp, create_component_name("layer-2-seed-of-life-x")):
        # top level comp
        seed_of_life_comp = create_component(
            component=root_comp,
            name=create_component_name("layer-2-seed-of-life-x"),
        )

        # start layer offset
        start_layer_offset = AppConfig.LayerDepth * 4

        # iterate; the enumerator is an array of multiples of 8; e.g [32, 40, 48, 56, 64, 72, 80]
        # for (_, radius) in enumerate(create_array_random_unique_multiples(size=2, multiple=8 * SCALE_FACTOR, min_multiple=4, max_multiple=10)):
        for _, values in enumerate(
            [
                [
                    44 * SCALE_FACTOR,
                    0.96 * SCALE_FACTOR,
                    AppConfig.LayerDepth * 4,
                    6,
                ],
                [
                    72 * SCALE_FACTOR,
                    0.96 * SCALE_FACTOR,
                    AppConfig.LayerDepth * 2,
                    4,
                ],
            ]
        ):
            # init
            radius, stroke_weight, extrude_height, depth_repeat = (
                values[0],
                values[1],
                values[2],
                values[3],
            )

            # comp
            seed_of_life_layer_0_comp = create_component(
                component=seed_of_life_comp,
                name=create_component_name("seed-of-life-layer-0-" + str(radius)),
            )

            # draw from middle
            center_x = 0
            center_y = 0

            # extrude height
            extrude_height_per_layer = extrude_height / depth_repeat

            # circle radius
            circle_radius = 36.0 * SCALE_FACTOR
            extra_leway = 16.0 * SCALE_FACTOR

            # depth iterator
            for layer_offset, sw in depth_repeat_iterator(
                depth_repeat=depth_repeat,
                start_layer_offset=start_layer_offset,
                extrude_height=extrude_height_per_layer,
                stroke_weight=stroke_weight,
                direction=DepthRepeat.Decrement,
            ):
                seed_of_life_layer_0_inner_comp = create_component(
                    component=seed_of_life_layer_0_comp,
                    name=create_component_name(
                        "seed-of-inner-layer-" + str(layer_offset) + "-" + str(sw)
                    ),
                )
                log(
                    f"INIT seed-of-life-layer-0: depth-repeat 2, initial-radius: {radius}, extrude-height-per-layer: {extrude_height_per_layer}, stroke-weight: {sw}"
                )
                create_seed_of_life(
                    component=seed_of_life_layer_0_inner_comp,
                    center_x=center_x,
                    center_y=center_y,
                    radius=radius,
                    extrude_height=extrude_height_per_layer,
                    stroke_weight=sw,
                    layer_offset=layer_offset,
                    side=DepthEffect.Center,
                )

                # intersect with draw rotated rectangle
                sketch = create_sketch(
                    seed_of_life_layer_0_inner_comp,
                    "seed-of-life-intersect",
                    offset=layer_offset,
                )
                draw_rectangle(
                    sketch=sketch,
                    length=circle_radius * 2 + extra_leway,
                    width=AppConfig.MaxWidth,
                )
                draw_circle(sketch=sketch, radius=circle_radius)
                extrude_profile_by_area(
                    component=seed_of_life_layer_0_inner_comp,
                    profiles=sketch.profiles,
                    area=calculate_rectangle_area(
                        circle_radius * 2 + extra_leway, AppConfig.MaxWidth
                    )
                    - calculate_circle_area(circle_radius),
                    extrude_height=extrude_height_per_layer,
                    name="seed-of-life-intersect",
                    operation=adsk.fusion.FeatureOperations.IntersectFeatureOperation,
                )

                # invert the joint body; re should always be in first occurance
                invert_bodies = adsk.core.ObjectCollection.create()
                for body in seed_of_life_layer_0_inner_comp.bRepBodies:
                    invert_bodies.add(body)
                sketch = create_sketch(
                    seed_of_life_layer_0_inner_comp,
                    "seed-of-life-inverse",
                    offset=layer_offset,
                )
                draw_rectangle(
                    sketch=sketch,
                    length=circle_radius * 2 + extra_leway,
                    width=AppConfig.MaxWidth,
                )
                draw_circle(sketch=sketch, radius=circle_radius)
                invert_body = extrude_single_profile_by_area(
                    component=seed_of_life_layer_0_inner_comp,
                    profiles=sketch.profiles,
                    area=calculate_rectangle_area(
                        circle_radius * 2 + extra_leway, AppConfig.MaxWidth
                    )
                    - calculate_circle_area(circle_radius),
                    extrude_height=extrude_height_per_layer,
                    name="seed-of-life-invert",
                    operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
                )
                combine_body(
                    seed_of_life_layer_0_inner_comp,
                    invert_body,
                    invert_bodies,
                    operation=adsk.fusion.FeatureOperations.CutFeatureOperation,
                )

        # only in bounds
        sketch = create_sketch(
            seed_of_life_comp, "seed-of-life-bound-intersect", offset=start_layer_offset
        )
        extrude_height = AppConfig.LayerDepth * 4
        draw_rectangle(
            sketch=sketch, length=AppConfig.MaxLength * 2, width=AppConfig.MaxWidth * 2
        )
        draw_rectangle(
            sketch=sketch, length=AppConfig.MaxLength, width=AppConfig.MaxWidth
        )
        extrude_single_profile_by_area(
            component=seed_of_life_comp,
            profiles=sketch.profiles,
            area=calculate_rectangle_area(
                AppConfig.MaxLength * 2, AppConfig.MaxWidth * 2
            )
            - calculate_rectangle_area(AppConfig.MaxLength, AppConfig.MaxWidth),
            extrude_height=extrude_height,
            name="seed-of-life-bound-intersect",
            operation=adsk.fusion.FeatureOperations.CutFeatureOperation,
        )


@timer
def create_seed_of_life(
    component: adsk.fusion.Component,
    center_x,
    center_y,
    radius,
    extrude_height,
    stroke_weight,
    layer_offset,
    side: adsk.fusion.ThinExtrudeWallLocation = adsk.fusion.ThinExtrudeWallLocation.Side1,
    plane: adsk.fusion.ConstructionPlane = None,
    start_from: adsk.fusion.BRepBody = None,
):
    # radius, stroke-weight, extrude-height difference each layer is based on j; gives it the "depth" effect
    r = radius
    sw = stroke_weight
    eh = extrude_height
    log(
        f"CREATE seed-of-life-inner: radius: {r} and stroke-weight: {sw} and extrude-height: {eh}"
    )

    # draw the center circle
    sketch = create_sketch(
        component, "seed-of-life-" + str(r) + "-center", layer_offset, plane
    )
    draw_circle(sketch, r, center_x, center_y)
    initial_body = extrude_thin_one(
        component=component,
        profile=sketch.profiles[0],
        extrudeHeight=eh,
        strokeWeight=sw,
        name="seed-of-life-center-" + str(r),
        operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        start_from=start_from,
    )
    initial_body.name = "seed-of-life-center-" + str(r)

    # draw; this is a standard seed of life algorithm.
    for i in range(6):
        # radiant angle; see obsidian://open?vault=Obsidian%20Vault&file=personal%2Fart-composition%2Fimages%2Feducation-radiant-circle-measure.png
        angle = math.radians(i * 60)
        x = center_x + r * math.cos(angle)
        y = center_y + r * math.sin(angle)

        # draw
        sketch = create_sketch(
            component,
            "seed-of-life-" + str(r) + "-" + str(angle),
            layer_offset,
            plane,
        )
        draw_circle(sketch, r, x, y)
        extrude_thin_one(
            component=component,
            profile=sketch.profiles[0],
            extrudeHeight=eh,
            name="seed-of-life-" + str(r) + "-" + str(angle),
            strokeWeight=sw,
            operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
            side=side,
            start_from=start_from,
        )


def create_component_name(name: str):
    return f"{FabricationType.get_name(FabricationType.CNC_MILL).lower()}-{name}"
