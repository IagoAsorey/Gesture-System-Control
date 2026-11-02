"""Optional real-time camera preview and HUD rendering module."""

import time
from typing import Sequence

import cv2
from mediapipe.tasks.python import vision
import numpy as np

from gesture_control import config
from gesture_control.controller import SystemController
from gesture_control.detector import DetectedHand


class Visualizer:
    """Renders hand landmarks, skeletal connections, and HUD status overlays."""

    def __init__(self, window_name: str = config.WINDOW_NAME) -> None:
        self.window_name = window_name
        self.drawing_utils = vision.drawing_utils
        self.drawing_styles = vision.drawing_styles
        self.hand_connections = vision.HandLandmarksConnections.HAND_CONNECTIONS

    def render(
        self,
        frame: np.ndarray,
        hands: Sequence[DetectedHand],
        controller: SystemController,
    ) -> bool:
        """Draws hand skeletons and HUD indicators onto the frame and updates the window.

        Args:
            frame: BGR video frame from OpenCV.
            hands: Sequence of detected hands in the current frame.
            controller: SystemController instance holding recent action feedback.

        Returns:
            True if the user requested to exit (ESC or 'q' key), False otherwise.
        """
        now = time.monotonic()

        for hand in hands:
            # Draw the 21 hand landmarks and their skeletal connections
            self.drawing_utils.draw_landmarks(
                frame,
                hand.landmarks,
                self.hand_connections,
                self.drawing_styles.get_default_hand_landmarks_style(),
                self.drawing_styles.get_default_hand_connections_style(),
            )

            # Render status label near the wrist
            frame_h, frame_w, _ = frame.shape
            wrist_px_x = int(hand.landmarks[0].x * frame_w)
            wrist_px_y = int(hand.landmarks[0].y * frame_h)
            is_gesture_active = hand.is_palm_visible and hand.is_fist_closed
            status_color = (0, 255, 0) if is_gesture_active else (200, 200, 200)
            status_label = f"{hand.label} ({'ACTIVE' if is_gesture_active else 'idle'})"
            cv2.putText(
                frame,
                status_label,
                (max(10, wrist_px_x - 60), min(frame_h - 15, wrist_px_y + 25)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                status_color,
                2,
            )

        # Render HUD feedback when VOLUME +/- or BRIGHTNESS +/- is triggered
        right_state = controller.states["Right"]
        if (
            right_state.last_action_text
            and (now - right_state.last_action_ts) <= config.HUD_FEEDBACK_DURATION_SEC
        ):
            cv2.putText(
                frame,
                right_state.last_action_text,
                (15, 45),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                right_state.last_action_color,
                3,
            )

        left_state = controller.states["Left"]
        if (
            left_state.last_action_text
            and (now - left_state.last_action_ts) <= config.HUD_FEEDBACK_DURATION_SEC
        ):
            cv2.putText(
                frame,
                left_state.last_action_text,
                (frame.shape[1] - 250, 45),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                left_state.last_action_color,
                3,
            )

        cv2.imshow(self.window_name, frame)
        key = cv2.waitKey(1) & 0xFF
        return key in (27, ord("q"))

    def close(self) -> None:
        """Closes all OpenCV highgui windows."""
        cv2.destroyAllWindows()

    def __enter__(self) -> "Visualizer":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
