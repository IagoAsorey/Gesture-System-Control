"""Thumb-index pinch gesture recognizer."""

from dataclasses import dataclass
import time
from typing import TYPE_CHECKING, Optional

from gesture_control import config
from gesture_control.gestures.base import BaseGesture
from gesture_control.gestures.poses import is_pinch, pinch_distance

if TYPE_CHECKING:
    from gesture_control.detector import DetectedHand


@dataclass(slots=True)
class _PinchState:
    """Internal per-hand state for edge-triggered pinch detection."""

    is_pinched: bool = False
    last_trigger_ts: float = 0.0


class PinchGesture(BaseGesture):
    """Recognizes when the user brings their index finger and thumb tips together.

    Emits:
        - "pinch": once when the thumb and index finger touch (rising edge).
          Requires separating the fingers before triggering again.
    """

    def __init__(
        self,
        distance_threshold: float = config.PINCH_DISTANCE_THRESHOLD,
        cooldown_sec: float = config.PINCH_COOLDOWN_SEC,
    ) -> None:
        self.distance_threshold = distance_threshold
        self.release_threshold = distance_threshold * 1.4
        self.cooldown_sec = cooldown_sec
        self._states: dict[str, _PinchState] = {
            "Right": _PinchState(),
            "Left": _PinchState(),
        }

    def reset(self, hand_label: str) -> None:
        """Resets pinch state when a hand leaves the frame."""
        if state := self._states.get(hand_label):
            state.is_pinched = False

    def update(self, hand: "DetectedHand") -> tuple[bool, Optional[str]]:
        """Evaluates thumb-index pinch pose and triggers on contact."""
        state = self._states.get(hand.label)
        if state is None or not hand.landmarks:
            return False, None

        if state.is_pinched:
            # Hysteresis: stay in pinched state until fingers separate past release_threshold
            if pinch_distance(hand.landmarks) > self.release_threshold:
                state.is_pinched = False
                return False, None
            return True, None

        if not is_pinch(hand.landmarks, hand.label, self.distance_threshold):
            return False, None

        state.is_pinched = True
        now = time.monotonic()
        if (now - state.last_trigger_ts) < self.cooldown_sec:
            return True, None

        state.last_trigger_ts = now
        return True, "pinch"
