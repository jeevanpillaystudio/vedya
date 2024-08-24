from typing import List
import adsk.fusion
from ...utils.lib import log
from ...core.geometry.index import Geometry, ModifiableGeometry
from ...core.component_utils import create_component


# @NOTE assuming all elements are on xYConstructionPlane
class CompositionGeometry(Geometry):
    def __init__(
        self,
        elements: List[ModifiableGeometry],
        count: int,
    ):
        self.elements = elements
        self.count = count

    # @TODO sketches should not be shared by all elements in a layer
    def draw(
        self,
        component: adsk.fusion.Component,
    ) -> None:
        for x in range(self.count):
            for element in self.elements:
                element.center_x = element.xyBound().x * x
                element.center_y = 0
                log(
                    f"DEBUG: Drawing element from center_x, center_y {element.center_x}, {element.center_y}"
                )
                element.pre_draw(component)
                element.draw()
                element.post_draw(component)

    def calculate_area(self) -> float:
        return sum([element.calculate_area() for element in self.elements])


class Composition:
    def __init__(self, layers: List[CompositionGeometry]):
        self.layers = layers

    def create(self, component: adsk.fusion.Component) -> None:
        for i, layer in enumerate(self.layers):
            geometry_component = create_component(component, f"geometry-{i}")
            layer.draw(geometry_component)
