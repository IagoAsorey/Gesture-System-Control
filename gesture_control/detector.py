"""Hand detection and landmark analysis module using MediaPipe Tasks."""

from dataclasses import dataclass
from pathlib import Path
import time
from typing import Sequence
import urllib.request

import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
import numpy as np

from gesture_control import config

# Landmark indices for the 4 non-thumb fingertips and their corresponding PIP joints
_FINGER_TIPS = (8, 12, 16, 20)
_FINGER_PIPS = (6, 10, 14, 18)


@dataclass(slots=True)
class DetectedHand:
    """Processed state and landmark data for a single detected hand."""

    label: str  # "Right" or "Left"
    landmarks: list
    is_gesture_active: bool
    wrist_y: float


class HandDetector:
    """Encapsulates MediaPipe HandLandmarker inference and gesture state analysis."""

    def __init__(
        self,
        max_num_hands: int = config.MAX_NUM_HANDS,
        min_detection_confidence: float = config.MIN_DETECTION_CONFIDENCE,
        min_presence_confidence: float = config.MIN_PRESENCE_CONFIDENCE,
        min_tracking_confidence: float = config.MIN_TRACKING_CONFIDENCE,
        model_path: Path = config.MODEL_PATH,
    ) -> None:
        self.model_path = Path(model_path)
        self._ensure_model()

        options = vision.HandLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=str(self.model_path)),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=max_num_hands,
            min_hand_detection_confidence=min_detection_confidence,
            min_hand_presence_confidence=min_presence_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self.landmarker = vision.HandLandmarker.create_from_options(options)
        self._last_timestamp_ms = 0

    def _ensure_model(self) -> None:
        """Downloads the official MediaPipe hand_landmarker.task bundle atomically if missing."""
        if self.model_path.is_file() and self.model_path.stat().st_size > 0:
            return

        print(f"Downloading MediaPipe model to {self.model_path}...")
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.model_path.with_suffix(".task.tmp")
        try:
            urllib.request.urlretrieve(config.MODEL_URL, str(tmp_path))
            tmp_path.replace(self.model_path)
            print("Model downloaded successfully.")
        except Exception:
            tmp_path.unlink(missing_ok=True)
            raise

    def detect(self, frame_rgb: np.ndarray) -> list[DetectedHand]:
        """Runs hand landmark detection on an RGB frame and returns analyzed hands."""
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        timestamp_ms = max(int(time.monotonic() * 1000), self._last_timestamp_ms + 1)
        self._last_timestamp_ms = timestamp_ms

        result = self.landmarker.detect_for_video(mp_image, timestamp_ms)
        if not result or not result.hand_landmarks:
            return []

        hands: list[DetectedHand] = []
        seen_labels: set[str] = set()

        for idx, hand_landmarks in enumerate(result.hand_landmarks):
            # MediaPipe assumes an unflipped camera frame and classifies the user's
            # physical hands directly as "Right" or "Left".
            mp_label = result.handedness[idx][0].category_name
            hand_label = "Right" if mp_label == "Right" else "Left"

            # Prevent duplicate hand classifications in the same frame from conflicting
            if hand_label in seen_labels:
                continue
            seen_labels.add(hand_label)

            is_active = self._is_palm_fist_active(hand_landmarks, hand_label)
            hands.append(
                DetectedHand(
                    label=hand_label,
                    landmarks=hand_landmarks,
                    is_gesture_active=is_active,
                    wrist_y=hand_landmarks[0].y,
                )
            )

        return hands

    @staticmethod
    def _is_palm_fist_active(hand_landmarks: Sequence, hand_label: str) -> bool:
        """Returns True if the palm faces the camera and the fingers form a closed fist."""
        index_mcp_x = hand_landmarks[5].x
        pinky_mcp_x = hand_landmarks[17].x

        # In an unflipped camera frame, when the palm faces the camera:
        # - Physical Right hand: index MCP is to the right of pinky MCP (index_mcp_x > pinky_mcp_x)
        # - Physical Left hand: pinky MCP is to the right of index MCP (pinky_mcp_x > index_mcp_x)
        is_palm_visible = (
            index_mcp_x > pinky_mcp_x
            if hand_label == "Right"
            else pinky_mcp_x > index_mcp_x
        )
        if not is_palm_visible:
            return False

        # Check that all 4 fingers (index, middle, ring, pinky) are folded down
        return all(
            hand_landmarks[tip].y > hand_landmarks[pip].y
            for tip, pip in zip(_FINGER_TIPS, _FINGER_PIPS)
        )

    def close(self) -> None:
        """Releases underlying MediaPipe C++ resources."""
        if getattr(self, "landmarker", None) is not None:
            self.landmarker.close()
            self.landmarker = None

    def __enter__(self) -> "HandDetector":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
