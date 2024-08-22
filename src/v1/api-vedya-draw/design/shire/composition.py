# from typing import List
import adsk.fusion
from ...core.component_utils import create_component

# from ...core.geometry.index import ModifiableGeometry


class CompositionLayer:
    def __init__(
        self,
        # elements: List[ModifiableGeometry],
        elements,
    ):
        self.elements = elements

    def create(self, component: adsk.fusion.Component) -> None:
        for element in self.elements:
            element.draw(component.sketches.add(component.xYConstructionPlane))


class Composition:
    def __init__(
        self,
        #  layers: List[CompositionLayer]
        layers,
    ):
        self.layers = layers

    def create(self, component: adsk.fusion.Component) -> None:
        for i, layer in enumerate(self.layers):
            layer_comp = create_component(component, f"layer-{i}")
            layer.create(layer_comp)
