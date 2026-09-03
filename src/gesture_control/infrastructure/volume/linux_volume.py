import subprocess


class LinuxVolumeControl:
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