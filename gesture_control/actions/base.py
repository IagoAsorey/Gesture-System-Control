"""Base interfaces and command runners for executable system actions."""

from abc import ABC, abstractmethod
import shutil
import subprocess
import sys
from typing import Optional

_WARNED_BINARIES: set[str] = set()


def _resolve_binary(binary_name: str) -> Optional[str]:
    """Resolves a CLI binary in PATH and logs a one-time warning if missing."""
    path = shutil.which(binary_name)
    if not path and binary_name not in _WARNED_BINARIES:
        _WARNED_BINARIES.add(binary_name)
        print(f"Warning: '{binary_name}' not found in PATH.", file=sys.stderr)
    return path


class BaseAction(ABC):
    """Base interface for all executable system actions."""

    label: str
    color: tuple[int, int, int] = (0, 255, 0)

    @abstractmethod
    def execute(self) -> str:
        """Executes the action and returns its HUD display label."""


class CommandAction(BaseAction):
    """Base action that executes an external CLI command asynchronously."""

    def __init__(
        self,
        binary_name: str,
        args: list[str],
        label: str,
        color: tuple[int, int, int] = (0, 255, 0),
    ) -> None:
        self.binary_name = binary_name
        self.binary_path = _resolve_binary(binary_name)
        self.args = args
        self.label = label
        self.color = color

    def execute(self) -> str:
        """Spawns the configured CLI command without blocking the main loop."""
        if self.binary_path:
            try:
                subprocess.Popen(
                    [self.binary_path, *self.args],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except OSError:
                pass
        return self.label
