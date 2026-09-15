from dataclasses import dataclass
from typing import List

from .enums import HandLabel, PalmState


@dataclass(frozen=True)
class Landmark:
    x: float
    y: float
    z: float


@dataclass(frozen=True)
class Hand:
    label: HandLabel
    landmarks: List[Landmark]
    palm_state: PalmState
    fingers_up: List[bool]

    @property
    def is_fist(self) -> bool:
        return not any(self.fingers_up)

    @property
    def wrist_y(self) -> float:
        return self.landmarks[0].y if self.landmarks else 0.0