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
        self._draw_landmarks = vision.drawing_utils.draw_landmarks
        self._hand_connections = vision.HandLandmarksConnections.HAND_CONNECTIONS
        self._landmark_style = vision.drawing_styles.get_default_hand_landmarks_style()
        self._connection_style = vision.drawing_styles.get_default_hand_connections_style()

    def render(
        self,
        frame: np.ndarray,
        hands: Sequence[DetectedHand],
        controller: SystemController,
    ) -> bool:
        """Draws hand skeletons and HUD indicators onto the frame and updates the window.

        Returns:
            True if the user requested to exit (ESC, 'q', or window closed), False otherwise.
        """
        now = time.monotonic()
        frame_h, frame_w, _ = frame.shape

        # 1. Draw skeletal landmarks on the unflipped frame so coordinates match 1:1
        for hand in hands:
            self._draw_landmarks(
                frame,
                hand.landmarks,
                self._hand_connections,
                self._landmark_style,
                self._connection_style,
            )

        # 2. Flip the frame horizontally for a natural mirror preview
        frame = cv2.flip(frame, 1)

        # 3. Draw text overlays after flipping so text is readable (not mirrored)
        for hand in hands:
            wrist_px_x = int((1.0 - hand.landmarks[0].x) * frame_w)
            wrist_px_y = int(hand.landmarks[0].y * frame_h)
            status_color = (0, 255, 0) if hand.is_gesture_active else (200, 200, 200)
            status_label = f"{hand.label} ({'ACTIVE' if hand.is_gesture_active else 'idle'})"
            cv2.putText(
                frame,
                status_label,
                (max(10, wrist_px_x - 60), min(frame_h - 15, wrist_px_y + 25)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                status_color,
                2,
            )

        # Render HUD feedback for both hands
        for label, pos_x in (("Right", 15), ("Left", frame_w - 250)):
            state = controller.states[label]
            if (
                state.last_action_text
                and (now - state.last_action_ts) <= config.HUD_FEEDBACK_DURATION_SEC
            ):
                cv2.putText(
                    frame,
                    state.last_action_text,
                    (pos_x, 45),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    state.last_action_color,
                    3,
                )

        cv2.imshow(self.window_name, frame)
        key = cv2.waitKey(1) & 0xFF
        if key in (27, ord("q")):
            return True

        # Exit cleanly if the window was closed via the window manager
        return cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE) < 1

    def close(self) -> None:
        """Closes all OpenCV highgui windows."""
        cv2.destroyAllWindows()
