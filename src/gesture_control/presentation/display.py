import cv2
import numpy as np

from gesture_control.domain.protocols import Display


class OpenCVDisplay:
    def __init__(self, window_name: str):
        self._window_name = window_name
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    def show(self, frame: np.ndarray, texts: list[tuple]) -> bool:
        for text, pos, color in texts:
            cv2.putText(
                frame, text, pos, cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3
            )

        cv2.imshow(self._window_name, frame)
        key = cv2.waitKey(1) & 0xFF
        return key != 27

    def close(self) -> None:
        cv2.destroyAllWindows()