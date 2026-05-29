"""
Train YOLOv8 / YOLO11 PPE detection model for SafeSite AI.

Recommended dataset: Roboflow "Construction Site Safety" (v28)
  https://universe.roboflow.com/roboflow-universe-projects/construction-site-safety

Usage examples
──────────────
  # Standard training on GPU 0:
  python training/train_yolo.py

  # Larger model, more epochs:
  python training/train_yolo.py --model yolov8s.pt --epochs 100 --batch 32

  # CPU only (slow):
  python training/train_yolo.py --device cpu --batch 4 --workers 0

  # Resume interrupted training:
  python training/train_yolo.py --resume runs/train/ppe_detector/weights/last.pt

  # Auto-copy best.pt to backend after training:
  python training/train_yolo.py --copy-weights

After training, copy weights manually if not using --copy-weights:
  cp runs/train/ppe_detector/weights/best.pt backend/weights/best.pt   (Linux/Mac)
  copy runs\\train\\ppe_detector\\weights\\best.pt backend\\weights\\best.pt  (Windows)
"""
import argparse
import shutil
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser(description="Train YOLO PPE detection model")
    p.add_argument(
        "--model", default="yolov8n.pt",
        help="Base model weights. Options: yolov8n.pt (fast), yolov8s.pt (balanced), yolov8m.pt (accurate)",
    )
    p.add_argument("--data",    default="training/dataset.yaml", help="Dataset YAML path")
    p.add_argument("--epochs",  type=int, default=50,  help="Training epochs (50 is a good start)")
    p.add_argument("--imgsz",   type=int, default=640, help="Input image size")
    p.add_argument("--batch",   type=int, default=16,  help="Batch size (-1 = auto)")
    p.add_argument("--device",  default="0",           help="GPU index ('0') or 'cpu'")
    p.add_argument("--workers", type=int, default=2,   help="DataLoader workers (use 0 on Colab/Windows if errors)")
    p.add_argument("--project", default="runs/train",  help="Output directory")
    p.add_argument("--name",    default="ppe_detector", help="Run name")
    p.add_argument(
        "--resume", metavar="LAST_PT", default=None,
        help="Path to last.pt to resume an interrupted training run",
    )
    p.add_argument(
        "--copy-weights", action="store_true",
        help="Auto-copy best.pt → backend/weights/best.pt after training",
    )
    p.add_argument(
        "--patience", type=int, default=15,
        help="Early stopping patience (epochs without improvement)",
    )
    return p.parse_args()


def print_metrics(results) -> None:
    """Pretty-print validation metrics after training."""
    try:
        metrics = results.results_dict
        print("\n" + "=" * 55)
        print("  Training complete — Validation metrics")
        print("=" * 55)
        print(f"  mAP50      : {metrics.get('metrics/mAP50(B)', 0):.4f}")
        print(f"  mAP50-95   : {metrics.get('metrics/mAP50-95(B)', 0):.4f}")
        print(f"  Precision  : {metrics.get('metrics/precision(B)', 0):.4f}")
        print(f"  Recall     : {metrics.get('metrics/recall(B)', 0):.4f}")
        print("=" * 55)

        map50 = metrics.get("metrics/mAP50(B)", 0)
        if map50 >= 0.70:
            print("  ✓ Good model — ready to use")
        elif map50 >= 0.50:
            print("  ~ Acceptable model — consider more epochs or a larger base model")
        else:
            print("  ✗ Low mAP — check dataset quality or try yolov8s.pt with more epochs")
    except Exception:
        pass


def main():
    from ultralytics import YOLO

    args = parse_args()

    if args.resume:
        # Resume from last.pt — ignores other training args except device
        model = YOLO(args.resume)
        print(f"Resuming training from: {args.resume}")
        results = model.train(resume=True, device=args.device)
    else:
        model = YOLO(args.model)
        print(f"Starting training: model={args.model}  epochs={args.epochs}  batch={args.batch}  device={args.device}")
        results = model.train(
            data=args.data,
            epochs=args.epochs,
            imgsz=args.imgsz,
            batch=args.batch,
            device=args.device,
            workers=args.workers,
            project=args.project,
            name=args.name,
            exist_ok=True,
            patience=args.patience,
            save=True,
            plots=True,
            # Augmentation — construction-site appropriate
            hsv_h=0.015,     # hue variation (slight)
            hsv_s=0.7,       # saturation variation
            hsv_v=0.4,       # brightness variation (handles indoor/outdoor)
            fliplr=0.5,      # horizontal flip
            flipud=0.0,      # no vertical flip (workers always upright)
            mosaic=1.0,      # mosaic augmentation
            mixup=0.1,       # mild mixup
        )

    best_weights = Path(args.project) / args.name / "weights" / "best.pt"
    print_metrics(results)

    print(f"\nBest weights saved at: {best_weights}")

    if args.copy_weights:
        dest = Path("backend/weights/best.pt")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(best_weights, dest)
        print(f"Copied → {dest}  ✓")
    else:
        print("\nTo use in SafeSite AI, copy the weights:")
        print(f"  Windows: copy {best_weights} backend\\weights\\best.pt")
        print(f"  Linux:   cp {best_weights} backend/weights/best.pt")


if __name__ == "__main__":
    main()
