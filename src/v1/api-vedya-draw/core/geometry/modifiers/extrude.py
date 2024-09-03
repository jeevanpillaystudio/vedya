from abc import abstractmethod
from typing import Callable
import uuid

import adsk.fusion
from ..libs.geometry_utils import create_sketch


# base class
class Extrude:
    def __init__(
        self,
        thickness: float,
        plane_offset: float,
        x_count: int = 1,
        y_count: int = 1,
        operation: adsk.fusion.FeatureOperations = adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    ):
        self.thickness = thickness
        self.plane_offset = plane_offset  # @NOTE this is based on the parent component & also only changes rleatively to XY Plane...
        self.operation = operation
        self.x_count = x_count
        self.y_count = y_count

    def run(
        self,
        draw_func: Callable[[adsk.fusion.Sketch], None],
        component: adsk.fusion.Component,
    ) -> adsk.fusion.BRepBodies:
        # create the sketch
        self.sketch = create_sketch(
            component=component,
            name="extrude-sketch",
            offset=self.plane_offset,
        )

        # draw the thing: re blah blah about maths goes in here, e.g points, etc
        draw_func(self.sketch)

        # extrude
        return self.extrude(component)

    @abstractmethod
    def extrude(self, component: adsk.fusion.Component) -> adsk.fusion.BRepBodies:
        pass

    @property
    def plane_offset(self):
        return self._plane_offset

    @plane_offset.setter
    def plane_offset(self, plane_offset: float):
        self._plane_offset = plane_offset


# full extrusion
class FullExtrude(Extrude):
    def __init__(
        self,
        thickness: float,
        plane_offset: float,
        x_count: int = 1,
        y_count: int = 1,
        operation: adsk.fusion.FeatureOperations = adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    ):
        super().__init__(thickness, plane_offset, x_count, y_count, operation)

    def extrude(
        self,
        component: adsk.fusion.Component,
    ) -> adsk.fusion.BRepBodies:
        bodies = adsk.core.ObjectCollection.create()
        for profile in self.sketch.profiles:
            extrudes = component.features.extrudeFeatures
            extrude_input = extrudes.createInput(profile, self.operation)
            extrude_input.setDistanceExtent(
                False, adsk.core.ValueInput.createByReal(self.thickness)
            )
            extrude = extrudes.add(extrude_input)
            body = extrude.bodies.item(0)
            body.name = f"{component.name}-{self.x_count}x{self.y_count}"
            bodies.add(body)
        return bodies


# thin extrusion
class ThinExtrude(Extrude):
    def __init__(
        self,
        thickness: float,
        plane_offset: float,
        x_count: int = 1,
        y_count: int = 1,
        stroke_weight: float = 0.0,
        operation: adsk.fusion.FeatureOperations = adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        side: adsk.fusion.ThinExtrudeWallLocation = adsk.fusion.ThinExtrudeWallLocation.Side1,
        start_from: adsk.fusion.BRepBody = None,
    ):
        super().__init__(thickness, plane_offset, x_count, y_count, operation)
        self.stroke_weight = stroke_weight
        self.side = side
        self.start_from = start_from

    def extrude(
        self,
        component: adsk.fusion.Component,
    ) -> adsk.fusion.BRepBodies:
        bodies = adsk.core.ObjectCollection.create()
        for profile in self.sketch.profiles:
            extrudes = component.features.extrudeFeatures
            profile = self.sketch.profiles.item(0)
            extrude_input = extrudes.createInput(profile, self.operation)

            if self.start_from is not None:
                mm0 = adsk.core.ValueInput.createByString("0 mm")
                start_from_extent = adsk.fusion.FromEntityStartDefinition.create(
                    self.start_from, mm0
                )
                extrude_input.startExtent = start_from_extent

            extrude_input.setThinExtrude(
                self.side, adsk.core.ValueInput.createByReal(self.stroke_weight)
            )
            extrude_input.setDistanceExtent(
                False, adsk.core.ValueInput.createByReal(self.thickness)
            )
            extrude = extrudes.add(extrude_input)
            body = extrude.bodies.item(0)
            body.name = f"{component.name}-{self.x_count}x{self.y_count}"
            bodies.add(body)
        return bodies
