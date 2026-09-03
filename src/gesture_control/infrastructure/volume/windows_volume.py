import pyautogui


class WindowsVolumeControl:
    def volume_up(self, step: int) -> bool:
        try:
            pyautogui.press("volumeup", presses=max(1, step // 5))
            return True
        except Exception:
            return False

    def volume_down(self, step: int) -> bool:
        try:
            pyautogui.press("volumedown", presses=max(1, step // 5))
            return True
        except Exception:
            return False