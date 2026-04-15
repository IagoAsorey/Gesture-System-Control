"""Módulo para la detección y análisis de manos usando MediaPipe."""

import mediapipe as mp


class DetectorManos:
    """Clase para encapsular la lógica de detección de manos."""

    def __init__(self, max_num_hands=4, min_detection_confidence=0.5):
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence
        )

    def procesar_frame(self, frame_rgb):
        """Procesa un frame RGB y devuelve los resultados de MediaPipe."""
        return self.hands.process(frame_rgb)

    def dibujar_manos(self, frame, hand_landmarks):
        """Dibuja las conexiones de la mano en el frame."""
        self.mp_drawing.draw_landmarks(
            frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS
        )

    def contar_dedos(self, hand_landmarks, hand_label):
        """Cuenta los dedos levantados y determina la visibilidad de la palma."""
        dedos = []
        tips = [4, 8, 12, 16, 20]

        x_base_pulgar = hand_landmarks.landmark[5].x
        x_base_menique = hand_landmarks.landmark[17].x
        
        # Determinar si la mano muestra la palma o el dorso
        if hand_label == 'Derecha':
            palma_visible = x_base_pulgar < x_base_menique
        else:
            palma_visible = x_base_menique < x_base_pulgar  

        estado_palma = 'visible' if palma_visible else 'no visible'

        x_punta_pulgar = hand_landmarks.landmark[tips[0]].x
        x_nudo_pulgar = hand_landmarks.landmark[tips[0] - 2].x

        if hand_label == 'Derecha':
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

        # Verificar los otros 4 dedos
        for i in range(1, 5):
            y_punta = hand_landmarks.landmark[tips[i]].y
            y_nudo = hand_landmarks.landmark[tips[i] - 2].y
            dedos.append(1 if y_punta < y_nudo else 0)
        
        return dedos, estado_palma