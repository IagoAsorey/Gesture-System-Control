"""System controller module that routes detected hand gestures to modular OS actions."""

from dataclasses import dataclass
import time
from typing import Any, Optional, Sequence

from gesture_control import config
from gesture_control.actions import BaseAction, create_default_actions
from gesture_control.detector import DetectedHand
from gesture_control.gestures import (
    BaseGesture,
    PinchGesture,
    PinchWheelGesture,
    SwipeGesture,
    normalize_fingers,
)

_SWIPE_GESTURE_NAMES = ("swipe_up", "swipe_down", "swipe_left", "swipe_right")
_WHEEL_GESTURE_NAMES = ("pinch_wheel_right", "pinch_wheel_left")


def _normalize_hand_rules(rules: Any) -> list[dict[str, Any]]:
    """Normalizes a hand's binding configuration into a list of rule dicts."""
    if isinstance(rules, dict):
        return [
            {"gesture": str(k), "action": str(v), "fingers": None}
            for k, v in rules.items()
        ]

    normalized: list[dict[str, Any]] = []
    for rule in rules:
        raw_fingers = rule.get("fingers")
        fingers = normalize_fingers(raw_fingers) if raw_fingers is not None else None
        normalized.append(
            {
                "gesture": str(rule["gesture"]),
                "action": str(rule["action"]),
                "fingers": fingers,
            }
        )
    return normalized


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
        step_threshold: float = config.SWIPE_STEP_THRESHOLD,
        cooldown_sec: float = config.ACTION_COOLDOWN_SEC,
        volume_step: int = config.VOLUME_STEP,
        brightness_step: int = config.BRIGHTNESS_STEP,
        gestures: Optional[Sequence[BaseGesture]] = None,
        actions: Optional[dict[str, BaseAction]] = None,
        bindings: Optional[dict[str, Any]] = None,
    ) -> None:
        self._step_threshold = step_threshold
        self._cooldown_sec = cooldown_sec

        source_bindings = bindings if bindings is not None else config.GESTURE_BINDINGS
        self.bindings: dict[str, list[dict[str, Any]]] = {
            hand: _normalize_hand_rules(hand_rules)
            for hand, hand_rules in source_bindings.items()
        }

        self._custom_gestures = gestures is not None
        self.gestures: list[BaseGesture] = (
            list(gestures)
            if gestures is not None
            else self._build_gestures_from_bindings()
        )
        self.actions: dict[str, BaseAction] = (
            dict(actions)
            if actions is not None
            else create_default_actions(
                volume_step=volume_step,
                brightness_step=brightness_step,
            )
        )

        self.states: dict[str, HandGestureState] = {
            "Right": HandGestureState(),
            "Left": HandGestureState(),
        }

    def _build_gestures_from_bindings(self) -> list[BaseGesture]:
        """Instantiates gesture recognizers for all gestures and finger combinations in self.bindings."""
        recognizers: list[BaseGesture] = []
        swipe_finger_sets: list[tuple[str, ...]] = []
        wheel_finger_sets: list[tuple[str, ...]] = []
        pinch_finger_sets: list[tuple[str, ...]] = []

        for rules in self.bindings.values():
            for rule in rules:
                g_name = rule["gesture"]
                fingers = rule.get("fingers")
                if g_name in _SWIPE_GESTURE_NAMES:
                    f_set = fingers if fingers is not None else ("index",)
                    if f_set not in swipe_finger_sets:
                        swipe_finger_sets.append(f_set)
                elif g_name in _WHEEL_GESTURE_NAMES:
                    f_set = fingers if fingers is not None else ("thumb", "index", "middle")
                    if f_set not in wheel_finger_sets:
                        wheel_finger_sets.append(f_set)
                elif g_name == "pinch":
                    f_set = fingers if fingers is not None else ("thumb", "index")
                    if f_set not in pinch_finger_sets:
                        pinch_finger_sets.append(f_set)

        for f_set in swipe_finger_sets:
            recognizers.append(
                SwipeGesture(
                    fingers=f_set,
                    step_threshold=self._step_threshold,
                    cooldown_sec=self._cooldown_sec,
                )
            )
        for f_set in wheel_finger_sets:
            recognizers.append(
                PinchWheelGesture(fingers=f_set, cooldown_sec=self._cooldown_sec)
            )
        for f_set in pinch_finger_sets:
            recognizers.append(PinchGesture(fingers=f_set))

        return recognizers

    def bind(
        self,
        hand_label: str,
        gesture_name: str,
        action_name: str,
        fingers: Optional[Any] = None,
    ) -> None:
        """Assigns or updates the action triggered by a gesture (and optional finger set) on a hand."""
        norm_fingers = normalize_fingers(fingers) if fingers is not None else None
        hand_rules = self.bindings.setdefault(hand_label, [])

        for rule in hand_rules:
            if rule["gesture"] == gesture_name and (
                norm_fingers is None or rule.get("fingers") == norm_fingers
            ):
                rule["action"] = action_name
                if norm_fingers is not None:
                    rule["fingers"] = norm_fingers
                break
        else:
            hand_rules.append(
                {
                    "gesture": gesture_name,
                    "action": action_name,
                    "fingers": norm_fingers,
                }
            )

        if not self._custom_gestures:
            self.gestures = self._build_gestures_from_bindings()

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
                gesture_fingers = getattr(gesture, "fingers", None)
                action_label = self.trigger_gesture(
                    hand.label, gesture_name, fingers=gesture_fingers
                )
                if action_label is not None:
                    triggered_label = action_label

        hand.is_gesture_active = any_pose_active
        return triggered_label

    def _resolve_action_name(
        self,
        hand_label: str,
        gesture_name: str,
        fingers: Optional[tuple[str, ...]] = None,
    ) -> Optional[str]:
        """Looks up the action name matching (hand_label, gesture_name, fingers)."""
        for target_hand in (hand_label, "Any"):
            for rule in self.bindings.get(target_hand, []):
                if rule["gesture"] != gesture_name:
                    continue
                rule_fingers = rule.get("fingers")
                if rule_fingers is None or fingers is None or rule_fingers == fingers:
                    return rule["action"]
        return None

    def trigger_gesture(
        self,
        hand_label: str,
        gesture_name: str,
        fingers: Optional[Any] = None,
    ) -> Optional[str]:
        """Resolves the action mapped to (hand_label, gesture_name, fingers) and executes it."""
        norm_fingers = (
            normalize_fingers(fingers)
            if fingers is not None and not isinstance(fingers, tuple)
            else fingers
        )
        action_name = self._resolve_action_name(hand_label, gesture_name, norm_fingers)
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
