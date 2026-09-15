from abc import ABC, abstractmethod
from typing import List, Optional, Protocol

import numpy as np

from .entities import Hand
from .enums import GestureType


class HandDetector(Protocol):
    def process(self, frame_rgb: np.ndarray) -> List[Hand]:
        ...

    def draw_landmarks(self, frame: np.ndarray, hand: Hand) -> None:
        ...

    def close(self) -> None:
        ...


class Camera(Protocol):
    def read(self) -> Optional[np.ndarray]:
        ...

    def release(self) -> None:
        ...

    @property
    def is_opened(self) -> bool:
        ...


class VolumeControl(Protocol):
    def volume_up(self, step: int) -> bool:
        ...

    def volume_down(self, step: int) -> bool:
        ...


class BrightnessControl(Protocol):
    def brightness_up(self, step: int) -> bool:
        ...

    def brightness_down(self, step: int) -> bool:
        ...


class Display(Protocol):
    def show(self, frame: np.ndarray, texts: List[tuple]) -> bool:
        ...

    def close(self) -> None:
        ...