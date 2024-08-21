from .float import Float


class Millimeter(Float):
    def __init__(self, value: float):
        super().__init__(value)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.value})"
