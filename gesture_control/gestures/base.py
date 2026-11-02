"""Base interface for hand gesture recognizers."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from gesture_control.detector import DetectedHand


class BaseGesture(ABC):
    """Base interface for all hand gesture recognizers."""

    @abstractmethod
    def update(self, hand: "DetectedHand") -> tuple[bool, Optional[str]]:
        """Evaluates a detected hand for the current frame.

        Returns:
            A tuple of (is_pose_active, triggered_gesture_name).
        """

    @abstractmethod
    def reset(self, hand_label: str) -> None:
        """Resets internal tracking state when a hand leaves the frame."""
