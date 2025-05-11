import adsk.fusion


class FabricationMode:
    def __init__(self):
        pass

    NORMAL = "Normal"
    SLICER = "Slicer"
    AGGREGATOR = "Aggregator"


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
