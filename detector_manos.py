"""Módulo para la detección y análisis de manos usando MediaPipe Tasks (HandLandmarker)."""

from dataclasses import dataclass
from pathlib import Path
import time
import urllib.request
from typing import Sequence

import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
import numpy as np

import config


@dataclass
class ManoDetectada:
    """Información procesada de una mano detectada en un frame."""

    etiqueta: str  # 'Derecha' o 'Izquierda'
    landmarks: list
    dedos_arriba: list[int]
    estado_palma: str  # 'visible' o 'no visible'
    puno_cerrado: bool
    y_muneca: float


class DetectorManos:
    """Clase para encapsular la lógica de detección de manos con MediaPipe Tasks."""

    def __init__(
        self,
        max_num_hands: int = config.MAX_NUM_HANDS,
        min_detection_confidence: float = config.MIN_DETECTION_CONFIDENCE,
        min_presence_confidence: float = config.MIN_PRESENCE_CONFIDENCE,
        min_tracking_confidence: float = config.MIN_TRACKING_CONFIDENCE,
        model_path: Path = config.MODEL_PATH,
    ):
        self.model_path = Path(model_path)
        self._asegurar_modelo()

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
        self._ultimo_timestamp_ms = 0

    def _asegurar_modelo(self) -> None:
        """Descarga automáticamente el modelo hand_landmarker.task si no existe localmente."""
        if self.model_path.is_file():
            return
        print(f"Descargando modelo de MediaPipe en {self.model_path}...")
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(config.MODEL_URL, str(self.model_path))
        print("Modelo descargado correctamente.")

    def procesar_frame(self, frame_rgb: np.ndarray):
        """Procesa un frame RGB y devuelve el resultado de HandLandmarker."""
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        timestamp_ms = int(time.monotonic() * 1000)
        if timestamp_ms <= self._ultimo_timestamp_ms:
            timestamp_ms = self._ultimo_timestamp_ms + 1
        self._ultimo_timestamp_ms = timestamp_ms

        return self.landmarker.detect_for_video(mp_image, timestamp_ms)

    def analizar_resultados(self, detection_result) -> list[ManoDetectada]:
        """Extrae y analiza todas las manos presentes en el resultado de MediaPipe."""
        manos: list[ManoDetectada] = []
        if not detection_result or not detection_result.hand_landmarks:
            return manos

        for idx, hand_landmarks in enumerate(detection_result.hand_landmarks):
            # Como la imagen de cámara se voltea horizontalmente (modo espejo) antes de
            # pasarse a MediaPipe, el modelo ya devuelve 'Right' para tu mano derecha real
            # y 'Left' para tu mano izquierda real.
            etiqueta_mp = detection_result.handedness[idx][0].category_name
            hand_label = "Derecha" if etiqueta_mp == "Right" else "Izquierda"

            dedos_arriba, estado_palma = self.contar_dedos(hand_landmarks, hand_label)
            # Consideramos puño cerrado cuando los 4 dedos largos están cerrados
            # y la suma total de dedos levantados es 0.
            puno_cerrado = sum(dedos_arriba) == 0

            manos.append(
                ManoDetectada(
                    etiqueta=hand_label,
                    landmarks=hand_landmarks,
                    dedos_arriba=dedos_arriba,
                    estado_palma=estado_palma,
                    puno_cerrado=puno_cerrado,
                    y_muneca=hand_landmarks[0].y,
                )
            )

        return manos

    def contar_dedos(
        self, hand_landmarks: Sequence, hand_label: str
    ) -> tuple[list[int], str]:
        """Cuenta los dedos levantados y determina la visibilidad de la palma."""
        dedos: list[int] = []
        tips = [4, 8, 12, 16, 20]

        x_base_pulgar = hand_landmarks[5].x
        x_base_menique = hand_landmarks[17].x

        # Determinar si la mano muestra la palma o el dorso hacia la cámara
        if hand_label == "Derecha":
            palma_visible = x_base_pulgar < x_base_menique
        else:
            palma_visible = x_base_menique < x_base_pulgar

        estado_palma = "visible" if palma_visible else "no visible"

        x_punta_pulgar = hand_landmarks[tips[0]].x
        x_nudo_pulgar = hand_landmarks[tips[0] - 1].x

        if hand_label == "Derecha":
            if palma_visible:
                pulgar_levantado = x_punta_pulgar < x_nudo_pulgar
            else:
                pulgar_levantado = x_punta_pulgar > x_nudo_pulgar
        else:
            if palma_visible:
                pulgar_levantado = x_punta_pulgar > x_nudo_pulgar
            else:
                pulgar_levantado = x_punta_pulgar < x_nudo_pulgar

        dedos.append(1 if pulgar_levantado else 0)

        # Verificar los otros 4 dedos (índice, corazón, anular, meñique)
        for i in range(1, 5):
            y_punta = hand_landmarks[tips[i]].y
            y_nudo = hand_landmarks[tips[i] - 2].y
            dedos.append(1 if y_punta < y_nudo else 0)

        return dedos, estado_palma

    def cerrar(self) -> None:
        """Libera los recursos del detector de MediaPipe."""
        if hasattr(self, "landmarker") and self.landmarker is not None:
            self.landmarker.close()
            self.landmarker = None
