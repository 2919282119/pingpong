"""
视频特征提取器

使用 PaddlePaddle 内置 ResNet50（ImageNet 预训练）提取帧级 2048 维特征，
再按时间维度聚合到 BMN 所需的 tscale 个时间步。

对于不需要 BMN 的流程，此模块可以跳过。
"""

import os
from pathlib import Path

_venv_site = Path(__file__).resolve().parent.parent.parent / "venv" / "Lib" / "site-packages"
_cuda_dirs = [
    _venv_site / "nvidia" / "cuda_runtime" / "bin",
    _venv_site / "nvidia" / "cublas" / "bin",
    _venv_site / "nvidia" / "cudnn" / "bin",
    _venv_site / "nvidia" / "cuda_nvrtc" / "bin",
]
for _d in _cuda_dirs:
    if _d.is_dir():
        os.environ["PATH"] = str(_d) + os.pathsep + os.environ.get("PATH", "")

import logging
from typing import Optional, Any

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """Extract 2048-d features from video frames using ResNet50 backbone."""

    def __init__(self, tscale: int = 200):
        self.tscale = tscale
        self._model: Any = None

    def _lazy_init(self):
        if self._model is not None:
            return
        import paddle
        from paddle.vision.models import resnet50
        paddle.set_device("cpu")
        logger.info("Loading ResNet50 feature extractor on CPU...")
        base = resnet50(pretrained=True)
        self._model = paddle.nn.Sequential(*list(base.children())[:-2])
        self._model.eval()
        logger.info("ResNet50 feature extractor loaded")

    def extract(self, video_path: str, fps: float,
                duration_s: float) -> np.ndarray:
        self._lazy_init()
        import paddle

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise IOError(f"Cannot open: {video_path}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_features: list[np.ndarray] = []

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = cv2.resize(img, (224, 224))
            img = img.astype(np.float32) / 255.0
            img = (img - np.array([0.485, 0.456, 0.406])) / np.array(
                [0.229, 0.224, 0.225])

            inp = paddle.to_tensor(
                img.transpose(2, 0, 1)[None, ...], dtype=paddle.float32)
            feat = self._model(inp).squeeze().numpy()
            if feat.ndim == 3:
                feat = feat.mean(axis=(1, 2))
            frame_features.append(feat)

        cap.release()

        if not frame_features:
            logger.warning("No frames extracted from %s", video_path)
            return np.zeros((1, 2048, self.tscale), dtype=np.float32)

        feat_arr = np.stack(frame_features, axis=0)
        return self._temporal_aggregate(feat_arr, total_frames)

    def _temporal_aggregate(self, features: np.ndarray,
                            total_frames: int) -> np.ndarray:
        if len(features) == 1:
            result = np.tile(features, (self.tscale, 1)).T
            return result[None, :, :]

        bin_edges = np.linspace(0, len(features) - 1, self.tscale + 1).astype(int)
        aggregated = []
        for i in range(self.tscale):
            lo, hi = bin_edges[i], bin_edges[i + 1]
            if hi > lo:
                aggregated.append(features[lo:hi].mean(axis=0))
            else:
                aggregated.append(features[max(0, lo)])
        result = np.stack(aggregated, axis=1)
        return result[None, :, :]
