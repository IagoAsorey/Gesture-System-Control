"""Vertical closed-fist drag gesture recognizer."""

from dataclasses import dataclass
import time
from typing import TYPE_CHECKING, Optional

from gesture_control import config
from gesture_control.gestures.base import BaseGesture
from gesture_control.gestures.poses import is_palm_fist

if TYPE_CHECKING:
    from gesture_control.detector import DetectedHand


@dataclass(slots=True)
class _VerticalTrackState:
    """Internal per-hand state for vertical drag tracking."""

    anchor_y: Optional[float] = None
    last_trigger_ts: float = 0.0


class FistVerticalGesture(BaseGesture):
    """Recognizes vertical upward/downward movement while holding a closed fist.

    Emits:
        - "fist_up": when the closed fist moves upward by at least step_threshold.
        - "fist_down": when the closed fist moves downward by at least step_threshold.
    """

    def __init__(
        self,
        step_threshold: float = config.MOVEMENT_STEP_THRESHOLD,
        cooldown_sec: float = config.ACTION_COOLDOWN_SEC,
    ) -> None:
        self.step_threshold = step_threshold
        self.cooldown_sec = cooldown_sec
        self._tracks: dict[str, _VerticalTrackState] = {
            "Right": _VerticalTrackState(),
            "Left": _VerticalTrackState(),
        }

    def reset(self, hand_label: str) -> None:
        """Resets the vertical anchor for the given hand."""
        if track := self._tracks.get(hand_label):
            track.anchor_y = None

    def update(self, hand: "DetectedHand") -> tuple[bool, Optional[str]]:
        """Evaluates palm-fist pose and vertical wrist displacement for a hand."""
        is_active = (
            is_palm_fist(hand.landmarks, hand.label)
            if hand.landmarks
            else hand.is_gesture_active
        )
        gesture_name = self.evaluate(hand.label, is_active, hand.wrist_y)
        return is_active, gesture_name

    def evaluate(
        self, hand_label: str, is_active: bool, current_y: float
    ) -> Optional[str]:
        """Evaluates vertical wrist movement and returns 'fist_up', 'fist_down', or None."""
        track = self._tracks.get(hand_label)
        if track is None:
            return None

        if not is_active:
            track.anchor_y = None
            return None

        # First frame with a closed fist: set the vertical anchor without firing an event
        if track.anchor_y is None:
            track.anchor_y = current_y
            return None

        # Positive delta means the hand moved upward (Y decreases toward top of frame)
        delta_y = track.anchor_y - current_y
        if abs(delta_y) < self.step_threshold:
            return None

        now = time.monotonic()
        if (now - track.last_trigger_ts) < self.cooldown_sec:
            return None

        track.anchor_y = current_y
        track.last_trigger_ts = now
        return "fist_up" if delta_y > 0 else "fist_down"
