"""Pinch and rotary pinch-wheel gesture recognizers with strict finger selection."""

from dataclasses import dataclass
import math
import time
from typing import TYPE_CHECKING, Optional, Sequence

from gesture_control import config
from gesture_control.gestures.base import BaseGesture
from gesture_control.gestures.poses import (
    FINGER_TIPS,
    is_exact_pinch,
    normalize_fingers,
    pinch_group_max_distance,
)

if TYPE_CHECKING:
    from gesture_control.detector import DetectedHand

_WRIST = 0


@dataclass(slots=True)
class _PinchState:
    """Internal per-hand state for edge-triggered pinch detection."""

    is_pinched: bool = False
    last_trigger_ts: float = 0.0


class PinchGesture(BaseGesture):
    """Recognizes when the user brings an exact set of fingertips together.

    Emits:
        - "pinch": once when the configured fingers touch (rising edge).
          Requires separating the fingers before triggering again.
    """

    def __init__(
        self,
        fingers: Sequence[str] = ("thumb", "index"),
        distance_threshold: float = config.PINCH_DISTANCE_THRESHOLD,
        cooldown_sec: float = config.PINCH_COOLDOWN_SEC,
    ) -> None:
        self.fingers: tuple[str, ...] = normalize_fingers(fingers)
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
        """Evaluates exact multi-finger pinch pose and triggers on contact."""
        state = self._states.get(hand.label)
        if state is None or not hand.landmarks:
            return False, None

        if state.is_pinched:
            # Hysteresis: stay in pinched state until the active fingers separate
            if (
                pinch_group_max_distance(hand.landmarks, self.fingers)
                > self.release_threshold
            ):
                state.is_pinched = False
                return False, None
            # If an extra finger joins while holding, mark pose inactive without re-arming
            is_still_exact = is_exact_pinch(
                hand.landmarks, hand.label, self.fingers, self.release_threshold
            )
            return is_still_exact, None

        if not is_exact_pinch(
            hand.landmarks, hand.label, self.fingers, self.distance_threshold
        ):
            return False, None

        state.is_pinched = True
        now = time.monotonic()
        if (now - state.last_trigger_ts) < self.cooldown_sec:
            return True, None

        state.last_trigger_ts = now
        return True, "pinch"


def _compute_pinch_wheel_angle(
    hand_landmarks: Sequence, fingers: Sequence[str]
) -> float:
    """Computes the rotation angle (in radians) of the pinched fingers relative to the wrist.

    Angle increases when rotating clockwise (to the right) from the user's perspective,
    and decreases when rotating counter-clockwise (to the left).
    """
    wrist = hand_landmarks[_WRIST]
    indices = [FINGER_TIPS[f] for f in fingers]
    pinch_x = sum(hand_landmarks[i].x for i in indices) / len(indices)
    pinch_y = sum(hand_landmarks[i].y for i in indices) / len(indices)

    # In the unflipped camera frame, user's physical right corresponds to smaller X
    dx = wrist.x - pinch_x
    dy = pinch_y - wrist.y
    return math.atan2(dy, dx)


@dataclass(slots=True)
class _PinchWheelTrackState:
    """Internal per-hand state for rotary pinch-wheel tracking."""

    anchor_angle: Optional[float] = None
    last_trigger_ts: float = 0.0


class PinchWheelGesture(BaseGesture):
    """Recognizes rotating the hand like a knob while pinching an exact set of fingers.

    Emits:
        - "pinch_wheel_right": when rotating clockwise (to the right) by at least angle_threshold.
        - "pinch_wheel_left": when rotating counter-clockwise (to the left) by at least angle_threshold.
    """

    def __init__(
        self,
        fingers: Sequence[str] = ("thumb", "index", "middle"),
        distance_threshold: float = config.PINCH_WHEEL_DISTANCE_THRESHOLD,
        angle_threshold: float = config.PINCH_WHEEL_ANGLE_THRESHOLD,
        cooldown_sec: float = config.ACTION_COOLDOWN_SEC,
    ) -> None:
        self.fingers: tuple[str, ...] = normalize_fingers(fingers)
        self.distance_threshold = distance_threshold
        self.angle_threshold = angle_threshold
        self.cooldown_sec = cooldown_sec
        self._tracks: dict[str, _PinchWheelTrackState] = {
            "Right": _PinchWheelTrackState(),
            "Left": _PinchWheelTrackState(),
        }

    def reset(self, hand_label: str) -> None:
        """Resets the angular anchor when a hand leaves the frame."""
        if track := self._tracks.get(hand_label):
            track.anchor_angle = None

    def update(self, hand: "DetectedHand") -> tuple[bool, Optional[str]]:
        """Evaluates the exact pinch-wheel pose and angular rotation for a detected hand."""
        if not hand.landmarks:
            self.reset(hand.label)
            return False, None

        is_active = is_exact_pinch(
            hand.landmarks, hand.label, self.fingers, self.distance_threshold
        )
        if not is_active:
            self.reset(hand.label)
            return False, None

        current_angle = _compute_pinch_wheel_angle(hand.landmarks, self.fingers)
        gesture_name = self.evaluate(hand.label, is_active, current_angle)
        return True, gesture_name

    def evaluate(
        self, hand_label: str, is_active: bool, current_angle: float
    ) -> Optional[str]:
        """Evaluates angular displacement and returns 'pinch_wheel_right', 'pinch_wheel_left', or None."""
        track = self._tracks.get(hand_label)
        if track is None:
            return None

        if not is_active:
            track.anchor_angle = None
            return None

        # First frame holding the exact pinch: set angular anchor without firing
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
        return "pinch_wheel_right" if delta_angle > 0 else "pinch_wheel_left"
