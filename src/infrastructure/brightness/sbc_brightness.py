import screen_brightness_control as sbc


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