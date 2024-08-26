import random

import adsk.core, adsk.fusion

# designer
from core.fabrication.composition.index import Composition, CompositionGeometry

# modifier
from ...core.modifier.index import Modifier
from ...core.modifier.boolean import Difference, Difference, Union
from ...core.modifier.array import Array

# geometry
from ...core.geometry.core.geometry import Geometry
from ...core.geometry.sol import SeedOfLife
from ...core.geometry.core.shapes.astroid import Astroid

# transform
from ...core.transform.depth import Depth
from ...core.transform.radial import Radial
from ...core.transform.index import CompositeTransform, Transform
from ...core.transform.grid import Grid
from ...core.transform.scaling import Scaling

from ...core.geometry.circle import (
    Circle,
)
from ...core.geometry.rectangle import (
    Rectangle,
)

from ...core.geometry_utils import (
    create_sketch,
    extrude_profile_by_area,
)
from ...core.component_utils import (
    create_component,
)
from ...utils.lib import (
    log,
)

from ...core.depth_utils import DepthRepeat, depth_repeat_iterator
from .config import (
    AppConfig,
    DiagonalRectangleConfig,
    SCALE_FACTOR,
)


# class DepthArray(Array):
#     def __init__(
#         self,
#         base_geometry: Geometry,
#         count: int,
#         total_depth: float,
#         start_scale: float,
#         end_scale: float,
#         direction: int,
#     ):
#         transform = CompositeTransform(
#             Depth(total_depth, direction), Scaling(start_scale, end_scale)
#         )
#         super().__init__(base_geometry, count, transform)
#         self.extrude_height_per_layer = total_depth / count

#     def apply(self, component: adsk.fusion.Component):
#         for i in range(self.count):
#             matrix = self.transform.get_matrix(i, self.count)
#             inner_comp = create_component(component, f"depth-layer-{i}")
#             sketch = create_sketch(inner_comp, "depth-geometry")
#             sketch.transform(matrix)
#             self.base_geometry.draw(sketch)
#             extrude_profile_by_area(
#                 component=inner_comp,
#                 profiles=sketch.profiles,
#                 area=self.base_geometry.calculate_area(),
#                 extrude_height=self.extrude_height_per_layer,
#                 name=f"depth-extrude-{i}",
#                 operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
#             )


background_layer = CompositionGeometry(
    [
        Rectangle(AppConfig.MaxLength, AppConfig.MaxWidth)
        # .add_modifier(
        #     Extrude(AppConfig.LayerDepth)
        # )
        # .add_modifier(Intersect(Circle(AppConfig.MaxLength / 2)))
    ]
)

# seed_of_life_layer_0 = CompositionLayer(
#     [
#         SeedOfLife(20 * AppConfig.SCALE_FACTOR)
#         .add_modifier(
#             Difference(
#                 Rectangle(
#                     DiagonalRectangleConfig.OuterDiagonalRectangleWidth,
#                     DiagonalRectangleConfig.OuterDiagonalRectangleHeight,
#                     rotation=45,
#                 )
#             )
#         )
#         .add_modifier(
#             DepthArray(
#                 count=4,
#                 total_depth=AppConfig.LayerDepth * 2,
#                 start_scale=1.0,
#                 end_scale=0.96,
#                 direction=DepthRepeat.Decrement,
#             )
#         ),
#     ]
# )

# seed_of_life_layer_1 = CompositionLayer(
#     [
#         DepthArray(
#             SeedOfLife(
#                 random.choice(
#                     create_array_random_unique_multiples(
#                         size=4,
#                         multiple=8 * AppConfig.SCALE_FACTOR,
#                         min_multiple=4,
#                         max_multiple=10,
#                     )
#                 )
#             ),
#             depth_repeat=random.randint(3, 4),
#             start_offset=AppConfig.LayerDepth * 2,
#             extrude_height=random.choice(
#                 [AppConfig.LayerDepth * 2, AppConfig.LayerDepth * 4]
#             ),
#             stroke_weight=random.uniform(0.96, 1.92) * AppConfig.SCALE_FACTOR,
#             direction=DepthRepeat.Decrement,
#         )
#         for _ in range(2)
#     ]
#     + [
#         DepthArray(
#             Intersect(
#                 Rectangle(AppConfig.MaxLength, AppConfig.MaxWidth),
#                 Difference(
#                     Rectangle(AppConfig.MaxLength, AppConfig.MaxWidth),
#                     Rectangle(
#                         DiagonalRectangleConfig.OuterDiagonalRectangleWidth,
#                         DiagonalRectangleConfig.OuterDiagonalRectangleHeight,
#                         rotation=45,
#                     ),
#                     Rectangle(
#                         DiagonalRectangleConfig.InnerDiagonalRectangleWidth,
#                         DiagonalRectangleConfig.InnerDiagonalRectangleHeight,
#                         rotation=45,
#                     ),
#                 ),
#             ),
#             depth_repeat=1,
#             start_offset=AppConfig.LayerDepth * 2,
#             extrude_height=AppConfig.LayerDepth,
#             stroke_weight=1,
#             direction=DepthRepeat.Increment,
#         )
#     ]
# )

# seed_of_life_layer_2 = CompositionLayer(
#     [
#         DepthArray(
#             SeedOfLife(44 * AppConfig.SCALE_FACTOR),
#             count=6,
#             total_depth=AppConfig.LayerDepth * 4,
#             start_scale=1.0,
#             end_scale=0.96,
#             direction=DepthRepeat.Decrement,
#         ),
#         Extrude(
#             Intersect(
#                 Rectangle(
#                     72.0 * AppConfig.SCALE_FACTOR + 0.1 * AppConfig.SCALE_FACTOR,
#                     AppConfig.MaxWidth,
#                 ),
#                 Difference(
#                     Rectangle(
#                         72.0 * AppConfig.SCALE_FACTOR + 0.1 * AppConfig.SCALE_FACTOR,
#                         AppConfig.MaxWidth,
#                     ),
#                     Circle(36.0 * AppConfig.SCALE_FACTOR),
#                 ),
#             ),
#             depth_repeat=1,
#             start_offset=AppConfig.LayerDepth * 4,
#             extrude_height=AppConfig.LayerDepth * 4,
#             stroke_weight=0.96 * AppConfig.SCALE_FACTOR,
#             direction=DepthRepeat.Decrement,
#         ),
#     ]
# )


# class TorusAstroid(Modifier):
#     def __init__(self, config):
#         self.config = config
#         self.outer_circle = Circle(self.config.OuterRadius)
#         self.inner_astroid = Astroid(
#             self.config.InnerAstroidRadius, self.config.N, self.config.NumPoints
#         )
#         self.astroid_stroke = Array(
#             Circle(self.config.InnerAstroidStrokeWeight / 2),
#             self.config.NumPoints,
#             CompositeTransform(
#                 Scaling(self.config.N),
#                 Radial(self.config.InnerAstroidRadius),
#             ),
#         )

#     def apply(self, sketch: adsk.fusion.Sketch):
#         self.outer_circle.draw(sketch)
#         self.inner_astroid.draw(sketch)
#         self.astroid_stroke.apply(sketch)

#     def calculate_area(self):
#         return (
#             self.outer_circle.calculate_area()
#             - self.inner_astroid.calculate_area()
#             + self.astroid_stroke.calculate_area()
#         )


# torus_astroid_layer = CompositionLayer(
#     [
#         DepthArray(
#             TorusAstroid(AstroidConfig),
#             depth_repeat=2,
#             start_offset=AppConfig.LayerDepth * 6,
#             extrude_height=AppConfig.LayerDepth,
#             stroke_weight=0.96 * AppConfig.SCALE_FACTOR,
#             direction=DepthRepeat.Decrement,
#         )
#     ]
# )

# Create the final composition
shire_composition = Composition(
    [
        background_layer,
        # seed_of_life_layer_0,
        # seed_of_life_layer_2,
        # seed_of_life_layer_1,
        # torus_astroid_layer,
    ]
)


def start_func(root_comp: adsk.fusion.Component):
    shire_composition.create(root_comp)

    # Additional operations that don't fit into the layer structure
    # create_middle_cut(root_comp)
    # create_kailash_terrain_cut(root_comp)
    # create_intersect_only_in_bounds(root_comp)


def create_component_name(name: str) -> str:
    return f"{AppConfig.ProjectName}-{name}"
