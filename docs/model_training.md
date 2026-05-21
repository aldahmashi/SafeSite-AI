# Model Training

## Requirements

- NVIDIA GPU with CUDA 11.8+ (recommended: RTX 3060 or better)
- OR Google Colab / Kaggle GPU session

## Training Command

```bash
python training/train_yolo.py \
  --model yolov8n.pt \
  --data training/dataset.yaml \
  --epochs 100 \
  --imgsz 640 \
  --batch 16 \
  --device 0
```

## Expected Output

```
runs/train/ppe_detector/
├── weights/
│   ├── best.pt      ← use this
│   └── last.pt
├── results.csv
└── confusion_matrix.png
```

## Copy Weights to Backend

```bash
cp runs/train/ppe_detector/weights/best.pt backend/weights/best.pt
```

## Evaluation

```bash
python training/evaluate.py --weights backend/weights/best.pt --data training/dataset.yaml
```
