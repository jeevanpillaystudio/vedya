import adsk.fusion


class FabricationType:
    def __init__(self):
        pass

    PRINT_3D = "Print3D"
    LASER_CUT = "Laser"
    CNC_MILL = "CNC"

    @classmethod
    def get_name(cls, value):
        # Find the attribute by its value
        for attr in dir(cls):
            if getattr(cls, attr) == value and not attr.startswith("__"):
                return attr
        return None


class DesignType:
    def __init__(self):
        pass

    DIRECT = adsk.fusion.DesignTypes.DirectDesignType
    PARAMETRIC = adsk.fusion.DesignTypes.ParametricDesignType


class Measurement:
    def __init__(self, value: float):
        self.value = value  # Value is always in mm

    def __str__(self):
        return f"{self.value} mm"
