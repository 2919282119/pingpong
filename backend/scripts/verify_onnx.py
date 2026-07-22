"""
Compare Paddle CPU vs ONNX GPU inference results for accuracy verification.

Usage: python scripts/verify_onnx.py <video_path>
"""
import sys
import os
import time
import logging

# Add CUDA DLL paths (same as onnx_inference.py)
from pathlib import Path
_CUDA_SEARCH_DIRS = [
    Path(os.path.expanduser("~")) / "AppData" / "Roaming" / "Python" / "Python313" / "site-packages" / "nvidia" / sub
    for sub in ["cublas/bin", "cuda_runtime/bin", "cuda_nvrtc/bin"]
]
_CUDA_SEARCH_DIRS.append(Path("D:/Code/conda/miniConda/envs/dl/Lib/site-packages/torch/lib"))
for _p in _CUDA_SEARCH_DIRS:
    if _p.is_dir():
        os.environ["PATH"] = str(_p) + os.pathsep + os.environ.get("PATH", "")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

import numpy as np
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("verify")

from app.services.feature_extractor import FeatureExtractor as PaddleFeatureExtractor
from app.services.onnx_inference import ONNXFeatureExtractor
from app.services.paddle_infer import BMNDetector as PaddleBMN
from app.services.onnx_inference import ONNXBMNDetector


def compare_features(video_path):
    print("=" * 60)
    print("COMPARING: Feature Extraction (ResNet50)")
    print("=" * 60)

    # Paddle CPU
    t0 = time.time()
    paddle_fe = PaddleFeatureExtractor(tscale=200)
    paddle_feats = paddle_fe.extract(video_path, 10, 0)
    t1 = time.time()
    print(f"Paddle CPU:  {t1-t0:.2f}s  shape={paddle_feats.shape}")

    # ONNX GPU
    t0 = time.time()
    onnx_fe = ONNXFeatureExtractor(tscale=200)
    onnx_feats = onnx_fe.extract(video_path, 10, 0)
    t1 = time.time()
    print(f"ONNX GPU:    {t1-t0:.2f}s  shape={onnx_feats.shape}")

    print(f"\nShape match: {paddle_feats.shape == onnx_feats.shape}")

    # Compare values with tolerance
    if paddle_feats.shape == onnx_feats.shape:
        abs_diff = np.abs(paddle_feats - onnx_feats)
        rel_diff = abs_diff / (np.abs(paddle_feats) + 1e-8)
        print(f"Max absolute diff:    {abs_diff.max():.6f}")
        print(f"Mean absolute diff:  {abs_diff.mean():.6f}")
        print(f"Max relative diff:   {rel_diff.max():.6f}")
        print(f"Mean relative diff:  {rel_diff.mean():.6f}")
        print(f"Identical (1e-5):    {np.allclose(paddle_feats, onnx_feats, atol=1e-5)}")
        print(f"Identical (1e-3):    {np.allclose(paddle_feats, onnx_feats, atol=1e-3)}")
    else:
        print("SKIPPED: shape mismatch")
    print()


def compare_bmn_output(video_path):
    print("=" * 60)
    print("COMPARING: BMN Detection")
    print("=" * 60)

    # Paddle CPU (use detect to get feature + BMN)
    t0 = time.time()
    paddle_bmn = PaddleBMN()
    paddle_segments = paddle_bmn._real_detect(video_path, 30.0, "fore_topspin")
    t1 = time.time()
    print(f"Paddle CPU BMN:    {t1-t0:.2f}s  segments={len(paddle_segments)}")
    for s in paddle_segments[:3]:
        print(f"  [{s.start_ms:.0f}-{s.end_ms:.0f}ms] conf={s.confidence:.4f}")

    # ONNX GPU
    t0 = time.time()
    onnx_bmn = ONNXBMNDetector()
    onnx_segments = onnx_bmn.detect(video_path, 30.0, "fore_topspin")
    t1 = time.time()
    print(f"ONNX GPU BMN:      {t1-t0:.2f}s  segments={len(onnx_segments)}")
    for s in onnx_segments[:3]:
        print(f"  [{s.start_ms:.0f}-{s.end_ms:.0f}ms] conf={s.confidence:.4f}")

    # Compare
    print(f"\nSegment count: Paddle={len(paddle_segments)} ONNX={len(onnx_segments)}")
    if len(paddle_segments) == len(onnx_segments):
        diffs = []
        for ps, os_ in zip(paddle_segments, onnx_segments):
            diffs.append(abs(ps.start_ms - os_.start_ms) + abs(ps.end_ms - os_.end_ms))
        print(f"Avg segment time diff: {sum(diffs)/len(diffs):.1f}ms")
    print()


if __name__ == "__main__":
    video_path = sys.argv[1] if len(sys.argv) > 1 else None
    if not video_path or not os.path.exists(video_path):
        print("Usage: python scripts/verify_onnx.py <video_path>")
        sys.exit(1)

    # Use a short video for speed (prefer already-preprocessed)
    # Take a short segment video from temp
    print(f"Video: {video_path} ({os.path.getsize(video_path)//1024}KB)")

    compare_features(video_path)
    compare_bmn_output(video_path)

    print("DONE")
