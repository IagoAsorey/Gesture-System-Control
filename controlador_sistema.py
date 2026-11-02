"""Módulo de control del sistema para Linux (Omarchy / Wayland) y gestión de gestos."""

import shutil
import subprocess
import time
from dataclasses import dataclass, field
from typing import Optional

import config


@dataclass
class EstadoGestoMano:
    """Almacena el estado de seguimiento continuo para una mano específica."""

    activo: bool = False
    y_ancla: Optional[float] = None
    ultimo_disparo_ts: float = 0.0
    ultima_accion_texto: str = ""
    ultima_accion_color: tuple[int, int, int] = (0, 255, 0)
    ultima_accion_ts: float = 0.0


class ControladorSistema:
    """Gestiona los cambios de volumen y brillo en el sistema operativo."""

    def __init__(
        self,
        umbral_paso: float = config.MOVEMENT_STEP_THRESHOLD,
        cooldown_sec: float = config.ACTION_COOLDOWN_SEC,
        paso_volumen: int = config.VOLUME_STEP,
        paso_brillo: int = config.BRIGHTNESS_STEP,
    ):
        self.umbral_paso = umbral_paso
        self.cooldown_sec = cooldown_sec
        self.paso_volumen = paso_volumen
        self.paso_brillo = paso_brillo

        self.estados: dict[str, EstadoGestoMano] = {
            "Derecha": EstadoGestoMano(),
            "Izquierda": EstadoGestoMano(),
        }

        # Verificar disponibilidad de comandos de Omarchy
        self.cmd_volumen = shutil.which("omarchy-audio-output-volume")
        self.cmd_brillo = shutil.which("omarchy-brightness-display")

    def reiniciar_mano(self, hand_label: str) -> None:
        """Reinicia el seguimiento de arrastre cuando la mano se abre o sale de cámara."""
        if hand_label in self.estados:
            estado = self.estados[hand_label]
            estado.activo = False
            estado.y_ancla = None

    def procesar_gesto_mano(
        self, hand_label: str, gesto_activo: bool, y_actual: float
    ) -> Optional[str]:
        """Evalúa el desplazamiento vertical de la mano mientras el gesto está activo.

        Args:
            hand_label: 'Derecha' (Volumen) o 'Izquierda' (Brillo).
            gesto_activo: True si la palma es visible y el puño está cerrado.
            y_actual: Coordenada Y normalizada (0.0 arriba, 1.0 abajo) de la muñeca.

        Returns:
            Texto de la acción ejecutada (ej. 'VOLUMEN +') o None si no se disparó acción.
        """
        estado = self.estados.get(hand_label)
        if estado is None:
            return None

        if not gesto_activo:
            self.reiniciar_mano(hand_label)
            return None

        ahora = time.monotonic()

        # Primer frame con el puño cerrado: fijamos el punto de anclaje sin disparar acción
        if not estado.activo or estado.y_ancla is None:
            estado.activo = True
            estado.y_ancla = y_actual
            return None

        # Diferencia positiva = la mano subió (Y disminuye al subir en la imagen)
        diferencia = estado.y_ancla - y_actual

        if abs(diferencia) < self.umbral_paso:
            return None

        # Respetar el cooldown para no saturar procesos ni el OSD
        if (ahora - estado.ultimo_disparo_ts) < self.cooldown_sec:
            return None

        subir = diferencia > 0
        # Actualizamos el ancla a la posición actual para requerir otro desplazamiento completo
        estado.y_ancla = y_actual
        estado.ultimo_disparo_ts = ahora

        if hand_label == "Derecha":
            self.ajustar_volumen(subir=subir)
            texto = "VOLUMEN +" if subir else "VOLUMEN -"
        else:
            self.ajustar_brillo(subir=subir)
            texto = "BRILLO +" if subir else "BRILLO -"

        estado.ultima_accion_texto = texto
        estado.ultima_accion_color = (0, 255, 0) if subir else (0, 0, 255)
        estado.ultima_accion_ts = ahora
        return texto

    def ajustar_volumen(self, subir: bool) -> None:
        """Sube o baja el volumen del sistema usando omarchy-audio-output-volume."""
        if not self.cmd_volumen:
            return
        arg = f"+{self.paso_volumen}" if subir else f"-{self.paso_volumen}"
        self._ejecutar_async([self.cmd_volumen, arg])

    def ajustar_brillo(self, subir: bool) -> None:
        """Sube o baja el brillo de la pantalla usando omarchy-brightness-display."""
        if not self.cmd_brillo:
            return
        arg = f"+{self.paso_brillo}%" if subir else f"{self.paso_brillo}%-"
        self._ejecutar_async([self.cmd_brillo, arg])

    @staticmethod
    def _ejecutar_async(comando: list[str]) -> None:
        """Ejecuta un comando del sistema sin bloquear el hilo de captura de vídeo."""
        try:
            subprocess.Popen(
                comando,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            pass
