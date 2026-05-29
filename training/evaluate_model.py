"""
Evaluate a trained YOLO PPE model on the validation set.

Computes and prints:
  - mAP50 and mAP50-95 (overall and per class)
  - Precision and Recall
  - Fitness score

Saves results to runs/evaluate/metrics.json

Usage
─────
  python training/evaluate_model.py
  python training/evaluate_model.py --weights backend/weights/best.pt --data training/dataset.yaml
"""
import argparse
import json
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser(description="Evaluate SafeSite AI YOLO model")
    p.add_argument("--weights", default="backend/weights/best.pt",   help="Path to best.pt")
    p.add_argument("--data",    default="training/dataset.yaml",     help="Dataset YAML")
    p.add_argument("--imgsz",   type=int, default=640,               help="Input image size")
    p.add_argument("--batch",   type=int, default=16,                help="Batch size")
    p.add_argument("--device",  default="0",                         help="Device ('0' or 'cpu')")
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--output",  default="runs/evaluate/metrics.json", help="Where to save JSON results")
    return p.parse_args()


def main():
    from ultralytics import YOLO

    args = parse_args()

    if not Path(args.weights).exists():
        print(f"ERROR: Weights not found: '{args.weights}'")
        print("Train first: python training/train_yolo.py --copy-weights")
        return

    if not Path(args.data).exists():
        print(f"ERROR: Dataset YAML not found: '{args.data}'")
        return

    print(f"Evaluating: {args.weights}")
    print(f"Dataset:    {args.data}\n")

    model = YOLO(args.weights)
    metrics = model.val(
        data=args.data,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        workers=args.workers,
        verbose=True,
    )

    # ── Overall metrics ───────────────────────────────────────────────────────
    rd = metrics.results_dict
    map50    = rd.get("metrics/mAP50(B)", 0)
    map5095  = rd.get("metrics/mAP50-95(B)", 0)
    prec     = rd.get("metrics/precision(B)", 0)
    recall   = rd.get("metrics/recall(B)", 0)
    fitness  = rd.get("fitness", 0)

    print("\n" + "=" * 55)
    print("  Model Evaluation Results")
    print("=" * 55)
    print(f"  mAP50      : {map50:.4f}  {'✓ Good' if map50 >= 0.7 else '~ Acceptable' if map50 >= 0.5 else '✗ Low'}")
    print(f"  mAP50-95   : {map5095:.4f}")
    print(f"  Precision  : {prec:.4f}")
    print(f"  Recall     : {recall:.4f}")
    print(f"  Fitness    : {fitness:.4f}")

    # Per-class breakdown
    if hasattr(metrics, "ap_class_index") and metrics.ap_class_index is not None:
        print("\n  Per-class mAP50:")
        print(f"  {'Class':<22} {'mAP50':>7}")
        print(f"  {'-'*22} {'-'*7}")
        names = model.names
        for cls_idx, ap in zip(metrics.ap_class_index, metrics.box.ap50):
            cls_name = names.get(int(cls_idx), str(cls_idx))
            print(f"  {cls_name:<22} {float(ap):>7.4f}")

    print("=" * 55)

    # Guidance
    print("\nInterpretation:")
    if map50 >= 0.70:
        print("  → Model is ready for production use in SafeSite AI.")
    elif map50 >= 0.50:
        print("  → Acceptable. Consider: more epochs, yolov8s.pt, or data augmentation.")
    else:
        print("  → Low accuracy. Check: dataset labels, class balance, training epochs.")
        print("     Tip: Try --model yolov8s.pt and --epochs 100.")

    # Save JSON
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    result_data = {
        "weights": args.weights,
        "dataset": args.data,
        "map50":    round(map50, 4),
        "map50_95": round(map5095, 4),
        "precision": round(prec, 4),
        "recall":    round(recall, 4),
        "fitness":   round(fitness, 4),
    }

    # Add per-class if available
    if hasattr(metrics, "ap_class_index") and metrics.ap_class_index is not None:
        result_data["per_class"] = {
            model.names.get(int(idx), str(idx)): round(float(ap), 4)
            for idx, ap in zip(metrics.ap_class_index, metrics.box.ap50)
        }

    output_path.write_text(json.dumps(result_data, indent=2))
    print(f"\nMetrics saved → {output_path}")


if __name__ == "__main__":
    main()
