"""Pinch family gesture recognizers (static pinch, pinch_wheel, and pinch_swipe)."""

from dataclasses import dataclass
import time
from typing import TYPE_CHECKING, Any, Optional

from gesture_control import config
from gesture_control.gestures.base import BaseGesture
from gesture_control.gestures.movements import (
    SwipeMovementTracker,
    WheelMovementTracker,
)
from gesture_control.gestures.poses import (
    compute_group_angle,
    is_exact_pinch,
    normalize_fingers,
    pinch_group_max_distance,
)

if TYPE_CHECKING:
    from gesture_control.detector import DetectedHand


@dataclass(slots=True)
class _PinchState:
    """Internal per-hand state for edge-triggered pinch detection with hysteresis."""

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
        fingers: Any = (1, 1, 0, 0, 0),
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


class PinchWheelGesture(BaseGesture):
    """Recognizes rotating the hand like a knob while pinching an exact set of fingers.

    Emits:
        - "pinch_wheel_right": when rotating clockwise (to the right) by at least angle_threshold.
        - "pinch_wheel_left": when rotating counter-clockwise (to the left) by at least angle_threshold.
    """

    def __init__(
        self,
        fingers: Any = (1, 1, 1, 0, 0),
        distance_threshold: float = config.PINCH_WHEEL_DISTANCE_THRESHOLD,
        angle_threshold: float = config.WHEEL_ANGLE_THRESHOLD,
        cooldown_sec: float = config.ACTION_COOLDOWN_SEC,
    ) -> None:
        self.fingers: tuple[str, ...] = normalize_fingers(fingers)
        self.distance_threshold = distance_threshold
        self._tracker = WheelMovementTracker(
            prefix="pinch",
            angle_threshold=angle_threshold,
            cooldown_sec=cooldown_sec,
        )

    def reset(self, hand_label: str) -> None:
        """Resets the angular anchor when a hand leaves the frame."""
        self._tracker.reset(hand_label)

    def update(self, hand: "DetectedHand") -> tuple[bool, Optional[str]]:
        """Evaluates the exact pinch pose and angular rotation for a detected hand."""
        if not hand.landmarks:
            self.reset(hand.label)
            return False, None

        is_active = is_exact_pinch(
            hand.landmarks, hand.label, self.fingers, self.distance_threshold
        )
        if not is_active:
            self.reset(hand.label)
            return False, None

        current_angle = compute_group_angle(hand.landmarks, self.fingers)
        gesture_name = self.evaluate(hand.label, is_active, current_angle)
        return True, gesture_name

    def evaluate(
        self, hand_label: str, is_active: bool, current_angle: float
    ) -> Optional[str]:
        """Evaluates angular displacement and returns 'pinch_wheel_right', 'pinch_wheel_left', or None."""
        return self._tracker.evaluate(hand_label, is_active, current_angle)


class PinchSwipeGesture(BaseGesture):
    """Recognizes 4-directional swipes while holding an exact multi-finger pinch.

    Emits:
        - "pinch_swipe_right", "pinch_swipe_left", "pinch_swipe_up", "pinch_swipe_down"
    """

    def __init__(
        self,
        fingers: Any = (1, 1, 0, 0, 0),
        distance_threshold: float = config.PINCH_WHEEL_DISTANCE_THRESHOLD,
        step_threshold: float = config.SWIPE_STEP_THRESHOLD,
        cooldown_sec: float = config.ACTION_COOLDOWN_SEC,
    ) -> None:
        self.fingers: tuple[str, ...] = normalize_fingers(fingers)
        self.distance_threshold = distance_threshold
        self._tracker = SwipeMovementTracker(
            prefix="pinch",
            step_threshold=step_threshold,
            cooldown_sec=cooldown_sec,
        )

    def reset(self, hand_label: str) -> None:
        """Resets the 2D swipe anchor when a hand leaves the frame."""
        self._tracker.reset(hand_label)

    def update(self, hand: "DetectedHand") -> tuple[bool, Optional[str]]:
        """Evaluates the exact pinch pose and 2D swipe movement for a detected hand."""
        if not hand.landmarks:
            self.reset(hand.label)
            return False, None

        is_active = is_exact_pinch(
            hand.landmarks, hand.label, self.fingers, self.distance_threshold
        )
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
        """Evaluates 2D displacement and returns 'pinch_swipe_up/down/left/right' or None."""
        return self._tracker.evaluate(hand_label, is_active, current_x, current_y)
