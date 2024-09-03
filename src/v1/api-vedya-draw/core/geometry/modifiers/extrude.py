from abc import abstractmethod
from typing import Callable
import uuid

import adsk.fusion
from ....core.utils import log
from ..libs.component_utils import create_component
from ..libs.geometry_utils import create_sketch, extrude_profile_by_area, fillet_bodies

# base class
class Extrude:
    def __init__(self, thickness: float, plane_offset: float, x_count: int = 1, y_count: int = 1, fillet_radius: float = 0.0, operation: adsk.fusion.FeatureOperations = adsk.fusion.FeatureOperations.NewBodyFeatureOperation):
        self.thickness = thickness
        self.plane_offset = plane_offset # @NOTE this is based on the parent component & also only changes rleatively to XY Plane...
        self.operation = operation
        self.parent_component = None
        self.body_component = None
        self.x_count = x_count
        self.y_count = y_count
        self.fillet_radius = fillet_radius
    
    def setup(self, parent_component: adsk.fusion.Component):
        self.parent_component = parent_component
        self.body_component = create_component(self.parent_component, f"extrude-component-{uuid.uuid4()}")
        
    def run(self, draw_func: Callable[[adsk.fusion.Sketch], None]) -> adsk.fusion.BRepBodies:    
        # create the sketch
        self.sketch = create_sketch(
            component=self.body_component,
            name="extrude-sketch",
            offset=self.plane_offset,
        )
        
        # draw the thing: re blah blah about maths goes in here, e.g points, etc
        draw_func(self.sketch)
        
        # extrude
        return self.extrude()
    
    @abstractmethod
    def extrude(self) -> adsk.fusion.BRepBody:
        pass
    
    def fillet(self, body: adsk.fusion.BRepBody):
        if self.fillet_radius <= 0.0:
            return body
        fillets = self.body_component.features.filletFeatures
        edge_collection = adsk.core.ObjectCollection.create()
        for face in body.faces:
            # Check if the face is parallel to the XY plane
            normal = face.evaluator.getNormalAtPoint(face.pointOnFace)[1]
            if normal.isParallelTo(adsk.core.Vector3D.create(0, 0, 1)):
                for edge in face.edges:
                    edge_collection.add(edge)
                break  # Assuming only one face is parallel to the XY plane

        radius1 = adsk.core.ValueInput.createByReal(self.fillet_radius)
        input1 = fillets.createInput()
        input1.isRollingBallCorner = True
        constRadiusInput = input1.edgeSetInputs.addConstantRadiusEdgeSet(edge_collection, radius1, True)
        constRadiusInput.continuity = adsk.fusion.SurfaceContinuityTypes.TangentSurfaceContinuityType
        # constRadiusInput.tangencyWeight = adsk.core.ValueInput.createByReal(tangency_weight)
        fillets.add(input1)
    
    @property
    def plane_offset(self):
        return self._plane_offset

    @plane_offset.setter
    def plane_offset(self, plane_offset: float):
        self._plane_offset = plane_offset


# full extrusion
class FullExtrude(Extrude):
    def __init__(self, thickness: float, plane_offset: float, x_count: int = 1, y_count: int = 1, fillet_radius: float = 0.0, operation: adsk.fusion.FeatureOperations = adsk.fusion.FeatureOperations.NewBodyFeatureOperation):
        super().__init__(thickness, plane_offset, x_count, y_count, fillet_radius, operation)
        
    def extrude(self) -> adsk.fusion.BRepBody:
        extrudes = self.body_component.features.extrudeFeatures
        profile = self.sketch.profiles.item(0)
        extInput = extrudes.createInput(profile, self.operation)
        extInput.setDistanceExtent(
            False, adsk.core.ValueInput.createByReal(self.thickness)
        )
        extrude = extrudes.add(extInput)
        body = extrude.bodies.item(0)
        body.name = f"{self.body_component.name}-{self.x_count}x{self.y_count}"
        return body

# thin extrusion
class ThinExtrude(Extrude):
    def __init__(self, thickness: float, plane_offset: float, x_count: int = 1, y_count: int = 1, fillet_radius: float = 0.0, operation: adsk.fusion.FeatureOperations = adsk.fusion.FeatureOperations.NewBodyFeatureOperation, stroke_weight: float = 0.0, side: adsk.fusion.ThinExtrudeWallLocation = adsk.fusion.ThinExtrudeWallLocation.Side1):
        super().__init__(thickness, plane_offset, x_count, y_count, fillet_radius, operation)
        self.stroke_weight = stroke_weight
        self.side = side
        
    def extrude(self) -> adsk.fusion.BRepBody:
        extrudes = self.body_component.features.extrudeFeatures
        profile = self.sketch.profiles.item(0)
        extInput = extrudes.createInput(profile, self.operation)
        extInput.setThinExtrude(self.side, adsk.core.ValueInput.createByReal(self.stroke_weight))
        extInput.setDistanceExtent(
            False, adsk.core.ValueInput.createByReal(self.thickness)
        )
        extrude = extrudes.add(extInput)
        body = extrude.bodies.item(0)
        body.name = f"{self.body_component.name}-{self.x_count}x{self.y_count}"
        return body
