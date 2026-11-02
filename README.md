# Gesture System Control

Control your Linux system volume and display brightness using real-time hand gestures via your webcam, powered by **OpenCV** and **MediaPipe Tasks** (`HandLandmarker`).

## Features

- **Right Hand (Volume Control):** Move a closed fist up or down to increase or decrease system audio volume via `omarchy-audio-output-volume`.
- **Left Hand (Brightness Control):** Move a closed fist up or down to increase or decrease display brightness via `omarchy-brightness-display`.
- **Palm & Fist Safety Lock:** Actions only trigger when your palm faces the camera and your fingers are closed into a fist, preventing accidental triggers.
- **Smooth Anchor-Based Tracking & Native OSD:** Continuous vertical movement tracking with configurable step thresholds and cooldowns, triggering your desktop's native OSD.
- **Modular Preview Architecture:** Optional real-time OpenCV visualization window (`--preview` / `--no-preview`) decoupled from core detection so the application can run lightweight in the background.

## Project Structure

```text
Gesture-System-Control/
├── gesture_control/
│   ├── __init__.py       # Package exports
│   ├── config.py         # Centralized configuration and thresholds
│   ├── controller.py     # Gesture state tracking and OS command execution
│   ├── detector.py       # MediaPipe HandLandmarker wrapper and finger analysis
│   └── visualizer.py     # Optional OpenCV HUD and skeletal rendering
├── models/               # Auto-downloaded MediaPipe .task model bundle (gitignored)
├── main.py               # CLI entry point and main application loop
├── pyproject.toml        # Standard PEP 621 project metadata and dependencies
└── README.md             # Project documentation
```

## Requirements

- Linux with Omarchy utilities (`omarchy-audio-output-volume` and `omarchy-brightness-display`)
- Python 3.10+
- Webcam

## Installation

1. Create and activate a virtual environment, then install the project and its dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

*(Note: The official MediaPipe `hand_landmarker.task` model is automatically downloaded into `models/hand_landmarker.task` on first run if not already present).*

## Usage

- **Development Mode (with real-time camera preview and hand skeleton overlay):**
  ```bash
  gesture-control --preview
  # or: python main.py --preview
  ```
  *(Preview is enabled by default in `gesture_control/config.py`. Press `ESC` or `q` inside the window to exit).*

- **Background / Headless Mode (no GUI window):**
  ```bash
  gesture-control --no-preview
  ```

- **Select a Different Camera Device:**
  ```bash
  gesture-control --camera 1
  ```
