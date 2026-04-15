# Gesture System Control

Este proyecto permite controlar el volumen y el brillo de tu ordenador mediante gestos manuales frente a la cámara, utilizando Computer Vision.

## Características
- **Mano Derecha:** Control de volumen (Subir/Bajar).
- **Mano Izquierda:** Control de brillo (Subir/Bajar).
- **Seguro de Palma:** Los controles solo se activan si la palma de la mano mira hacia la cámara, evitando activaciones accidentales.
- **Modo Rápido:** Ajustes de gran escala para un control ágil.

## Requisitos
- Python 3.x
- Webcam

## Instalación rápida
1. Instala las librerías necesarias:
```bash
pip install opencv-python mediapipe pyautogui screen-brightness-control