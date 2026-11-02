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


@dataclass
class DetectedHand:
    """Processed state and landmark data for a single detected hand."""

    label: str  # "Right" or "Left"
    landmarks: list
    fingers_up: list[int]
    is_palm_visible: bool
    is_fist_closed: bool
    wrist_y: float


class HandDetector:
    """Encapsulates MediaPipe HandLandmarker inference and finger state analysis."""

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

        base_options = mp_python.BaseOptions(model_asset_path=str(self.model_path))
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=max_num_hands,
            min_hand_detection_confidence=min_detection_confidence,
            min_hand_presence_confidence=min_presence_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self.landmarker = vision.HandLandmarker.create_from_options(options)
        self._last_timestamp_ms = 0

    def _ensure_model(self) -> None:
        """Downloads the official MediaPipe hand_landmarker.task bundle if missing."""
        if self.model_path.is_file():
            return
        print(f"Downloading MediaPipe model to {self.model_path}...")
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(config.MODEL_URL, str(self.model_path))
        print("Model downloaded successfully.")

    def process_frame(self, frame_rgb: np.ndarray) -> vision.HandLandmarkerResult:
        """Processes an RGB frame and returns the MediaPipe HandLandmarkerResult."""
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        timestamp_ms = int(time.monotonic() * 1000)
        if timestamp_ms <= self._last_timestamp_ms:
            timestamp_ms = self._last_timestamp_ms + 1
        self._last_timestamp_ms = timestamp_ms

        return self.landmarker.detect_for_video(mp_image, timestamp_ms)

    def analyze_results(
        self, detection_result: vision.HandLandmarkerResult
    ) -> list[DetectedHand]:
        """Extracts and analyzes all hands present in a HandLandmarkerResult."""
        hands: list[DetectedHand] = []
        if not detection_result or not detection_result.hand_landmarks:
            return hands

        for idx, hand_landmarks in enumerate(detection_result.hand_landmarks):
            # Because the video frame is horizontally flipped (mirror view) before
            # inference, MediaPipe's classification directly matches the user's physical hand.
            mp_label = detection_result.handedness[idx][0].category_name
            hand_label = "Right" if mp_label == "Right" else "Left"

            fingers_up, is_palm_visible = self.count_fingers(hand_landmarks, hand_label)
            is_fist_closed = sum(fingers_up) == 0

            hands.append(
                DetectedHand(
                    label=hand_label,
                    landmarks=hand_landmarks,
                    fingers_up=fingers_up,
                    is_palm_visible=is_palm_visible,
                    is_fist_closed=is_fist_closed,
                    wrist_y=hand_landmarks[0].y,
                )
            )

        return hands

    def count_fingers(
        self, hand_landmarks: Sequence, hand_label: str
    ) -> tuple[list[int], bool]:
        """Counts extended fingers and determines whether the palm faces the camera."""
        fingers: list[int] = []
        tip_indices = [4, 8, 12, 16, 20]

        index_mcp_x = hand_landmarks[5].x
        pinky_mcp_x = hand_landmarks[17].x

        # Determine if the palm is facing the camera or facing away
        if hand_label == "Right":
            is_palm_visible = index_mcp_x < pinky_mcp_x
        else:
            is_palm_visible = pinky_mcp_x < index_mcp_x

        thumb_tip_x = hand_landmarks[tip_indices[0]].x
        thumb_ip_x = hand_landmarks[tip_indices[0] - 1].x

        if hand_label == "Right":
            if is_palm_visible:
                is_thumb_up = thumb_tip_x < thumb_ip_x
            else:
                is_thumb_up = thumb_tip_x > thumb_ip_x
        else:
            if is_palm_visible:
                is_thumb_up = thumb_tip_x > thumb_ip_x
            else:
                is_thumb_up = thumb_tip_x < thumb_ip_x

        fingers.append(1 if is_thumb_up else 0)

        # Evaluate the remaining 4 fingers (index, middle, ring, pinky)
        for i in range(1, 5):
            finger_tip_y = hand_landmarks[tip_indices[i]].y
            finger_pip_y = hand_landmarks[tip_indices[i] - 2].y
            fingers.append(1 if finger_tip_y < finger_pip_y else 0)

        return fingers, is_palm_visible

    def close(self) -> None:
        """Releases underlying MediaPipe C++ resources."""
        if getattr(self, "landmarker", None) is not None:
            self.landmarker.close()
            self.landmarker = None

    def __enter__(self) -> "HandDetector":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
