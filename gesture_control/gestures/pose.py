"""Extended-finger pose family gesture recognizers (static pose, pose_wheel, and pose_swipe)."""

from typing import TYPE_CHECKING, Any, Optional

from gesture_control import config
from gesture_control.gestures.base import BaseGesture
from gesture_control.gestures.movements import (
    HoldTriggerTracker,
    SwipeMovementTracker,
    WheelMovementTracker,
)
from gesture_control.gestures.poses import (
    compute_group_angle,
    is_exact_extended_pose,
    normalize_fingers,
)

if TYPE_CHECKING:
    from gesture_control.detector import DetectedHand


class PoseGesture(BaseGesture):
    """Recognizes holding an exact combination of extended/folded fingers.

    Emits:
        - "pose": once after holding the exact finger pose for `hold_sec`.
          Requires changing the pose before triggering again.
    """

    def __init__(
        self,
        fingers: Any = (0, 1, 0, 0, 0),
        hold_sec: float = config.POSE_HOLD_DURATION_SEC,
        cooldown_sec: float = config.POSE_COOLDOWN_SEC,
    ) -> None:
        self.fingers: tuple[str, ...] = normalize_fingers(fingers)
        self._tracker = HoldTriggerTracker(
            event_name="pose",
            hold_sec=hold_sec,
            cooldown_sec=cooldown_sec,
        )

    def reset(self, hand_label: str) -> None:
        """Resets hold state when a hand leaves the frame."""
        self._tracker.reset(hand_label)

    def update(self, hand: "DetectedHand") -> tuple[bool, Optional[str]]:
        """Evaluates the exact extended-finger pose and hold confirmation."""
        if not hand.landmarks:
            self.reset(hand.label)
            return False, None

        is_active = is_exact_extended_pose(hand.landmarks, hand.label, self.fingers)
        gesture_name = self._tracker.evaluate(hand.label, is_active)
        return is_active, gesture_name


class PoseWheelGesture(BaseGesture):
    """Recognizes rotating the hand like a knob while holding an exact extended-finger pose.

    Emits:
        - "pose_wheel_right": when rotating clockwise (to the right) by at least angle_threshold.
        - "pose_wheel_left": when rotating counter-clockwise (to the left) by at least angle_threshold.
    """

    def __init__(
        self,
        fingers: Any = (0, 1, 0, 0, 0),
        angle_threshold: float = config.WHEEL_ANGLE_THRESHOLD,
        cooldown_sec: float = config.ACTION_COOLDOWN_SEC,
    ) -> None:
        self.fingers: tuple[str, ...] = normalize_fingers(fingers)
        self._tracker = WheelMovementTracker(
            prefix="pose",
            angle_threshold=angle_threshold,
            cooldown_sec=cooldown_sec,
        )

    def reset(self, hand_label: str) -> None:
        """Resets the angular anchor when a hand leaves the frame."""
        self._tracker.reset(hand_label)

    def update(self, hand: "DetectedHand") -> tuple[bool, Optional[str]]:
        """Evaluates the exact extended-finger pose and angular rotation for a hand."""
        if not hand.landmarks:
            self.reset(hand.label)
            return False, None

        is_active = is_exact_extended_pose(hand.landmarks, hand.label, self.fingers)
        if not is_active:
            self.reset(hand.label)
            return False, None

        current_angle = compute_group_angle(hand.landmarks, self.fingers)
        gesture_name = self.evaluate(hand.label, is_active, current_angle)
        return True, gesture_name

    def evaluate(
        self, hand_label: str, is_active: bool, current_angle: float
    ) -> Optional[str]:
        """Evaluates angular displacement and returns 'pose_wheel_right', 'pose_wheel_left', or None."""
        return self._tracker.evaluate(hand_label, is_active, current_angle)


class PoseSwipeGesture(BaseGesture):
    """Recognizes 4-directional swipes (up, down, left, right) while holding an exact extended-finger pose.

    Emits:
        - "pose_swipe_right", "pose_swipe_left", "pose_swipe_up", "pose_swipe_down"
    """

    def __init__(
        self,
        fingers: Any = (0, 1, 0, 0, 0),
        step_threshold: float = config.SWIPE_STEP_THRESHOLD,
        cooldown_sec: float = config.ACTION_COOLDOWN_SEC,
    ) -> None:
        self.fingers: tuple[str, ...] = normalize_fingers(fingers)
        self._tracker = SwipeMovementTracker(
            prefix="pose",
            step_threshold=step_threshold,
            cooldown_sec=cooldown_sec,
        )

    def reset(self, hand_label: str) -> None:
        """Resets the 2D swipe anchor when a hand leaves the frame."""
        self._tracker.reset(hand_label)

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
        """Evaluates 2D movement and returns 'pose_swipe_up/down/left/right' or None."""
        return self._tracker.evaluate(hand_label, is_active, current_x, current_y)
