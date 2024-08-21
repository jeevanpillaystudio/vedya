import math
import random
import adsk.core, adsk.fusion
from abc import ABC, abstractmethod
from core.depth_utils import DepthEffect, DepthRepeat
from core.modifier.index import Modifier

from core.modifier.intersection import Intersection
from core.modifier.subtraction import Subtraction

from ...core.modifier.array import Array
from ...core.geometry.index import Geometry

from ...core.transform.radial import Radial
from ...core.transform.index import Transform
from ...core.transform.grid import Grid
from ...core.transform.scaling import Scaling

from ...core.geometry.circle import (
    Circle,
    calculate_circle_area,
    draw_circle,
)
from ...core.geometry.rectangle import (
    Rectangle,
    calculate_rectangle_area,
    draw_rectangle,
    draw_rotated_rectangle,
)
from ...core.geometry_utils import (
    create_sketch,
    extrude_profile_by_area,
    extrude_single_profile_by_area,
    extrude_thin_one,
)
from ...core.component_utils import (
    create_component,
    is_component_exist,
    aggregate_all_bodies,
    combine_body,
)
from ...utils.lib import (
    log,
    timer,
    create_array_random_unique_multiples,
)
from ...core.depth_utils import DepthRepeat, depth_repeat_iterator
from .config import (
    AppConfig,
    AstroidConfig,
    BackgroundConfig,
    DiagonalRectangleConfig,
    SCALE_FACTOR,
)


class CompositeTransform(Transform):
    def __init__(self, *transforms: Transform):
        self.transforms = transforms

    def get_matrix(self, index: int, total: int) -> adsk.core.Matrix3D:
        composite = adsk.core.Matrix3D.create()
        for transform in self.transforms:
            composite.transformBy(transform.get_matrix(index, total))
        return composite


class CompositeLayer:
    def __init__(self, modifiers):
        self.modifiers = modifiers

    def create(self, component):
        for modifier in self.modifiers:
            modifier.apply(component)


class Layered(Modifier):
    def __init__(
        self,
        base_geometry: Geometry,
        depth_repeat: int,
        start_offset: float,
        extrude_height: float,
        stroke_weight: float,
        direction: DepthRepeat,
    ):
        self.base_geometry = base_geometry
        self.depth_repeat = depth_repeat
        self.start_offset = start_offset
        self.extrude_height = extrude_height
        self.stroke_weight = stroke_weight
        self.direction = direction

    def apply(self, component: adsk.fusion.Component):
        extrude_height_per_layer = self.extrude_height / self.depth_repeat
        for layer_offset, sw in depth_repeat_iterator(
            self.depth_repeat,
            self.start_offset,
            extrude_height_per_layer,
            self.stroke_weight,
            self.direction,
        ):
            inner_comp = create_component(component, f"inner-layer-{layer_offset}-{sw}")
            sketch = create_sketch(inner_comp, "layered-geometry", offset=layer_offset)
            self.base_geometry.draw(sketch)
            extrude_profile_by_area(
                component=inner_comp,
                profiles=sketch.profiles,
                area=self.base_geometry.calculate_area(),
                extrude_height=extrude_height_per_layer,
                name="layered-geometry-extrude",
                operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
            )

    def calculate_area(self):
        return self.base_geometry.calculate_area()


class SeedOfLife(Modifier):
    def __init__(self, radius: float, num_circles: int = 6):
        self.radius = radius
        self.num_circles = num_circles
        self.center_circle = Circle(radius)
        self.outer_circles = Array(Circle(radius), num_circles, Radial(radius))

    def apply(self, sketch: adsk.fusion.Sketch):
        self.center_circle.draw(sketch)
        self.outer_circles.apply(sketch)

    def calculate_area(self):
        return self.center_circle.calculate_area() + self.outer_circles.calculate_area()


background_layer = CompositeLayer(
    [
        Layered(
            Intersection(
                Rectangle(AppConfig.MaxLength, AppConfig.MaxWidth),
                Circle(AppConfig.MaxLength / 2),
            ),
            depth_repeat=1,
            start_offset=0,
            extrude_height=AppConfig.LayerDepth,
            stroke_weight=1,
            direction=DepthRepeat.Increment,
        )
    ]
)

seed_of_life_layer_0 = CompositeLayer(
    [
        Layered(
            Subtraction(
                SeedOfLife(20 * AppConfig.SCALE_FACTOR),
                Rectangle(
                    DiagonalRectangleConfig.OuterDiagonalRectangleWidth,
                    DiagonalRectangleConfig.OuterDiagonalRectangleHeight,
                    rotation=45,
                ),
            ),
            depth_repeat=4,
            start_offset=AppConfig.LayerDepth * 4,
            extrude_height=AppConfig.LayerDepth * 2,
            stroke_weight=0.96 * AppConfig.SCALE_FACTOR,
            direction=DepthRepeat.Decrement,
        ),
        Layered(
            Intersection(
                Circle(36.0 * AppConfig.SCALE_FACTOR),
                Rectangle(
                    DiagonalRectangleConfig.OuterDiagonalRectangleWidth,
                    DiagonalRectangleConfig.OuterDiagonalRectangleHeight,
                    rotation=45,
                ),
            ),
            depth_repeat=1,
            start_offset=AppConfig.LayerDepth * 4,
            extrude_height=AppConfig.LayerDepth * 2,
            stroke_weight=0.96 * AppConfig.SCALE_FACTOR,
            direction=DepthRepeat.Decrement,
        ),
    ]
)

seed_of_life_layer_1 = CompositeLayer(
    [
        Layered(
            SeedOfLife(
                random.choice(
                    create_array_random_unique_multiples(
                        size=4,
                        multiple=8 * AppConfig.SCALE_FACTOR,
                        min_multiple=4,
                        max_multiple=10,
                    )
                )
            ),
            depth_repeat=random.randint(3, 4),
            start_offset=AppConfig.LayerDepth * 2,
            extrude_height=random.choice(
                [AppConfig.LayerDepth * 2, AppConfig.LayerDepth * 4]
            ),
            stroke_weight=random.uniform(0.96, 1.92) * AppConfig.SCALE_FACTOR,
            direction=DepthRepeat.Decrement,
        )
        for _ in range(2)
    ]
    + [
        Layered(
            Intersection(
                Rectangle(AppConfig.MaxLength, AppConfig.MaxWidth),
                Subtraction(
                    Rectangle(AppConfig.MaxLength, AppConfig.MaxWidth),
                    Rectangle(
                        DiagonalRectangleConfig.OuterDiagonalRectangleWidth,
                        DiagonalRectangleConfig.OuterDiagonalRectangleHeight,
                        rotation=45,
                    ),
                    Rectangle(
                        DiagonalRectangleConfig.InnerDiagonalRectangleWidth,
                        DiagonalRectangleConfig.InnerDiagonalRectangleHeight,
                        rotation=45,
                    ),
                ),
            ),
            depth_repeat=1,
            start_offset=AppConfig.LayerDepth * 2,
            extrude_height=AppConfig.LayerDepth,
            stroke_weight=1,
            direction=DepthRepeat.Increment,
        )
    ]
)

seed_of_life_layer_2 = CompositeLayer(
    [
        Layered(
            SeedOfLife(44 * AppConfig.SCALE_FACTOR),
            depth_repeat=6,
            start_offset=AppConfig.LayerDepth * 4,
            extrude_height=AppConfig.LayerDepth * 4,
            stroke_weight=0.96 * AppConfig.SCALE_FACTOR,
            direction=DepthRepeat.Decrement,
        ),
        Layered(
            Intersection(
                Rectangle(
                    72.0 * AppConfig.SCALE_FACTOR + 0.1 * AppConfig.SCALE_FACTOR,
                    AppConfig.MaxWidth,
                ),
                Subtraction(
                    Rectangle(
                        72.0 * AppConfig.SCALE_FACTOR + 0.1 * AppConfig.SCALE_FACTOR,
                        AppConfig.MaxWidth,
                    ),
                    Circle(36.0 * AppConfig.SCALE_FACTOR),
                ),
            ),
            depth_repeat=1,
            start_offset=AppConfig.LayerDepth * 4,
            extrude_height=AppConfig.LayerDepth * 4,
            stroke_weight=0.96 * AppConfig.SCALE_FACTOR,
            direction=DepthRepeat.Decrement,
        ),
    ]
)

torus_astroid_layer = CompositeLayer(
    [
        Layered(
            TorusAstroid(AstroidConfig),
            depth_repeat=2,
            start_offset=AppConfig.LayerDepth * 6,
            extrude_height=AppConfig.LayerDepth,
            stroke_weight=0.96 * AppConfig.SCALE_FACTOR,
            direction=DepthRepeat.Decrement,
        )
    ]
)

# Create the final composition
shire_composition = Composition(
    [
        background_layer,
        seed_of_life_layer_0,
        seed_of_life_layer_2,
        seed_of_life_layer_1,
        torus_astroid_layer,
    ]
)


class Composition:
    def __init__(self, layers):
        self.layers = layers

    def create(self, component):
        for layer in self.layers:
            layer.create(component)


def start_func(root_comp: adsk.fusion.Component):
    shire_composition.create(root_comp)

    # Additional operations that don't fit into the layer structure
    create_middle_cut(root_comp)
    create_kailash_terrain_cut(root_comp)
    create_intersect_only_in_bounds(root_comp)


class TorusAstroid(Modifier):
    def __init__(self, config):
        self.config = config
        self.outer_circle = Circle(self.config.OuterRadius)
        self.inner_astroid = Astroid(
            self.config.InnerAstroidRadius, self.config.N, self.config.NumPoints
        )
        self.astroid_stroke = Array(
            Circle(self.config.InnerAstroidStrokeWeight / 2),
            self.config.NumPoints,
            CompositeTransform(
                Scaling(self.config.N),
                Radial(self.config.InnerAstroidRadius),
            ),
        )

    def apply(self, sketch: adsk.fusion.Sketch):
        self.outer_circle.draw(sketch)
        self.inner_astroid.draw(sketch)
        self.astroid_stroke.apply(sketch)

    def calculate_area(self):
        return (
            self.outer_circle.calculate_area()
            - self.inner_astroid.calculate_area()
            + self.astroid_stroke.calculate_area()
        )


def create_middle_cut(root_comp):
    if not is_component_exist(root_comp, create_component_name("middle_circle_comp")):
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


def create_intersect_only_in_bounds(root_comp):
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


def create_component_name(name: str) -> str:
    return f"{AppConfig.ProjectName}-{name}"
