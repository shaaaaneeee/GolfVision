# Golf Vision

Real-time golf swing analysis using multi-person pose estimation powered by [AlphaPose](https://github.com/MVIG-SJTU/AlphaPose).

## Overview

Golf Vision uses AlphaPose to detect and track body keypoints during a golf swing, enabling:
- Full-body pose estimation (17–136 keypoints)
- Swing phase detection
- Posture and alignment analysis
- Video and webcam input support

## Project Structure

```
GolfVision/
├── AlphaPose/          # AlphaPose submodule (pose estimation engine)
├── src/
│   ├── analyze.py      # Main golf swing analysis pipeline
│   └── utils.py        # Helper utilities
├── input/              # Input videos/images
├── output/             # Analysis results
├── requirements.txt
└── README.md
```

## Setup

### 1. Clone with submodules

```bash
git clone --recurse-submodules https://github.com/eydinsafin/GolfVision.git
cd GolfVision
```

### 2. Install AlphaPose dependencies

Follow the [AlphaPose installation guide](AlphaPose/docs/INSTALL.md):

```bash
cd AlphaPose
pip install -r requirements.txt
python setup.py build develop
cd ..
```

### 3. Install Golf Vision dependencies

```bash
pip install -r requirements.txt
```

### 4. Download pretrained models

Download models from AlphaPose and place them in `AlphaPose/pretrained_models/`.
See [AlphaPose Model Zoo](AlphaPose/docs/MODEL_ZOO.md) for available models.

## Usage

### Analyze a golf swing video

```bash
python src/analyze.py --video input/swing.mp4 --outdir output/
```

### Run on webcam

```bash
python src/analyze.py --webcam 0 --outdir output/
```

## Requirements

- Python 3.7+
- PyTorch 1.11+ with CUDA (recommended)
- See `requirements.txt` for full list

## License

AlphaPose is free for non-commercial use. See [AlphaPose license](AlphaPose/LICENSE) for details.
