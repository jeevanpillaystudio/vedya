class Measurement:
    def __init__(self, value: float):
        self.value = value  # Value is always in mm

    def __str__(self):
        return f"{self.value} mm"
