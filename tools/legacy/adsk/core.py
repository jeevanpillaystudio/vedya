"""The `adsk.core` members Vedya's scripts call: points, values, collections, the application.

Lengths are in centimetres, as Fusion's API takes them.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import ClassVar

__all__ = [
    "Application",
    "BoundingBox3D",
    "Matrix3D",
    "ObjectCollection",
    "Point3D",
    "Product",
    "UserInterface",
    "ValueInput",
]


class Point3D:
    """A point, in centimetres."""

    def __init__(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z

    @staticmethod
    def create(x: float = 0.0, y: float = 0.0, z: float = 0.0) -> Point3D:
        return Point3D(float(x), float(y), float(z))


class BoundingBox3D:
    """The box aligned with the axes that holds a body, from `minPoint` to `maxPoint`."""

    def __init__(self, minPoint: Point3D, maxPoint: Point3D) -> None:
        self.minPoint = minPoint
        self.maxPoint = maxPoint


class Matrix3D:
    """A transform. The stand-in has only the identity, the only one the scripts make."""

    @staticmethod
    def create() -> Matrix3D:
        return Matrix3D()


class ValueInput:
    """A value passed to a feature: a length in centimetres."""

    def __init__(self, real_value: float) -> None:
        self.realValue = real_value

    @staticmethod
    def createByReal(realValue: float) -> ValueInput:
        return ValueInput(float(realValue))


class ObjectCollection:
    """A list of API objects, as the scripts pass bodies to a combine."""

    def __init__(self) -> None:
        self._items: list[object] = []

    @staticmethod
    def create() -> ObjectCollection:
        return ObjectCollection()

    def add(self, item: object) -> bool:
        self._items.append(item)
        return True

    def removeByIndex(self, index: int) -> bool:
        del self._items[index]
        return True

    @property
    def count(self) -> int:
        return len(self._items)

    def item(self, index: int) -> object:
        return self._items[index]

    def __getitem__(self, index: int) -> object:
        return self._items[index]

    def __iter__(self) -> Iterator[object]:
        return iter(list(self._items))

    def __len__(self) -> int:
        return len(self._items)


class Product:
    """What a document holds; `adsk.fusion.Design` is the one the scripts use."""


class UserInterface:
    """Fusion's dialogs. A message box is recorded in `messages` instead of shown.

    The scripts open a message box only to report an exception they caught, so the
    tools that run them treat any message as a failure.
    """

    def __init__(self) -> None:
        self.messages: list[str] = []

    def messageBox(self, text: str, title: str = "", buttons: int = 0, icon: int = 0) -> int:
        self.messages.append(text)
        return 0


class Application:
    """The running application, whose active product is the open document."""

    _instance: ClassVar[Application | None] = None

    def __init__(self) -> None:
        self._product: Product | None = None
        self._ui = UserInterface()

    @staticmethod
    def get() -> Application:
        if Application._instance is None:
            Application._instance = Application()
        return Application._instance

    @property
    def activeProduct(self) -> Product:
        if self._product is None:
            raise RuntimeError("no document is open in the stand-in")
        return self._product

    @property
    def userInterface(self) -> UserInterface:
        return self._ui

    def open_product(self, product: Product) -> None:
        """Make `product` the active document, with a user interface that has shown nothing."""
        self._product = product
        self._ui = UserInterface()
