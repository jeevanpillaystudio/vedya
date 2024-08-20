SCALE_FACTOR = 1.0


class AppConfig:
    """
    List of the configurations for the creation
    """

    def __init__(self):
        pass

    def __str__(self) -> str:
        return f"AppConfig: HoleRadius={self.HoleRadius}, Extrude={self.Extrude}, MaxWidth={self.MaxWidth}, MaxLength={self.MaxLength}, LayerDepth={self.LayerDepth}"

    Extrude = True

    HoleRadius = 0.48 * 12 * SCALE_FACTOR
    MaxWidth = 96.0 * SCALE_FACTOR
    MaxLength = 64.0 * SCALE_FACTOR
    LayerDepth = 0.48 * SCALE_FACTOR
    StrokeWeight = 0.72 * SCALE_FACTOR

    BorderWidth = 0.48 * 4 * SCALE_FACTOR
    BorderDepth = (1.28 * 2) * SCALE_FACTOR

    SlicerRecursiveDepthLimit = 4

    def aspect_ratio(self):
        return self.MaxLength / self.MaxWidth


class BackgroundConfig:
    def __init__(self):
        pass

    MaxWidth = AppConfig.MaxWidth
    MaxLength = AppConfig.MaxLength
    ExtrudeHeight = AppConfig.LayerDepth * 2 * SCALE_FACTOR


class DiagonalRectangleConfig:
    def __init__(self):
        pass

    def __str__(self) -> str:
        return f"DiagonalRectangleConfig: NumPoints={self.NumPoints}, StrokeWeight={self.StrokeWeight}, OuterDiagonalRectangleWidth={self.OuterDiagonalRectangleWidth}, OuterDiagonalRectangleHeight={self.OuterDiagonalRectangleHeight}, MiddleDiagonalRectangleWidth={self.MiddleDiagonalRectangleWidth}, MiddleDiagonalRectangleHeight={self.MiddleDiagonalRectangleHeight}, InnerDiagonalRectangleWidth={self.InnerDiagonalRectangleWidth}, InnerDiagonalRectangleHeight={self.InnerDiagonalRectangleHeight}"

    OuterDiagonalRectangleWidth = (32.0 - 1.0) * SCALE_FACTOR
    OuterDiagonalRectangleHeight = (32.0 - 1.0) * SCALE_FACTOR
    OuterDiagonalRectangleStrokeWeight = AppConfig.StrokeWeight * SCALE_FACTOR

    MiddleDiagonalRectangleWidth = (64.0 - 16.0) / (2.0) * SCALE_FACTOR
    MiddleDiagonalRectangleHeight = (64.0 - 16.0) / (2.0) * SCALE_FACTOR
    MiddleDiagonalRectangleStrokeWeight = AppConfig.StrokeWeight * SCALE_FACTOR

    InnerDiagonalRectangleWidth = 32.0 / 2.0 * SCALE_FACTOR
    InnerDiagonalRectangleHeight = 32.0 / 2.0 * SCALE_FACTOR
    InnerDiagonalRectangleStrokeWeight = AppConfig.StrokeWeight * SCALE_FACTOR


class AstroidConfig:
    def __init__(self):
        pass

    def __str__(self) -> str:
        return f"AstroidConfig: NumPoints={self.NumPoints}, N={self.N}, OuterAstroidRadius={self.OuterAstroidRadius}, InnerAstroidRadius={self.InnerAstroidRadius}"

    N = 2 / 3
    NumPoints = 128

    OuterAstroidRadius = (32.0 - 2.56) * SCALE_FACTOR
    OuterAstroidStrokeWeight = AppConfig.StrokeWeight * SCALE_FACTOR

    InnerAstroidRadius = (16.0 + 2.56) * SCALE_FACTOR
    InnerAstroidStrokeWeight = AppConfig.StrokeWeight * SCALE_FACTOR
