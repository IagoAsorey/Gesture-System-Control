"""Static hand pose evaluation helpers."""

import math
from typing import Any, Sequence

from gesture_control import config

# Canonical finger order and MediaPipe landmark indices
# Index 0: thumb, 1: index, 2: middle, 3: ring, 4: pinky
FINGER_NAMES: tuple[str, ...] = ("thumb", "index", "middle", "ring", "pinky")
FINGER_TIPS: dict[str, int] = {
    "thumb": 4,
    "index": 8,
    "middle": 12,
    "ring": 16,
    "pinky": 20,
}
FINGER_PIPS: dict[str, int] = {
    "index": 6,
    "middle": 10,
    "ring": 14,
    "pinky": 18,
}


def normalize_fingers(fingers: Any) -> tuple[str, ...]:
    """Validates and normalizes finger configuration into a canonical tuple.

    Supports:
      - Binary arrays/lists, e.g. [1, 1, 0, 0, 0] (thumb, index, middle, ring, pinky).
      - Sequence of names, e.g. ("thumb", "index") or ["thumb", "middle"].
    """
    if (
        isinstance(fingers, (list, tuple))
        and fingers
        and all(isinstance(x, (int, bool)) for x in fingers)
    ):
        if len(fingers) != 5:
            raise ValueError(
                f"Binary finger array must have exactly 5 elements [thumb, index, middle, ring, pinky], got {fingers}"
            )
        return tuple(name for name, active in zip(FINGER_NAMES, fingers) if active)

    cleaned = {str(f).strip().lower() for f in fingers}
    unknown = cleaned - FINGER_TIPS.keys()
    if unknown:
        raise ValueError(
            f"Unknown finger name(s): {sorted(unknown)}. "
            f"Valid fingers are: {list(FINGER_NAMES)}"
        )
    return tuple(f for f in FINGER_NAMES if f in cleaned)


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


def is_finger_extended(
    hand_landmarks: Sequence, hand_label: str, finger_name: str
) -> bool:
    """Returns True if the specified finger is extended outward."""
    if finger_name == "thumb":
        thumb_tip_x = hand_landmarks[4].x
        thumb_ip_x = hand_landmarks[3].x
        return (
            thumb_tip_x > thumb_ip_x
            if hand_label == "Right"
            else thumb_tip_x < thumb_ip_x
        )

    tip_idx = FINGER_TIPS[finger_name]
    pip_idx = FINGER_PIPS[finger_name]
    return hand_landmarks[tip_idx].y < hand_landmarks[pip_idx].y


def is_exact_extended_pose(
    hand_landmarks: Sequence,
    hand_label: str,
    fingers: Any = (0, 1, 0, 0, 0),
) -> bool:
    """Returns True if the palm faces the camera and ONLY the specified fingers are extended."""
    if not is_palm_visible(hand_landmarks, hand_label):
        return False

    selected = set(normalize_fingers(fingers))
    for name in FINGER_NAMES:
        is_ext = is_finger_extended(hand_landmarks, hand_label, name)
        if name in selected and not is_ext:
            return False
        if name not in selected and is_ext:
            return False
    return True


def pinch_group_max_distance(
    hand_landmarks: Sequence,
    fingers: Any = ("thumb", "index"),
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
    fingers: Any = ("thumb", "index"),
    distance_threshold: float = config.PINCH_DISTANCE_THRESHOLD,
) -> bool:
    """Returns True if and only if the exact specified fingers are pinched together.

    All fingers in `fingers` must be within `distance_threshold` of the reference finger,
    and every non-selected finger must stay separated from all pinched fingers.
    """
    if not is_palm_visible(hand_landmarks, hand_label):
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
    excluded = [f for f in FINGER_NAMES if f not in selected]
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
    fingers: Any = ("thumb", "index"),
) -> bool:
    """Returns True if the specified fingers form an exact pinch."""
    return is_exact_pinch(
        hand_landmarks=hand_landmarks,
        hand_label=hand_label,
        fingers=fingers,
        distance_threshold=distance_threshold,
    )
