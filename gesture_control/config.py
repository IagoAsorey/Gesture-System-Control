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
# Normalized 2D distance (0.0 to 1.0) required to trigger a single swipe step
SWIPE_STEP_THRESHOLD = 0.035

# Minimum elapsed time (in seconds) between consecutive adjustments per hand
ACTION_COOLDOWN_SEC = 0.12

# Normalized 2D distance (0.0 to 1.0) between fingertips to detect a standard pinch
PINCH_DISTANCE_THRESHOLD = 0.05

# Minimum elapsed time (in seconds) between consecutive pinch triggers per hand
PINCH_COOLDOWN_SEC = 0.5

# Normalized 2D distance (0.0 to 1.0) to detect a multi-finger pinch wheel grip
PINCH_WHEEL_DISTANCE_THRESHOLD = 0.065

# Rotation angle in radians (~15 degrees) required to trigger a pinch wheel step adjustment
PINCH_WHEEL_ANGLE_THRESHOLD = 0.26

# Adjustment step sizes (in percentage)
VOLUME_STEP = 10
BRIGHTNESS_STEP = 10

# Duration (in seconds) to display visual action feedback on the HUD
HUD_FEEDBACK_DURATION_SEC = 0.4

# Gesture-to-action mappings per hand.
# "fingers" is a 5-element binary array: [thumb, index, middle, ring, pinky]
#   - For "pinch" and "pinch_wheel_*": 1 = pinched together, 0 = separated.
#   - For "swipe_up", "swipe_down", "swipe_left", "swipe_right": 1 = extended, 0 = folded.
GESTURE_BINDINGS: dict[str, list[dict[str, object]]] = {
    "Right": [
        {
            "gesture": "swipe_right",
            "fingers": [0, 1, 0, 0, 0],
            "action": "next_track",
        },
        {
            "gesture": "swipe_left",
            "fingers": [0, 1, 0, 0, 0],
            "action": "previous_track",
        },
        {
            "gesture": "pinch_wheel_right",
            "fingers": [1, 1, 1, 0, 0],
            "action": "volume_up",
        },
        {
            "gesture": "pinch_wheel_left",
            "fingers": [1, 1, 1, 0, 0],
            "action": "volume_down",
        },
        {
            "gesture": "pinch",
            "fingers": [1, 1, 0, 0, 0],
            "action": "play_pause",
        },
    ],
    "Left": [
        {
            "gesture": "swipe_up",
            "fingers": [0, 1, 0, 0, 0],
            "action": "brightness_up",
        },
        {
            "gesture": "swipe_down",
            "fingers": [0, 1, 0, 0, 0],
            "action": "brightness_down",
        },
    ],
}
