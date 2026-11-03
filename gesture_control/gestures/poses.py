"""Static hand pose evaluation helpers."""

import math
from typing import Sequence

from gesture_control import config

# Canonical finger order and MediaPipe fingertip landmark indices
_FINGER_ORDER = ("thumb", "index", "middle", "ring", "pinky")
FINGER_TIPS: dict[str, int] = {
    "thumb": 4,
    "index": 8,
    "middle": 12,
    "ring": 16,
    "pinky": 20,
}

# Landmark indices for the 4 non-thumb fingertips and their corresponding PIP joints
_FINGER_TIPS = (8, 12, 16, 20)
_FINGER_PIPS = (6, 10, 14, 18)


def normalize_fingers(fingers: Sequence[str]) -> tuple[str, ...]:
    """Validates and normalizes a sequence of finger names into a canonical tuple."""
    cleaned = {f.strip().lower() for f in fingers}
    unknown = cleaned - FINGER_TIPS.keys()
    if unknown:
        raise ValueError(
            f"Unknown finger name(s): {sorted(unknown)}. "
            f"Valid fingers are: {list(_FINGER_ORDER)}"
        )
    return tuple(f for f in _FINGER_ORDER if f in cleaned)


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


def pinch_group_max_distance(
    hand_landmarks: Sequence,
    fingers: Sequence[str] = ("thumb", "index"),
) -> float:
    """Returns the maximum 2D distance between the reference finger and all other selected fingers."""
    selected = normalize_fingers(fingers)
    if len(selected) < 2:
        return 0.0

    ref_name = "thumb" if "thumb" in selected else selected[0]
    ref_pt = hand_landmarks[FINGER_TIPS[ref_name]]
    return max(
        math.hypot(
            ref_pt.x - hand_landmarks[FINGER_TIPS[f]].x,
            ref_pt.y - hand_landmarks[FINGER_TIPS[f]].y,
        )
        for f in selected
        if f != ref_name
    )


def pinch_distance(hand_landmarks: Sequence) -> float:
    """Returns the normalized 2D distance between the thumb tip and index fingertip."""
    return pinch_group_max_distance(hand_landmarks, ("thumb", "index"))


def is_exact_pinch(
    hand_landmarks: Sequence,
    hand_label: str,
    fingers: Sequence[str] = ("thumb", "index"),
    distance_threshold: float = config.PINCH_DISTANCE_THRESHOLD,
) -> bool:
    """Returns True if and only if the exact specified fingers are pinched together.

    All fingers in `fingers` must be within `distance_threshold` of the reference finger,
    and every non-selected finger must stay separated from all pinched fingers.
    """
    if not is_palm_visible(hand_landmarks, hand_label):
        return False

    if is_palm_fist(hand_landmarks, hand_label):
        return False

    selected = normalize_fingers(fingers)
    if len(selected) < 2:
        return False

    ref_name = "thumb" if "thumb" in selected else selected[0]
    ref_pt = hand_landmarks[FINGER_TIPS[ref_name]]
    other_selected = [f for f in selected if f != ref_name]

    # 1. Inclusion check: all required fingers must touch the reference finger
    for f in other_selected:
        pt = hand_landmarks[FINGER_TIPS[f]]
        if math.hypot(ref_pt.x - pt.x, ref_pt.y - pt.y) > distance_threshold:
            return False

    # 2. Strict exclusion check: no unselected finger may join the pinch cluster
    excluded = [f for f in _FINGER_ORDER if f not in selected]
    exclusion_ref_threshold = distance_threshold * 1.25
    for g in excluded:
        g_pt = hand_landmarks[FINGER_TIPS[g]]
        if math.hypot(ref_pt.x - g_pt.x, ref_pt.y - g_pt.y) <= exclusion_ref_threshold:
            return False
        for f in other_selected:
            f_pt = hand_landmarks[FINGER_TIPS[f]]
            if math.hypot(f_pt.x - g_pt.x, f_pt.y - g_pt.y) <= distance_threshold:
                return False

    return True


def is_pinch(
    hand_landmarks: Sequence,
    hand_label: str,
    distance_threshold: float = config.PINCH_DISTANCE_THRESHOLD,
    fingers: Sequence[str] = ("thumb", "index"),
) -> bool:
    """Returns True if the specified fingers form an exact pinch."""
    return is_exact_pinch(
        hand_landmarks=hand_landmarks,
        hand_label=hand_label,
        fingers=fingers,
        distance_threshold=distance_threshold,
    )
