"""Gesture System Control package for hand tracking and system actions."""

from gesture_control import config
from gesture_control.actions import (
    BaseAction,
    BrightnessAction,
    CommandAction,
    MediaNextAction,
    MediaPlayPauseAction,
    MediaPreviousAction,
    VolumeAction,
    create_default_actions,
)
from gesture_control.controller import HandGestureState, SystemController
from gesture_control.detector import DetectedHand, HandDetector
from gesture_control.gestures import (
    FINGER_NAMES,
    FINGER_TIPS,
    BaseGesture,
    PinchGesture,
    PinchWheelGesture,
    SwipeGesture,
    is_exact_extended_pose,
    is_exact_pinch,
    is_finger_extended,
    is_palm_visible,
    is_pinch,
    normalize_fingers,
    pinch_group_max_distance,
)
from gesture_control.visualizer import Visualizer

__all__ = [
    "BaseAction",
    "BaseGesture",
    "BrightnessAction",
    "CommandAction",
    "DetectedHand",
    "FINGER_NAMES",
    "FINGER_TIPS",
    "HandDetector",
    "HandGestureState",
    "MediaNextAction",
    "MediaPlayPauseAction",
    "MediaPreviousAction",
    "PinchGesture",
    "PinchWheelGesture",
    "SwipeGesture",
    "SystemController",
    "Visualizer",
    "VolumeAction",
    "config",
    "create_default_actions",
    "is_exact_extended_pose",
    "is_exact_pinch",
    "is_finger_extended",
    "is_palm_visible",
    "is_pinch",
    "normalize_fingers",
    "pinch_group_max_distance",
]
