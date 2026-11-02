"""Módulo opcional de previsualización en tiempo real para desarrollo."""

import time
from typing import Sequence

import cv2
from mediapipe.tasks.python import vision
import numpy as np

import config
from controlador_sistema import ControladorSistema
from detector_manos import ManoDetectada


class Visualizador:
    """Se encarga de dibujar los puntos de las manos, conexiones e indicadores sobre el vídeo."""

    def __init__(self, window_name: str = config.WINDOW_NAME):
        self.window_name = window_name
        self.drawing_utils = vision.drawing_utils
        self.drawing_styles = vision.drawing_styles
        self.hand_connections = vision.HandLandmarksConnections.HAND_CONNECTIONS

    def renderizar(
        self,
        frame: np.ndarray,
        manos: Sequence[ManoDetectada],
        controlador: ControladorSistema,
    ) -> bool:
        """Dibuja las manos y el HUD en el frame y actualiza la ventana de OpenCV.

        Returns:
            True si el usuario solicitó cerrar la ventana (tecla ESC o 'q'), False en caso contrario.
        """
        ahora = time.monotonic()

        for mano in manos:
            # Dibujar las 21 marcas y sus conexiones encima de la mano
            self.drawing_utils.draw_landmarks(
                frame,
                mano.landmarks,
                self.hand_connections,
                self.drawing_styles.get_default_hand_landmarks_style(),
                self.drawing_styles.get_default_hand_connections_style(),
            )

            # Mostrar etiqueta discreta junto a la muñeca
            h, w, _ = frame.shape
            cx = int(mano.landmarks[0].x * w)
            cy = int(mano.landmarks[0].y * h)
            gesto_activo = mano.estado_palma == "visible" and mano.puno_cerrado
            color_estado = (0, 255, 0) if gesto_activo else (200, 200, 200)
            texto_mano = f"{mano.etiqueta} ({'ACTIVO' if gesto_activo else 'espera'})"
            cv2.putText(
                frame,
                texto_mano,
                (max(10, cx - 60), min(h - 15, cy + 25)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                color_estado,
                2,
            )

        # Mostrar retroalimentación en pantalla cuando se dispara VOLUMEN +/- o BRILLO +/-
        estado_der = controlador.estados["Derecha"]
        if (
            estado_der.ultima_accion_texto
            and (ahora - estado_der.ultima_accion_ts) <= config.HUD_FEEDBACK_DURATION_SEC
        ):
            cv2.putText(
                frame,
                estado_der.ultima_accion_texto,
                (15, 45),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                estado_der.ultima_accion_color,
                3,
            )

        estado_izq = controlador.estados["Izquierda"]
        if (
            estado_izq.ultima_accion_texto
            and (ahora - estado_izq.ultima_accion_ts) <= config.HUD_FEEDBACK_DURATION_SEC
        ):
            cv2.putText(
                frame,
                estado_izq.ultima_accion_texto,
                (frame.shape[1] - 200, 45),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                estado_izq.ultima_accion_color,
                3,
            )

        cv2.imshow(self.window_name, frame)
        key = cv2.waitKey(1) & 0xFF
        return key in (27, ord("q"))

    def cerrar(self) -> None:
        """Cierra todas las ventanas abiertas de OpenCV."""
        cv2.destroyAllWindows()
