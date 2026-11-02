"""Centralized configuration for the Gesture System Control application."""

from pathlib import Path

# Base project directories
BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"

# MediaPipe HandLandmarker model configuration
MODEL_PATH = MODELS_DIR / "hand_landmarker.task"
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
)

# Camera capture settings
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Preview window settings (enabled by default for development, toggle via --no-preview / --headless)
SHOW_PREVIEW = True
WINDOW_NAME = "Gesture System Control"

# MediaPipe HandLandmarker confidence thresholds
MAX_NUM_HANDS = 2
MIN_DETECTION_CONFIDENCE = 0.6
MIN_PRESENCE_CONFIDENCE = 0.6
MIN_TRACKING_CONFIDENCE = 0.6

# Gesture recognition and sensitivity settings
# Normalized vertical distance (0.0 to 1.0) required to trigger a single step adjustment
MOVEMENT_STEP_THRESHOLD = 0.035

# Minimum elapsed time (in seconds) between consecutive adjustments per hand
ACTION_COOLDOWN_SEC = 0.12

# Adjustment step sizes (in percentage)
VOLUME_STEP = 5
BRIGHTNESS_STEP = 5

# Duration (in seconds) to display visual action feedback on the HUD
HUD_FEEDBACK_DURATION_SEC = 0.4
