from ...utils import log
import adsk.fusion, adsk.core


class FilletFace:
    Top = 1
    Bottom = 2


class FilletEdge:
    Outer = 1
    Inner = 2


class Fillet:
    def __init__(
        self,
        radius: float,
        target_face: FilletFace = FilletFace.Top,
        target_edge: FilletEdge = FilletEdge.Outer,
    ):
        self.radius = radius
        self.target_face = target_face
        self.target_edge = target_edge

    def fillet(self, body: adsk.fusion.BRepBody, component: adsk.fusion.Component):
        if self.radius <= 0.0:
            return body
        fillets = component.features.filletFeatures

        target_face = self.get_xy_faces(body, self.target_face)
        edge_collection = self.get_edge(target_face)

        log(f"DEBUG: Filleting {len(edge_collection)} edges")

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

    # @NOTE now a thin extrude circle has two edges on a single face
    def get_edge(self, target_face: adsk.fusion.BRepFace) -> adsk.core.ObjectCollection:
        edge_collection = adsk.core.ObjectCollection.create()
        for edge in target_face.edges:
            edge_collection.add(edge)
        return edge_collection

    # @NOTE only works with XY faces; and assuming only two faces
    def get_xy_faces(self, body, target_face: FilletFace) -> adsk.fusion.BRepFace:
        parallel_faces = adsk.core.ObjectCollection.create()
        for face in body.faces:
            normal = face.evaluator.getNormalAtPoint(face.pointOnFace)[1]
            if normal.isParallelTo(adsk.core.Vector3D.create(0, 0, 1)):
                parallel_faces.add(face)

        # sort face by z value
        sorted_faces = sorted(
            parallel_faces,
            key=lambda face: face.pointOnFace.z,
            reverse=target_face == FilletFace.Top,
        )

        if target_face == FilletFace.Top:
            # pick the top face
            return sorted_faces[0]
        elif target_face == FilletFace.Bottom:
            # pick the bottom face
            return sorted_faces[-1]

    def run(self, bodies: adsk.fusion.BRepBodies, component: adsk.fusion.Component):
        for body in bodies:
            self.fillet(body, component)
