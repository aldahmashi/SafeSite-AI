"""
Quick inference test on a video file — standalone, no backend required.

Usage:
    python training/inference_video.py --source path/to/video.mp4 --weights backend/weights/best.pt
"""
import argparse
import cv2
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True, help="Path to video file or RTSP URL")
    p.add_argument("--weights", default="backend/weights/best.pt")
    p.add_argument("--conf", type=float, default=0.4)
    p.add_argument("--output", default="runs/inference/output.mp4")
    return p.parse_args()


def main():
    from ultralytics import YOLO

    args = parse_args()
    model = YOLO(args.weights)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(args.source)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    writer = cv2.VideoWriter(args.output, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    frame_idx = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        results = model(frame, conf=args.conf, verbose=False)
        annotated = results[0].plot()
        writer.write(annotated)
        frame_idx += 1
        if frame_idx % 30 == 0:
            print(f"Processed frame {frame_idx}")

    cap.release()
    writer.release()
    print(f"Done. Output saved to {args.output}")


if __name__ == "__main__":
    main()
