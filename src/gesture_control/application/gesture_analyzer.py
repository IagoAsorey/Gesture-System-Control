from gesture_control.domain.entities import Hand
from gesture_control.domain.enums import GestureType, HandLabel, PalmState


class GestureAnalyzer:
    def __init__(self, movement_threshold: float, palm_required: bool):
        self._threshold = movement_threshold
        self._palm_required = palm_required
        self._prev_wrist_y: dict[HandLabel, float | None] = {
            HandLabel.LEFT: None,
            HandLabel.RIGHT: None,
        }

    def analyze(self, hand: Hand) -> GestureType:
        if self._palm_required and hand.palm_state != PalmState.VISIBLE:
            self._prev_wrist_y[hand.label] = hand.wrist_y
            return GestureType.NONE

        if not hand.is_fist:
            self._prev_wrist_y[hand.label] = hand.wrist_y
            return GestureType.NONE

        prev_y = self._prev_wrist_y[hand.label]
        self._prev_wrist_y[hand.label] = hand.wrist_y

        if prev_y is None:
            return GestureType.NONE

        diff = prev_y - hand.wrist_y

        if abs(diff) < self._threshold:
            return GestureType.NONE

        if diff > 0:
            return (
                GestureType.VOLUME_UP
                if hand.label == HandLabel.RIGHT
                else GestureType.BRIGHTNESS_UP
            )
        else:
            return (
                GestureType.VOLUME_DOWN
                if hand.label == HandLabel.RIGHT
                else GestureType.BRIGHTNESS_DOWN
            )

    def reset(self) -> None:
        self._prev_wrist_y = {HandLabel.LEFT: None, HandLabel.RIGHT: None}