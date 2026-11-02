"""System controller module for Linux (Omarchy / Wayland) volume and brightness actions."""

from dataclasses import dataclass
import shutil
import subprocess
import time
from typing import Optional

from gesture_control import config


@dataclass
class HandGestureState:
    """Tracks continuous vertical drag state and HUD feedback for a specific hand."""

    is_active: bool = False
    anchor_y: Optional[float] = None
    last_trigger_ts: float = 0.0
    last_action_text: str = ""
    last_action_color: tuple[int, int, int] = (0, 255, 0)
    last_action_ts: float = 0.0


class SystemController:
    """Manages gesture state evaluation and dispatches OS volume/brightness commands."""

    def __init__(
        self,
        step_threshold: float = config.MOVEMENT_STEP_THRESHOLD,
        cooldown_sec: float = config.ACTION_COOLDOWN_SEC,
        volume_step: int = config.VOLUME_STEP,
        brightness_step: int = config.BRIGHTNESS_STEP,
    ) -> None:
        self.step_threshold = step_threshold
        self.cooldown_sec = cooldown_sec
        self.volume_step = volume_step
        self.brightness_step = brightness_step

        self.states: dict[str, HandGestureState] = {
            "Right": HandGestureState(),
            "Left": HandGestureState(),
        }

        # Resolve native Omarchy CLI utilities
        self.volume_cmd = shutil.which("omarchy-audio-output-volume")
        self.brightness_cmd = shutil.which("omarchy-brightness-display")

    def reset_hand(self, hand_label: str) -> None:
        """Resets vertical drag tracking when a hand opens or leaves the camera frame."""
        if hand_label in self.states:
            state = self.states[hand_label]
            state.is_active = False
            state.anchor_y = None

    def process_hand_gesture(
        self, hand_label: str, is_gesture_active: bool, current_y: float
    ) -> Optional[str]:
        """Evaluates vertical wrist movement while the closed-fist gesture is active.

        Args:
            hand_label: "Right" (Volume) or "Left" (Brightness).
            is_gesture_active: True if the palm faces the camera and the fist is closed.
            current_y: Normalized vertical coordinate (0.0 top, 1.0 bottom) of the wrist.

        Returns:
            Action label executed (e.g., "VOLUME +") or None if no step was triggered.
        """
        state = self.states.get(hand_label)
        if state is None:
            return None

        if not is_gesture_active:
            self.reset_hand(hand_label)
            return None

        now = time.monotonic()

        # First frame with a closed fist: set the vertical anchor without firing an action
        if not state.is_active or state.anchor_y is None:
            state.is_active = True
            state.anchor_y = current_y
            return None

        # Positive delta means the hand moved upward (Y decreases toward top of frame)
        delta_y = state.anchor_y - current_y

        if abs(delta_y) < self.step_threshold:
            return None

        # Enforce cooldown so the OS / OSD is not flooded
        if (now - state.last_trigger_ts) < self.cooldown_sec:
            return None

        increase = delta_y > 0
        # Shift the anchor to the current position to require another full step movement
        state.anchor_y = current_y
        state.last_trigger_ts = now

        if hand_label == "Right":
            self.adjust_volume(increase=increase)
            action_text = "VOLUME +" if increase else "VOLUME -"
        else:
            self.adjust_brightness(increase=increase)
            action_text = "BRIGHTNESS +" if increase else "BRIGHTNESS -"

        state.last_action_text = action_text
        state.last_action_color = (0, 255, 0) if increase else (0, 0, 255)
        state.last_action_ts = now
        return action_text

    def adjust_volume(self, increase: bool) -> None:
        """Increases or decreases system audio volume via omarchy-audio-output-volume."""
        if not self.volume_cmd:
            return
        arg = f"+{self.volume_step}" if increase else f"-{self.volume_step}"
        self._run_async([self.volume_cmd, arg])

    def adjust_brightness(self, increase: bool) -> None:
        """Increases or decreases display brightness via omarchy-brightness-display."""
        if not self.brightness_cmd:
            return
        arg = f"+{self.brightness_step}%" if increase else f"{self.brightness_step}%-"
        self._run_async([self.brightness_cmd, arg])

    @staticmethod
    def _run_async(command: list[str]) -> None:
        """Spawns a system command asynchronously without blocking the video capture loop."""
        try:
            subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            pass
