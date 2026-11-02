"""Script principal para el control gestual del volumen y brillo en Linux."""

import argparse
import signal
import sys

import cv2

import config
from controlador_sistema import ControladorSistema
from detector_manos import DetectorManos
from visualizador import Visualizador


def parse_args() -> argparse.Namespace:
    """Procesa los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Control gestual de volumen y brillo mediante cámara web."
    )
    grupo_preview = parser.add_mutually_exclusive_group()
    grupo_preview.add_argument(
        "--preview",
        dest="preview",
        action="store_true",
        help="Muestra la ventana de previsualización de la cámara (por defecto en desarrollo).",
    )
    grupo_preview.add_argument(
        "--no-preview",
        "--headless",
        dest="preview",
        action="store_false",
        help="Ejecuta en segundo plano sin abrir ventana de previsualización.",
    )
    parser.set_defaults(preview=config.SHOW_PREVIEW)

    parser.add_argument(
        "--camera",
        type=int,
        default=config.CAMERA_INDEX,
        help=f"Índice de la cámara de vídeo (por defecto: {config.CAMERA_INDEX}).",
    )
    return parser.parse_args()


def main() -> None:
    """Función principal que ejecuta el bucle de captura, detección y control."""
    args = parse_args()

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print(f"Error: No se puede abrir la cámara (índice {args.camera}).", file=sys.stderr)
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

    detector = DetectorManos()
    controlador = ControladorSistema()
    visualizador = Visualizador() if args.preview else None

    detener = False

    def manejar_senal(_sig, _frame):
        nonlocal detener
        detener = True

    signal.signal(signal.SIGINT, manejar_senal)
    signal.signal(signal.SIGTERM, manejar_senal)

    modo_str = "con previsualización (pulsa ESC o 'q' para salir)" if args.preview else "en segundo plano (headless)"
    print(f"Control Gestual iniciado {modo_str}.")

    try:
        while not detener:
            ret, frame = cap.read()
            if not ret:
                print("Advertencia: No se pudo leer el frame de la cámara.", file=sys.stderr)
                break

            # Preparación de la imagen (modo espejo)
            frame = cv2.resize(frame, (config.FRAME_WIDTH, config.FRAME_HEIGHT))
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Detectar y analizar manos presentes en el frame
            resultado_mp = detector.procesar_frame(frame_rgb)
            manos_detectadas = detector.analizar_resultados(resultado_mp)

            etiquetas_presentes = set()
            for mano in manos_detectadas:
                etiquetas_presentes.add(mano.etiqueta)
                gesto_activo = mano.estado_palma == "visible" and mano.puno_cerrado
                controlador.procesar_gesto_mano(
                    hand_label=mano.etiqueta,
                    gesto_activo=gesto_activo,
                    y_actual=mano.y_muneca,
                )

            # Reiniciar el estado de las manos que no están en el frame actual
            for etiqueta in ("Derecha", "Izquierda"):
                if etiqueta not in etiquetas_presentes:
                    controlador.reiniciar_mano(etiqueta)

            # Renderizar ventana opcional de previsualización
            if visualizador is not None:
                salir = visualizador.renderizar(frame, manos_detectadas, controlador)
                if salir:
                    break
    finally:
        cap.release()
        detector.cerrar()
        if visualizador is not None:
            visualizador.cerrar()


if __name__ == "__main__":
    main()
