class Float:
    def __init__(self, value: float):
        self.value = float(value)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.value})"

    def __str__(self):
        return str(self.value)

    def __float__(self):
        return self.value

    def __add__(self, other):
        return self.__class__(self.value + float(other))

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        return self.__class__(self.value - float(other))

    def __rsub__(self, other):
        return self.__class__(float(other) - self.value)

    def __mul__(self, other):
        return self.__class__(self.value * float(other))

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        return self.__class__(self.value / float(other))

    def __rtruediv__(self, other):
        return self.__class__(float(other) / self.value)

    def __eq__(self, other):
        return self.value == float(other)

    def __lt__(self, other):
        return self.value < float(other)

    def __le__(self, other):
        return self.value <= float(other)

    def __gt__(self, other):
        return self.value > float(other)

    def __ge__(self, other):
        return self.value >= float(other)
