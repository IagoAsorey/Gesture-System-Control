"""System audio volume actions."""

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
