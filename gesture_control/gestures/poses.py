"""Static hand pose evaluation helpers."""

from typing import Sequence

# Landmark indices for the 4 non-thumb fingertips and their corresponding PIP joints
_FINGER_TIPS = (8, 12, 16, 20)
_FINGER_PIPS = (6, 10, 14, 18)


def is_palm_fist(hand_landmarks: Sequence, hand_label: str) -> bool:
    """Returns True if the palm faces the camera and the fingers form a closed fist."""
    index_mcp_x = hand_landmarks[5].x
    pinky_mcp_x = hand_landmarks[17].x

    # In an unflipped camera frame, when the palm faces the camera:
    # - Physical Right hand: index MCP is to the right of pinky MCP (index_mcp_x > pinky_mcp_x)
    # - Physical Left hand: pinky MCP is to the right of index MCP (pinky_mcp_x > index_mcp_x)
    is_palm_visible = (
        index_mcp_x > pinky_mcp_x
        if hand_label == "Right"
        else pinky_mcp_x > index_mcp_x
    )
    if not is_palm_visible:
        return False

    # Check that all 4 fingers (index, middle, ring, pinky) are folded down
    return all(
        hand_landmarks[tip].y > hand_landmarks[pip].y
        for tip, pip in zip(_FINGER_TIPS, _FINGER_PIPS)
    )
