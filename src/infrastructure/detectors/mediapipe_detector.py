import mediapipe as mp
import numpy as np
from pathlib import Path

from gesture_control.domain.entities import Hand, Landmark
from gesture_control.domain.enums import HandLabel, PalmState
from gesture_control.domain.protocols import HandDetector


class MediaPipeHandDetector:
    def __init__(
        self,
        max_num_hands: int = 2,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        model_path: str | None = None,
    ):
        self._mp_hands = mp.tasks.vision.HandLandmarker
        self._mp_drawing = mp.tasks.vision.drawing_utils
        self._hand_connections = mp.tasks.vision.HandLandmarksConnections.HAND_CONNECTIONS

        if model_path is None:
            model_path = str(Path(__file__).parent.parent.parent.parent / "hand_landmarker.task")

        base_options = mp.tasks.BaseOptions(
            model_asset_path=model_path
        )
        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
            num_hands=max_num_hands,
            min_hand_detection_confidence=min_detection_confidence,
            min_hand_presence_confidence=min_tracking_confidence,
            min_tracking_confidence=min_tracking_confidence,
            result_callback=self._result_callback,
        )
        self._landmarker = self._mp_hands.create_from_options(options)
        self._latest_result = None
        self._timestamp = 0

    def _result_callback(self, result, _, __):
        self._latest_result = result

    def process(self, frame_rgb: np.ndarray) -> list[Hand]:
        self._timestamp += 1
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        self._landmarker.detect_async(mp_image, self._timestamp)

        hands = []
        if self._latest_result and self._latest_result.hand_landmarks:
            for idx, hand_landmarks in enumerate(self._latest_result.hand_landmarks):
                label_mp = self._latest_result.handedness[idx][0].category_name
                hand_label = HandLabel.from_mediapipe(label_mp)

                landmarks = [
                    Landmark(lm.x, lm.y, lm.z) for lm in hand_landmarks
                ]

                fingers_up, palm_state = self._analyze_hand(landmarks, hand_label)

                hands.append(
                    Hand(
                        label=hand_label,
                        landmarks=landmarks,
                        palm_state=palm_state,
                        fingers_up=fingers_up,
                    )
                )

        return hands

    def _analyze_hand(
        self, landmarks: list[Landmark], hand_label: HandLabel
    ) -> tuple[list[bool], PalmState]:
        tips = [4, 8, 12, 16, 20]
        fingers = []

        x_base_thumb = landmarks[5].x
        x_base_pinky = landmarks[17].x

        if hand_label == HandLabel.RIGHT:
            palm_visible = x_base_thumb < x_base_pinky
        else:
            palm_visible = x_base_pinky < x_base_thumb

        palm_state = PalmState.VISIBLE if palm_visible else PalmState.NOT_VISIBLE

        x_tip_thumb = landmarks[tips[0]].x
        x_ip_thumb = landmarks[tips[0] - 2].x

        if hand_label == HandLabel.RIGHT:
            thumb_up = x_tip_thumb < x_ip_thumb if palm_visible else x_tip_thumb > x_ip_thumb
        else:
            thumb_up = x_tip_thumb > x_ip_thumb if palm_visible else x_tip_thumb < x_ip_thumb

        fingers.append(thumb_up)

        for i in range(1, 5):
            y_tip = landmarks[tips[i]].y
            y_pip = landmarks[tips[i] - 2].y
            fingers.append(y_tip < y_pip)

        return fingers, palm_state

    def draw_landmarks(self, frame: np.ndarray, hand: Hand) -> None:
        if self._latest_result and self._latest_result.hand_landmarks:
            for hand_landmarks in self._latest_result.hand_landmarks:
                self._mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self._hand_connections,
                )

    def close(self) -> None:
        self._landmarker.close()