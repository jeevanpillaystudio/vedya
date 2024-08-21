from ...core.component_utils import create_component
import adsk.fusion


class CompositionLayer:
    def __init__(self, elements):
        self.elements = elements

    def create(self, component):
        for element in self.elements:
            element.apply(component)


class Composition:
    def __init__(self, layers: list[CompositionLayer]):
        self.layers = layers

    def create(self, component: adsk.fusion.Component):
        for layer in self.layers:
            layer_comp = create_component(
                component, f"layer-{self.layers.index(layer)}"
            )
            layer.create(layer_comp)
