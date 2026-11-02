"""Entry point for the Gesture System Control application."""

import argparse
import signal
import sys

import cv2

from gesture_control import (
    HandDetector,
    SystemController,
    Visualizer,
    config,
)


def parse_args() -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Real-time hand gesture control for system volume and display brightness."
    )
    preview_group = parser.add_mutually_exclusive_group()
    preview_group.add_argument(
        "--preview",
        dest="preview",
        action="store_true",
        help="Show the real-time camera preview window (enabled by default in development).",
    )
    preview_group.add_argument(
        "--no-preview",
        "--headless",
        dest="preview",
        action="store_false",
        help="Run in the background without opening a camera preview window.",
    )
    parser.set_defaults(preview=config.SHOW_PREVIEW)

    parser.add_argument(
        "--camera",
        type=int,
        default=config.CAMERA_INDEX,
        help=f"Video capture device index (default: {config.CAMERA_INDEX}).",
    )
    return parser.parse_args()


def main() -> None:
    """Runs the main video capture, hand detection, and system control loop."""
    args = parse_args()

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print(f"Error: Could not open video camera (index {args.camera}).", file=sys.stderr)
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

    should_stop = False

    def handle_signal(_sig: int, _frame) -> None:
        nonlocal should_stop
        should_stop = True

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    # Automatically reap finished background child processes to prevent zombies
    if hasattr(signal, "SIGCHLD"):
        signal.signal(signal.SIGCHLD, signal.SIG_IGN)

    controller = SystemController()
    visualizer = Visualizer() if args.preview else None

    mode_str = (
        "with preview window (press ESC or 'q' to exit)"
        if args.preview
        else "in headless background mode"
    )
    print(f"Gesture System Control started {mode_str}.")

    try:
        with HandDetector() as detector:
            while not should_stop:
                ret, frame = cap.read()
                if not ret:
                    print("Warning: Failed to read frame from camera.", file=sys.stderr)
                    break

                # Resize only if the camera driver ignored the requested dimensions
                if (
                    frame.shape[1] != config.FRAME_WIDTH
                    or frame.shape[0] != config.FRAME_HEIGHT
                ):
                    frame = cv2.resize(frame, (config.FRAME_WIDTH, config.FRAME_HEIGHT))

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                detected_hands = detector.detect(frame_rgb)

                present_labels = {hand.label for hand in detected_hands}
                for hand in detected_hands:
                    controller.process_hand_gesture(
                        hand_label=hand.label,
                        is_gesture_active=hand.is_gesture_active,
                        current_y=hand.wrist_y,
                    )

                for label in ("Right", "Left"):
                    if label not in present_labels:
                        controller.reset_hand(label)

                if visualizer is not None and visualizer.render(
                    frame, detected_hands, controller
                ):
                    break
    finally:
        cap.release()
        if visualizer is not None:
            visualizer.close()


if __name__ == "__main__":
    main()
