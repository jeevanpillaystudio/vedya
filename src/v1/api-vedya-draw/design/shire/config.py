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
