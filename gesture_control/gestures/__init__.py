"""Modular gesture recognizers package."""

from gesture_control.gestures.base import BaseGesture
from gesture_control.gestures.movements import (
    HoldTriggerTracker,
    SwipeMovementTracker,
    WheelMovementTracker,
)
from gesture_control.gestures.pinch import (
    PinchGesture,
    PinchSwipeGesture,
    PinchWheelGesture,
)
from gesture_control.gestures.pose import (
    PoseGesture,
    PoseSwipeGesture,
    PoseWheelGesture,
)
from gesture_control.gestures.poses import (
    FINGER_NAMES,
    FINGER_TIPS,
    compute_group_angle,
    is_exact_extended_pose,
    is_exact_pinch,
    is_finger_extended,
    is_palm_visible,
    is_pinch,
    normalize_fingers,
    pinch_group_max_distance,
)

__all__ = [
    "BaseGesture",
    "FINGER_NAMES",
    "FINGER_TIPS",
    "HoldTriggerTracker",
    "PinchGesture",
    "PinchSwipeGesture",
    "PinchWheelGesture",
    "PoseGesture",
    "PoseSwipeGesture",
    "PoseWheelGesture",
    "SwipeMovementTracker",
    "WheelMovementTracker",
    "compute_group_angle",
    "is_exact_extended_pose",
    "is_exact_pinch",
    "is_finger_extended",
    "is_palm_visible",
    "is_pinch",
    "normalize_fingers",
    "pinch_group_max_distance",
]
