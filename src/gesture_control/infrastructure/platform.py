import platform
import subprocess
import sys
from abc import ABC, abstractmethod

import screen_brightness_control as sbc

from gesture_control.domain.protocols import BrightnessControl, VolumeControl


class VolumeControlBase(ABC):
    @abstractmethod
    def volume_up(self, step: int) -> bool:
        pass

    @abstractmethod
    def volume_down(self, step: int) -> bool:
        pass


class WindowsVolumeControl(VolumeControlBase):
    def __init__(self):
        import pyautogui

        self._pyautogui = pyautogui

    def volume_up(self, step: int) -> bool:
        try:
            self._pyautogui.press("volumeup", presses=step // 5 or 1)
            return True
        except Exception:
            return False

    def volume_down(self, step: int) -> bool:
        try:
            self._pyautogui.press("volumedown", presses=step // 5 or 1)
            return True
        except Exception:
            return False


class LinuxVolumeControl(VolumeControlBase):
    def __init__(self, method: str = "wpctl"):
        self._method = method

    def _run(self, cmd: list[str]) -> bool:
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def volume_up(self, step: int) -> bool:
        if self._method == "wpctl":
            return self._run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{step}%+"])
        elif self._method == "pactl":
            return self._run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"+{step}%"])
        elif self._method == "amixer":
            return self._run(["amixer", "-D", "pulse", "sset", "Master", f"{step}%+"])
        return False

    def volume_down(self, step: int) -> bool:
        if self._method == "wpctl":
            return self._run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{step}%-"])
        elif self._method == "pactl":
            return self._run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"-{step}%"])
        elif self._method == "amixer":
            return self._run(["amixer", "-D", "pulse", "sset", "Master", f"{step}%-"])
        return False


class SBCBrightnessControl:
    def brightness_up(self, step: int) -> bool:
        try:
            current = sbc.get_brightness(display=0)
            if isinstance(current, list):
                current = current[0]
            sbc.set_brightness(min(100, current + step), display=0)
            return True
        except Exception:
            return False

    def brightness_down(self, step: int) -> bool:
        try:
            current = sbc.get_brightness(display=0)
            if isinstance(current, list):
                current = current[0]
            sbc.set_brightness(max(0, current - step), display=0)
            return True
        except Exception:
            return False


def create_volume_control(method: str | None = None) -> VolumeControl:
    system = platform.system().lower()
    if system == "windows":
        return WindowsVolumeControl()
    elif system == "linux":
        return LinuxVolumeControl(method or "wpctl")
    else:
        raise RuntimeError(f"Unsupported platform: {system}")


def create_brightness_control() -> BrightnessControl:
    return SBCBrightnessControl()


def get_platform_info() -> dict:
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "python": sys.version,
    }