import cv2
import numpy as np

from gesture_control.domain.protocols import Camera


class OpenCVCamera:
    def __init__(self, index: int, width: int, height: int):
        self._cap = cv2.VideoCapture(index)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def read(self) -> np.ndarray | None:
        ret, frame = self._cap.read()
        if not ret:
            return None
        frame = cv2.flip(frame, 1)
        return frame

    def release(self) -> None:
        self._cap.release()

    @property
    def is_opened(self) -> bool:
        return self._cap.isOpened()