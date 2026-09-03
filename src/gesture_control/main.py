from pathlib import Path
from gesture_control import config
from gesture_control.application import ActionExecutor, FrameProcessor, GestureAnalyzer
from gesture_control.infrastructure import (
    create_brightness_control,
    create_volume_control,
)
from gesture_control.infrastructure.camera import OpenCVCamera
from gesture_control.infrastructure.detectors import MediaPipeHandDetector
from gesture_control.presentation import OpenCVDisplay


def main() -> None:
    print(f"Camera: {config.camera.index} ({config.camera.width}x{config.camera.height})")
    print(f"Volume step: {config.volume.step}%")
    print(f"Brightness step: {config.brightness.step}%")
    print("Press ESC to exit")

    camera = OpenCVCamera(
        index=config.camera.index,
        width=config.camera.width,
        height=config.camera.height,
    )

    if not camera.is_opened:
        print("Error: Could not open camera")
        return

    model_path = str(Path(__file__).parent.parent.parent / "hand_landmarker.task")
    detector = MediaPipeHandDetector(model_path=model_path)
    display = OpenCVDisplay(config.display.window_name)
    analyzer = GestureAnalyzer(
        movement_threshold=config.gesture.movement_threshold,
        palm_required=config.gesture.palm_required,
    )
    volume_control = create_volume_control(config.volume.linux_method)
    brightness_control = create_brightness_control()
    executor = ActionExecutor(
        volume_control=volume_control,
        brightness_control=brightness_control,
        volume_step=config.volume.step,
        brightness_step=config.brightness.step,
    )

    processor = FrameProcessor(
        camera=camera,
        detector=detector,
        display=display,
        analyzer=analyzer,
        executor=executor,
        show_landmarks=config.display.show_landmarks,
    )

    processor.run()


if __name__ == "__main__":
    main()