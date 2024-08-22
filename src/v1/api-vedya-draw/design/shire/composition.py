from typing import List
import adsk.fusion
from ...core.geometry.index import ModifiableGeometry
from ...core.geometry_utils import create_sketch
from ...core.component_utils import create_component


class CompositionLayer:
    def __init__(
        self,
        elements: List[ModifiableGeometry],
    ):
        self.elements = elements

    # @TODO sketches should not be shared by all elements in a layer
    def create(self, component: adsk.fusion.Component) -> None:
        sketch = create_sketch(component, "layer-sketch")
        for element in self.elements:
            element.draw(sketch)
            element.post_draw(component, sketch.profiles)


class Composition:
    def __init__(self, layers: List[CompositionLayer]):
        self.layers = layers

    def create(self, component: adsk.fusion.Component) -> None:
        for i, layer in enumerate(self.layers):
            layer_comp = create_component(component, f"layer-{i}")
            layer.create(layer_comp)
