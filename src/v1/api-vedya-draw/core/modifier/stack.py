# from typing import List
from typing import List
from .index import Modifier
import adsk.fusion


class ModifierStack:
    def __init__(self):
        self.modifiers: List[Modifier] = []

    def add_modifier(self, modifier: Modifier):
        self.modifiers.append(modifier)

    def remove_modifier(self, index: int):
        if 0 <= index < len(self.modifiers):
            del self.modifiers[index]

    def move_modifier(self, from_index: int, to_index: int):
        if 0 <= from_index < len(self.modifiers) and 0 <= to_index < len(
            self.modifiers
        ):
            modifier = self.modifiers.pop(from_index)
            self.modifiers.insert(to_index, modifier)

    def apply(self, sketch: adsk.fusion.Sketch):
        for modifier in self.modifiers:
            modifier.apply(sketch)

    def preview(self, sketch: adsk.fusion.Sketch):
        # This could be implemented to show a temporary preview
        pass
