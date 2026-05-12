"""
Golf swing analysis pipeline using AlphaPose.
"""

import sys
import os
import argparse

# Make AlphaPose importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'AlphaPose'))


def parse_args():
    parser = argparse.ArgumentParser(description='Golf Vision - Swing Analyzer')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--video', type=str, help='Path to input video file')
    group.add_argument('--webcam', type=int, help='Webcam device index (e.g. 0)')
    parser.add_argument('--outdir', type=str, default='output/', help='Output directory')
    parser.add_argument('--config', type=str,
                        default='AlphaPose/configs/coco/resnet/256x192_res50_lr1e-3_1x.yaml',
                        help='AlphaPose config file')
    parser.add_argument('--checkpoint', type=str,
                        default='AlphaPose/pretrained_models/fast_res50_256x192.pth',
                        help='AlphaPose model checkpoint')
    return parser.parse_args()


def run_pose_estimation(args):
    from alphapose.utils.config import update_config
    from alphapose.utils.transforms import get_func_heatmap_to_coord

    cfg = update_config(args.config)
    os.makedirs(args.outdir, exist_ok=True)

    source = args.video if args.video else args.webcam
    print(f"[Golf Vision] Running pose estimation on: {source}")
    print(f"[Golf Vision] Output will be saved to: {args.outdir}")

    # AlphaPose demo script handles the full inference loop
    demo_script = os.path.join(
        os.path.dirname(__file__), '..', 'AlphaPose', 'scripts', 'demo_inference.py'
    )
    cmd = (
        f"python {demo_script} "
        f"--cfg {args.config} "
        f"--checkpoint {args.checkpoint} "
        f"--{'video' if args.video else 'webcam'} {source} "
        f"--outdir {args.outdir} "
        f"--save_video"
    )
    print(f"[Golf Vision] Running: {cmd}")
    os.system(cmd)


if __name__ == '__main__':
    args = parse_args()
    run_pose_estimation(args)
