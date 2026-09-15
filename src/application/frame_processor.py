import cv2
import numpy as np

from gesture_control.application.actions import ActionExecutor
from gesture_control.application.gesture_analyzer import GestureAnalyzer
from gesture_control.domain.entities import Hand
from gesture_control.domain.enums import GestureType
from gesture_control.domain.protocols import Camera, Display, HandDetector


class FrameProcessor:
    def __init__(
        self,
        camera: Camera,
        detector: HandDetector,
        display: Display,
        analyzer: GestureAnalyzer,
        executor: ActionExecutor,
        show_landmarks: bool,
    ):
        self._camera = camera
        self._detector = detector
        self._display = display
        self._analyzer = analyzer
        self._executor = executor
        self._show_landmarks = show_landmarks

    def run(self) -> None:
        while self._camera.is_opened:
            frame = self._camera.read()
            if frame is None:
                break

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            hands = self._detector.process(frame_rgb)

            texts = []
            for hand in hands:
                gesture = self._analyzer.analyze(hand)
                ok, label = self._executor.execute(gesture)
                if ok and label:
                    pos = (10, 50) if hand.label.value == "Derecha" else (400, 50)
                    color = (0, 255, 0) if "UP" in label or "+" in label else (0, 0, 255)
                    texts.append((label, pos, color))

                if self._show_landmarks:
                    self._detector.draw_landmarks(frame, hand)

            if not self._display.show(frame, texts):
                break

        self._cleanup()

    def _cleanup(self) -> None:
        self._camera.release()
        self._detector.close()
        self._display.close()