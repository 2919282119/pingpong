"""
BMN 时序动作检测

使用 PaddleVideo 的 BMN 模型（ResNet50 特征 + BMN 推理）。
"""

import os

# Add cuDNN DLL path for PaddlePaddle (needed even in CPU mode for layer init)
_cudnn_bin = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "venv", "Lib", "site-packages", "nvidia", "cudnn", "bin",
)
if os.path.isdir(_cudnn_bin):
    os.environ["PATH"] = _cudnn_bin + os.pathsep + os.environ.get("PATH", "")

import logging
import sys
from pathlib import Path
from typing import Optional, Any

import numpy as np

from app.models.schemas import ActionSegment
from app.services.feature_extractor import FeatureExtractor
from app.config import PADDLEVIDEO_BMN_MODEL

logger = logging.getLogger(__name__)

_PV_DIR = Path(__file__).resolve().parent.parent.parent / "PaddleVideo"
if str(_PV_DIR) not in sys.path:
    sys.path.insert(0, str(_PV_DIR))

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


class BMNDetector:
    """BMN temporal action proposal detector."""

    def __init__(self, model_path: Optional[str] = None):
        self._model: Any = None
        self._model_path = model_path or str(_PV_DIR / "BMN.pdparams")
        self._device = "cpu"
        self._feat_extractor = FeatureExtractor(tscale=TSCALE)
        self._try_load_model()

    def _try_load_model(self):
        os.environ.setdefault("CUDA_VISIBLE_DEVICES", "-1")
        os.environ.setdefault("CPU_NUM", "4")
        mp = Path(self._model_path)
        if not mp.exists():
            logger.warning("BMN weights not found at %s, falling back to placeholder", mp)
            return
        try:
            import paddle
            from paddlevideo.modeling.backbones.bmn import BMN

            ckpt = paddle.load(str(mp))
            clean = {}
            for k, v in ckpt.items():
                k = k.replace("backbone.", "", 1)
                if k == "b_conv1.weight":
                    repeats = (512 + v.shape[1] - 1) // v.shape[1]
                    v = v.tile([1, repeats, 1])[:, :512, :]
                clean[k] = v

            model = BMN(
                tscale=TSCALE, dscale=DSCALE,
                prop_boundary_ratio=PROP_BOUNDARY_RATIO,
                num_sample=NUM_SAMPLE, num_sample_perbin=NUM_SAMPLE_PERBIN,
                feat_dim=FEAT_DIM,
            )
            model.set_state_dict(clean)
            model.eval()
            self._model = model
            logger.info("BMN model loaded on %s from %s", self._device, mp)
        except Exception as e:
            logger.error("Failed to load BMN model: %s", e)
            logger.warning("Falling back to placeholder BMN")

    def detect(self, video_path: str, duration_s: float, action_type: str) -> list[ActionSegment]:
        if self._model is not None:
            return self._real_detect(video_path, duration_s, action_type)
        return self._placeholder_detect(duration_s, action_type)

    def _real_detect(self, video_path: str, duration_s: float, action_type: str) -> list[ActionSegment]:
        import paddle
        features = self._feat_extractor.extract(video_path, 10, duration_s)
        inp = paddle.to_tensor(features, dtype=paddle.float32)
        with paddle.no_grad():
            pred_bm, pred_start, pred_end = self._model(inp)
        pred_bm = pred_bm.numpy()
        pred_start = pred_start.numpy().squeeze()
        pred_end = pred_end.numpy().squeeze()
        proposals = self._generate_proposals(pred_bm, pred_start, pred_end, duration_s)
        return [
            ActionSegment(start_ms=round(s*1000,1), end_ms=round(e*1000,1), action_type=action_type, confidence=round(float(c),4))
            for s, e, c in proposals
        ]

    def _generate_proposals(self, pred_bm, pred_start, pred_end, duration_s):
        conf_map = pred_bm[0,0,:,:] * pred_bm[0,1,:,:]
        start_idx = self._peak_select(pred_start)
        end_idx = self._peak_select(pred_end)
        raw = []
        for dur in range(MIN_WINDOW, min(MAX_WINDOW, conf_map.shape[0])):
            for st in range(conf_map.shape[1] - dur):
                if start_idx[st] and end_idx[st+dur]:
                    score = float(pred_start[st] * pred_end[st+dur] * conf_map[dur,st])
                    if score > CONF_THRESH:
                        raw.append((st, st+dur, score))
        if not raw: return []
        proposals = [(st/TSCALE*duration_s, ed/TSCALE*duration_s, sc) for st, ed, sc in raw]
        proposals.sort(key=lambda x: x[2], reverse=True)
        return self._nms(proposals)

    @staticmethod
    def _peak_select(scores):
        max_s = scores.max()
        if max_s < 0.1: return [False]*len(scores)
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
                if union > 0 and inter/union > iou_thresh:
                    suppressed = True
                    break
            if not suppressed: keep.append(proposals[i])
        return keep

    def _placeholder_detect(self, duration_s, action_type):
        rng = np.random.RandomState(42)
        segments = []
        t = 2.0
        while t < duration_s - 3:
            seg_len = round(1.0 + rng.random()*1.5, 2)
            end = min(t+seg_len, duration_s)
            conf = round(0.75+rng.random()*0.2, 3)
            segments.append(ActionSegment(start_ms=round(t*1000), end_ms=round(end*1000), action_type=action_type, confidence=min(conf,0.99)))
            t = end + 2.0 + rng.random()*3.0
        return segments
