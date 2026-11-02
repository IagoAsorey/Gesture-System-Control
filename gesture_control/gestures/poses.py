"""Static hand pose evaluation helpers."""

import math
from typing import Sequence

from gesture_control import config

# Landmark indices for thumb and fingertips/PIP joints
_THUMB_TIP = 4
_INDEX_TIP = 8
_MIDDLE_TIP = 12
_FINGER_TIPS = (8, 12, 16, 20)
_FINGER_PIPS = (6, 10, 14, 18)
_OTHER_FINGER_TIPS = (12, 16, 20)
_OTHER_FINGER_PIPS = (10, 14, 18)


def is_palm_visible(hand_landmarks: Sequence, hand_label: str) -> bool:
    """Returns True if the palm of the given hand is facing the camera."""
    index_mcp_x = hand_landmarks[5].x
    pinky_mcp_x = hand_landmarks[17].x

    # In an unflipped camera frame, when the palm faces the camera:
    # - Physical Right hand: index MCP is to the right of pinky MCP (index_mcp_x > pinky_mcp_x)
    # - Physical Left hand: pinky MCP is to the right of index MCP (pinky_mcp_x > index_mcp_x)
    return (
        index_mcp_x > pinky_mcp_x
        if hand_label == "Right"
        else pinky_mcp_x > index_mcp_x
    )


def is_palm_fist(hand_landmarks: Sequence, hand_label: str) -> bool:
    """Returns True if the palm faces the camera and the fingers form a closed fist."""
    if not is_palm_visible(hand_landmarks, hand_label):
        return False

    # Check that all 4 fingers (index, middle, ring, pinky) are folded down
    return all(
        hand_landmarks[tip].y > hand_landmarks[pip].y
        for tip, pip in zip(_FINGER_TIPS, _FINGER_PIPS)
    )


def pinch_distance(hand_landmarks: Sequence) -> float:
    """Returns the normalized 2D distance between the thumb tip and index fingertip."""
    thumb_tip = hand_landmarks[_THUMB_TIP]
    index_tip = hand_landmarks[_INDEX_TIP]
    return math.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)


def is_three_finger_pinch(
    hand_landmarks: Sequence,
    hand_label: str,
    distance_threshold: float = config.WHEEL_DISTANCE_THRESHOLD,
) -> bool:
    """Returns True when thumb, index, and middle fingertips are pinched together."""
    if not is_palm_visible(hand_landmarks, hand_label):
        return False

    if is_palm_fist(hand_landmarks, hand_label):
        return False

    thumb = hand_landmarks[_THUMB_TIP]
    index = hand_landmarks[_INDEX_TIP]
    middle = hand_landmarks[_MIDDLE_TIP]

    dist_index = math.hypot(thumb.x - index.x, thumb.y - index.y)
    dist_middle = math.hypot(thumb.x - middle.x, thumb.y - middle.y)
    return dist_index <= distance_threshold and dist_middle <= distance_threshold


def is_pinch(
    hand_landmarks: Sequence,
    hand_label: str,
    distance_threshold: float = config.PINCH_DISTANCE_THRESHOLD,
) -> bool:
    """Returns True if only the thumb and index fingertips touch (2-finger pinch)."""
    if not is_palm_visible(hand_landmarks, hand_label):
        return False

    # Ensure at least one of the remaining fingers (middle, ring, pinky) is extended
    # so that a closed fist does not accidentally trigger a pinch
    has_extended_other_finger = any(
        hand_landmarks[tip].y < hand_landmarks[pip].y
        for tip, pip in zip(_OTHER_FINGER_TIPS, _OTHER_FINGER_PIPS)
    )
    if not has_extended_other_finger:
        return False

    # Exclude 3-finger wheel grip: middle finger must stay separated from thumb and index
    thumb = hand_landmarks[_THUMB_TIP]
    index = hand_landmarks[_INDEX_TIP]
    middle = hand_landmarks[_MIDDLE_TIP]
    if math.hypot(thumb.x - middle.x, thumb.y - middle.y) <= config.WHEEL_DISTANCE_THRESHOLD * 1.2:
        return False
    if math.hypot(index.x - middle.x, index.y - middle.y) <= distance_threshold:
        return False

    return pinch_distance(hand_landmarks) <= distance_threshold
