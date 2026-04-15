import cv2
import mediapipe as mp

# Inicializar mediapipe para manos
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

# Función para contar los dedos levantados
def contar_dedos(hand_landmarks, hand_label):
    dedos = []
    tips = [4, 8, 12, 16, 20]   # Lista de puntos de los dedos
    
    # Determinar si la mano muestra la palma o el dorso
    if hand_label == 'Derecha':
        palma_visible = hand_landmarks.landmark[5].x < hand_landmarks.landmark[17].x
    else:
        palma_visible = hand_landmarks.landmark[17].x < hand_landmarks.landmark[5].x

    # Mensaje de estado de la palma
    if palma_visible:
        estado_palma = 'visible'
    else:
        estado_palma = 'no visible'

    # Verificar si el pulgar está levantado
    if hand_label == 'Derecha':   # Mano derecha
        if palma_visible:
            pulgar_levantado = hand_landmarks.landmark[tips[0]].x < hand_landmarks.landmark[tips[0] - 2].x
        else:  
            pulgar_levantado = hand_landmarks.landmark[tips[0]].x > hand_landmarks.landmark[tips[0] - 2].x
        dedos.append(1 if pulgar_levantado else 0)
    else:       # Mano izquierda
        if palma_visible:
            pulgar_levantado = hand_landmarks.landmark[tips[0]].x > hand_landmarks.landmark[tips[0] - 2].x
        else:
            pulgar_levantado = hand_landmarks.landmark[tips[0]].x < hand_landmarks.landmark[tips[0] - 2].x
        dedos.append(1 if pulgar_levantado else 0)

    # Verificar los otros 4 dedos
    for id in range(1, 5):
        dedos.append(1 if hand_landmarks.landmark[tips[id]].y < hand_landmarks.landmark[tips[id] - 2].y else 0)
    
    return dedos, estado_palma

cap = cv2.VideoCapture(0)  # Carga la cámara
if not cap.isOpened():  # Comprobar si la cámara se abrió correctamente
    print("Error: No se puede abrir la cámara.")
    exit()

# Usar el modelo de detección de manos
with mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=4,  # Limita el número de manos
    min_detection_confidence=0.5) as hands:

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: No se pudo capturar el frame.")
            break

        # Redimensionar el frame para mejorar el rendimiento
        frame = cv2.resize(frame, (640, 480))   # Redimensionar a 640x480
        frame = cv2.flip(frame, 1)              # Voltear la imagen horizontalmente
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convertir a RGB

        results = hands.process(frame_rgb)  # Procesar la imagen para detectar manos

        total_dedos = 0

        if results.multi_hand_landmarks:  # Verificar si se detectan manos
            for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                # Obtener la etiqueta de la mano (izquierda o derecha)
                if results.multi_handedness[idx].classification[0].label == "Right":
                    hand_label = "Derecha"
                else:
                    hand_label = "Izquierda"
                
                # Contar dedos para cada mano
                dedos_arriba, estado_palma = contar_dedos(hand_landmarks, hand_label)
                total_dedos += sum(dedos_arriba)

                # Mostrar el número de dedos levantados en el frame
                cv2.putText(frame, f'Dedos mano {hand_label}: {sum(dedos_arriba)}', (10, 70 + idx*30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)
                
                # Mostrar el estado de la palma
                cv2.putText(frame, f'Palma: {estado_palma}', (350, 70 + idx*30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)

                # Dibujar las conexiones y los puntos clave de la mano en la imagen original
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        # Mostrar el total de dedos levantados (máx. 10)
        cv2.putText(frame, f'Total dedos levantados: {total_dedos}', (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        cv2.imshow("Frame", frame)

        if cv2.waitKey(1) & 0xFF == 27:  # Salir al pulsar ESC
            break

cap.release()
cv2.destroyAllWindows() 