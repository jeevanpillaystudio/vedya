from typing import List
import adsk.fusion
from ...core.geometry.index import ModifiableGeometry
from ...core.geometry_utils import create_sketch
from ...core.component_utils import create_component


class CompositionGeometry:
    def __init__(
        self,
        elements: List[ModifiableGeometry],
        plane_offset: float = 0.0,
    ):
        self.elements = elements
        self.plane_offset = plane_offset

    # @TODO sketches should not be shared by all elements in a layer
    def draw(self, component: adsk.fusion.Component) -> None:
        for element in self.elements:
            element.pre_draw(component)
            element.draw()
            element.post_draw(component)


class Composition:
    def __init__(self, layers: List[CompositionGeometry]):
        self.layers = layers

    def create(self, component: adsk.fusion.Component) -> None:
        for i, layer in enumerate(self.layers):
            geometry_component = create_component(component, f"geometry-{i}")
            layer.draw(geometry_component)
