"""
Quick inference test on a video file — standalone, no backend required.
Useful for validating that best.pt works before uploading to SafeSite AI.

Usage
─────
  python training/inference_video.py --source path/to/video.mp4
  python training/inference_video.py --source path/to/video.mp4 --weights backend/weights/best.pt --conf 0.4
  python training/inference_video.py --source 0   # webcam

Output
──────
  • Annotated video saved to --output
  • Per-class detection count table printed to terminal
  • Violation summary (NO_HELMET / NO_VEST counts)
  • Average FPS
"""
import argparse
import time
from collections import defaultdict
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser(description="SafeSite AI inference validator")
    p.add_argument("--source",  required=True,                       help="Video path, RTSP URL, or webcam index (0)")
    p.add_argument("--weights", default="backend/weights/best.pt",   help="Path to best.pt")
    p.add_argument("--conf",    type=float, default=0.4,             help="Confidence threshold")
    p.add_argument("--output",  default="runs/inference/output.mp4", help="Output video path")
    p.add_argument("--no-save", action="store_true",                 help="Skip writing output video")
    return p.parse_args()


# Violation classes for summary table
_VIOLATION_CLASSES = {"no_helmet", "no_hardhat", "no-hardhat", "no_vest", "no_safety_vest", "no-safety vest"}
_HELMET_CLASSES    = {"helmet", "hardhat"}
_VEST_CLASSES      = {"vest", "safety_vest", "safety vest"}
_PERSON_CLASSES    = {"person", "worker"}


def main():
    import cv2
    from ultralytics import YOLO

    args = parse_args()

    if not Path(args.weights).exists():
        print(f"ERROR: Weights not found at '{args.weights}'")
        print("Train the model first: python training/train_yolo.py --copy-weights")
        return

    model = YOLO(args.weights)
    print(f"Model loaded: {args.weights}")
    print(f"Classes:      {list(model.names.values())}\n")

    # Open source
    src = int(args.source) if args.source.isdigit() else args.source
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        print(f"ERROR: Cannot open source '{args.source}'")
        return

    fps    = cap.get(cv2.CAP_PROP_FPS) or 25.0
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total  = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    writer = None
    if not args.no_save:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(args.output, fourcc, fps, (width, height))

    # Counters
    class_counts: dict[str, int] = defaultdict(int)
    frame_idx  = 0
    t_start    = time.perf_counter()

    print(f"Processing {'webcam' if str(args.source).isdigit() else args.source} ...")
    print(f"Resolution: {width}×{height}  |  FPS: {fps:.1f}  |  Frames: {total or '?'}\n")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame, conf=args.conf, verbose=False)
        annotated = results[0].plot()

        if writer:
            writer.write(annotated)

        # Accumulate class counts
        for box in results[0].boxes:
            name = model.names[int(box.cls[0])].lower()
            class_counts[name] += 1

        frame_idx += 1
        if frame_idx % 100 == 0:
            elapsed = time.perf_counter() - t_start
            cur_fps = frame_idx / elapsed
            pct = f"{frame_idx / total * 100:.0f}%" if total else f"{frame_idx}fr"
            print(f"  [{pct}] frame {frame_idx}  |  {cur_fps:.1f} fps")

    cap.release()
    if writer:
        writer.release()

    elapsed = time.perf_counter() - t_start
    avg_fps = frame_idx / elapsed if elapsed > 0 else 0

    # ── Summary report ────────────────────────────────────────────────────────
    print("\n" + "=" * 50)
    print("  Detection Summary")
    print("=" * 50)
    print(f"  Frames processed : {frame_idx}")
    print(f"  Average FPS      : {avg_fps:.1f}")
    print(f"  Total time       : {elapsed:.1f}s")

    if class_counts:
        print("\n  Detections by class:")
        print(f"  {'Class':<22} {'Count':>6}")
        print(f"  {'-'*22} {'-'*6}")
        for cls, count in sorted(class_counts.items(), key=lambda x: -x[1]):
            flag = ""
            if cls in _VIOLATION_CLASSES:
                flag = " ← violation"
            print(f"  {cls:<22} {count:>6}{flag}")

        # Violation summary
        violations = {k: v for k, v in class_counts.items() if k in _VIOLATION_CLASSES}
        if violations:
            print("\n  Violation summary:")
            for vtype in ("no_helmet", "no-hardhat", "no_hardhat"):
                if vtype in violations:
                    print(f"    NO_HELMET  : {violations[vtype]}")
                    break
            for vtype in ("no_vest", "no-safety vest", "no_safety_vest"):
                if vtype in violations:
                    print(f"    NO_VEST    : {violations[vtype]}")
                    break
        else:
            print("\n  No violations detected — check confidence threshold or model quality.")
    else:
        print("\n  No detections — model may not have found any objects.")
        print("  Try lowering --conf (e.g. --conf 0.25) or check your best.pt.")

    print("=" * 50)
    if not args.no_save:
        print(f"\nOutput saved → {args.output}")


if __name__ == "__main__":
    main()
