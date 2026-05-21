# Dataset Preparation

## Recommended Datasets

1. **Construction Site Safety (Roboflow)**
   - Classes: hardhat, safety vest, person, machinery
   - Format: YOLOv8
   - URL: https://universe.roboflow.com/roboflow-universe-projects/construction-site-safety

2. **SH17 PPE Dataset**
   - 17 PPE categories including helmet, vest, gloves, goggles, boots
   - URL: https://github.com/erfanMhi/SH17-Dataset

## Download and Prepare

```bash
# Install Roboflow CLI
pip install roboflow

# Download dataset (requires free Roboflow account)
python - <<EOF
from roboflow import Roboflow
rf = Roboflow(api_key="YOUR_ROBOFLOW_KEY")
project = rf.workspace("roboflow-universe-projects").project("construction-site-safety")
dataset = project.version(1).download("yolov8", location="data/ppe_dataset")
EOF
```

## Directory Structure Expected by dataset.yaml

```
data/ppe_dataset/
├── images/
│   ├── train/
│   ├── val/
│   └── test/
└── labels/
    ├── train/
    ├── val/
    └── test/
```
