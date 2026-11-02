"""Display brightness actions."""

from gesture_control import config
from gesture_control.actions.base import CommandAction


class BrightnessAction(CommandAction):
    """Adjusts display brightness via omarchy-brightness-display."""

    def __init__(self, increase: bool, step: int = config.BRIGHTNESS_STEP) -> None:
        arg = f"+{step}%" if increase else f"{step}%-"
        label = "BRIGHTNESS +" if increase else "BRIGHTNESS -"
        color = (0, 255, 0) if increase else (0, 0, 255)
        super().__init__(
            binary_name="omarchy-brightness-display",
            args=[arg],
            label=label,
            color=color,
        )
