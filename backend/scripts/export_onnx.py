"""
Export PaddlePaddle models (ResNet50 + BMN) to ONNX format.

This script is designed to run with PaddlePaddle 2.6.x (not 3.x)
because paddle2onnx is incompatible with Paddle 3.x.

Usage:
    D:\\Code\\conda\\miniConda\\Scripts\\conda.exe run -n dl python scripts/export_onnx.py

Output:
    backend/onnx_models/resnet50.onnx
    backend/onnx_models/bmn.onnx
"""

import os
import sys
import logging
import math
import numpy as np
import paddle
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parent.parent
ONNX_DIR = BACKEND_DIR / "onnx_models"
os.makedirs(ONNX_DIR, exist_ok=True)

TSCALE = 200
DSCALE = 200
PROP_BOUNDARY_RATIO = 0.5
NUM_SAMPLE = 32
NUM_SAMPLE_PERBIN = 3
FEAT_DIM = 2048


# ---- BMN model definition (self-contained, no PaddleVideo dependency) ----

def _get_interp1d_bin_mask(seg_xmin, seg_xmax, tscale, num_sample, num_sample_perbin):
    plen = float(seg_xmax - seg_xmin)
    plen_sample = plen / (num_sample * num_sample_perbin - 1.0)
    total_samples = [
        seg_xmin + plen_sample * ii
        for ii in range(num_sample * num_sample_perbin)
    ]
    p_mask = []
    for idx in range(num_sample):
        bin_samples = total_samples[idx * num_sample_perbin:(idx + 1) * num_sample_perbin]
        bin_vector = np.zeros([tscale])
        for sample in bin_samples:
            sample_upper = math.ceil(sample)
            sample_decimal, sample_down = math.modf(sample)
            if (tscale - 1) >= int(sample_down) >= 0:
                bin_vector[int(sample_down)] += 1 - sample_decimal
            if (tscale - 1) >= int(sample_upper) >= 0:
                bin_vector[int(sample_upper)] += sample_decimal
        bin_vector = 1.0 / num_sample_perbin * bin_vector
        p_mask.append(bin_vector)
    p_mask = np.stack(p_mask, axis=1)
    return p_mask


def _get_interp1d_mask(tscale, dscale, prop_boundary_ratio, num_sample, num_sample_perbin):
    mask_mat = []
    for start_index in range(tscale):
        mask_mat_vector = []
        for duration_index in range(dscale):
            if start_index + duration_index < tscale:
                p_xmin = start_index
                p_xmax = start_index + duration_index
                center_len = float(p_xmax - p_xmin) + 1
                sample_xmin = p_xmin - center_len * prop_boundary_ratio
                sample_xmax = p_xmax + center_len * prop_boundary_ratio
                p_mask = _get_interp1d_bin_mask(sample_xmin, sample_xmax, tscale, num_sample, num_sample_perbin)
            else:
                p_mask = np.zeros([tscale, num_sample])
            mask_mat_vector.append(p_mask)
        mask_mat_vector = np.stack(mask_mat_vector, axis=2)
        mask_mat.append(mask_mat_vector)
    mask_mat = np.stack(mask_mat, axis=3)
    mask_mat = mask_mat.astype(np.float32)
    sample_mask = np.reshape(mask_mat, [tscale, -1])
    return sample_mask


class BMN(paddle.nn.Layer):
    def __init__(self, tscale, dscale, prop_boundary_ratio, num_sample, num_sample_perbin, feat_dim=400):
        super().__init__()
        self.feat_dim = feat_dim
        self.tscale = tscale
        self.dscale = dscale
        self.prop_boundary_ratio = prop_boundary_ratio
        self.num_sample = num_sample
        self.num_sample_perbin = num_sample_perbin
        self.hidden_dim_1d = 256
        self.hidden_dim_2d = 128
        self.hidden_dim_3d = 512

        def _init_weights(name, in_c, k):
            fan_in = in_c * k * 1
            k_val = 1. / math.sqrt(fan_in)
            return paddle.ParamAttr(name=name, initializer=paddle.nn.initializer.Uniform(low=-k_val, high=k_val))

        self.b_conv1 = paddle.nn.Conv1D(in_channels=self.feat_dim, out_channels=self.hidden_dim_1d, kernel_size=3, padding=1, groups=4, weight_attr=_init_weights('Base_1_w', self.feat_dim, 3), bias_attr=_init_weights('Base_1_b', self.feat_dim, 3))
        self.b_conv1_act = paddle.nn.ReLU()
        self.b_conv2 = paddle.nn.Conv1D(in_channels=self.hidden_dim_1d, out_channels=self.hidden_dim_1d, kernel_size=3, padding=1, groups=4, weight_attr=_init_weights('Base_2_w', self.hidden_dim_1d, 3), bias_attr=_init_weights('Base_2_b', self.hidden_dim_1d, 3))
        self.b_conv2_act = paddle.nn.ReLU()
        self.ts_conv1 = paddle.nn.Conv1D(in_channels=self.hidden_dim_1d, out_channels=self.hidden_dim_1d, kernel_size=3, padding=1, groups=4, weight_attr=_init_weights('TEM_s1_w', self.hidden_dim_1d, 3), bias_attr=_init_weights('TEM_s1_b', self.hidden_dim_1d, 3))
        self.ts_conv1_act = paddle.nn.ReLU()
        self.ts_conv2 = paddle.nn.Conv1D(in_channels=self.hidden_dim_1d, out_channels=1, kernel_size=1, padding=0, groups=1, weight_attr=_init_weights('TEM_s2_w', self.hidden_dim_1d, 1), bias_attr=_init_weights('TEM_s2_b', self.hidden_dim_1d, 1))
        self.ts_conv2_act = paddle.nn.Sigmoid()
        self.te_conv1 = paddle.nn.Conv1D(in_channels=self.hidden_dim_1d, out_channels=self.hidden_dim_1d, kernel_size=3, padding=1, groups=4, weight_attr=_init_weights('TEM_e1_w', self.hidden_dim_1d, 3), bias_attr=_init_weights('TEM_e1_b', self.hidden_dim_1d, 3))
        self.te_conv1_act = paddle.nn.ReLU()
        self.te_conv2 = paddle.nn.Conv1D(in_channels=self.hidden_dim_1d, out_channels=1, kernel_size=1, padding=0, groups=1, weight_attr=_init_weights('TEM_e2_w', self.hidden_dim_1d, 1), bias_attr=_init_weights('TEM_e2_b', self.hidden_dim_1d, 1))
        self.te_conv2_act = paddle.nn.Sigmoid()
        self.p_conv1 = paddle.nn.Conv1D(in_channels=self.hidden_dim_1d, out_channels=self.hidden_dim_2d, kernel_size=3, padding=1, groups=1, weight_attr=_init_weights('PEM_1d_w', self.hidden_dim_1d, 3), bias_attr=_init_weights('PEM_1d_b', self.hidden_dim_1d, 3))
        self.p_conv1_act = paddle.nn.ReLU()

        sample_mask = _get_interp1d_mask(self.tscale, self.dscale, self.prop_boundary_ratio, self.num_sample, self.num_sample_perbin)
        self.sample_mask = paddle.to_tensor(sample_mask)
        self.sample_mask.stop_gradient = True

        self.p_conv3d1 = paddle.nn.Conv3D(in_channels=128, out_channels=self.hidden_dim_3d, kernel_size=(self.num_sample, 1, 1), stride=(self.num_sample, 1, 1), padding=0, weight_attr=paddle.ParamAttr(name="PEM_3d1_w"), bias_attr=paddle.ParamAttr(name="PEM_3d1_b"))
        self.p_conv3d1_act = paddle.nn.ReLU()
        self.p_conv2d1 = paddle.nn.Conv2D(in_channels=512, out_channels=self.hidden_dim_2d, kernel_size=1, stride=1, padding=0, weight_attr=paddle.ParamAttr(name="PEM_2d1_w"), bias_attr=paddle.ParamAttr(name="PEM_2d1_b"))
        self.p_conv2d1_act = paddle.nn.ReLU()
        self.p_conv2d2 = paddle.nn.Conv2D(in_channels=128, out_channels=self.hidden_dim_2d, kernel_size=3, stride=1, padding=1, weight_attr=paddle.ParamAttr(name="PEM_2d2_w"), bias_attr=paddle.ParamAttr(name="PEM_2d2_b"))
        self.p_conv2d2_act = paddle.nn.ReLU()
        self.p_conv2d3 = paddle.nn.Conv2D(in_channels=128, out_channels=self.hidden_dim_2d, kernel_size=3, stride=1, padding=1, weight_attr=paddle.ParamAttr(name="PEM_2d3_w"), bias_attr=paddle.ParamAttr(name="PEM_2d3_b"))
        self.p_conv2d3_act = paddle.nn.ReLU()
        self.p_conv2d4 = paddle.nn.Conv2D(in_channels=128, out_channels=2, kernel_size=1, stride=1, padding=0, weight_attr=paddle.ParamAttr(name="PEM_2d4_w"), bias_attr=paddle.ParamAttr(name="PEM_2d4_b"))
        self.p_conv2d4_act = paddle.nn.Sigmoid()

    def forward(self, x):
        x = self.b_conv1(x)
        x = self.b_conv1_act(x)
        x = self.b_conv2(x)
        x = self.b_conv2_act(x)
        xs = self.ts_conv1(x)
        xs = self.ts_conv1_act(xs)
        xs = self.ts_conv2(xs)
        xs = self.ts_conv2_act(xs)
        xs = paddle.squeeze(xs, axis=[1])
        xe = self.te_conv1(x)
        xe = self.te_conv1_act(xe)
        xe = self.te_conv2(xe)
        xe = self.te_conv2_act(xe)
        xe = paddle.squeeze(xe, axis=[1])
        xp = self.p_conv1(x)
        xp = self.p_conv1_act(xp)
        xp = paddle.matmul(xp, self.sample_mask)
        xp = paddle.reshape(xp, shape=[0, 0, -1, self.dscale, self.tscale])
        xp = self.p_conv3d1(xp)
        xp = self.p_conv3d1_act(xp)
        xp = paddle.squeeze(xp, axis=[2])
        xp = self.p_conv2d1(xp)
        xp = self.p_conv2d1_act(xp)
        xp = self.p_conv2d2(xp)
        xp = self.p_conv2d2_act(xp)
        xp = self.p_conv2d3(xp)
        xp = self.p_conv2d3_act(xp)
        xp = self.p_conv2d4(xp)
        xp = self.p_conv2d4_act(xp)
        return xp, xs, xe


def export_resnet50():
    """Export ResNet50 feature extractor to ONNX."""
    logger.info("Exporting ResNet50...")
    from paddle.vision.models import resnet50

    base = resnet50(pretrained=True)
    model = paddle.nn.Sequential(*list(base.children())[:-2])
    model.eval()

    # Input: [1, 3, 224, 224] normalized image
    input_spec = [
        paddle.static.InputSpec(
            shape=[1, 3, 224, 224],
            dtype="float32",
            name="input",
        )
    ]

    onnx_path = str(ONNX_DIR / "resnet50.onnx")
    paddle.onnx.export(model, onnx_path.replace(".onnx", ""), input_spec=input_spec, opset_version=13)

    # Verify
    import onnx
    onnx_model = onnx.load(onnx_path)
    onnx.checker.check_model(onnx_model)
    logger.info("ResNet50 exported: %s (%d MB)", onnx_path, os.path.getsize(onnx_path) // 1024 // 1024)
    return onnx_path


def export_bmn():
    """Export BMN model to ONNX."""
    logger.info("Exporting BMN...")
    import paddle

    model_path = BACKEND_DIR / "PaddleVideo" / "BMN.pdparams"
    if not model_path.exists():
        logger.error("BMN weights not found at %s", model_path)
        return None

    ckpt = paddle.load(str(model_path))
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

    # BMN input: [1, 2048, 200] features
    input_spec = [
        paddle.static.InputSpec(
            shape=[1, FEAT_DIM, TSCALE],
            dtype="float32",
            name="features",
        )
    ]

    onnx_path = str(ONNX_DIR / "bmn.onnx")
    paddle.onnx.export(model, onnx_path.replace(".onnx", ""), input_spec=input_spec, opset_version=13)

    # Verify
    import onnx
    onnx_model = onnx.load(onnx_path)
    onnx.checker.check_model(onnx_model)
    logger.info("BMN exported: %s (%d KB)", onnx_path, os.path.getsize(onnx_path) // 1024)
    return onnx_path


def test_inference(onnx_resnet_path, onnx_bmn_path):
    """Test ONNX models with onnxruntime to ensure they produce valid output."""
    logger.info("Testing ONNX models with onnxruntime...")
    import numpy as np
    import onnxruntime as ort

    # Test ResNet50
    sess = ort.InferenceSession(onnx_resnet_path, providers=["CPUExecutionProvider"])
    dummy_input = np.random.randn(1, 3, 224, 224).astype(np.float32)
    output = sess.run(None, {"input": dummy_input})
    logger.info("ResNet50 output shape: %s", output[0].shape)
    assert output[0].shape == (1, 2048, 7, 7), f"Unexpected shape: {output[0].shape}"

    # Test BMN
    sess = ort.InferenceSession(onnx_bmn_path, providers=["CPUExecutionProvider"])
    dummy_input = np.random.randn(1, 2048, TSCALE).astype(np.float32)
    outputs = sess.run(None, {"features": dummy_input})
    logger.info("BMN output count: %d", len(outputs))
    for i, o in enumerate(outputs):
        logger.info("  output[%d] shape: %s", i, o.shape)
    # BMN should output 3 tensors: pred_bm, pred_start, pred_end
    assert len(outputs) == 3, f"Expected 3 outputs, got {len(outputs)}"

    logger.info("All tests passed!")


if __name__ == "__main__":
    logger.info("Starting ONNX export...")
    logger.info("ONNX output dir: %s", ONNX_DIR)

    r_path = export_resnet50()
    b_path = export_bmn()

    if r_path and b_path:
        test_inference(r_path, b_path)
        logger.info("Export complete!")
    else:
        logger.error("Export failed!")
        sys.exit(1)
