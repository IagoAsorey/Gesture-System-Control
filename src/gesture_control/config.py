import sys
from dataclasses import dataclass
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


@dataclass(frozen=True)
class CameraConfig:
    index: int
    width: int
    height: int


@dataclass(frozen=True)
class GestureConfig:
    movement_threshold: float
    palm_required: bool
    cooldown_frames: int


@dataclass(frozen=True)
class VolumeConfig:
    step: int
    method: str


@dataclass(frozen=True)
class BrightnessConfig:
    step: int


@dataclass(frozen=True)
class DisplayConfig:
    show_fps: bool
    show_landmarks: bool
    window_name: str


@dataclass(frozen=True)
class Config:
    camera: CameraConfig
    gesture: GestureConfig
    volume: VolumeConfig
    brightness: BrightnessConfig
    display: DisplayConfig


def load_config(path: Path = Path("config.toml")) -> Config:
    with path.open("rb") as f:
        data = tomllib.load(f)

    return Config(
        camera=CameraConfig(**data["camera"]),
        gesture=GestureConfig(**data["gesture"]),
        volume=VolumeConfig(**data["volume"]),
        brightness=BrightnessConfig(**data["brightness"]),
        display=DisplayConfig(**data["display"]),
    )


config = load_config()