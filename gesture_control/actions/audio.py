"""Audio and media actions (volume and playback control)."""

from gesture_control import config
from gesture_control.actions.base import CommandAction


class VolumeAction(CommandAction):
    """Adjusts system audio output volume via omarchy-audio-output-volume."""

    def __init__(self, increase: bool, step: int = config.VOLUME_STEP) -> None:
        arg = f"+{step}" if increase else f"-{step}"
        label = "VOLUME +" if increase else "VOLUME -"
        color = (0, 255, 0) if increase else (0, 0, 255)
        super().__init__(
            binary_name="omarchy-audio-output-volume",
            args=[arg],
            label=label,
            color=color,
        )


class MediaPlayPauseAction(CommandAction):
    """Toggles media playback (Play/Pause) via omarchy-shell media playPause."""

    def __init__(self) -> None:
        super().__init__(
            binary_name="omarchy-shell",
            args=["media", "playPause"],
            label="PLAY / PAUSE",
            color=(255, 200, 0),
        )


class MediaNextAction(CommandAction):
    """Skips to the next media track/video via omarchy-shell media next."""

    def __init__(self) -> None:
        super().__init__(
            binary_name="omarchy-shell",
            args=["media", "next"],
            label="NEXT TRACK",
            color=(255, 200, 0),
        )


class MediaPreviousAction(CommandAction):
    """Returns to the previous media track/video via omarchy-shell media previous."""

    def __init__(self) -> None:
        super().__init__(
            binary_name="omarchy-shell",
            args=["media", "previous"],
            label="PREV TRACK",
            color=(255, 200, 0),
        )
