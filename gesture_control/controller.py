"""System controller module that routes detected hand gestures to modular OS actions."""

from dataclasses import dataclass
import time
from typing import Optional, Sequence

from gesture_control import config
from gesture_control.actions import BaseAction, create_default_actions
from gesture_control.detector import DetectedHand
from gesture_control.gestures import BaseGesture, FistVerticalGesture


@dataclass(slots=True)
class HandGestureState:
    """Tracks HUD feedback state for a specific hand."""

    last_action_text: str = ""
    last_action_color: tuple[int, int, int] = (0, 255, 0)
    last_action_ts: float = 0.0


class SystemController:
    """Evaluates modular gestures and dispatches mapped system actions."""

    def __init__(
        self,
        step_threshold: float = config.MOVEMENT_STEP_THRESHOLD,
        cooldown_sec: float = config.ACTION_COOLDOWN_SEC,
        volume_step: int = config.VOLUME_STEP,
        brightness_step: int = config.BRIGHTNESS_STEP,
        gestures: Optional[Sequence[BaseGesture]] = None,
        actions: Optional[dict[str, BaseAction]] = None,
        bindings: Optional[dict[str, dict[str, str]]] = None,
    ) -> None:
        self._fist_gesture = FistVerticalGesture(
            step_threshold=step_threshold,
            cooldown_sec=cooldown_sec,
        )
        self.gestures: list[BaseGesture] = (
            list(gestures) if gestures is not None else [self._fist_gesture]
        )
        self.actions: dict[str, BaseAction] = (
            dict(actions)
            if actions is not None
            else create_default_actions(
                volume_step=volume_step,
                brightness_step=brightness_step,
            )
        )
        source_bindings = bindings if bindings is not None else config.GESTURE_BINDINGS
        self.bindings: dict[str, dict[str, str]] = {
            hand: dict(hand_map) for hand, hand_map in source_bindings.items()
        }

        self.states: dict[str, HandGestureState] = {
            "Right": HandGestureState(),
            "Left": HandGestureState(),
        }

    def bind(self, hand_label: str, gesture_name: str, action_name: str) -> None:
        """Assigns or updates the action triggered by a gesture on a given hand."""
        self.bindings.setdefault(hand_label, {})[gesture_name] = action_name

    def reset_hand(self, hand_label: str) -> None:
        """Resets gesture tracking state when a hand leaves the camera frame."""
        for gesture in self.gestures:
            gesture.reset(hand_label)

    def process_hand(self, hand: DetectedHand) -> Optional[str]:
        """Evaluates all registered gestures for a detected hand and runs bound actions."""
        any_pose_active = False
        triggered_label: Optional[str] = None

        for gesture in self.gestures:
            is_active, gesture_name = gesture.update(hand)
            if is_active:
                any_pose_active = True
            if gesture_name is not None:
                action_label = self.trigger_gesture(hand.label, gesture_name)
                if action_label is not None:
                    triggered_label = action_label

        hand.is_gesture_active = any_pose_active
        return triggered_label

    def process_hand_gesture(
        self, hand_label: str, is_gesture_active: bool, current_y: float
    ) -> Optional[str]:
        """Evaluates vertical wrist movement and triggers the bound action."""
        gesture_name = self._fist_gesture.evaluate(
            hand_label=hand_label,
            is_active=is_gesture_active,
            current_y=current_y,
        )
        if gesture_name is None:
            return None
        return self.trigger_gesture(hand_label, gesture_name)

    def trigger_gesture(self, hand_label: str, gesture_name: str) -> Optional[str]:
        """Resolves the action mapped to (hand_label, gesture_name) and executes it."""
        action_name = self.bindings.get(hand_label, {}).get(gesture_name)
        if action_name is None:
            action_name = self.bindings.get("Any", {}).get(gesture_name)
        if action_name is None:
            return None

        action = self.actions.get(action_name)
        if action is None:
            return None

        action_text = action.execute()
        if state := self.states.get(hand_label):
            state.last_action_text = action_text
            state.last_action_color = action.color
            state.last_action_ts = time.monotonic()

        return action_text
