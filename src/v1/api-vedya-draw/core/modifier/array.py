from ...core.geometry.index import ModifiableGeometry
from ...core.modifier.index import Modifier
from typing import Callable
import adsk.fusion


class Array(Modifier):
    def __init__(self, count_x: int, count_y: int):
        self.count_x = count_x
        self.count_y = count_y

    def apply(self, geometry: ModifiableGeometry, component: adsk.fusion.Component):
        original_center = (geometry.center_x, geometry.center_y)
        for x in range(self.count_x):
            for y in range(self.count_y):
                offset_x, offset_y = (
                    geometry.xyBound().x * x,
                    geometry.xyBound().y * y,
                )
                new_center_x = original_center[0] + offset_x
                new_center_y = original_center[1] + offset_y
                geometry.create_body(component, new_center_x, new_center_y)
        geometry.center_x, geometry.center_y = (
            original_center  # Reset to original position
        )
