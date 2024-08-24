from typing import List
import adsk.fusion
from ...core.geometry.index import Geometry, ModifiableGeometry
from ...core.component_utils import create_component


# @NOTE assuming all elements are on xYConstructionPlane
class CompositionGeometry(Geometry):
    def __init__(
        self,
        elements: List[ModifiableGeometry],
        count: int,
        spacing: float = 0,
    ):
        self.elements = elements
        self.count = count
        self.spacing = spacing

    # @TODO sketches should not be shared by all elements in a layer
    def draw(
        self,
        component: adsk.fusion.Component,
    ) -> None:
        # for y in range(self.count_y):
        for x in range(self.count):
            for element in self.elements:
                offset = element.width * x + self.spacing * x
                element.set_plane_offset(offset)
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
