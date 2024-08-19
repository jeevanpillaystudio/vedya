class ScaleConfig:
    def __init__(self):
        pass

    ScaleFactor: float = FabricationMethod.CNC

    def __str__(self) -> str:
        return f"ScaleConfig: ScaleFactor={self.ScaleFactor}"


class DepthEffect:
    def __init__(self):
        pass

    Side1 = adsk.fusion.ThinExtrudeWallLocation.Side1
    Side2 = adsk.fusion.ThinExtrudeWallLocation.Side2
    Center = adsk.fusion.ThinExtrudeWallLocation.Center
