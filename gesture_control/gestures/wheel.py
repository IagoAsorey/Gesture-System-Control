"""Three-finger rotary wheel (knob) gesture recognizer."""

from dataclasses import dataclass
import math
import time
from typing import TYPE_CHECKING, Optional, Sequence

from gesture_control import config
from gesture_control.gestures.base import BaseGesture
from gesture_control.gestures.poses import is_three_finger_pinch

if TYPE_CHECKING:
    from gesture_control.detector import DetectedHand

_WRIST = 0
_THUMB_TIP = 4
_INDEX_TIP = 8
_MIDDLE_TIP = 12


def _compute_wheel_angle(hand_landmarks: Sequence) -> float:
    """Computes the rotation angle (in radians) of the 3-finger pinch relative to the wrist.

    Angle increases when rotating clockwise (to the right) from the user's perspective,
    and decreases when rotating counter-clockwise (to the left).
    """
    wrist = hand_landmarks[_WRIST]
    thumb = hand_landmarks[_THUMB_TIP]
    index = hand_landmarks[_INDEX_TIP]
    middle = hand_landmarks[_MIDDLE_TIP]

    pinch_x = (thumb.x + index.x + middle.x) / 3.0
    pinch_y = (thumb.y + index.y + middle.y) / 3.0

    # In the unflipped camera frame, user's physical right corresponds to smaller X
    dx = wrist.x - pinch_x
    dy = pinch_y - wrist.y
    return math.atan2(dy, dx)


@dataclass(slots=True)
class _WheelTrackState:
    """Internal per-hand state for rotary knob tracking."""

    anchor_angle: Optional[float] = None
    last_trigger_ts: float = 0.0


class WheelGesture(BaseGesture):
    """Recognizes rotating the hand like a knob while pinching thumb, index, and middle fingers.

    Emits:
        - "wheel_right": when rotating clockwise (to the right) by at least angle_threshold.
        - "wheel_left": when rotating counter-clockwise (to the left) by at least angle_threshold.
    """

    def __init__(
        self,
        distance_threshold: float = config.WHEEL_DISTANCE_THRESHOLD,
        angle_threshold: float = config.WHEEL_ANGLE_THRESHOLD,
        cooldown_sec: float = config.ACTION_COOLDOWN_SEC,
    ) -> None:
        self.distance_threshold = distance_threshold
        self.angle_threshold = angle_threshold
        self.cooldown_sec = cooldown_sec
        self._tracks: dict[str, _WheelTrackState] = {
            "Right": _WheelTrackState(),
            "Left": _WheelTrackState(),
        }

    def reset(self, hand_label: str) -> None:
        """Resets the angular anchor when a hand leaves the frame."""
        if track := self._tracks.get(hand_label):
            track.anchor_angle = None

    def update(self, hand: "DetectedHand") -> tuple[bool, Optional[str]]:
        """Evaluates the 3-finger knob pose and angular rotation for a detected hand."""
        if not hand.landmarks:
            self.reset(hand.label)
            return False, None

        is_active = is_three_finger_pinch(
            hand.landmarks, hand.label, self.distance_threshold
        )
        if not is_active:
            self.reset(hand.label)
            return False, None

        current_angle = _compute_wheel_angle(hand.landmarks)
        gesture_name = self.evaluate(hand.label, is_active, current_angle)
        return True, gesture_name

    def evaluate(
        self, hand_label: str, is_active: bool, current_angle: float
    ) -> Optional[str]:
        """Evaluates angular displacement and returns 'wheel_right', 'wheel_left', or None."""
        track = self._tracks.get(hand_label)
        if track is None:
            return None

        if not is_active:
            track.anchor_angle = None
            return None

        # First frame holding the 3-finger pinch: set angular anchor without firing
        if track.anchor_angle is None:
            track.anchor_angle = current_angle
            return None

        # Shortest signed angular difference in (-pi, pi]
        delta_angle = math.atan2(
            math.sin(current_angle - track.anchor_angle),
            math.cos(current_angle - track.anchor_angle),
        )
        if abs(delta_angle) < self.angle_threshold:
            return None

        now = time.monotonic()
        if (now - track.last_trigger_ts) < self.cooldown_sec:
            return None

        track.anchor_angle = current_angle
        track.last_trigger_ts = now
        return "wheel_right" if delta_angle > 0 else "wheel_left"
