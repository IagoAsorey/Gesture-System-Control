"""Directional 4-way swipe gesture recognizer with strict extended-finger selection."""

from dataclasses import dataclass
import time
from typing import TYPE_CHECKING, Any, Optional

from gesture_control import config
from gesture_control.gestures.base import BaseGesture
from gesture_control.gestures.poses import is_exact_extended_pose, normalize_fingers

if TYPE_CHECKING:
    from gesture_control.detector import DetectedHand


@dataclass(slots=True)
class _SwipeTrackState:
    """Internal per-hand state for 2D anchor-based swipe tracking."""

    anchor_x: Optional[float] = None
    anchor_y: Optional[float] = None
    last_trigger_ts: float = 0.0


class SwipeGesture(BaseGesture):
    """Recognizes 4-directional swipes (up, down, left, right) for an exact set of extended fingers.

    Automatically accounts for mirror-mode horizontal coordinates so that:
        - Moving the hand toward the user's physical right emits "swipe_right".
        - Moving the hand toward the user's physical left emits "swipe_left".
        - Moving the hand upward emits "swipe_up".
        - Moving the hand downward emits "swipe_down".
    """

    def __init__(
        self,
        fingers: Any = (0, 1, 0, 0, 0),
        step_threshold: float = config.SWIPE_STEP_THRESHOLD,
        cooldown_sec: float = config.ACTION_COOLDOWN_SEC,
    ) -> None:
        self.fingers: tuple[str, ...] = normalize_fingers(fingers)
        self.step_threshold = step_threshold
        self.cooldown_sec = cooldown_sec
        self._tracks: dict[str, _SwipeTrackState] = {
            "Right": _SwipeTrackState(),
            "Left": _SwipeTrackState(),
        }

    def reset(self, hand_label: str) -> None:
        """Resets the 2D swipe anchor for the given hand."""
        if track := self._tracks.get(hand_label):
            track.anchor_x = None
            track.anchor_y = None

    def update(self, hand: "DetectedHand") -> tuple[bool, Optional[str]]:
        """Evaluates the exact extended-finger pose and 2D displacement for a hand."""
        if not hand.landmarks:
            self.reset(hand.label)
            return False, None

        is_active = is_exact_extended_pose(hand.landmarks, hand.label, self.fingers)
        current_x = hand.landmarks[0].x
        current_y = hand.landmarks[0].y
        gesture_name = self.evaluate(hand.label, is_active, current_x, current_y)
        return is_active, gesture_name

    def evaluate(
        self,
        hand_label: str,
        is_active: bool,
        current_x: float,
        current_y: float,
    ) -> Optional[str]:
        """Evaluates 2D movement and returns 'swipe_up', 'swipe_down', 'swipe_left', 'swipe_right', or None."""
        track = self._tracks.get(hand_label)
        if track is None:
            return None

        if not is_active:
            track.anchor_x = None
            track.anchor_y = None
            return None

        # First frame holding the target finger pose: set 2D anchor without firing
        if track.anchor_x is None or track.anchor_y is None:
            track.anchor_x = current_x
            track.anchor_y = current_y
            return None

        # In the unflipped camera frame:
        # - Moving to the user's physical right decreases X -> delta_x > 0
        # - Moving upward decreases Y -> delta_y > 0
        delta_x = track.anchor_x - current_x
        delta_y = track.anchor_y - current_y

        if max(abs(delta_x), abs(delta_y)) < self.step_threshold:
            return None

        now = time.monotonic()
        if (now - track.last_trigger_ts) < self.cooldown_sec:
            return None

        track.anchor_x = current_x
        track.anchor_y = current_y
        track.last_trigger_ts = now

        if abs(delta_x) >= abs(delta_y):
            return "swipe_right" if delta_x > 0 else "swipe_left"
        return "swipe_up" if delta_y > 0 else "swipe_down"
