"""Script principal para el control gestual del volumen y brillo."""

import cv2
import pyautogui
import screen_brightness_control as sbc

from detector_manos import DetectorManos


def main():
    """Función principal que ejecuta el bucle de la cámara y la lógica de control."""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: No se puede abrir la cámara.")
        exit()

    detector = DetectorManos()

    # Memoria para la posición Y de la muñeca del frame anterior
    y_anterior = {"Derecha": None, "Izquierda": None}
    umbral_movimiento = 0.02

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Preparación de la imagen
        frame = cv2.resize(frame, (640, 480))
        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Procesar para detectar manos
        results = detector.procesar_frame(frame_rgb)

        if results.multi_hand_landmarks:
            for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                # Obtener la etiqueta de la mano
                etiqueta_mp = results.multi_handedness[idx].classification[0].label
                hand_label = "Derecha" if etiqueta_mp == "Right" else "Izquierda"
                
                # Analizar mano
                dedos_arriba, estado_palma = detector.contar_dedos(hand_landmarks, hand_label)
                y_actual = hand_landmarks.landmark[0].y

                if estado_palma == 'visible':
                    # Mano cerrada
                    if sum(dedos_arriba) == 0:
                        if y_anterior[hand_label] is not None:
                            diferencia = y_anterior[hand_label] - y_actual

                            # Gesto de subir
                            if diferencia > umbral_movimiento:
                                if hand_label == "Derecha":     # Volumen
                                    pyautogui.press('volumeup', presses=10)
                                    cv2.putText(
                                        frame, 'VOLUMEN +', (10, 50),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3
                                    )
                                elif hand_label == "Izquierda": # Brillo
                                    try:
                                        brillo_actual = sbc.get_brightness()[0]
                                        sbc.set_brightness(min(100, brillo_actual + 10))
                                        cv2.putText(
                                            frame, 'BRILLO +', (400, 50),
                                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3
                                        )
                                    except Exception:
                                        pass
                                                        
                            # Gesto de bajar
                            elif diferencia < -umbral_movimiento:
                                if hand_label == "Derecha":     # Volumen
                                    pyautogui.press('volumedown', presses=10)
                                    cv2.putText(
                                        frame, 'VOLUMEN -', (10, 50),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3
                                    )
                                elif hand_label == "Izquierda": # Brillo
                                    try:
                                        brillo_actual = sbc.get_brightness()[0]
                                        sbc.set_brightness(max(0, brillo_actual - 10))
                                        cv2.putText(
                                            frame, 'BRILLO -', (400, 50),
                                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3
                                        )
                                    except Exception:
                                        pass
                # Guardamos la posición para compararla en el siguiente frame
                y_anterior[hand_label] = y_actual
                
                # Dibujar esqueleto sobre el video
                detector.dibujar_manos(frame, hand_landmarks)

        cv2.imshow("Control Gestual del Sistema", frame)

        # Salir con la tecla ESC (código ASCII 27)
        if cv2.waitKey(1) & 0xFF == 27: break

    cap.release()
    cv2.destroyAllWindows()

# Punto de entrada de la aplicación
if __name__ == "__main__":
    main()