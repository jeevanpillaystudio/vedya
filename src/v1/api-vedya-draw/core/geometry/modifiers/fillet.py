import adsk.fusion, adsk.core


class Fillet:
    def __init__(self, radius: float):
        self.radius = radius
        self.body_component = None

    def setup(self, body_component: adsk.fusion.Component):
        self.body_component = body_component

    def fillet(self, body: adsk.fusion.BRepBody):
        if self.radius <= 0.0:
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

        radius1 = adsk.core.ValueInput.createByReal(self.radius)
        input1 = fillets.createInput()
        input1.isRollingBallCorner = True
        radius_input = input1.edgeSetInputs.addConstantRadiusEdgeSet(
            edge_collection, radius1, True
        )
        radius_input.continuity = (
            adsk.fusion.SurfaceContinuityTypes.TangentSurfaceContinuityType
        )
        # constRadiusInput.tangencyWeight = adsk.core.ValueInput.createByReal(tangency_weight)
        fillets.add(input1)
        return body

    def run(self, body: adsk.fusion.BRepBody):
        return self.fillet(body)
