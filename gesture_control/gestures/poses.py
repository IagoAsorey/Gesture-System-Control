"""Static hand pose evaluation and geometry helpers."""

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

_WRIST = 0
_MIDDLE_MCP = 9


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
    pinch_exclusion_threshold: float = config.PINCH_DISTANCE_THRESHOLD,
) -> bool:
    """Returns True if the palm faces the camera, ONLY the specified fingers are extended,
    and no fingers are pinched against the thumb.
    """
    if not is_palm_visible(hand_landmarks, hand_label):
        return False

    # Exclude active pinches so 'pose' and 'pinch' families never conflict
    thumb_pt = hand_landmarks[FINGER_TIPS["thumb"]]
    for f_name in ("index", "middle", "ring", "pinky"):
        pt = hand_landmarks[FINGER_TIPS[f_name]]
        if math.hypot(thumb_pt.x - pt.x, thumb_pt.y - pt.y) <= pinch_exclusion_threshold:
            return False

    selected = set(normalize_fingers(fingers))
    for name in FINGER_NAMES:
        is_ext = is_finger_extended(hand_landmarks, hand_label, name)
        if name in selected and not is_ext:
            return False
        if name not in selected and is_ext:
            return False
    return True


def compute_group_angle(
    hand_landmarks: Sequence, fingers: Sequence[str]
) -> float:
    """Computes the rotation angle (in radians) of the active fingers relative to the wrist.

    Angle increases when rotating clockwise (to the right) from the user's perspective,
    and decreases when rotating counter-clockwise (to the left).
    """
    wrist = hand_landmarks[_WRIST]
    if fingers:
        indices = [FINGER_TIPS[f] for f in fingers]
        target_x = sum(hand_landmarks[i].x for i in indices) / len(indices)
        target_y = sum(hand_landmarks[i].y for i in indices) / len(indices)
    else:
        # Fallback for 0 extended fingers ([0, 0, 0, 0, 0] closed fist): use middle MCP
        knuckle = hand_landmarks[_MIDDLE_MCP]
        target_x = knuckle.x
        target_y = knuckle.y

    # In the unflipped camera frame, user's physical right corresponds to smaller X
    dx = wrist.x - target_x
    dy = target_y - wrist.y
    return math.atan2(dy, dx)


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
