from gesture_control.domain.enums import GestureType
from gesture_control.domain.protocols import BrightnessControl, VolumeControl


class ActionExecutor:
    def __init__(
        self,
        volume_control: VolumeControl,
        brightness_control: BrightnessControl,
        volume_step: int,
        brightness_step: int,
    ):
        self._volume = volume_control
        self._brightness = brightness_control
        self._volume_step = volume_step
        self._brightness_step = brightness_step

    def execute(self, gesture: GestureType) -> tuple[bool, str | None]:
        if gesture == GestureType.VOLUME_UP:
            ok = self._volume.volume_up(self._volume_step)
            return ok, "VOLUMEN +"
        elif gesture == GestureType.VOLUME_DOWN:
            ok = self._volume.volume_down(self._volume_step)
            return ok, "VOLUMEN -"
        elif gesture == GestureType.BRIGHTNESS_UP:
            ok = self._brightness.brightness_up(self._brightness_step)
            return ok, "BRILLO +"
        elif gesture == GestureType.BRIGHTNESS_DOWN:
            ok = self._brightness.brightness_down(self._brightness_step)
            return ok, "BRILLO -"
        return False, None