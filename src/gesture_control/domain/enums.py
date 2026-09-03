from enum import Enum


class HandLabel(Enum):
    LEFT = "Izquierda"
    RIGHT = "Derecha"

    @classmethod
    def from_mediapipe(cls, label: str) -> "HandLabel":
        return cls.RIGHT if label == "Right" else cls.LEFT


class PalmState(Enum):
    VISIBLE = "visible"
    NOT_VISIBLE = "no visible"


class GestureType(Enum):
    VOLUME_UP = "volume_up"
    VOLUME_DOWN = "volume_down"
    BRIGHTNESS_UP = "brightness_up"
    BRIGHTNESS_DOWN = "brightness_down"
    NONE = "none"