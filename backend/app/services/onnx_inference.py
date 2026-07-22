"""
ONNX Runtime GPU inference for ResNet50 feature extraction and BMN detection.

Replaces PaddlePaddle inference with ONNX Runtime + CUDA for GPU acceleration.
"""

import os
import logging
from pathlib import Path
from typing import Optional

# Add CUDA 12 runtime DLL paths before importing onnxruntime
_CUDA_SEARCH_DIRS = [
    Path(os.path.expanduser("~")) / "AppData" / "Roaming" / "Python" / "Python313" / "site-packages" / "nvidia" / sub
    for sub in ["cublas/bin", "cuda_runtime/bin", "cuda_nvrtc/bin"]
]
# Also check dl conda env for cuDNN (from PyTorch)
_CUDA_SEARCH_DIRS.append(
    Path("D:/Code/conda/miniConda/envs/dl/Lib/site-packages/torch/lib")
)
for _p in _CUDA_SEARCH_DIRS:
    if _p.is_dir():
        os.environ["PATH"] = str(_p) + os.pathsep + os.environ.get("PATH", "")

import cv2
import numpy as np
import onnxruntime as ort

from app.config import ONNX_MODELS_DIR, TARGET_FPS

logger = logging.getLogger(__name__)

TSCALE = 200
DSCALE = 200
PROP_BOUNDARY_RATIO = 0.5
NUM_SAMPLE = 32
NUM_SAMPLE_PERBIN = 3
FEAT_DIM = 2048
CONF_THRESH = 0.15
NMS_THRESH = 0.7
MIN_WINDOW = 5
MAX_WINDOW = 200


class ONNXFeatureExtractor:
    """Extract 2048-d features using ONNX ResNet50 on GPU."""

    def __init__(self, tscale: int = TSCALE):
        self.tscale = tscale
        self._sess: Optional[ort.InferenceSession] = None

    def _lazy_init(self):
        if self._sess is not None:
            return
        model_path = ONNX_MODELS_DIR / "resnet50.onnx"
        if not model_path.exists():
            raise FileNotFoundError(f"ONNX model not found: {model_path}")
        logger.info("Loading ONNX ResNet50 on GPU...")
        self._sess = ort.InferenceSession(
            str(model_path),
            providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
        )
        logger.info("ONNX ResNet50 loaded")

    def extract(self, video_path: str, fps: float, duration_s: float) -> np.ndarray:
        self._lazy_init()
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise IOError(f"Cannot open: {video_path}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_features: list[np.ndarray] = []
        input_name = self._sess.get_inputs()[0].name

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = cv2.resize(img, (224, 224))
            img = img.astype(np.float32) / 255.0
            img = (img - np.array([0.485, 0.456, 0.406])) / np.array(
                [0.229, 0.224, 0.225])

            inp = img.transpose(2, 0, 1)[None, ...].astype(np.float32)
            feat = self._sess.run(None, {input_name: inp})[0]
            # feat shape: (1, 2048, 7, 7)
            feat = feat.squeeze(0)  # (2048, 7, 7)
            feat = feat.mean(axis=(1, 2))  # (2048,)
            frame_features.append(feat)

        cap.release()

        if not frame_features:
            logger.warning("No frames extracted from %s", video_path)
            return np.zeros((1, 2048, self.tscale), dtype=np.float32)

        feat_arr = np.stack(frame_features, axis=0)
        return self._temporal_aggregate(feat_arr, total_frames)

    def _temporal_aggregate(self, features: np.ndarray, total_frames: int) -> np.ndarray:
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


class ONNXBMNDetector:
    """BMN temporal action proposal detection using ONNX Runtime on GPU."""

    def __init__(self, tscale: int = TSCALE):
        self.tscale = tscale
        self.dscale = DSCALE
        self.prop_boundary_ratio = PROP_BOUNDARY_RATIO
        self.num_sample = NUM_SAMPLE
        self.num_sample_perbin = NUM_SAMPLE_PERBIN
        self.feat_dim = FEAT_DIM
        self._sess: Optional[ort.InferenceSession] = None
        self._feat_extractor = ONNXFeatureExtractor(tscale=tscale)

    def _lazy_init(self):
        if self._sess is not None:
            return
        model_path = Path(__file__).resolve().parent.parent.parent / "onnx_models" / "bmn.onnx"
        if not model_path.exists():
            raise FileNotFoundError(f"ONNX model not found: {model_path}")
        logger.info("Loading ONNX BMN on GPU...")
        self._sess = ort.InferenceSession(
            str(model_path),
            providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
        )
        logger.info("ONNX BMN loaded")

    def detect(self, video_path: str, duration_s: float, action_type: str):
        if not self._sess:
            self._lazy_init()
        return self._real_detect(video_path, duration_s, action_type)

    def _real_detect(self, video_path: str, duration_s: float, action_type: str):
        from app.models.schemas import ActionSegment

        features = self._feat_extractor.extract(video_path, TARGET_FPS, duration_s)
        input_name = self._sess.get_inputs()[0].name
        pred_bm, pred_start, pred_end = self._sess.run(
            None, {input_name: features.astype(np.float32)}
        )

        proposals = self._generate_proposals(pred_bm, pred_start, pred_end, duration_s)
        return [
            ActionSegment(
                start_ms=round(s * 1000, 1),
                end_ms=round(e * 1000, 1),
                action_type=action_type,
                confidence=round(float(c), 4),
            )
            for s, e, c in proposals
        ]

    # ---- Post-processing (identical to original Paddle version) ----

    def _generate_proposals(self, pred_bm, pred_start, pred_end, duration_s):
        conf_map = pred_bm[0, 0, :, :] * pred_bm[0, 1, :, :]
        start_idx = self._peak_select(pred_start)
        end_idx = self._peak_select(pred_end)
        raw = []
        for dur in range(MIN_WINDOW, min(MAX_WINDOW, conf_map.shape[0])):
            for st in range(conf_map.shape[1] - dur):
                if start_idx[st] and end_idx[st + dur]:
                    score = float(pred_start[0, st] * pred_end[0, st + dur] * conf_map[dur, st])
                    if score > CONF_THRESH:
                        raw.append((st, st + dur, score))
        if not raw:
            return []
        proposals = [(st / TSCALE * duration_s, ed / TSCALE * duration_s, sc) for st, ed, sc in raw]
        proposals.sort(key=lambda x: x[2], reverse=True)
        return self._nms(proposals)

    @staticmethod
    def _peak_select(scores):
        scores = scores.squeeze()
        max_s = scores.max()
        if max_s < 0.1:
            return [False] * len(scores)
        high = scores > max_s * 0.5
        padded = np.pad(scores, 1, mode="constant")
        peak = (padded[1:-1] > padded[:-2]) & (padded[1:-1] > padded[2:])
        return (high | peak).tolist()

    @staticmethod
    def _nms(proposals, iou_thresh=NMS_THRESH):
        keep = []
        for i, (s1, e1, _) in enumerate(proposals):
            suppressed = False
            for s2, e2, _ in proposals[:i]:
                inter = max(0, min(e1, e2) - max(s1, s2))
                union = max(e1, e2) - min(s1, s2)
                if union > 0 and inter / union > iou_thresh:
                    suppressed = True
                    break
            if not suppressed:
                keep.append(proposals[i])
        return keep
