"""Configuración centralizada del proyecto Gesture System Control."""

from pathlib import Path

# Directorio base del proyecto
BASE_DIR = Path(__file__).resolve().parent

# Modelo de MediaPipe HandLandmarker
MODEL_PATH = BASE_DIR / "hand_landmarker.task"
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
)

# Configuración de la cámara
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Previsualización (True por defecto para desarrollo, desactivable con --no-preview / --headless)
SHOW_PREVIEW = True
WINDOW_NAME = "Control Gestual del Sistema"

# Configuración de MediaPipe HandLandmarker
MAX_NUM_HANDS = 2
MIN_DETECTION_CONFIDENCE = 0.6
MIN_PRESENCE_CONFIDENCE = 0.6
MIN_TRACKING_CONFIDENCE = 0.6

# Configuración de gestos y sensibilidad
# Distancia vertical normalizada (0.0 a 1.0) necesaria para disparar un paso de ajuste
MOVEMENT_STEP_THRESHOLD = 0.035

# Tiempo mínimo en segundos entre ajustes consecutivos por mano (evita saturar el sistema/OSD)
ACTION_COOLDOWN_SEC = 0.12

# Pasos de cambio en porcentaje
VOLUME_STEP = 5
BRIGHTNESS_STEP = 5

# Tiempo que permanece en pantalla el indicador visual de acción (en segundos)
HUD_FEEDBACK_DURATION_SEC = 0.4
