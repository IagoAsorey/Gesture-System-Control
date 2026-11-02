# Gesture System Control

Controla el volumen y el brillo de tu ordenador en Linux (Omarchy / Wayland) mediante gestos manuales frente a la cámara utilizando Computer Vision (**OpenCV** + **MediaPipe Tasks**).

## Características
- **Mano Derecha:** Control de volumen (`VOLUMEN +` / `VOLUMEN -` mediante `omarchy-audio-output-volume`).
- **Mano Izquierda:** Control de brillo (`BRILLO +` / `BRILLO -` mediante `omarchy-brightness-display`).
- **Seguro de Palma y Puño:** Los controles solo se activan si la palma mira hacia la cámara y cierras el puño, evitando activaciones accidentales.
- **Control Fluido con OSD Nativo:** Ajuste progresivo por desplazamiento vertical con *cooldown*, mostrando el OSD nativo del sistema.
- **Previsualización Modular:** Ventana de desarrollo opcional (`--preview` / `--no-preview`) totalmente desacoplada para poder ejecutarse en segundo plano en producción.

## Requisitos
- Linux con entorno Omarchy (`omarchy-audio-output-volume` y `omarchy-brightness-display`)
- Python 3.10+
- Webcam

## Instalación rápida

1. Crea y activa el entorno virtual e instala las dependencias:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
*(El modelo oficial `hand_landmarker.task` de MediaPipe se descargará automáticamente la primera vez que inicies el programa si no está presente).*

## Uso

- **Modo desarrollo (con ventana de previsualización y dibujo de manos):**
```bash
.venv/bin/python main.py --preview
```
*(Por defecto la previsualización está activada en `config.py`. Pulsa `ESC` o `q` en la ventana para salir).*

- **Modo segundo plano / versión final (sin ventana gráfica):**
```bash
.venv/bin/python main.py --no-preview
```

- **Seleccionar otra cámara:**
```bash
.venv/bin/python main.py --camera 1
```
