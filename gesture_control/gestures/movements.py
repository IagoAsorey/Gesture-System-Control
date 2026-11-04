"""Reusable movement trackers (static hold, rotary wheel, and 4-way swipe)."""

from dataclasses import dataclass
import math
import time
from typing import Optional

from gesture_control import config


@dataclass(slots=True)
class _HoldState:
    """Per-hand state for one-shot static pose/pinch triggers."""

    active_since: Optional[float] = None
    has_triggered: bool = False
    last_trigger_ts: float = 0.0


class HoldTriggerTracker:
    """Emits a one-shot event when a pose is held for `hold_sec` and requires release to re-arm."""

    def __init__(
        self,
        event_name: str,
        hold_sec: float = 0.0,
        cooldown_sec: float = config.POSE_COOLDOWN_SEC,
    ) -> None:
        self.event_name = event_name
        self.hold_sec = hold_sec
        self.cooldown_sec = cooldown_sec
        self._states: dict[str, _HoldState] = {
            "Right": _HoldState(),
            "Left": _HoldState(),
        }

    def reset(self, hand_label: str) -> None:
        """Resets hold state for the specified hand."""
        if state := self._states.get(hand_label):
            state.active_since = None
            state.has_triggered = False

    def evaluate(self, hand_label: str, is_active: bool) -> Optional[str]:
        """Evaluates hold duration and returns `event_name` once per activation."""
        state = self._states.get(hand_label)
        if state is None:
            return None

        if not is_active:
            state.active_since = None
            state.has_triggered = False
            return None

        now = time.monotonic()
        if state.active_since is None:
            state.active_since = now

        if state.has_triggered:
            return None

        if (now - state.active_since) < self.hold_sec:
            return None

        state.has_triggered = True
        if (now - state.last_trigger_ts) < self.cooldown_sec:
            return None

        state.last_trigger_ts = now
        return self.event_name


@dataclass(slots=True)
class _WheelState:
    """Per-hand state for rotary wheel tracking."""

    anchor_angle: Optional[float] = None
    last_trigger_ts: float = 0.0


class WheelMovementTracker:
    """Tracks angular rotation and emits '<prefix>_wheel_right' or '<prefix>_wheel_left'."""

    def __init__(
        self,
        prefix: str,
        angle_threshold: float = config.WHEEL_ANGLE_THRESHOLD,
        cooldown_sec: float = config.ACTION_COOLDOWN_SEC,
    ) -> None:
        self.prefix = prefix
        self.angle_threshold = angle_threshold
        self.cooldown_sec = cooldown_sec
        self._tracks: dict[str, _WheelState] = {
            "Right": _WheelState(),
            "Left": _WheelState(),
        }

    def reset(self, hand_label: str) -> None:
        """Resets angular anchor for the specified hand."""
        if track := self._tracks.get(hand_label):
            track.anchor_angle = None

    def evaluate(
        self, hand_label: str, is_active: bool, current_angle: float
    ) -> Optional[str]:
        """Evaluates angular displacement and returns '<prefix>_wheel_right', '<prefix>_wheel_left', or None."""
        track = self._tracks.get(hand_label)
        if track is None:
            return None

        if not is_active:
            track.anchor_angle = None
            return None

        if track.anchor_angle is None:
            track.anchor_angle = current_angle
            return None

        delta_angle = math.atan2(
            math.sin(current_angle - track.anchor_angle),
            math.cos(current_angle - track.anchor_angle),
        )
        if abs(delta_angle) < self.angle_threshold:
            return None

        now = time.monotonic()
        if (now - track.last_trigger_ts) < self.cooldown_sec:
            return None

        track.anchor_angle = current_angle
        track.last_trigger_ts = now
        direction = "right" if delta_angle > 0 else "left"
        return f"{self.prefix}_wheel_{direction}"


@dataclass(slots=True)
class _SwipeState:
    """Per-hand state for 2D anchor-based swipe tracking."""

    anchor_x: Optional[float] = None
    anchor_y: Optional[float] = None
    last_trigger_ts: float = 0.0


class SwipeMovementTracker:
    """Tracks 2D displacement and emits '<prefix>_swipe_up/down/left/right'."""

    def __init__(
        self,
        prefix: str,
        step_threshold: float = config.SWIPE_STEP_THRESHOLD,
        cooldown_sec: float = config.ACTION_COOLDOWN_SEC,
    ) -> None:
        self.prefix = prefix
        self.step_threshold = step_threshold
        self.cooldown_sec = cooldown_sec
        self._tracks: dict[str, _SwipeState] = {
            "Right": _SwipeState(),
            "Left": _SwipeState(),
        }

    def reset(self, hand_label: str) -> None:
        """Resets 2D swipe anchor for the specified hand."""
        if track := self._tracks.get(hand_label):
            track.anchor_x = None
            track.anchor_y = None

    def evaluate(
        self,
        hand_label: str,
        is_active: bool,
        current_x: float,
        current_y: float,
    ) -> Optional[str]:
        """Evaluates 2D displacement and returns '<prefix>_swipe_up/down/left/right' or None."""
        track = self._tracks.get(hand_label)
        if track is None:
            return None

        if not is_active:
            track.anchor_x = None
            track.anchor_y = None
            return None

        if track.anchor_x is None or track.anchor_y is None:
            track.anchor_x = current_x
            track.anchor_y = current_y
            return None

        # In the unflipped camera frame:
        # - Moving to the user's physical right decreases X -> delta_x > 0
        # - Moving upward decreases Y -> delta_y > 0
        delta_x = track.anchor_x - current_x
        delta_y = track.anchor_y - current_y

        if max(abs(delta_x), abs(delta_y)) < self.step_threshold:
            return None

        now = time.monotonic()
        if (now - track.last_trigger_ts) < self.cooldown_sec:
            return None

        track.anchor_x = current_x
        track.anchor_y = current_y
        track.last_trigger_ts = now

        if abs(delta_x) >= abs(delta_y):
            direction = "right" if delta_x > 0 else "left"
        else:
            direction = "up" if delta_y > 0 else "down"
        return f"{self.prefix}_swipe_{direction}"
