import math
import random
import adsk.core, adsk.fusion
from ...core.geometry.astroid import (
    calculate_astroid_area,
    draw_astroid,
    draw_astroid_stroke,
)
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
from .config import (
    SCALE_FACTOR,
    AppConfig,
    AstroidConfig,
    BackgroundConfig,
    DiagonalRectangleConfig,
    KailashConfig,
)


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


def create_component_seed_of_life_layer_1(root_comp: adsk.fusion.Component):
    if not component_exist(root_comp, create_component_name("layer-1-seed-of-life-x")):
        # top level comp
        seed_of_life_comp = create_component(
            component=root_comp,
            name=create_component_name("layer-1-seed-of-life-x"),
        )

        # start layer offset
        start_layer_offset = AppConfig.LayerDepth * 2

        # iterate; the enumerator is an array of multiples of 8; e.g [32, 40, 48, 56, 64, 72, 80]
        # for (_, radius) in enumerate(create_array_random_unique_multiples(size=2, multiple=8 * SCALE_FACTOR, min_multiple=4, max_multiple=10)):
        for _, values in enumerate(
            [
                (
                    28 * SCALE_FACTOR,
                    1.92 * SCALE_FACTOR,
                    AppConfig.LayerDepth * 4,
                    6,
                ),
                (
                    16 * SCALE_FACTOR,
                    0.96 * SCALE_FACTOR,
                    AppConfig.LayerDepth * 2,
                    4,
                ),
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

            # extrude height
            extrude_height_per_layer = extrude_height / depth_repeat

            # draw from middle
            center_x = 0
            center_y = 0

            # stroke weight
            # stroke_weight = create_array_random_unique_multiples(size=1, multiple=0.48 * SCALE_FACTOR, min_multiple=1, max_multiple=6)[0]

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
                # all_bodies.add(seed_of_life_inner_layer_comp.bRepBodies.item(0))

                # intersect with draw rotated rectangle
                sketch = create_sketch(
                    seed_of_life_layer_0_inner_comp,
                    "seed-of-life-intersect",
                    offset=layer_offset,
                )
                draw_rectangle(
                    sketch=sketch, length=AppConfig.MaxLength, width=AppConfig.MaxWidth
                )
                draw_rotated_rectangle(
                    sketch=sketch,
                    width=DiagonalRectangleConfig.OuterDiagonalRectangleWidth,
                    height=DiagonalRectangleConfig.OuterDiagonalRectangleHeight,
                )
                draw_rotated_rectangle(
                    sketch=sketch,
                    width=DiagonalRectangleConfig.MiddleDiagonalRectangleWidth,
                    height=DiagonalRectangleConfig.MiddleDiagonalRectangleHeight,
                )
                extrude_single_profile_by_area(
                    component=seed_of_life_layer_0_inner_comp,
                    profiles=sketch.profiles,
                    area=calculate_three_point_rectangle_area(
                        DiagonalRectangleConfig.OuterDiagonalRectangleWidth,
                        DiagonalRectangleConfig.OuterDiagonalRectangleHeight,
                    )
                    - calculate_three_point_rectangle_area(
                        DiagonalRectangleConfig.MiddleDiagonalRectangleHeight,
                        DiagonalRectangleConfig.MiddleDiagonalRectangleWidth,
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
                draw_rectangle(
                    sketch=sketch, length=AppConfig.MaxLength, width=AppConfig.MaxWidth
                )
                draw_rotated_rectangle(
                    sketch=sketch,
                    width=DiagonalRectangleConfig.OuterDiagonalRectangleWidth,
                    height=DiagonalRectangleConfig.OuterDiagonalRectangleHeight,
                )
                draw_rotated_rectangle(
                    sketch=sketch,
                    width=DiagonalRectangleConfig.MiddleDiagonalRectangleWidth,
                    height=DiagonalRectangleConfig.MiddleDiagonalRectangleHeight,
                )
                invert_body = extrude_single_profile_by_area(
                    component=seed_of_life_layer_0_inner_comp,
                    profiles=sketch.profiles,
                    area=calculate_three_point_rectangle_area(
                        DiagonalRectangleConfig.OuterDiagonalRectangleWidth,
                        DiagonalRectangleConfig.OuterDiagonalRectangleHeight,
                    )
                    - calculate_three_point_rectangle_area(
                        DiagonalRectangleConfig.MiddleDiagonalRectangleHeight,
                        DiagonalRectangleConfig.MiddleDiagonalRectangleWidth,
                    ),
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


def create_component_core(root_comp):
    if not component_exist(root_comp, create_component_name("core")):
        main_comp = create_component(
            component=root_comp, name=create_component_name("core")
        )

        # level 2D -----------
        layer_offset = AppConfig.LayerDepth * 2

        # draw the bottom layer diagonal
        sketch = create_sketch(main_comp, "seed-of-life-base", offset=layer_offset)
        extrude_height = AppConfig.LayerDepth * 2
        draw_rectangle(
            sketch=sketch, length=AppConfig.MaxLength, width=AppConfig.MaxWidth
        )
        draw_rotated_rectangle(
            sketch=sketch,
            width=DiagonalRectangleConfig.OuterDiagonalRectangleWidth,
            height=DiagonalRectangleConfig.OuterDiagonalRectangleHeight,
        )
        extrude_single_profile_by_area(
            component=main_comp,
            profiles=sketch.profiles,
            area=calculate_rectangle_area(AppConfig.MaxWidth, AppConfig.MaxLength)
            - calculate_three_point_rectangle_area(
                DiagonalRectangleConfig.OuterDiagonalRectangleWidth,
                DiagonalRectangleConfig.OuterDiagonalRectangleHeight,
            ),
            extrude_height=extrude_height,
            name="seed-of-life-base",
            operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        )

        # level 2.5D -----------

        # nothing....

        # level 2.5 -----------
        layer_offset = AppConfig.LayerDepth * 2.5

        # draw the rotated rectangle middle
        sketch = create_sketch(
            main_comp, "angled-rectangles-middle", offset=layer_offset
        )
        extrude_height = AppConfig.LayerDepth * 3
        draw_rotated_rectangle(
            sketch=sketch,
            width=DiagonalRectangleConfig.MiddleDiagonalRectangleWidth,
            height=DiagonalRectangleConfig.MiddleDiagonalRectangleHeight,
        )
        for profile in sketch.profiles:
            extrude_thin_one(
                component=main_comp,
                profile=profile,
                extrudeHeight=extrude_height,
                strokeWeight=DiagonalRectangleConfig.MiddleDiagonalRectangleStrokeWeight,
                name="angled-rectangles-middle",
                operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
            )

        # draw the astroid 64
        sketch = create_sketch(main_comp, "astroid-64-outer", offset=layer_offset)
        extrude_height = AppConfig.LayerDepth
        draw_astroid(
            sketch=sketch,
            n=AstroidConfig.N,
            num_points=AstroidConfig.NumPoints,
            scale_x=AstroidConfig.OuterAstroidRadius,
            scale_y=AstroidConfig.OuterAstroidRadius,
        )
        extrude_profile_by_area(
            component=main_comp,
            profiles=sketch.profiles,
            area=calculate_astroid_area(AstroidConfig.OuterAstroidRadius),
            extrude_height=extrude_height,
            name="astroid-64-outer",
            fp_tolerance=1e0,
        )

        # level 3D -----------
        layer_offset = AppConfig.LayerDepth * 3

        # draw the astroid 64 inner
        sketch = create_sketch(main_comp, "astroid-64-inner", offset=layer_offset)
        extrude_height = AppConfig.LayerDepth * 2
        draw_astroid(
            sketch=sketch,
            n=AstroidConfig.N,
            num_points=AstroidConfig.NumPoints,
            scale_x=AstroidConfig.OuterAstroidRadius
            - AstroidConfig.OuterAstroidStrokeWeight,
            scale_y=AstroidConfig.OuterAstroidRadius
            - AstroidConfig.OuterAstroidStrokeWeight,
        )
        extrude_profile_by_area(
            component=main_comp,
            profiles=sketch.profiles,
            area=calculate_astroid_area(
                AstroidConfig.OuterAstroidRadius
                - AstroidConfig.OuterAstroidStrokeWeight
            ),
            extrude_height=extrude_height,
            name="astroid-64-inner",
            fp_tolerance=1e0,
        )

        # level 5D -----------
        layer_offset = AppConfig.LayerDepth * 5

        # draw the rotated rectangle inner
        sketch = create_sketch(
            main_comp, "angled-rectangles-inner", offset=layer_offset
        )
        extrude_height = AppConfig.LayerDepth * 2
        draw_rotated_rectangle(
            sketch=sketch,
            width=DiagonalRectangleConfig.InnerDiagonalRectangleWidth,
            height=DiagonalRectangleConfig.InnerDiagonalRectangleHeight,
        )
        for profile in sketch.profiles:
            extrude_thin_one(
                component=main_comp,
                profile=profile,
                extrudeHeight=extrude_height,
                strokeWeight=DiagonalRectangleConfig.InnerDiagonalRectangleStrokeWeight,
                name="angled-rectangles-inner",
                operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
            )

            # draw the astroid 32
        sketch = create_sketch(main_comp, "astroid-32-outer", offset=layer_offset)
        extrude_height = AppConfig.LayerDepth
        draw_astroid(
            sketch=sketch,
            n=AstroidConfig.N,
            num_points=AstroidConfig.NumPoints,
            scale_x=AstroidConfig.InnerAstroidRadius,
            scale_y=AstroidConfig.InnerAstroidRadius,
        )
        extrude_profile_by_area(
            component=main_comp,
            profiles=sketch.profiles,
            area=calculate_astroid_area(AstroidConfig.InnerAstroidRadius),
            extrude_height=extrude_height,
            name="astroid-32-outer",
            fp_tolerance=1e0,
        )

        # layer 6D -----------
        layer_offset = AppConfig.LayerDepth * 6

        # draw the astroid 32 inner
        sketch = create_sketch(main_comp, "astroid-32-inner", offset=layer_offset)
        extrude_height = AppConfig.LayerDepth
        draw_astroid(
            sketch=sketch,
            n=AstroidConfig.N,
            num_points=AstroidConfig.NumPoints,
            scale_x=AstroidConfig.InnerAstroidRadius
            - AstroidConfig.InnerAstroidStrokeWeight,
            scale_y=AstroidConfig.InnerAstroidRadius
            - AstroidConfig.InnerAstroidStrokeWeight,
        )
        extrude_profile_by_area(
            component=main_comp,
            profiles=sketch.profiles,
            area=calculate_astroid_area(
                AstroidConfig.InnerAstroidRadius
                - AstroidConfig.InnerAstroidStrokeWeight
            ),
            extrude_height=extrude_height,
            name="astroid-32-inner",
            fp_tolerance=1e0,
        )


def create_torus_astroid(root_comp):
    if not component_exist(root_comp, create_component_name("torus")):
        torus_comp = create_component(
            component=root_comp, name=create_component_name("torus")
        )

        # inner torus
        iterations = 16

        # @TODO move random to libs
        radius = random.choice([0.48 * 20 * 2]) * SCALE_FACTOR
        stroke_weight = random.choice([0.32]) * SCALE_FACTOR
        inner_torus_component = create_component(
            component=torus_comp,
            name=create_component_name(
                "torus-outer-" + str(radius) + "-" + str(iterations)
            ),
        )
        depth_repeat = 2
        start_layer_offset = AppConfig.LayerDepth * 6
        extrude_height_per_layer = AppConfig.LayerDepth / depth_repeat

        for layer_offset, sw in depth_repeat_iterator(
            depth_repeat,
            start_layer_offset,
            extrude_height_per_layer,
            stroke_weight,
            direction=DepthRepeat.Decrement,
        ):
            # create the torus
            torus_layer_0_inner_comp = create_component(
                component=inner_torus_component,
                name=create_component_name(
                    "torus-inner-" + str(radius) + "-" + str(sw)
                ),
            )
            create_torus(
                component=torus_layer_0_inner_comp,
                center_x=0,
                center_y=0,
                radius=radius,
                iterations=iterations,
                stroke_weight=sw,
                extrude_height=extrude_height_per_layer,
                layer_offset=layer_offset,
            )

            # get all bodies
            invert_bodies = adsk.core.ObjectCollection.create()
            for body in torus_layer_0_inner_comp.bRepBodies:
                invert_bodies.add(body)

            # invert the joint body; re should always be in first occurance
            sketch = create_sketch(
                torus_comp, "torus-astroid-32-inverse", offset=layer_offset
            )
            draw_astroid(
                sketch=sketch,
                n=AstroidConfig.N,
                num_points=AstroidConfig.NumPoints,
                scale_x=AstroidConfig.InnerAstroidRadius
                - AstroidConfig.InnerAstroidStrokeWeight,
                scale_y=AstroidConfig.InnerAstroidRadius
                - AstroidConfig.InnerAstroidStrokeWeight,
            )
            invert_body = extrude_single_profile_by_area(
                component=torus_comp,
                profiles=sketch.profiles,
                area=calculate_astroid_area(
                    AstroidConfig.InnerAstroidRadius
                    - AstroidConfig.InnerAstroidStrokeWeight
                ),
                extrude_height=extrude_height_per_layer,
                name="astroid-32-inner",
                fp_tolerance=1e-0,
            )
            combine_body(
                torus_comp,
                invert_body,
                invert_bodies,
                operation=adsk.fusion.FeatureOperations.CutFeatureOperation,
            )

            # add astroid bracing (stroke)
            sketch = create_sketch(
                torus_comp, "torus-astroid-32-inverse-bracing", offset=layer_offset
            )
            draw_astroid_stroke(
                sketch=sketch,
                n=AstroidConfig.N,
                num_points=AstroidConfig.NumPoints,
                scale_x=AstroidConfig.InnerAstroidRadius
                - AstroidConfig.InnerAstroidStrokeWeight,
                scale_y=AstroidConfig.InnerAstroidRadius
                - AstroidConfig.InnerAstroidStrokeWeight,
                thickness=AppConfig.StrokeWeight,
            )
            extrude_profile_by_area(
                component=torus_comp,
                profiles=sketch.profiles,
                area=calculate_astroid_area(
                    AstroidConfig.InnerAstroidRadius
                    - AstroidConfig.InnerAstroidStrokeWeight
                )
                - calculate_astroid_area(
                    AstroidConfig.InnerAstroidRadius
                    - AstroidConfig.InnerAstroidStrokeWeight
                    - AppConfig.StrokeWeight
                ),
                extrude_height=extrude_height_per_layer,
                name="torus-astroid-bracing",
                operation=adsk.fusion.FeatureOperations.JoinFeatureOperation,
                fp_tolerance=1e-0,
            )

        # combine all the bodies
        all_bodies = aggregate_all_bodies(torus_comp)
        root_body = all_bodies.item(0)
        all_bodies.removeByIndex(0)
        combine_body(
            torus_comp,
            root_body,
            all_bodies,
            operation=adsk.fusion.FeatureOperations.JoinFeatureOperation,
        )


def create_middle_cut(root_comp):
    if not component_exist(root_comp, create_component_name("middle_circle_comp")):
        try:
            middle_circle_comp = create_component(
                component=root_comp,
                name=create_component_name("middle_circle_comp"),
            )

            sketch = create_sketch(
                middle_circle_comp, "hole-thin-circle", offset=AppConfig.LayerDepth
            )
            stroke_weight = AppConfig.LayerDepth * 1.5 * SCALE_FACTOR
            draw_circle(sketch=sketch, radius=AppConfig.HoleRadius)
            extrude_thin_one(
                component=middle_circle_comp,
                profile=sketch.profiles[0],
                extrudeHeight=AppConfig.LayerDepth * 6,
                strokeWeight=stroke_weight,
                name="hole-thin-circle",
                operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
                side=DepthEffect.Side2,
            )

            sketch = create_sketch(middle_circle_comp, "cut-hole", offset=0.0)
            draw_circle(sketch=sketch, radius=AppConfig.HoleRadius)
            extrude_profile_by_area(
                component=middle_circle_comp,
                profiles=sketch.profiles,
                area=calculate_circle_area(AppConfig.HoleRadius),
                extrude_height=AppConfig.LayerDepth * 9,
                name="cut-hole",
                operation=adsk.fusion.FeatureOperations.CutFeatureOperation,
            )
        except:
            log("cut-hole: none to cut")


@timer
def create_torus(
    component: adsk.fusion.Component,
    center_x,
    center_y,
    radius,
    iterations,
    stroke_weight,
    extrude_height,
    layer_offset,
):
    sketch = create_sketch(
        component,
        "torus-outer-circle-" + str(radius) + "-" + str(iterations),
        offset=layer_offset,
    )

    # draw the outer circle
    draw_circle(sketch, radius, center_x, center_y)
    initial_body = extrude_thin_one(
        component=component,
        profile=sketch.profiles[0],
        extrudeHeight=extrude_height,
        strokeWeight=stroke_weight,
        name="torus-outer-circle" + str(radius) + "-" + str(iterations),
        operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    initial_body.name = "torus-outer-circle" + str(radius) + "-" + str(iterations)

    # create the torus
    angle_per_iteration = 360 / iterations
    r = radius / 2.0

    # draw; this is a standard torus algorithm.
    for i in range(iterations):
        # radiant angle; see obsidian://open?vault=Obsidian%20Vault&file=personal%2Fart-composition%2Fimages%2Feducation-radiant-circle-measure.png
        angle = math.radians(i * angle_per_iteration)
        x = center_x + r * math.cos(angle)
        y = center_y + r * math.sin(angle)

        real_sketch = create_sketch(
            component,
            "torus-inner-circle-" + str(r) + "-" + str(angle),
            layer_offset,
        )
        draw_circle(real_sketch, r, x, y)
        extrude_thin_one(
            component=component,
            profile=real_sketch.profiles[0],
            extrudeHeight=extrude_height,
            strokeWeight=stroke_weight,
            name="torus-inner-circle-" + str(r) + "-" + str(angle),
            operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        )

    # log the seed of life
    log(f"torus: {iterations} circles with radius: {r}")


def create_intersect_only_in_bounds(root_comp):
    # intersect only in bounds
    try:
        intersect_only_in_bounds_comp = create_component(
            root_component=root_comp,
            component_name=create_component_name("intersect-only-in-bounds"),
        )
        sketch = create_sketch(
            intersect_only_in_bounds_comp,
            "intersect-only-in-bounds",
            offset=AppConfig.LayerDepth,
        )
        draw_rectangle(
            sketch=sketch, length=AppConfig.MaxLength, width=AppConfig.MaxWidth
        )
        extrude_profile_by_area(
            component=intersect_only_in_bounds_comp,
            profiles=sketch.profiles,
            area=calculate_rectangle_area(AppConfig.MaxLength, AppConfig.MaxWidth),
            extrude_height=AppConfig.LayerDepth * 2,
            name="intersect-only-in-bounds",
            operation=adsk.fusion.FeatureOperations.IntersectFeatureOperation,
        )
    except:
        log(f"WARNING: intersect-only-in-bounds: none to cut")


def create_component_outer_diagonal_steps(root_comp: adsk.fusion.Component):
    if not component_exist(
        root_comp, create_component_name("interstellar-tesellation")
    ):
        interstellar_tesellation_comp = create_component(
            component=root_comp,
            name=create_component_name("interstellar-tesellation"),
        )

        # draw from middle
        center_x = 0
        center_y = 0
        depth_repeat = 4
        extrude_height_per_layer = AppConfig.LayerDepth * 2 / depth_repeat
        stroke_weight = 0.72 * SCALE_FACTOR
        start_layer_offset = AppConfig.LayerDepth * 3

        for layer_offset, sw in depth_repeat_iterator(
            depth_repeat, start_layer_offset, extrude_height_per_layer, stroke_weight
        ):
            sketch = create_sketch(
                interstellar_tesellation_comp,
                "interstellar-tesellation-outer",
                offset=layer_offset,
            )
            draw_rotated_rectangle(
                sketch=sketch,
                width=DiagonalRectangleConfig.OuterDiagonalRectangleWidth,
                height=DiagonalRectangleConfig.OuterDiagonalRectangleHeight,
            )
            extrude_thin_one(
                component=interstellar_tesellation_comp,
                profile=sketch.profiles[0],
                extrudeHeight=extrude_height_per_layer,
                strokeWeight=sw,
                name="interstellar-tesellation-outer",
                operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
            )

        # for layer_offset, sw in depth_repeat_iterator(depth_repeat, start_layer_offset, extrude_height_per_layer, stroke_weight):
        #     sketch = create_sketch(interstellar_tesellation_comp, 'interstellar-tesellation-middle', offset=layer_offset)
        #     draw_rotated_rectangle(sketch=sketch, width=DiagonalRectangleConfig.MiddleDiagonalRectangleWidth, height=DiagonalRectangleConfig.MiddleDiagonalRectangleHeight)
        #     extrude_thin_one(component=interstellar_tesellation_comp, profile=sketch.profiles[0], extrudeHeight=extrude_height_per_layer, strokeWeight=sw, name='interstellar-tesellation-middle', operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation, side=DepthEffect.Side2)

        # cut with AstroidOuterCutWithMiddleDiagonalRectangleExtrudeArea
        # sketch = create_sketch(interstellar_tesellation_comp, 'interstellar-tesellation-astroid-outer-cut', offset=AppConfig.LayerDepth)
        # draw_astroid_stroke(sketch=sketch, n=AstroidConfig.N, numPoints=AstroidConfig.NumPoints, scaleX=AstroidConfig.OuterAstroidRadius, scaleY=AstroidConfig.OuterAstroidRadius, strokeWeight=AstroidConfig.OuterAstroidStrokeWeight)
        # draw_rotated_rectangle(sketch=sketch, width=DiagonalRectangleConfig.MiddleDiagonalRectangleWidth, height=DiagonalRectangleConfig.MiddleDiagonalRectangleHeight)
        # extrude_profile_y_area(component=interstellar_tesellation_comp, profiles=sketch.profiles, area=KailashConfig.AstroidOuterCutWithMiddleDiagonalRectangleExtrudeArea, extrude_height=AppConfig.LayerDepth, name='interstellar-tesellation-astroid-outer-cut', operation=adsk.fusion.FeatureOperations.CutFeatureOperation)


# @TODO where to move?
def aggregate_all_bodies(
    component: adsk.fusion.Component,
    all_bodies: adsk.core.ObjectCollection = None,
    depth_limit: int = -1,
):
    if all_bodies is None:
        all_bodies = adsk.core.ObjectCollection.create()

    # Add all bodies from the current component
    for body in component.bRepBodies:
        all_bodies.add(body)

    # Check if the depth limit has been reached
    if depth_limit == 0:
        return all_bodies

    # Recursively process all subcomponents, decreasing depth limit by 1 with each call
    for occurrence in component.occurrences:
        aggregate_all_bodies(
            occurrence.component, all_bodies, depth_limit - 1 if depth_limit > 0 else -1
        )

    return all_bodies


def create_kailash_terrain_cut(component: adsk.fusion.Component):
    if not component_exist(
        component, create_component_name("cut-kailash-intersection")
    ):
        # Structural Component - Kailash Terrain Generation Sketch
        # Note: This is a placeholder for the actual terrain generation code. Requires manual intervention using STL files & Fusion Forms.
        # Guide: https://www.youtube.com/watch?v=Ea_YC4Jh0Sw
        try:
            kailash_comp = create_component(
                root_component=component,
                component_name=create_component_name("cut-kailash-intersection"),
            )
            start_layer_offset = AppConfig.LayerDepth * 3.5
            extrude_height = AppConfig.LayerDepth * 3
            sketch = create_sketch(
                kailash_comp, "cut-kailash-intersection", offset=start_layer_offset
            )
            draw_rotated_rectangle(
                sketch=sketch,
                width=DiagonalRectangleConfig.MiddleDiagonalRectangleWidth
                - DiagonalRectangleConfig.MiddleDiagonalRectangleStrokeWeight * 2,
                height=DiagonalRectangleConfig.MiddleDiagonalRectangleHeight
                - DiagonalRectangleConfig.MiddleDiagonalRectangleStrokeWeight * 2,
            )
            draw_rotated_rectangle(
                sketch=sketch,
                width=DiagonalRectangleConfig.InnerDiagonalRectangleWidth,
                height=DiagonalRectangleConfig.InnerDiagonalRectangleHeight,
            )
            draw_astroid(
                sketch=sketch,
                n=AstroidConfig.N,
                num_points=AstroidConfig.NumPoints,
                scale_x=AstroidConfig.OuterAstroidRadius,
                scale_y=AstroidConfig.OuterAstroidRadius,
            )
            draw_astroid(
                sketch=sketch,
                n=AstroidConfig.N,
                num_points=AstroidConfig.NumPoints,
                scale_x=AstroidConfig.OuterAstroidRadius
                - AstroidConfig.OuterAstroidStrokeWeight,
                scale_y=AstroidConfig.OuterAstroidRadius
                - AstroidConfig.OuterAstroidStrokeWeight,
            )
            draw_astroid(
                sketch=sketch,
                n=AstroidConfig.N,
                num_points=AstroidConfig.NumPoints,
                scale_x=AstroidConfig.InnerAstroidRadius,
                scale_y=AstroidConfig.InnerAstroidRadius,
            )
            draw_astroid(
                sketch=sketch,
                n=AstroidConfig.N,
                num_points=AstroidConfig.NumPoints,
                scale_x=AstroidConfig.InnerAstroidRadius
                - AstroidConfig.InnerAstroidStrokeWeight,
                scale_y=AstroidConfig.InnerAstroidRadius
                - AstroidConfig.InnerAstroidStrokeWeight,
            )
            # for profile in sketch.profiles:
            #     log(f"cut-kailash-intersection: profile area: {profile.areaProperties().area}")
            extrude_profile_by_area(
                component=kailash_comp,
                profiles=sketch.profiles,
                area=KailashConfig.KailashIntersectExtrudeArea,
                extrude_height=extrude_height,
                name="cut-kailash-intersection",
                operation=adsk.fusion.FeatureOperations.CutFeatureOperation,
            )
        except:
            log(f"WARNING: cut-kailash-intersection: none to cut")


def create_component_name(name: str):
    return f"{FabricationType.get_name(FabricationType.CNC_MILL).lower()}-{name}"
