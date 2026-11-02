"""Modular system actions package."""

from gesture_control import config
from gesture_control.actions.base import BaseAction, CommandAction
from gesture_control.actions.brightness import BrightnessAction
from gesture_control.actions.volume import VolumeAction


def create_default_actions(
    volume_step: int = config.VOLUME_STEP,
    brightness_step: int = config.BRIGHTNESS_STEP,
) -> dict[str, BaseAction]:
    """Creates the default registry of available system actions."""
    return {
        "volume_up": VolumeAction(increase=True, step=volume_step),
        "volume_down": VolumeAction(increase=False, step=volume_step),
        "brightness_up": BrightnessAction(increase=True, step=brightness_step),
        "brightness_down": BrightnessAction(increase=False, step=brightness_step),
    }


__all__ = [
    "BaseAction",
    "BrightnessAction",
    "CommandAction",
    "VolumeAction",
    "create_default_actions",
]
