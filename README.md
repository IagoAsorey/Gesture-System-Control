# Gesture System Control

Control system volume and brightness using hand gestures via webcam. Cross-platform (Windows/Linux).

## Features
- **Right Hand**: Volume control (Up/Down)
- **Left Hand**: Brightness control (Up/Down)
- **Palm Safety**: Controls only activate when palm faces camera
- **Cross-platform**: Works on Windows and Linux (tested on Omarchy/Arch)

## Requirements
- Python 3.10+
- Webcam
- Linux: `wpctl` (PipeWire/WirePlumber), `brightnessctl` or `ddcutil` for brightness

## Installation

```bash
# Using uv (recommended)
uv sync

# Or pip
pip install -e .
```

## Usage

```bash
# Run the application
python -m gesture_control.main
```

Press **ESC** to exit.

## Gestures
| Hand | Gesture | Action |
|------|---------|--------|
| Right | Fist + Move Up | Volume Up |
| Right | Fist + Move Down | Volume Down |
| Left | Fist + Move Up | Brightness Up |
| Left | Fist + Move Down | Brightness Down |

*Palm must be visible to camera for gestures to work*

## Configuration

Edit `config.toml`:

```toml
[camera]
index = 0
width = 640
height = 480

[gesture]
movement_threshold = 0.02
palm_required = true
cooldown_frames = 3

[volume]
step = 5
linux_method = "wpctl"  # wpctl | pactl | amixer

[brightness]
step = 10

[display]
show_landmarks = true
window_name = "Gesture Control"
```

## Architecture

```
src/gesture_control/
├── domain/           # Pure business logic
│   ├── entities.py   # Hand, Landmark
│   ├── enums.py      # HandLabel, PalmState, GestureType
│   └── protocols.py  # Interfaces (Detector, Camera, Volume, Brightness, Display)
├── application/      # Use cases
│   ├── gesture_analyzer.py
│   ├── frame_processor.py
│   └── actions.py
├── infrastructure/   # External implementations
│   ├── detectors/mediapipe_detector.py
│   ├── camera/opencv_camera.py
│   ├── volume/windows_volume.py, linux_volume.py
│   ├── brightness/sbc_brightness.py
│   └── platform.py   # Factory (OS detection)
├── presentation/     # UI
│   └── display.py
├── config.py         # TOML config loader
└── main.py           # Entry point
```

## Linux Setup (Omarchy/Arch)

```bash
# Volume (PipeWire/WirePlumber - default on Omarchy)
sudo pacman -S wireplumber

# Brightness (laptop backlight)
sudo pacman -S brightnessctl

# Brightness (external monitors via DDC/CI)
sudo pacman -S ddcutil
sudo usermod -aG i2c $USER
# reboot or re-login
```

## License
MIT