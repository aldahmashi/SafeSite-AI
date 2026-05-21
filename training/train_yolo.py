"""
Train YOLOv8/YOLO11 PPE detection model.

Usage:
    python training/train_yolo.py --model yolov8n.pt --epochs 50 --imgsz 640
"""
import argparse
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser(description="Train YOLO PPE model")
    p.add_argument("--model", default="yolov8n.pt", help="Base YOLO model weights")
    p.add_argument("--data", default="training/dataset.yaml", help="Dataset YAML path")
    p.add_argument("--epochs", type=int, default=50)
    p.add_argument("--imgsz", type=int, default=640)
    p.add_argument("--batch", type=int, default=16)
    p.add_argument("--device", default="0", help="cuda device index or 'cpu'")
    p.add_argument("--project", default="runs/train", help="Output project directory")
    p.add_argument("--name", default="ppe_detector")
    return p.parse_args()


def main():
    from ultralytics import YOLO

    args = parse_args()
    model = YOLO(args.model)
    results = model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        project=args.project,
        name=args.name,
        exist_ok=True,
        patience=10,
        save=True,
        plots=True,
    )
    best_weights = Path(args.project) / args.name / "weights" / "best.pt"
    print(f"\nTraining complete. Best weights: {best_weights}")
    print(f"Copy to backend: cp {best_weights} backend/weights/best.pt")


if __name__ == "__main__":
    main()
